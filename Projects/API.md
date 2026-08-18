<!--
url: /Projects/API.md
About:
  Defines the planned ValLG REST API boundaries, authentication and
  authorization requirements, contract-first development rules, pipeline
  interfaces, and API documentation expectations.
-->

# ValLG API Plan

**Version:** 1.0  
**Status:** PLANNING

## API Technology

FastAPI + REST.

## Contract-First Rule

Before implementing an API-dependent feature, define:
- Endpoint
- HTTP method
- Authentication requirement
- Request schema
- Response schema
- Error schema
- Pagination
- Tenant ownership
- Rate/usage implications

## Example Resource Areas

Planned API areas may include:
- Authentication/session
- Search/discovery
- Leads
- Companies
- Contacts
- Pipeline runs
- Enrichment
- Lead scoring
- Exports
- Usage
- Integrations

Exact endpoints must be approved before implementation.

## Security

Protected endpoints must enforce:

Authentication
→ Authorization
→ Tenant ownership
→ Input validation

Never trust client-supplied ownership, permissions, quota, score, pricing, or system role.

## API Stability

Once approved and consumed by the frontend, breaking API changes require:
1. Explanation.
2. Impact analysis.
3. Migration proposal.
4. Approval.
5. Updated tests/documentation.
