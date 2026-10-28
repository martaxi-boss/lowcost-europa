# AliExpress integration

## Purpose

`apps.integrations.aliexpress` isolates all communication with the AliExpress Open Platform. Business code should use `AliExpressClient` rather than implement signing, HTTP calls or raw-response parsing itself.

## Configuration

Required environment variables:

- `ALIEXPRESS_APP_KEY`
- `ALIEXPRESS_APP_SECRET`
- `ALIEXPRESS_TRACKING_ID`
- `ALIEXPRESS_GATEWAY` (default/example: `https://api-sg.aliexpress.com/sync`)

Optional operational variables:

- `ALIEXPRESS_TIMEOUT_SECONDS` (default `10`)
- `ALIEXPRESS_MAX_RETRIES` (default `2`)

Never commit real secrets. `.env.example` contains placeholders only.

## Capabilities

The client supports category retrieval, product search, product detail lookup and affiliate-link generation. Search supports destination country, target currency and pagination. Portugal (`PT`) and EUR are the initial defaults.



### Destination-country argument in official affiliate calls

The AliExpress Open Platform defines different parameter names for the two
official affiliate methods. `aliexpress.affiliate.product.query` accepts
`ship_to_country=PT`, while `aliexpress.affiliate.productdetail.get` accepts
`country=PT`. The client uses each method's documented key, with EUR as
the target currency. See the provider's product-query API 45803 and
product-detail API 48595.

Neither endpoint provides an authoritative `ship_from_country` selection
parameter. The fixed permitted origin countries **PL, CZ, FR, ES, DE** remain
a separate, manual Owner protocol attestation, not an inferred property of
the delivery destination, keywords, seller address or delivery estimate.

## Signing and HTTP

Requests use HMAC-SHA256 over canonicalized sorted parameters, matching the previously validated project behavior for the AliExpress `/sync` gateway. Network calls use the Python standard library, explicit timeouts and bounded retries for transient network failures and HTTP 429/5xx responses.

Authentication, deterministic API errors and invalid responses are not retried blindly.

## Normalization

Raw responses are converted into lightweight dataclasses. Only fields supported by the response are populated. Missing optional values remain `None`; sales, commission, logistics and warehouse data are never invented.

`evaluate_rate` is normalized as `evaluation_rate_percent`. It is a percentage from the source, not a 0–5 star rating. For example, `96.5%` becomes `Decimal("96.5")`, meaning 96.5 percent. A future genuine star-rating field would be represented separately.

For logistics, `ship_to_days_raw` preserves the source text when `ship_to_days` (or an equivalent supported field) is present. `delivery_days` is populated only when a day count can be extracted safely and deterministically; otherwise it remains `None`. The commercial `<= 5 days` rule is intentionally not applied in this integration layer.

Products and categories require valid identifiers. Responses without a required `product_id`/equivalent or `category_id`/equivalent raise `AliExpressResponseError`; fictitious IDs such as `"None"` are never created.

## Errors and logging

Integration-specific exceptions distinguish configuration, authentication, transport, API and response failures. Logging records operation/retry information without App Secret, signatures, tokens or credentials.

## Tests

Run the full project suite:

```bash
python manage.py test
ruff check .
```

Automated tests use mocks and synthetic responses and require no live AliExpress credentials.

## Live smoke test

On an authorized environment with credentials already stored securely:

```bash
python manage.py aliexpress_smoke_test --keyword HIFU --country PT --currency EUR
```

The command checks configuration, categories, search, product detail and affiliate-link generation when a source URL is available. It reports only safe structural information such as counts, whether logistics/evaluation data are present, and interpreted `delivery_days` when available. It does not dump raw JSON, URLs, signatures, credentials or secrets, and it does not persist results.

## Scope boundaries

LE-002 does not add commercial database models, discovery, scoring, public UI, catalog mirroring, background workers, Redis, Celery or deployment infrastructure.

## MVP API safety policy

ALIEXPRESS API SAFETY 001 centralizes operational protection in `AliExpressClient`.
The storefront is deliberately isolated from the external API: normal public requests read PostgreSQL only, and `/go/<offer>/` redirects using the already persisted affiliate URL.

External-call concurrency is one operation at a time through global `flock`.
The lock is held across the whole logical operation, including automatic retries.
A shared cadence state enforces `ALIEXPRESS_MIN_INTERVAL_SECONDS` (default 1.0 second) between HTTP-attempt starts, including retries.
The default runtime files are `/run/lowcost-europa/aliexpress.lock` and `/run/lowcost-europa/aliexpress.last-start`. The shared `/run/lowcost-europa` directory is provisioned by `deploy/tmpfiles.d/lowcost-europa.conf` as `0750`, owned by `le001_1789265592:le001_1789265592`; state files retain secure no-follow opening, regular-file/owner validation and mode `0600`.
`PrivateTmp=true` remains enabled on the Django and catalog-maintenance services. Because the coordination state lives under `/run`, Django, maintenance and direct management commands use the same lock/cadence state rather than isolated `/tmp` copies.
Kernel `flock` release on file-descriptor/process exit provides crash safety without PID files.

Retries are allowed only for HTTP 429, HTTP 500/502/503/504, `URLError` and `TimeoutError`.
HTTP 400/401/403/404 and other ordinary 4xx are not automatically retried; authentication and invalid payload/normalization failures fail fast.
Each retry rebuilds timestamp, signature and request.

Operational defaults:

- `ALIEXPRESS_TIMEOUT_SECONDS=10`
- `ALIEXPRESS_MAX_RETRIES=2`
- `ALIEXPRESS_MIN_INTERVAL_SECONDS=1.0`
- `ALIEXPRESS_BACKOFF_BASE_SECONDS=1.0`
- `ALIEXPRESS_BACKOFF_MAX_SECONDS=30.0`
- `ALIEXPRESS_JITTER_MAX_SECONDS=0.5`
- `ALIEXPRESS_MAX_RETRY_AFTER_SECONDS=60`
- `ALIEXPRESS_MAX_CONSECUTIVE_429=3`
- `ALIEXPRESS_LOCK_TIMEOUT_SECONDS=15`

HTTP 429 honors valid Retry-After seconds or HTTP-date values, capped at the configured maximum. Without valid Retry-After, exponential backoff plus bounded jitter is used.
Three consecutive 429 responses by default trigger `AliExpressRateLimitError`, a rate-limit circuit-breaker abort rather than a persistent cooldown.
Multi-product discovery and cohort observation explicitly propagate this exception so the entire batch stops; they do not continue to the next product.

`observe_existing_offer_detail()` provides an exact-ID, detail-only refresh for an already persisted Offer. It never generates an affiliate link or mutates Offer identity/family/primary/active/title/image/product URL/affiliate URL, and creates one OfferObservation only after a valid response.
Failures preserve last-known-good data and create no empty observation.

Management commands report safe logical-operation/HTTP-attempt/retry/429/5xx/transport/rate-limit counters. They do not log signed requests, APP_KEY, APP_SECRET, tracking-ID values or affiliate URLs.
See `docs/integrations/ALIEXPRESS-API-SAFETY-001.md` for the implementation and validation record.
