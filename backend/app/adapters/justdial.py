"""
url: /backend/app/adapters/justdial.py
About:
  Playwright-based JustDial scraper for ValLG. Attempts to extract business
  listings from JustDial's mobile site. JustDial uses aggressive anti-bot
  protection (Akamai) so this adapter may fail gracefully.
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
    if location:
        return query.strip(), location.strip()
    for pat in [r"^(.+?)\s+(?:in|near|around|at|of)\s+(.+)$", r"^(.+?)\s*[-]\s*(.+)$"]:
        m = re.match(pat, query, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip()
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

    async def _ensure_browser(self):
        if self._browser is not None:
            return
        from playwright.async_api import async_playwright
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    async def _try_mobile_site(self, category: str, city: str, extracted_at: str) -> list[dict[str, Any]]:
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={"width": 390, "height": 844},
            locale="en-IN",
            is_mobile=True,
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
                    "search_url": search_url,
                    "extracted_at": extracted_at,
                    "extraction_method": "justdial",
                    "source_type": "business_directory",
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
        records = await self._try_mobile_site(category, city, extracted_at)

        logger.info(f"JustDial total: {len(records)} unique")
        return records[:limit]

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        provenance = raw_record.pop("_provenance", {})
        name = raw_record.get("name") or ""
        source_id = hashlib.md5(f"jd_{name}".encode()).hexdigest()[:16]

        return {
            "source_record_id": f"jd_{source_id}",
            "raw_data": {
                "name": raw_record.get("name"),
                "address": raw_record.get("address"),
                "city": None,
                "state": None,
                "pin_code": None,
                "phone": raw_record.get("phone"),
                "website": raw_record.get("website"),
                "email": None,
                "industry": raw_record.get("category"),
                "latitude": None,
                "longitude": None,
                "rating": None,
                "reviews_count": None,
                "opening_hours": None,
                "maps_url": None,
                "source_url": provenance.get("search_url"),
                "metadata": {
                    "extraction_method": "justdial",
                    "search_query": provenance.get("search_query"),
                    "extracted_at": provenance.get("extracted_at"),
                    "source_type": "business_directory",
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            from playwright.async_api import async_playwright
            pw = await async_playwright().start()
            browser = await pw.chromium.launch(headless=True, args=["--no-sandbox"])
            await browser.close()
            await pw.stop()
            return True
        except Exception:
            return False

    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
