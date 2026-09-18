# ALIEXPRESS API SAFETY 001

Status: implemented on `builder/aliexpress-api-safety-001`; awaiting Supervisor audit.
Base: `99c0cc0d3e4392919793eada4dbfc6a0be99dabd`.

## Objective

Protect AliExpress quota, persisted last-known-good data and the small MVP Droplet with one central, bounded external-call policy.
The storefront remains database-backed: normal visitor requests do not call AliExpress.

## Central architecture

All external AliExpress operations pass through `apps/integrations/aliexpress/client.py`.
Retry, cadence and concurrency policy is not duplicated in discovery, persistence, cohort services or commands.
Discovery remains bounded at `DEFAULT_LIMIT=10`, `MAX_LIMIT=25`, with no unbounded auto-pagination.

## Concurrency and cadence

MVP external-call concurrency is one operation at a time through a local `flock`.
The lock is held for the whole logical `_call`, including automatic retries.
A shared cadence file records the last HTTP-attempt start and enforces `ALIEXPRESS_MIN_INTERVAL_SECONDS`, default 1.0 second.
The same cadence applies to retries.

## Runtime-state hardening

The original `/tmp` runtime paths were superseded by GLOBAL ALIEXPRESS RUNTIME STATE 001 after a `PrivateTmp=true` audit proved that separate systemd units and manual commands could see different inodes. Current default state paths are:

- `/run/lowcost-europa/aliexpress.lock`
- `/run/lowcost-europa/aliexpress.last-start`

`/run/lowcost-europa` is provisioned by the versioned tmpfiles policy with mode `0750` and service-user ownership. State files are opened through the existing secure helper using `O_NOFOLLOW` where supported, `O_CLOEXEC`, regular-file validation, owner validation and mode `0600`.
A malicious symlink or state file owned by another local user is rejected before upstream access. `PrivateTmp=true` remains enabled; moving only the global coordination state to `/run` preserves sandboxing while making the lock/cadence shared between Django, maintenance and manual management commands.
`flock` is kernel/file-descriptor based, so the lock is released automatically when a process exits or crashes; no fragile PID-file lock is used.

## Retry matrix

Automatic retry is limited to HTTP 429, HTTP 500/502/503/504, `URLError` and `TimeoutError`.
HTTP 400/401/403/404 and other ordinary 4xx fail without automatic retry.
Authentication payload errors and invalid JSON/normalization errors fail fast.
Default `ALIEXPRESS_MAX_RETRIES=2`, therefore at most three HTTP attempts per logical external operation.

Each retry rebuilds timestamp, parameters, HMAC signature and request. A signed request from an older attempt is not reused.

## Retry-After, backoff and jitter

HTTP 429 honors a valid `Retry-After` value in seconds or HTTP-date form.
The delay is capped by `ALIEXPRESS_MAX_RETRY_AFTER_SECONDS`, default 60 seconds.
Without valid Retry-After, exponential backoff uses `base * 2^(retry_number - 1)`, capped by `ALIEXPRESS_BACKOFF_MAX_SECONDS`.
Defaults are base 1.0 second and maximum 30.0 seconds.
A random jitter in `[0, ALIEXPRESS_JITTER_MAX_SECONDS]` is added to exponential backoff; default jitter maximum is 0.5 second.
Time, sleep and jitter sources are injectable so automated tests never need real retry waits.

## Rate-limit circuit breaker

`ALIEXPRESS_MAX_CONSECUTIVE_429` defaults to 3.
At that threshold, or when the retry budget is exhausted by 429 responses, the client raises `AliExpressRateLimitError`.
This is a rate-limit circuit breaker / abort, not a persistent temporal cooldown.
No cross-process cooldown window is claimed.

`AliExpressRateLimitError` is explicitly re-raised by multi-product discovery and cohort-observation loops.
A rate-limit abort therefore terminates the whole batch and no later product is attempted.
Normal per-product `AliExpressError` failures may still be recorded and skipped where the existing workflow permits it.

## Configuration

Operational fields added to `.env.example`:

- `ALIEXPRESS_MIN_INTERVAL_SECONDS=1.0`
- `ALIEXPRESS_MAX_RETRIES=2`
- `ALIEXPRESS_BACKOFF_BASE_SECONDS=1.0`
- `ALIEXPRESS_BACKOFF_MAX_SECONDS=30.0`
- `ALIEXPRESS_JITTER_MAX_SECONDS=0.5`
- `ALIEXPRESS_MAX_RETRY_AFTER_SECONDS=60`
- `ALIEXPRESS_MAX_CONSECUTIVE_429=3`
- `ALIEXPRESS_LOCK_TIMEOUT_SECONDS=15`

`ALIEXPRESS_TIMEOUT_SECONDS=10` remains supported.
`AliExpressConfig.from_env()` rejects invalid numeric values, non-positive timeout/lock timeout, unreasonable retry counts, negative intervals/jitter/backoff, invalid backoff ordering and consecutive-429 values outside the accepted range.

No secret value is versioned.

## Safe metrics

The client records per execution: logical operations, HTTP attempts, successful calls, retries, 429 responses, 5xx responses, transport failures, rate-limit abort, total duration and lock wait.
Management commands print these safe counters without request bodies, signatures, tracking IDs, affiliate URLs, APP_KEY or APP_SECRET values.

## Last-known-good preservation

A failed external refresh never replaces persisted price, image, sales, evaluation, commission, logistics, affiliate URL or availability with null values merely because transport/API failed.
`import_aliexpress_product()` performs network work before its database transaction and does not create a partial observation when the external call fails.
A dedicated test proves an existing Offer and its last observation remain unchanged after refresh failure.

## Existing Offer detail-only refresh

`apps.catalog.services.existing_offer_refresh.observe_existing_offer_detail()` is the safe path for an existing Offer when only a current detail snapshot is authorized.
It performs exactly one logical `get_product_detail()` call, validates the returned product ID against `Offer.external_product_id`, and never generates an affiliate link.
It does not change Offer identity, family, primary, active, title, image, product URL or affiliate URL.
Only after a valid exact-ID response does it open `transaction.atomic()` and create one factual `OfferObservation`.
A detail failure or ID mismatch creates zero observations and leaves the Offer intact.

## Storefront isolation

Home, family detail, institutional pages and `/go/<offer>/` read persisted PostgreSQL data only.
The public request path does not instantiate `AliExpressClient`.
`/go/` records a minimal OfferClick and redirects to the affiliate URL already stored on the Offer; it never refreshes AliExpress data.

## Test gate

The final pre-live gate passed on the branch code:

- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: no changes
- `migrate --plan`: no planned operations
- full project suite: 224/224 PASS
- Ruff: PASS
- `git diff --check`: PASS

Specific tests cover Retry-After, exponential backoff, jitter, repeated-429 abort, bounded 5xx/transport/timeout retries, non-retry 4xx, auth/invalid-payload fail-fast, lock timeout, cross-client serialization, minimum interval, retry re-signing, secret redaction, secure runtime-state symlink rejection, last-known-good, storefront zero-API and batch abort propagation.

The explicit batch-abort tests prove that if product 1 raises `AliExpressRateLimitError`, product 2 is not passed to persistence in either discovery or cohort observation.

## Live validation — Offers 55 and 56

After the complete mock/test gate passed, exactly two authorized logical detail operations were executed, in order 55 then 56, using the detail-only existing-Offer refresh service.
No search, category, discovery, affiliate-link generation or manual retry was performed.

Offer 55 / `1005012991431121`: SUCCESS, exact product ID, one new OfferObservation (id 67).
Offer 56 / `1005012839981986`: SUCCESS, exact product ID, one new OfferObservation (id 68).

Live execution counters:

- logical operations: 2
- HTTP attempts: 2
- retries: 0
- HTTP 429: 0
- HTTP 5xx: 0
- transport failures: 0
- rate-limit abort: NO
- aggregate duration: 1874 ms
- aggregate lock wait: 0 ms

Both current detail responses retained the prior observed price values for these Offers: Offer 55 EUR 969.45 and Offer 56 EUR 930.69. Detail delivery remained unavailable (`NULL`) for both.
No claim of European warehouse, guaranteed delivery, conversion or purchase is inferred.

## Database / tracking result

Phase baseline was 5 ProductFamilies / 6 Offers / 13 OfferObservations / 34 OfferClicks.
Immediately before the authorized live detail calls, OfferClicks had independently increased to 35 due to an external `/go/54/` request recorded by Nginx; the Builder did not call `/go/`.
After live validation the database snapshot was 5 ProductFamilies / 6 Offers / 15 OfferObservations / 35 OfferClicks.
No Offer, ProductFamily or OfferClick was created by the AliExpress detail validation.

## API payload rate-limit mapping

No project evidence currently establishes a specific AliExpress `error_response` code/sub-code that means rate limiting while HTTP status is 200.
That mapping therefore remains UNKNOWN in this phase; only confirmed HTTP 429 is treated as rate limiting.
No undocumented code was invented.

## Scope / staging invariants

No Redis, Celery, Docker, queue, extra Droplet or external observability service was introduced.
No schema migration was created.
DuckDNS staging, sslip compatibility, certificates and DNS were not changed.
Noindex/nofollow and `robots.txt: Disallow: /` remain the staging policy.
PUBLIC LAUNCH remains unauthorized.

Temporary test/live workspaces and debug scripts are removed at phase close; the secure lock/cadence state files are architecture runtime state and are not treated as disposable browser/test cache.
