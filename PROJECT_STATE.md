# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-003 IMPLEMENTED — AWAITING SUPERVISOR REVIEW**.

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
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 are the approved foundation.
- Environment-specific settings, PostgreSQL configuration, health checks, automated tests, Ruff and GitHub Actions CI are in place.
- AliExpress integration layer is implemented on `builder/le-002-aliexpress-integration` with environment-based configuration, HMAC-SHA256 signing, categories, product search, product detail, affiliate-link generation, semantic normalization, bounded retries/timeouts, structured errors, tests and documentation. `evaluate_rate` is treated as a percentage, logistics raw text is preserved with conservative `delivery_days` parsing, and entities without required IDs are rejected.
- Live AliExpress smoke test: **PASS** for categories, HIFU search using PT/EUR, product detail and affiliate-link generation.
- LE-003 minimal catalog data model is implemented with ProductFamily, Offer and OfferObservation, PostgreSQL constraints, protected history, Django Admin, tests and documentation.
- No discovery, automatic AliExpress-to-database import, scoring, frontend or public deployment has been started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) is the initial system target for a future validated deployment. The system must remain lightweight enough to begin on this server. Scaling requires measured need and Supervisor approval.

## Current task

`LE-003 — Minimal catalog data model` is implemented on `builder/le-003-catalog-model` and awaits Supervisor review. It contains only the minimum relational model for permanent Product Families, replaceable Offers and factual Offer Observations.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` is recorded as GitHub Issue #2. It must not start yet. It belongs before the full public frontend, after the motor/data needed for truthful presentation are sufficiently defined.

## Gate

Gate 3 is active. LE-003 awaits Supervisor review. No merge, discovery, automatic AliExpress-to-database import, scoring, LE-UX-001, frontend or public deployment is authorized.
