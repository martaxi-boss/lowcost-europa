# Private Login Protection 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Scope

This control protects authentication POST attempts on:

- `/painel/entrar/`
- `/admin/login/`

GET login pages remain normally accessible. The control does not change Owner credentials, Django Admin authentication semantics, CSRF, session security, SSH, Nginx, firewall, catalog, backups or public indexing.

## Policy

The production policy is source-oriented:

- **5 failed authentication POST attempts**
- within a **5 minute window**
- the next attempt is answered with **HTTP 429**
- temporary throttle duration: **5 minutes**
- successful staff authentication clears the temporary state for that source
- state expires naturally
- stored source entries are capped at **4096**

The same source state covers both protected login surfaces. Submitted username/account identity is not part of the limiter key, so changing usernames or alternating between the Owner login and Django Admin does not create fresh source identities.

A throttle response is generic and includes `Retry-After`, `Cache-Control: private, no-store` and `X-Robots-Tag: noindex, nofollow`. It does not report remaining attempts or account existence.

## Trusted source attribution

The audited production topology is:

`Internet -> Nginx -> Gunicorn on 127.0.0.1:8001 -> Django`

Gunicorn listens only on loopback.

Nginx explicitly overwrites:

`X-Real-IP $remote_addr`

and also supplies `X-Forwarded-For`. The limiter intentionally **does not use X-Forwarded-For**.

Source selection is:

1. Parse Django `REMOTE_ADDR`.
2. If the immediate peer is loopback, accept a valid `X-Real-IP` supplied by the trusted local Nginx hop.
3. Otherwise use `REMOTE_ADDR` directly and ignore forwarded client headers.
4. Malformed direct peer input collapses to a bounded `unknown` source rather than creating attacker-controlled arbitrary keys.
5. IPv4 and IPv6 are normalized with Python's `ipaddress` library.

This policy relies on the audited loopback-only Gunicorn binding and Nginx header overwrite. If that topology changes, source attribution must be re-audited before relying on this control.

## Shared state mechanism

The application currently uses two Gunicorn workers, so per-process Python memory is not sufficient.

No external dependency, Redis, Celery, cache service, database table or migration is introduced.

Rate-limit state is stored under the existing shared runtime directory:

`/run/lowcost-europa/`

using:

- a dedicated lock file;
- `fcntl.flock` for inter-process exclusion;
- mode `0600` state/lock files;
- atomic state-file replacement;
- bounded entry count;
- automatic expiry/pruning.

Only a SHA-256 token derived from the normalized source is persisted; raw passwords, POST bodies, session IDs, cookies, CSRF tokens, usernames and credentials are not stored.

## Logging

Security logging is intentionally minimal:

- protected endpoint classification;
- generic failed-authentication event;
- generic throttle event;
- abbreviated hashed source token.

Logs do not include passwords, submitted usernames, POST bodies, sessions, cookies, CSRF tokens or authorization credentials.

## Failure behavior

The limiter is **fail-open** if its state mechanism cannot be read or written:

- the login request continues through the existing authentication path;
- the endpoint does not crash;
- no permanent Owner lockout is created;
- a generic operational error is logged without exception detail or credentials.

This choice prioritizes preserving authorized Owner/Admin access if the short-lived rate-limit state becomes unavailable.

## CSRF ordering

The limiter is implemented as view/response middleware after Django's CSRF middleware. A request rejected by CSRF is rejected before the authentication rate-limit decision and is not counted as an authentication failure.

Existing Owner-panel private headers and Django Admin authentication flow remain unchanged.

## Operational rollback

Rollback is application-only:

1. revert the private-login-protection commit;
2. deploy the reverted application through the normal audited process;
3. optionally remove the two dedicated transient rate-limit files under `/run/lowcost-europa/` after the old code is no longer running.

No database rollback, migration, Nginx change, firewall change or external service cleanup is required.

## Pre-merge limitation

This change is tested before merge/deploy. No repeated authentication attempts are generated against production during this implementation pass. Controlled runtime threshold validation requires separate Supervisor authorization after an approved deployment.
