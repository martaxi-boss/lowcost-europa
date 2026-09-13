# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **GATE 8 CLOSED — LE-009 AUTHORIZED**.

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
- LE-007 provenance-aware logistics persistence was approved at Gate 7 and merged into `main` through PR #23.
- LE-008 conservative logistics evidence assessment was approved at Gate 8 and merged into `main` through PR #26.
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 remain the approved foundation.
- AliExpress integration, catalog persistence and bounded discovery are implemented with automated tests and GitHub Actions CI.
- Plain `HIFU` search previously showed strong Hanfu/cosplay semantic noise; specific queries such as `HIFU machine`, `7D HIFU machine` and `professional HIFU machine` produced relevant professional HIFU products in the observed studies.
- LE-006 added optional `target_language` and documented `delivery_days` search controls while preserving backward compatibility.
- Across three LE-006 PT/EUR/EN dry-run studies with `delivery_days=5`, search returned normalized 5-day logistics for all 25 observed candidates.
- 24 detail operations succeeded, and none of those 24 reproduced `delivery_days`; 24 search/detail logistics mismatches were therefore observed.
- LE-007 added normal catalog migration `0002` with nullable `OfferObservation.search_ship_to_days_raw` and `OfferObservation.search_delivery_days`; the original `0001_initial.py` remains unchanged.
- Search logistics and detail logistics are persisted with explicit provenance and without fallback or precedence. Manual product import leaves search logistics NULL; discovery may pass normalized search evidence only for the same product ID.
- LE-008 added a pure, derived logistics-evidence assessment with states `UNKNOWN`, `SEARCH_ONLY`, `DETAIL_ONLY`, `CONSISTENT` and `CONFLICT`.
- LE-008 reports only whether one observation contains non-conflicting source evidence compatible with the <=5-day candidate criterion. `CONFLICT` never supports the criterion automatically, even when both values are <=5.
- LE-008 introduced no schema, migration, effective delivery value, score, ranking, winner selection or customer-facing claim. Final validation passed 97 tests and exact-head CI was green.
- No frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-009 — Temporal validity of logistics evidence` is authorized as GitHub Issue #27.

LE-009 must add a pure, derived, timezone-aware assessment of observation freshness. It must keep evidence quality (LE-008) separate from temporal validity and compose them only for internal diagnostics.

For this phase, an explicit **24-hour diagnostic window** is authorized for studies/output. This is a provisional internal engineering threshold, not a final commercial policy or customer promise. The freshness service must accept `max_age` as a parameter rather than hard-code an immutable production rule.

Minimum freshness states are `FRESH`, `STALE` and `FUTURE`. `FRESH` means `0 <= age <= max_age`; `STALE` means `age > max_age`; `FUTURE` means the observation timestamp is later than the evaluation time and must not be silently corrected. Naive datetimes and non-positive max-age values must be rejected clearly.

The internal diagnostic composition may report `supports_current_5d_candidate = evidence.supports_within_5_days AND freshness.is_fresh`. It must not filter persistence, create an effective delivery estimate, score, rank, select winners or authorize customer-facing logistics claims.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 8 is closed. LE-009 is authorized on a dedicated Builder branch. The Builder must open a Pull Request and stop at Gate 9 before merge. No LE-010, final commercial freshness policy, scoring, LE-UX-001, frontend or public deployment is authorized.
