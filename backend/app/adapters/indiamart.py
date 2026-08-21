"""
url: /backend/app/adapters/indiamart.py
About:
  IndiaMART B2B directory scraper with Playwright + httpx fallback.
  Searches IndiaMART for businesses matching the search category.
  When Playwright is unavailable, falls back to httpx HTML parsing.
  Fully generic — category parameter drives search.
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
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

INDIAMART_DIR_URL = "https://dir.indiamart.com/impcat"
INDIAMART_SEARCH_URL = "https://www.indiamart.com/proddetail"


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


def _extract_city_from_location(location: str) -> str:
    parts = [p.strip() for p in location.split(",")]
    return parts[0] if parts else ""


class IndiaMARTAdapter(SourceAdapter):
    """Scrapes IndiaMART B2B directory for businesses."""

    name = "indiamart"
    display_name = "IndiaMART (B2B Directory)"

    def __init__(self, api_key=None, delay_min=1.0, delay_max=2.5):
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
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
            )
            self._has_playwright = True
        except ImportError:
            logger.info("Playwright not available, using httpx fallback for IndiaMART")
            self._has_playwright = False
        except Exception as e:
            logger.warning("Playwright launch failed: %s, using httpx fallback", e)
            self._has_playwright = False

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    # --- httpx fallback ---
    async def _search_category_httpx(self, category_slug: str, city: str, extracted_at: str) -> list[dict[str, Any]]:
        """Fallback: fetch IndiaMART category page via httpx and parse."""
        url = f"{INDIAMART_DIR_URL}/{category_slug}.html"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-IN,en;q=0.9",
        }
        records = []
        try:
            resp = await self.client.get(url, headers=headers, follow_redirects=True, timeout=15.0)
            if resp.status_code != 200:
                logger.warning("IndiaMART httpx returned %d for '%s'", resp.status_code, category_slug)
                return []
            html = resp.text
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            # IndiaMART product cards
            cards = soup.select(".pCard1, .pla-ai-card, .product-card, [class*='product']")
            for card in cards:
                title_el = card.select_one(".prdtitle, .pla-ai-name, .product-name, h3, h2")
                company_el = card.select_one(".pla-ai-company, .cp, .company-name, .seller-name")
                addr_el = card.select_one(".seller-addr, [itemprop='addressLocality'], .address")
                link_el = card.select_one("a[href*='/proddetail/'], a[href*='/impcat/']")
                title = title_el.get_text(strip=True) if title_el else ""
                company = company_el.get_text(strip=True) if company_el else ""
                addr = addr_el.get_text(strip=True) if addr_el else ""
                link = link_el.get("href", "") if link_el else ""
                if title or company:
                    name = company or title
                    if city.lower() in addr.lower() or not city:
                        records.append({
                            "name": name, "product": title, "address": addr,
                            "source_url": link,
                            "_provenance": {
                                "search_query": f"{category_slug} in {city}",
                                "search_url": url, "extracted_at": extracted_at,
                                "extraction_method": "indiamart_httpx",
                                "source_type": "b2b_directory",
                            },
                        })
        except Exception as e:
            logger.error("IndiaMART httpx error for '%s': %s", category_slug, e)
        return records

    # --- Playwright path ---
    async def _search_category(self, category_slug: str, city: str, extracted_at: str) -> list[dict[str, Any]]:
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent, viewport={"width": 1920, "height": 1080}, locale="en-IN",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false });")
        records = []
        page = None
        try:
            page = await context.new_page()
            url = f"{INDIAMART_DIR_URL}/{category_slug}.html"
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
            raw_records = await page.evaluate("""(cityFilter) => {
                const results = [];
                const cards = document.querySelectorAll('.pCard1, .pla-ai-card');
                cards.forEach(card => {
                    const titleEl = card.querySelector('.prdtitle, .pla-ai-name');
                    const companyEl = card.querySelector('.pla-ai-company, .cp');
                    const addrEl = card.querySelector('.seller-addr, [itemprop="addressLocality"]');
                    const linkEl = card.querySelector('a[href*="/proddetail/"], a[href*="/impcat/"]');
                    const title = titleEl ? titleEl.innerText.trim() : '';
                    const company = companyEl ? companyEl.innerText.trim() : '';
                    const addr = addrEl ? addrEl.innerText.trim() : '';
                    const link = linkEl ? linkEl.href : '';
                    if (title || company) {
                        results.push({ name: company || title, product: title, address: addr, source_url: link });
                    }
                });
                return results;
            }""", city)
            for rec in raw_records:
                addr = rec.get("address", "")
                if city.lower() in addr.lower() or not city:
                    rec["_provenance"] = {
                        "search_query": f"{category_slug} in {city}",
                        "search_url": url, "extracted_at": extracted_at,
                        "extraction_method": "indiamart", "source_type": "b2b_directory",
                    }
                    records.append(rec)
        except Exception as e:
            logger.error(f"IndiaMART search error for {category_slug}: {e}")
        finally:
            if page:
                await page.close()
            await context.close()
        return records

    async def search(self, query: str, location: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        await self._ensure_browser()
        category, loc = _parse_query(query, location)
        city = _extract_city_from_location(loc) if loc else ""
        extracted_at = datetime.now(timezone.utc).isoformat()

        # Generate category slugs - use original query text for better matching
        category_slugs = []
        # Primary: use the category from the parsed query
        slug = re.sub(r"[^a-z0-9]+", "-", category.lower().strip()).strip("-")
        if slug:
            category_slugs.append(slug)

        # Secondary: if category has multiple words, try the full category
        if len(category.split()) > 1 and slug not in [category.lower().replace(" ", "-")]:
            full_slug = re.sub(r"[^a-z0-9]+", "-", category.lower()).strip("-")
            if full_slug and full_slug not in category_slugs:
                category_slugs.append(full_slug)

        all_records: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        if self._has_playwright and self._browser:
            # Playwright path: run sequentially (browser resource constraints)
            for cat_slug in category_slugs[:2]:
                records = await self._search_category(cat_slug, city, extracted_at)
                for rec in records:
                    name_key = re.sub(r"[^a-z0-9]", "", (rec.get("name") or "").lower())
                    if name_key and name_key not in seen_names and len(name_key) > 2:
                        seen_names.add(name_key)
                        all_records.append(rec)
        else:
            # httpx fallback: run category searches concurrently
            async def search_one(cat_slug: str):
                return await self._search_category_httpx(cat_slug, city, extracted_at)

            tasks = [search_one(slug) for slug in category_slugs[:2]]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, Exception):
                    continue
                for rec in result:
                    name_key = re.sub(r"[^a-z0-9]", "", (rec.get("name") or "").lower())
                    if name_key and name_key not in seen_names and len(name_key) > 2:
                        seen_names.add(name_key)
                        all_records.append(rec)

        logger.info(f"IndiaMART total: {len(all_records)} unique for category '{category}'")
        return all_records[:limit]

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        provenance = raw_record.pop("_provenance", {})
        name = raw_record.get("name") or ""
        source_url = raw_record.get("source_url") or ""
        source_id = hashlib.md5(f"{name}|{source_url}".encode()).hexdigest()[:16]
        return {
            "source_record_id": f"imart_{source_id}",
            "raw_data": {
                "name": raw_record.get("name"), "address": raw_record.get("address"),
                "city": None, "state": None, "pin_code": None,
                "phone": raw_record.get("phone"), "website": raw_record.get("website"),
                "email": None, "industry": raw_record.get("product"),
                "latitude": None, "longitude": None,
                "rating": None, "reviews_count": None, "opening_hours": None,
                "maps_url": None, "source_url": raw_record.get("source_url"),
                "metadata": {
                    "extraction_method": provenance.get("extraction_method", "indiamart"),
                    "search_query": provenance.get("search_query"),
                    "extracted_at": provenance.get("extracted_at"),
                    "source_type": "b2b_directory",
                },
            },
        }

    async def health_check(self) -> bool:
        try:
            resp = await self.client.get(INDIAMART_DIR_URL, timeout=10.0)
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
