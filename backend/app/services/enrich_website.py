"""
url: /backend/app/services/enrich_website.py
About:
  Website-based enrichment. Scrapes company websites to extract
  industry, description, social links, founded year, company size,
  and contact information. Uses httpx for HTTP and BeautifulSoup for parsing.
   Timeout: 5 seconds per request. Best-effort — failures return None.
"""

import re
import logging
from typing import Any
from urllib.parse import urljoin, urlparse

logger = logging.getLogger(__name__)

# Social media domain patterns
_SOCIAL_PATTERNS = {
    "facebook": r"https?://(?:www\.)?facebook\.com/[^\s\"'<>]+",
    "twitter": r"https?://(?:www\.)?twitter\.com/[^\s\"'<>]+",
    "linkedin": r"https?://(?:www\.)?linkedin\.com/(?:company|in)/[^\s\"'<>]+",
    "instagram": r"https?://(?:www\.)?instagram\.com/[^\s\"'<>]+",
    "youtube": r"https?://(?:www\.)?youtube\.com/(?:channel|c|user)/[^\s\"'<>]+",
}

# Industry keywords for meta tag / title analysis
_INDUSTRY_KEYWORDS = {
    "hospital": "Healthcare",
    "medical": "Healthcare",
    "health": "Healthcare",
    "clinic": "Healthcare",
    "pharma": "Healthcare",
    "diagnostic": "Healthcare",
    "eye": "Healthcare",
    "dental": "Healthcare",
    "surgical": "Healthcare",
    "nursing": "Healthcare",
    "care": "Healthcare",
    "school": "Education",
    "college": "Education",
    "university": "Education",
    "academy": "Education",
    "institute": "Education",
    "engineering": "Education",
    "restaurant": "Food & Beverage",
    "hotel": "Hospitality",
    "travel": "Travel & Tourism",
    "bank": "Finance",
    "finance": "Finance",
    "insurance": "Finance",
    "IT": "Technology",
    "software": "Technology",
    "technology": "Technology",
    "digital": "Technology",
    "tech": "Technology",
    "retail": "Retail",
    "store": "Retail",
    "shop": "Retail",
    "manufacturing": "Manufacturing",
    "construction": "Construction",
    "real estate": "Real Estate",
    "legal": "Legal Services",
    "law": "Legal Services",
    "accounting": "Accounting",
    "ca": "Accounting",
}


def _clean_text(text: str | None) -> str | None:
    """Clean scraped text: strip whitespace, remove excessive newlines."""
    if not text:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


async def scrape_website(url: str) -> dict[str, Any]:
    """Scrape a company website to extract enrichment data.

    Returns a dict with:
    - industry: detected industry
    - description: meta description or first paragraph
    - social_links: dict of social media URLs
    - founded_year: year if found
    - company_size: size range if found
    - email: contact email if found
    - technologies: list of detected technologies
    - raw_title: page title
    - raw_meta: meta tags
    """
    result: dict[str, Any] = {}
    source_label = f"website:{url}"

    try:
        import httpx
        async with httpx.AsyncClient(
            timeout=5.0,
            follow_redirects=True,
            headers={"User-Agent": "ValLG/1.0 (Enrichment Bot)"},
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning("Website %s returned %d", url, resp.status_code)
                return {"error": f"HTTP {resp.status_code}", "source": source_label}

            html = resp.text
    except ImportError:
        logger.warning("httpx not installed — skipping website scrape")
        return {"error": "httpx not installed", "source": source_label}
    except Exception as e:
        logger.warning("Failed to fetch %s: %s", url, e)
        return {"error": str(e), "source": source_label}

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
    except ImportError:
        logger.warning("beautifulsoup4 not installed — using regex fallback")
        soup = None

    if soup:
        # --- Title ---
        title_el = soup.find("title")
        if title_el:
            result["raw_title"] = _clean_text(title_el.get_text())

        # --- Meta description ---
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            result["description"] = _clean_text(meta_desc.get("content"))

        # --- Meta keywords (industry hint) ---
        meta_keywords = soup.find("meta", attrs={"name": "keywords"})
        if meta_keywords:
            kw = _clean_text(meta_keywords.get("content"))
            if kw:
                result["meta_keywords"] = kw

        # --- About / description from body ---
        if not result.get("description"):
            # Try common about sections
            for selector in ["about", "about-us", "关于我们", "#about"]:
                about = soup.find(id=selector) or soup.find(class_=re.compile(r"about", re.I))
                if about:
                    text = about.get_text(separator=" ", strip=True)
                    result["description"] = _clean_text(text[:500])
                    break

        # --- Social links ---
        social_links = {}
        page_text = str(soup)
        for platform, pattern in _SOCIAL_PATTERNS.items():
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                # Deduplicate and clean
                seen = set()
                for m in matches:
                    m = m.rstrip("/").rstrip('"').rstrip("'")
                    if m not in seen:
                        seen.add(m)
                        social_links[platform] = m
                        break
        if social_links:
            result["social_links"] = social_links
            result["social_links_source"] = source_label

        # --- Founded year ---
        year_patterns = [
            r"(?:founded|established|since|est\.?)\s*(?:in\s*)?(\d{4})",
            r"©\s*\d{4}\s*[-–]\s*(\d{4})",
            r"(\d{4})\s*[-–]\s*(?:present|till|today)",
        ]
        body_text = soup.get_text(separator=" ", strip=True)[:5000]
        for pattern in year_patterns:
            m = re.search(pattern, body_text, re.IGNORECASE)
            if m:
                year = m.group(1)
                if 1900 <= int(year) <= 2026:
                    result["founded_year"] = year
                    result["founded_year_source"] = source_label
                    break

        # --- Company size ---
        size_patterns = [
            r"(\d+[\-\+]?\d*)\s*(?:employees?|staff|team members?)",
            r"(?:team of|workforce of)\s*(\d+[\-\+]?\d*)",
        ]
        for pattern in size_patterns:
            m = re.search(pattern, body_text, re.IGNORECASE)
            if m:
                result["company_size"] = m.group(0).strip()
                result["company_size_source"] = source_label
                break

        # --- Email ---
        email_pattern = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, page_text)
        # Filter out common non-business emails
        filtered = [e for e in emails if not any(x in e.lower() for x in
                    ["example.com", "sentry.io", "wixpress.com", "w3.org",
                     "schema.org", "googleapis.com", "jquery"])]
        if filtered:
            result["email"] = filtered[0]
            result["email_source"] = source_label

        # --- Industry from meta / title ---
        title_text = (result.get("raw_title") or "").lower()
        kw_text = (result.get("meta_keywords") or "").lower()
        combined = f"{title_text} {kw_text}"
        for keyword, industry in _INDUSTRY_KEYWORDS.items():
            if keyword.lower() in combined:
                result["industry"] = industry
                result["industry_source"] = source_label
                break

    else:
        # Regex fallback without BeautifulSoup
        # Extract title
        m = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
        if m:
            result["raw_title"] = _clean_text(m.group(1))

        # Extract meta description
        m = re.search(r'<meta\s+name=["\']description["\']\s+content=["\']([^"\']+)', html, re.IGNORECASE)
        if m:
            result["description"] = _clean_text(m.group(1))

        # Social links from raw HTML
        social_links = {}
        for platform, pattern in _SOCIAL_PATTERNS.items():
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                social_links[platform] = matches[0].rstrip("/").rstrip('"').rstrip("'")
        if social_links:
            result["social_links"] = social_links
            result["social_links_source"] = source_label

    result["source"] = source_label
    return result
