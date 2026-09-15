# LAUNCH READINESS 001

## Scope

Temporary staging hostname and final pre-launch QA only. This phase does not authorize a permanent domain, public indexing, campaigns or GO LIVE.

- Authorized base: `ea390319bcf9d4b8023a24140828f049a7fba10a`.
- Branch: `builder/launch-readiness-001-duckdns`.
- Temporary staging hostname: `lowcost-europa.duckdns.org`.
- Staging IP: `165.22.114.67`.
- Existing technical hostname remains supported: `lowcost-europa.165-22-114-67.sslip.io`.

## DNS and HTTPS

DNS resolved `lowcost-europa.duckdns.org` to `165.22.114.67` before configuration.
A dedicated Let's Encrypt ECDSA certificate was issued for `lowcost-europa.duckdns.org`; it expires on 2026-12-14. OpenSSL hostname verification and chain verification both passed (`Verify return code: 0`). Real Chromium navigation also accepted TLS without bypass.

The existing sslip certificate was retained for the old hostname and still validates that hostname. Certificates from other projects were not modified or removed.

Certbot timer is enabled and active, and the DuckDNS renewal configuration exists. No Cloudflare DNS/proxy/CDN/WAF configuration was introduced.
## Nginx and Django staging configuration

`deploy/nginx/lowcost-europa.conf` now contains separate HTTPS virtual hosts for DuckDNS and sslip, with each hostname using a certificate valid for that hostname. Both HTTP virtual hosts redirect to HTTPS with 301. The active Nginx file is byte-for-byte identical to the versioned configuration.

Staging environment changes:

- `DJANGO_ALLOWED_HOSTS=lowcost-europa.165-22-114-67.sslip.io,lowcost-europa.duckdns.org`
- `DJANGO_CSRF_TRUSTED_ORIGINS=https://lowcost-europa.165-22-114-67.sslip.io,https://lowcost-europa.duckdns.org`
- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=` remains empty.
- `DJANGO_SECURE_HSTS_SECONDS=0` remains unchanged for staging.

The environment and previous Nginx configuration were backed up root-only before change under `/root/launch-readiness-001-backup-20260915T142028Z/`. No secret values are documented or versioned.

## Functional QA

On `https://lowcost-europa.duckdns.org`, homepage, live/ready health, Contacto, Como funciona, Afiliados, Privacidade, Termos, robots, sitemap, AliExpress callback and all five existing family pages returned HTTP 200.

`http://lowcost-europa.duckdns.org/` returns 301 to HTTPS without a redirect loop. The old sslip hostname still returns 200 over HTTPS and still redirects HTTP to its own HTTPS hostname.

The AliExpress callback route returned HTTP 200 on DuckDNS. No external AliExpress account callback setting was changed and no credential was displayed.
## Noindex and security headers

DuckDNS remains fail-closed for search engines:

- HTML meta robots: `noindex, nofollow`.
- `X-Robots-Tag: noindex, nofollow`.
- `robots.txt`: `User-agent: *` plus `Disallow: /`.
- `PUBLIC_SITE_URL` remains empty, so no public canonical URL is created for the temporary hostname.

Observed HTTPS headers include `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin` and `X-Robots-Tag: noindex, nofollow`. HSTS is intentionally not increased in this phase; staging remains at `DJANGO_SECURE_HSTS_SECONDS=0`.

## Automated validation

Final branch validation passed:

- `python manage.py check`: PASS.
- `makemigrations --check --dry-run`: no changes detected.
- `migrate --plan`: no planned operations.
- Full test suite: 201/201 PASS.
- Ruff: PASS.
- `git diff --check`: PASS.

No migration, schema, catalog model or AliExpress integration contract change was introduced.
## Real browser QA

Chromium QA was executed against the real DuckDNS HTTPS hostname with normal TLS validation.

Mobile viewport 390x844 covered homepage, open mobile menu, HIFU 7D, Cavitation and Contacto. Desktop viewport 1440x900 covered homepage, product cards and HIFU 7D.

Across all measured pages:

- horizontal overflow: ZERO;
- JavaScript page errors: ZERO;
- robots meta: `noindex, nofollow`;
- one H1 per page and no heading-level skips in measured pages;
- mobile menu target: 80x48 px;
- minimum measured CTA height: 48 px;
- desktop navigation visible without opening a menu;
- raw AliExpress affiliate href exposure in rendered links: ZERO;
- footer present.

Final evidence is stored in `docs/qa/launch-readiness-001/`, including eight screenshots and `qa-results.json`. A final independent revalidation against the live DuckDNS HTTPS hostname reproduced zero horizontal overflow, zero JavaScript errors, visible desktop navigation, 48 px mobile targets, zero raw affiliate href exposure and zero browser requests to `/go/`.

The factual second HIFU 7D source image remains 123x123. Status: **OPEN / NON-BLOCKING**. It was not replaced or masked.
## OfferClick audit during staging QA

Baseline before DuckDNS QA was 5 ProductFamilies / 6 Offers / 9 OfferObservations / 5 OfferClicks.

During the public-hostname QA window, OfferClicks first increased from 5 to 23. Execution stopped for origin audit as required. Those 18 `/go/` requests formed three automated-looking batches: three distinct remote sources each requested all six Offer routes exactly once, with the same Windows Chrome 124 User-Agent and no referer.

The Builder Chromium QA identified itself as Linux `HeadlessChrome/140.0.7339.16`; its script only navigated to storefront/institutional pages and did not request `/go/`. The initial 18 records are therefore classified as external automated staging traffic, not Builder QA clicks.

A later pre-commit snapshot found five more external mobile-browser `/go/` requests, bringing the audited total to 28. Final revalidation found six further external mobile-browser requests, bringing the audited snapshot to 34. These later requests used Android Chrome variants, some with DuckDNS pages as referer, and were distinct from the Builder HeadlessChrome QA. Source IP values are intentionally not retained in project documentation.

No OfferClick records were deleted or modified. The counter may continue to increase while the publicly reachable staging hostname receives external traffic. Audited live state at the final validation snapshot is:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 9
- OfferClicks = 34

These raw staging events are not unique users, buyers, purchases, conversions or commissions.
## Performance and resources

A final simple HTTPS sample on DuckDNS measured approximately 0.061 s total for the homepage, with about 0.036 s TLS application-connect time, about 0.061 s TTFB and 15,707 bytes of HTML. The storefront CSS returned 200 in about 0.039 s and was 14,044 bytes. No load test was performed.

Resource snapshot after configuration:

- RAM: 961 MiB total, 415 MiB available;
- swap: 4095 MiB total, 422 MiB used;
- root filesystem: 24 GiB total, 16 GiB used, 7.5 GiB available (68%).

No Droplet upgrade or heavy stack was added.

## Open blockers / launch status

- DuckDNS is staging only; it is not the permanent public domain.
- Public indexing remains disabled and GO LIVE is not authorized.
- Operator legal/public-launch readiness is not resolved by this phase.
- Off-server R2/restic recovery remains outside this phase and owner-gated.
- GitHub main protection remains an external account/admin capability issue from the operational closeout.
- AliExpress external callback registration was not changed; only the DuckDNS route itself was technically validated.
- HIFU 123x123 source image remains OPEN / NON-BLOCKING.

**PUBLIC LAUNCH = NO.** Supervisor audit is required before any later decision.