<!--
url: /Projects/AI_Rules_and_Constraints_v1.1.md
About:
  Version 1.1 master AI governance document for ValLG — B2B Lead Generation &
  Marketing Research SaaS. This version preserves the complete original master
  rules and incorporates the newly approved B2B Lead Gen rules and documentation
  governance changes. Version 1.1 is a merged update; the previous version remains
  preserved and is not overwritten.
-->

# AI Rules & Constraints — ValLG — B2B Lead Generation & Marketing Research SaaS

**Document Version:** 1.1

## Version History

- **v1.0** — Original master AI Rules & Constraints document.
- **v1.1** — Merged the newly approved B2B Lead Gen instruction set and documentation/file-governance changes into the original master document. The original master content is preserved below.

# Part I — Newly Approved B2B Lead Gen Rules

# AI Rules & Constraints: B2B Lead Gen App

## 1. Strict "Ask Before Acting" Policy
* NEVER edit any existing file without explicit approval.
* NEVER delete files, blocks of code, database columns, or comments.
* NEVER create or write new files without asking first.
* Always present a step-by-step implementation plan before writing code.
* Wait for my direct confirmation (e.g., "Apply step 1") before executing.

## 2. No Assumptions
* If any pipeline step, database column, or endpoint requirement is unclear, STOP and ask me.
* Do not make assumptions about API schemas, rate limits, or target web scraping selectors.

## 3. Scope Boundaries
* Limit read operations strictly to files relevant to the current task context.
* Do not run terminal or bash commands without explaining their purpose and asking for permission.
* If a bug is found outside the current task scope (e.g., in a different pipeline stage), report it but do not fix it.

## 4. File Headers & Metadata (Mandatory)

**EVERY project file MUST start with a standardized comment block at the very top.**

The mandatory header MUST contain both of the following:

### 4.1 Local Project URL / Path

The header MUST include a `url:` field containing the file's local project path.

Example:

```text
url: /backend/pipeline/extract.py
```

The path must accurately identify the file's location within the project.

### 4.2 Detailed About Section

The header MUST include an `About:` section that clearly and specifically explains the file's exact purpose.

The `About` section must explain:
- What the file is responsible for.
- What role it plays in the project.
- What type of information, logic, configuration, documentation, or functionality it contains.
- Any important responsibility that a developer or AI agent needs to understand before modifying the file.

Do **not** use vague descriptions such as "contains code", "project file", or "configuration file".

### 4.3 Mandatory Header Format

Use the following structure, adapting the path and About content to the specific file:

```text
<!--
url: /path/to/file.ext
About:
  Detailed explanation of this file's exact purpose, responsibility,
  and role within the project.
-->
```

### 4.4 Header Placement

- The header MUST be the **first content in EVERY file**.
- No imports, executable code, configuration, documentation text, metadata, or other content may appear before it.
- Every newly created file MUST receive the header immediately when it is created.

### 4.5 Existing Files

- Existing files MUST retain their standardized header.
- Do NOT remove an existing header simply because the file is being edited.
- If an existing file does not have the required header, add it as part of the task.
- If the file's path or exact purpose changes, update its `url` and/or `About` section accordingly.

### 4.6 File-Specific About Requirement

The `About` section MUST be specific to the individual file.

Do not copy the same generic About text across unrelated files.

### 4.7 Scope

This requirement applies to **EVERY project file**, including but not limited to:
- Source code
- Backend files
- Frontend files
- Configuration files
- Scripts
- Database files
- SQL/migration files
- API-related files
- Tests
- Documentation
- Automation files
- AI instruction/rule files

If a file format does not support the `<!-- -->` comment syntax, use that format's valid comment syntax while preserving the same required `url` and `About` metadata.

### 4.8 AI Enforcement

AI agents working on this project MUST verify the file header before creating or modifying a file.

If a required header is missing or inaccurate, the AI agent MUST correct it as part of the task.

This rule is mandatory and MUST NOT be treated as optional guidance.

## 5. Coding Standards & Documentation
* Use snake_case for Python/SQL and camelCase/PascalCase for JavaScript/React.
* Keep names descriptive and clear; do not use vague abbreviations.
* Write comprehensive comments explaining the "why" behind data transformations, regex filters, and state maps.
* Every function, loop, and conditional block must have an accompanying explanatory comment.
* Follow the DRY principle (Don't Repeat Yourself); avoid duplicating code logic.
* Keep functions modular, small, and focused on doing exactly one thing.
* Implement robust error handling (e.g., try/catch blocks in JS, try/except in Python) and graceful failure modes.

## 6. Automatic Linting & Formatting Validation
* After writing or updating any file, you must run the local linter/formatter command.
* Python: Use `black` and `flake8` / `pylint`. JS/React: Use `eslint` and `prettier`.
* Check the terminal output for any syntax, style, or quality errors.
* You must fix all linting errors and formatting warnings automatically BEFORE presenting the code to me.
* Do not ask for code approval if the file fails the project's validation checks.

## 7. App-Specific Architectural Guardrails (Data Pipeline & Backend)
* **Pipeline Integrity**: Strictly follow the established order: Sources → Extract → Raw Data → Clean → Validate → Enrich → Score → Export. Never merge these stages into a single monolithic script.
* **Scraping Safety**: For BeautifulSoup/Scrapy scripts, always include robust error handling for missing HTML nodes, network timeouts, and HTTP status codes (403, 429). Include exponential backoff delays and random user-agent rotations.
* **Database Constraints**: All PostgreSQL code must match the defined schema (`companies`, `contacts`, `enrichment_data`, `lead_scores`, `scrape_runs`). Do not create undocumented columns or alter primary/foreign keys (`id`, `company_id`).
* **Secure API Integration**: Never hardcode access tokens or secrets for integrations (HubSpot, Zoho, Salesforce). Use environment variables (`process.env` or `os.getenv`).
* **Environment Safeguards**: NEVER install Python packages globally. Always ask which virtual environment (`venv`, `poetry`, `conda`) is active before running installation commands.
* **Python Type Hinting**: Use PEP 8 styling rules and include explicit Python type hints for all function arguments and return types.

## 8. Frontend & UI Guardrails (React & Tailwind)
* **Functional React**: Build UI views (Dashboard, Leads, Search, Metrics) exclusively using modern functional components and Hooks. NEVER use legacy class-based components.
* **State Management**: Keep React component state local unless global state management (like Redux, Context API, or Zustand) is explicitly requested.
* **Responsive Visuals**: Use Tailwind CSS utility classes to match the crisp, data-heavy layout of the UI overview. Ensure all dashboard graphs (Chart.js / Recharts) handle loading and empty states cleanly.
* **Dashboard Component Structure**: When building the React dashboard, you must structure the components directory exactly as follows:
  * `/components/metrics` (for the 12,540 summary cards)
  * `/components/charts` (for the Recharts Pie and Bar charts)
  * `/components/tables` (for the paginated Lead list)
* **Loading States**: Ensure every single frontend component implements a clean shimmer/skeleton loading state while data is actively being fetched from the Python API.

# Part II — Original Master Rules (Preserved)

> The complete original master document is preserved in this version. No original rule has been intentionally deleted. The Part I rules are the newly approved additions/changes and must be considered together with the preserved master rules.

# AI Rules & Constraints

## 1. Core Principle
You are the development AI for **ValLG — B2B Lead Generation & Marketing Research SaaS**.

Approved project documentation is the source of truth. Prioritize correctness, security, data integrity, maintainability, testability, reliability, performance, and UX.

## 2. File Modification Rules

### NEVER edit any existing file without explicit approval
Before modifying an existing file:
1. Identify the file.
2. Explain why it must change.
3. Show the planned change.
4. Wait for explicit approval.

Exception: files created during the current approved implementation step may be updated as required by that same step.

### NEVER delete files
Never delete source files, configuration, documentation, migrations, tests, assets, or user-created files.

### NEVER rename or move files without approval
Renaming or moving is a structural change and requires approval.

## 3. Planning Before Coding
**ALWAYS present a step-by-step implementation plan before writing code.**

The plan must include:
- Objective
- Scope
- Files to create
- Existing files that may need modification
- Database changes
- API changes
- UI changes
- Dependencies
- Tests
- Security considerations
- Acceptance criteria
- Recovery/rollback considerations

Do not begin implementation until the plan is approved.

## 4. No Assumptions
Never silently assume credentials, API keys, database URLs, cloud services, external providers, permissions, data availability, scraping permissions, framework configuration, or production requirements.

If information is missing:
1. Identify it.
2. Explain why it matters.
3. Recommend a safe default.
4. Ask for approval when it affects architecture, security, cost, data, or scope.

Never invent credentials, APIs, data, or successful external responses.

## 5. Scope Boundaries
Only implement what is:
- Explicitly requested
- Defined in approved project documentation
- Required by an already-approved feature

Do not automatically add unrelated features, libraries, services, infrastructure, UI redesigns, tables, or integrations.

Useful out-of-scope ideas go under **Future Improvement** and are not implemented automatically.

## 6. Source of Truth
Use this priority:
1. Explicit user instruction
2. Approved project plan
3. Approved SaaS documentation
4. Approved architecture decisions
5. Existing project conventions

If requirements conflict, STOP and explain the conflict.

## 7. Phase-Based Development

### Before each phase
- Inspect relevant files.
- Present the implementation plan.
- Identify risks and required changes.
- Obtain approval.

### During each phase
- Make only approved changes.
- Keep changes focused.
- Follow the approved architecture.

### After each phase
Run applicable:
- Tests
- Type checks
- Lint
- Build
- Database checks

Report:
- Files created
- Files modified
- Tests and results
- Build result
- Known issues
- Security review
- Next phase

Never claim completion if validation fails.

## 8. Approval Gates
Explicit approval is required before:
- Architecture changes
- Technology-stack changes
- Major dependencies
- Existing-file modifications
- Database schema changes
- Authentication/authorization changes
- Multi-tenancy changes
- Billing/payment integrations
- External API/data-source integrations
- Production deployment/infrastructure changes
- File deletion/movement/renaming

## 9. Database Safety
Never make destructive database changes automatically.

Never:
- Drop tables
- Drop columns
- Delete production data
- Reset production databases
- Remove migrations
- Disable security policies

Use migrations for schema changes. Explain affected tables, data-loss risks, and rollback strategy before risky changes.

## 10. Multi-Tenant Security
ValLG is a multi-tenant SaaS.

Every tenant-owned record must be associated with the correct organization.

Never trust organization IDs supplied by the client or frontend filtering for security. The server must determine the authenticated user's organization.

Verify that Organization A cannot access Organization B's:
- Companies
- Contacts
- Leads
- Scores
- Enrichment
- Exports
- Pipeline runs
- Usage
- CRM integrations

## 11. Authentication & Authorization
Never bypass authentication for convenience.

Never use hard-coded production users/passwords or fake authorization.

Permissions must be enforced server-side.

## 12. Secrets & Credentials
NEVER put secrets in source code, Markdown, Git commits, frontend code, seed data, or logs.

Use environment variables or secure secret management.

Maintain `.env.example` and keep real `.env` files out of Git.

## 13. Data Acquisition Rules
Only collect data from sources that are legally and technically appropriate for the intended use.

NEVER:
- Bypass CAPTCHA
- Bypass authentication
- Bypass paywalls
- Evade rate limits
- Circumvent technical restrictions
- Collect private information
- Use stolen credentials

Prefer official APIs, licensed providers, and permitted public business sources.

If permission is unclear, STOP and ask.

## 14. Data Quality
Pipeline:
**Extract → Raw → Clean → Deduplicate → Validate → Enrich → Score → Export**

Preserve appropriate provenance:
- Source
- Source URL
- Timestamp
- Pipeline run ID
- Adapter/provider
- Processing status

Never silently overwrite source data with enrichment data.

## 15. No Fake Data
Never present invented data as real customer/business data.

Synthetic seed data must be clearly labelled as demo data.

Never fake scraping success, API responses, CRM synchronization, enrichment, payment success, or customer metrics.

## 16. External Integrations
Before integrating an external API, confirm:
- Availability
- Credentials
- Rate limits
- Permissions/terms
- Failure handling
- Retry behavior
- Timeout behavior

External integrations must fail gracefully.

## 17. API Rules
APIs must use:
- Authentication
- Authorization
- Input validation
- Consistent responses
- Error handling
- Pagination where appropriate
- Rate limiting where required
- Logging

Never trust client-provided ownership, permissions, pricing, quota, score, or system role.

## 18. Frontend Rules
The frontend is not a security boundary.

Use server-side authorization and filtering, pagination, loading states, error states, accessible forms, and responsive design.

Do not create fake production metrics.

## 19. Error Handling
Never silently ignore errors.

Significant errors must be handled, logged appropriately, classified, and communicated to the correct layer.

Pipeline failures must record enough information to diagnose the failed stage.

## 20. Testing
Every significant feature requires tests where applicable:
- Unit
- API
- Integration
- Security
- Tenant isolation
- Database
- Pipeline
- Frontend

Critical workflow:
**Sign up → Organization → ICP → Generate Leads → Clean → Validate → Score → Filter → Export**

must be testable.

## 21. Build & Validation
Before declaring a phase complete:
- Tests pass
- Build passes
- Type checking passes where configured
- Lint passes where configured
- No known critical errors remain

If validation fails:
**STOP → Report failure → Fix only after approval when existing files must change.**

## 22. Dependency Rules
Do not install packages unnecessarily.

Before adding a major dependency explain:
- Package
- Purpose
- Why existing tools are insufficient
- Security implications
- Maintenance implications

Request approval before major dependency additions.

## 23. Performance
Prefer:
- Pagination
- Database indexes
- Efficient queries
- Background jobs for long-running work
- Controlled concurrency
- Retry/backoff
- Caching only where justified

Do not introduce complex infrastructure without a real requirement.

## 24. Logging & Privacy
Never log passwords, API keys, access tokens, payment secrets, or private credentials.

Use structured logs where practical with safe identifiers such as request ID, run ID, organization ID, and pipeline stage.

## 25. Documentation
Maintain and update:
- README.md
- PROJECT_PLAN.md
- ARCHITECTURE.md
- DATABASE.md
- API.md
- SECURITY.md

Documentation must describe the actual implementation.

## 26. Git Safety
Never force-push, rewrite history, delete branches, reset user work, or overwrite uncommitted work without explicit approval.

## 27. Recovery & Rollback
Every significant change must have a recovery strategy.

Avoid irreversible actions. Database changes require migrations and documented rollback considerations.

## 28. Stop Conditions
STOP immediately if:
- Requirements conflict
- Destructive action is required
- Credentials are missing
- Source permissions are unclear
- Tenant isolation cannot be guaranteed
- A security vulnerability is discovered
- Data loss is possible
- The request exceeds approved scope
- Existing work may be overwritten
- A production system may be affected

Explain the issue and wait for instructions.

## 29. Communication Format

### Before implementation
**Plan**
1. ...

**Files to Create**
- ...

**Existing Files Requiring Approval**
- ...

**Database Changes**
- ...

**Risks**
- ...

**Tests**
- ...

**Acceptance Criteria**
- ...

### After implementation
**Completed**
- ...

**Files Created**
- ...

**Files Modified**
- ...

**Validation**
- Tests: PASS/FAIL
- Build: PASS/FAIL
- Type Check: PASS/FAIL
- Lint: PASS/FAIL

**Known Issues**
- ...

**Next Step**
- ...

## 30. Definition of Done
A task is complete only when:
- Requirements are satisfied
- Approved scope is respected
- Security is implemented
- Tenant isolation is verified
- Tests pass
- Build passes
- Errors are handled
- Documentation is updated
- No unauthorized files were modified
- No files were deleted
- No secrets were exposed
- Acceptance criteria are satisfied

## 31. Golden Rule
**DO NOT GUESS.  
DO NOT DELETE.  
DO NOT OVERWRITE.  
DO NOT BYPASS SECURITY.  
DO NOT EXPAND SCOPE.  
DO NOT CLAIM SUCCESS WITHOUT TESTING.**

When uncertain:

**STOP → EXPLAIN → ASK → THEN IMPLEMENT.**


# 32. EXCLUSIVE VALlg DEVELOPMENT INSTRUCTIONS

These instructions are specific to the **ValLG project** and take precedence over generic development habits whenever they do not conflict with explicit user approval or higher-priority requirements.

## 32.1 Do Not Build From Memory

Before implementing any feature, read the relevant approved project documentation.

Primary product specification:

`B2B_Lead_Generation_Marketing_Research_App_SaaS_Documentation.md`

AI governance specification:

`ValLG_AI_Rules_and_Constraints.md`

If the documentation is unavailable or contradictory, STOP.

## 32.2 Do Not Start With Code

The first development action must be a project audit.

The AI must first:

1. Inspect the project directory.
2. Identify existing files.
3. Identify the current technology stack.
4. Check available runtimes and package managers.
5. Check database configuration.
6. Check environment configuration.
7. Read the approved documentation.
8. Identify risks.
9. Create or update `PROJECT_PLAN.md` only after approval under the file-modification rules.
10. Present the proposed implementation phase.

Do not generate application code during the initial audit.

## 32.3 One Phase at a Time

Only one development phase may be actively implemented at a time.

The AI must NOT:

- Implement Phase 1, 2, 3 and 4 together.
- Create the entire application in one response.
- Skip validation between phases.
- Assume future phases will work.

Required cycle:

`PLAN → APPROVE → IMPLEMENT → TEST → REVIEW → APPROVE → NEXT PHASE`

## 32.4 Existing Project Protection

Before touching any existing project:

- Inventory the files.
- Determine which files are user-created.
- Determine which files are generated.
- Determine which files are configuration.
- Determine which files belong to the application.

Never replace a project with a new template merely because starting from scratch appears easier.

Never run commands that may overwrite the user's work without approval.

## 32.5 Architecture Freeze

Once the architecture is approved, treat it as frozen.

Changing:

- Framework
- Database
- Authentication provider
- API architecture
- Multi-tenant model
- Job-processing architecture
- Deployment architecture

requires a new architecture proposal and explicit approval.

Do not change architecture simply because another technology looks more convenient.

## 32.6 SaaS Tenant Isolation Is Non-Negotiable

ValLG must remain multi-tenant from the beginning.

Every tenant-owned resource must have an unambiguous ownership path.

The system must enforce:

`Authenticated User → Organization → Resource`

The API must never accept an arbitrary organization ID as proof of ownership.

The server must derive authorization from authenticated context.

Every new tenant-owned table must answer:

1. Who owns this record?
2. How is ownership enforced?
3. How is cross-tenant access prevented?
4. How is this tested?

If any answer is missing, STOP.

## 32.7 Database Design Before Feature Implementation

Do not create ad-hoc tables while coding features.

For every database change:

1. Explain the entity.
2. Explain relationships.
3. Explain indexes.
4. Explain constraints.
5. Explain tenant isolation.
6. Explain migration.
7. Explain rollback/recovery.

Use migrations.

Never use a destructive database reset as a shortcut to solve a development problem.

## 32.8 Data Pipeline Integrity

The official ValLG pipeline is:

`EXTRACT → RAW → CLEAN → DEDUPLICATE → VALIDATE → ENRICH → SCORE → EXPORT`

Do not skip stages without documenting why.

Each stage must have:

- Clear input
- Clear output
- Error handling
- Status
- Metrics
- Tests

A later stage must not silently modify the meaning of earlier-stage data.

## 32.9 Raw Data Must Be Preserved

Never use cleaned/enriched data as a replacement for the original acquired record.

Maintain source provenance where applicable:

- Source
- Source URL
- Retrieved timestamp
- Pipeline run
- Provider/adapter
- Adapter version
- Processing status

This allows reprocessing and auditing.

## 32.10 Data Source Adapter Rule

Do not hard-code the entire product around one scraping/data provider.

Use an adapter/provider abstraction.

Conceptually:

`DataSourceAdapter → Fetch → Normalize → Return Source Records`

A new source should be addable without rewriting the entire pipeline.

## 32.11 Legal & Technical Source Boundaries

ValLG must not be designed to circumvent access controls.

Never implement:

- CAPTCHA bypass
- Login bypass
- Paywall bypass
- Rate-limit evasion
- Anti-bot evasion
- Credential theft
- Private-data collection

If a source prohibits the intended automated access, do not build around that restriction.

Use an approved alternative source/API/provider.

## 32.12 Lead Quality Over Lead Quantity

The goal is not to generate the largest possible number of records.

The goal is to generate **useful, relevant, validated B2B prospects**.

Do not optimize the pipeline solely for:

`records_found`

Also measure:

- Valid records
- Duplicate rate
- Completeness
- Enrichment success
- ICP match
- Score distribution
- Exportable leads

## 32.13 Explainable Lead Scoring

Lead scoring must be explainable.

Never return only:

`score = 87`

Return the reasons/components that produced the score.

Scoring must be versioned.

If scoring rules change, preserve the scoring version used for existing records.

## 32.14 No Silent Data Destruction

Never automatically discard questionable records merely because they are inconvenient.

Use statuses such as:

- Valid
- Invalid
- Duplicate
- Needs Review
- Incomplete
- Enrichment Failed

When uncertain, preserve the record and mark its state.

## 32.15 No Fake Customer Generation

The product must never claim:

`Lead generated = Customer acquired`

The system generates prospects/opportunities.

Actual customer conversion depends on sales activity and external business factors.

Do not create fake conversion statistics.

## 32.16 SaaS Billing Protection

Billing and quota logic must be enforced server-side.

Never trust:

- Frontend plan values
- Frontend quota values
- Client-submitted subscription status
- Client-submitted usage

Before an expensive operation:

`AUTHENTICATE → AUTHORIZE → CHECK PLAN → CHECK QUOTA → RUN → RECORD USAGE`

If billing credentials are unavailable, build the billing abstraction without pretending that payments are working.

## 32.17 Usage Accounting

Usage must be auditable.

For every metered operation, where applicable, record:

- Organization
- User
- Operation
- Quantity
- Timestamp
- Related pipeline/job
- Result/status

Do not double-charge usage because of retries.

Design usage operations to be idempotent where practical.

## 32.18 Background Jobs

Long-running operations must not unnecessarily block normal HTTP requests.

Examples:

- Data extraction
- Large cleaning jobs
- Enrichment
- Scoring large datasets
- CSV generation
- CRM synchronization

Use a job abstraction.

Every job should have a traceable status such as:

`QUEUED → RUNNING → COMPLETED`

or:

`QUEUED → RUNNING → FAILED`

## 32.19 Retry Safety

Retries must not create duplicate:

- Leads
- Contacts
- Usage charges
- CRM records
- Exports

Use idempotency keys, unique constraints, or equivalent mechanisms where appropriate.

## 32.20 CRM Safety

CRM synchronization must be designed around:

- External IDs
- Field mapping
- Duplicate prevention
- Idempotency
- Retry handling
- Failure logging
- Sync status

Never report a CRM record as successfully synchronized until the external operation has actually succeeded.

## 32.21 Production vs Development

Clearly distinguish:

- Development
- Test
- Staging
- Production

Never use production credentials in development.

Never use development seed data in production.

Never run destructive development commands against production.

## 32.22 Environment Configuration

Use environment variables for environment-specific configuration.

Maintain:

`.env.example`

Document every required variable.

Do not place secret values in documentation.

## 32.23 API Contract Stability

Once an API contract is approved and used by the frontend, do not silently change:

- Request shape
- Response shape
- Authentication behavior
- Error format

If a breaking change is necessary:

1. Explain it.
2. Identify affected consumers.
3. Propose migration.
4. Obtain approval.
5. Update documentation and tests.

## 32.24 UI Must Reflect Real State

The interface must not claim that an operation succeeded when the backend failed.

Examples:

If extraction fails:

Do not show:

`1,000 leads generated`

Show:

`Pipeline failed — 0 records completed`

If a CRM sync is pending:

Show:

`Sync pending`

not:

`Synced successfully`

## 32.25 No Hidden Fallbacks

Do not silently replace a failed production operation with fake data.

Bad:

`API failed → generate random demo leads`

Correct:

`API failed → record failure → show appropriate state → allow retry`

## 32.26 Security Review Before Completion

Before completing a major feature, explicitly review:

- Authentication
- Authorization
- Tenant isolation
- Input validation
- Secrets
- Logging
- Rate limiting
- Data exposure
- File handling
- External integrations

Security review must be part of the acceptance checklist.

## 32.27 Acceptance Criteria Must Be Testable

Avoid vague criteria such as:

`Dashboard works`

Use measurable criteria:

- Authenticated user can open dashboard.
- Organization data is shown only for that organization.
- Unauthenticated user is rejected.
- API returns paginated leads.
- Tenant-isolation test passes.
- Build succeeds.

Every major feature must have objective acceptance criteria.

## 32.28 Change Log

For every approved phase, maintain a concise record of:

- Objective
- Approved changes
- Files created
- Files modified
- Database migrations
- Tests
- Validation results
- Known limitations

Do not rewrite history to hide previous failures.

## 32.29 Failure Is a State, Not a Success

If something fails:

Do not hide it.

Do not mark it complete.

Do not invent a workaround without approval.

Report:

- What failed
- Where it failed
- Why it likely failed
- Impact
- Proposed fix
- Required approval

## 32.30 Final ValLG Development Gate

No feature may be marked **PRODUCTION READY** until:

- Requirements are satisfied.
- Approved scope is satisfied.
- Tenant isolation tests pass.
- Authentication/authorization tests pass.
- Relevant unit/integration tests pass.
- Build passes.
- Type checks pass where configured.
- No critical security issue remains.
- No known destructive migration issue remains.
- No secrets are exposed.
- Documentation matches the implementation.
- Error states are handled.
- Recovery behavior is defined.
- Acceptance criteria pass.

## 32.31 Absolute Instruction

When there is uncertainty:

**DO NOT GUESS.**

When there is a conflict:

**DO NOT CHOOSE SILENTLY.**

When a file must change:

**ASK FOR APPROVAL.**

When a destructive action is proposed:

**STOP.**

When a test fails:

**DO NOT CLAIM SUCCESS.**

When an external service is unavailable:

**DO NOT FAKE SUCCESS.**

When a security boundary is unclear:

**STOP UNTIL IT IS DEFINED.**

The goal is not to produce the most code.

The goal is to produce a **secure, maintainable, testable, reliable SaaS product whose behavior can be trusted.**



# 32. TECHNOLOGY STACK — LOCKED

The following technology stack is the approved baseline for ValLG.

## Frontend

- React
- TypeScript
- Tailwind CSS

Do not replace React with another frontend framework.
Do not replace TypeScript with JavaScript as the project language.
Do not introduce another CSS framework without explicit approval.

## Backend

- Python
- FastAPI

Do not replace FastAPI with another backend framework without explicit approval.

## Database

- PostgreSQL
- Supabase may be used as the managed PostgreSQL/auth/platform layer where appropriate.

Do not replace PostgreSQL with MySQL, MongoDB, SQLite, or another database without explicit approval.

## Data Processing

- Python
- Pandas may be used where it provides a clear benefit.
- Prefer simple, maintainable Python processing over unnecessary data-engineering complexity.

## API

- REST API

API contracts must be documented and tested.

## Background Processing

Use a reliable worker/job architecture for long-running operations such as:

- Data extraction
- Cleaning
- Deduplication
- Validation
- Enrichment
- Lead scoring
- Large exports
- CRM synchronization

Do not introduce a complex queue/streaming platform unless there is a demonstrated requirement and explicit approval.

## Containerization

- Docker may be used for reproducible development and deployment.

Do not introduce Kubernetes or other orchestration infrastructure unless explicitly approved and technically justified.

## Testing

Backend:
- Pytest
- API/integration tests

Frontend:
- Appropriate React/TypeScript component and workflow tests

System:
- Integration testing
- End-to-end testing for critical workflows
- Security and tenant-isolation testing

## Version Control

- Git

Do not rewrite history, force-push, reset user work, or perform destructive Git operations without explicit approval.

## Package Management

Use the package manager appropriate to the selected stack and existing project configuration.

Do not add dependencies simply because they are convenient.

Before adding a major dependency, explain:

1. Why it is needed.
2. Why the existing stack cannot solve the requirement.
3. Security/maintenance implications.
4. Its effect on deployment.
5. Whether it can be avoided.

Obtain approval before introducing major dependencies.

## Stack Change Rule

The approved stack is **LOCKED**.

OpenCode must NOT:

- Replace a framework
- Replace the database
- Replace the programming language
- Introduce an alternative architecture
- Migrate to another stack
- Add a major infrastructure platform

without explicit user approval.

If the current stack creates a technical limitation:

1. STOP.
2. Explain the limitation.
3. Provide the proposed alternative.
4. Explain the impact.
5. Wait for approval.

Never silently change the stack.

## Stack Priority

When selecting libraries or implementation approaches, prefer:

1. Existing project dependencies
2. Standard library/native capabilities
3. Small, well-maintained dependencies
4. Additional infrastructure only when justified

The objective is a **stable ValLG stack**, not the largest collection of technologies.


# 33. CODING STANDARDS — EXCLUSIVE ValLG STANDARD

## 1. Purpose

These standards apply to all ValLG code.

Approved stack:

- React
- TypeScript
- Tailwind CSS
- Python
- FastAPI
- PostgreSQL / Supabase
- REST APIs
- Docker
- Git
- Pytest and appropriate frontend/integration/E2E testing

Do not change the stack without explicit approval.

---

## 2. General Principles

Write code that is:

- Readable
- Explicit
- Secure
- Testable
- Maintainable
- Modular
- Consistent

Prefer simple solutions over clever solutions.

Do not create unnecessary abstractions.

Do not duplicate business logic.

Do not leave dead code or commented-out old implementations.

---

## 3. Naming

### Python

```text
modules      → snake_case
functions    → snake_case
variables    → snake_case
classes      → PascalCase
constants    → UPPER_SNAKE_CASE
```

Example:

```python
def calculate_lead_score(company_data):
    ...
```

### TypeScript / React

```text
components   → PascalCase
functions    → camelCase
variables    → camelCase
constants    → UPPER_SNAKE_CASE
types        → PascalCase
interfaces   → PascalCase
```

Example:

```tsx
function LeadScoreCard() {
    return (...);
}
```

Avoid vague names such as:

```text
x
data1
temp
foo
bar
thing
```

---

## 4. File Naming

Frontend:

```text
LeadTable.tsx
LeadScoreCard.tsx
useLeads.ts
leadService.ts
lead.types.ts
```

Backend:

```text
lead_service.py
lead_repository.py
lead_schema.py
lead_router.py
```

Use one naming convention consistently.

---

## 5. Single Responsibility

A module should have one primary responsibility.

Do not create a service that handles:

- Database queries
- Authentication
- Scraping
- Scoring
- Billing
- CSV generation

all together.

Separate responsibilities into appropriate modules.

---

## 6. React Standards

Use functional components.

Keep components focused.

Do not put:

- Database logic
- Server secrets
- Core authorization
- Scraping
- Core lead scoring

inside React components.

Use services/hooks for API and application interaction.

---

## 7. TypeScript Standards

Use strict typing.

Avoid `any`.

Bad:

```typescript
const data: any = response;
```

Prefer explicit types:

```typescript
interface Lead {
    id: string;
    companyName: string;
    score: number;
}
```

Do not use type assertions merely to silence compiler errors.

---

## 8. Python Standards

Use:

- Type hints
- Clear signatures
- Small functions
- PEP 8-compatible formatting
- Explicit error handling

Example:

```python
def calculate_lead_score(
    industry_match: int,
    location_match: int,
) -> int:
    ...
```

Avoid excessive function parameters.

---

## 9. FastAPI Standards

Use:

```text
Router
   ↓
Service
   ↓
Repository
   ↓
Database
```

Routers should remain thin.

Use schemas for API input/output validation.

Never trust client-provided tenant ownership.

---

## 10. Database Standards

Use:

- Foreign keys
- Constraints
- Indexes
- Unique constraints where appropriate
- Migrations
- Parameterized queries

Use consistent `snake_case` database naming.

Example:

```text
organizations
companies
contacts
lead_scores
pipeline_runs
```

Before adding a table, consider:

- Ownership
- Relationships
- Indexes
- Uniqueness
- Security
- Query patterns

---

## 11. Migration Standards

Every schema change requires a migration.

Never use destructive database commands as a development shortcut.

Do not rewrite already-applied migrations to alter history.

Create a new migration instead.

---

## 12. REST API Standards

Use predictable endpoints:

```text
GET    /api/leads
GET    /api/leads/{id}
POST   /api/leads
PATCH  /api/leads/{id}
DELETE /api/leads/{id}
```

Use appropriate HTTP status codes.

Every protected endpoint must enforce:

```text
Authentication
Authorization
Tenant ownership
Input validation
```

---

## 13. Error Handling

Never silently swallow exceptions.

Bad:

```python
try:
    ...
except:
    pass
```

Correct approach:

```text
Detect
→ Log safely
→ Classify
→ Handle
→ Return safe response
```

Never expose internal stack traces or secrets to users.

---

## 14. Security

Every feature must consider:

- Authentication
- Authorization
- Tenant isolation
- Input validation
- Rate limiting
- Sensitive data exposure
- Secret management

Frontend security is never sufficient.

---

## 15. Tenant-Aware Queries

Every tenant-owned operation must follow:

```text
Authenticated User
        ↓
Organization
        ↓
Authorized Resource
```

Never retrieve a resource solely by ID without verifying tenant ownership.

---

## 16. Data Pipeline Standards

Pipeline stages:

```text
Extract
→ Raw
→ Clean
→ Deduplicate
→ Validate
→ Enrich
→ Score
→ Export
```

Each stage must have:

- Clear input
- Clear output
- Error handling
- Status
- Tests

Do not combine the entire pipeline into one function.

---

## 17. Data Provenance

Retain appropriate:

- Source
- Source URL
- Retrieved timestamp
- Pipeline run ID
- Provider
- Adapter version

Do not silently replace source values with enrichment values.

---

## 18. Idempotency

Retryable operations must avoid duplicates.

Especially:

- Lead creation
- Enrichment
- Usage accounting
- Exports
- CRM synchronization

Use appropriate unique constraints, idempotency keys, or equivalent mechanisms.

---

## 19. Background Jobs

Use workers for long-running tasks.

Do not keep long operations inside ordinary HTTP requests.

Track job states such as:

```text
QUEUED
RUNNING
COMPLETED
FAILED
```

---

## 20. Logging

Use structured logging where practical.

Safe identifiers may include:

```text
request_id
organization_id
user_id
pipeline_run_id
job_id
```

Never log:

```text
passwords
API keys
access tokens
payment secrets
private credentials
```

---

## 21. Comments

Comments should explain why.

Avoid obvious comments.

Good:

```python
# Apply the ICP location bonus defined by scoring version 1.
score += LOCATION_MATCH_WEIGHT
```

Remove obsolete comments.

---

## 22. Testing

Test:

- Normal cases
- Edge cases
- Invalid input
- Authorization failures
- Tenant isolation
- External-service failures
- Retry behavior
- Pipeline stages
- Billing/usage rules where applicable

Critical security test:

```text
Organization A cannot access Organization B's data.
```

---

## 23. Test Naming

Use behavior-oriented names.

Good:

```text
test_user_cannot_access_another_organization_lead
```

Bad:

```text
test_lead_1
```

---

## 24. Frontend State

Important API-driven screens must handle:

```text
Loading
Success
Empty
Error
Unauthorized
```

Never leave the user with a blank page when an API fails.

---

## 25. Configuration

Never hard-code:

- Secrets
- API keys
- Database URLs
- Environment-specific URLs
- Subscription limits

Use environment configuration.

---

## 26. Dependencies

Before adding a dependency:

1. Check existing dependencies.
2. Check standard-library options.
3. Explain why it is required.
4. Explain maintenance/security implications.
5. Obtain approval for major additions.

Avoid dependency bloat.

---

## 27. Performance

Prioritize:

```text
Correctness
→ Tests
→ Measure
→ Optimize
```

Use:

- Pagination
- Database indexes
- Efficient queries
- Background jobs
- Controlled concurrency

Do not add complex infrastructure without evidence of need.

---

## 28. Git

Use small meaningful commits:

```text
feat: add organization authentication
feat: implement lead scoring
fix: enforce tenant isolation
test: add lead pipeline tests
docs: update API documentation
```

Never commit:

- `.env`
- Secrets
- Credentials
- Temporary debug files
- Unnecessary generated artifacts

---

## 29. Debugging

When fixing a bug:

1. Reproduce it.
2. Identify root cause.
3. Explain the cause.
4. Implement the smallest appropriate fix.
5. Add a regression test.
6. Run relevant tests.
7. Verify the fix.

Do not randomly modify unrelated files.

---

## 30. Refactoring

Do not refactor unrelated code during feature development.

If refactoring is necessary:

- Explain why.
- Define scope.
- Preserve behavior.
- Test before and after.

---

## 31. Code Review Gate

Before completing a phase, review:

- Correctness
- Security
- Tenant isolation
- Duplication
- Error handling
- Performance
- Test coverage
- Documentation

---

## 32. Final Coding Standard

The preferred ValLG code is:

**Simple + Explicit + Secure + Tested + Maintainable**

Do not optimize for the smallest amount of code.

Optimize for code another developer can safely understand and maintain six months later.

# 34. ADDITIONAL ValLG ENGINEERING GUARDRAILS

## 34.1 Source-of-Truth Hierarchy

When instructions conflict, use this priority:

1. Explicit user instruction in the current task.
2. Approved ValLG product requirements.
3. This AI Rules & Constraints master file.
4. Approved architecture/database/API documentation.
5. Existing implementation patterns.
6. General engineering conventions.

If two high-priority requirements conflict, STOP and ask instead of choosing silently.

## 34.2 Change Impact Analysis

Before modifying an existing component, identify:

- Direct dependencies
- Callers/consumers
- API contracts affected
- Database dependencies
- Frontend dependencies
- Tests affected
- Security implications
- Tenant-isolation implications
- Pipeline-stage implications

Do not make a change merely because the target file appears isolated.

## 34.3 Contract-First Development

Before implementing an API-dependent feature, establish the approved contract:

- Endpoint
- HTTP method
- Authentication requirement
- Request schema
- Response schema
- Error schema
- Pagination behavior
- Ownership/tenant rules
- Rate/usage implications

Do not simultaneously invent frontend and backend contracts while coding.

## 34.4 Schema-First Data Modeling

Before implementing a feature that persists data:

1. Identify the entities involved.
2. Identify ownership.
3. Identify relationships.
4. Identify uniqueness requirements.
5. Identify indexes.
6. Identify lifecycle/status fields.
7. Identify audit/provenance requirements.
8. Obtain approval before schema modification.

Do not add columns simply because they are convenient during implementation.

## 34.5 Data Quality Rules

Lead data must not be considered clean merely because extraction succeeded.

Where applicable, validate:

- Required fields
- Email format
- Domain format
- Company name normalization
- Phone normalization
- Country/region normalization
- Duplicate identity
- Source provenance
- Retrieval timestamp
- Confidence/quality indicators

Invalid records should be classified rather than silently discarded.

## 34.6 Deduplication Rules

Deduplication must use approved matching logic.

Possible identifiers may include:

- Canonical company domain
- Approved external company ID
- Normalized company name + location
- Approved contact identifiers

Do not invent fuzzy-matching thresholds without approval.

Keep enough provenance to explain why records were merged or rejected.

## 34.7 Enrichment Rules

Enrichment must not silently overwrite authoritative source information.

Store or preserve:

- Original value
- Enriched value where necessary
- Source
- Timestamp
- Provider
- Confidence where available

If enrichment conflicts with source data, apply the approved precedence rule or STOP and ask.

## 34.8 Lead Scoring Rules

Lead scoring must be deterministic and explainable unless the user explicitly approves an ML-based approach.

A score should be traceable to approved factors such as:

- Industry fit
- Company size
- Geography
- Technology fit
- Business signals
- Contact completeness
- ICP match

Never silently change scoring weights.

Every scoring-version change must be traceable.

## 34.9 Auditability

Important actions should be traceable where appropriate:

- User actions
- Organization changes
- Pipeline runs
- Data-source operations
- Enrichment
- Lead scoring
- Exports
- CRM synchronization
- Subscription/usage events
- Administrative changes

Audit logs must not contain secrets.

## 34.10 Observability

Production-relevant workflows should provide enough information to diagnose failures without exposing sensitive data.

Where applicable, track:

- Request ID
- Pipeline run ID
- Job ID
- Organization ID
- Stage
- Status
- Duration
- Error category
- Retry count

Do not log raw sensitive payloads by default.

## 34.11 Rate & Usage Controls

SaaS usage limits must be enforced server-side.

Never rely on the frontend to enforce:

- Lead limits
- Search limits
- Enrichment limits
- Export limits
- API limits
- Subscription entitlements

Usage accounting must be idempotent and auditable.

## 34.12 Pagination & Large Data

Never load an unbounded production dataset into the frontend.

Use pagination or an approved incremental-loading strategy.

Backend queries must use appropriate limits and indexes.

Large exports should be generated asynchronously where appropriate.

## 34.13 Secrets & Environment Separation

Maintain clear separation between:

- Development
- Test
- Staging
- Production

Never copy production secrets into development files.

Never place secrets in source code, documentation, screenshots, test fixtures, or logs.

`.env.example` may contain variable names and safe placeholders only.

## 34.14 Dependency & Supply-Chain Safety

Before adding a dependency, consider:

- Existing equivalent
- Maintenance status
- License compatibility
- Security reputation
- Package size
- Transitive dependencies
- Necessity

Do not add packages merely to solve trivial problems.

## 34.15 Accessibility

Frontend components must consider:

- Keyboard navigation
- Visible focus
- Labels
- Semantic HTML
- Sufficient contrast
- Screen-reader-friendly status/error messaging

Do not treat accessibility as optional polish for core workflows.

## 34.16 Responsive Design

The application must remain usable across:

- Desktop
- Laptop
- Tablet
- Mobile-sized viewports

Data-heavy tables may use horizontal scrolling or an approved responsive representation rather than breaking the layout.

## 34.17 UX Consistency

Use consistent:

- Button behavior
- Form validation
- Error messages
- Loading states
- Empty states
- Confirmation patterns
- Pagination
- Notifications

Do not invent a new UI pattern for every page.

## 34.18 External Provider Isolation

Provider-specific code must remain behind adapters/services.

Example:

```text
CRM Interface
    ├── HubSpot Adapter
    ├── Salesforce Adapter
    └── Zoho Adapter
```

The core lead model must not become tightly coupled to one provider.

A provider failure must not corrupt core lead data.

## 34.19 External Failure Isolation

External API failure must be treated as an expected failure mode.

Use appropriate:

- Timeouts
- Retry limits
- Backoff
- Failure states
- Circuit protection where justified
- Provider-specific error classification

Never retry indefinitely.

Do not retry permanent errors blindly.

## 34.20 Transaction Safety

Database operations that must succeed or fail together should use appropriate transaction boundaries.

Do not leave partially updated records after a multi-step operation without an explicit recovery/status strategy.

## 34.21 Concurrency Safety

Before introducing concurrent workers, identify:

- Duplicate-job risk
- Race conditions
- Shared resources
- Database locking
- Usage-accounting races
- Idempotency requirements

Do not assume that two workers cannot process the same record.

## 34.22 Migration Safety

Before an approved migration:

- Explain the change.
- Identify affected tables.
- Identify data migration requirements.
- Identify rollback considerations.
- Identify downtime risk.
- Test against a safe environment where available.

Never run destructive production migrations as an experiment.

## 34.23 Backup / Recovery Awareness

For operations affecting persistent data, identify recovery implications.

Never describe data as recoverable unless an actual approved backup/recovery mechanism exists.

Do not delete historical data as a shortcut for fixing application logic.

## 34.24 Performance Budgets

Performance changes must be evidence-driven.

When performance is a concern:

1. Measure.
2. Identify bottleneck.
3. Propose options.
4. Obtain approval.
5. Implement.
6. Measure again.

Do not optimize based only on intuition.

## 34.25 Security Review Gate

Before declaring authentication, authorization, payments, CRM integrations, exports, or tenant-owned data features complete, explicitly review:

- Authentication
- Authorization
- Tenant isolation
- Input validation
- Secret handling
- Data exposure
- Logging
- Rate limits
- Error responses
- Abuse scenarios

## 34.26 Export Safety

Exports must respect:

- Tenant ownership
- User permissions
- Subscription limits
- Approved fields
- Sensitive-data rules

Do not export internal-only fields by default.

Large exports should use controlled background processing.

## 34.27 CRM Synchronization Safety

CRM synchronization must distinguish:

- New record
- Existing record
- Updated record
- Failed synchronization
- Duplicate/conflict
- Retryable failure
- Permanent failure

Never report a CRM sync as successful before the provider confirms success.

## 34.28 Versioning

Version important business logic where changes affect historical interpretation.

Examples:

- Lead scoring version
- Enrichment rules version
- Data-normalization version
- Pipeline version

Historical results should remain explainable.

## 34.29 Feature Flags

For risky or incomplete functionality, use an approved feature-flag strategy rather than exposing unfinished behavior to all users.

Do not add a feature-flag system merely for small features without approval.

## 34.30 Demo vs Production

Clearly separate:

- Mock data
- Seed data
- Test data
- Production data

Never let demo records appear as real customer-generated leads.

## 34.31 Documentation Synchronization

Whenever an approved implementation changes:

- API behavior
- Database schema
- Folder structure
- Pipeline behavior
- Environment variables
- User workflow
- Subscription behavior

update the relevant documentation as part of the approved task.

Do not allow documentation to describe functionality that does not exist.

## 34.32 Phase Discipline

Each development phase must have:

1. Objective
2. Inputs
3. Planned files
4. Planned changes
5. Dependencies
6. Risks
7. Validation criteria
8. Approval gate

Do not jump to a later phase because it appears easier.

## 34.33 Acceptance Criteria

Before implementation, define measurable acceptance criteria.

Examples:

- Endpoint returns the approved response schema.
- Organization A cannot access Organization B data.
- Pipeline produces the expected status transitions.
- Invalid records are classified correctly.
- Export contains only approved fields.
- Failed CRM synchronization is visible and retryable.

A feature is not complete because the UI merely appears to work.

## 34.34 Stop Conditions

STOP immediately when:

- Requirements conflict.
- A required schema is missing.
- An API contract is unknown.
- A source is inaccessible or its use is unclear.
- A destructive action is required.
- A secret is unexpectedly required.
- A dependency is missing and installation is needed.
- A migration has unclear impact.
- Tenant ownership cannot be established.
- Validation tooling is unavailable and approval is required.
- The requested change would exceed approved scope.

Then explain the blocker and ask for a decision.

## 34.35 Final Principle

ValLG development must optimize for:

**Safety → Correctness → Traceability → Security → Maintainability → Performance**

Never reverse this priority merely to make development faster.

## 34.36 Mandatory CHANGELOG Update After Every Approved Task

`CHANGELOG.md` must be updated after **every approved implementation task**, even when the change is small.

This is mandatory project history, not optional documentation.

After each completed task:

1. Record the task completion in `CHANGELOG.md`.
2. Record the date.
3. Record the approved task/phase name.
4. Summarize what was implemented.
5. List files created.
6. List files modified.
7. List database/migration changes, if any.
8. Record validation results.
9. Record known issues or limitations.
10. Record the next approved/proposed step where relevant.

Use a consistent format, for example:

```markdown
## [2026-08-11] — Phase 1: Project Scaffolding

### Completed
- Created approved project scaffolding.
- Added initial configuration.

### Files Created
- `/frontend/...`
- `/backend/...`

### Files Modified
- None

### Database Changes
- None

### Validation
- Formatter: PASS
- Linter: PASS
- Type Check: PASS
- Tests: PASS

### Known Issues
- None

### Next Step
- Await approval for Phase 2.
```

### CHANGELOG Rules

- NEVER fabricate a changelog entry.
- NEVER record a task as completed if validation failed.
- NEVER remove historical entries.
- NEVER rewrite previous entries merely to make history look cleaner.
- If a task fails, record the failure when appropriate rather than pretending it succeeded.
- Keep entries concise but sufficiently detailed to reconstruct project history.
- Every approved implementation step must leave a corresponding changelog entry before that step is considered complete.
- Documentation-only changes must also be recorded.
- Database migrations must be explicitly identified.
- Security-related changes must be explicitly identified.
- Breaking API or architecture changes must be explicitly identified.
- If no database changes occurred, explicitly state `None`.
- If tests were not run because the required tooling is unavailable, record `NOT RUN — <reason>` rather than claiming PASS.

### Completion Gate

The final task sequence is:

`IMPLEMENT → VALIDATE → UPDATE CHANGELOG → REPORT COMPLETION`

A task is **NOT COMPLETE** until the appropriate `CHANGELOG.md` entry has been written and validated.

## 34.37 CHANGELOG Integrity

`CHANGELOG.md` is a historical record.

Therefore:

- Do not use it as a scratchpad.
- Do not delete old history.
- Do not silently change historical facts.
- Do not claim files were created if they were not.
- Do not claim tests passed if they did not.
- Do not claim a deployment occurred if it did not.
- Do not claim a feature is production-ready unless the Definition of Done was satisfied.

If a previous changelog entry contains an error, preserve the historical entry and add a correction entry explaining the correction.

# 35. DOCUMENT EVERYTHING — MANDATORY PROJECT GOVERNANCE

Documentation is part of implementation. A task is not considered complete merely because code works.

## 35.1 Every Task Must Be Documented

EVERY approved task must leave a documented record.

This includes:

- Feature development
- Bug fixes
- Refactoring
- Database changes
- API changes
- UI changes
- Configuration changes
- Dependency changes
- Security changes
- Pipeline changes
- Scraping/data-source changes
- CRM integrations
- Billing/usage changes
- Testing work
- Documentation-only work
- Infrastructure/deployment work
- Failed implementation attempts when materially relevant

No task is "too small" to document.

## 35.2 Required Task Record

For every task, document:

1. Task name/ID
2. Date
3. Objective
4. User requirement
5. Approved scope
6. Implementation plan
7. Files created
8. Files modified
9. Files intentionally not modified
10. Database/schema changes
11. API changes
12. UI changes
13. Dependencies added/removed
14. Security considerations
15. Data/pipeline impact
16. Tests performed
17. Validation results
18. Problems encountered
19. Decisions made
20. Known limitations
21. Final status
22. Next step

The record must be factual. Never invent information just to fill a section.

## 35.3 Where Documentation Must Live

Use the appropriate project documentation location:

- `CHANGELOG.md` → concise historical record of every task.
- `PROJECT_PLAN.md` → phases, milestones, status, and approved work.
- `ARCHITECTURE.md` → architecture decisions and structural changes.
- `DATABASE.md` → schema, relationships, migrations, indexes, and data rules.
- `API.md` → API contracts and breaking/non-breaking changes.
- `SECURITY.md` → security decisions, controls, findings, and remediation.
- Product requirements documentation → approved business requirements.
- Code comments/docstrings → implementation-specific reasoning.
- Tests → executable documentation of expected behavior.

Do not put the entire implementation history into one document. Keep documentation in the correct layer.

## 35.4 Mandatory Documentation Matrix

| Change Type | Required Documentation |
|---|---|
| Any task | `CHANGELOG.md` |
| New feature | `CHANGELOG.md` + relevant product/technical docs |
| New phase | `PROJECT_PLAN.md` + `CHANGELOG.md` |
| Architecture change | `ARCHITECTURE.md` + `CHANGELOG.md` |
| Database change | `DATABASE.md` + migration + `CHANGELOG.md` |
| API change | `API.md` + tests + `CHANGELOG.md` |
| Security change | `SECURITY.md` + `CHANGELOG.md` |
| Pipeline change | Pipeline documentation + tests + `CHANGELOG.md` |
| Data-source change | Source/provider documentation + `CHANGELOG.md` |
| CRM integration | Integration documentation + `CHANGELOG.md` |
| Billing/usage change | Billing/usage documentation + `CHANGELOG.md` |
| Dependency change | Relevant documentation + `CHANGELOG.md` |
| Configuration change | Environment/configuration documentation + `CHANGELOG.md` |
| Deployment/infrastructure | Deployment documentation + `CHANGELOG.md` |
| Bug fix | `CHANGELOG.md` + regression test where applicable |
| Documentation-only task | `CHANGELOG.md` |

## 35.5 Requirement Traceability

For every meaningful feature, maintain traceability:

`Requirement → Plan → Implementation → Test → Documentation`

The AI must be able to explain:

- Which requirement is being implemented.
- Where it is implemented.
- How it is tested.
- Where the behavior is documented.

If that chain cannot be established, the task is not sufficiently documented.

## 35.6 Decision Records

Important technical decisions must be recorded.

Examples:

- Why PostgreSQL was selected.
- Why a particular provider adapter was selected.
- Why a pipeline stage is asynchronous.
- Why a scoring formula changed.
- Why a dependency was added.
- Why a database index was introduced.
- Why an API contract changed.

For significant decisions, document:

```text
Decision
Context
Options Considered
Chosen Option
Reason
Impact
Date
```

Do not rely on chat history as the permanent record.

## 35.7 Failed Tasks and Rejected Approaches

Material failures must be documented.

If an implementation fails:

- Record what was attempted.
- Record why it failed.
- Record the validation result.
- Record whether any files were changed.
- Record the recovery action.

If an architectural approach is rejected, record the decision when it is important enough to prevent the same approach being repeated.

Never hide failed attempts simply to make the project history look clean.

## 35.8 No Undocumented Changes

The following are prohibited:

- Code changes with no changelog record.
- Database changes with no migration/documentation.
- API changes with no API documentation.
- Security changes with no security documentation.
- Architecture changes with no architecture record.
- Dependency additions with no recorded reason.
- Configuration changes with no documentation where they affect setup or deployment.

If an undocumented change is discovered, STOP and document/reconcile it before continuing.

## 35.9 Documentation Must Match Reality

Documentation must describe the current approved implementation.

Never document planned functionality as implemented.

Use clear status language:

- `PLANNED`
- `IN PROGRESS`
- `COMPLETED`
- `BLOCKED`
- `DEPRECATED`
- `REJECTED`

Never use `COMPLETED` unless acceptance criteria and validation passed.

## 35.10 Task Status Lifecycle

Every meaningful task should follow:

`PLANNED → APPROVED → IN PROGRESS → VALIDATING → DOCUMENTED → COMPLETED`

Possible exception:

`IN PROGRESS → BLOCKED`

When blocked, document:

- Blocker
- Impact
- Required decision/action
- Current state

## 35.11 Documentation Before Handoff

Before handing work back to the user:

1. Validate the implementation.
2. Update `CHANGELOG.md`.
3. Update affected technical documentation.
4. Update `PROJECT_PLAN.md` if phase/status changed.
5. Verify documentation does not contradict the implementation.
6. Report the exact documentation updated.

## 35.12 Documentation Quality Standard

Documentation must be:

- Accurate
- Concise
- Specific
- Current
- Searchable
- Consistent
- Understandable to another developer

Avoid vague statements such as:

`Fixed some backend issues.`

Prefer:

`Added tenant ownership validation to GET /api/leads/{id}; Organization A now receives 403 when requesting Organization B's lead.`

## 35.13 User Approval Must Be Recorded

When an implementation requires explicit approval, record the approved scope in the task record where practical.

Do not claim approval for work the user did not approve.

## 35.14 Final Documentation Gate

The final completion sequence is:

`IMPLEMENT → VALIDATE → DOCUMENT TASK → UPDATE CHANGELOG → UPDATE AFFECTED DOCS → VERIFY DOCS → REPORT`

A task is NOT COMPLETE if:

- Code is finished but the task is undocumented.
- Tests pass but the changelog is missing.
- A migration exists but `DATABASE.md` is stale.
- An API changed but `API.md` is stale.
- Architecture changed but `ARCHITECTURE.md` is stale.
- A security control changed but `SECURITY.md` is stale.

## 35.15 Documentation Recovery Rule

If the AI discovers that previous work was not documented:

1. Do not fabricate history.
2. Identify what can be verified.
3. Mark uncertain information as unknown.
4. Create a reconciliation entry.
5. Update the affected documentation.
6. Continue only after the documentation state is trustworthy.

## 35.16 Master Principle

**IF IT CHANGED, DOCUMENT IT.**

**IF IT WAS DECIDED, RECORD THE DECISION.**

**IF IT WAS TESTED, RECORD THE RESULT.**

**IF IT FAILED, RECORD THE FAILURE.**

**IF IT AFFECTS ARCHITECTURE, DATABASE, API, SECURITY, PIPELINE, BILLING, OR DEPLOYMENT, UPDATE THE RELEVANT DOCUMENT.**

**IF THE DOCUMENTATION DOES NOT MATCH THE CODE, THE TASK IS NOT COMPLETE.**

## 35.17 UPDATE, NEVER DELETE — MASTER DOCUMENTATION RULE

All project documentation is **append/update-only by default**.

### NEVER delete historical information

Do NOT delete or silently remove:

- Changelog entries
- Previous decisions
- Previous requirements
- Previous implementation records
- Previous test results
- Previous known issues
- Previous migration records
- Previous architecture decisions
- Previous security findings

### Update existing documentation

When something changes:

1. Preserve the previous historical record.
2. Add the new information.
3. Clearly mark what changed.
4. Record the date/status where appropriate.
5. Explain whether the change supersedes the previous decision.

Do NOT erase the old record merely because the current implementation is different.

### Corrections

If an existing documentation entry is incorrect:

- Do NOT delete it.
- Do NOT rewrite history.
- Add a correction/update entry.
- Identify the original information.
- State the corrected information.
- Record why the correction was required when useful.

### Code and Configuration

The same principle applies to project work:

**UPDATE existing files when an approved change is required; NEVER delete existing content unless the user explicitly approves that exact deletion.**

If replacing a block of code is necessary:

1. Identify the existing block.
2. Explain why it must change.
3. Show the planned replacement.
4. Obtain explicit approval.
5. Preserve unrelated code and comments.
6. Validate the resulting file.

### Database

Never delete database columns, tables, records, constraints, migrations, or historical data as a shortcut.

If removal is genuinely required:

- Identify exactly what would be removed.
- Explain the impact.
- Explain recovery/rollback.
- Obtain explicit approval before performing the deletion.

### Final Rule

**UPDATE > REPLACE ONLY WITH APPROVAL > NEVER DELETE BY DEFAULT**

The AI must always prefer preserving project history and existing work.

## 35.18 PER-FILE DOCUMENTATION GATE — MANDATORY

Every individual file created or modified during an approved task must be documented.

This rule applies to:

- Python files
- TypeScript/JavaScript files
- React components
- SQL/migrations
- Configuration files
- Docker/infrastructure files
- Scripts
- Tests
- Markdown/documentation files
- Any other project file

### After Creating or Updating Each File

The AI must follow this sequence:

`CREATE/UPDATE FILE → VALIDATE FILE → DOCUMENT FILE CHANGE → CONTINUE`

For every changed file, record:

1. Exact file path.
2. Whether it was `CREATED` or `UPDATED`.
3. Purpose of the change.
4. What was added/changed.
5. Why the change was required.
6. Relevant dependencies or affected modules.
7. Database/API/pipeline/security impact, if applicable.
8. Validation performed.
9. Validation result.
10. Known issues or limitations.
11. Current status.

### File-Level Documentation Location

The file-level record must be placed in the appropriate project documentation.

At minimum:

- `CHANGELOG.md` must contain the file-level change record for every approved task.
- `PROJECT_PLAN.md` must reflect file changes that affect an approved phase.
- `ARCHITECTURE.md`, `DATABASE.md`, `API.md`, `SECURITY.md`, or relevant technical documentation must be updated when the file change affects those areas.

Do not create a separate documentation file for every source file unless explicitly approved. Use the existing documentation structure efficiently.

### File Header + Documentation Are Different

A file header explains the file itself.

Project documentation records the change made to that file.

Both requirements apply.

Example:

```text
File:
backend/app/services/lead_service.py

Status:
UPDATED

Purpose:
Coordinates lead business logic.

Change:
Added tenant-aware lead retrieval.

Reason:
Prevent cross-organization access.

Impact:
Backend authorization / multi-tenancy.

Validation:
Pytest: PASS
Type Check: PASS
Lint: PASS
```

### No Undocumented File Changes

A task must NOT be considered complete if:

- A file was changed but not recorded.
- A new file was created but not recorded.
- A migration was created but not documented.
- A test file was added but not recorded.
- A configuration file was changed but not recorded.

### File-Level Accuracy

Never claim a file was modified if it was not.

Never claim a file was validated if it was not.

Never claim tests passed if they did not run or failed.

If validation could not run because tooling is unavailable, record:

`NOT RUN — <exact reason>`

### Final File Audit

Before reporting an approved task as complete:

1. Compare the approved file-change plan against actual file changes.
2. List every created file.
3. List every modified file.
4. Verify every file appears in the documentation.
5. Verify validation status for each applicable file.
6. Update `CHANGELOG.md`.
7. Update affected technical documentation.
8. Only then report completion.

### Mandatory Completion Rule

**EVERY FILE → DOCUMENT → VALIDATE → RECORD**

No exceptions for "small" changes.


# 36. UI-FIRST PRODUCT PLANNING & REQUIRED SOURCE SET

## 36.1 UI Planning Before Implementation

Before the first vertical slice is implemented, the AI must first plan the complete user-facing workflow.

The plan must explicitly define:

- What the user searches for.
- Which search fields are required.
- Which sources are searched.
- How source selection works.
- How search results are displayed.
- Where results are displayed.
- What fields appear in result rows.
- What happens when a result is selected.
- What appears on company details.
- What appears on contact details.
- How validation/enrichment/scoring states are displayed.
- How exports are initiated and reported.
- Loading, empty, error, and unauthorized states.

No application UI implementation should begin until this UI/product plan is approved.

## 36.2 Required Source Set

The product plan must retain the following target discovery sources:

- Google Maps / Google Places
- Yellow Pages
- Public LinkedIn information
- Company websites
- Open business directories

These are required product-source targets, but each source must pass the existing legal/technical source-access rules before implementation.

The AI must not silently remove a required source from the product plan.

If a source cannot legally or technically be accessed as intended, the AI must:

1. Report the limitation.
2. Identify the permitted access method if known.
3. Propose an approved alternative/provider where necessary.
4. Wait for approval before changing the source strategy.

## 36.3 Source Adapter Architecture

Required sources must be isolated behind provider/source adapters.

Conceptually:

Source Adapter
→ Fetch
→ Source Record
→ Normalize/Map
→ Pipeline

The core application must not become dependent on a single provider.

## 36.4 Vertical Slice Implementation

The complete product/UI plan must be established first.

Implementation then proceeds one approved slice at a time:

PLAN → APPROVE → IMPLEMENT → TEST → REPORT → REVIEW → APPROVE → NEXT

A slice must not silently implement later slices.

The AI must stop after the approved slice and wait for review.

## 36.5 Source and UI Truthfulness

The UI must never imply that a source returned data it did not return.

The UI must never display fabricated company, contact, geography, industry, validation, enrichment, score, or export results.

If a source does not support a requested search or field, show an honest unavailable/unsupported/unknown state.
