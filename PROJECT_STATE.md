# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-005 IMPLEMENTED — AWAITING SUPERVISOR REVIEW**.

## Strategic state

### Initial market
Portugal.

### Main logistics criterion
Prioritize products with estimated/verifiable delivery in up to **5 days**. Never promise logistics information that cannot be supported.

### Product model
`Product Family` is permanent in Lowcost Europa. `Offer` is replaceable. A permanent page must not disappear only because an AliExpress offer disappears.

### First strategic niche
Professional aesthetics. This does not limit the project to this niche.

### Automation
Measure and understand before automating critical decisions.

## Technical state

- Phase 0 reconnaissance completed and approved.
- ADR-001 initial architecture is Accepted.
- ADR-002 initial infrastructure and scaling is Accepted.
- LE-001 Foundation was approved at Gate 1 and merged into `main` through PR #1.
- LE-002 AliExpress integration layer was approved at Gate 2 and merged into `main` through PR #5.
- LE-003 minimal catalog data model was approved at Gate 3 and merged into `main` through PR #8.
- LE-004 controlled AliExpress persistence was approved at Gate 4 and merged into `main` through PR #11.
- The deep audit through Gate 4 is archived at `docs/audits/AUDIT_GATE_4.md`.
- The post-Gate-4 checkpoint was reviewed by the owner, partner and consultant and approved externally.
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 remain the approved foundation.
- Environment-specific settings, PostgreSQL configuration, health checks, automated tests, Ruff and GitHub Actions CI are in place.
- AliExpress integration provides environment-based configuration, HMAC-SHA256 signing, categories, product search, product detail, affiliate-link generation, semantic normalization, bounded retries/timeouts, structured errors, tests and documentation.
- Live AliExpress smoke tests passed for categories, HIFU search using PT/EUR, product detail and affiliate-link generation.
- The catalog contains ProductFamily, Offer and OfferObservation with PostgreSQL constraints, protected history, Django Admin, tests and documentation.
- Controlled persistence proves `AliExpressClient -> AliExpressProduct -> Offer / OfferObservation` for one explicitly supplied product ID.
- No scoring, ranking, frontend, public deployment or autonomous scheduling has been started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-005 — Controlled Discovery Portugal` is implemented on its builder branch and awaits Supervisor review.

LE-005 must study small, bounded batches of real AliExpress candidates for Portugal before any automatic scoring or publication. Each execution uses one explicit keyword, PT/EUR, default 10 results and a hard cap of 25 results. It must reuse the existing AliExpress integration and controlled persistence pipeline rather than creating a parallel importer.

The phase must measure data quality and coverage, including price, currency, evaluation rate, sales count, commission and logistics. `delivery_days <= 5` may be reported as an observational metric when data exists, but must not yet become an automatic commercial filter or selection decision.

No ProductFamily auto-assignment, scoring, ranking, winner selection, scheduler, cron, mass import or publication is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 4 and the post-Gate-4 audit checkpoint are closed. LE-005 is authorized on a dedicated Builder branch. The Builder must open a Pull Request and stop at Gate 5 before merge. No LE-006, scoring, LE-UX-001, frontend or public deployment is authorized.