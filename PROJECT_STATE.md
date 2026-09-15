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
- A technical HTTPS staging deployment now exists on the current Droplet; it is explicitly noindex and is not a public MVP launch or production release.
- The approved Admin, storefront shell and production-settings hardening integrations are now merged into `main`.
- MVP LIVE CATALOG 001 created the first real ProductFamily: `Máquinas HIFU 7D` (`maquinas-hifu-7d`), status `NEW`.
- Offers `1005012522304882` and `1005013116584854` remain manually associated with the 7D family.
- MVP LIVE CATALOG 002 created the second real ProductFamily: `Máquinas HIFU 22D MAX` (`maquinas-hifu-22d-max`), status `NEW`; existing Offer `1005013002556821` is its sole active Offer and explicit editorial primary.
- Current live catalog state is 5 ProductFamilies / 6 Offers / 15 OfferObservations / 35 raw staging OfferClick records. Eighteen were added by an audited automated external batch, followed by eleven audited external mobile-browser requests after temporary DuckDNS staging exposure; they are not unique users or conversions. The minimum five-family MVP catalog target is reached; additional discovery is paused for pre-launch work.
- MVP DISCOVERY 001 and subsequent live revalidation established the fresh-candidate workflow. MVP LIVE CATALOG 004 selected current API candidates rather than automatically reusing previously absent IDs; RF Microneedling remains on hold after its earlier detail-normalization failure.
- `catalog.0003_offer_is_primary_and_more` is applied live and explicit editorial primary selection is operational.
- Initial editorial primary for `Máquinas HIFU 7D` is `1005012522304882`; the choice is manual and reversible, not scoring, ranking, winner, proven, or verified status.
- `/go/<offer_id>/` and privacy-minimal raw outbound click tracking are implemented in code with no user identification, impressions, conversion or revenue tracking.
- `catalog.0004_offerclick` is applied live. LAUNCH READINESS 001 began from 5 raw staging OfferClick records; after the temporary DuckDNS hostname became reachable, 18 additional automated-looking external `/go/` requests were audited across three remote sources, followed by eleven external mobile-browser requests, producing an audited launch-readiness snapshot total of 34; one later external `/go/54/` request brought the current raw snapshot to 35. These raw records are not unique users, customers, purchases, conversions or commissions.
- Real Django staging is established through Nginx -> Gunicorn -> Django production settings -> PostgreSQL; systemd and HTTPS are active, while public MVP launch remains unauthorized.
- Conversion, revenue and external analytics tracking remain unimplemented.
- MVP OPERATIONAL CLOSEOUT 001 final-completion pass reconciled staging to current merged main `1b5e9f30d2606bf030463a4f5a571e7b4fcb4bb6`; health, homepage, Contacto, robots and AliExpress callback returned HTTP 200 with noindex preserved. The commercial validation report is therefore present on staging as a repository document, with no runtime restart required.
- PostgreSQL restore drill passed: the pre-0004 backup restored into an isolated temporary DB, retained 1/3/6 and the editorial primary, migrated forward through catalog.0004, then the temporary DB was dropped.
- A local daily PostgreSQL backup timer is operational with 7-day retention; MVP OPERATIONAL CLOSEOUT 001 validated the latest daily dump/checksum and a tested root-only local AliExpress secret restore link. Off-server backup remains OWNER BLOCKED pending explicit authorization for private Cloudflare R2 + restic activation; an off-Droplet recovery key is required.
- Product imagery is deployed to the noindex staging environment. Real Chromium visual QA at desktop 1440x900 and mobile 390x844 passed with no overflow or broken images. The second 7D Offer image is factual but only 123x123 and visibly pixelated at card size; MVP PRELAUNCH 003 performed one fresh detail lookup for the same product ID and AliExpress returned the same image URL, so this finding remains OPEN.
- VISUAL + COMMERCIAL READINESS 001 is approved, merged and deployed in official main `ea390319bcf9d4b8023a24140828f049a7fba10a`. Its final Chromium QA passed at 390x844 and 1440x900 with zero horizontal overflow/JS errors, visible desktop navigation, 48 px mobile menu/CTA targets and no raw AliExpress affiliate href exposure. The HIFU 123x123 source-image finding remains OPEN / NON-BLOCKING.
- LAUNCH READINESS 001 configured temporary staging hostname `lowcost-europa.duckdns.org` -> `165.22.114.67` with a dedicated valid Let's Encrypt certificate, preserved sslip compatibility, HTTP->HTTPS, noindex, callback reachability and real mobile/desktop QA. Public launch remains unauthorized. The external OfferClick audit during DuckDNS exposure is documented in `docs/launch/LAUNCH-READINESS-001.md`.
- CATALOG + COMMERCIAL READINESS 001 audited exactly the 6 existing Offers: 4 exact-ID detail refreshes succeeded and received one new factual OfferObservation each; Diode and Hydro detail refreshes failed once with AliExpressAPIError and remain REVIEW REQUIRED without persistence. Decisions are 3 KEEP, 1 KEEP WITH FINDING (the known 123x123 HIFU image), and 2 REVIEW REQUIRED. No new Offer or ProductFamily was created.
- ALIEXPRESS API SAFETY 001 centralizes serial external calls, secure local flock/cadence state, 1.0s minimum cadence, bounded Retry-After/backoff/jitter retries and batch-wide rate-limit abort. After a 224/224 full test gate, the authorized detail-only refreshes for existing Offers 55 and 56 both returned exact IDs with 2 logical operations / 2 HTTP attempts / zero retries and created one factual OfferObservation each; no Offer fields or affiliate URLs changed.
- AUDIT + OPERATIONAL HYGIENE CLOSEOUT 001 is merged into official main `3a4869f6bdbf75a56e370a653d13e713cfc59900`; its operational cleanup/recovery evidence remains documented, and public launch remains unauthorized.
- CATALOG STRUCTURE 001, EIGHT-FAMILY TAXONOMY 001, STOREFRONT PLACEMENT MIGRATION 001 and STOREFRONT VISUAL & COMMERCIAL ENHANCEMENT 001 are APPROVED / MERGED / DEPLOYED / CLOSED. The Phase 4 application merge commit is `da5b6641597c77962e0ead169a492842796add76`, and staging is deployed at that same application commit. Subsequent documentation-only commits may advance repository `main` without requiring an application deployment. The public catalog uses `OfferFamilyPlacement` as source of truth. Phase 4 was presentation-only: no migrations or catalog mutations; authorized QA produced no OfferClick increase and no live AliExpress calls; no raw affiliate URLs or unproven Europe claims were exposed; noindex was preserved; graphical screenshot QA was not performed during the Phase 4 operation. Public launch remains unauthorized.
- MVP PRELAUNCH 001 is merged and its transparency/privacy/affiliate/terms pages plus conservative technical SEO baseline are deployed to noindex staging through MVP PRELAUNCH 002. Fail-closed indexing was validated with PUBLIC_INDEXING_ENABLED=false and PUBLIC_SITE_URL empty. Authorized public contact channels are now defined in PRELAUNCH 004; operator legal identity remains PENDING OWNER INPUT, off-server backup remains pending, final public domain remains pending, and public launch is not authorized.

## Infrastructure classification

The existing DigitalOcean Droplet (1 vCPU / 1 GB RAM / 25 GB) remains the initial system target. No infrastructure increase is authorized. Scaling continues to require measured need and Supervisor approval.

## Current task

Phase 4 application/staging baseline is `da5b6641597c77962e0ead169a492842796add76`. STOREFRONT VISUAL & COMMERCIAL ENHANCEMENT 001 is APPROVED / MERGED / DEPLOYED / CLOSED through PR #69. PR #70 records the documentation-only Phase 4 closeout. No application deployment is required for this documentation closeout; repository `main` may therefore be ahead of the deployed application solely by documentation commits. The Phase 4 result is presentation-only with zero migrations, zero catalog mutation, zero OfferClick increase during authorized QA, zero live AliExpress calls, zero raw affiliate URL exposure and zero unproven Europe claims; noindex remains enabled. Graphical screenshot QA was not performed in this Phase 4 operation. PUBLIC LAUNCH NOT AUTHORIZED. NEXT PHASE AWAITS SUPERVISOR ORDER.

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
7. Implement `/go/<offer>/` — operational in technical staging after live `catalog.0004`; current audited snapshot total is 35 raw staging OfferClick records after the previously documented automated/external traffic plus one later external `/go/54/` request on DuckDNS staging. These are not unique users or conversions.
8. Add minimal, privacy-respecting click tracking — operational as raw outbound `OfferClick` events only, with no user identification; no real-user click claim yet.
9. Establish real staging — completed on the current Droplet with HTTPS Nginx, local Gunicorn, systemd, production settings and noindex.
10. Add operational hardening and backup — local daily backup + restore drill completed; local AliExpress secret recovery is tested; legacy firewall ports were removed and the inactive legacy AliExpress panel was quarantined root-only with checksum verification. Off-server R2/restic recovery remains OWNER BLOCKED pending explicit authorization, and GitHub main protection remains BLOCKED pending account/admin capability.
11. Expand to 5–10 ProductFamilies — in progress conservatively; 5 real ProductFamilies / 6 Offers are now live. Further imports still require fresh validation and Supervisor approval.
12. Complete mobile/desktop QA — real Chromium desktop/mobile visual QA completed on staging with PASS; second Offer image quality (123x123 source) remains an OPEN non-blocking pre-launch data-quality finding after PRELAUNCH 003 returned the same factual image URL.
13. Add basic technical SEO and legal/affiliate transparency — implemented, merged and deployed to noindex staging; authorized public contact channels are implemented in PRELAUNCH 004, while operator legal identity still requires owner input before public launch.
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
