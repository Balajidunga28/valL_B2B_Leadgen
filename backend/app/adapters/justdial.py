"""
url: /backend/app/adapters/justdial.py
About:
  JustDial business directory scraper with Playwright + httpx fallback.
  JustDial uses aggressive anti-bot protection (Akamai) so this adapter
  may fail gracefully. Falls back to httpx when Playwright unavailable.
"""

import asyncio
import hashlib
import logging
import random
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from app.adapters.base import SourceAdapter

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
]


def _parse_query(query: str, location: str | None) -> tuple[str, str]:
    """Parse query into (category, location). Location param overrides query location."""
    for pat in [r"^(.+?)\s+(?:in|near|around|at|of)\s+(.+)$", r"^(.+?)\s*[-]\s*(.+)$"]:
        m = re.match(pat, query, re.IGNORECASE)
        if m:
            cat = m.group(1).strip()
            if location:
                return cat, location.strip()
            return cat, m.group(2).strip()
    if location:
        return query.strip(), location.strip()
    return query.strip(), ""


def _clean_name(name: str) -> str:
    name = re.sub(r"\s*[-–|]\s*(?:JustDial|India|list|directory).*$", "", name, flags=re.IGNORECASE).strip()
    return name if len(name) > 2 else ""


class JustDialAdapter(SourceAdapter):
    """Attempts to scrape JustDial for business listings."""

    name = "justdial"
    display_name = "JustDial (Business Directory)"

    def __init__(self, api_key=None, delay_min=1.5, delay_max=3.0):
        super().__init__(api_key=None)
        self.delay_min = delay_min
        self.delay_max = delay_max
        self._playwright = None
        self._browser = None
        self._has_playwright = False

    async def _ensure_browser(self):
        if self._browser is not None or self._has_playwright:
            return
        try:
            from playwright.async_api import async_playwright
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox", "--disable-dev-shm-usage",
                    "--disable-gpu", "--disable-web-security",
                    "--disable-features=IsolateOrigins,site-per-process",
                ],
            )
            self._has_playwright = True
        except ImportError:
            logger.info("Playwright not available, using httpx fallback for JustDial")
            self._has_playwright = False
        except Exception as e:
            logger.warning("Playwright launch failed: %s, using httpx fallback", e)
            self._has_playwright = False

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    # --- httpx fallback ---
    async def _try_mobile_site_httpx(self, category: str, city: str, extracted_at: str) -> list[dict[str, Any]]:
        """Fallback: fetch JustDial via httpx and parse HTML."""
        url = f"https://www.justdial.com/{quote_plus(city)}/{quote_plus(category)}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        records = []
        try:
            resp = await self.client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            if resp.status_code != 200:
                logger.warning("JustDial httpx returned %d", resp.status_code)
                return []
            html = resp.text
            if "unusual traffic" in html.lower() or len(html) < 500:
                logger.warning("JustDial blocked httpx request or returned minimal content")
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select(".resultbox_info, .store-info, .resultbox, [class*='listing'], [class*='result']")
            for card in cards:
                name_el = card.select_one(".resultbox_title, .store-name, h3, h2, [class*='name']")
                phone_el = card.select_one(".resultbox_contact, [class*='phone'], [class*='contact']")
                addr_el = card.select_one(".resultbox_addr, [class*='address'], [class*='locality']")
                rating_el = card.select_one("[class*='rating'], [class*='star']")
                name = name_el.get_text(strip=True) if name_el else ""
                phone = phone_el.get_text(strip=True) if phone_el else ""
                addr = addr_el.get_text(strip=True) if addr_el else ""
                rating = rating_el.get_text(strip=True) if rating_el else ""
                if name and len(name) > 2:
                    name = _clean_name(name)
                    if name:
                        records.append({
                            "name": name, "phone": phone, "address": addr, "rating": rating,
                            "_provenance": {
                                "search_query": f"{category} in {city}",
                                "search_url": url, "extracted_at": extracted_at,
                                "extraction_method": "justdial_httpx",
                                "source_type": "business_directory",
                            },
                        })
        except Exception as e:
            logger.error("JustDial httpx error: %s", e)
        return records

    # --- Playwright path ---
    async def _try_mobile_site(self, category: str, city: str, extracted_at: str) -> list[dict[str, Any]]:
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent, viewport={"width": 390, "height": 844},
            locale="en-IN", is_mobile=True,
        )
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => false });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        """)
        records = []
        page = None
        try:
            page = await context.new_page()
            search_url = f"https://www.justdial.com/{quote_plus(city)}/{quote_plus(category)}"
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(5000)
            content = await page.content()
            if "unusual traffic" in content.lower() or len(content) < 500:
                logger.warning("JustDial blocked the request")
                return []
            raw_records = await page.evaluate("""() => {
                const results = [];
                const cards = document.querySelectorAll('.resultbox_info, .store-info, .resultbox, [class*="listing"], [class*="result"]');
                cards.forEach(card => {
                    const nameEl = card.querySelector('.resultbox_title, .store-name, h3, h2, [class*="name"]');
                    const phoneEl = card.querySelector('.resultbox_contact, [class*="phone"], [class*="contact"]');
                    const addrEl = card.querySelector('.resultbox_addr, [class*="address"], [class*="locality"]');
                    const ratingEl = card.querySelector('[class*="rating"], [class*="star"]');
                    const name = nameEl ? nameEl.innerText.trim() : '';
                    const phone = phoneEl ? phoneEl.innerText.trim() : '';
                    const addr = addrEl ? addrEl.innerText.trim() : '';
                    const rating = ratingEl ? ratingEl.innerText.trim() : '';
                    if (name && name.length > 2) {
                        results.push({ name, phone, address: addr, rating });
                    }
                });
                return results;
            }""")
            for rec in raw_records:
                name = _clean_name(rec.get("name", ""))
                if not name:
                    continue
                rec["name"] = name
                rec["_provenance"] = {
                    "search_query": f"{category} in {city}",
                    "search_url": search_url, "extracted_at": extracted_at,
                    "extraction_method": "justdial", "source_type": "business_directory",
                }
                records.append(rec)
        except Exception as e:
            logger.error(f"JustDial search error: {e}")
        finally:
            if page:
                await page.close()
            await context.close()
        return records

    async def search(self, query: str, location: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        await self._ensure_browser()
        category, loc = _parse_query(query, location)
        city = loc.split(",")[0].strip() if loc else ""
        if not city:
            return []
        extracted_at = datetime.now(timezone.utc).isoformat()
        if self._has_playwright and self._browser:
            records = await self._try_mobile_site(category, city, extracted_at)
        else:
            records = await self._try_mobile_site_httpx(category, city, extracted_at)
        logger.info(f"JustDial total: {len(records)} unique")
        return records[:limit]

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        provenance = raw_record.pop("_provenance", {})
        name = raw_record.get("name") or ""
        source_id = hashlib.md5(f"jd_{name}".encode()).hexdigest()[:16]
        return {
            "source_record_id": f"jd_{source_id}",
            "raw_data": {
                "name": raw_record.get("name"), "address": raw_record.get("address"),
                "city": None, "state": None, "pin_code": None,
                "phone": raw_record.get("phone"), "website": raw_record.get("website"),
                "email": None, "industry": raw_record.get("category"),
                "latitude": None, "longitude": None,
                "rating": None, "reviews_count": None, "opening_hours": None,
                "maps_url": None, "source_url": provenance.get("search_url"),
                "metadata": {
                    "extraction_method": provenance.get("extraction_method", "justdial"),
                    "search_query": provenance.get("search_query"),
                    "extracted_at": provenance.get("extracted_at"),
                    "source_type": "business_directory",
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get("https://www.justdial.com", timeout=10.0)
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
