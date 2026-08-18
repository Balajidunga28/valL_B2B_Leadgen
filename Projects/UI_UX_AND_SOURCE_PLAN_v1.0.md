<!--
url: /Projects/UI_UX_AND_SOURCE_PLAN_v1.0.md
About:
  Defines the product UI/UX, user journey, search form, result presentation,
  source strategy, and source-by-source discovery requirements for ValLG.
  This is the high-level planning document. The detailed Phase 2 UI/UX plan
  is in UI_UX_PLAN_Phase2_v1.0.md (APPROVED).
-->

# ValLG — UI/UX & Source Plan

**Version:** 1.0
**Status:** PLANNED — Superseded by detailed Phase 2 plan (UI_UX_PLAN_Phase2_v1.0.md — APPROVED)

## Product and UI
ValLG is a multi-industry B2B Lead Generation & Marketing Research SaaS, with India as the primary target geography while keeping the product flexible for other geographies.

Primary navigation:
- Dashboard
- Search Leads
- Leads
- Companies
- Contacts
- Enrichment
- Lead Scoring
- Exports
- Settings

The Search Leads screen must be planned before implementation. Candidate search fields:
- Industry
- Country
- State/Region
- City
- Company size / employee range
- Technology
- Business signals
- Keywords
- Source selection where appropriate

Search results should be presented in a responsive, data-heavy table/list with candidate fields:
- Company
- Industry
- Location
- Company size, when available
- Website
- Contact information, when available
- Source
- Validation status
- Enrichment status
- Lead score, once scoring exists
- Selection/action controls

Company details should show identity, website, industry, geography, available enrichment, provenance, validation, and scoring information. Contact views should show legitimate available contact data and provenance.

The dashboard should use real persisted data for metrics such as total leads, valid leads, high-score leads, exported leads, industry/geography distributions, recent leads, and pipeline activity. Mockup numbers must never be hard-coded.

Every API-driven screen must support loading, success, empty, error, and unauthorized states.

## Required source set
The product plan must retain these target discovery sources:
1. Google Maps / Google Places
2. Yellow Pages
3. Public LinkedIn information
4. Company websites
5. Open business directories

Each source must be implemented behind an adapter/provider boundary.

### Google Maps / Google Places
Google Places API (New) provides Text Search, Nearby Search, Place Details and related place functionality. Text Search supports text queries and location controls, and responses are controlled with field masks. Production use requires API setup/authentication and billing.

Official documentation:
https://developers.google.com/maps/documentation/places/web-service
https://developers.google.com/maps/documentation/places/web-service/text-search

### Yellow Pages
The Real Yellow Pages is a business directory with business search and city/category directory pages. Before automated acquisition is implemented, verify permitted technical access, terms, rate limits, and whether an approved API/provider exists. Never bypass access controls or rate limits.

Official site:
https://www.yellowpages.com/

### Public LinkedIn
Use public LinkedIn information only where the intended access is legally and technically permitted. Do not bypass authentication, CAPTCHA, anti-bot controls, rate limits, or other technical restrictions. Prefer an approved API/licensed provider where available.

### Company websites
Use company websites where automated access is permitted. Respect source terms, robots.txt where applicable, rate limits, timeouts, and HTTP errors.

### Open business directories
Evaluate each directory individually for legitimate public access, available fields, geographic coverage, and applicable restrictions.

## Source verification gate
Before integrating any source, document:
- What it provides
- Geographic coverage
- Search capabilities
- Available fields
- Authentication/API requirements
- Terms/permissions relevant to intended use
- Rate limits
- Cost, if applicable
- Failure modes
- Provenance strategy
- Adapter design

## Vertical-slice rule
Plan the complete UI/product first, then implement one approved slice at a time:

PLAN → APPROVE → IMPLEMENT → TEST → REPORT → REVIEW → APPROVE → NEXT SLICE

A slice must stop before implementing later slices.
