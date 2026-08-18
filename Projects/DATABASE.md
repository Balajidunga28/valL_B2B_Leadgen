<!--
url: /Projects/DATABASE.md
About:
  Defines the planned ValLG PostgreSQL data model, tenant ownership rules,
  pipeline relationships, provenance requirements, constraints, indexes, and
  migration expectations.
-->

# ValLG Database Plan

**Version:** 1.0  
**Status:** PLANNING

## Database

PostgreSQL is the approved database.

Supabase may be used as the managed PostgreSQL/auth/platform layer where appropriate.

## Core Entities

The detailed schema must be finalized and approved before implementation.

Expected areas include:
- Organizations
- Users/memberships
- Companies
- Contacts
- Pipeline runs
- Raw records
- Cleaned records
- Validation results
- Enrichment data
- Lead scores
- Exports
- Usage records
- Source/provider metadata

## Tenant Ownership

Every tenant-owned record must have an unambiguous ownership path:

Authenticated User → Organization → Resource

The server must enforce tenant ownership.

## Provenance

Where applicable, retain:
- Source
- Source URL
- Retrieved timestamp
- Pipeline run ID
- Provider/adapter
- Adapter version
- Processing status

## Pipeline Relationships

Records must remain traceable through:

Pipeline Run
→ Raw Record
→ Cleaned Record
→ Deduplicated Record/state
→ Validation
→ Enrichment
→ Score
→ Export

## Database Safety

- Use migrations.
- Use foreign keys.
- Use constraints.
- Use indexes based on actual query patterns.
- Do not make destructive changes automatically.
- Do not reset production data as a development shortcut.

Detailed schema changes require approval before implementation.
