# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-011 IMPLEMENTED — AWAITING SUPERVISOR REVIEW**.

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
- LE-011 created the first controlled live longitudinal baseline: 3 professional-HIFU AliExpress Offers and 3 OfferObservations for PT/EUR, one baseline Observation per Offer.
- All three baseline Observations preserve search delivery=5 and detail delivery=NULL as separate provenance; each currently diagnoses as SEARCH_ONLY and FRESH.
- LE-011 used one explicit live commit after exact-cohort dry-run, kept ProductFamily unassigned, and did not run a second observation. No commercial stability threshold is authorized.
- No frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-011 — Controlled real logistics observation cohort` is implemented on its dedicated Builder branch and awaits Supervisor review under GitHub Issue #33.

The controlled baseline contains exactly 3 AliExpress Offers and 3 OfferObservations for PT/EUR professional HIFU. The documented IDs are `1005012522304882`, `1005013116584854` and `1005013002556821`; each has exactly one baseline Observation and no ProductFamily assignment.

The exact cohort passed dry-run before the single live commit. PostgreSQL migrations `0001` and `0002` are applied with zero migration drift; the prior OperationalError was an execution-context configuration issue and did not require schema changes. The persistence layer now also rejects mismatched detail product IDs before affiliate generation or database writes.

The baseline study is archived at `docs/studies/LE-011-INITIAL-LOGISTICS-COHORT.md`, and `aliexpress_logistics_history` confirmed `Observations: 1` and zero span for every cohort Offer. No second observation has been run.

No commercial stability threshold, customer-facing delivery claim, automatic filtering, scheduler, cron, ProductFamily automation, frontend, deployment or infrastructure increase is authorized.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 11 is active. LE-011 is implemented on its dedicated Builder branch and awaits Supervisor review. The Builder must stop before merge. No LE-012, second longitudinal observation, commercial stability threshold, scoring, LE-UX-001, frontend or public deployment is authorized.
