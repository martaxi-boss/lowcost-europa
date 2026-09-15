# MVP PRELAUNCH 002 — STAGING DEPLOY VALIDATION

## Deployment

- Target main SHA: `a3b8e5400c48ed70c3b83e1ca69c924226fb6dfb`
- Deploy workspace before: `0a0c79be959665b75b4911b1ae5f25ed8424eb7a`
- Deploy workspace after: `a3b8e5400c48ed70c3b83e1ca69c924226fb6dfb`
- Deploy worktree was clean before sync.
- `migrate --plan`: no planned migration operations.
- Official requirements were already satisfied in the existing venv.
- `collectstatic`: 1 copied, 127 unmodified.
- Only `lowcost-europa.service` was restarted; it returned `active`.
- PostgreSQL, PHP callback and Nginx configuration were not changed.

## Indexing environment

Staging explicitly uses:

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=`

No final public domain was configured. The staging hostname remains non-public/noindex.

## Backup health

Latest daily backup checked before deploy:

- `lowcost-europa-20260915T031500Z.dump`
- size 94,565 bytes
- dump mode 600
- checksum sidecar mode 600
- `sha256sum -c`: OK
- `pg_restore --list`: PASS
## Health and institutional pages

HTTPS results:

- `/health/live/` = 200
- `/health/ready/` = 200
- `/` = 200
- `/aliexpress/callback` = 200
- `/como-funciona/` = 200
- `/afiliados/` = 200
- `/privacidade/` = 200
- `/termos/` = 200

Footer links correctly target all four institutional pages.

`/termos/` still visibly contains:

- `PRE-LAUNCH / NOT PUBLIC READY`
- `PENDING OWNER INPUT`
- `NIF/VAT`
- official email remains pending owner input

Affiliate disclosure remains conservative: Lowcost Europa may receive commission; payment happens at the seller; final price/conditions are defined by the seller.

Privacy text describes OfferClick as `offer + clicked_at` only and distinguishes application tracking from technical server/security logs. It does not claim that IP is never processed by infrastructure.

## Cookies

Real GET responses, without `/go/`, were inspected for:

- homepage
- HIFU 7D detail
- Como funciona
- Afiliados
- Privacidade
- Termos

`Set-Cookie` present = NO for every audited page. This is a factual observation, not an absolute "cookie-free" claim.
## SEO fail-closed validation

Staging real responses confirmed:

- homepage meta robots = `noindex, nofollow`
- ProductFamily detail meta robots = `noindex, nofollow`
- institutional page meta robots = `noindex, nofollow`
- canonical = absent on all audited pages
- Nginx `X-Robots-Tag` = `noindex, nofollow`

`/robots.txt` = 200 and contains:

```text
User-agent: *
Disallow: /
```

It does not contain `Allow: /` and does not announce a sitemap while `PUBLIC_SITE_URL` is empty.

`/sitemap.xml` = 200 with `Content-Type: application/xml`. It contains 10 URLs: homepage, four institutional pages and exactly the five non-retired ProductFamily pages. The staging hostname in sitemap entries is not treated as canonical.

## Catalog smoke

All current family detail pages returned 200:

- `maquinas-hifu-7d`
- `maquinas-hifu-22d-max`
- `maquinas-cavitation-rf-body-shaping`
- `maquinas-diode-laser-hair-removal`
- `maquinas-hydro-dermabrasion-aqua-peel`

Homepage renders 5 ProductFamily cards, 5 internal `/go/` CTAs, factual images/prices and five conservative `Estimativa indicada pela pesquisa: 5 dias` messages. Direct AliExpress affiliate destinations are absent from homepage and all five detail HTML responses. No `/go/` endpoint was requested by the Builder.
## Visual QA

Real Chromium/Playwright validation used:

- desktop viewport 1440x900
- mobile viewport 390x844

Audited pages: homepage, Como funciona, Afiliados, Privacidade and Termos.

All 10 page/viewport combinations returned 200 with no horizontal overflow. Headings and footer links were visible and readable. Terms visibly showed both `PRE-LAUNCH / NOT PUBLIC READY` and `PENDING OWNER INPUT` on desktop and mobile. No commercial CTA was clicked.

## Log review

Post-deploy application logs showed no traceback, application 500, proxy failure, template error or relevant static 404. Gunicorn worker SIGTERM entries correspond to the controlled service restart.

Nginx error-log matches inspected were unrelated internet scanning against the default host, not Lowcost Europa staging application failures.

## OfferClick audit and DB state

Initial PRELAUNCH 002 preflight had found 4 raw OfferClick rows and correctly stopped. The Supervisor audited those events read-only; during that audit one additional raw click appeared, establishing the resumed official baseline at 5.

The five rows are preserved. No delete or update was performed. They are raw staging click records and must not be interpreted as five people, customers, purchases, conversions or commissions.

- click baseline before resume = 5
- click final count = 5
- new click caused by Builder = 0
- OfferClick deletions = 0
- OfferClick updates = 0

DB before resume and after validation:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 9
- OfferClicks = 5

Net catalog writes by this task = ZERO.

## Remaining public-launch blockers

- Legal/operator identity: operator name/entity, NIF/VAT where applicable, publishable legal address, official contact email and final legal terms remain PENDING OWNER INPUT.
- Off-server backup is still not implemented.
- HIFU Offer `1005013116584854` still has a 123x123 source image; this remains a pre-launch data-quality finding.
- Final public domain is not configured.
- Public MVP launch remains NOT authorized.
