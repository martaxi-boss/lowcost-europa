# Lowcost Europa — Project State

## Graceful reload deployed; Bing Live recovered — 8 November 2026, 13:42 UTC

Seven upstream connection refusals were correlated by second with controlled application stop/start events. [PR #225](https://github.com/martaxi-boss/lowcost-europa/pull/225) adds the missing Gunicorn HUP reload handler. Its test and audit checks passed. [Guarded production rollout #42486100692](https://github.com/martaxi-boss/VPS/actions/runs/42486100692) deployed `4f59453306aeebbc37849f9face098f8a2133c50`: **75/75 HTTPS requests returned 200** across homepage, robots and sitemap during an actual reload; the listening master stayed unchanged and old workers were replaced. Private panel/admin routes retained login redirects and noindex/private headers; private environment, operator data and Nginx checksums stayed unchanged. The app and IndexNow timer remained active. This removes a demonstrated update interruption mechanism; it does not establish the cause of the engines' sitemap errors.

**Authenticated Bing follow-up:** homepage Live URL at 13:42 again reports **URL can be indexed by Bing** and **No SEO/GEO issues found**, recovering from the 11:33 fetch failure. No causal claim is made from this timing. The homepage and all five category index inspections still report **Discovered but not crawled**; sitemap still **Error / 0 discovered**. No index request or sitemap resubmission was sent. Google currently redirects to its signed-out account chooser, so no fresh Google sitemap/index result is asserted; its earlier six confirmations remain historical evidence. Yandex's previously observed service-side read-only restriction is not reinterpreted as resolved.

Production checks are GitHub Actions→SSH evidence, not a new Ferrari engine-job certification. The existing monitoring task must remain active; the completion conditions are unmet. Required rollback checkpoints and IndexNow state are retained; only temporary task workflows are removed.


## Sitemap diagnosis and Bing Live regression — 08/11/2026, 11:34 Lisbon (latest)

- **Bing Live regression:** authenticated tests of sitemap at 11:31 and homepage at 11:33 now report unable to fetch / cannot be indexed. This supersedes the earlier successful homepage Live test; it is not confirmation that an indexed page was removed. The homepage index report remains Discovered but not crawled.
- **Independent transport passes:** [public probe #42476080980](https://github.com/martaxi-boss/VPS/actions/runs/42476080980) received HTTP 200, valid TLS and the same valid 922-byte/11-URL XML in all twelve request variants. No production change or resubmission.
- **Fresh correlation:** [server audit #42476188412](https://github.com/martaxi-boss/VPS/actions/runs/42476188412) found a DNS-forward/reverse verified Bing source receiving /sitemap.xml HTTP 200, 922 bytes, at 11:31:27. Logs are shared and lack the requested host, so this is time/path/size correlation, not definitive per-vhost attribution. No verified Google fetch is established by these samples.
- **Unresolved:** the engine-reported fetch failure has no reproduced site-side cause yet. Google/Bing sitemap acceptance, Bing six-page index inclusion and Yandex's read-only sitemap service remain pending. Do not make speculative runtime changes. [Detailed limitations and evidence](docs/operations/international-search-20261108.md).


## Yandex ownership confirmed — 08/11/2026 (latest)

- **Ownership confirmed by authenticated Yandex Webmaster:** Manage access shows the Owner role, verification by root HTML file and verification date 08/11/2026. The prior owner-action gate below is resolved. No verification value or account identifier is published here.
- **New external blocker:** Yandex Sitemap files explicitly reports read-only mode while its engineers restore service; Add is disabled. No sitemap was submitted and no workaround or duplicate IndexNow request was attempted.
- **Index inclusion remains unconfirmed in Yandex.** Ownership verification does not establish crawling or index inclusion. [Current authenticated observations](docs/operations/international-search-20261108.md).
- This update is documentation only; the previously deployed proof and configuration remain in place. Google/Bing sitemap errors and the Bing six-page index confirmations remain pending.


## Search follow-up — 08/11/2026, 10:21 Lisbon

- **New confirmed public result:** Brave displays the homepage; categories remain unconfirmed there. Seznam accepted the direct homepage submission; this is not index inclusion.
- **Yandex:** owner authentication/account creation completed, canonical property added, proof deployed privately via [PR #221](https://github.com/martaxi-boss/lowcost-europa/pull/221) and [VPS #42471054301](https://github.com/martaxi-boss/VPS/actions/runs/42471054301). **Owner must press Verify and accept the Webmaster agreement** before ownership, sitemap processing or indexing can be confirmed.
- **Current checks:** Google session restored; authenticated Google sitemap remains “Não foi possível obter” / zero. Bing sitemap remains Error / zero; homepage plus five categories show Discovered but not crawled. No duplicate requests.
- **IndexNow:** live dry run `public=11 changed=0 removed=0`, accepted state unchanged, no submission. 778 tests PASS; public routes, HTTPS and private-panel controls PASS.
- **Deployed application/config revision:** `ffbacda4c5c166e204a0bf2b8d621099480c8f7e`; later documentation-only alignment does not change runtime behavior. DNS/email preserved. [Full current evidence](docs/operations/international-search-20261108.md).


## Estado canónico e higienização — 08/11/2026 (atual)

- **Domínio único de produção:** `https://www.lowcost-europa.eu`; raiz → WWW por HTTPS 301. DNS de Dynadot, correio e certificados oficiais permanecem ativos. O domínio de teste DuckDNS e os subdomínios `sslip.io` deixaram de fazer parte do Nginx, dos hosts Django e da renovação de certificados da Low Cost Europa.
- **Código operacional:** branch GitHub `main` única, sem PR abertas. As 14 branches antigas foram eliminadas com proteção de SHA; as oito com trabalho próprio mantêm tags de arquivo `archive/lowcost-20261108/*`. Não reintroduzir branches de teste.
- **QA:** [PR #220](https://github.com/martaxi-boss/lowcost-europa/pull/220) integrada, 778 testes PASS, 15 checks de browser WWW PASS, segurança PASS; capturas de provas antigas retiradas da árvore, sem eliminar testes atuais.
- **VPS:** [higiene #42439717221](https://github.com/martaxi-boss/VPS/actions/runs/42439717221) PASS; 15 caches removidas e redução medida de 4352 KiB. Cinco categorias, sitemap, painel privado, indexação, Nginx e timers PASS. [Certificados antigos #42439829660](https://github.com/martaxi-boss/VPS/actions/runs/42439829660) removidos com prova de zero consumidores, certificado WWW e demais projetos preservados.
- **Fonte de procedimentos:** [relatório final e manutenção segura](docs/ops/LOWCOST-HYGIENE-20261108.md). As secções antigas de migração DNS, staging e `noindex` deste ficheiro **são históricas e não autorizam restaurar configurações ultrapassadas**.
- **Limite comercial:** a AliExpress ainda não certifica todos os SKUs, armazéns e prazos. Não inventar stock/disponibilidade nem garantias de entrega. O site público funciona tecnicamente, não há validação comercial integral.

## Bing homepage quality and IndexNow acceptance — 2026-11-08 00:46 Lisbon

- **Deployed PR #212:** `f1c1a3a8d3e6336721a201301cd43a7a8ac50cd1`. Homepage title is descriptive in all five existing languages; category image alternatives are meaningful/localized. [Rollout #42431236626](https://github.com/martaxi-boss/VPS/actions/runs/42431236626) PASS: 9/9 homepage images have alt text, canonical/index-follow/HTTPS and private login routes preserved; no configuration changes.
- **Bing live confirmation at 00:46:** URL can be indexed by Bing; **No SEO/GEO issues found**, replacing the previous two notices. This is live eligibility, not Bing index inclusion; the homepage remains Discovered but not crawled in the index report.
- **IndexNow resolved:** live submission returned **HTTP 200**, all eleven URLs received and key accepted. This supersedes the earlier HTTP 202/key-pending state. Index inclusion by individual participants is still unconfirmed.
- **Validation:** CI #42431063213, security #42431063206 and four-viewport source browser QA #42431063222 PASS; nine focused presentation tests passed locally. The broader local language tests lacked PostgreSQL; CI provided the database-backed full validation.
- **Remaining:** Google confirms the six inspected URLs indexed (details below); sitemap reports still show fetch errors despite real successful access. No repeat sitemap or individual indexing requests in this follow-up. [Current evidence](docs/operations/international-search-20261108.md).

## Search recheck — six Google pages confirmed indexed, 2026-11-08 00:35–00:37 Lisbon

- **Google confirmed individually:** homepage and all five categories show “O URL está no Google” / “A página está indexada”, HTTPS confirmed. This supersedes the earlier pending state for those six pages only. Institutional pages and other engines remain unconfirmed.
- **Bing:** homepage now Discovered but not crawled; Live URL says URL can be indexed by Bing; robots.txt Tester says sitemap Allowed. Sitemap report still Error / zero discovered. Verified Bing crawler access to the actual sitemap returned HTTP 200 (reverse DNS + forward match).
- **IndexNow:** live recheck again HTTP 202 for eleven public URLs; key validation still pending. Timer and proof file healthy. No duplicate individual indexing requests.
- **Google sitemap:** report still Couldn't fetch / zero discovered, re-submission accepted successfully. Per-page indexing confirmation remains valid independently of this report.
- **Evidence/preservation:** [recheck #42430294495](https://github.com/martaxi-boss/VPS/actions/runs/42430294495) PASS; DNS/email, HTTPS, app, timer and private operator permissions preserved. No runtime code/configuration change in recheck. [Detailed current report](docs/operations/international-search-20261108.md).


## International search discovery — 2026-11-08

- **Deployed:** PR #209, application revision `93c5dedcf0877eeff583b2863fe246d132c7225c`; 754 tests and security analysis PASS. Independent VPS checks #42428884310 and #42429109681 PASS. IndexNow timer active/enabled, private key proof HTTP 200, 11 public URLs received with HTTP 202 (key verification pending). Notifications are hourly and preserve pending state until HTTP 200; no index inclusion implied.
- **Bing:** property imported from Google after owner-approved read-only access; six direct URL submissions confirmed (homepage + five categories). Sitemap initially failed with The page is not accessible despite independent HTTP 200/TLS checks; re-submitted once, latest observed Processing / zero discovered. No confirmed successful sitemap processing or indexed page.
- **Other engines:** Brave homepage re-fetch submission accepted; DuckDuckGo and Seznam site queries showed no results, Yahoo no matching domain result. Yandex search and Brave status query required human verification. IndexNow shared receipt covers participants including Bing/Yandex/Seznam, without individual crawl/index confirmation.
- **Preservation:** external audit passes 11 public pages, three private endpoints, three canonical redirects and five synthetic bot agents. Panel/admin still require login and noindex/private. DNS/email records, HTTPS, Nginx, catalog and database schema preserved.
- **Evidence and limitations:** [international search report](docs/operations/international-search-20261108.md), [external HTTP evidence](docs/operations/international-public-audit-20261108.json). Pending engine processing is explicitly unresolved; do not declare indexing complete.

## Public technical launch and Google requests — 2026-11-07

- **Application deployed:** `51bee8009492c3cd5855f4aae71de3597fd1965b` from PR #207. [Guarded VPS launch #42422451050](https://github.com/martaxi-boss/VPS/actions/runs/42422451050) PASS: PUBLIC_INDEXING_ENABLED=true, legal identity privately provisioned, Django/Nginx healthy, no migrations. Main CI #42422298302 passed 744 tests; Chromium #42422298343 and source audit #42422298429 passed.
- **Public SEO:** external verification passed 11/11 sitemap pages with HTTP 200, index/follow, exact WWW canonical and no noindex header; 52/52 affiliate routes HTTPS with sponsored/nofollow. Panel/admin still require authentication and remain noindex/private, as do operational endpoints, search and noncanonical hosts. HTTPS and redirects remain valid; mail DNS unchanged.
- **Google confirmed:** domain ownership verified by additive Dynadot TXT; six individual indexing requests (home + all five categories) each accepted into the priority crawl queue. This is **not** confirmation of index inclusion.
- **Sitemap:** submission accepted, but the sitemap report initially still showed Couldn't fetch / zero discovered URLs. The live Google smartphone test at 22:59:54 successfully fetched the XML, with crawling and indexing permitted. Sitemap processing and actual indexing remain external pending states; do not declare them complete.
- **Legal data:** supplied by the owner, stored only in private VPS configuration, rendered on contact/terms/privacy. No real identity fields in source/tests/logs. Temporary encryption key and launch workflows removed, rollback preserved.
- **Closeout:** [full report](docs/operations/indexing-closeout-20261107.md) and [postlaunch public evidence](docs/operations/indexing-public-after-20261107.json). Final documentation alignment checks that only documentation differs from the deployed application revision and confirms clean Git/VPS state.


## Indexing preparation and verified domain — 2026-11-07

- **Current production evidence:** [VPS audit #42421004057](https://github.com/martaxi-boss/VPS/actions/runs/42421004057) confirms main and VPS at `bb3921b646102cba0af0f397bddfde8b2f37d39a`, clean tracked files, active Django, valid Nginx, HTTPS SAN apex+WWW and renewal timer. The earlier "DNS/cutover pending" section below is historical and superseded by this readback.
- **Google domain ownership:** `lowcost-europa.eu` confirmed by Search Console through an additional Dynadot TXT; all existing site/email records preserved. Ownership verification is complete; Google URL inspection still says the homepage is not indexed / unknown.
- **Operator identity supplied by the owner:** individual name, address and fiscal ID were supplied in the conversation. They are deployed privately and rendered only on the authorized legal pages, never committed to source or logs. The loader fails closed if incomplete. Public noindex remains in force until guarded deployment and live acceptance.
- **Preparation only:** draft PR #207 bounds indexing to the canonical hostname, keeps operational routes private, qualifies affiliate links and includes regression tests. Not deployed or merged. Sitemap submission and six indexing requests remain outstanding until legal completion and launch verification.
- **Live offers:** 52 eligible links, 17/10/5/12/8 across the five categories. All 52 HEAD routes return HTTPS affiliate redirects. Three observed prices older than seven days; latest stock observations all UNKNOWN. No stock, checkout-price, delivery or commission guarantee.
- Evidence and continuation: [indexing readiness report](docs/operations/indexing-readiness-20261107.md), [public HTTP audit](docs/operations/indexing-public-audit-20261107.json). Temporary VPS audit workflow removed after completion. No runtime application data or backup deletion.


## Dynadot paid domain readiness — 2026-11-07 (DNS and cutover pending)

- **Última decisão:** endereço principal `https://www.lowcost-europa.eu`; `https://lowcost-europa.eu` deve passar por 301 para WWW após certificado, contacto público `geral@lowcost-europa.eu` no site todo. O Gmail de destino para encaminhamento permanece privado e a ativação não é verificável por DNS; a configuração na Dynadot fica pendente de confirmação. Indexação comercial só depois de certificar todos os gates de lançamento.


- Intended primary domain **lowcost-europa.eu** using **Dynadot DNS**; no Cloudflare. The authoritative DNS preflight [VPS #42405767220](https://github.com/martaxi-boss/VPS/actions/runs/42405767220) confirmed ns1/ns2.dyna-ns.net, but both apex/www A records still point to Dynadot parking **185.53.179.149**, not the OVH VPS **146.59.145.3**.
- Existing Dynadot email MX, SPF, DKIM and DMARC are publicly present and must be preserved. Mail DNS does not certify functional send/receive.
- VPS application live at **fefd5df92753382bb7ad191ee19e38b90d8167a3**; Django active, Nginx config valid, old DuckDNS health PASS. New TLS certificate, vhost, allowed hosts, CSRF origins and primary URL are **NOT YET configured**.
- Source-only domain preparation supplies separate HTTP ACME and eventual HTTPS Nginx configurations and [operational runbook](docs/operations/custom-domain-dynadot-20261107.md). **Do not activate SSL template until certificate issuance and both DNS A records verified.** Keep DuckDNS and noindex until fully checked.

## IP-country storefront language — live staging certified 2026-11-07

- [PR #202](https://github.com/martaxi-boss/lowcost-europa/pull/202) and [PR #203](https://github.com/martaxi-boss/lowcost-europa/pull/203) merged; VPS deployed matching SHA **fefd5df92753382bb7ad191ee19e38b90d8167a3** in [rollout #42404667890](https://github.com/martaxi-boss/VPS/actions/runs/42404667890). Country MMDB in project-local .geoip/; service, backups, HTTPS and noindex PASS.
- Exact rule: public IP country **PT→pt-PT, ES→es, FR→fr, DE→de, GB→en; all others and unresolved→en**. Browser language and an old cookie are ignored on the public storefront when IP mode is enabled. VPN egress IP is treated like any other.
- [VPS six-country QA #42404916518](https://github.com/martaxi-boss/VPS/actions/runs/42404916518) PASS for PT/ES/FR/DE/GB/NL with local requests that supply database-derived public-IP samples. These are **not six independent live VPN connections**. The first provision attempt [#42404168316](https://github.com/martaxi-boss/VPS/actions/runs/42404168316) failed safely on protected data/ directory and rollback passed; isolated .geoip/ fixed it without weakening private data permissions.

Historical reconciliation baseline: 2026-10-03. Most recent verified staging evidence before this source-only update: 2026-10-30.

## GitHub source and hygiene — 2026-11-07 (runtime deployment not yet certified)

- **Integrated source:** GitHub `main` at `d1562eb8458652bdf0a04fa60ee6029a4b60514e` after [PR #196](https://github.com/martaxi-boss/lowcost-europa/pull/196) (professional storefront redesign) and [PR #197](https://github.com/martaxi-boss/lowcost-europa/pull/197) (safe GitHub hygiene). No database schema, automatic publication, DNS, commercial indexing or affiliate integration change was introduced by the visual PR.
- **Source CI:** post-merge [CI #42388935895](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42388935895) SUCCESS, [source-browser Chromium QA #42388935881](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42388935881) SUCCESS (synthetic catalogue; four viewports), [Final audit evidence #42388935902](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42388935902) SUCCESS. The prior branch CI covered 717 Django tests. Passing CI does not prove current VPS SHA or real product photography quality.
- **GitHub hygiene:** tracked generated files blocked by CI, ignore rules for disposable caches and browser output, and guarded merged-PR branch pruning. [#42385458184](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42385458184) cleaned eight provably merged refs; [#42388936280](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42388936280) handled the visual PR ref. Unmerged history was preserved.
- **VPS hygiene:** [#42389097397](https://github.com/martaxi-boss/VPS/actions/runs/42389097397) ran the existing allowlisted cache cleaner, reported NO_ELIGIBLE_CACHE across seven allowed roots, with services unchanged and zero application or DB data deleted. The issue was closed.
- **Verified VPS readback (07/11/2026):** [inventory #42389288194](https://github.com/martaxi-boss/VPS/actions/runs/42389288194) confirmed `/srv/projects/lowcost-europa` at `388860c6a167686a378b89f4282304bce89c25de`, service `active`, and **9 modified tracked files**. At this checkpoint, GitHub source `d1562eb8458652bdf0a04fa60ee6029a4b60514e` was 17 commits ahead; the VPS was not updated. The independent read-only [blob audit #42389467108](https://github.com/martaxi-boss/VPS/actions/runs/42389467108) found eight VPS-local modifications whose blob IDs already equal GitHub `main`; the ninth, `deploy/scripts/offsite-restore-drill.sh`, has a VPS-only blob not available in public Git history. **Do not overwrite, reset or deploy over that backup-recovery script until it is reviewed and securely preserved.** No VPS rollout was attempted. Source-browser CI uses synthetic offers and cannot certify real photography, logged-in Owner interaction or physical Android QA.
- **Commercial controls:** `noindex`, test hostname, legal/operator information and final domain decision remain outside this redesign; do not activate launch or paid campaigns. `main` branch protection is still an administrative task.


## REA FINAL verified live audit and bounded corrections — 2026-10-30

- **Current staged revision verified independently:** GitHub `main` and VPS staging both at `8b8bdaeaeb49f01def64b127f1b0c1459d5cf24e`, clean worktree. REA native MCP process captures [41064710140](https://github.com/martaxi-boss/VPS/actions/runs/41064710140) and [41065936402](https://github.com/martaxi-boss/VPS/actions/runs/41065936402) recorded Django `check`, `check --deploy`, migration-drift checks, PostgreSQL reads, public routes and five categories, HTTP 200, and private-panel login redirects. Latest `main` CI [41042308845](https://github.com/martaxi-boss/lowcost-europa/actions/runs/41042308845) passed 706 Django tests.
- **Catalog reality, not stock guarantee:** 135 active stored offers and 59 public-eligible offers at audit; 53 eligible offers lack independently recorded individual origin. Latest 59/59 observations had `UNKNOWN` availability, although each offer has older `AVAILABLE` evidence and historic price. Five price observations were older than 24h (none older than 7d). Only 2/59 offers had *any* numeric delivery-days evidence; this does not certify the 5-day promise. Data read through REA [41065087404](https://github.com/martaxi-boss/VPS/actions/runs/41065087404), [41065485543](https://github.com/martaxi-boss/VPS/actions/runs/41065485543), [41065936402](https://github.com/martaxi-boss/VPS/actions/runs/41065936402).
- **Queues/hygiene:** 192 pending candidates total: 184 across five operational families and eight historical candidates in `microcorrente-ultrassons` (`RETIRED`). Three operational families remain above the 20-candidate cap. No automatic approval, rejection, origin inference, backlog deletion, or cap increase is authorized. The corrective Owner dashboard work only surfaces factual warnings and archived queue counts; the existing manual decisions remain mandatory.
- **Operations:** last local, offsite and offsite-health backup services exited 0; live restore drill is *not* part of this audit. HTTPS certificate/HTTP redirect/static JS syntax passed in [41066187870](https://github.com/martaxi-boss/VPS/actions/runs/41066187870). REA [41065087404](https://github.com/martaxi-boss/VPS/actions/runs/41065087404) saw no HSTS or CSP response headers. The staging environment explicitly set `DJANGO_SECURE_HSTS_SECONDS=0` in [41066856729](https://github.com/martaxi-boss/VPS/actions/runs/41066856729); a short, opt-out production default in source does not modify that runtime override until deployed/configured.
- **Limits:** this audit is not a penetration test, physical Android test, authenticated Owner acceptance, external AliExpress warehouse/SKU confirmation, or end-to-end commission attribution. GitHub `main` still has `protected=false`; protection requires separate GitHub administration. The final domain, public indexing, Meta ad changes and commercial GO LIVE remain OFF.


## REA FINAL corrective quality and hygiene — 2026-10-30

- **Verified deployed baseline:** GitHub main and staging VPS both reported application revision `28c998e88bb723424c8ed36d4ba93904339ec877` during [VPS Actions 41019784552](https://github.com/martaxi-boss/VPS/actions/runs/41019784552). Pinned host, backups, Django checks, migration plan, local readiness, DuckDNS HTTPS/noindex and private login checks passed. Automated Chromium desktop/mobile staging checks reported 15/15, zero errors.
- **Baseline security:** [GitHub Actions 41019656392](https://github.com/martaxi-boss/lowcost-europa/actions/runs/41019656392) passed pip-audit and Bandit; baseline CI passed. The original REA FINAL in VPS performed its own read-only frontend scan in [Actions 41041261678](https://github.com/martaxi-boss/VPS/actions/runs/41041261678); JavaScript syntax was parsed without errors, but semantic coverage is partial. This is not a Python/Django penetration test.
- **Corrective source changes:** [PR #184](https://github.com/martaxi-boss/lowcost-europa/pull/184) bounds the historical observations fetched by the storefront while preserving original PostgreSQL facts; makes missing individual ship-from evidence and paused candidate queues visible in the private owner dashboard; preserves human-only candidate decisions; adds accurate seller-side stock/origin copy; and widens the existing security-audit workflow to application, configuration, deployment, test and workflow changes. No new server, MCP, provider, migration or third-party analytics is introduced.
- **Evidence boundary:** the deployed SHA above predates PR #184. Its new code must not be described as deployed until a matching, successful staging rollout has been independently observed. A green source CI is not itself a deployment.
- **Remaining external dependencies:** GitHub main branch protection requires repository administration; individual seller SKU/warehouse truth is not provided reliably by the available AliExpress Affiliate API; physical-device and authenticated Owner scenario acceptance, Meta server credentials/report freshness and off-VPS Restic recovery-secret custody require real operational verification. Do not auto-approve/reject products or invent shipping origins to clear these gates.
- **Commercial controls:** final commercial domain, legal/operator launch gates, indexing, Search Console, Meta campaign changes and public GO LIVE remain outside this corrective work; DuckDNS and `noindex` remain the staging baseline.

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
