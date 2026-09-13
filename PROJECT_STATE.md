# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-005 ACCEPTED AND MERGED — LE-006 AUTHORIZED**.

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
- The deep audit through Gate 4 is archived at `docs/audits/AUDIT_GATE_4.md` and the post-Gate-4 checkpoint was approved externally.
- LE-005 controlled Portugal discovery was approved at Gate 5 and merged into `main` through PR #17.
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 remain the approved foundation.
- AliExpress integration, catalog persistence and bounded discovery are implemented with automated tests and GitHub Actions CI.
- LE-005 final suite passed 69 tests with no migration drift and no new infrastructure cost.
- The first HIFU/PT study showed two key findings: plain `HIFU` search produced strong Hanfu/cosplay semantic noise, and the initial batch exposed no normalized delivery data.
- Supervisor verification after Gate 5 confirmed that more specific keywords such as `HIFU machine`, `7D HIFU machine` and `professional HIFU machine` return relevant professional HIFU products.
- Supervisor verification also confirmed that the documented AliExpress `delivery_days=5` query filter returns HIFU candidates with normalized `Ship to PT in 5 days` / `delivery_days=5` in the observed live sample.
- No scoring, ranking, winner selection, frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-006 — Controlled search precision and delivery filtering` is authorized as GitHub Issue #18.

LE-006 must add only the minimal explicit search controls needed to study search precision and source-supported fast-delivery filtering for Portugal. It must remain bounded, manual and measurable, reuse the existing integration/discovery/persistence pipeline and introduce no scoring or automatic commercial decisions.

The phase may support the documented AliExpress search parameters `target_language` and `delivery_days` in a controlled way. Initial live studies use PT/EUR, `target_language=EN`, `delivery_days=5` and explicit professional HIFU keyword variants. `delivery_days=5` is a source query/filter, not by itself a customer promise; future presentation still requires per-product normalized evidence.

No ProductFamily auto-assignment, relevance scoring, ranking, winner selection, automated keyword expansion, scheduler, cron, mass import or publication is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 5 is closed. LE-006 is authorized on a dedicated Builder branch. The Builder must open a Pull Request and stop at Gate 6 before merge. No LE-007, scoring, LE-UX-001, frontend or public deployment is authorized.