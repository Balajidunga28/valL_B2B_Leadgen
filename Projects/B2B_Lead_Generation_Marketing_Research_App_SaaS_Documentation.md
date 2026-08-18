<!--
url: /Projects/B2B_Lead_Generation_Marketing_Research_App_SaaS_Documentation.md
About:
  Defines the approved product requirements, business purpose, user workflow,
  B2B lead-generation domain scope, target market, and functional expectations
  for the ValLG SaaS application.
-->

# ValLG — B2B Lead Generation & Marketing Research SaaS

**Status:** PLANNING  
**Version:** 1.0

## Product Purpose

ValLG is a multi-industry B2B Lead Generation & Marketing Research SaaS.

The primary target market is India, while the product architecture must remain flexible enough to support other geographies and industries.

The product helps users define the type of businesses/prospects they need, discover relevant business records from approved sources, process and improve the data through a controlled pipeline, qualify leads, and export/use the resulting prospects.

## Core User Journey

Search criteria
→ Source discovery
→ Extract
→ Raw Data
→ Clean
→ Deduplicate
→ Validate
→ Enrich
→ Score
→ Filter/select
→ Export / CRM

## Target Discovery Sources

The product plan must retain these target sources:

- Google Maps / Google Places
- Yellow Pages
- Public LinkedIn information
- Company websites
- Open business directories

Each source must be evaluated for actual capabilities, geographic coverage, available fields, access method, permissions/terms, rate limits, and provenance before implementation.

## User-Facing Areas

Planned areas include:

- Dashboard
- Search Leads
- Leads
- Companies
- Contacts
- Enrichment
- Lead Scoring
- Exports
- Settings

## Search Experience

The search UI should be planned around business intent rather than technical pipeline terminology.

Candidate search criteria include:

- Industry
- Country
- State/Region
- City
- Company size / employee range
- Technology
- Business signals
- Keywords
- Source selection where appropriate

The exact form must be finalized after domain and source research.

## Search Results

Results should provide useful company/lead information, with available fields such as:

- Company
- Industry
- Location
- Company size
- Website
- Contact information
- Source/provenance
- Validation status
- Enrichment status
- Lead score after scoring is implemented

Results must be based on real data. Unknown or unavailable values must not be fabricated.

## Data Pipeline

The approved pipeline is:

**Sources → Extract → Raw → Clean → Deduplicate → Validate → Enrich → Score → Export**

Each stage must have clear input, output, status, error handling, metrics, and tests.

Raw acquired data must remain traceable and must not be silently replaced by cleaned or enriched values.

## Lead Quality

The objective is useful, relevant, validated B2B prospects rather than maximum record quantity.

Lead scoring must be explainable and versioned.

## SaaS Requirements

The application is multi-tenant.

Tenant-owned resources must be protected server-side through authenticated user → organization → resource ownership.

The system must include appropriate authentication, authorization, security, usage controls, error handling, testing, and auditability.

## Development Approach

The complete product and UI are planned first.

Implementation uses vertical slicing:

**PLAN → APPROVE → IMPLEMENT → TEST → REPORT → REVIEW → APPROVE → NEXT SLICE**

Only one approved slice is implemented at a time.

## Data Integrity

- No fabricated business/customer data.
- Preserve source provenance.
- Preserve raw data.
- Treat uncertainty as an explicit state.
- External-source failures must not be represented as successful operations.

## Documentation

The project must continuously maintain:

- PROJECT_PLAN.md
- ARCHITECTURE.md
- DATABASE.md
- API.md
- SECURITY.md
- CHANGELOG.md

Documentation must match actual implementation.
