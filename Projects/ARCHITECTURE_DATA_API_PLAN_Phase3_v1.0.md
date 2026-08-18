<!--
url: /Projects/ARCHITECTURE_DATA_API_PLAN_Phase3_v1.0.md
About:
  Phase 3 Architecture/Data/API Plan for ValLG. Defines the complete system
  architecture, data model, API contracts, source adapter design, security
  controls, scalability approach, technology decisions, and Phase 4 implementation
  boundaries. Based on Phase 1 source research and Phase 2 UI/UX plan. Planning
  documentation only — no application code.
-->

# ValLG — Phase 3 Architecture / Data / API Plan

**Version:** 1.0  
**Status:** PLANNING — Awaiting approval  
**Date:** 2026-08-15  
**Based on:** SOURCE_RESEARCH_v1.0.md, UI_UX_PLAN_Phase2_v1.0.md, ARCHITECTURE.md, DATABASE.md, API.md, SECURITY.md

---

## Table of Contents

1. [Overall System Architecture](#1-overall-system-architecture)
2. [Data Architecture](#2-data-architecture)
3. [API Architecture](#3-api-architecture)
4. [Source Adapter Architecture](#4-source-adapter-architecture)
5. [Security and Compliance](#5-security-and-compliance)
6. [Scalability and Operations](#6-scalability-and-operations)
7. [Technology Decisions](#7-technology-decisions)
8. [Phase 4 Implementation Boundaries](#8-phase-4-implementation-boundaries)

---

## 1. Overall System Architecture

### 1.1 System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              USER                                       │
│                     (Browser / Mobile Browser)                          │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ HTTPS
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                         │
│                     React + TypeScript                                  │
│                     Tailwind CSS                                        │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │Dashboard │ │ Search   │ │ Leads    │ │ Exports  │ │ Settings │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└─────────────────────────┬───────────────────────────────────────────────┘
                          │ REST API (JSON)
                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND API                                         │
│                     FastAPI + Python                                     │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│  │Auth/RBAC │ │Search/   │ │Pipeline  │ │Exports   │ │Usage/    │    │
│  │          │ │Discovery │ │Runs      │ │          │ │Billing   │    │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘    │
└───────┬─────────────┬─────────────────────┬─────────────────────────────┘
        │             │                     │
        ▼             ▼                     ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────────────────────────────┐
│ PostgreSQL   │ │Background    │ │External APIs                         │
│ (Supabase)   │ │Worker        │ │                                      │
│              │ │              │ │ ┌────────────┐ ┌──────────────────┐ │
│ ┌──────────┐ │ │ ┌──────────┐│ │ │Google      │ │Commercial India  │ │
│ │Auth/Users│ │ │ │Extract   ││ │ │Places API  │ │API (FileSure/    │ │
│ │Companies │ │ │ │Clean     ││ │ │            │ │Infyner)          │ │
│ │Contacts  │ │ │ │Dedup     ││ │ └────────────┘ └──────────────────┘ │
│ │Leads     │ │ │ │Validate  ││ │ ┌────────────┐ ┌──────────────────┐ │
│ │Pipeline  │ │ │ │Enrich    ││ │ │MCA OGD     │ │Company Websites  │ │
│ │Exports   │ │ │ │Score     ││ │ │Bulk Data   │ │(polite crawl)    │ │
│ │Usage     │ │ │ │Export    ││ │ └────────────┘ └──────────────────┘ │
│ └──────────┘ │ │ └──────────┘│ │                                      │
└──────────────┘ └──────────────┘ └──────────────────────────────────────┘
```

### 1.2 Component Responsibilities

| Component | Responsibility | Technology (Confirmed) |
|-----------|---------------|------------------------|
| **Frontend** | User interface, form handling, result display, state management | React, TypeScript, Tailwind CSS |
| **Backend API** | Request handling, auth, validation, business logic, API orchestration | Python, FastAPI |
| **Database** | Persistent storage, multi-tenant data, query optimization | PostgreSQL (Supabase optional) |
| **Background Worker** | Long-running pipeline jobs, scheduled tasks | Python (job abstraction) |
| **External APIs** | Data sources for discovery and enrichment | Google Places, MCA OGD, Commercial APIs |

### 1.3 Deployment Architecture (Proposed)

| Environment | Purpose | Infrastructure |
|-------------|---------|----------------|
| **Development** | Local development | Docker Compose (frontend + backend + DB) |
| **Staging** | Pre-production testing | Single cloud instance or managed services |
| **Production** | Live service | Cloud hosting with managed PostgreSQL |

**Technology note:** Specific cloud provider (AWS/GCP/Azure/Vercel/Railway) is a Phase 4 decision. Docker ensures environment consistency.

### 1.4 Authentication and Authorization Flow

```
User Login
    │
    ▼
Frontend (login form)
    │ POST /api/auth/login
    ▼
Backend Auth Service
    │ Validate credentials
    │ Create session / issue JWT
    │ Determine organization_id
    ▼
Response: { token, user, organization }
    │
    ▼
Frontend stores token
    │ Authorization: Bearer <token>
    ▼
Backend Middleware
    │ 1. Validate token
    │ 2. Resolve user → organization
    │ 3. Attach org context to request
    │ 4. Check permission for endpoint
    ▼
Handler executes with org-scoped context
```

**Key rules:**
- Organization ID is derived server-side from the authenticated user, never from client request.
- Every database query is scoped to the user's organization.
- Frontend is never a security boundary.

---

## 2. Data Architecture

### 2.1 Core Entity Model (Conceptual)

```
Organizations
    │
    ├── Users/Memberships
    │
    ├── Companies (deduplicated entities)
    │       │
    │       ├── Contacts (people at companies)
    │       │
    │       └── EnrichmentData (per-source enrichment)
    │
    ├── PipelineRuns (search sessions)
    │       │
    │       └── RawRecords (per-source extracted data)
    │               │
    │               └── CleanedRecords
    │                       │
    │                       └── Leads (validated, scored)
    │
    ├── Exports (export history)
    │
    └── UsageRecords (API usage tracking)
```

### 2.2 Entity Definitions — Fields Based on Researched Source Capabilities

Every field below is mapped to an actual source capability. No invented fields.

#### 2.2.1 Organizations

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `name` | VARCHAR(255) | Yes | Organization name |
| `slug` | VARCHAR(100) | Yes | URL-friendly identifier, unique |
| `plan` | ENUM | Yes | `free`, `starter`, `pro`, `enterprise` |
| `created_at` | TIMESTAMP | Yes | |
| `updated_at` | TIMESTAMP | Yes | |

#### 2.2.2 Users

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | → organizations.id |
| `email` | VARCHAR(255) | Yes | Unique per org |
| `password_hash` | VARCHAR(255) | Yes | bcrypt/argon2 |
| `name` | VARCHAR(255) | Yes | Display name |
| `role` | ENUM | Yes | `admin`, `member`, `viewer` |
| `is_active` | BOOLEAN | Yes | Default true |
| `created_at` | TIMESTAMP | Yes | |
| `last_login_at` | TIMESTAMP | No | |

#### 2.2.3 Companies (Deduplicated Entities)

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `id` | UUID | Yes | System | Primary key |
| `organization_id` | UUID FK | Yes | System | Tenant ownership |
| `name` | VARCHAR(500) | Yes | Google Places `displayName`, MCA `Company Name` | Normalized |
| `domain` | VARCHAR(255) | No | Google Places `websiteUri` | Extracted from website URL |
| `industry` | VARCHAR(255) | No | Google Places `primaryType`, MCA `Company Category` | |
| `categories` | TEXT[] | No | Google Places `types` | Array of category strings |
| `address` | TEXT | No | Google Places `formattedAddress`, MCA `Registered Office Address` | Full address |
| `city` | VARCHAR(255) | No | Parsed from address | |
| `state` | VARCHAR(255) | No | Parsed from address or MCA `Registered State` | |
| `country` | VARCHAR(100) | No | Parsed from address | Default: India |
| `latitude` | DECIMAL(10,7) | No | Google Places `location.latitude` | |
| `longitude` | DECIMAL(10,7) | No | Google Places `location.longitude` | |
| `phone` | VARCHAR(50) | No | Google Places `nationalPhoneNumber` | Normalized |
| `phone_intl` | VARCHAR(50) | No | Google Places `internationalPhoneNumber` | |
| `website` | VARCHAR(500) | No | Google Places `websiteUri` | |
| `rating` | DECIMAL(2,1) | No | Google Places `rating` | 1.0–5.0 |
| `review_count` | INTEGER | No | Google Places `userRatingCount` | |
| `business_status` | VARCHAR(50) | No | Google Places `businessStatus` | OPERATIONAL, CLOSED, etc. |
| `google_maps_url` | VARCHAR(500) | No | Google Places `googleMapsUri` | |
| `source_place_id` | VARCHAR(255) | No | Google Places `id` | Dedup key for Google Places |
| `source_cin` | VARCHAR(20) | No | MCA `CIN` | Dedup key for MCA data |
| `completeness_score` | DECIMAL(5,2) | No | System | Calculated field |
| `created_at` | TIMESTAMP | Yes | System | |
| `updated_at` | TIMESTAMP | Yes | System | |

**Indexes:**
- `organization_id` (tenant scoping)
- `domain` (dedup lookup)
- `source_place_id` (Google Places dedup)
- `source_cin` (MCA dedup)
- `name` + `organization_id` (search)
- `city` + `state` (geographic queries)

**Unique constraint:** `organization_id` + `domain` (when domain is not null), `organization_id` + `source_place_id` (when not null), `organization_id` + `source_cin` (when not null)

#### 2.2.4 Contacts

| Field | Type | Required | Source | Notes |
|-------|------|----------|--------|-------|
| `id` | UUID | Yes | System | Primary key |
| `organization_id` | UUID FK | Yes | System | Tenant ownership |
| `company_id` | UUID FK | Yes | System | → companies.id |
| `name` | VARCHAR(255) | No | Company website crawl, MCA (directors) | Person name |
| `title` | VARCHAR(255) | No | Company website crawl | Job title |
| `email` | VARCHAR(255) | No | Company website crawl | Role-based preferred (info@, sales@) |
| `phone` | VARCHAR(50) | No | Company website crawl, MCA | |
| `linkedin_url` | VARCHAR(500) | No | Company website crawl | Only if voluntarily listed |
| `source` | VARCHAR(100) | Yes | System | `website_crawl`, `mca_director`, `commercial_api` |
| `source_url` | VARCHAR(500) | No | System | Where this contact was found |
| `is_decision_maker` | BOOLEAN | No | System | Heuristic based on title |
| `created_at` | TIMESTAMP | Yes | System | |
| `updated_at` | TIMESTAMP | Yes | System | |

**Indexes:**
- `organization_id` (tenant scoping)
- `company_id` (company → contacts lookup)
- `email` + `organization_id` (contact dedup)

#### 2.2.5 Pipeline Runs

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `user_id` | UUID FK | Yes | Who initiated |
| `name` | VARCHAR(255) | No | User-provided search name |
| `query_text` | TEXT | Yes | Original search query |
| `query_params` | JSONB | Yes | Full search parameters (location, filters, sources) |
| `status` | ENUM | Yes | `queued`, `running`, `completed`, `failed`, `partial` |
| `sources_used` | TEXT[] | Yes | Which sources were queried |
| `total_extracted` | INTEGER | No | Count of raw records extracted |
| `total_cleaned` | INTEGER | No | |
| `total_deduplicated` | INTEGER | No | |
| `total_valid` | INTEGER | No | |
| `total_enriched` | INTEGER | No | |
| `error_message` | TEXT | No | If failed |
| `started_at` | TIMESTAMP | No | |
| `completed_at` | TIMESTAMP | No | |
| `created_at` | TIMESTAMP | Yes | |

#### 2.2.6 Raw Records (Per-Source Extracted Data)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `pipeline_run_id` | UUID FK | Yes | → pipeline_runs.id |
| `company_id` | UUID FK | No | → companies.id (linked after dedup) |
| `source_adapter` | VARCHAR(100) | Yes | e.g., `google_places_v1`, `mca_ogd`, `filesure_v1` |
| `source_record_id` | VARCHAR(255) | No | External ID (Place ID, CIN, etc.) |
| `raw_data` | JSONB | Yes | Complete unprocessed source response |
| `normalized_data` | JSONB | No | Mapped to common schema |
| `status` | ENUM | Yes | `extracted`, `cleaning`, `cleaned`, `deduped`, `validated`, `failed` |
| `error_message` | TEXT | No | |
| `retrieved_at` | TIMESTAMP | Yes | When data was fetched from source |
| `created_at` | TIMESTAMP | Yes | |

**Notes:**
- `raw_data` preserves the complete source response for provenance and reprocessing.
- `normalized_data` is the mapped-to-common-schema version.
- This record is never deleted — it's the audit trail.

#### 2.2.7 Leads (Validated, Scored)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `company_id` | UUID FK | Yes | → companies.id |
| `pipeline_run_id` | UUID FK | Yes | → pipeline_runs.id |
| `raw_record_id` | UUID FK | Yes | → raw_records.id |
| `validation_status` | ENUM | Yes | `valid`, `invalid`, `needs_review`, `duplicate` |
| `validation_issues` | JSONB | No | Array of validation issues found |
| `enrichment_status` | ENUM | Yes | `pending`, `running`, `complete`, `failed`, `partial` |
| `lead_score` | DECIMAL(5,2) | No | Populated by Slice 7 scoring |
| `score_version` | VARCHAR(50) | No | Scoring model version |
| `score_components` | JSONB | No | Explainable score breakdown |
| `exported_at` | TIMESTAMP | No | When first exported |
| `created_at` | TIMESTAMP | Yes | |
| `updated_at` | TIMESTAMP | Yes | |

**Indexes:**
- `organization_id` (tenant scoping)
- `company_id` (company → leads lookup)
- `pipeline_run_id` (run → leads lookup)
- `validation_status` + `organization_id` (filtering)
- `lead_score` + `organization_id` (sorting/filtering)

#### 2.2.8 Enrichment Data

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `company_id` | UUID FK | Yes | → companies.id |
| `lead_id` | UUID FK | No | → leads.id (if lead-specific) |
| `source_adapter` | VARCHAR(100) | Yes | Which enrichment source |
| `source_record_id` | VARCHAR(255) | No | External ID from enrichment source |
| `enrichment_type` | VARCHAR(100) | Yes | `directors`, `financials`, `contacts`, `website_crawl` |
| `data` | JSONB | Yes | Enrichment payload |
| `retrieved_at` | TIMESTAMP | Yes | |
| `expires_at` | TIMESTAMP | No | When this data becomes stale |
| `created_at` | TIMESTAMP | Yes | |

#### 2.2.9 Exports

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `user_id` | UUID FK | Yes | Who initiated |
| `name` | VARCHAR(255) | No | Auto-generated or user-named |
| `format` | ENUM | Yes | `csv` (Slice 1), `xlsx`, `json` (future) |
| `field_list` | TEXT[] | Yes | Which fields were included |
| `lead_ids` | UUID[] | Yes | Which leads were exported |
| `status` | ENUM | Yes | `queued`, `processing`, `complete`, `failed` |
| `file_path` | VARCHAR(500) | No | Storage path |
| `file_size` | INTEGER | No | Bytes |
| `record_count` | INTEGER | Yes | |
| `error_message` | TEXT | No | |
| `created_at` | TIMESTAMP | Yes | |
| `completed_at` | TIMESTAMP | No | |

#### 2.2.10 Source API Keys (Per-Organization)

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `source_adapter` | VARCHAR(100) | Yes | e.g., `google_places`, `filesure` |
| `api_key_encrypted` | TEXT | Yes | Encrypted API key (AES-256) |
| `api_key_hint` | VARCHAR(20) | Yes | Last 4 chars for display |
| `status` | ENUM | Yes | `active`, `invalid`, `expired` |
| `last_verified_at` | TIMESTAMP | No | |
| `quota_used` | INTEGER | No | Current period usage |
| `quota_limit` | INTEGER | No | Current period limit |
| `created_at` | TIMESTAMP | Yes | |
| `updated_at` | TIMESTAMP | Yes | |

#### 2.2.11 Usage Records

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `id` | UUID | Yes | Primary key |
| `organization_id` | UUID FK | Yes | Tenant ownership |
| `user_id` | UUID FK | No | |
| `source_adapter` | VARCHAR(100) | Yes | |
| `operation` | VARCHAR(100) | Yes | `text_search`, `place_details`, `website_crawl`, `api_call` |
| `quantity` | INTEGER | Yes | Number of API units consumed |
| `pipeline_run_id` | UUID FK | No | Related pipeline run |
| `created_at` | TIMESTAMP | Yes | |

### 2.3 Source Attribution Model

Every field that originates from an external source must carry provenance metadata. This is stored in the `raw_records.raw_data` (full response) and linked through `raw_record_id` in leads.

**Provenance chain:**
```
Lead → RawRecord → { source_adapter, source_record_id, retrieved_at, raw_data }
EnrichmentData → { source_adapter, source_record_id, retrieved_at, data }
```

**Field-level attribution** is derived at query time by comparing the lead's field values against the raw record and enrichment data sources. This avoids duplicating attribution metadata on every field.

### 2.4 Deduplication Strategy

| Dedup Scope | Key | Source |
|-------------|-----|--------|
| Google Places → Companies | `source_place_id` + `organization_id` | Google Places `id` |
| MCA → Companies | `source_cin` + `organization_id` | MCA `CIN` |
| Cross-source | `domain` + `organization_id` | Extracted from website URL |
| Cross-source (no domain) | `LOWER(name)` + `city` + `organization_id` | Fuzzy match on normalized name + location |
| Contacts | `LOWER(email)` + `organization_id` | Email is canonical contact key |

**Dedup rules:**
1. First check exact unique key match (place_id, CIN, domain).
2. If no exact match, check normalized name + city.
3. If match found → link raw_record to existing company.
4. If no match → create new company.
5. Never silently discard records — duplicates are linked, not deleted.

### 2.5 Database Migration Strategy

- All schema changes via numbered migrations (e.g., `001_initial_schema.sql`).
- Migrations are forward-only — never rewrite applied migrations.
- Foreign keys enforced at database level.
- Indexes created based on actual query patterns (not speculative).
- Supabase migrations if using Supabase; otherwise standard Alembic (Python) or raw SQL.

---

## 3. API Architecture

### 3.1 API Design Principles

- **Contract-first:** Define request/response schemas before implementation.
- **REST:** Standard HTTP methods, resource-oriented URLs.
- **JSON:** All request/response bodies in JSON.
- **Tenant-scoped:** Every endpoint operates within the authenticated user's organization.
- **Paginated:** All list endpoints return paginated results.

### 3.2 API Endpoint Map (Slice 1 Focus)

#### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/login` | No | Login, return JWT |
| `POST` | `/api/auth/logout` | Yes | Invalidate session |
| `GET` | `/api/auth/me` | Yes | Current user info |

#### Search / Discovery

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/searches` | Yes | Create and run a search (pipeline run) |
| `GET` | `/api/searches` | Yes | List user's searches |
| `GET` | `/api/searches/{id}` | Yes | Get search details + status |
| `GET` | `/api/searches/{id}/results` | Yes | Get paginated results from a search |
| `DELETE` | `/api/searches/{id}` | Yes | Cancel/delete a search |

#### Leads

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/leads` | Yes | List leads (filterable, sortable, paginated) |
| `GET` | `/api/leads/{id}` | Yes | Lead detail with full provenance |
| `PATCH` | `/api/leads/{id}` | Yes | Update lead (e.g., mark as exported) |
| `POST` | `/api/leads/bulk-action` | Yes | Bulk operations (export selection, etc.) |

#### Companies

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/companies` | Yes | List companies |
| `GET` | `/api/companies/{id}` | Yes | Company detail |
| `GET` | `/api/companies/{id}/contacts` | Yes | Contacts at a company |
| `GET` | `/api/companies/{id}/leads` | Yes | Leads for a company |

#### Exports

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/exports` | Yes | Create export job |
| `GET` | `/api/exports` | Yes | List export history |
| `GET` | `/api/exports/{id}` | Yes | Get export status |
| `GET` | `/api/exports/{id}/download` | Yes | Download export file |

#### Settings / Configuration

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/settings/api-keys` | Yes | List configured API keys (masked) |
| `POST` | `/api/settings/api-keys` | Yes | Add/update API key |
| `DELETE` | `/api/settings/api-keys/{id}` | Yes | Remove API key |
| `POST` | `/api/settings/api-keys/{id}/verify` | Yes | Verify API key validity |
| `GET` | `/api/settings/usage` | Yes | Usage statistics |

#### Dashboard

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `GET` | `/api/dashboard/metrics` | Yes | Summary metrics |
| `GET` | `/api/dashboard/pipeline-activity` | Yes | Pipeline stage counts |
| `GET` | `/api/dashboard/recent-leads` | Yes | Recent leads list |
| `GET` | `/api/dashboard/distributions` | Yes | Industry/geography charts |

### 3.3 Request/Response Conventions

**Pagination (all list endpoints):**
```
Request:
  GET /api/leads?page=1&per_page=25&sort=created_at&order=desc&validation_status=valid

Response:
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 25,
    "total_count": 142,
    "total_pages": 6
  }
}
```

**Error responses:**
```
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid search parameters",
    "details": [
      { "field": "query", "message": "Query text is required" }
    ]
  }
}
```

**Standard error codes:**
| Code | HTTP Status | Meaning |
|------|-------------|---------|
| `VALIDATION_ERROR` | 400 | Invalid request parameters |
| `UNAUTHORIZED` | 401 | Missing or invalid authentication |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SOURCE_UNAVAILABLE` | 503 | External API temporarily unavailable |
| `QUOTA_EXCEEDED` | 402 | API quota or plan limit reached |

### 3.4 Rate-Limit Handling (Internal API)

The ValLG API itself should enforce rate limits per organization to prevent abuse:

| Plan | Requests/min | Search runs/hour | Exports/day |
|------|-------------|------------------|-------------|
| Free | 60 | 5 | 3 |
| Starter | 120 | 20 | 10 |
| Pro | 300 | 50 | 50 |
| Enterprise | Custom | Custom | Custom |

Rate limit headers included in responses:
```
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1692100800
```

### 3.5 External Source API Integration

| Source | Auth Method | Quota Handling | Error Handling |
|--------|-------------|----------------|----------------|
| Google Places | API Key header | Track per-org usage, warn at 80%, block at 100% | Retry 429 with backoff, surface partial results |
| MCA OGD | Open (no auth) | N/A (bulk download) | Handle download failures gracefully |
| FileSure/Infyner | Token header | Track credit balance, warn before depletion | Retry on 5xx, fail gracefully |
| Company Websites | No auth (HTTP) | Domain-level rate limiting (1 req/5s) | Respect robots.txt, handle 403/429 |

---

## 4. Source Adapter Architecture

### 4.1 Adapter Interface Design

Every source adapter implements a common interface. This ensures the pipeline logic is decoupled from specific providers.

```python
# Conceptual interface (documentation only — no implementation code)

class SourceAdapter:
    """Common interface for all source adapters."""

    source_id: str          # e.g., "google_places_v1"
    display_name: str       # e.g., "Google Places API"

    async def search(self, params: SearchParams) -> SearchResult:
        """Execute a search and return results."""
        ...

    async def get_details(self, record_id: str) -> SourceRecord:
        """Get full details for a specific record."""
        ...

    async def verify_api_key(self, api_key: str) -> bool:
        """Verify that an API key is valid."""
        ...

    def get_quota_info(self) -> QuotaInfo:
        """Return current quota usage and limits."""
        ...

    def map_to_common_schema(self, raw_data: dict) -> dict:
        """Map source-specific fields to common schema."""
        ...
```

### 4.2 Google Places Adapter

| Aspect | Design |
|--------|--------|
| **Adapter ID** | `google_places_v1` |
| **API Base** | `https://places.googleapis.com/v1/` |
| **Auth** | `X-Goog-Api-Key` header |
| **Field Mask** | `X-Goog-FieldMask` header — configurable per request |
| **Endpoints Used** | `places:searchText`, `places:searchNearby`, `places/{place_id}` |
| **Rate Limit** | 600 RPM (per project) |
| **Pagination** | `nextPageToken` — cursor-based, forward only |
| **Field Mask (Slice 1)** | `places.id,places.displayName,places.formattedAddress,places.postalAddress,places.location,places.types,places.primaryType,places.nationalPhoneNumber,places.internationalPhoneNumber,places.websiteUri,places.businessStatus,places.rating,places.userRatingCount,places.googleMapsUri` |
| **Error Handling** | 429 → exponential backoff (30s, 60s, 120s). 403 → check API key. Quota exceeded → surface to user, suggest wait. |
| **Caching** | Place IDs cached permanently. Other data cached max 30 days per Google ToS. |
| **Provenance** | Source: `google_places_v1`, Source Record ID: `place.id`, Retrieved: request timestamp |

**Search parameters mapping:**

| SearchParam | Google Places API Param |
|-------------|------------------------|
| `query` (free text) | `textQuery` |
| `location_bias` (lat, lng, radius) | `locationBias.circle` |
| `included_type` | `includedType` |
| `min_rating` | `minRating` |
| `open_now` | `openNow` |
| `page_token` | `pageToken` |

### 4.3 MCA OGD Bulk Data Adapter

| Aspect | Design |
|--------|--------|
| **Adapter ID** | `mca_ogd_v1` |
| **Data Source** | `https://data.gov.in/catalog/company-master-data` |
| **Auth** | None (open government data) |
| **Access Method** | Bulk CSV/JSON download + CKAN Catalog API for updates |
| **Update Frequency** | Monthly snapshot + incremental via Catalog API |
| **Fields** | CIN, Company Name, Status, Class, Category, Capital, Registration Date, State, RoC, Address |
| **Limitations** | No contacts, no emails, no phones, no directors in bulk data |
| **Dedup Key** | CIN (Corporate Identification Number) |
| **Provenance** | Source: `mca_ogd_v1`, Source Record ID: CIN, Dataset Version: download date |

**Search capability:** MCA data is pre-loaded into PostgreSQL. Search is SQL-based (name, CIN, state, status). Not a real-time API — it's a local dataset.

### 4.4 Commercial India API Adapter (FileSure / Infyner)

| Aspect | Design |
|--------|--------|
| **Adapter ID** | `filesure_v1` or `infyner_v1` |
| **API Base** | Provider-specific REST endpoint |
| **Auth** | Bearer token or API key |
| **Operations** | Company search by CIN/name, Director details, Financials, GST/PAN verification |
| **Pricing** | Per-call (₹1–5 per read) |
| **Rate Limit** | Provider-specific |
| **Error Handling** | Retry on 5xx, fail gracefully on 4xx. Deduct credits only on success. |
| **Provenance** | Source: adapter ID, Source Record ID: CIN or provider ID |

**Note:** This adapter is for enrichment (Slice 6+), not primary discovery. Used to enrich companies already discovered via Google Places or MCA data.

### 4.5 Company Website Crawler Adapter

| Aspect | Design |
|--------|--------|
| **Adapter ID** | `website_crawler_v1` |
| **Access Method** | HTTP/HTTPS + HTML parsing |
| **Auth** | None (public websites) |
| **robots.txt** | MUST check before crawling. Respect `Disallow` and `Crawl-delay`. |
| **Rate Limit** | Domain-level: 1 request per 5 seconds. Random delay 1–5s between requests. |
| **User Agent** | Rotate among standard browser user agents |
| **Fields Extracted** | Company name, address, phone, email (role-based: info@, sales@), team page data |
| **JS Rendering** | Deferred — server-rendered HTML only for Slice 1. Headless browser for JS-heavy sites is a future enhancement. |
| **Error Handling** | 403/429 → skip domain for 1 hour. 5xx → retry once. Timeout → skip. |
| **Provenance** | Source: `website_crawler_v1`, Source Record ID: URL, Retrieved: crawl timestamp |

### 4.6 Blocked Sources — No Adapter

| Source | Status | Rationale |
|--------|--------|-----------|
| Yellow Pages | **BLOCKED** | No public API. ToS explicitly prohibits scraping. US-focused. |
| LinkedIn | **BLOCKED** | Active litigation against commercial scrapers. ToS prohibits scraping. |
| Google Search (CSE) | **DEFERRED** | Closed to new customers. Sunsetting Jan 2027. May revisit if access obtained. |

These sources are NOT implemented. If their access status changes, a new adapter can be added without modifying pipeline logic (adapter interface is pluggable).

### 4.7 Adapter Registration

Adapters are registered in a configuration registry:

```python
# Conceptual registration (documentation only)

ADAPTER_REGISTRY = {
    "google_places_v1": GooglePlacesAdapter,
    "mca_ogd_v1": McaOgdAdapter,
    "filesure_v1": FileSureAdapter,
    "infyner_v1": InfynerAdapter,
    "website_crawler_v1": WebsiteCrawlerAdapter,
}
```

New sources are added by implementing the `SourceAdapter` interface and registering. No pipeline logic changes required.

---

## 5. Security and Compliance

### 5.1 Secrets Management

| Secret | Storage | Access |
|--------|---------|--------|
| Database URL | Environment variable `DATABASE_URL` | Backend only |
| JWT Secret | Environment variable `JWT_SECRET` | Backend only |
| Google Places API Key | Encrypted in `source_api_keys` table (AES-256) | Per-org, backend only |
| Commercial API Keys | Encrypted in `source_api_keys` table (AES-256) | Per-org, backend only |
| Session Secret | Environment variable | Backend only |

**Rules:**
- Never commit secrets to Git.
- Never log secrets.
- Never expose secrets in API responses (show only last 4 chars).
- `.env.example` contains safe placeholders only.
- Frontend never has access to source API keys — all external API calls go through backend.

### 5.2 Multi-Tenant Security

```
Request → Auth Middleware
    │
    ├─ 1. Validate JWT
    ├─ 2. Resolve user → organization_id
    ├─ 3. Attach org_id to request context
    │
    └─ Handler
         │
         └─ All DB queries include WHERE organization_id = :org_id
```

**Never trust:**
- Client-supplied organization IDs
- Client-supplied user IDs
- Client-supplied permissions or roles
- Client-supplied quota or plan values

**Tenant isolation tests** must verify:
- User A cannot read User B's leads
- User A cannot access User B's exports
- User A cannot see User B's API keys
- User A cannot modify User B's companies

### 5.3 Data Handling Rules

| Rule | Implementation |
|------|---------------|
| **Source attribution** | Every lead linked to raw_record → source adapter + timestamp |
| **No fabricated data** | Empty fields stored as NULL, displayed as "—" |
| **Raw data preserved** | `raw_records.raw_data` stores complete source response, never overwritten |
| **Caching limits** | Google Places data cached max 30 days per ToS |
| **MCA attribution** | MCA OGD data requires attribution: provider, source, license, DOI/URL |
| **DPDP Act 2023** | Director/contact personal data requires lawful basis. Only business-contact data collected. |
| **Export controls** | Exports respect tenant ownership, field permissions, plan limits |
| **Data retention** | Raw records retained for audit. Leads retained until user deletes. Exports retained for 30 days. |

### 5.4 Logging and Auditing

| Event | Logged | Data |
|-------|--------|------|
| User login | Yes | User ID, timestamp, IP |
| Search executed | Yes | Org ID, user ID, query, sources, result count |
| API key added/changed | Yes | Org ID, user ID, source, timestamp (never the key itself) |
| Export created | Yes | Org ID, user ID, record count, format |
| Pipeline stage completed | Yes | Run ID, stage, duration, record counts |
| External API error | Yes | Source, error code, run ID (never API keys) |
| Tenant isolation violation attempt | Yes | User ID, attempted action, blocked |

**Never log:** Passwords, API keys, access tokens, payment secrets.

### 5.5 Source Compliance

| Source | Compliance Requirement | Implementation |
|--------|----------------------|----------------|
| Google Places | Display Google attribution where required | Include attribution in map view and exports |
| Google Places | No caching beyond 30 days | TTL on cached data, re-fetch after expiry |
| Google Places | No redistribution as competing service | ValLG is a lead-gen tool, not a places database |
| MCA OGD | Attribution: provider, source, license | Metadata stored with MCA records, included in exports |
| Company Websites | Respect robots.txt | Check robots.txt before every domain crawl |
| Company Websites | Rate limit compliance | Domain-level 1 req/5s, respect Crawl-delay |
| Company Websites | No personal data collection | Extract only role-based business contacts (info@, sales@) |

---

## 6. Scalability and Operations

### 6.1 Rate Limit Strategy

| Source | Limit | Strategy |
|--------|-------|----------|
| Google Places | 600 RPM per project | Token bucket per org. Queue excess requests. Auto-resume when tokens replenish. |
| Internal API | Per-plan limits | Rate limit middleware in FastAPI. Return 429 with Retry-After header. |
| Company Websites | 1 req/5s per domain | Domain-level semaphore. Exponential backoff on 429/403. |
| Commercial APIs | Per-credit | Check balance before call. Warn at 20% remaining. Fail gracefully at 0%. |

### 6.2 Caching Strategy

| Data | Cache Duration | Rationale |
|------|---------------|-----------|
| Google Places Place IDs | Permanent | Stable identifiers, no billing for ID-only requests |
| Google Places place data | 30 days max | Google ToS requirement |
| MCA bulk data | 30 days (full refresh) | Government data updates monthly |
| Company website data | 7 days | Websites change infrequently |
| Dashboard metrics | 5 minutes | Reduce DB load, slightly stale data acceptable |
| API key verification | 1 hour | Avoid excessive verification calls |

### 6.3 Background Job Architecture

Long-running operations run in a background worker process, not blocking HTTP requests.

**Job types for Slice 1:**

| Job Type | Trigger | Stages | Estimated Duration |
|----------|---------|--------|-------------------|
| **Search/Extract** | User clicks "Search Leads" | Create pipeline run → call Google Places API → store raw records → link to companies | 10s–5min (depends on result count) |
| **Export** | User clicks "Export" | Query leads → generate CSV → store file → notify | 5s–30s |

**Job states:**
```
QUEUED → RUNNING → COMPLETED
                    FAILED
```

**Worker technology (proposed):**
- Python `asyncio` with a task queue (e.g., `arq`, `celery`, or simple `asyncio.Queue` for Slice 1).
- **Decision deferred to Phase 4:** Simple async tasks for Slice 1. Evaluate dedicated task queue (Celery, RQ, arq) if complexity grows.

### 6.4 Retry Strategy

| Scenario | Retry Policy |
|----------|-------------|
| Google Places 429 (rate limit) | Exponential backoff: 30s, 60s, 120s. Max 3 retries. |
| Google Places 5xx (server error) | Retry once after 5s. |
| Google Places 403 (forbidden) | No retry — check API key. |
| Company website 429/403 | Skip domain for 1 hour. |
| Company website 5xx | Retry once after 5s. |
| Commercial API 5xx | Retry twice with 10s backoff. |
| Commercial API 4xx (invalid request) | No retry — log and fail. |
| Database connection error | Retry 3 times with 2s backoff. |

**Retry safety:** Retries must not create duplicate leads, contacts, or usage charges. Use idempotency keys where applicable.

### 6.5 Observability

| Signal | Tool (Proposed) | Purpose |
|--------|----------------|---------|
| HTTP request logs | FastAPI logging middleware | Request/response tracking |
| Pipeline job logs | Structured logging per job | Track extraction progress |
| Error tracking | Sentry or similar (Phase 4 decision) | Aggregate and alert on errors |
| API usage metrics | Database `usage_records` | Per-org usage tracking |
| External API latency | Application metrics | Monitor Google Places response times |

**Logging format:** Structured JSON with safe identifiers (request_id, org_id, user_id, pipeline_run_id, job_id). Never log secrets.

### 6.6 Failure Handling

| Failure | System Response | User Experience |
|---------|----------------|-----------------|
| Google Places API down | Return partial results + error banner | "Showing results from other sources. Google Places temporarily unavailable." |
| Google Places quota exceeded | Stop extraction, record failure | "Google Places quota exceeded. X of Y results retrieved. Upgrade or wait for quota reset." |
| Company website unreachable | Skip website, continue with other data | "Website crawl failed for N companies. Other data preserved." |
| Database connection lost | Return 500 error, log incident | "Something went wrong. Please try again." |
| Worker crash | Job stays in RUNNING state, timeout after 5 min → mark FAILED | "Search failed. Please try again." |
| Export file generation fails | Mark export as FAILED | "Export failed. Please try again." |

---

## 7. Technology Decisions

### 7.1 Confirmed Technology Choices (Locked)

| Component | Choice | Source |
|-----------|--------|--------|
| Frontend framework | React | ARCHITECTURE.md, AI Rules |
| Frontend language | TypeScript | ARCHITECTURE.md, AI Rules |
| CSS framework | Tailwind CSS | ARCHITECTURE.md, AI Rules |
| Backend framework | FastAPI | ARCHITECTURE.md, AI Rules |
| Backend language | Python | ARCHITECTURE.md, AI Rules |
| Database | PostgreSQL | ARCHITECTURE.md, AI Rules |
| API style | REST | ARCHITECTURE.md, AI Rules |
| Testing (backend) | Pytest | ARCHITECTURE.md |
| Version control | Git | ARCHITECTURE.md |

### 7.2 Proposed Choices (Require Approval)

| Component | Proposal | Rationale | Alternatives |
|-----------|----------|-----------|--------------|
| **Auth provider** | Supabase Auth | Managed PostgreSQL + Auth + RLS. Fits multi-tenant model. Free tier sufficient for start. | Custom JWT (more work), Auth0 ($$), Clerk ($$) |
| **ORM / DB queries** | SQLAlchemy 2.0 + Alembic | Mature Python ORM, good FastAPI integration, migration support | Django ORM (heavier), raw SQL (more control, more work), Prisma (Python support immature) |
| **Task queue** | `arq` (async Redis queue) or simple `asyncio` tasks for Slice 1 | Lightweight, async-native, Redis-based. Evaluate if Celery needed later. | Celery (heavier), RQ (sync), raw asyncio (simpler but no persistence) |
| **Cache / queue backend** | Redis | Industry standard, used by `arq`, fast, supports pub/sub | PostgreSQL LISTEN/NOTIFY (simpler but limited), RabbitMQ (heavier) |
| **Chart library** | Deferred to Phase 4 | Phase 2 decision: do not lock now | Recharts, Chart.js, D3, Visx |
| **CSV generation** | Python `csv` module (stdlib) | No dependency needed for basic CSV | `openpyxl` for Excel (future), `pandas` (heavier) |
| **HTTP client** | `httpx` (async) | Async-native, matches FastAPI async model | `requests` (sync), `aiohttp` |
| **HTML parsing** | `BeautifulSoup4` + `lxml` | Mature, well-documented, fast | `selectolax` (faster but less known), `lxml` only |
| **robots.txt parser** | `robotexclusionrules` or `rebulk` | Standard robots.txt parsing | Manual parsing (fragile) |
| **API key encryption** | `cryptography` library (Fernet AES-128) | Simple, symmetric encryption for DB storage | AWS KMS (heavier), vault (heavier) |
| **Cloud hosting** | Deferred to Phase 4 | Not enough info to decide now | Vercel (frontend), Railway/Fly.io (backend), AWS, GCP |
| **File storage (exports)** | Local filesystem for Slice 1, S3-compatible later | Simple for start, migrate when needed | S3, Supabase Storage, GCS |

### 7.3 Technology NOT Introduced

| Technology | Why Not |
|------------|---------|
| Redux / Zustand / Global state | AI Rules: keep state local unless justified. Start without global state. |
| GraphQL | REST is locked. No demonstrated need for GraphQL. |
| WebSocket | Manual refresh per Phase 2 decision. No real-time push needed in Slice 1. |
| Kubernetes | AI Rules: no orchestration unless explicitly justified. |
| Microservices | Monolith-first per architecture. Single FastAPI app. |
| Elasticsearch | PostgreSQL full-text search sufficient for initial scale. |

---

## 8. Phase 4 Implementation Boundaries

### 8.1 What Is Ready After Phase 3 Approval

Phase 4 implements the first vertical slice: **Slice 1 — Discovery/Extract + Dashboard + Settings**.

**Scope of Slice 1:**

| Area | Includes | Does NOT Include |
|------|----------|-----------------|
| **Auth** | Login, JWT, org context | User invitations, RBAC roles |
| **Search** | Google Places Text Search, search form, templates | MCA search mode, Nearby Search mode |
| **Pipeline** | Extract stage only | Clean, Dedup, Validate, Enrich, Score |
| **Results** | Table view, Map view (secondary), pagination | List view, filtering, sorting (beyond basics) |
| **Leads** | Basic leads list from search results | Lead management, bulk operations |
| **Dashboard** | Real metrics from DB (total leads, pipeline activity) | Charts (deferred), industry/geography distributions |
| **Settings** | Google Places API key config | MCA data config, commercial API keys, user management |
| **Exports** | CSV export (basic) | Excel/JSON, export history, field selection |
| **Database** | Organizations, Users, Companies, Raw Records, Pipeline Runs, Leads (basic) | Contacts, Enrichment Data, Lead Scores, full Export model |

### 8.2 Slice 1 Dependencies

```
Frontend (React + TypeScript + Tailwind)
    │
    ├── Auth pages (login)
    ├── Dashboard (metrics cards)
    ├── Search form
    ├── Results table
    ├── Map view (secondary)
    ├── Settings (API keys)
    └── Export (basic CSV)
    │
    ▼
Backend API (FastAPI + Python)
    │
    ├── Auth endpoints (login, me)
    ├── Search endpoints (create, list, results)
    ├── Leads endpoints (list, detail)
    ├── Dashboard endpoints (metrics)
    ├── Settings endpoints (API keys)
    ├── Export endpoints (create, download)
    │
    ├── Google Places Adapter
    │   ├── Search (textSearch)
    │   ├── Details (placeDetails)
    │   └── Field mask management
    │
    └── Background worker
        └── Search/Extract job
    │
    ▼
Database (PostgreSQL)
    │
    ├── organizations
    ├── users
    ├── companies
    ├── raw_records
    ├── pipeline_runs
    ├── leads (basic)
    └── source_api_keys
```

### 8.3 Slice 1 Test Requirements

| Test Type | Scope |
|-----------|-------|
| Unit tests | Source adapter (mocked API), search parameter mapping, field mask generation |
| API tests | All endpoints with authenticated requests |
| Integration tests | Search → extract → results flow (mocked Google Places) |
| Tenant isolation tests | User A cannot access User B's data |
| Frontend tests | Search form, results table, settings form |
| E2E test | Login → Search → View Results → Export CSV (critical path) |

### 8.4 Slice 1 Acceptance Criteria

1. User can log in and see their organization's dashboard.
2. User can configure Google Places API key in Settings.
3. User can enter search criteria and run a search.
4. Backend calls Google Places Text Search API and stores raw records.
5. Results appear in a sortable table with company name, industry, location, phone, website, rating.
6. Map view shows results on a map.
7. User can click into a lead detail and see full provenance.
8. User can select leads and export as CSV.
9. All data is scoped to the user's organization (tenant isolation).
10. Loading, empty, and error states are handled for all API-driven screens.
11. All tests pass.
12. No secrets exposed in source code, logs, or API responses.

### 8.5 Future Slices (Post-Slice 1)

| Slice | Scope | Depends On |
|-------|-------|-----------|
| Slice 2 | Raw Data storage + Companies view | Slice 1 |
| Slice 3 | Clean stage (phone normalization, address parsing) | Slice 2 |
| Slice 4 | Deduplicate stage (cross-source matching) | Slice 3 |
| Slice 5 | Validate stage (field validation, quality badges) | Slice 4 |
| Slice 6 | Enrich stage (website crawl, MCA lookup, commercial API) | Slice 5 |
| Slice 7 | Score stage (explainable lead scoring) | Slice 6 |
| Slice 8 | Export stage (full export with field selection, history) | Slice 5 |

---

## 9. Open Questions Requiring Approval

| # | Question | Options | Recommendation |
|---|----------|---------|----------------|
| 1 | **Auth provider** | Supabase Auth vs Custom JWT vs Auth0 | Supabase Auth (managed, fits architecture) |
| 2 | **ORM** | SQLAlchemy 2.0 vs raw SQL vs Django ORM | SQLAlchemy 2.0 (mature, FastAPI-native) |
| 3 | **Task queue for Slice 1** | Simple asyncio vs `arq` vs Celery | Simple asyncio for Slice 1, evaluate `arq` later |
| 4 | **Redis** | Required for task queue + caching vs skip for Slice 1 | Include Redis (small instance, useful for rate limiting + queue) |
| 5 | **MCA data loading** | Full 3.5M+ bulk load at startup vs on-demand search vs defer to Slice 2 | Defer MCA bulk loading to Slice 2. Slice 1 focuses on Google Places only. |
| 6 | **Commercial API provider** | FileSure vs Infyner vs defer | Defer to Slice 6 (enrichment phase). No provider selected yet. |
| 7 | **Export file storage** | Local filesystem vs S3 for Slice 1 | Local filesystem for Slice 1. Migrate to S3-compatible storage later. |
| 8 | **Map library** | Google Maps JS API vs Leaflet + OpenStreetMap | Leaflet + OSM for Slice 1 (no additional API key needed). Google Maps as upgrade option. |
| 9 | **Frontend routing** | React Router vs Next.js (SSR) | React Router (SPA per locked React stack). Next.js would be a stack change. |
| 10 | **Database migrations** | Alembic (Python) vs Supabase migrations vs raw SQL | Alembic if using SQLAlchemy. Supabase migrations if using Supabase CLI. |

---

**END OF PHASE 3 ARCHITECTURE/DATA/API PLAN** — Awaiting approval before proceeding to Phase 4 implementation.
