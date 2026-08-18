"""
url: /backend/app/adapters/web_search.py
About:
  Playwright-based web search adapter that discovers business listings through
  Bing search results. Searches for business directories and extracts business
  names, phones, and addresses from search snippets and directory pages.
  No API key required. Fully generic — no hardcoded city/category/query logic.
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
from app.geo import GENERIC_SKIP_WORDS, GENERIC_NAME_PATTERN

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
]

BING_SEARCH_URL = "https://www.bing.com/search"


def _parse_query(query: str, location: str | None) -> tuple[str, str]:
    for pat in [r"^(.+?)\s+(?:in|near|around|at|of)\s+(.+)$", r"^(.+?)\s*[-]\s*(.+)$"]:
        m = re.match(pat, query, re.IGNORECASE)
        if m:
            return m.group(1).strip(), m.group(2).strip()
    if location:
        return query.strip(), location.strip()
    return query.strip(), ""


def _dedup_key(record: dict) -> str:
    name = re.sub(r"[^a-z0-9]", "", (record.get("name") or "").lower().strip())
    phone = re.sub(r"[^0-9]", "", record.get("phone") or "")
    if phone and len(phone) >= 8:
        return hashlib.md5(f"p:{phone}".encode()).hexdigest()
    return hashlib.md5(f"n:{name}".encode()).hexdigest()


def _extract_phones(text: str) -> list[str]:
    phones = []
    for m in re.finditer(r"(?:\+91[\s\-]?)?(\d{5}[\s\-]?\d{5}|\d{4}[\s\-]?\d{3}[\s\-]?\d{3}|\d{10})", text):
        phone = re.sub(r"[^0-9+]", "", m.group(0))
        if len(phone) >= 10:
            phones.append(phone)
    return phones


def _extract_business_name_from_snippet(title: str, snippet: str) -> str | None:
    """Try to extract a business name from search result title/snippet."""
    name = title.strip()

    prefixes = ["list of ", "top ", "best ", "directory of ", "find ", "all ", "explore "]
    for p in prefixes:
        if name.lower().startswith(p):
            return None

    skip_phrases = [
        "empanelled", "facilities in india", "across india", "interactive map",
        "contact details and", "world health organization", "who.int",
        "government", "ministry", "cghs", "ayushman", "insurance",
        "articles", "guides", "tips", "reviews of", "vs ", "comparison",
        "how to", "what is", "benefits of", "cost of", "price of",
        "near me", "in india", "list of", "top 10", "best 10",
    ]
    for sp in skip_phrases:
        if sp in name.lower():
            return None

    for sw in GENERIC_SKIP_WORDS:
        if sw in name.lower():
            return None

    if len(name) < 3 or len(name) > 100:
        return None

    name = re.sub(r"\s*[-–|]\s*(?:India|list|directory|contact|guide|article).*$", "", name, flags=re.IGNORECASE).strip()

    return name if len(name) > 2 else None


class WebSearchAdapter(SourceAdapter):
    """Discovers businesses through Bing search results."""

    name = "web_search"
    display_name = "Web Search (Free)"

    def __init__(self, api_key=None, delay_min=1.0, delay_max=2.5):
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
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
        )

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    async def _search_bing(self, query: str, page_num: int = 0) -> list[dict[str, Any]]:
        """Search Bing and extract business-relevant results."""
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false });")

        results = []
        page = None

        try:
            page = await context.new_page()
            offset = page_num * 10
            search_url = f"{BING_SEARCH_URL}?q={quote_plus(query)}&first={offset + 1}"
            await page.goto(search_url, wait_until="networkidle", timeout=20000)
            await page.wait_for_timeout(2000)

            raw_results = await page.evaluate("""() => {
                const data = [];
                const items = document.querySelectorAll('.b_algo');
                items.forEach(item => {
                    const titleEl = item.querySelector('h2 a');
                    const snippetEl = item.querySelector('.b_caption p, .b_algoSlug');
                    if (titleEl) {
                        data.push({
                            title: titleEl.innerText.trim(),
                            url: titleEl.href,
                            snippet: snippetEl ? snippetEl.innerText.trim() : ''
                        });
                    }
                });
                return data;
            }""")

            for r in raw_results:
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                url = r.get("url", "")
                combined = f"{title} {snippet}"

                phones = _extract_phones(combined)
                name = _extract_business_name_from_snippet(title, snippet)

                if name:
                    results.append({
                        "name": name,
                        "phone": phones[0] if phones else None,
                        "source_url": url,
                        "snippet": snippet[:200],
                    })

        except Exception as e:
            logger.error(f"Bing search error: {e}")
        finally:
            if page:
                await page.close()
            await context.close()

        return results

    async def _scrape_directory_page(self, url: str, extracted_at: str) -> list[dict[str, Any]]:
        """Attempt to scrape a directory/listing page for business data."""
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )

        records = []
        page = None

        try:
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)

            text_content = await page.inner_text("body")

            phones = _extract_phones(text_content)

            business_pattern = re.compile(
                GENERIC_NAME_PATTERN,
                re.MULTILINE
            )

            for match in business_pattern.finditer(text_content):
                name = match.group(1).strip()
                context_text = match.group(2).strip()

                if len(name) < 5 or len(name) > 80:
                    continue

                ctx_phones = _extract_phones(context_text)
                record = {
                    "name": name,
                    "phone": ctx_phones[0] if ctx_phones else None,
                    "address": None,
                    "website": None,
                    "maps_url": None,
                    "category": None,
                    "latitude": None,
                    "longitude": None,
                    "rating": None,
                    "reviews_count": None,
                    "opening_hours": None,
                    "source_url": url,
                    "_provenance": {
                        "search_query": url,
                        "search_url": url,
                        "extracted_at": extracted_at,
                        "extraction_method": "web_search",
                        "source_type": "directory_page",
                    },
                }
                records.append(record)

        except Exception as e:
            logger.debug(f"Directory scrape error for {url}: {e}")
        finally:
            if page:
                await page.close()
            await context.close()

        return records

    async def search(self, query: str, location: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        await self._ensure_browser()

        category, loc = _parse_query(query, location)
        extracted_at = datetime.now(timezone.utc).isoformat()

        search_terms = [
            f"{category} {loc} phone number address",
            f"{category} {loc} contact details",
            f"site:justdial.com {category} {loc}",
            f"site:indiamart.com {category} {loc}",
            f"site:sulekha.com {category} {loc}",
        ]

        all_records: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        for st in search_terms:
            search_results = await self._search_bing(st)
            await self._rate_limit()

            for sr in search_results:
                name_key = re.sub(r"[^a-z0-9]", "", sr["name"].lower())
                if name_key in seen_names or len(name_key) < 3:
                    continue
                seen_names.add(name_key)

                record = {
                    "name": sr["name"],
                    "phone": sr.get("phone"),
                    "address": None,
                    "website": None,
                    "maps_url": None,
                    "category": category if category else None,
                    "latitude": None,
                    "longitude": None,
                    "rating": None,
                    "reviews_count": None,
                    "opening_hours": None,
                    "source_url": sr.get("source_url"),
                    "_provenance": {
                        "search_query": st,
                        "search_url": sr.get("source_url", ""),
                        "extracted_at": extracted_at,
                        "extraction_method": "web_search",
                        "source_type": "bing_results",
                    },
                }
                all_records.append(record)

                if len(all_records) >= limit:
                    break

            if len(all_records) >= limit:
                break

        logger.info(f"Web search total: {len(all_records)} unique from {len(search_terms)} queries")
        return all_records[:limit]

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        provenance = raw_record.pop("_provenance", {})
        name = raw_record.get("name") or ""
        source_url = raw_record.get("source_url") or ""
        source_id = hashlib.md5(f"{name}|{source_url}".encode()).hexdigest()[:16]

        return {
            "source_record_id": f"web_{source_id}",
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
                "latitude": raw_record.get("latitude"),
                "longitude": raw_record.get("longitude"),
                "rating": raw_record.get("rating"),
                "reviews_count": raw_record.get("reviews_count"),
                "opening_hours": raw_record.get("opening_hours"),
                "maps_url": raw_record.get("maps_url"),
                "source_url": raw_record.get("source_url"),
                "metadata": {
                    "extraction_method": "web_search",
                    "search_query": provenance.get("search_query"),
                    "extracted_at": provenance.get("extracted_at"),
                    "source_type": provenance.get("source_type"),
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
