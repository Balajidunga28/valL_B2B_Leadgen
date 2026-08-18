<!--
url: /Projects/UI_UX_PLAN_Phase2_v1.0.md
About:
  Phase 2 UI/UX plan for ValLG. Defines all proposed screens, user workflow,
  search form design, source selection, result layouts, lead detail view,
  pipeline visibility, export workflow, loading/empty/error states, pagination,
  source attribution, data quality indicators, and important UX decisions.
  Based on Phase 1 source research findings. Documentation only — no code.
-->

# ValLG — Phase 2 UI/UX Plan

**Version:** 1.0  
**Status:** APPROVED  
**Date:** 2026-08-15  
**Based on:** SOURCE_RESEARCH_v1.0.md, UI_UX_AND_SOURCE_PLAN_v1.0.md, ARCHITECTURE.md, DATABASE.md, API.md

---

## 1. Source Reality Summary (Phase 1 Findings)

Before designing the UI, the following source availability must be reflected in the product:

| Source | Status | Discovery Use | Enrichment Use |
|--------|--------|---------------|----------------|
| Google Places API (New) | APPROVED | Primary — Text Search, Nearby Search | Place Details (phone, website, hours, rating) |
| MCA OGD Bulk Data (India) | APPROVED | India company backbone — CIN, name, status, address | Registration data, capital, state |
| Commercial India API (FileSure/Infyner) | APPROVED | Supplemental search by CIN/name | Directors, financials, GST/PAN, filings |
| Company Websites | APPROVED (constrained) | Not a search source | Contact extraction from discovered websites |
| Google Search / Web Search | CAUTION — Closed to new customers, sunsetting Jan 2027 | Not available for Slice 1 | Not available for Slice 1 |
| Yellow Pages | BLOCKED — No API, ToS prohibits scraping | Not available | Not available |
| LinkedIn | BLOCKED — Active litigation, ToS breach | Not available | Not available |

**UI consequence:** The search form must be designed around Google Places Text Search capabilities, not around the full original source list. Future sources appear as "Coming Soon" placeholders only.

---

## 2. Proposed Navigation Structure

```
┌─────────────────────────────────────────────────────┐
│  Logo   Dashboard   Search   Leads   Companies      │
│          Exports   Settings                         │
└─────────────────────────────────────────────────────┘
```

### Primary Navigation Items

| Nav Item | Purpose | Status |
|----------|---------|--------|
| **Dashboard** | Summary metrics, pipeline activity, recent leads | Slice 1+ |
| **Search** | Create new lead discovery searches | Slice 1 |
| **Leads** | View/manage all discovered leads across searches | Slice 1+ |
| **Companies** | Company-centric view (deduplicated entities) | Slice 2+ |
| **Contacts** | Contact records extracted from companies | Slice 3+ |
| **Exports** | Export history, download, status | Slice 8 |
| **Settings** | Org settings, API keys, source config, usage | Slice 1+ |

### Simplified Navigation for Slice 1

For the first vertical slice, only these are active:

- **Dashboard** (basic metrics from real data)
- **Search** (the primary discovery screen)
- **Settings** (API key configuration)

Leads, Companies, Contacts, and Exports activate in later slices as the pipeline matures.

---

## 3. Search Screen — Primary User Entry Point

### 3.1 Screen Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Search Leads                                                 │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─ Search Criteria ───────────────────────────────────────┐ │
│  │                                                          │ │
│  │  What are you looking for?                              │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │ e.g. "software companies in Bangalore"           │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  │                                                          │ │
│  │  Industry            Country        State/Region        │ │
│  │  ┌──────────────┐   ┌──────────┐   ┌──────────────┐   │ │
│  │  │ Manufacturing│   │ India  ▼ │   │ Karnataka  ▼ │   │ │
│  │  └──────────────┘   └──────────┘   └──────────────┘   │ │
│  │                                                          │ │
│  │  City              Company Size (Coming Soon)  Keywords│ │
│  │  ┌──────────────┐   ┌──────────────────┐  ┌──────────┐│ │
│  │  │ Bangalore  ▼ │   │ 🔒 Not yet       │  │ ERP, CRM││ │
│  │  └──────────────┘   └──────────────────┘  └──────────┘│ │
│  │                                                          │ │
│  │  ── Sources ──────────────────────────────────────────  │ │
│  │  ☑ Google Places    ☐ MCA Data    ☐ Company Websites  │ │
│  │                                                          │ │
│  │  ── Advanced (optional) ──────────────────────────────  │ │
│  │  ▸ Expand for: radius, rating filter, open-now filter  │ │
│  │                                                          │ │
│  │  [ Search Leads ]    [ Save as Template ]               │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Recent Searches ───────────────────────────────────────┐ │
│  │  "IT companies in Pune" — 2h ago — 142 results         │ │
│  │  "Pharma companies in Hyderabad" — 1d ago — 87 results │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Search Form Fields — Mapped to Source Capabilities

Every search field must correspond to an actual capability of the approved sources. Fields that no approved source supports are excluded or clearly marked as future.

| Form Field | Type | Google Places Mapping | MCA Data Mapping | Notes |
|------------|------|----------------------|------------------|-------|
| **Free-text query** | Text input | `textQuery` — e.g. "software companies in Bangalore" | Not supported | Primary search input. Google Places Text Search. |
| **Industry / Category** | Dropdown + text | `includedType` (Table A type) or free-text in query | `Company Category`, `Company Class` | Google Places uses predefined types. MCA uses company classification. |
| **Country** | Dropdown | Location restriction bias (lat/lng viewport) | `Registered State` | Google Places doesn't have a country field — uses location bias. |
| **State / Region** | Dropdown | Location restriction bias | `Registered State`, `RoC` | Same — location bias for Google. Direct field for MCA. |
| **City** | Dropdown + text | Free-text in query, location bias | Not in bulk data | Google Places handles city in text query. |
| **Company Size** | Dropdown (ranges) | Not available from Places API | Not in MCA bulk data | **APPROVED DECISION: Omit from Slice 1. Show as "Coming Soon" because currently researched sources do not reliably provide employee count.** |
| **Keywords** | Text input | Appended to `textQuery` | Not supported | Additional search terms added to query string. |
| **Minimum Rating** | Slider (1-5) | `minRating` in Nearby Search | N/A | Google Places only. Optional advanced filter. |
| **Open Now** | Checkbox | `openNow` in Nearby Search | N/A | Google Places only. Optional advanced filter. |
| **Search Radius** | Number + unit | `locationBias` radius in Nearby Search | N/A | Meters. For Nearby Search mode. Optional. |

### 3.3 Search Mode Selection

The user chooses how to search:

| Mode | When to Use | Google Places Endpoint | Form Behaviors |
|------|-------------|----------------------|----------------|
| **Keyword Search** | "Find companies matching criteria" | `places:searchText` | Free-text query + optional filters |
| **Nearby Search** | "Find companies near a location" | `places:searchNearby` | Location input + type filter + radius |
| **MCA Lookup** | "Find Indian registered companies" | N/A — MCA OGD data | CIN, company name, or state filter |

Radio buttons or segmented control above the form to switch modes. Default: Keyword Search.

### 3.4 Source Selection and Visibility

```
Sources:
┌─────────────────────────────────────────────────────────┐
│ ☑ Google Places API                                      │
│   Text Search for businesses by query + location         │
│   Fields: name, address, phone, website, rating, type   │
│                                                          │
│ ☐ MCA Company Data (India)                               │
│   Indian registered companies — CIN, name, status        │
│   Fields: CIN, name, status, capital, address            │
│                                                          │
│ ☐ Company Websites                                       │
│   Crawl discovered company websites for contacts         │
│   Fields: emails, phone, team, services (if available)  │
│                                                          │
│ ── Coming Soon ───────────────────────────────────────── │
│ 🔒 Google Web Search — API access pending                │
│ 🔒 Yellow Pages — Evaluation pending                     │
│ 🔒 LinkedIn — Evaluation pending                         │
└─────────────────────────────────────────────────────────┘
```

**Key UX decisions:**
- Approved sources are selectable with checkboxes.
- Blocked sources show as "Coming Soon" with a brief reason (no false promises).
- Source selection only appears when the source is relevant to the chosen search mode.
- Default: Google Places checked, others unchecked.
- MCA Data checkbox only visible when Country = India.

### 3.5 Search Templates (Approved)

**APPROVED DECISION:** Provide a small set of useful predefined search templates while keeping free-text search as the primary input. Templates reduce friction for common search patterns.

| Template Name | Pre-filled Query | Location | Industry |
|---------------|-----------------|----------|----------|
| IT Companies — Bangalore | "IT services companies in Bangalore" | Bangalore, Karnataka, India | information_technology_company |
| Manufacturing — Pune | "Manufacturing companies in Pune" | Pune, Maharashtra, India | manufacturing |
| Pharma — Hyderabad | "Pharmaceutical companies in Hyderabad" | Hyderabad, Telangana, India | pharmaceutical_company |
| Startups — Bangalore | "Startups in Bangalore" | Bangalore, Karnataka, India | — |
| Consulting — Delhi NCR | "Consulting firms in Delhi NCR" | Delhi NCR, India | consulting |

**Template behavior:**
- Templates appear as clickable chips/pills above or below the search form.
- Clicking a template pre-fills all relevant fields (query, location, industry).
- User can modify any pre-filled field before searching.
- "Custom Search" option clears all fields for free-text entry.
- Templates are configurable in Settings (admin can add/edit/remove).

---

## 4. Google Places Text Search — Workflow Integration

### 4.1 How Text Search Fits the Workflow

The primary user action is: **type what they want, where they want it.**

Example queries:
- "Manufacturing companies in Pune"
- "IT services companies in Bangalore"
- "Pharmaceutical companies in Hyderabad"
- "Restaurants in Mumbai"

### 4.2 Text Search → Form Mapping

| User Intent | Google Places API Parameter | Form Field |
|-------------|---------------------------|------------|
| "software companies in Bangalore" | `textQuery` | Free-text query |
| Limit to Pune area | `locationBias` (circle or rectangle) | City + State dropdowns |
| Only IT companies | `includedType` = "information_technology_company" | Industry dropdown |
| Only highly rated | `minRating` = 4.0 | Rating slider (advanced) |
| Only currently open | `openNow` = true | Open now checkbox (advanced) |

### 4.3 Field Mask Strategy

The UI must not request fields that incur unnecessary billing. The field mask controls which fields are returned and their billing SKU tier.

**Slice 1 Field Mask (Essentials/Pro tier):**
```
places.id,
places.displayName,
places.formattedAddress,
places.postalAddress,
places.location,
places.types,
places.primaryType,
places.nationalPhoneNumber,
places.internationalPhoneNumber,
places.websiteUri,
places.businessStatus,
places.rating,
places.userRatingCount,
places.googleMapsUri
```

**Future enrichment fields (higher SKU tier):**
```
places.currentOpeningHours,
places.priceLevel,
places.photos,
places.reviews,
places.accessibilityOptions
```

The UI should show which fields are available at the current billing tier and visually indicate fields that require upgrade.

### 4.4 Search Result Mapping

Google Places Text Search returns a list of `places` objects. Each place maps to:

| Google Places Field | UI Display Field | Pipeline Field |
|--------------------|-----------------|----------------|
| `places.displayName.text` | Company Name | `company_name` |
| `places.formattedAddress` | Address | `address` |
| `places.postalAddress.addressLines` | Full Address | `address_full` |
| `places.location.latitude/longitude` | Coordinates | `latitude`, `longitude` |
| `places.primaryType` | Industry/Category | `industry` |
| `places.types` | All Categories | `categories` |
| `places.nationalPhoneNumber` | Phone | `phone` |
| `places.internationalPhoneNumber` | Intl Phone | `phone_intl` |
| `places.websiteUri` | Website | `website` |
| `places.businessStatus` | Status | `business_status` |
| `places.rating` | Rating | `rating` |
| `places.userRatingCount` | Review Count | `review_count` |
| `places.googleMapsUri` | Maps Link | `google_maps_url` |
| `places.id` | Place ID (dedup key) | `source_place_id` |

---

## 5. Search Results Layout

### 5.1 Results Table View

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│ Search: "IT companies in Bangalore"                    142 results    [Export] [Save]│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│ ☐ Select All   Filter ▾   Sort ▾   Columns ▾   Source: Google Places (142)        │
│ ─────────────────────────────────────────────────────────────────────────────────── │
│                                                                                     │
│ ☐ │ Company Name          │ Industry    │ Location      │ Phone      │ Website     │
│───┼───────────────────────┼─────────────┼───────────────┼────────────┼─────────────│
│ ☐ │ TechVista Solutions   │ IT Services │ Bangalore, KA │ +91-80...  │ techvista.. │
│   │ ★★★★☆ (4.2)           │             │               │            │             │
│───┼───────────────────────┼─────────────┼───────────────┼────────────┼─────────────│
│ ☐ │ DataPeak Pvt Ltd      │ Software    │ Bangalore, KA │ +91-80...  │ datapeak..  │
│   │ ★★★★☆ (4.5)           │             │               │            │             │
│───┼───────────────────────┼─────────────┼───────────────┼────────────┼─────────────│
│ ☐ │ CloudFirst Inc        │ IT Services │ Bangalore, KA │ —          │ cloudfirst. │
│   │ ★★★☆☆ (3.8)           │             │               │            │             │
│───┴───────────────────────┴─────────────┴───────────────┴────────────┴─────────────│
│                                                                                     │
│ Page 1 of 15   < 1 2 3 ... 15 >                                                    │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 Results Table Columns

| Column | Source | Editable | Sortable | Filterable | Notes |
|--------|--------|----------|----------|------------|-------|
| **Checkbox** | — | Yes | No | No | Multi-select for bulk actions |
| **Company Name** | Google Places `displayName` | No | Yes | No | Primary identifier |
| **Industry** | Google Places `primaryType` | No | Yes | Yes (dropdown) | Category from Places types |
| **Location** | Google Places `formattedAddress` | No | Yes | Yes (dropdown) | City, state extracted |
| **Phone** | Google Places `nationalPhoneNumber` | No | No | No | May be absent |
| **Website** | Google Places `websiteUri` | No | No | No | Clickable link |
| **Rating** | Google Places `rating` | No | Yes | Yes (slider) | Star display |
| **Source** | System | No | Yes | Yes (checkbox) | Which source provided this |
| **Status** | System | No | No | Yes (dropdown) | Pipeline status |
| **Enrichment** | System | No | No | Yes (dropdown) | Enrichment status |
| **Score** | System (future) | No | Yes | Yes (range) | **APPROVED DECISION: "Coming Soon" — no score displayed in Slice 1. Scoring shown only after Slice 7 implementation.** |
| **Actions** | — | No | No | No | View detail, select |

### 5.3 Results View Modes

| Mode | Description | When to Use | Slice |
|------|-------------|-------------|-------|
| **Table** (default) | Sortable data table with all columns | Bulk review, comparison | 1 |
| **Map** (secondary) | Map pins with location data | Geographic discovery | 1 |
| **List** | Card-based layout with key fields | Quick scan, mobile | Future |

**APPROVED DECISION:** Map view is included in Slice 1 as secondary view. Table remains default.

### 5.4 Results Pagination

- **Strategy:** Server-side pagination, 25 results per page (default), options: 25 / 50 / 100.
- **Rationale:** Google Places returns max 20 per page with `nextPageToken`. Server handles pagination transparently.
- **Cursor-based:** Use `nextPageToken` for reliable forward pagination. No random page jumping (Google API limitation).
- **Total count:** Display "Showing 1-25 of 142" where available. Google Places does not always return total count — show "142+" if estimated.

### 5.5 Auto-Refresh Behavior (Approved)

**APPROVED DECISION:** Auto-refresh is OFF by default. Users must manually refresh results.

| Behavior | Setting | Default |
|----------|---------|---------|
| Results auto-refresh when pipeline stages complete | OFF | Default for Slice 1 |
| Manual refresh button available | Always | Always visible |
| Refresh interval (if enabled) | Configurable | N/A for Slice 1 |

**Rationale:** Auto-refresh can be disorienting during active review. Users should control when their view updates. Manual refresh preserves scroll position and selection state.

---

## 6. Lead Detail View

### 6.1 Screen Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│ ← Back to Results                                                    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  TechVista Solutions Pvt Ltd                                        │
│  IT Services · Bangalore, Karnataka, India                          │
│                                                                      │
│  [ Add to Leads ]  [ Export ]  [ View on Google Maps ]              │
│                                                                      │
│  ── Identity ────────────────────────────────────────────────────── │
│  Company Name:    TechVista Solutions Pvt Ltd                       │
│  Industry:        information_technology_company                     │
│  Categories:      IT services, Software development, Consulting     │
│  Place ID:        ChIJN1t_tDeuEmsRUsoyG83frY4                      │
│  Business Status: OPERATIONAL                                        │
│                                                                      │
│  ── Location ────────────────────────────────────────────────────── │
│  Address:         123 MG Road, Bangalore 560001                     │
│  Coordinates:     12.9716° N, 77.5946° E                           │
│  Maps:            [Open in Google Maps →]                           │
│                                                                      │
│  ── Contact ─────────────────────────────────────────────────────── │
│  Phone:           +91-80-2555-1234                                  │
│  Intl Phone:      +91 80 2555 1234                                  │
│  Website:         [techvistasolutions.com →]                        │
│                                                                      │
│  ── Ratings ─────────────────────────────────────────────────────── │
│  Rating:          ★★★★☆ 4.2 / 5.0 (187 reviews)                   │
│                                                                      │
│  ── Source & Provenance ─────────────────────────────────────────── │
│  Source:          Google Places API (New)                            │
│  Retrieved:       2026-08-15 14:30 UTC                              │
│  Pipeline Run:    #1247                                             │
│  Adapter:         google_places_v1                                   │
│  Raw Record ID:   rec_abc123                                        │
│                                                                      │
│  ── Pipeline Status ─────────────────────────────────────────────── │
│  Extract:         ✅ Complete                                       │
│  Clean:           ✅ Complete                                       │
│  Deduplicate:     ✅ Unique (no duplicates found)                   │
│  Validate:        ✅ Valid                                          │
│  Enrichment:      ⏳ Pending (Company Website crawl queued)          │
│  Score:           ⬜ Not started                                    │
│                                                                      │
│  ── Enrichment Data ────────────────────────────────────────────── │
│  (Will show after enrichment completes)                             │
│                                                                      │
│  ── Audit Log ───────────────────────────────────────────────────── │
│  2026-08-15 14:30 — Extracted from Google Places (run #1247)       │
│  2026-08-15 14:31 — Cleaned: phone normalized, address parsed      │
│  2026-08-15 14:31 — Validated: all required fields present          │
│  2026-08-15 14:32 — Enrichment queued: Company Website crawl        │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 Lead Detail Sections

| Section | Fields | Source |
|---------|--------|--------|
| **Identity** | Name, Industry, Categories, Place ID, Business Status | Google Places |
| **Location** | Address, Coordinates, Maps link | Google Places |
| **Contact** | Phone, Intl Phone, Website | Google Places |
| **Ratings** | Rating, Review Count | Google Places |
| **Source & Provenance** | Source name, Retrieved timestamp, Pipeline run ID, Adapter, Raw record ID | System |
| **Pipeline Status** | Stage status for each pipeline step | System |
| **Enrichment Data** | Director names, financials, GST/PAN (from MCA/commercial API) | Future slices |
| **Audit Log** | Timestamped list of all pipeline actions on this record | System |

---

## 7. Pipeline Status — Discovery, Enrichment, Export Separation

### 7.1 Pipeline Stage Visibility

The pipeline is a core UX concept. Users must understand where each lead is in the process.

**Pipeline Progress Bar (per lead or per batch):**

```
Extract → Clean → Deduplicate → Validate → Enrich → Score → Export
  ✅        ✅        ✅           ✅         ⏳        ⬜       ⬜
```

| Stage | UI Label | Status Values | Slice |
|-------|----------|---------------|-------|
| Extract | "Discovery" | Queued, Running, Complete, Failed | 1 |
| Clean | "Cleaning" | Queued, Running, Complete, Failed | 3 |
| Deduplicate | "Deduplication" | Queued, Running, Complete, Failed | 4 |
| Validate | "Validation" | Queued, Running, Complete, Failed | 5 |
| Enrich | "Enrichment" | Queued, Running, Complete, Failed, Partial | 6 |
| Score | "Scoring" | Queued, Running, Complete, Failed | 7 |
| Export | "Export" | Queued, Running, Complete, Failed | 8 |

### 7.2 Three-Phase Separation

The UI separates the pipeline into three user-facing phases:

| Phase | Pipeline Stages | User Action | UI Section |
|-------|----------------|-------------|------------|
| **Discovery** | Extract → Raw → Clean → Deduplicate → Validate | "Find leads" — search and discover | Search screen, Results table |
| **Enrichment** | Enrich → Score | "Improve data" — add contacts, scores | Leads detail, Enrichment screen |
| **Export** | Export | "Use data" — download or sync | Export screen, bulk actions |

This separation maps to the user's mental model:
1. **Find** companies that match my criteria
2. **Improve** the data with contacts and scoring
3. **Use** the qualified leads

---

## 8. Data Quality and Status Indicators

### 8.1 Lead Quality Badges

| Badge | Color | Meaning |
|-------|-------|---------|
| ✅ Valid | Green | Passes all validation rules |
| ⚠️ Needs Review | Yellow | Partially valid, human review recommended |
| ❌ Invalid | Red | Fails critical validation (missing required fields) |
| 🔁 Duplicate | Gray | Identified as duplicate of another lead |
| 📋 Incomplete | Orange | Missing optional but useful fields |
| ⏳ Enriching | Blue | Currently being enriched |

### 8.2 Source Attribution

Every field that came from an external source shows a small source indicator:

```
Company Name: TechVista Solutions        [Google Places]
Phone:        +91-80-2555-1234           [Google Places]
Website:      techvistasolutions.com     [Google Places]
Address:      123 MG Road, Bangalore     [Google Places]
Director:     Rajesh Kumar               [MCA Data]      (future)
GST:          29AABCT1234F1Z5            [FileSure API]  (future)
```

This is critical for trust and compliance. Users must know where each piece of data came from.

### 8.3 Data Completeness Score

Each lead shows a completeness indicator:

```
██████████░░░░  72% complete
```

Completeness components:
- Company name: required (weight: 20%)
- Address: required (weight: 15%)
- Phone: recommended (weight: 15%)
- Website: recommended (weight: 10%)
- Industry: recommended (weight: 10%)
- Email/Contact person: recommended (weight: 15%)
- Financial data: optional (weight: 10%)
- Director/team data: optional (weight: 5%)

---

## 9. Loading, Empty, Error, Rate-Limit, and Partial-Result States

### 9.1 Loading States

| State | UI Treatment |
|-------|-------------|
| **Initial page load** | Skeleton shimmer for table rows (8-10 placeholder rows) |
| **Search in progress** | Progress bar with "Searching Google Places..." text. If MCA involved: "Searching MCA database..." |
| **Enrichment running** | Per-lead spinner with stage label: "Crawling company website..." |
| **Export generating** | Modal with progress bar: "Generating CSV... 45 of 142 records" |

### 9.2 Empty States

| State | UI Treatment |
|-------|-------------|
| **No search yet** | Illustration + "Define your ideal customer profile and start discovering leads" + Search form |
| **Search returned 0 results** | "No companies found matching your criteria. Try broadening your search — expand the location, try different keywords, or adjust industry filters." |
| **No leads yet** | "Your leads list is empty. Run a search to discover leads." |
| **No exports yet** | "No exports yet. Select leads and export them as CSV." |

### 9.3 Error States

| State | UI Treatment |
|-------|-------------|
| **API key missing** | Banner: "Google Places API key not configured. Go to Settings to add your API key." |
| **API key invalid** | Banner: "Google Places API key is invalid. Please check your Settings." |
| **Quota exceeded** | Banner: "Google Places API quota exceeded. Your plan allows X queries/month. Upgrade or wait for quota reset." |
| **Rate limit hit** | Inline message: "Rate limit reached. Retrying in 30 seconds..." with countdown. Auto-resumes. |
| **Partial results** | Warning banner: "Showing partial results. Google Places returned 15 of 20 expected results for this page. Some results may be missing." |
| **Network error** | Full-page error: "Unable to connect. Please check your internet connection." + Retry button |
| **Server error** | Full-page error: "Something went wrong on our end. Error ID: xyz. Our team has been notified." + Retry button |
| **Source unavailable** | Inline per-source: "Google Places API is currently unavailable. Results from this source are暂时 unavailable." |
| **MCA data stale** | Info banner: "MCA data last updated: 2026-07-01. Some company statuses may have changed." |

### 9.4 Rate-Limit UX (Critical for Google Places)

Google Places enforces per-project, per-minute quotas. The UI must handle this gracefully:

1. **Proactive quota display:** Settings screen shows current quota usage bar.
2. **Per-search estimate:** Before searching, show estimated API cost: "This search may use ~5-10 API queries."
3. **Graceful degradation:** If quota is hit mid-search, show partial results with clear explanation.
4. **Queue mode:** If user triggers search during rate limit, queue it and auto-execute when limit resets.

---

## 10. Export Workflow

### 10.1 Export Flow

```
1. User selects leads (checkboxes or "Select All")
   **APPROVED DECISION:** Reasonable initial bulk limit for Slice 1. Limit based on
   API/page constraints — e.g., max 100 leads per export to avoid over-engineering
   bulk operations. Limit adjustable in future slices.
2. Clicks "Export" button
3. Export configuration modal appears:
   ┌─────────────────────────────────────────────┐
   │  Export Leads                                │
   │                                              │
   │  Selected: 25 leads (max 100)               │
   │                                              │
   │  Format:  CSV (additional formats deferred)  │
   │                                              │
   │  Fields:                                     │
   │  ☑ Company Name    ☑ Industry               │
   │  ☑ Address         ☑ Phone                  │
   │  ☑ Website         ☑ Rating                 │
   │  ☑ Source                                   │
   │  ☐ Raw Record ID   ☐ Place ID              │
   │                                              │
   │  Include provenance: ☑ Source attribution    │
   │                                              │
   │  [ Cancel ]              [ Export ]          │
   └─────────────────────────────────────────────┘
4. Export job queued (background)
5. Notification when ready: "Your export of 25 leads is ready."
6. Download button appears in Exports screen
```

**APPROVED DECISION:** CSV is the initial export format for Slice 1. Excel and JSON formats deferred to later phases.

### 10.2 Export History

| Column | Description |
|--------|-------------|
| Export Name | Auto-generated or user-named |
| Date | When export was created |
| Records | Number of leads exported |
| Format | CSV / Excel / JSON |
| Status | Complete / Failed / Processing |
| Size | File size |
| Actions | Download, Delete |

---

## 11. Dashboard

### 11.1 Dashboard Layout

```
┌──────────────────────────────────────────────────────────────────────┐
│  Dashboard                                                           │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐               │
│  │ Total    │ │ Valid    │ │ High     │ │ Exported │               │
│  │ Leads    │ │ Leads    │ │ Score    │ │ Leads    │               │
│  │ 1,247    │ │ 1,102    │ │ 342      │ │ 89       │               │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘               │
│                                                                      │
│  ┌─ Pipeline Activity ─────────┐ ┌─ Recent Leads ─────────────────┐ │
│  │                             │ │                                 │ │
│  │  Extract:   ████████ 1,247  │ │  TechVista - 2h ago           │ │
│  │  Clean:     ███████░ 1,180  │ │  DataPeak - 3h ago            │ │
│  │  Validated: ██████░░ 1,102  │ │  CloudFirst - 5h ago          │ │
│  │  Enriched:  ████░░░░  890   │ │  NetSoft - 1d ago             │ │
│  │  Scored:    ███░░░░░  654   │ │                                 │ │
│  │                             │ │  [ View All → ]                │ │
│  └─────────────────────────────┘ └─────────────────────────────────┘ │
│                                                                      │
│  ┌─ Industry Distribution ────┐ ┌─ Geography Distribution ────────┐ │
│  │  (Pie chart)               │ │  (Bar chart)                    │ │
│  │  IT Services    34%        │ │  Bangalore  ████ 28%           │ │
│  │  Manufacturing  22%        │ │  Pune       ███  18%           │ │
│  │  Pharma         15%        │ │  Mumbai     ██   12%           │ │
│  │  Other          29%        │ │  Other      ███  42%           │ │
│  └────────────────────────────┘ └─────────────────────────────────┘ │
│                                                                      │
│  ┌─ Source Performance ───────┐ ┌─ Quota Usage ───────────────────┐ │
│  │  Google Places: 1,247 leads│ │  Google Places API              │ │
│  │  MCA Data:        0 leads  │ │  ████████░░ 78% used           │ │
│  │  Websites:       89 crawled│ │  Resets: Sep 1, 2026            │ │
│  └────────────────────────────┘ └─────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 11.2 Dashboard Metrics (All from Real Data)

| Metric | Source | Calculation |
|--------|--------|-------------|
| Total Leads | `leads` table | COUNT where org_id = current org |
| Valid Leads | `leads` table | COUNT where validation_status = 'valid' |
| High Score Leads | `lead_scores` table | COUNT where score >= 80 (Slice 7+) |
| Exported Leads | `exports` table | COUNT distinct leads in completed exports |
| Pipeline Activity | `pipeline_runs` table | Per-stage counts for current org |
| Industry Distribution | `companies` table | GROUP BY industry |
| Geography Distribution | `companies` table | GROUP BY city/state |
| Source Performance | `raw_records` table | GROUP BY source_adapter |
| Quota Usage | `usage_records` table | Sum API calls this billing period |

**APPROVED DECISION:** Chart library technology choice deferred to architecture/implementation phase. Dashboard charts (pie, bar) will use whatever library is selected in Phase 3.

---

## 12. Settings Screen

### 12.1 Settings Sections

| Section | Purpose | Slice |
|---------|---------|-------|
| **Organization** | Org name, plan, billing | 1 |
| **API Keys** | Google Places key, commercial API keys | 1 |
| **Sources** | Enable/disable sources, configure adapters | 1 |
| **Users** | Invite/manage team members | 2 |
| **Usage** | API usage, quota, billing | 1 |
| **Exports** | Default export format, field presets | 8 |

### 12.2 API Key Configuration

```
┌──────────────────────────────────────────────────────────────────────┐
│  Settings → API Keys                                                 │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Google Places API                                                   │
│  Status: ✅ Connected (verified 2 min ago)                          │
│  Key:    AIza•••••••••••••••••••••k4R                              │
│  Quota:  78% used this month (7,800 / 10,000 queries)              │
│  [ Update Key ]                                                     │
│                                                                      │
│  FileSure API (India Company Data)                                  │
│  Status: ⬜ Not configured                                          │
│  Key:    [________________]                                          │
│  [ Save ]                                                           │
│                                                                      │
│  Infyner API (India Company Data)                                   │
│  Status: ⬜ Not configured                                          │
│  Key:    [________________]                                          │
│  [ Save ]                                                           │
│                                                                      │
│  ── Coming Soon ──────────────────────────────────────────────────  │
│  🔒 Google Web Search — API access pending                          │
│  🔒 LinkedIn — Evaluation pending                                   │
│  🔒 Yellow Pages — Evaluation pending                               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 13. Important UX Decisions and Rationale

### 13.1 Search Form Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Free-text query as primary input** | Google Places Text Search is the primary discovery engine. It accepts natural language queries. The form should feel like "tell me what you want" not "fill in database fields." |
| **Industry as dropdown + text** | Google Places uses predefined types (Table A). Dropdown provides discoverability. Free-text fallback allows arbitrary queries. |
| **Location as cascading dropdowns** | Country → State → City hierarchy matches both Google Places location bias and MCA data structure. Google Places handles city/region in the text query itself. |
| **Company Size "Coming Soon"** | Neither Google Places nor MCA bulk data provides employee count. Adding it now would be misleading. Display as "Coming Soon" with clear label. |
| **Source selection with checkboxes** | Users should know which sources contribute data. But default to Google Places for simplicity. |
| **Advanced section collapsed by default** | Most users search by keyword + location. Advanced filters (rating, open-now, radius) are power-user features. |
| **Predefined search templates** | Small set of useful templates reduces friction for common search patterns. Free-text remains primary input. Templates configurable in Settings. |

### 13.2 Results Layout Decisions

| Decision | Rationale |
|----------|-----------|
| **Table as default view** | B2B lead review is data-heavy. Tables support comparison, sorting, and scanning. Cards waste vertical space. |
| **Map view included in Slice 1 as secondary** | Geographic discovery benefits from spatial visualization. Useful for "find companies near X" searches. Approved for Slice 1. |
| **Server-side pagination** | Google Places returns 20 results per page with token-based pagination. Client-side pagination of 1000+ leads is impractical. |
| **No infinite scroll** | Table UX with explicit pagination is better for data-heavy B2B workflows. Users need to jump to specific positions. |
| **Source column visible** | Critical for trust. Users must know if a lead came from Google Places or MCA data. Different sources have different reliability. |
| **Score column "Coming Soon"** | No fabricated scores in Slice 1. Column placeholder shown with "Coming Soon" label until Slice 7 scoring is implemented. |

### 13.3 Pipeline Visibility Decisions

| Decision | Rationale |
|----------|-----------|
| **Three-phase separation** | Users think in "Find → Improve → Use" not "Extract → Clean → Deduplicate." Simplify pipeline terminology for the UI. |
| **Per-lead pipeline status** | Users need to know if a specific lead is ready for export. Batch status hides individual lead readiness. |
| **Technical pipeline names in detail view** | Lead detail view is for power users who need full provenance. Show actual pipeline stage names here. |

### 13.4 Data Quality Decisions

| Decision | Rationale |
|----------|-----------|
| **Source attribution on every field** | Compliance requirement. Users must know where each data point came from. Prevents misuse of unverified data. |
| **Completeness score** | Helps users prioritize which leads to enrich further. A 30% complete lead needs more work than a 90% lead. |
| **Never fabricate data** | If a field is empty, show "—" not a placeholder value. Never guess phone numbers, emails, or names. |

### 13.5 State Management Decisions

| Decision | Rationale |
|----------|-----------|
| **Local component state preferred** | Per architecture doc and AI rules. No global state library unless justified. |
| **Loading skeletons over spinners** | Better UX for data-heavy tables. Users see the layout immediately. |
| **Partial results displayed** | If Google Places returns 15 of 20 expected results, show all 15 with a warning. Don't block on partial data. |
| **Auto-refresh OFF by default** | Users control when their view updates. Manual refresh preserves scroll position and selection state. Less disorienting during active review. |

---

## 14. Complete Screen Inventory

| Screen | Slice | Purpose |
|--------|-------|---------|
| **Dashboard** | 1 | Overview metrics, pipeline activity, recent leads |
| **Search** | 1 | Create new lead discovery searches |
| **Search Results** | 1 | View results from a search run |
| **Lead Detail** | 1 | View full details of a single lead |
| **Settings → API Keys** | 1 | Configure source API keys |
| **Settings → Sources** | 1 | Enable/disable/configure sources |
| **Settings → Usage** | 1 | View quota usage and billing |
| **Leads** | 2 | Browse all leads across searches |
| **Companies** | 2 | Company-centric deduplicated view |
| **Contacts** | 3 | Contact records from companies |
| **Enrichment** | 6 | Trigger and monitor enrichment jobs |
| **Lead Scoring** | 7 | Configure and view scoring |
| **Exports** | 8 | Export history, downloads |

---

## 15. User Flow Summary

### Primary Flow (Slice 1)

```
1. User navigates to Search screen
2. Enters search criteria (query + location + optional filters)
3. Selects sources (default: Google Places)
4. Clicks "Search Leads"
5. Backend creates pipeline run → Extract via Google Places API
6. Results appear in table as they are processed
7. User reviews results, clicks into Lead Detail
8. User sees pipeline status (Extract ✅, Clean ✅, etc.)
9. User selects leads, clicks "Export"
10. Exports CSV with chosen fields
11. Downloads file from Exports screen
```

### Enrichment Flow (Slice 6+)

```
1. User navigates to Leads screen
2. Filters to leads needing enrichment
3. Selects leads, clicks "Enrich"
4. Backend runs enrichment pipeline:
   - Company website crawl (contact extraction)
   - MCA data lookup (director details)
   - Commercial API call (financials, GST)
5. Enrichment results appear in lead detail
6. User reviews enriched data
7. Proceeds to scoring or export
```

---

## 16. Approved Decisions (Phase 2)

The following decisions were approved on 2026-08-15:

| # | Decision | Resolution |
|---|----------|------------|
| 1 | **Company Size** | Omit from Slice 1. Show "Coming Soon" because currently researched sources do not reliably provide employee count. |
| 2 | **Map View** | Include in Slice 1 as secondary results view. Table remains default. |
| 3 | **Search Templates** | Provide a small set of useful predefined templates while keeping free-text search as the primary input. Templates configurable in Settings. |
| 4 | **Chart Library** | Do not lock in a chart library during Phase 2. Defer the technology choice to the architecture/implementation phase (Phase 3). |
| 5 | **Lead Scoring** | Do not fabricate scores in Slice 1. Show scoring as "Coming Soon" / not available until the scoring capability is actually implemented (Slice 7). |
| 6 | **Export Format** | CSV is the initial export format for Slice 1. Excel and JSON formats deferred to a later phase. |
| 7 | **Bulk Selection** | Use a reasonable initial limit based on API/page constraints (e.g., max 100 leads per export). Do not over-engineer bulk operations in Slice 1. Limit adjustable in future slices. |
| 8 | **Auto-Refresh** | Off by default. Users can manually refresh results. Manual refresh preserves scroll position and selection state. |

---

**END OF PHASE 2 UI/UX PLAN** — Approved. Ready to proceed to Phase 3 (Architecture/Data/API Plan) upon user approval.
