# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-004 ACCEPTED — DEVELOPMENT PAUSED FOR DEEP AUDIT**.

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
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 are the approved foundation.
- Environment-specific settings, PostgreSQL configuration, health checks, automated tests, Ruff and GitHub Actions CI are in place.
- AliExpress integration provides environment-based configuration, HMAC-SHA256 signing, categories, product search, product detail, affiliate-link generation, semantic normalization, bounded retries/timeouts, structured errors, tests and documentation.
- Live AliExpress smoke tests passed for categories, HIFU search using PT/EUR, product detail and affiliate-link generation.
- The catalog contains ProductFamily, Offer and OfferObservation with PostgreSQL constraints, protected history, Django Admin, tests and documentation.
- Structural catalog invariants are enforced at PostgreSQL level for lifecycle/source/availability, timeline and numeric ranges.
- Controlled persistence now proves `AliExpressClient -> AliExpressProduct -> Offer / OfferObservation` for one explicitly supplied product ID.
- Reimports reuse the same Offer, append factual OfferObservation history, preserve ProductFamily and do not invent missing source facts.
- Live LE-004 dry-run passed on the Droplet with full transaction rollback and no persistent test data.
- No discovery, scoring, frontend or public deployment has been started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) is the initial system target for a future validated deployment. The system must remain lightweight enough to begin on this server. Scaling requires measured need and Supervisor approval.

## Current checkpoint

Development is intentionally paused after Gate 4 for the independent deep audit recorded as GitHub Issue #12.

The audit must review governance, architecture, security, CI/tests, migrations, AliExpress integration, data model, controlled persistence, Git/documentation and real Droplet state before any next construction phase is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision.

## Gate

Gate 4 is closed. **No LE-005 is authorized.** No automatic discovery, mass import, scoring, LE-UX-001, frontend or public deployment may begin until the deep-audit checkpoint has been reviewed by the owner, partner and consultant and the Supervisor issues a new decision.
