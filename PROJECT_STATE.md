# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **GATE 10 CLOSED — LE-011 AUTHORIZED**.

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
- LE-009 temporal validity of logistics evidence was approved at Gate 9 and merged into `main` through PR #29.
- LE-010 longitudinal logistics history diagnostics was approved at Gate 10 and merged into `main` through PR #32.
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
- LE-009 added a pure, derived, timezone-aware freshness assessment with `FRESH`, `STALE` and `FUTURE`; its 24-hour window remains provisional diagnostic configuration, not commercial policy.
- LE-009 composes freshness with LE-008 only for internal `supports_current_5d_candidate`; one shared `as_of` is used per discovery batch, with no automatic filtering, ranking or persistence changes.
- A single fresh positive observation is not sufficient, by itself, to authorize a public delivery promise. No final minimum-history threshold has been defined.
- LE-010 added a read-only longitudinal logistics history diagnostic for one Offer, using one ordered query plus O(n) in-memory evaluation. It reports chronological counts, span, latest diagnostics, conflict/future flags and current-support counts without score, percentage or stability decision.
- LE-010 final validation passed 120 tests with PostgreSQL 16 and exact-head CI green. The live study DB remained empty and the read-only `Offer not found` path was validated honestly.
- The live catalog study database still has no real longitudinal cohort; therefore no commercial stability threshold is authorized.
- No frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-011 — Controlled real logistics observation cohort` is authorized as GitHub Issue #33.

LE-011 must create a tiny, explicit, non-commercial live cohort for future longitudinal study: PT/EUR, professional HIFU, at most 3 Offers, manually identified and documented, with one real baseline `OfferObservation` per Offer.

Before any live write, the exact selection must be exercised in dry-run. Commit mode must require explicit intent and must reject a cohort larger than 3 products. The implementation must reuse existing LE-007 persistence/provenance and must not create a Cohort model, migration, score, ranking or automatic selection.

The baseline study must be archived at `docs/studies/LE-011-INITIAL-LOGISTICS-COHORT.md`. After the baseline, `aliexpress_logistics_history` must confirm exactly one Observation per cohort Offer. The Builder must not immediately repeat observations merely to fabricate history.

No commercial stability threshold, customer-facing delivery claim, automatic filtering, scheduler, cron, ProductFamily automation, frontend, deployment or infrastructure increase is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 10 is closed. LE-011 is authorized on a dedicated Builder branch. The Builder must stop at Gate 11 before merge. No LE-012, commercial stability threshold, scoring, LE-UX-001, frontend or public deployment is authorized.
