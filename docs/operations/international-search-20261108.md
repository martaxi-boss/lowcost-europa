# International search discovery — 8 November 2026


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
