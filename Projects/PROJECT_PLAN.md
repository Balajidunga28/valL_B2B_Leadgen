<!--
url: /Projects/PROJECT_PLAN.md
About:
  Tracks the approved development phases, vertical slices, milestones,
  acceptance gates, and current project status for ValLG.
-->

# ValLG Project Plan

**Version:** 1.0  
**Status:** IMPLEMENTATION (Slice 1 Complete)

## Development Principle

Plan the whole product first, then implement one complete vertical slice at a time.

Required cycle:

**PLAN → APPROVE → IMPLEMENT → TEST → REPORT → REVIEW → APPROVE → NEXT**

## Phase 0 — Project Audit

Status: PLANNED

- Inspect project directory.
- Identify technology/runtime/package configuration.
- Read approved documentation.
- Identify risks.
- Do not write application code.

## Phase 1 — Domain & Source Research

Status: PLANNED

Understand:
- B2B lead-generation workflow.
- Search intent.
- Required sources.
- Source capabilities.
- Geographic coverage.
- Available fields.
- Access/permission requirements.
- Failure/rate-limit behavior.

Required target sources:
- Google Maps / Google Places
- Yellow Pages
- Public LinkedIn information
- Company websites
- Open business directories

## Phase 2 — UI/UX Plan

Status: APPROVED

Define:
- Navigation.
- Search form.
- Search fields.
- Source selection.
- Results presentation.
- Company details.
- Contact details.
- Pipeline visibility.
- Dashboard.
- Exports.
- Loading/empty/error/unauthorized states.

Approval gate required before implementation.

## Phase 3 — Architecture/Data/API Plan

Status: APPROVED

Define:
- Frontend architecture.
- Backend architecture.
- Database entities/relationships.
- API contracts.
- Multi-tenancy.
- Source adapters.
- Background jobs.
- Security boundaries.

Approval gate required.

## Phase 4 — Implementation (Slice 1)

Status: COMPLETE

Depends on Phase 3 approval.

## Vertical Slices

### Slice 1 — Discovery / Extract
Status: COMPLETE

Must include only the approved first slice and its tests.

### Slice 2 — Raw Data
Status: NOT STARTED

### Slice 3 — Clean
Status: NOT STARTED

### Slice 4 — Deduplicate
Status: NOT STARTED

### Slice 5 — Validate
Status: NOT STARTED

### Slice 6 — Enrich
Status: NOT STARTED

### Slice 7 — Score
Status: NOT STARTED

### Slice 8 — Export
Status: NOT STARTED

Additional user-facing vertical slices will be defined after the UI/product plan is approved.

## Completion Gate

A slice is complete only when:
- Approved scope is implemented.
- Tests pass.
- Build/type/lint checks pass where configured.
- Security considerations are reviewed.
- Documentation is updated.
- CHANGELOG is updated.
- Acceptance criteria pass.
- User review/approval is received.
