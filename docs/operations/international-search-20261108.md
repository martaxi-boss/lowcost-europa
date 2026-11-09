# International search discovery — 8 November 2026

## Bing sitemap processing confirmed — 9 November 2026, 07:14–07:17 Lisbon

**Material change, authenticated Bing report:** the canonical sitemap https://www.lowcost-europa.eu/sitemap.xml now reports **Success**, **23 URLs discovered**, zero sitemap errors and zero warnings. The dashboard displays last submit and last crawl as 11/9/2026 (9 November). This supersedes Error/0 for Bing sitemap processing. It does not establish page index inclusion. No submission was made during this check; the displayed submission date differs from the older baseline and its cause was not investigated or attributed.

**Per-page Bing checks:** homepage, Cavitação, Hydrodermoabrasão, Pressoterapia, HIFU and Diodo were inspected separately via Bing Index. All remain **Discovered but not crawled**, discovered 8 November. No Request indexing action was used.

**Google access boundary:** official APIs Explorer was configured for sc-domain:lowcost-europa.eu with only webmasters.readonly (write scope and API key disabled). Execute reached the Google account chooser, where the available accounts were signed out. No authenticated response was obtained, no credential/token exported and no login/CAPTCHA cycle attempted. The 8 November 18:43–19:07 pending sitemap responses and six indexed confirmations remain historical evidence; no new Google resolution or regression is inferred. Secure browser authentication is required for a fresh authenticated Google check in an interactive session.

**Other engines:** authenticated Yandex Sitemap files still explicitly read-only with Add disabled; no submission. Seznam products-path public query still returns only the homepage, with categories unconfirmed. Yahoo domain query displayed no matching domain link; this is not proof of global absence. DuckDuckGo returned 418.html / error 5401, leaving inclusion unknown. Brave six-page public baseline is retained, with no re-fetch or submission. A new read-only Brave search navigation was stopped by automatic approval review as a perceived repeat of the confirmed check; it was not retried or bypassed.

This run made no site/runtime/DNS/mail/HTTPS/catalogue/panel changes, manual IndexNow sends or messages to third parties. Latest PROJECT_STATE.md was read first: the site has since expanded to 23 public URLs; older 11-URL snapshots are historical, not a current inventory. No new objective site fault was reproduced. Monitoring remains necessary for Google sitemap processing, Bing six-page inclusion and remaining agreed engines. This browser follow-up is not a Ferrari engine-job certification.


## Brave six separate results; Seznam homepage appears — 8 November 2026, 19:06–19:11 Lisbon

**New material progress:** the public Brave query for the domain showed the homepage and a separate Cavitação result, plus four category sitelinks. Sitelinks alone were not treated as individual index confirmation. A subsequent focused [products-path query](https://search.brave.com/search?q=site%3Alowcost-europa.eu%2Fproducts%2F&source=web) displayed **five separate category results**, each pointing at the exact canonical WWW URL. This confirms public search presence for the homepage and all five categories at the observation time. The [Seznam domain query](https://search.seznam.cz/?q=site%3Alowcost-europa.eu) now displays the canonical homepage, superseding the earlier receipt-only/unconfirmed state for that page. Its category inclusion remains unconfirmed; a focused products-path query displayed only the homepage.

| Engine | Latest evidence | Scope and limit |
| --- | --- | --- |
| Google | Six indexed-version confirmations at 18:50–18:56, authenticated API | Historical six-page baseline retained; sitemap recheck at 19:07 still pending |
| Brave | Public results at 19:10 | Homepage plus five separate category results; not an authenticated report or permanent guarantee |
| Seznam | Public result at 19:09 | Homepage only; categories unconfirmed |
| Bing | Authenticated six inspections at 19:06–19:09 | All Discovered but not crawled; sitemap Error / 0 discovered |
| Yandex | Authenticated Webmaster tools | Sitemap read-only/Add disabled; Searchable pages data may be delayed or unavailable |
| Yahoo | One public domain query | No matching domain link displayed; global absence not established |
| DuckDuckGo | Public query returned an unexpected-error page, 418.html | Index inclusion unknown; not evidence of removal |

Google's fresh Sitemaps:list response remains HTTP 200, isPending=true, errors=0, warnings=0 and unchanged lastSubmitted=00:35:17.963 UTC. No lastDownloaded/type/contents or successful-processing confirmation was returned. The six Google per-URL inspections were not repeated here.

Bing's IndexNow dashboard still displays zero alongside two momentary-service-error messages. That unreliable UI count does not invalidate earlier accepted HTTP 200 notifications. There is no new demonstrated IndexNow regression. Yandex Searchable pages says charts/export are temporarily unavailable and data may not update or may be delayed; All pages is disabled. Its Latest changes row says No changes to page indexing, which cannot establish zero indexed pages from a complete fresh report.

[Sanitized observations](international-search-followup-20261108-1911.json) record source type, check times, public queries, canonical result URLs and the remaining limits. An independent review agrees with the distinction between public presence and authenticated reporting, and found no new technical defect justifying a runtime change or submission. No sitemap/index request, restriction bypass or message to a third party was sent. No site/DNS/mail/HTTPS/catalogue/panel setting changed. Continue the same monitoring task; original sitemap/Bing completion conditions and the expanded engine scope are not yet satisfied. This evidence update is not a new Ferrari execution certification.


## Authenticated Google API readback — 8 November 2026, 18:43–18:56 Lisbon

The owner completed Google authentication. Official Google APIs Explorer then returned authenticated results using only the Search Console read-only scope. This supplies new direct engine evidence after the earlier Search Console web-session persistence blocker; it does not establish a permanent unattended API connection on the VPS.

**Sitemap still pending:** Sitemaps:list returned HTTP 200, isPending=true, warnings=0, errors=0 and lastSubmitted=2026-11-08T00:35:17.963Z for the existing canonical sitemap. No lastDownloaded, type or contents is returned. Google's [resource definition](https://developers.google.com/webmaster-tools/v1/sitemaps) says pending means not yet processed. Therefore zero errors/warnings in this response does not confirm successful processing or resolution of the earlier Couldn't fetch report. No resubmission occurred.

**Six indexed versions reconfirmed:** the official [URL Inspection method](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect) returned HTTP 200 and PASS / **Enviada e indexada** individually:

| Page | Last Google crawl (UTC) |
| --- | --- |
| Homepage | 2026-11-07 22:53:01 |
| Cavitação / RF / vacuum | 2026-11-07 22:55:00 |
| Hydrodermoabrasão / aqua facial | 2026-11-07 22:57:01 |
| Pressoterapia / vacuum / drenagem | 2026-11-07 22:59:02 |
| HIFU | 2026-11-07 22:59:02 |
| Diodo / laser / tatuagens | 2026-11-08 13:52:54 |

All six results report robots ALLOWED, INDEXING_ALLOWED, page fetch SUCCESSFUL, MOBILE crawler and Google canonical equal to user canonical and the exact requested WWW URL. These are indexed-version inspections, not Live URL tests or indexing requests. They reconfirm the six-page baseline from earlier today. [Sanitized per-URL results and sitemap response](google-search-console-20261108-1856.json) preserve check times and the relevant engine fields only. No credentials, tokens, account identifiers, raw headers, opaque inspection links or private data are committed.

**Other engines:** the latest authenticated Bing baseline remains six pages Discovered but not crawled and sitemap Error/0; homepage Live at 16:56 was indexable with zero SEO notices. At approximately 17:50 its XML Live diagnostic showed Failed to load insights again after one Re-try. Its IndexNow dashboard displayed zero together with two momentary-service-error messages. Neither display establishes a fresh origin fetch failure, zero accepted notifications or an IndexNow regression; the earlier read-only VPS evidence remains valid. Do not loop retries or re-submit. Public HTTPS sitemap/robots checks still passed without a reproduced origin fault.

Yandex's sitemap tool remains restricted to read-only in the latest authenticated observation. Brave's five category re-fetch receipts and Seznam's homepage receipt remain submission evidence only; Yahoo/DuckDuckGo inclusion is unconfirmed. Continue the **same** task for all seven agreed engines following the owner's latest instruction. Final closure requires the original successful Google/Bing sitemap processing and Bing six-page confirmations plus confirmed completion of the expanded engine scope. Site-side eligibility and IndexNow receipts cannot force an engine's inclusion decision.

This follow-up changes documentation only. No DNS/mail, HTTPS, catalogue, panel controls or runtime configuration was altered; no index request, sitemap re-submission or third-party message was sent. The interactive Google grant is not exported to the VPS. Browser observations and Actions→SSH alignment are not new Ferrari engine-job certifications.


## Five Brave category receipts; IndexNow stable — 8 November 2026, 17:00 Lisbon

- **New work completed:** each of the five existing category URLs was submitted once through Brave's official re-fetch form. Every submission displayed **Success / Thank you for your submission**. The homepage was not re-submitted. These are receipt confirmations, not category index-inclusion confirmations. Do not repeat them without a new technical reason.
- **IndexNow independently verified:** [read-only VPS check #42502446710](https://github.com/martaxi-boss/VPS/actions/runs/42502446710) compared two full snapshots against accepted state: 11 public / 11 accepted; both snapshots stable; accepted state unchanged by the check; three current differences (homepage, Cavitação and HIFU), zero removed. Accepted-state timestamp was 16:09:30 UTC. Sanitized existing timer events since 13:00 show HTTP 200 receipts for batches of 5, 4, 5 and 6 URLs. No manual endpoint request was sent. The earlier changed=4 is not a demonstrated instability or notification regression. Public observation timestamps/order can change with catalogue maintenance; exact historical content differences cannot be reconstructed from hashes alone.
- **Authenticated Bing recheck:** the homepage and all five categories remain **Discovered but not crawled**; sitemap remains **Error / 0 discovered**. Homepage Live URL at 16:56 again confirms **URL can be indexed by Bing / No SEO/GEO issues found**. No Bing resubmission or request-indexing action.
- **Authenticated Yandex recheck:** Sitemap files still explicitly states read-only mode; Add remains disabled. No submission or workaround.
- **Google evidence boundary:** after the owner restored authentication earlier today, a fresh homepage inspection confirmed **O URL está no Google / A página está indexada**, with successful smartphone Googlebot crawl dated 07/11/2026 22:53:01, indexing/crawl allowed and canonical WWW selected. The authenticated sitemap still could not be read, zero discovered. In this later session Google is signed out again and presents a CAPTCHA; no fresh sitemap result is inferred from that blocker.
- **No speculative site correction:** independent review and 22 anonymous public-page fetches found stable eligible content and valid sitemap transport. No new reproducible sitemap fault was identified. The site code, catalogue, DNS/mail, HTTPS and private panel were not changed. Initial diagnostic attempts failed on task-script access/journal permissions; the successful check preserved the existing private permissions. Temporary diagnostic script/workflow are removed; required state and rollback checkpoints are retained. Existing monitoring stays enabled because sitemap processing and Bing six-page inclusion are unresolved.


## Graceful reload deployed; Bing Live recovered — 8 November 2026, 13:42 UTC

Seven upstream connection refusals were correlated by second with controlled application stop/start events. [PR #225](https://github.com/martaxi-boss/lowcost-europa/pull/225) adds the missing Gunicorn HUP reload handler. Its test and audit checks passed. [Guarded production rollout #42486100692](https://github.com/martaxi-boss/VPS/actions/runs/42486100692) deployed `4f59453306aeebbc37849f9face098f8a2133c50`: **75/75 HTTPS requests returned 200** across homepage, robots and sitemap during an actual reload; the listening master stayed unchanged and old workers were replaced. Private panel/admin routes retained login redirects and noindex/private headers; private environment, operator data and Nginx checksums stayed unchanged. The app and IndexNow timer remained active. This removes a demonstrated update interruption mechanism; it does not establish the cause of the engines' sitemap errors.

**Authenticated Bing follow-up:** homepage Live URL at 13:42 again reports **URL can be indexed by Bing** and **No SEO/GEO issues found**, recovering from the 11:33 fetch failure. No causal claim is made from this timing. The homepage and all five category index inspections still report **Discovered but not crawled**; sitemap still **Error / 0 discovered**. No index request or sitemap resubmission was sent. Google currently redirects to its signed-out account chooser, so no fresh Google sitemap/index result is asserted; its earlier six confirmations remain historical evidence. Yandex's previously observed service-side read-only restriction is not reinterpreted as resolved.

Production checks are GitHub Actions→SSH evidence, not a new Ferrari engine-job certification. The existing monitoring task must remain active; the completion conditions are unmet. Required rollback checkpoints and IndexNow state are retained; only temporary task workflows are removed.


## Proven deployment interruption; graceful reload correction — 8 November 2026

[Readiness evidence #42477175567](https://github.com/martaxi-boss/VPS/actions/runs/42477175567) confirms that the live application unit exactly matches source, CanReload=no, and NRestarts=0. All seven Lowcost connection-refused errors correlate by second with controlled stop/start events between 01:24 and 02:43. These are demonstrated deployment interruptions, not evidence of a current crash loop and not proof that they caused the later sitemap reports.

The service now declares ExecReload using Gunicorn's HUP signal. For application-code updates with unchanged environment, runtime/dependencies and compatible schema, use `sudo systemctl reload lowcost-europa.service` after tests and the usual guarded checkout. Gunicorn keeps its listening master while replacing workers. Environment changes are not picked up by HUP and require a separately planned restart; this change does not make incompatible migrations or binary upgrades safe.

Production acceptance must verify the existing unit before replacement, preserve a private rollback, run systemd unit verification, daemon-reload and one real reload under concurrent HTTPS requests to home/robots/sitemap, require zero failed samples and an unchanged master PID, and recheck private routes and configuration checksums. Until that rollout passes, treat this as source-only. Engine sitemap processing and index inclusion remain unresolved unless their own reports confirm a change.

Further isolation: [TLS probe #42476901175](https://github.com/martaxi-boss/VPS/actions/runs/42476901175) passed TLS 1.2 and TLS 1.3 for home, robots and sitemap. The **actual negotiated HTTP version was 1.1** in every sample, even when HTTP/2 was requested. Earlier references to HTTP/2 flags must not be treated as proof of HTTP/2 support; HTTP/2 enablement was not made into a speculative indexing fix. [Default-port probe #42476988311](https://github.com/martaxi-boss/VPS/actions/runs/42476988311) shows identical indexing eligibility for canonical Host with and without explicit :443. The fresh Google settings page has no crawl-statistics data yet and reports no robots file in its aggregate view, while direct public robots requests work; that aggregate is not a demonstrated robots.txt transport fault.


## Fresh sitemap transport diagnosis and Bing Live regression — 8 November 2026, 11:34 Lisbon

**New authenticated observation:** Bing Live URL tested the sitemap at 11:31 and the homepage at 11:33; both now report an inability to fetch and no indexability. This is a regression from the earlier successful homepage Live check. The separate homepage index report still says Discovered but not crawled. The XML sitemap's absence from the page index is not itself an error or a page-indexing objective.

[Independent public probe #42476080980](https://github.com/martaxi-boss/VPS/actions/runs/42476080980) tested twelve combinations of plain/Google/Bing user-agent strings, requested HTTP modes and identity/gzip negotiation through normal public DNS and TLS. Every response was HTTP 200 with TLS validation 0, application/xml, identical 922-byte XML and eleven unique canonical WWW URLs. All XML parsed successfully. These are synthetic requests, not authenticated crawler fetches. The response did not advertise Content-Encoding, so this does not prove a compressed gzip payload; negotiated HTTP version was not recorded, so flags alone do not independently certify HTTP/2.

[Sanitized server correlation #42476188412](https://github.com/martaxi-boss/VPS/actions/runs/42476188412), repeated after the homepage result in [#42476326926](https://github.com/martaxi-boss/VPS/actions/runs/42476326926), found a source verified by reverse DNS under search.msn.com and forward resolution receiving /sitemap.xml with HTTP 200 and 922 response bytes at 11:31:27 UTC. It coincides with the Bing Live test. However, the configured shared combined access log has no requested-host field: it cannot independently prove exact vhost attribution or which internal Bing pipeline consumed the response. Claimed Google user agents in these samples were not DNS-verified. No raw logs, source IPs, proof values or private identities were published.

Google's authenticated sitemap detail still says it could not read the sitemap, last read 08/11/26, zero discovered. The inspected source paths, canonical host gate, robots route and privacy middleware did not reveal a reproduced sitemap fault. The user-agent compatibility and XML tests passed; no objective runtime correction was identified. The discrepancy is **unresolved**, not fixed, and neither the origin HTTP 200 nor the new Live failure establishes individual index inclusion or removal.

The VPS remained at the previously aligned revision with a clean tracked worktree and valid/active Nginx/application checks. This investigation changed no site code, DNS, email, HTTPS, catalogue, panel controls or IndexNow state, and sent no sitemap/indexing resubmissions or messages to support. Temporary diagnostic workflows are removed after recording/alignment. Continue the existing task without creating duplicate submissions or treating this as completed indexing.


## Yandex ownership verified; sitemap service read-only — 8 November 2026 (latest)

The owner completed the Yandex verification step. The authenticated **Manage access** page now shows **Owner**, verification method **File in root directory**, and verification date **08/11/2026**. This supersedes the pending owner-action statements in the preceding follow-up. The proof value and account identifier are intentionally omitted.

The authenticated [Sitemap files page](https://webmaster.yandex.com/site/https:www.lowcost-europa.eu:443/indexing/sitemap/) explicitly states that the tool is in **read-only mode** and that files cannot currently be added or submitted for recrawling while Yandex engineers restore the service. The **Add** button is disabled. The interface links to [Yandex's service notice](https://yandex.ru/company/news/09-10-2026-01); that article was not independently inspected, so only the directly observed Webmaster restriction is asserted.

No sitemap submission was attempted, no alternative API was used to bypass the restriction, and no repeated IndexNow request was sent. Ownership is verified; sitemap processing, crawl progress and index inclusion in Yandex remain unconfirmed. The existing public robots/sitemap and previously accepted shared IndexNow receipt are unchanged. Resume the normal sitemap tool when Yandex restores it; do not change the site, DNS or mail in response to this service-side blocker.

This is an authenticated engine observation, distinct from the previously observed public Brave result and public site queries. The prior Google/Bing sitemap errors are unresolved. Monitoring must remain enabled because the required completion conditions are not met.


## Authenticated follow-up and Yandex proof — 8 November 2026, 10:21 Lisbon

- **Brave public result:** a direct Brave `site:lowcost-europa.eu` query now displays the homepage, titled “Lowcost Europa | Professional beauty equipment”, linking to the apex URL. This is an observed public search result for the homepage only; no category inclusion or authenticated Brave index report is claimed.
- **Seznam:** its official direct add-URL form confirmed successful receipt of `https://www.lowcost-europa.eu/` after the owner-authorized CAPTCHA. This is submission acceptance, not indexing. A public site query still returned no results. No duplicate Seznam submission was sent.
- **Google authentication restored:** the domain property's authenticated sitemap report still shows “Não foi possível obter” / zero discovered. No sitemap or per-page resubmission. The earlier six individually confirmed Google pages remain the historical baseline, not fresh individual inspections.
- **Bing authenticated report:** sitemap still Error / zero discovered. Individual inspections in this follow-up showed the homepage and all five categories as Discovered but not crawled. The general explanatory text is not a newly demonstrated site-side fault.
- **Yandex:** the owner completed Google authorization and account creation. The canonical WWW property is added. Its ownership proof is privately provisioned on the site, but **the Yandex Verify button has not been pressed**: that button explicitly accepts the Webmaster User Agreement and is left for the owner. Ownership, sitemap submission and index inclusion remain unconfirmed.
- **Bounded change:** [PR #221](https://github.com/martaxi-boss/lowcost-europa/pull/221), deployed revision `ffbacda4c5c166e204a0bf2b8d621099480c8f7e`, adds only a narrowly matched public Yandex proof route in the existing Nginx vhost and updates the existing header-count test. Proof values, private configuration and legal identity are absent from Git history. No DNS/mail, TLS, Django application, catalogue or database change.
- **Validation:** 778 tests PASS in [CI #42470658629](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42470658629); source audit [#42470658648](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42470658648) PASS. [Guarded VPS rollout #42471054301](https://github.com/martaxi-boss/VPS/actions/runs/42471054301) PASS: exact HTTPS proof content, six public pages, apex redirect, private panel/admin headers, unchanged private configuration, active app/IndexNow/TLS timers and clean tracked source.
- **IndexNow current readback:** `INDEXNOW_DRY_RUN public=11 changed=0 removed=0`; accepted-state checksum unchanged. No endpoint submission was made. The previous HTTP 200 remains receipt evidence only.
- **Recovery evidence:** the active vhost is a symlink into the tracked project configuration. The first preflight stopped safely on that path difference. A subsequent immediate fetch encountered a proven graceful-reload delay (404 followed later by 200); an ordering defect in the task's rollback script was corrected after [baseline recovery #42471001806](https://github.com/martaxi-boss/VPS/actions/runs/42471001806) PASS. The final rollout waits for that bounded reload transition. Private rollback checkpoints and the required public proof remain; temporary transport keys and plaintext transfer material were removed.
- **Execution boundary:** this follow-up used the authenticated engine consoles and GitHub Actions→SSH. It is not a new Ferrari engine-job certification. Search-engine processing remains external; do not declare indexing complete or disable monitoring.




## Latest verified update — 8 November 2026, 00:46 Lisbon

**IndexNow now returns HTTP 200.** The live worker submitted all eleven public URLs, received acceptance and persisted the accepted fingerprints. Key verification is no longer pending. This replaces the earlier HTTP 202 observations; it still does not confirm individual search-engine index inclusion.

Bing's previous homepage notices were corrected in [PR #212](https://github.com/martaxi-boss/lowcost-europa/pull/212): a descriptive title in the existing five languages and localized category image alternatives. The real Bing Live URL test at 00:46 explicitly returned **URL can be indexed by Bing** and **No SEO/GEO issues found**. The index report still says Discovered but not crawled; no Bing index inclusion is claimed.

[Guarded rollout #42431236626](https://github.com/martaxi-boss/VPS/actions/runs/42431236626) PASS at application revision `f1c1a3a8d3e6336721a201301cd43a7a8ac50cd1`: all **9/9 homepage images** have alternatives, the descriptive localized title is live, canonical/index-follow/HTTPS remain correct, panel/admin still redirect privately to login, private environment and operator-file checksums unchanged, app and IndexNow timer active. No DNS/email, Nginx, certificate or database changes.

Validation passed: [full CI #42431063213](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42431063213), [security audit #42431063206](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42431063206) and [four-viewport source browser QA #42431063222](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42431063222). Nine local presentation checks passed; the broader local language test suite could not start without PostgreSQL, so the database-backed validation was supplied by CI rather than claimed as a local pass.

Google's six individually verified indexed URLs remain recorded below. The Google sitemap report was checked again and still reported Couldn't fetch / zero discovered; Bing's sitemap report still reported Error / zero discovered. Successful sitemap-report processing remains unresolved even though live fetches, authenticated Bing crawler access and IndexNow acceptance succeed. No additional sitemap or individual indexing requests were sent during this follow-up.

Earlier sections below retain the chronological evidence and are superseded by this latest update where states differ.

## Verified update — 8 November 2026, approximately 00:35–00:37 Lisbon

This update supersedes the earlier unconfirmed Google state. Each of the following URLs was inspected individually in the authenticated Google Search Console. Every inspection displayed **O URL está no Google** and **A página está indexada**, with HTTPS confirmed. This is actual Google index-inclusion confirmation for these six URLs, not merely successful submission.

| URL | Google confirmation |
| --- | --- |
| https://www.lowcost-europa.eu/ | Indexed |
| https://www.lowcost-europa.eu/products/cavitacao-rf-vacuum-corpo/ | Indexed |
| https://www.lowcost-europa.eu/products/hydrodermoabrasao-aqua-facial-multifuncoes/ | Indexed |
| https://www.lowcost-europa.eu/products/pressoterapia-vacuum-drenagem/ | Indexed |
| https://www.lowcost-europa.eu/products/hifu/ | Indexed |
| https://www.lowcost-europa.eu/products/diodo-laser-remocao-tatuagens-pigmentacao/ | Indexed |

These observations do not establish index inclusion for the five institutional sitemap pages or for any other engine.

Bing's homepage inspection advanced from Not discovered to **Discovered but not crawled**, discovery dated 8 November 2026. Its Live URL test at 00:35 now says **URL can be indexed by Bing**. Its robots.txt Tester fetched the current rules and returned **Allowed** for the canonical sitemap. These are positive discovery/access results, not confirmation of Bing index inclusion. The live homepage test also reports a short title and three missing-alt notices; those quality/accessibility notices do not change the test's explicit indexability result and were not treated as crawl blockers.

The Bing sitemap report still shows Error / zero discovered. Google's sitemap report still showed Couldn't fetch / zero discovered despite the six positive page inspections. The same valid sitemap was re-submitted to Google once in this recheck, and Google returned **Mapa do site enviado com êxito**. Successful processing of either sitemap report remains unconfirmed; the earlier per-page requests were not duplicated.

[Independent server recheck #42430294495](https://github.com/martaxi-boss/VPS/actions/runs/42430294495) **PASS**: Google and Quad9 public DNS resolvers return the expected addresses; existing mail records were rechecked by the same workflow; site, timer, HTTPS and private operator permissions remain healthy. Server logs now show a **verified Bing crawler** receiving `/sitemap.xml` with HTTP 200 and robots.txt with HTTP 200. Verification used reverse DNS under `.search.msn.com` and forward resolution back to the source IP; IPs, keys and private log details are not published. This is evidence of an actual Bing request reaching the server, while its sitemap-report error remains unresolved.

The IndexNow worker was run once more after the earlier verification interval. It again received **HTTP 202 for 11 URLs**, and accepted state remains pending. The proof file returns the correct contents with HTTP 200. No HTTP 200 IndexNow acceptance or per-participant index inclusion is claimed. Automatic hourly retries remain enabled.

No application, DNS, mail, catalog, certificate or Nginx changes were needed during this recheck. The runtime revision remained `280fca9dd5ea1b99b734f33df78b8fdd985731e0` before this documentation update. The report is aligned back to the VPS with documentation-only changes; temporary task workflow removed afterwards.

## Earlier initial-submission snapshot (00:22)

## Confirmed work

The Google-verified domain was imported into Bing Webmaster Tools after the owner explicitly approved read-only Search Console access. The canonical sitemap is `https://www.lowcost-europa.eu/sitemap.xml`. Bing's URL Submission table confirms **six submitted URLs**: the homepage and all five current category pages, with quota reduced from 100 to 94. Submission is not index inclusion.

The sitemap initially entered Processing, then Bing reported **The page is not accessible**, with zero discovered URLs. Bing's Live URL test of the XML also reported a fetch failure. After independent server checks it was re-submitted once; the final observed state returned to **Processing**, still zero discovered URLs. This item remains unresolved at the search engine; there is no confirmed successful Bing sitemap processing.

Brave's official re-fetch form returned **Success — Thank you for your submission** for the homepage. This is receipt of a re-fetch request, not confirmation that the page is in the Brave index.

## IndexNow implementation and live receipt

[PR #209](https://github.com/martaxi-boss/lowcost-europa/pull/209) deploys an hourly systemd timer and a management command, without schema changes. It uses the official shared endpoint `https://api.indexnow.org/indexnow`; participating engines include Bing, Yandex and Seznam. A generated key lives in private VPS configuration, and the exact-host proof file returns HTTP 200. The actual key and its file location are intentionally omitted from this report, source and test logs.

The worker fetches the canonical sitemap, checks each allowlisted public page for HTTP 200, an exact canonical and absence of noindex, and fingerprints the anonymous rendered HTML. Random CSRF masks are excluded from comparisons. It submits new/changed pages and previously public pages removed from the sitemap; private paths, search, click redirects, foreign hosts and query URLs cannot enter the submission set. A lock prevents concurrent runs, and failures preserve the previous accepted state.

The live endpoint received **11 public URLs** and returned **HTTP 202**, meaning key verification remains pending. Two initial receipts were recorded when enabling the timer. Only HTTP 200 advances accepted fingerprints; the hourly worker retries pending verification. Neither 200 nor 202 means index inclusion. The timer is active and enabled across restarts.

## Engine discovery observations

| Engine | Actual observation | Official route used | Index inclusion confirmed? |
| --- | --- | --- | --- |
| Bing | Homepage inspection: Not discovered; six URL submissions visible | Search Console import, sitemap and URL Submission | No |
| DuckDuckGo | `site:lowcost-europa.eu` returned No results found | Bing is a principal source for traditional links; public crawl allowed | No |
| Yahoo | No matching domain result visible in the site query; unrelated AI suggestions are not site discovery | Bing webmaster submission; Yahoo page identifies Powered by Bing | No |
| Brave | Homepage re-fetch submission succeeded; search status check encountered a human-verification challenge | Official Submit URL form | No |
| Yandex | Public search encountered a CAPTCHA identifying automated requests; no attempt to bypass it | Shared IndexNow notification received, verification pending | No |
| Seznam | Site query said no results; direct add-URL form requires a CAPTCHA and was not submitted | Shared IndexNow notification received, verification pending | No |

Absence from one `site:` query does not prove complete absence from an engine's index. CAPTCHA-limited observations remain unknown. Shared IndexNow receipt is not an individually confirmed crawl or indexing decision by every participant.

## Real tests and preservation evidence

- [Source CI #42428713424](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42428713424): PASS; branch CI #42428616102 records **754 Django tests**, including ten specific IndexNow tests. These cover private/foreign URL rejection, exact proof host/key, CSRF stability, content changes, deduplication, deletion notifications, dry run, 202 and failed-submission state preservation.
- [Security audit #42428713384](https://github.com/martaxi-boss/lowcost-europa/actions/runs/42428713384): PASS. The earlier audit found unsafe standard XML parsing; the implementation was corrected to use pinned `defusedxml==0.7.1`, and the audit passed.
- [Independent VPS certificate #42428884310](https://github.com/martaxi-boss/VPS/actions/runs/42428884310): PASS — deployed SHA `93c5dedcf0877eeff583b2863fe246d132c7225c`, private proof/environment preservation, active timer/service and clean tracked worktree.
- [Access/TLS diagnosis #42429109681](https://github.com/martaxi-boss/VPS/actions/runs/42429109681): PASS — root-domain and WWW A records, no unexpected AAAA, existing MX/SPF/DKIM/DMARC and Google verification TXT preserved on both authoritative servers and a public resolver. Direct origin TLS chain verifies successfully. Sitemap fetch with Bing's user agent returns HTTP 200.
- [External HTTP evidence](international-public-audit-20261108.json): **11/11 public sitemap pages** return HTTP 200 with exact WWW canonicals and no noindex; panel/admin redirect to login with noindex and private/no-store; health remains noindex/private. Three HTTP/apex redirects remain 301 to canonical HTTPS. Five synthetic bot user agents can fetch the homepage; these are compatibility tests, not authenticated engine crawls.
- Aggregate server logs contain successful sitemap/robots requests claiming Bing's user agent. These claims alone are not authenticated crawler identities and do not override Bing's report.

The first rollout #42428780643 activated the worker and received HTTP 202, but its final shell terminator caused exit 127 **after** activation. The independent certificate and subsequent access/TLS diagnosis passed. No DNS, mail, Nginx, certificate, catalog data or database schema was changed by this task. DNS preservation does not substitute for an end-to-end email delivery test.

## Operations and remaining work

The hourly timer continues notifying participants of genuine public content changes. Disable `lowcost-europa-indexnow.timer` to stop notifications; the previous application revision and environment backup remain available privately for recovery. No credentials or private legal identity were committed. Temporary task workflows are removed after the final alignment check; intentional private rollback material and required fingerprint state are retained.

Outstanding external confirmations: IndexNow key verification, successful Bing sitemap processing, actual discovery/index inclusion in each engine. Do not describe this report as completed indexing.

## Official references

- [Bing import and verification](https://www.bing.com/webmasters/help/add-and-verify-site-12184f8b)
- [IndexNow protocol](https://www.indexnow.org/documentation), [FAQ and endpoints](https://www.indexnow.org/faq), [participant registry](https://www.indexnow.org/searchengines.json)
- [DuckDuckGo sources](https://duckduckgo.com/duckduckgo-help-pages/results/sources)
- [Yahoo ranking and Bing](https://uk.help.yahoo.com/kb/SLN35619.html)
- [Brave official re-fetch route](https://search.brave.com/help/contact)
- [Yandex IndexNow reference](https://yandex.com/support/webmaster/en/indexnow/reference)
- [Seznam official add-URL form](https://search.seznam.cz/wt/pridej-stranku)
