# Lowcost Europa — Project State

Updated: 2026-09-13.

Current state: **LE-008 IMPLEMENTED — AWAITING SUPERVISOR REVIEW**.

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
- Python 3.12, Django 5.2 LTS and PostgreSQL 16 remain the approved foundation.
- AliExpress integration, catalog persistence and bounded discovery are implemented with automated tests and GitHub Actions CI.
- Plain `HIFU` search previously showed strong Hanfu/cosplay semantic noise; specific queries such as `HIFU machine`, `7D HIFU machine` and `professional HIFU machine` produced relevant professional HIFU products in the observed studies.
- LE-006 added optional `target_language` and documented `delivery_days` search controls while preserving backward compatibility.
- Across three LE-006 PT/EUR/EN dry-run studies with `delivery_days=5`, search returned normalized 5-day logistics for all 25 observed candidates.
- 24 detail operations succeeded, and none of those 24 reproduced `delivery_days`; 24 search/detail logistics mismatches were therefore observed.
- LE-007 added normal catalog migration `0002` with nullable `OfferObservation.search_ship_to_days_raw` and `OfferObservation.search_delivery_days`; the original `0001_initial.py` remains unchanged.
- Search logistics and detail logistics are now persisted with explicit provenance and without fallback or precedence. Manual product import leaves search logistics NULL; discovery may pass normalized search evidence only for the same product ID.
- LE-007 final validation passed 86 tests with PostgreSQL 16, migration drift check and CI green. No new infrastructure cost was introduced.
- No scoring, ranking, winner selection, frontend, public deployment or autonomous scheduling has started.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

`LE-008 — Conservative logistics evidence assessment` is implemented on its Builder branch and awaits Supervisor review as GitHub Issue #24.

LE-008 must create a small, derived, non-persisted assessment of logistics evidence for a single `OfferObservation`. It must classify observations as `UNKNOWN`, `SEARCH_ONLY`, `DETAIL_ONLY`, `CONSISTENT` or `CONFLICT` according to the separately persisted search/detail delivery values.

At observation level only, the assessment may report whether the available non-conflicting source evidence supports the strategic <=5-day candidate criterion. Search-only evidence remains an estimate reported by the source, not an independent verification or customer guarantee. `CONSISTENT` means the search and detail endpoints agree; it does not mean guaranteed delivery.

LE-008 must not create `effective_delivery_days`, database fields, migrations, precedence between search/detail, numeric confidence/scoring, automatic filtering of persistence, ranking, winners or customer-facing delivery claims. The assessment may appear in diagnostic discovery output for human review only.

The implemented derived service classifies exactly five states (`UNKNOWN`, `SEARCH_ONLY`, `DETAIL_ONLY`, `CONSISTENT`, `CONFLICT`). Non-conflicting source evidence supports the <=5-day candidate criterion only when its interpreted day value is <=5; every conflict returns false, including conflicts where both values are <=5. No schema change or scoring was introduced.

The LE-008 live dry-run (`HIFU machine`, PT/EUR, EN, delivery filter 5, limit 3) returned two search candidates with 5-day search evidence, but both detail operations returned sanitized `AliExpressAPIError`; therefore no integrated evidence state was asserted from that live batch. Database counts remained zero before and after.

## Planned later task

`LE-UX-001 — UX/UI e Design System inicial` remains recorded as GitHub Issue #2. It must not start until a later explicit Supervisor decision after the data motor is sufficiently understood for truthful presentation.

## Gate

Gate 8 is active. LE-008 is implemented on its dedicated Builder branch and awaits Supervisor review. The Builder must stop before merge. No LE-009, scoring, LE-UX-001, frontend or public deployment is authorized.
