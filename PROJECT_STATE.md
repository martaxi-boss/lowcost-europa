# Lowcost Europa — Project State

Updated: 2026-09-14.

Current state: **MVP MANUAL CURATION STARTED — FIRST LIVE PRODUCTFAMILY CREATED**.

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
Do not require automation before validating the business manually.

Não automatizar totalmente uma decisão que ainda não compreendemos.

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
- LE-011 controlled real logistics observation cohort was approved at Gate 11 and merged into `main` through PR #35 as `11bbc3fb48ea9fe3281096e63b067fa9ddf92481`.
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
- All three baseline Observations preserve search delivery=5 and detail delivery=NULL as separate provenance; each diagnosed as SEARCH_ONLY and FRESH at baseline time.
- LE-011 used one explicit live commit after exact-cohort dry-run, kept ProductFamily unassigned, did not run a second observation, passed 130 tests and exact-head CI, and was independently revalidated against the live DB by the Supervisor.
- LE-012 executed one controlled second live observation round after more than 24 real hours, using exactly the three fixed LE-011 product IDs after a zero-write dry-run.
- LE-012 completed 3/3 successfully: ProductFamily remains 0, Offers remain 3, OfferObservations are now 6, with exactly two Observations per Offer.
- All three second Observations preserve search delivery=5, detail delivery=NULL, SEARCH_ONLY evidence and UNKNOWN availability; latest freshness is FRESH and the older baseline is now diagnostically STALE.
- Prices changed in the second round; sales counts and 7% commission rates did not change. No external failure, conflict, future timestamp, third observation, score, ranking or automatic commercial decision occurred.
- LE-012 was approved at Gate 12 and merged to `main` through PR #38. Gate 12 is closed.
- The second round completed 3/3 with live DB state 0 ProductFamilies / 3 Offers / 6 Observations, exactly 2 Observations per fixed Offer.
- Both time points remained SEARCH_ONLY; two observations do not prove commercial logistics stability and no public 5-day delivery guarantee is authorized.
- LE-013 longitudinal work is not authorized. Any further longitudinal research requires a concrete blocker and explicit Supervisor approval.
- The default direction is now MVP transition, not an automatic third longitudinal research round.
- No commercial stability threshold has been authorized.
- No public deployment or autonomous scheduling has started; the server-rendered storefront shell is integrated but not publicly deployed.
- The approved Admin, storefront shell and production-settings hardening integrations are now merged into `main`.
- MVP LIVE CATALOG 001 created the first real ProductFamily: `Máquinas HIFU 7D` (`maquinas-hifu-7d`), status `NEW`.
- Offers `1005012522304882` and `1005013116584854` are manually associated with that family; `1005013002556821` remains unassigned because it is explicitly a distinct 22D MAX model.
- Current live catalog state is 1 ProductFamily / 3 Offers / 6 OfferObservations. No new Offer or Observation was created during curation.
- `catalog.0003_offer_is_primary_and_more` is applied live and explicit editorial primary selection is operational.
- Initial editorial primary for `Máquinas HIFU 7D` is `1005012522304882`; the choice is manual and reversible, not scoring, ranking, winner, proven, or verified status.
- `/go/` and click tracking are not implemented, and no public deployment has occurred.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

MVP construction is active. The approved preparatory components are integrated, and manual live catalog curation has started with one real ProductFamily while preserving conservative logistics language and zero public deployment.

### MVP integrations completed

- Manual catalog curation Admin was integrated through PR #40.
- Storefront shell was integrated through PR #41.
- Production settings security baseline was integrated through PR #42.
- Manual live catalog curation has now started with the first ProductFamily.

## Immediate MVP roadmap

1. Manual catalog curation tooling — completed.
2. Storefront shell integration — completed.
3. Production settings hardening integration — completed.
4. First real ProductFamily creation — completed.
5. Associate 1–3 real Offers — completed for the first family with 2 coherent 7D Offers.
6. Explicit editorial primary Offer selection — completed for the first family with `1005012522304882`; no scoring or winner inference.
7. Implement `/go/<offer>/`.
8. Add minimal, privacy-respecting click tracking.
9. Establish real staging.
10. Add operational hardening and backup.
11. Expand to 5–10 ProductFamilies.
12. Complete mobile/desktop QA.
13. Add basic technical SEO and legal/affiliate transparency.
14. Launch the Portugal MVP.
15. Measure business outcomes.
16. Only then decide whether scoring, scheduling or additional automation is justified.

## Infrastructure after Gate 12

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the approved initial target. No second server, managed database, Redis, Celery, Elasticsearch, Kubernetes or additional paid infrastructure is authorized. Upgrade only on measured need and Supervisor approval.

## Security and honesty invariants

- Never promise guaranteed delivery without supporting proof; SEARCH_ONLY requires conservative language.
- ProductFamily remains permanent; Offer remains replaceable.
- Observation history remains factual and append-only.
- Affiliate nature must be disclosed.
- No fake reviews, cloaking or invasive fingerprinting.

## Gate

**GATE 12 CLOSED — MVP TRANSITION AUTHORIZED.**

LE-012 is approved and merged. LE-013 is not authorized. Further longitudinal work requires a concrete blocker plus explicit Supervisor approval. The next phase is controlled MVP construction and integration, not additional research by default.
