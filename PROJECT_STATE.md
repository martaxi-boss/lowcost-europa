# Lowcost Europa — Project State

Historical reconciliation baseline: 2026-10-03. Most recent operational evidence: 2026-10-28.

## REA safe stock and backlog improvement — 2026-10-28 (latest verified)

- **Application revision installed on existing VPS:** `a21ca6d6a09f8d147bc072da7686075b0123d960` from prior `b19fe804c05cf81cf340cce4cc27d0816f3dfaa3`. [VPS Actions 40678609876](https://github.com/martaxi-boss/VPS/actions/runs/40678609876) **SUCCESS** at 11:16 UTC. Checks observed: pinned SSH host key, exact clean base/target, valid recent local/offsite backup, Django/check --deploy, no migrations, login throttle and affiliate-first-link guard, new STOCK_REVIEW_GUARD, 5 families, local readiness and external HTTPS/noindex. Temporary VPS workflow branch deleted.
- **Source code/CI:** [PR #173](https://github.com/martaxi-boss/lowcost-europa/pull/173) (merged application SHA above), [CI 40677845712](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40677845712) **SUCCESS** after import-order-only formatting corrections. Exact staging rollout authorized by [PR #174](https://github.com/martaxi-boss/lowcost-europa/pull/174), whose CI also passed. No migrations, config, dependency, DNS, SEO or external marketing edits.
- **Conservative listing evidence:** a product-detail title/URL does **not** prove stock. A valid detail with no explicitly affirmative availability now records `UNKNOWN` (with factual metadata) and does not deactivate; `AVAILABLE` requires recognized affirmative listing status; explicit `sold out`/`out of stock` or known dead item status deactivates. Seller SKU, selected origin/warehouse and real-time inventory are not certified by the current affiliate API.
- **Hourly maintenance fairness:** batch remains 10. With both lanes nonempty, oldest 6 eligible public listings and oldest 4 private active listings are checked each run. Spare quota is reassigned to available candidates; no duplicates or automated reactivation. Existing external API lock/cadence and fail-closed 429 behavior unchanged.
- **Human queue review support:** existing authenticated storefront `?gestao=rever` now explains paused weekly discovery for family queues at >=20, displays the minimum number of manual decisions to restart and offers oldest/recent sort. Default on a blocked queue is oldest. No candidate statuses, placements or approvals are mutated by this GET-only view.
- **Prior read-only queue baseline** [40673904816](https://github.com/martaxi-boss/VPS/actions/runs/40673904816) (before the change): cavitação 2, hidrodermoabrasão 40, pressoterapia 39, HIFU 4, diodo/laser 101 PENDING: 194 total, 3/5 family discoveries cap20 blocked. These are not a claim of new post-deploy counts. Owner must decide per listing to lower below 20; no auto rejection/approval.
- **Outstanding gates:** physical Android and authenticated Owner end-to-end visual acceptance, GitHub main branch protection (still unprotected as last observed), Off-VPS Restic recovery credential custody, exact SKU and origin proof where provider lacks authoritative data. Five allowed ship-from countries remain PL,CZ,FR,ES,DE as composite Owner attestation (no auto origin guess). Staging DuckDNS and noindex remain; commercial launch, domain switch, SEO and Meta changes are not authorized.

## REA availability and five-origin audit — 2026-10-28 (latest)

- **Staging deployment:** exact application code `b19fe804c05cf81cf340cce4cc27d0816f3dfaa3` installed over `2cf3487c` by [VPS Actions 40675018884](https://github.com/martaxi-boss/VPS/actions/runs/40675018884), **SUCCESS**. Pinned SSH host, recent local/offsite backups, clean revision, Django checks, no migration drift, first-affiliate-link guard, five family pages, local readiness, HTTPS/noindex external checks **PASS**. One-use VPS workflow branch removed. No DNS, indexing, advertising, publication, checkout or catalog DB changes.
- **Official AliExpress destination-field fix:** [PR #170](https://github.com/martaxi-boss/lowcost-europa/pull/170) with passing CI [40674274624](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40674274624) and main CI, fixes `aliexpress.affiliate.productdetail.get` to use documented `country=PT`; search still uses documented `ship_to_country=PT`. Provider docs: [detail API 48595](https://developer.alibaba.com/docs/api.htm?apiId=48595), [search API 45803](https://developer.alibaba.com/docs/api.htm?apiId=45803). No official automatic ship-from filter is declared by the current affiliate search method.
- **Verified VPS read-only status at 2026-10-28 10:36 UTC:** [Actions 40673496747](https://github.com/martaxi-boss/VPS/actions/runs/40673496747) **SUCCESS** (prior to this staging patch): 134 total Offers, 134 `is_active`, 0 inactive; 59 eligible for public display, of which latest observation 55 `AVAILABLE`, 4 `UNKNOWN`, 0 `UNAVAILABLE`; all 59 observed within previous 24 hours. Hourly maintenance active, last run 09:51:52 UTC exited 0; weekly discovery active, last run 2026-10-26 23:40:29 UTC exited 0. **AVAILABLE is technical detail evidence (product ID/title or URL), NOT a verified seller SKU/stock quantity guarantee.** Transient/unknown API observations must not cause unfounded deactivation.
- **Origin provenance:** five mandatory permitted origins PL/CZ/FR/ES/DE remain a composite Owner approval/revalidation attestation. In 59 eligible offers: 6 `ship_from_country=PL`, **53 NULL**, 0 other individually recorded origin; the missing individual field is allowed by the existing catalog constitution and is *not* evidence of forbidden origin. It does mean automated independent origin-per-listing verification is **unavailable**. The supported official Affiliate search API does not have a trustworthy ship-from filter; do not infer warehouse from title/seller/currency/ETA.
- **Queue pressure and weekly discovery:** [Actions 40673904816](https://github.com/martaxi-boss/VPS/actions/runs/40673904816) **SUCCESS**. 194 total pending. Cavitação/RF: 2 pending/18 public (runs); Hydrodermoabrasão: 40 pending/13 public (weekly cap20 prevents more search); Pressoterapia: 39/6 (blocked); HIFU: 4/13 (runs); Diodo/Laser: 101/9 (blocked). Three of five product **families** are paused at cap20; product families are not ship-from countries. Existing candidates cannot be silently rejected/deleted/approved to force the cap open.
- **Current factual-availability policy:** observed seller-unavailable status or unambiguous withdrawn-item error deactivates `is_active`; public listing and `/go/` then fail closed. Unconfirmed, unavailable stock by SKU, source API unknown values, and transient failures do **not** prove that an item is gone. The published store may therefore still show a product later unavailable in a seller-selected variant: no claim of 100% stock coverage.
- **Commercial gates unchanged:** `https://lowcost-europa.duckdns.org` staging only, robots and header noindex, public indexing/commercial launch remain OFF. No third-party stock data provider, product approval/publication, deletion/rejection, or automatic country inference introduced. Issue [#151](https://github.com/martaxi-boss/lowcost-europa/issues/151) retains the honest remaining Owner and governance gates.

## Final technical follow-up — 2026-10-28, REA 6.8.0

- **Remaining affiliate import path fixed:** [PR #167](https://github.com/martaxi-boss/lowcost-europa/pull/167) merged at application commit `2cf3487c941c77ca489ed543c249192c5ca273e2`. The legacy `import_aliexpress_product()` no longer generates a new affiliate URL or overwrites an already verified URL. New products created through that diagnostic persistence path have a blank affiliate URL. The publication-controlled workflow is unchanged. PR CI [40669879905](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40669879905) and code-main CI [40670128591](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40670128591) **SUCCESS**.
- **Current verified staging code:** `2cf3487c941c77ca489ed543c249192c5ca273e2`. [VPS Actions 40670545125](https://github.com/martaxi-boss/VPS/actions/runs/40670545125) **SUCCESS**: reversible change from `8b350bd0` with verified backups, pinned SSH, exact code, Django check/deploy check, migration drift/plan, private rate-limit guard, importer first-link guard, local readiness, five family pages, external HTTPS and noindex. Temporary deployment ref cleaned. Only existing Lowcost service was restarted; no schema, catalog publication, marketing, DNS or production change.
- **Historical credential-pattern scan:** [Actions 40670799560](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40670799560) **SUCCESS** over all Git-history objects reachable by the fetched refs: 3,065 unique Git objects, 1,060 unique blobs, approximately 8.2 MB of text inspected, 0 matching candidate blobs for supported private-key and known token patterns. 17 binary blobs were not scanned as text, 0 oversized blobs were excluded. This is a known-signature audit, **not a guarantee against all credential leaks**; unknown token formats, external stores and unreachable history remain unverified. The temporary audit branch was deleted.
- **Physical-device acceptance:** REA 6.8.0 `list_adb_devices` found 0 connected Android devices. Real Android/desktop human approval and authenticated Owner click-through still require a separate device/session; automated Chromium 12/12 success is not a substitute.
- **Governance:** GitHub `main` still reports `protected=false` with no active rulesets on 2026-10-28. The connected GitHub tool surface does not provide an administration write action to enable protection; no unverified protection was claimed.
- **Launch gates unchanged:** `lowcost-europa.duckdns.org` remains the test hostname. Nginx/app robots and `robots.txt` remain noindex/disallow. Public indexing, final domain, legal/operator identity, commercial go-live and advertising changes have not been authorized. Also requires Owner confirmation that Restic recovery bootstrap credentials exist outside the VPS.

## Most recent verified staging operations — 2026-10-28

- **Live pilot (existing VPS and DuckDNS test hostname only):** REA static inspection confirmed `/srv/lowcost-europa`; exact live base `eeff80db3d3473a447b79bd5637a70fc4a9b8d7b` was measured by read-only VPS Actions [40663608168](https://github.com/martaxi-boss/VPS/actions/runs/40663608168). The previous rollout [40663295570](https://github.com/martaxi-boss/VPS/actions/runs/40663295570) failed closed before any checkout because an older historical base was assumed, with `ROLLBACK_STATUS=not_needed`. The R2 transition used that independently measured clean base.
- **Deployed and verified application commit:** `8b350bd0cb92492e9d6f031f3472533336acd00d` on `146.59.145.3:/srv/lowcost-europa` from `eeff80db`, via proven pinned-SSH GitHub Actions [40664260730](https://github.com/martaxi-boss/VPS/actions/runs/40664260730). Backup preflight, exact revision, Django checks, migration drift/plan, noindex settings, private login throttle write, static assets, readiness, all five family pages, external HTTPS/robots and Git worktree readback **PASS**. Only the existing Lowcost service was restarted; no catalog/data, DNS, Nginx or other project changed.
- **Public browser regression:** [40664538172](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40664538172) **PASS**, 12/12 page/viewport combinations (home and five families; Chromium desktop and mobile-emulated), 13 checks, zero errors, zero horizontal overflow. [Screenshot and JSON artifact 12805341348](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40664538172/artifacts/12805341348). The test does not authenticate, publish, follow `/go/`, purchase or claim revenue.
- **Independent disaster-recovery drill:** [40664960134](https://github.com/martaxi-boss/VPS/actions/runs/40664960134) **PASS**: Restic offsite snapshot restored into a disposable directory; validated PostgreSQL dump restored into a *temporary* database; Django migration/core catalog tables queried; temporary database dropped and directory removed; `LIVE DATABASE MODIFIED=NO`. Pinned SSH and exact deployed SHA were reverified.
- **Operational observation:** three baseline services and five maintenance/backup timers active; daily backup checksum and `pg_restore --list` passed with backup approx. 6 hours old at preflight, offsite marker approx. 5 hours old. The one-use GitHub Actions task branches were verified deleted. No permanent VPS workflow was added to main.
- **Preserved limitations:** `https://lowcost-europa.duckdns.org` remains test-only; Nginx/app `noindex, nofollow` and `robots.txt Disallow: /` verified; no commercial domain, SEO launch, billing, advertising adjustment or public launch was performed. Remaining Owner/manual items: real physical-device and authenticated Owner flow acceptance, GitHub `main` governance protection (`protected=false` last observed), confirmation that Restic bootstrap credentials are recoverable *off the VPS*, legal/operator contact data, final commercial domain, purchase/commission attribution and explicit commercial launch authorization.

## Addendum — pilot corrections verified 2026-10-28 (without commercial launch)

- **GitHub main:** `bdf27346d7e3b9bb8064c96cc8d5067f5fe4decd` after PR #161 and #162. CI main run [40658869462](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40658869462) **SUCCESS**; the implementation PR runs [40656957589](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40656957589) and [40658555718](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40658555718) also passed.
- Owner/admin password login fails closed when rate-limit state cannot be read or durably written. The private dashboard shows raw outbound OfferClicks over the last 7 days and visible offers without a recent observed `last_seen_at`; these figures are **not buyers, orders, commissions or unique users**.
- Social sharing metadata now includes a factual brand image. This does not enable indexing.
- Candidate approval does **not** generate the first affiliate link: a newly approved Offer remains hidden with promotion status UNKNOWN. The Owner's explicit publication generates and verifies the official AliExpress HTTPS link; unsuccessful generation does not publish. Previously verified links and current visibility are preserved by approval. Maintenance does not generate initial affiliate links for hidden, unlinked Offers.
- **Test-only hostname:** `https://lowcost-europa.duckdns.org` remains the intended pilot domain. Nginx `X-Robots-Tag: noindex, nofollow`, app meta noindex and `robots.txt Disallow: /` remain unchanged. **No SEO indexing, new commercial domain, public launch, campaigns or spending are authorized** by these changes.
- **Runtime evidence boundary:** source CI was not by itself proof of deployment. The separately verified VPS rollout, current deployed SHA, timers, live HTTPS QA and restored offsite snapshot are certified in the latest 2026-10-28 addendum above.
- **Governance boundary:** GitHub `main` reports `protected=false` on 2026-10-28 and no active repository rulesets. This is an outstanding GitHub administration control, not something remedied by CI or by these PRs. Open issue #151 retains real-device and operational acceptance follow-ups.

## Current status — staging certified, human/commercial acceptance pending

- Application corrections, CI and staging rollout are **COMPLETED AND VERIFIED** as of 2026-10-28. Current deployed code: `8b350bd0cb92492e9d6f031f3472533336acd00d`, proven on the existing VPS by Actions `40664260730`. Later commits which contain only control records and documentation do not require another service restart.
- Latest verified main CI for the documentation/control authorization: [40664052344](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40664052344) **SUCCESS**; source code test run [40659389026](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40659389026) **SUCCESS**. Chromium public staging run [40664538172](https://github.com/martaxi-boss/lowcost-europa/actions/runs/40664538172) **PASS**: home and all five families in desktop and mobile-emulated viewports, 12/12 page/viewport checks, zero failures. Independent offsite restore run [40664960134](https://github.com/martaxi-boss/VPS/actions/runs/40664960134) **PASS**.
- No open pull requests at this audit. Issue #151 remains **OPEN** specifically for genuine physical-device, authenticated Owner workflow, independent restore/backup, feedback and security/governance follow-ups.
- Public GitHub repository is not authorization for search indexing, DNS changes or commercial GO-LIVE. Preserve `noindex, nofollow`, human publication controls and sandbox scope.
- Historical headings, counts and infrastructure notes below describe prior snapshots, not a claim that today's runtime equals 2026-09/10 values.

## Addendum — technical pilot revalidation (2026-10-14)

- GitHub repository visibility is **PUBLIC**. This is a repository-access change, **not** permission for commercial GO-LIVE or website indexing.
- **Current integrated application baseline:** `main` commit `ed067409c997daacee7c19d6a8ca36fa98494e82` (PR #152). Older baseline `82ff2d68835bf083de3b4da6ce674ae24631b3c5` below is historical; later documentation-only commits can change the HEAD without changing application code. The live staging revision was independently certified in VPS run `38591194575`.
- Technical pilot improvements are **MERGED and DEPLOYED TO EXISTING STAGING**: verified application Git HEAD `f0d520d31ef6a3aa06ee11f2793be50f75d58a2c` on 2026-10-14 via pinned-SSH VPS run `38591194575`. Earlier `82ff2d68835bf083de3b4da6ce674ae24631b3c5` remains the documented rollback version; later `main` documentation/control descendants do not need a staging restart.
- On merged `main` application commit `ed067409c997daacee7c19d6a8ca36fa98494e82`, GitHub Actions run `38583874116` completed **SUCCESS**: 638/638 Django tests, 6/6 Node image tests, Ruff, Django checks and PostgreSQL migrations.
- Repository/CI tests are green. **The staging rollout has since passed**: actual VPS Git SHA independently verified, Django checks/migration plan/collectstatic/readiness PASS, all five family endpoints HTTP 200, new `/static/storefront/product-images.js` served over HTTPS, homepage meta and Nginx headers `noindex, nofollow`, robots `Disallow: /` (VPS Actions `38591194575`). Previous HTTP probe `38582509781` predates this deployment. Local backup SHA256 and `pg_restore --list` PASS; recent offsite success marker observed but an independent full restore was not performed in this rollout. Real Android/desktop browser assessment, authenticated Owner workflows and human feedback remain pending.
- Pilot work items/feedback: issue #151. Documentation-hygiene PR #147 was **MERGED** at `4b2a96cbcd3a101e1f65ceea11072d58328195e9` and removed four SHA-identical archived screenshots. Neither PR #147 nor #152 authorizes commercial launch or performs a VPS deploy.
- Commercial deployment, final domain, public indexing, changes to Owner approval/publication gates and a marketing launch all remain **unauthorized**.


## Completed baseline

- Owner status: completed / fully operational within the accepted project scope.
- Verified GitHub application baseline: `82ff2d68835bf083de3b4da6ce674ae24631b3c5`.
- PR #146 merged on 2026-09-30. PR-head CI runs `36763343523` and `36763348828`: success; accepted closeout: 623 tests.
- Runtime equality was accepted in the prior closeout; this task does not renew live VPS evidence.
- Architecture frozen: Python 3.12, Django 5.2 LTS, PostgreSQL, Gunicorn, Nginx, systemd, OVH.
- Administration: GitHub workflows. Desktop Commander/self-hosted runners are not the current operating path.
- Documentation-only commits advance main without changing/restarting the runtime.

The accepted technical scope stays closed. No new construction, architecture rebuild, public launch or indexing activation follows from this document. Final commercial domain, operator/legal inputs and commercial activation remain separate Owner decisions.

## Catalog and human workflow

`DISCOVERY → FAMILY RELEVANCE → GLOBAL DEDUPE → FAMILY RANKING → PENDING / A REVER → HUMAN APPROVAL → HIDDEN OFFER → HUMAN PUBLICATION → PUBLIC ELIGIBILITY → FACTUAL MAINTENANCE`

Product identity: `(source, external_product_id)`. ProductFamily is durable; OfferFamilyPlacement supplies public family membership. Retired taxonomy and decision/observation/click/move history remain preserved.

Operational family order/public names come from the database. Five operational slugs:

1. `cavitacao-rf-vacuum-corpo`
2. `hydrodermoabrasao-aqua-facial-multifuncoes`
3. `pressoterapia-vacuum-drenagem`
4. `hifu`
5. `diodo-laser-remocao-tatuagens-pigmentacao`

Owner panel: `/painel/`, authenticated staff only. Approval, rejection, revalidation, publication, hiding and family moves remain human actions.

Approval attests delivery to Portugal and ship-from within PL/CZ/FR/ES/DE, verified on the actual listing. Individual country metadata is optional and never fabricated. Approval records the Owner's attestation and a hidden Offer without generating its first affiliate link. New affiliate links are generated through the official AliExpress path only when the Owner explicitly publishes the Offer. Previously verified links and existing editorial visibility remain unchanged on approval. Hourly maintenance does not create an initial affiliate link for hidden unlinked Offers.

Approval is not a positive discovery-learning signal. Semantic rejections and classification moves remain family-isolated; factual/logistics failures do not become semantic rejection signals.

## Public eligibility and lifecycle

Central gate: `apps/catalog/services/public_eligibility.py`.

- `is_active=True`, `owner_hidden=False`, non-empty affiliate URL;
- `affiliate_promotion_status=ELIGIBLE` and non-null `affiliate_promotion_verified_at`;
- non-null `protocol_verified_at`, not in the future.

Protocol age expiry: **NONE**. Time alone never hides an eligible Offer. Ship-from metadata is optional; human attestation remains mandatory. Price/observation availability are separate editorial concerns.

Public placement/publication respects operational families and cap 20 per family. Storefront and `/go/<offer_id>/` share the central gate; ineligible Offers do not redirect or create valid clicks.

Only factual unavailability deactivates Offers. Transient errors/rate limits/insufficient detail do not establish unavailability. Maintenance never renews human protocol, auto-publishes, clears Owner hiding or auto-reactivates inactive Offers.

## Discovery and maintenance

- Weekly discovery: Monday 23:40 UTC, five families sequentially, Persistent=true.
- Creates PENDING candidates only; no auto-approval/publication, final affiliate generation or Offer editorial mutation.
- Weekly intake pauses at 20 pending candidates per family. This is a campaign budget guard, distinct from public cap 20; existing candidates are not deleted.
- Hourly maintenance: scheduled batch 10; command range 1–20; settings fallback 5.
- Shared AliExpress locking/cadence/retries/backoff/jitter/Retry-After/rate-limit breaker remain unchanged.
- Shared state: `/run/lowcost-europa/`; preserve tmpfiles provisioning and PrivateTmp=true.
- HIFU logistics recovery remains paused independently of weekly discovery.

## Accepted storefront

- `VER EQUIPAMENTOS E PREÇOS` → `#familias`.
- Existing five public family names/order preserved.
- `VER PREÇO E COMPRAR NO ALIEXPRESS` → `/go/<offer_id>/` only.
- WhatsApp: `/contactar/whatsapp/` → `351965471236`.
- Public reads use PostgreSQL, not AliExpress. Purchase/payment/order support belongs to the partner.
- OfferClicks are outbound clicks, not sales/commission evidence.

## Infrastructure and evidence boundaries

Owner policy: one OVH VPS, GitHub-hosted workflows, credentials outside source control in the VPS cofre. Historical documents do not authorize paid provider backups or old administration tooling.

Versioned PostgreSQL/Restic scripts, systemd units and regression tests remain recovery implementations. Their presence does not prove active timers or authorize reinstating old backup policy. Current backup health, packages/kernel, systemd state and runtime SHA require live host verification; September snapshots are historical.

Technical closeout did not authorize public launch/indexing. Fail-closed indexing controls remain. No legal/commercial activation is certified by this cleanup.

## Document authority

Read PROJECT_CONSTITUTION.md, PROJECT_STATE.md and AGENTS.md in order. Catalog rules: docs/catalog/CATALOG-CONSTITUTION.md. Architecture: docs/ARQUITETURA-DO-SITE.md.

Phase reports, initial ADRs, old runbooks and QA captures are checkpoint evidence only. They cannot reopen completed tasks, supersede current authorization or restore old rules/infrastructure. See docs/README.md. Git history retains superseded versions.
