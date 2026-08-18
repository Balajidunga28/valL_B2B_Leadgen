<!--
url: /Projects/SOURCE_RESEARCH_v1.0.md
About:
  Documents the Phase 1 Domain & Source Research findings for ValLG's 6 required
  discovery sources (including Google Search/Web Search added per user request).
  Covers permitted access methods, API availability, authentication, fields, India
  coverage, rate limits, terms/restrictions, technical feasibility, and legal/
  compliance considerations. Distinguishes verified facts from assumptions and
  unresolved questions. This is a research deliverable — no implementation code.
-->

# ValLG — Source Research Report (Phase 1)

**Version:** 1.0  
**Status:** COMPLETE — Research Only  
**Date:** 2026-08-15

---

## Executive Summary

Research conducted on all 6 required source categories per `UI_UX_AND_SOURCE_PLAN_v1.0.md`, `PROJECT_PLAN.md`, and user request (Google Search/Web Search added). Each source evaluated against the Source Verification Gate criteria.

| Source | Verdict | Primary Access Method | Legal Risk |
|--------|---------|----------------------|------------|
| Google Maps / Google Places | ✅ **APPROVED** | Official REST API (Places API New) | Low — Official licensed API |
| **Google Search / Web Search** | ⚠️ **CAUTION** | Custom Search JSON API (closed to new customers; sunsetting Jan 1, 2027) | Medium — API access restricted, scraping prohibited, litigation active |
| Yellow Pages (YP.com / Thryv) | ❌ **BLOCKED** | No official public API; scraping prohibited by ToS | High — ToS prohibits automated collection |
| Public LinkedIn Information | ❌ **BLOCKED** | Official API (restricted); scraping prohibited by ToS | High — Active litigation, ToS breach risk |
| Company Websites | ✅ **APPROVED (with constraints)** | HTTP/HTML (respect robots.txt, terms) | Medium — Varies by site; respect ToS/robots.txt |
| Open Business Directories (India) | ✅ **APPROVED** | Official MCA OGD bulk data/API; commercial APIs available | Low — Official government open data license |

---

## 1. Google Maps / Google Places

### Verified Facts (from Official Google Documentation)

**API Endpoints (Places API New — recommended over Legacy):**
- `POST https://places.googleapis.com/v1/places:searchText` — Text Search
- `POST https://places.googleapis.com/v1/places:searchNearby` — Nearby Search
- `GET https://places.googleapis.com/v1/places/{place_id}` — Place Details
- `POST https://places.googleapis.com/v1/places:autocomplete` — Autocomplete

**Authentication:** API Key (via `X-Goog-Api-Key` header) or OAuth 2.0. Requires Google Cloud project with Places API enabled and billing configured.

**Field Mask Required:** Every request MUST specify `X-Goog-FieldMask` header listing desired fields. No default fields returned. Billing based on highest SKU tier in field mask.

**Key Fields Available (B2B-relevant):**
- `places.displayName` — Business name
- `places.formattedAddress` / `places.postalAddress` — Full address
- `places.location` — Lat/long
- `places.types` / `places.primaryType` — Business category (Table A types)
- `places.nationalPhoneNumber` / `places.internationalPhoneNumber` — Phone
- `places.websiteUri` — Website URL
- `places.rating` / `places.userRatingCount` — Ratings
- `places.businessStatus` — OPEN, CLOSED_TEMPORARILY, CLOSED_PERMANENTLY
- `places.currentOpeningHours` — Hours
- `places.priceLevel` — Price tier
- `places.plusCode` — Location code
- `places.googleMapsUri` — Google Maps link
- `places.photos` — Photo references
- `places.reviews` — Reviews (Enterprise SKU)
- `places.accessibilityOptions` — Accessibility (Pro SKU)

**India Coverage:** Full coverage. India-specific pricing applies (up to 70% lower than global). Address descriptors generally available for India customers.

**Rate Limits / Quotas (per project, per method, per minute):**
- Text Search: 600 RPM (configurable up to 1000+)
- Nearby Search: 600 RPM
- Place Details: 600 RPM
- Autocomplete: 600 RPM
- Quota limits enforced; service stops responding when exceeded

**Pricing (India, effective March 1, 2025 — free monthly thresholds):**
| SKU Category | Free Monthly | Price (Cap–5M) | Price (5M+) |
|--------------|--------------|----------------|-------------|
| Essentials (Text Search IDs Only, Place Details IDs Only) | Unlimited | $0 | $0 |
| Essentials (Text Search, Place Details Location) | 70,000 | $1.50/1k | $0.38/1k |
| Pro (Text Search, Nearby Search, Place Details) | 35,000 | $9.60/1k | $2.40/1k |
| Enterprise (Text Search, Nearby Search, Place Details + Atmosphere) | 7,000 | $10.50–12.00/1k | $2.63–3.40/1k |

**Terms/Restrictions:**
- Must comply with Google Maps Platform Terms of Service
- No caching of place data beyond 30 days (except place IDs)
- Must display Google attribution where required
- No redistribution of raw API data as a competing service
- India pricing requires billing account with India as primary country and majority usage in India

**Technical Feasibility:** ✅ **HIGH** — Official REST API, well-documented, field-level billing control, India-optimized pricing, supports text queries like "software companies in Bangalore" with location bias/restriction.

**Legal/Compliance:** ✅ **LOW RISK** — Licensed API usage. Must enable billing, monitor quota, respect caching limits.

**Unresolved Questions:**
- Exact monthly volume estimates for ValLG usage (affects cost tier)
- Whether Essentials SKU (IDs only + separate Place Details calls) is sufficient vs Pro/Enterprise for enrichment needs
- Google Cloud project setup and billing account creation process

---

## 2. Google Search / Web Search

### Verified Facts (from Official Google Documentation)

**API Offerings (Programmable Search Engine — 4 variants):**

| Offering | Implementation | Cost | Daily Limit | Availability |
|----------|---------------|------|-------------|--------------|
| Standard Search Element | Client-side JS | Free | No limit | Everyone |
| Non-profit Search Element | Client-side JS | Free | No limit | Non-profits only |
| Paid Search Element | Client-side JS | $5/1000 queries | No limit | Everyone |
| **Custom Search JSON API** | **Server-side REST** | **$5/1000 queries** | **10,000/day** | **Closed to new customers** |

**Custom Search JSON API — Primary Programmatic Option:**
- Endpoint: `GET https://www.googleapis.com/customsearch/v1`
- Required params: `key` (API key), `cx` (Programmable Search Engine ID), `q` (query)
- Response: JSON with `items[]` (results), `searchInformation`, `queries`, `context`
- Result fields: `title`, `link`, `displayLink`, `snippet`, `htmlSnippet`, `pagemap` (structured data: Schema.org, OpenGraph, etc.), `mime`, `fileFormat`

**Search Capabilities Relevant to B2B Lead Discovery:**
- Full web search with standard Google operators (`site:`, `filetype:`, `intitle:`, `inurl:`)
- Site-restricted search (up to 10 specific domains via Site Restricted API)
- Date range filtering (`dateRestrict`: d[ays], w[eeks], m[onths], y[ears])
- Language (`hl`), country (`gl`), safe search, exact/exclude terms
- Pagination via `start` parameter (10 results per page, up to 100 results)
- Image search (`searchType=image`)

**Authentication:** API Key + Programmable Search Engine ID (`cx`). Requires Google Cloud project.

**India/Geography Coverage:** Global Google index. Country biasing via `gl` parameter (e.g., `gl=in` for India). Language via `hl` (e.g., `hl=en`).

**Rate Limits / Quotas:**
- **Custom Search JSON API:** 100 free queries/day, then $5/1000 queries, **hard cap 10,000 queries/day**
- To exceed 10k/day: Enable billing in GCP Console + request quota increase
- **Site Restricted JSON API:** No daily limit (ceased Jan 8, 2025 — transition to Vertex AI Search)
- Standard/Paid Search Elements: No daily limit (client-side only)

**Pricing (Custom Search JSON API):**
- Free tier: 100 queries/day
- Paid: $5 per 1,000 queries (no volume discounts)
- Monthly cost at 10k/day cap: ~$1,485/month
- Billed in USD to GCP billing account

**Critical Status — SUNSETTING:**
> "The following pricing applies only to **existing Custom Search JSON API customers until the service discontinuation on January 1, 2027. This API is not available for new customers.**" — Google Developers (2026-02-18)

**Stated Replacement:** **Vertex AI Agent Search** (Google Cloud) — fundamentally different product:
- Per-query + per-GB-indexed pricing (not flat $5/1k)
- Free trial: 10,000 queries/month
- Production pricing not published as simple per-thousand table
- Requires choosing pricing model first (General vs Configurable)

**Terms/Restrictions (Custom Search JSON API Additional Terms):**
- Must accept Google APIs ToS + Programmable Search Engine ToS + Additional Terms
- **Prohibited:** Cache results beyond cache headers, frame/modify/filter/reorder results, commingle with non-Google results, display in pop-ups, show to third parties, access outside designated Site
- **Prohibited:** Automated query generation (robots, macros, click spam), create substitute service, store/cache results non-transitorily
- **Prohibited:** Remove Google copyright/branding, disparage Google
- Google may terminate/discontinue at any time without liability
- Liability capped at $1,000

**Technical Feasibility:** ⚠️ **MEDIUM-LOW** —
- API technically works for existing customers until Jan 1, 2027
- **NEW CUSTOMERS CANNOT SIGN UP** — blocked from onboarding
- 10k/day hard limit insufficient for SaaS-scale lead discovery
- Vertex AI Agent Search is not a drop-in replacement (different architecture, opaque pricing)
- Third-party SERP APIs (SerpAPI, Scrappa, etc.) available but add vendor dependency

**Legal/Compliance:** ⚠️ **MEDIUM RISK** —
- **Direct scraping of google.com violates Google ToS** — Google actively litigating (SerpApi DMCA lawsuit 2026, court dismissed main claims but case continues)
- Custom Search JSON API usage is contractually permitted (for existing customers)
- Third-party SERP APIs shift compliance burden to vendor but add cost/vendor risk
- No caching allowed beyond transient display

**Unresolved Questions:**
- **Can ValLG get Custom Search JSON API access?** (Closed to new customers — may need Google Cloud sales contact)
- **Vertex AI Agent Search viability:** Pricing, migration effort, feature parity for B2B lead queries
- **Third-party SERP API selection:** Cost comparison (SerpAPI $25/1k vs Scrappa ~$0.30/1k), reliability, data freshness
- **Query volume estimate:** B2B lead discovery may need 100k–1M queries/month — exceeds 10k/day cap

---

## 3. Yellow Pages (YP.com / Thryv)

## 2. Yellow Pages (YP.com / Thryv)

### Verified Facts

**Official API:** ❌ **NO PUBLIC API** — YellowPages.com (Thryv, Inc.) does not publish a general-purpose public API for third-party business search.

**Terms of Service (https://www.yellowpages.com/about/legal/terms-conditions):**
- Section 2.1: **"Data Mining/Scraping and Framing Prohibited. You may not use bots, scrapers, crawlers, spiders, or any similar methods, processes, or tools to 'data mine' or otherwise gather or extract data from the YP Sites"**
- Requires "prior express consent" from Thryv, Inc. for any automated collection
- Consent "may be withdrawn at any time, with or without notice"
- Limited license granted only for "individual, non-commercial, informational purposes"

**robots.txt:** Restricts crawler paths (specific paths not verified in research; assume restrictive based on ToS).

**Unofficial "APIs":** Third-party scrapers exist on RapidAPI, Apify, etc. — **NOT affiliated with Yellow Pages**, violate ToS, service continuity and legal posture vary widely.

**Legal Precedent:** hiQ v. LinkedIn (9th Cir. 2022) held CFAA doesn't criminalize public data access, **but** Yellow Pages ToS breach claim remains viable (contract law). Yellow Pages can terminate access, pursue civil remedies.

**India Coverage:** YP.com is **US-focused**. Yellow Pages India (yellowpages.in) exists but separate entity — terms unknown.

**Technical Feasibility:** ⚠️ **LOW** — No official API. Scraping technically possible (server-rendered HTML) but:
- Violates ToS explicitly
- Rate limiting, CAPTCHA, IP blocking employed
- Legal risk: breach of contract, potential trespass to chattels
- No guaranteed data quality or continuity

**Legal/Compliance:** ❌ **HIGH RISK** — ToS explicitly prohibits automated collection. Commercial use requires written permission/licensing from Thryv. No evidence of available licensing program for third-party SaaS.

**Unresolved Questions:**
- Whether Thryv offers commercial data licensing (contact sales?)
- Yellow Pages India (yellowpages.in) terms — separate evaluation needed
- Whether "public business facts" (name, address, phone) extraction at small scale changes risk profile

---

## 3. Public LinkedIn Information

### Verified Facts

**Official API:** ✅ **EXISTS BUT RESTRICTED** — LinkedIn Marketing API, Sales Navigator API, Recruiter API, Learning API. Requires:
- LinkedIn Partner Program approval (application, review, contract)
- Specific use case approval (marketing, recruiting, sales, learning)
- Rate limits per partner tier
- Data fields strictly limited to approved scopes

**Terms of Service — User Agreement Section 8.2:**
- "Develop, support or use software, devices, scripts, robots or any other means or processes (such as crawlers, browser plugins and add-ons or any other technology) to scrape or copy the Services, including profiles and other data from the Services" — **PROHIBITED**

**Crawling Terms (https://www.linkedin.com/legal/crawling-terms):**
- "Automated Crawling & Indexing without the express permission of LinkedIn is strictly prohibited"
- Permitted use confined to "search indexing for display in a publicly available search engine"
- LinkedIn may revoke permission at any time

**API Terms of Use:**
- Section 24: "Access, store, display, or facilitate the transfer of any LinkedIn content obtained through... scraping, crawling, spidering or using any other technology or software to access LinkedIn content outside the APIs... prohibited"
- Applies whether obtained directly or through third parties

**Legal Landscape (2025–2026):**
- **hiQ v. LinkedIn (2022):** CFAA doesn't criminalize public profile scraping (9th Circuit)
- **BUT:** District court found hiQ **breached LinkedIn User Agreement** (contract law)
- hiQ settled: paid $500K, permanently barred from scraping, deleted all data, destroyed code
- **Proxycurl (Nubela) sued by LinkedIn/Microsoft Jan 2025** — operated 100K+ fake accounts, $10M ARR, **shut down by July 2025**
- LinkedIn actively pursues commercial scraping services via CFAA + ToS breach + copyright + injunctions

**GDPR/Privacy:** EU/UK profiles = personal data. Requires lawful basis (legitimate interest assessment), Article 14 notices, RoPA entry, opt-out/suppression list. India DPDP Act 2023 may apply.

**Technical Feasibility:** ⚠️ **LOW FOR SCRAPING, MEDIUM FOR OFFICIAL API** —
- Scraping: Technically feasible (public profiles viewable) but **high legal/operational risk**
- Official API: Requires partnership approval, limited fields, not designed for general B2B lead gen

**Legal/Compliance:** ❌ **HIGH RISK** for scraping. Active litigation against commercial scrapers. ToS breach enforceable. Fake account usage = clear violation. GDPR/DPDP exposure for EU/India personal data.

**Unresolved Questions:**
- Whether LinkedIn Partner Program would approve ValLG use case (B2B lead gen SaaS)
- Exact data fields available via approved APIs vs. public profile fields
- Cost and volume limits for approved partners

---

## 4. Company Websites

### Verified Facts

**Access Method:** HTTP/HTTPS requests to company websites. HTML parsing (BeautifulSoup, lxml) or headless browser (Playwright, Selenium) for JS-rendered content.

**robots.txt:** Standard mechanism. MUST check per domain. Example patterns:
- `User-agent: *` / `Disallow: /` — blocks all
- `Disallow: /admin/`, `/private/` — partial
- `Crawl-delay: 10` — rate limit hint

**Terms of Service:** Varies by site. Common restrictions:
- No automated access/scraping
- No commercial reuse of content
- Rate limits, IP blocking for abusive access

**Technical Feasibility:** ✅ **MEDIUM-HIGH** —
- Most B2B sites are server-rendered (accessible via plain HTTP)
- Contact pages, about pages, team pages often contain: company name, address, phone, email, leadership, services
- JS-heavy sites (React, Vue, Angular) require headless browser (higher cost, slower)
- No standard schema — each site unique structure

**Fields Typically Available:**
- Company name, tagline
- Address (HQ, offices)
- Phone, email (generic: info@, sales@, contact@)
- Leadership team (names, titles, sometimes LinkedIn links)
- Services/products
- Case studies, clients
- Technologies (from job postings, stack pages)
- Social media links

**India Coverage:** Universal — any company with a website.

**Rate Limits / Best Practices:**
- Respect `robots.txt` and `Crawl-delay`
- Implement exponential backoff, random delays (1–5s)
- Rotate user agents
- Handle 429, 403, 5xx gracefully
- Cache results (respect freshness)

**Legal/Compliance:** ⚠️ **MEDIUM RISK** —
- Public facts (name, address, phone) generally not copyrightable
- But: compilation, presentation, creative content protected
- ToS breach risk if site prohibits scraping
- India: DPDP Act 2023 — personal data (individual names, emails) requires lawful basis
- Telecom/spam rules (TRAI) — unsolicited commercial communication restrictions
- Best practice: Only extract business contact info (role-based: sales@, hr@), avoid personal emails

**Unresolved Questions:**
- Scale: How many company websites to crawl per pipeline run?
- Prioritization: Which websites (from Google Places results? MCA data?)
- Freshness: Re-crawl frequency?
- JavaScript rendering budget (headless browser cost)

---

## 5. Open Business Directories (India Focus)

### Verified Facts

#### A. MCA Company Master Data (Official Government Source)
**Source:** Ministry of Corporate Affairs via Open Government Data (OGD) Platform India  
**URL:** https://data.gov.in/catalog/company-master-data  
**Access Model:** Catalog API (CKAN) + ZIP bulk download  
**License:** Government Open Data License (NDSAP) — worldwide, royalty-free, non-exclusive, commercial use permitted  
**Attribution Required:** Must cite provider, source, license, DOI/URL  
**Non-endorsement:** Cannot imply government endorsement  
**No Warranty:** Provider not liable for errors/omissions

**Fields (Company Master Data):**
- CIN (Corporate Identification Number) — unique key
- Company Name
- Company Status (Active, Strike Off, Liquidation, etc.)
- Company Class (Private, Public, One Person, etc.)
- Company Category (Company limited by shares, guarantee, etc.)
- Authorized Capital (INR)
- Paid-up Capital (INR)
- Date of Registration
- Registered State
- Registrar of Companies (RoC)
- Registered Office Address
- **NO contact emails/phones, NO director details in bulk master data**

**Coverage:** 3.5M+ companies/LLPs registered in India (as of 2025)

**Rate Limits:** Catalog API typical CKAN limits; bulk download unrestricted

**Technical Feasibility:** ✅ **HIGH** — Official bulk data, machine-readable (CSV/JSON), open license, India-comprehensive

**Legal/Compliance:** ✅ **LOW RISK** — Government open data license explicitly permits commercial use with attribution

#### B. MCA Company/LLP Master Data Service (Live Portal)
**URL:** https://www.mca.gov.in/content/mca/global/en/mca/master-data/MDS/company-master-info.html  
**Access:** Web search (CAPTCHA protected), not a scraping license  
**Use Case:** Live verification of CIN/status/address  
**Limitation:** Portal access ≠ bulk scraping license

#### C. Commercial Indian Business Data APIs
| Provider | Access | Pricing | Key Features |
|----------|--------|---------|--------------|
| **FileSure** (api.filesure.in) | REST API, token auth | ₹5/call (reads), ₹330 unlock/year | MCA master, directors, charges, filings, financial extractions; sandbox free |
| **Infyner** (infyner.com) | REST API, token auth | ~₹1/credit, search free daily | Company search, CIN/DIN/GST/PAN verification, financials, directors, compliance |
| **SensiBook** (sensibook.com) | REST API, key auth | 1 credit=₹1, 100 free credits | 36L+ companies, full financials, shareholding, directors, charges |
| **CompanyData** (companydata.com) | REST API, bulk, platform | €25/mo API, €425/1k contacts | 30M+ Indian businesses, 50+ fields, enriched with global intel |

**All commercial APIs:** Primary sources (MCA21, GSTN, Income Tax, EPFO, IBBI, MSME, courts). No scraping. Source attribution per field.

#### D. Procurement / Regulator Sources (Enrichment)
- **GeM** (Government e Marketplace): Supplier/buyer data — GeM terms
- **CPPP** (Central Public Procurement Portal): Tenders/awards — portal terms
- **SEBI**: Listed company filings — SEBI terms
- **IP India**: Trademarks/patents — IP India terms
- **IBBI**: Insolvency orders — regulator terms

**Technical Feasibility:** ✅ **HIGH** for MCA OGD bulk + commercial APIs. Official, structured, licensed.

**Legal/Compliance:** ✅ **LOW RISK** for MCA OGD (open license). Commercial APIs — contractual, licensed. **DPDP Act 2023 applies** — director/signatory personal data requires lawful basis. MCA data ≠ marketing consent database.

**Unresolved Questions:**
- Which commercial API best fits ValLG cost/volume/fields needs?
- MCA bulk data freshness (snapshot vs. live) — how often to refresh?
- Whether MCA bulk data includes enough fields for lead qualification (no contacts, no tech stack)

---

## Source Verification Gate Checklist

| Criterion | Google Places | **Google Search** | Yellow Pages | LinkedIn | Company Websites | India Open Dirs |
|-----------|---------------|-------------------|--------------|----------|------------------|-----------------|
| What it provides | Places/Businesses | **Web search results (SERP)** | Business listings | Professional profiles | Company web content | Company registry + enrichment |
| Geographic coverage | Global (India strong) | **Global (Google index)** | US primarily | Global | Global | India comprehensive |
| Search capabilities | Text, Nearby, Type | **Full web ops, site restrict, date, pagination** | Category/City (web) | People/Jobs/Companies (API) | Ad-hoc per site | CIN search, bulk download |
| Available fields | Rich (name, addr, phone, web, rating, hours, type) | **Title, URL, snippet, pagemap (structured data)** | Name, addr, phone, category | Name, title, company, skills, exp | Unstructured, variable | CIN, name, status, capital, address, filings |
| Auth/API requirements | API Key + Billing | **API Key + CSE ID (closed to new)** | None (no public API) | Partner Program (strict) | None (HTTP) | OGD: open; Commercial: API key |
| Terms/Permissions | Google Maps ToS | **CSE ToS (sunset 2027), no caching, no automation** | **Prohibits scraping** | **Prohibits scraping** | Per-site ToS/robots.txt | NDSAP/OGD License (permissive) |
| Rate limits | 600 RPM/method | **100 free/day, 10k/day hard cap** | Anti-bot, CAPTCHA | Strict API limits | Per-site (respect robots.txt) | API: provider limits; Bulk: none |
| Cost | Pay-as-you-go (India pricing) | **$5/1k (existing only), Vertex AI: opaque** | N/A (licensing?) | Partner pricing | Compute/bandwidth | OGD: free; Commercial: per-call |
| Failure modes | Quota exceeded, billing | **Quota cap, API sunset, 403/429** | IP block, legal | Account ban, lawsuit | 403, 429, structure change | API downtime, data lag |
| Provenance strategy | Place ID, timestamp, API version | **Query, timestamp, CSE ID, result rank** | N/A | N/A | URL, timestamp, selector version | CIN, dataset version, source attribution |
| Adapter design | REST client + field mask | **REST client (CSE) / Vertex AI / 3rd-party SERP** | **Not recommended** | Official API only (if approved) | HTTP + parser per pattern | Bulk loader + API clients |

---

## Recommendations for First Vertical Slice (Slice 1 — Discovery/Extract)

### ✅ **APPROVED SOURCES — Implement First**

1. **Google Places API (New)** — Primary discovery engine
   - Text Search for "industry + location" queries (e.g., "manufacturing companies in Pune")
   - Nearby Search for area-based discovery
   - Place Details for enrichment (website, phone, rating, hours)
   - Field mask control keeps costs predictable
   - India pricing favorable
   - **Adapter: REST client with field mask config, exponential backoff, quota tracking**

2. **MCA Company Master Data (OGD India)** — Authoritative India company backbone
   - Bulk CSV/JSON download for initial seed
   - Catalog API for incremental updates
   - CIN as canonical deduplication key
   - **Adapter: Bulk loader (CSV/JSON) + CKAN API client for updates**

3. **Commercial India API (select one)** — Contact/enrichment layer
   - Recommend **FileSure** or **Infyner** for: director details, financials, charges, filings, GST/PAN verification
   - Per-call pricing, sandbox for dev, source-attributed fields
   - **Adapter: REST client with credit/wallet management**

### ⚠️ **CAUTION — Defer, Restrict, or Evaluate Alternatives**

4. **Google Search / Web Search** — **Do not implement Custom Search JSON API for new customers**
   - **API closed to new signups; sunsetting Jan 1, 2027**
   - 10k/day hard limit insufficient for SaaS-scale discovery
   - Vertex AI Agent Search: Not drop-in replacement, opaque pricing, migration required
   - **Alternative for Slice 1:** Use Google Places Text Search as primary discovery (covers "industry + location" queries with structured Place data)
   - **Future consideration:** If web-search-specific queries needed (e.g., "site:linkedin.com CEO Bangalore"), evaluate third-party SERP APIs (SerpAPI, Scrappa, etc.) or apply for Vertex AI Agent Search access
   - **Adapter (if needed later):** Pluggable SERP client interface supporting multiple backends

5. **Company Websites** — Supplemental enrichment only
   - Crawl only websites returned by Google Places / MCA data
   - Respect robots.txt strictly
   - Extract only business-contact fields (role-based emails, phone, address)
   - Rate limit aggressively (1 req/5s/domain)
   - **Adapter: Polite HTTP crawler with robots.txt parser, domain-level rate limiting**

### ❌ **BLOCKED / NOT APPROVED**

6. **Yellow Pages (YP.com)** — Do not implement
   - No official API, ToS prohibits scraping, US-focused, high legal risk
   - Alternative: Use Google Places + MCA data for US entities if needed later

7. **Public LinkedIn Scraping** — Do not implement
   - Active litigation, ToS breach, high operational risk (account bans)
   - Alternative: If LinkedIn data needed, apply for LinkedIn Partner Program (separate initiative)

---

## Implementation Priority for Slice 1

| Priority | Source | Adapter Type | Effort |
|----------|--------|--------------|--------|
| 1 | Google Places API (New) | REST + Field Mask | Medium |
| 2 | MCA OGD Bulk Data | CSV/JSON Loader | Low |
| 3 | Commercial India API (FileSure/Infyner) | REST + Auth | Medium |
| 4 | Company Websites (polite crawl) | HTTP + Parser | High (per-site variance) |
| — | Google Search (CSE JSON API) | **Not recommended for new customers** | — |

---

## Next Steps (Require Approval)

1. **Select Commercial India API Provider** — FileSure vs Infyner vs SensiBook vs CompanyData (evaluate fields, pricing, SLA)
2. **Google Cloud Project Setup** — Create project, enable Places API (New), configure billing, generate API key
3. **Define Field Masks** — Which Place fields per SKU tier (Essentials vs Pro vs Enterprise) for cost/value optimization
4. **MCA Bulk Download Strategy** — Initial full load + incremental sync frequency
5. **Adapter Interface Design** — Common `DataSourceAdapter` abstraction before coding

---

**END OF PHASE 1 RESEARCH** — Awaiting approval to proceed to Phase 2 (UI/UX Plan) or Phase 3 (Architecture/Data/API Plan) per `PROJECT_PLAN.md` vertical slice gates.