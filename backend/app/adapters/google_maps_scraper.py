"""
url: /backend/app/adapters/google_maps_scraper.py
About:
  Google Maps scraper adapter for ValLG. Uses Playwright for browser automation
  to extract business listings from Google Maps. Implements the SourceAdapter
  interface for integration with the existing discovery pipeline.
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
from app.geo import (
    INDIAN_STATES_LOWER,
    is_state_name,
)

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

MAPS_URL = "https://www.google.com/maps"

PER_LISTING_TIMEOUT = 10.0
MAX_LISTINGS_PER_QUERY = 50


def _extract_location_from_address(address: str) -> tuple[str | None, str | None, str | None]:
    if not address:
        return None, None, None
    city = None
    state = None
    pin_code = None
    pm = re.search(r"\b(\d{6})\b", address)
    if pm:
        pin_code = pm.group(1)
    if is_state_name(address.split(",")[-1].strip() if "," in address else ""):
        state = address.split(",")[-1].strip()
    addr_parts = [p.strip() for p in address.split(",")]
    if len(addr_parts) >= 2:
        second = addr_parts[-2].strip()
        if re.match(r"^[A-Za-z\s]+$", second) and len(second) > 2 and not is_state_name(second):
            city = second
    if not city and addr_parts:
        for part in reversed(addr_parts):
            part_clean = part.strip()
            if re.match(r"^[A-Za-z\s]+$", part_clean) and len(part_clean) > 2:
                if not is_state_name(part_clean) and part_clean.lower() != "india":
                    city = part_clean
                    break
    return city, state, pin_code


def _parse_query(query: str, location: str | None) -> tuple[str, str]:
    for pat in [r"^(.+?)\s+(?:in|near|around|at|of)\s+(.+)$", r"^(.+?)\s*[-]\s*(.+)$"]:
        m = re.match(pat, query, re.IGNORECASE)
        if m:
            cat = m.group(1).strip()
            loc_from_query = m.group(2).strip()
            if location:
                return cat, location.strip()
            return cat, loc_from_query
    if location:
        return query.strip(), location.strip()
    return query.strip(), ""


def _dedup_key(record: dict) -> str:
    name = re.sub(r"[^a-z0-9]", "", (record.get("name") or "").lower().strip())
    phone = re.sub(r"[^0-9]", "", record.get("phone") or "")
    if phone and len(phone) >= 8:
        return hashlib.md5(f"p:{phone}".encode()).hexdigest()
    return hashlib.md5(f"n:{name}".encode()).hexdigest()


class GoogleMapsScraperAdapter(SourceAdapter):
    """Scrapes Google Maps for business listings via Playwright."""

    name = "google_maps_scraper"
    display_name = "Google Maps Scraper"

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
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            self._has_playwright = True
        except ImportError:
            logger.info("Playwright not available, Google Maps scraper will not function")
            self._has_playwright = False
        except Exception as e:
            logger.warning("Playwright launch failed: %s", e)
            self._has_playwright = False

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(self.delay_min, self.delay_max))

    def _build_maps_url(self, query: str) -> str:
        return f"{MAPS_URL}/search/{quote_plus(query)}"

    async def _scroll_results_panel(self, page, max_scrolls: int = 15):
        selector = 'div[role="feed"]'
        panel = await page.query_selector(selector)
        if not panel:
            return
        prev_count = 0
        for _ in range(max_scrolls):
            await page.evaluate(
                """(sel) => { const el = document.querySelector(sel); if (el) el.scrollTop = el.scrollHeight; }""",
                selector,
            )
            await page.wait_for_timeout(800)
            items = await page.query_selector_all('div[role="feed"] > div > div > a[href*="/maps/place"]')
            if len(items) == prev_count:
                break
            prev_count = len(items)

    async def _extract_listings(self, page, max_listings: int = 50) -> list[dict[str, Any]]:
        records = []
        feed_links = await page.query_selector_all('div[role="feed"] > div > div > a[href*="/maps/place"]')
        for i, link_el in enumerate(feed_links):
            if i >= max_listings:
                break
            try:
                record = await asyncio.wait_for(
                    self._extract_single_listing(link_el),
                    timeout=PER_LISTING_TIMEOUT,
                )
                if record:
                    records.append(record)
            except asyncio.TimeoutError:
                logger.debug(f"Timeout extracting listing {i}, skipping")
                continue
            except Exception as e:
                logger.debug(f"Error extracting listing {i}: {e}")
                continue
        return records

    async def _extract_single_listing(self, link_el) -> dict[str, Any] | None:
        """Extract a single listing with timeout protection."""
        href = await link_el.get_attribute("href") or ""
        name_el = await link_el.query_selector('span')
        name = (await name_el.inner_text()).strip() if name_el else None
        if not name or len(name) < 2:
            return None
        parent_text = await link_el.evaluate("""el => {
            const p = el.parentElement;
            return p ? (p.innerText || '') : '';
        }""")
        lines = [l.strip() for l in parent_text.split("\n") if l.strip()]
        rating = None
        reviews_count = None
        category = None
        address = None
        phone = None
        hours = None
        for ln in lines:
            rm = re.match(r"^([\d.]+)$", ln)
            if rm:
                try:
                    rating = float(rm.group(1))
                except ValueError:
                    pass
                continue
            if re.search(r"[·•⋅]", ln):
                parts = re.split(r"\s*[·•⋅]\s*", ln)
                parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]
                has_hours = any("open" in p.lower() or "close" in p.lower() for p in parts)
                if has_hours:
                    for p in parts:
                        pl = p.lower()
                        if "open" in pl or "close" in pl:
                            hours = p
                        elif re.match(r"^[\d\s\-\+()]{7,}$", p):
                            phone = p
                elif not category and parts:
                    category = parts[0] if len(parts[0]) < 50 else None
                    addr_parts = [p for p in parts[1:] if p and not re.match(r"^[\s\d\W]+$", p)]
                    if addr_parts:
                        address = ", ".join(addr_parts)
                continue
            if not phone and re.match(r"^\+?[\d][\d\s\-()]{6,}$", ln):
                phone = ln
        rating_el = await link_el.evaluate_handle("el => el.parentElement")
        if rating_el and rating is None:
            try:
                label = await rating_el.evaluate("""p => {
                    const img = p ? p.querySelector('[role="img"][aria-label*="star"]') : null;
                    return img ? img.getAttribute('aria-label') : null;
                }""")
                if label:
                    m = re.search(r"([\d.]+)\s*star.*?([\d,]+)\s*[Rr]eview", label)
                    if m:
                        rating = float(m.group(1))
                        reviews_count = int(m.group(2).replace(",", ""))
                    else:
                        m2 = re.search(r"([\d.]+)", label)
                        if m2:
                            rating = float(m2.group(1))
            except Exception:
                pass
        if reviews_count is None:
            for ln in lines:
                m = re.match(r"^([\d,]+)\s*[Rr]eview", ln)
                if m:
                    reviews_count = int(m.group(1).replace(",", ""))
                    break
        name_clean = re.split(r"\s*[\|:\-]\s*", name)[0].strip()
        if name_clean and len(name_clean) > 2:
            name = name_clean
        if address:
            address = re.sub(r"^[^\w\d]+", "", address).strip()
            if not address:
                address = None
        lat = None
        lng = None
        m = re.search(r"!3d([-\d.]+)!4d([-\d.]+)", href)
        if m:
            lat = float(m.group(1))
            lng = float(m.group(2))
        record = {
            "name": name,
            "address": address,
            "phone": phone,
            "website": None,
            "rating": rating,
            "reviews_count": reviews_count,
            "category": category,
            "opening_hours": hours,
            "latitude": lat,
            "longitude": lng,
            "maps_url": href if "maps/place" in href else None,
        }
        return record

    async def _search_single_query(self, search_query: str, limit: int, extracted_at: str) -> list[dict[str, Any]]:
        user_agent = random.choice(USER_AGENTS)
        context = await self._browser.new_context(
            user_agent=user_agent,
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
            timezone_id="Asia/Kolkata",
        )
        await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => false });")
        records = []
        page = None
        try:
            page = await context.new_page()
            search_url = self._build_maps_url(search_query)
            await page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(4000)
            content = await page.content()
            if "unusual traffic" in content.lower():
                logger.warning("Google Maps blocked the request")
                return []
            await self._scroll_results_panel(page, max_scrolls=20)
            raw_records = await self._extract_listings(page)
            for rec in raw_records[:limit]:
                rec["_provenance"] = {
                    "search_query": search_query,
                    "search_url": search_url,
                    "extracted_at": extracted_at,
                    "browser": "chromium",
                    "extraction_method": "google_maps_scraper",
                    "user_agent": user_agent,
                }
                records.append(rec)
        except Exception as e:
            logger.error(f"Google Maps scraper error for '{search_query}': {e}")
        finally:
            if page:
                await page.close()
            await context.close()
        return records

    async def search(self, query: str, location: str | None = None, limit: int = 20, offset: int = 0) -> list[dict[str, Any]]:
        await self._ensure_browser()
        if not self._has_playwright or not self._browser:
            logger.warning("Playwright not available, Google Maps scraper cannot run")
            return []

        extracted_at = datetime.now(timezone.utc).isoformat()

        # The user's query IS the search — no variation generation
        search_queries = [query.strip()]

        all_records: list[dict[str, Any]] = []
        seen_keys: set[str] = set()

        for i, sq in enumerate(search_queries):
            remaining = limit - len(all_records)
            if remaining <= 0:
                break
            records = await self._search_single_query(sq, remaining + 5, extracted_at)
            for rec in records:
                dk = _dedup_key(rec)
                if dk not in seen_keys:
                    seen_keys.add(dk)
                    all_records.append(rec)
            if i < len(search_queries) - 1:
                await self._rate_limit()

        logger.info(f"Google Maps Scraper total: {len(all_records)} unique from {len(search_queries)} queries")
        return all_records[:limit]

    def normalize(self, raw_record: dict[str, Any]) -> dict[str, Any]:
        provenance = raw_record.pop("_provenance", {})
        name = raw_record.get("name") or ""
        maps_url = raw_record.get("maps_url") or ""
        source_id = hashlib.md5(f"{name}|{maps_url}".encode()).hexdigest()[:16]
        address = raw_record.get("address") or ""
        city, state, pin_code = _extract_location_from_address(address)
        return {
            "source_record_id": f"gmaps_scraper_{source_id}",
            "raw_data": {
                "name": raw_record.get("name"),
                "address": address,
                "city": city,
                "state": state,
                "pin_code": pin_code,
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
                "source_url": raw_record.get("maps_url") or provenance.get("search_url"),
                "metadata": {
                    "extraction_method": provenance.get("extraction_method", "google_maps_scraper"),
                    "search_query": provenance.get("search_query"),
                    "extracted_at": provenance.get("extracted_at"),
                    "maps_url": raw_record.get("maps_url"),
                },
            },
        }

    async def health_check(self) -> bool:
        if not self._has_playwright:
            return False
        try:
            resp = await self.client.get("https://www.google.com/maps", timeout=10.0)
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