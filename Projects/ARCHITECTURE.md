<!--
url: /Projects/ARCHITECTURE.md
About:
  Defines the approved ValLG application architecture, technology boundaries,
  pipeline-stage separation, source-adapter strategy, and major system
  structural decisions.
-->

# ValLG Architecture

**Version:** 1.0  
**Status:** PLANNING

## Locked Technology Stack

### Frontend
- React
- TypeScript
- Tailwind CSS

### Backend
- Python
- FastAPI

### Database
- PostgreSQL
- Supabase may be used as the managed PostgreSQL/auth/platform layer where appropriate.

### API
- REST

### Processing
- Python
- Pandas only where clearly beneficial.

### Testing
- Pytest
- Frontend/component/workflow tests
- Integration tests
- E2E tests for critical workflows
- Security and tenant-isolation tests

### Containerization
- Docker where useful.

## High-Level Architecture

User
→ React/TypeScript UI
→ FastAPI REST API
→ Application services
→ PostgreSQL/Supabase

Long-running work:
API
→ Job abstraction/worker
→ Pipeline stage
→ Database/status

## Pipeline Architecture

Sources
→ Extract
→ Raw
→ Clean
→ Deduplicate
→ Validate
→ Enrich
→ Score
→ Export

Stages must remain separate and independently testable.

## Source Adapter Architecture

Required target sources:

- Google Maps / Google Places
- Yellow Pages
- Public LinkedIn information
- Company websites
- Open business directories

Conceptual boundary:

Source Adapter
→ Fetch
→ Source Record
→ Normalize/Map
→ Pipeline

Core pipeline logic must not be tightly coupled to a single provider.

## Multi-Tenant Architecture

Authenticated User
→ Organization
→ Authorized Resource

The server determines organization ownership. Client-supplied organization IDs must never be trusted as authorization.

## Background Jobs

Use a job abstraction for long-running work such as:
- Extraction
- Cleaning
- Deduplication
- Validation
- Enrichment
- Scoring
- Large exports
- CRM synchronization

Job states should be traceable, e.g.:

QUEUED → RUNNING → COMPLETED

or

QUEUED → RUNNING → FAILED

## Architecture Change Rule

The approved stack and architecture are locked unless an explicit architecture proposal is approved.
