# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-001 ACCEPTED AND MERGED — LE-002 AUTHORIZED**.

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
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 are the approved foundation.
- Environment-specific settings, PostgreSQL configuration, health checks, automated tests, Ruff and GitHub Actions CI are in place.
- No public production deployment has been performed.
- AliExpress API capability was validated technically before this codebase, but the Django integration layer is not implemented yet.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) is the initial system target for a future validated deployment. The system must remain lightweight enough to begin on this server. Scaling requires measured need and Supervisor approval.

## Authorized next task

`LE-002 — AliExpress integration layer` is authorized. It must be developed on its own branch, tested, submitted by Pull Request and stopped at the next Supervisor gate before merge.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` is recorded as GitHub Issue #2. It must not start yet. It belongs before the full public frontend, after the motor/data needed for truthful presentation are sufficiently defined.

## Gate

Gate 1 is closed. LE-001 is officially accepted. LE-002 may start. No deployment to public production is authorized.
