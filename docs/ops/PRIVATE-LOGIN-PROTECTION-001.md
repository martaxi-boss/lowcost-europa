# Private Login Protection 001

## Scope

This control protects authentication POST attempts on:

- `/painel/entrar/`
- `/admin/login/`

It does not change Owner credentials, Django authentication semantics, CSRF, session cookies, staff/admin authorization, SSH, Nginx, firewall rules, public indexing or storefront behavior.

## Policy

The application allows up to **5 authentication POST attempts per normalized source within 5 minutes**.

After the fifth unsuccessful authentication attempt, subsequent authentication POSTs from that source are temporarily throttled for **5 minutes**. A throttled request receives:

- HTTP `429 Too Many Requests`;
- a `Retry-After` value derived from the remaining throttle period;
- a generic message that does not disclose account existence, password correctness, remaining attempts, keys or implementation details.

GET login pages remain accessible.

A successful staff authentication clears the current temporary source state. State also expires naturally. No account or username is permanently locked.

## Source attribution

The production topology is:

`Internet → Nginx → loopback Gunicorn/Django`

Gunicorn listens only on `127.0.0.1:8001`. Nginx overwrites `X-Real-IP` with its observed `$remote_addr` and forwards requests to loopback.

The limiter therefore:

1. uses `REMOTE_ADDR` directly for non-loopback requests;
2. only trusts `X-Real-IP` when Django's `REMOTE_ADDR` is loopback;
3. ignores `X-Forwarded-For` for rate-limit identity;
4. validates and normalizes IPv4/IPv6 with Python's IP-address parser;
5. falls back to a single `unknown` source identifier for malformed/missing direct addresses.

The normalized address is converted to a SHA-256 source token before limiter state or limiter logs use it. Submitted usernames are not part of the limiter key.

## Shared state

Two Gunicorn workers currently serve the application. Per-process Python memory and Django's default local-memory cache are therefore not suitable for this control.

The limiter uses short-lived JSON state in the existing shared runtime directory:

`/run/lowcost-europa/`

The directory already exists outside systemd `PrivateTmp`, is owned by the application service account and is shared by the Gunicorn workers.

State coordination uses a dedicated POSIX `flock` lock. State writes are atomic and files are restricted to mode `0600`.

State growth is bounded to **4096 source entries**. Expired entries are pruned during normal access, and oldest entries are evicted if the cap is reached.

No Redis, Celery, external service, new Python dependency, Django model or migration is introduced.

## Failure behavior

Limiter-state failures are **fail-open for authentication availability**:

- the login endpoint continues through its existing authentication flow;
- visitors do not receive internal error details;
- a generic operational error is logged.

This avoids turning a local limiter-state fault into permanent Owner lockout. The application authentication system remains authoritative.

## Logging

Limiter logs may contain only:

- logging timestamp;
- protected endpoint classification;
- generic failed/throttled/storage-error classification;
- truncated hashed source token.

The limiter does not log:

- passwords;
- POST bodies;
- submitted usernames;
- session IDs/cookies;
- CSRF tokens;
- authorization headers;
- private credentials.

## Existing security controls preserved

- CSRF validation remains handled by Django.
- Owner login remains fixed to the configured Owner username and requires an active staff user.
- Django Admin continues to use the standard `AdminSite.login` / `LoginView` authentication flow.
- Owner private responses retain `Cache-Control: private, no-store` and `X-Robots-Tag: noindex, nofollow`.
- Django Admin login retains its existing never-cache behavior.
- Public indexing remains independently disabled.

## Operational rollback

Rollback is application-only:

1. revert the private-login-protection commit/PR;
2. redeploy the previously approved application revision using the normal release procedure.

No database rollback, schema change, Redis cleanup, Nginx change, firewall change or systemd change is required.

The transient limiter files under `/run/lowcost-europa/` may be left to disappear on reboot or removed only as part of an explicitly approved rollback. Their presence does not affect the application once the middleware is absent.
