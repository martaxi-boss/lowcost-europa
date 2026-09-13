# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **GATE 6 CLOSED — LE-007 AUTHORIZED**.

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
- LE-006 controlled search precision and delivery filtering was approved at Gate 6 and merged into `main` through PR #20.
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 remain the approved foundation.
- AliExpress integration, catalog persistence and bounded discovery are implemented with automated tests and GitHub Actions CI.
- LE-006 final suite passed 76 tests with no migration drift and no new infrastructure cost.
- Plain `HIFU` search previously showed strong Hanfu/cosplay semantic noise; specific queries such as `HIFU machine`, `7D HIFU machine` and `professional HIFU machine` produced relevant professional HIFU products in the observed studies.
- LE-006 added optional `target_language` and documented `delivery_days` search controls while preserving backward compatibility.
- Across three LE-006 PT/EUR/EN dry-run studies with `delivery_days=5`, search returned normalized 5-day logistics for all 25 observed candidates.
- 24 detail operations succeeded, and none of those 24 reproduced `delivery_days`; 24 search/detail logistics mismatches were therefore observed.
- Search and detail logistics remain separate. No data fusion, scoring, ranking, winner selection or customer-facing delivery claim has been authorized.
- No frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-007 — Provenance-aware logistics persistence` is authorized as GitHub Issue #21.

LE-007 must persist logistics evidence with explicit provenance before any scoring or customer-facing use. The current `OfferObservation.ship_to_days_raw` and `OfferObservation.delivery_days` remain detail-level evidence. The phase may add separate nullable search-level logistics fields and pass search evidence from controlled discovery into persistence only for the same product ID.

LE-007 must use a normal new migration; the already-merged catalog initial migration must not be rewritten. Manual product imports without search context must leave search-level logistics fields NULL. Search values must never be silently copied into detail fields, and detail values must never be silently copied into search fields.

No `effective_delivery_days`, ProductFamily auto-assignment, scoring, ranking, winner selection, scheduler, cron, mass import, publication or customer-facing delivery promise is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 6 is closed. LE-007 is authorized on a dedicated Builder branch. The Builder must open a Pull Request and stop at Gate 7 before merge. No LE-008, scoring, LE-UX-001, frontend or public deployment is authorized.
