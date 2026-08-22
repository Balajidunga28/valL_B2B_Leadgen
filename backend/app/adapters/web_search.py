"""
url: /backend/app/adapters/web_search.py
About:
  Bing/DuckDuckGo search adapter with Playwright + httpx fallback. Searches
  for business directory listings. When Playwright is unavailable (Render
  free tier), falls back to httpx HTML parsing via Bing then DuckDuckGo.
  Fully generic — no hardcoded logic.
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
DDG_SEARCH_URL = "https://html.duckduckgo.com/html/"

PER_LISTING_TIMEOUT = 10.0
MAX_RESULTS_PER_QUERY = 50


def _dedup_key(record: dict) -> str:
    name = re.sub(r"[^a-z0-9]", "", (record.get("name") or "").lower().strip())
    phone = re.sub(r"[^0-9]", "", record.get("phone") or "")
    if phone and len(phone) >= 8:
        return hashlib.md5(f"p:{phone}".encode()).hexdigest()
    return hashlib.md5(f"n:{name}".encode()).hexdigest()


def _extract_phones(text: str) -> list[str]:
    phones = []
    for m in re.finditer(r"(?:\+?\d{1,4}[\s\-]?)?\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{3,4}", text):
        phone = re.sub(r"[^0-9+]", "", m.group(0))
        if len(phone) >= 10:
            phones.append(phone)
    return phones


def _extract_business_name_from_snippet(title: str, snippet: str) -> str | None:
    name = title.strip()
    prefixes = ["list of ", "top ", "best ", "directory of ", "find ", "all ", "explore "]
    for p in prefixes:
        if name.lower().startswith(p):
            return None
    skip_phrases = [
        "empanelled", "facilities in india", "across india", "interactive map",
        "contact details and", "world health organization", "who.int",
        "government", "ministry", "cghs", "ayushman",
        "articles", "guides", "tips", "reviews of", "vs ", "comparison",
        "how to", "what is", "benefits of", "cost of", "price of",
        "near me", "list of", "top 10", "best 10",
    ]
    for sp in skip_phrases:
        if sp in name.lower():
            return None
    for sw in GENERIC_SKIP_WORDS:
        if sw in name.lower():
            return None
    if len(name) < 3 or len(name) > 100:
        return None
    name = re.sub(r"\s*[-\u2013|]\s*(?:India|list|directory|contact|guide|article).*$", "", name, flags=re.IGNORECASE).strip()
    return name if len(name) > 2 else None


class WebSearchAdapter(SourceAdapter):
    """Discovers businesses through Bing/DuckDuckGo search results."""

    name = "web_search"
    display_name = "Web Search (Free)"

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
            logger.info("Playwright not available, using httpx fallback for Web Search")
            self._has_playwright = False
        except Exception as e:
            logger.warning("Playwright launch failed: %s, using httpx fallback", e)
            self._has_playwright = False

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    async def _search_bing_httpx(self, query: str, page_num: int = 0) -> list[dict[str, Any]]:
        offset = page_num * 10
        url = f"{BING_SEARCH_URL}?q={quote_plus(query)}&first={offset + 1}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        results = []
        try:
            resp = await self.client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            if resp.status_code != 200:
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select("li.b_algo"):
                title_el = item.select_one("h2 a")
                snippet_el = item.select_one(".b_caption p, .b_algoSlug")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                link = title_el.get("href", "")
                combined = f"{title} {snippet}"
                phones = _extract_phones(combined)
                name = _extract_business_name_from_snippet(title, snippet)
                if name:
                    results.append({
                        "name": name,
                        "phone": phones[0] if phones else None,
                        "source_url": link,
                        "snippet": snippet[:200],
                    })
        except Exception as e:
            logger.debug("Bing httpx error for '%s': %s", query, e)
        return results

    async def _search_ddg_httpx(self, query: str) -> list[dict[str, Any]]:
        """Search DuckDuckGo HTML endpoint — less likely to block datacenter IPs."""
        url = f"{DDG_SEARCH_URL}?q={quote_plus(query)}"
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        results = []
        try:
            resp = await self.client.get(url, headers=headers, follow_redirects=True, timeout=10.0)
            if resp.status_code != 200:
                return []
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(resp.text, "html.parser")
            for item in soup.select(".result"):
                title_el = item.select_one(".result__title")
                snippet_el = item.select_one(".result__snippet")
                link_el = item.select_one(".result__url")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                snippet = snippet_el.get_text(strip=True) if snippet_el else ""
                link = link_el.get_text(strip=True) if link_el else ""
                combined = f"{title} {snippet}"
                phones = _extract_phones(combined)
                name = _extract_business_name_from_snippet(title, snippet)
                if name:
                    results.append({
                        "name": name,
                        "phone": phones[0] if phones else None,
                        "source_url": link,
                        "snippet": snippet[:200],
                    })
        except Exception as e:
            logger.debug("DuckDuckGo httpx error for '%s': %s", query, e)
        return results

    async def _search_bing(self, query: str, page_num: int = 0) -> list[dict[str, Any]]:
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent, viewport={"width": 1920, "height": 1080}, locale="en-US",
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
            for i, r in enumerate(raw_results):
                if i >= MAX_RESULTS_PER_QUERY:
                    break
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

    async def _build_record(self, sr: dict, source_type: str, extracted_at: str, search_query: str) -> dict[str, Any]:
        return {
            "name": sr["name"],
            "phone": sr.get("phone"),
            "address": None,
            "website": None,
            "maps_url": None,
            "category": None,
            "latitude": None,
            "longitude": None,
            "rating": None,
            "reviews_count": None,
            "opening_hours": None,
            "source_url": sr.get("source_url"),
            "_provenance": {
                "search_query": search_query,
                "search_url": sr.get("source_url", ""),
                "extracted_at": extracted_at,
                "extraction_method": "web_search",
                "source_type": source_type,
            },
        }

    async def search(self, query: str, location: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        await self._ensure_browser()
        extracted_at = datetime.now(timezone.utc).isoformat()
        search_terms = [query.strip()]
        all_records: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        def _add_records(results_list, source_type, search_query):
            nonlocal all_records, seen_names
            for sr in results_list:
                name_key = re.sub(r"[^a-z0-9]", "", sr["name"].lower())
                if name_key in seen_names or len(name_key) < 3:
                    continue
                seen_names.add(name_key)
                all_records.append(asyncio.get_event_loop().run_until_complete(
                    self._build_record(sr, source_type, extracted_at, search_query)
                ) if False else {
                    "name": sr["name"], "phone": sr.get("phone"),
                    "address": None, "website": None, "maps_url": None,
                    "category": None, "latitude": None, "longitude": None,
                    "rating": None, "reviews_count": None, "opening_hours": None,
                    "source_url": sr.get("source_url"),
                    "_provenance": {
                        "search_query": search_query, "search_url": sr.get("source_url", ""),
                        "extracted_at": extracted_at, "extraction_method": "web_search",
                        "source_type": source_type,
                    },
                })
                if len(all_records) >= limit:
                    break

        if self._has_playwright and self._browser:
            for st in search_terms:
                search_results = await self._search_bing(st)
                _add_records(search_results, "bing_results", st)
                if len(all_records) >= limit:
                    break
                await self._rate_limit()
        else:
            for st in search_terms:
                bing_results = await self._search_bing_httpx(st)
                if bing_results:
                    _add_records(bing_results, "bing_results", st)
                elif len(all_records) < limit:
                    ddg_results = await self._search_ddg_httpx(st)
                    _add_records(ddg_results, "duckduckgo_results", st)
                if len(all_records) >= limit:
                    break

        logger.info("Web search total: %d unique results", len(all_records))
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
                "city": None, "state": None, "pin_code": None,
                "phone": raw_record.get("phone"), "website": raw_record.get("website"),
                "email": None, "industry": raw_record.get("category"),
                "latitude": raw_record.get("latitude"), "longitude": raw_record.get("longitude"),
                "rating": raw_record.get("rating"), "reviews_count": raw_record.get("reviews_count"),
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
            resp = await self.client.get(BING_SEARCH_URL, timeout=10.0)
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
