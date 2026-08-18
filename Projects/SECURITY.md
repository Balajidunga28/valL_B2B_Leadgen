<!--
url: /Projects/SECURITY.md
About:
  Defines the planned ValLG security controls for authentication,
  authorization, multi-tenant isolation, secrets, external data sources,
  logging, exports, and security validation.
-->

# ValLG Security Plan

**Version:** 1.0  
**Status:** PLANNING

## Core Principles

- Authentication is mandatory for protected operations.
- Authorization is enforced server-side.
- Frontend is never a security boundary.
- Tenant isolation is non-negotiable.
- Secrets must never be exposed in source, frontend, documentation, logs, or Git.

## Tenant Isolation

Organization ownership must be derived from authenticated context.

Organization A must never access Organization B's:
- Companies
- Contacts
- Leads
- Scores
- Enrichment
- Exports
- Pipeline runs
- Usage
- Integrations

Tenant-isolation tests are required.

## Secrets

Use environment variables or approved secret management.

Maintain `.env.example` with safe placeholders only.

Never commit real credentials.

## Data Sources

Only use sources that are legally and technically appropriate for the intended use.

Never:
- Bypass CAPTCHA.
- Bypass authentication.
- Bypass paywalls.
- Evade rate limits.
- Circumvent technical restrictions.
- Collect private information.
- Use stolen credentials.

Target sources must be individually evaluated before integration.

## API Security

Use:
- Authentication
- Authorization
- Input validation
- Appropriate rate limiting
- Safe errors
- Secure logging

## Logging

Never log:
- Passwords
- API keys
- Access tokens
- Payment secrets
- Private credentials

Use safe identifiers such as request ID, organization ID, pipeline run ID, and job ID.

## Export Security

Exports must respect:
- Tenant ownership
- User permissions
- Approved fields
- Subscription/usage limits
- Sensitive-data rules

## Security Completion Gate

Before a major feature is complete, review:
- Authentication
- Authorization
- Tenant isolation
- Input validation
- Secrets
- Logging
- Rate limits
- Data exposure
- External integrations
- Abuse/failure scenarios
