# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-004 IMPLEMENTED — AWAITING SUPERVISOR REVIEW**.

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
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 are the approved foundation.
- Environment-specific settings, PostgreSQL configuration, health checks, automated tests, Ruff and GitHub Actions CI are in place.
- AliExpress integration layer provides environment-based configuration, HMAC-SHA256 signing, categories, product search, product detail, affiliate-link generation, semantic normalization, bounded retries/timeouts, structured errors, tests and documentation. `evaluate_rate` is treated as a percentage, logistics raw text is preserved with conservative `delivery_days` parsing, and entities without required IDs are rejected.
- Live AliExpress smoke test previously passed for categories, HIFU search using PT/EUR, product detail and affiliate-link generation.
- The catalog contains ProductFamily, Offer and OfferObservation with PostgreSQL constraints, protected history, Django Admin, tests and documentation.
- Structural catalog invariants are enforced at PostgreSQL level for lifecycle/source/availability, timeline and numeric ranges.
- No discovery, scoring, frontend or public deployment has been started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) is the initial system target for a future validated deployment. The system must remain lightweight enough to begin on this server. Scaling requires measured need and Supervisor approval.

## Current task

`LE-004 — Controlled AliExpress persistence` is implemented on the Builder branch and awaits Supervisor review.

The controlled path `AliExpressClient -> AliExpressProduct -> Offer / OfferObservation` is implemented for explicit import of one known product with transactional persistence and dry-run rollback. Automatic discovery, mass import, scoring, background scheduling and frontend remain outside scope.

Important semantics for LE-004:

- repeated imports reuse the same Offer and append factual OfferObservation history;
- missing source data stays unknown and is never invented;
- availability remains UNKNOWN unless the normalized source explicitly supports another state;
- `Offer.is_active=True` means the external listing was successfully seen, not confirmed stock availability;
- ProductFamily assignment remains manual/outside LE-004.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` is recorded as GitHub Issue #2. It must not start yet. It belongs before the full public frontend, after the motor/data needed for truthful presentation are sufficiently defined.

## Gate

Gate 4 is active. LE-004 awaits Supervisor review. The Builder must stop before merge. No LE-005, automatic discovery, mass import, scoring, LE-UX-001, frontend or public deployment is authorized.
