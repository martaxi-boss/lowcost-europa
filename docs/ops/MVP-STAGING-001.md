# MVP STAGING 001

Date: 2026-09-14
Deployed main SHA: `f4533a21628b0ae5f328fd980b7d5c8141206598`
Host: `lowcost-europa.165-22-114-67.sslip.io`

## Architecture

HTTPS Nginx -> Gunicorn -> Django production settings -> PostgreSQL.
Gunicorn service: `lowcost-europa.service`.
Gunicorn bind: `127.0.0.1:8001` with 2 workers.
Static root: `/srv/lowcost-europa/staticfiles` served directly by Nginx.
Secrets live outside Git in a restricted environment file.
HSTS remains `0`; preload and includeSubDomains remain disabled.

## Database migration

Pre-migration DB state was 1 ProductFamily / 3 Offers / 6 OfferObservations / 0 OfferClicks.
Backup `pre-catalog-0004-20260914T220545Z.dump` was created in custom format with mode 600, size 43,500 bytes, SHA256 `d80315ae7129f692feec69b434a5f44070235cb6086ff38755fc9f17f5053727`.
The migration plan contained only `catalog.0004_offerclick` and it applied successfully.
Post-migration state remained 1 ProductFamily / 3 Offers / 6 OfferObservations / 0 OfferClicks before redirect validation.
## Staging validation

HTTPS certificate validation succeeds and the Let's Encrypt certificate is valid through 2026-12-11.
Liveness and readiness both return HTTP 200; readiness queries PostgreSQL.
Homepage and `/products/maquinas-hifu-7d/` return HTTP 200 with real catalog data.
The primary remains external product `1005012522304882`.
SEARCH_ONLY wording, source-sales wording, and affiliate disclosure remain conservative.
Storefront HTML exposes internal `/go/<id>/` links and does not expose affiliate URLs directly.

Exactly one controlled request was sent to the primary `/go/` endpoint without following the redirect.
It returned HTTP 302 to host `s.click.aliexpress.com` and created exactly one OfferClick.
That row is a **STAGING VALIDATION CLICK**, not a real user click.
OfferClick contains only `id`, `offer_id`, and `clicked_at`.

## Nginx and callback

The existing `/aliexpress/callback` PHP-FPM location and callback file were preserved.
The existing Certbot certificate configuration was preserved.
Nginx serves `/static/` directly and proxies all other Django traffic to local Gunicorn.
The staging HTTPS server emits `X-Robots-Tag: noindex, nofollow`.
## Rollback

The pre-change Nginx config is retained as `lowcost-europa-temp.pre-mvp-staging-001-20260914T220912Z`.
Rollback is: restore that config, run `nginx -t`, reload Nginx, and stop/disable `lowcost-europa.service` if required.
Do not remove the certificate or callback PHP file during rollback.
The pre-0004 PostgreSQL dump is retained separately from the repository.

## Limits

This host is technical staging, not a public MVP launch.
No external analytics, conversion tracking, revenue reconciliation, scoring, ranking, scheduler, second ProductFamily, or LE-013 work was introduced.
The only click in the table is the controlled staging validation event.
