# AUDIT + OPERATIONAL HYGIENE CLOSEOUT 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Status: READY FOR SUPERVISOR AUDIT

## Scope

Final hygiene, recovery and regression audit on official base `6ed75927509672c9e0ea89e6104c9b280973176a`.
No new feature, catalog discovery/import, schema change, public indexing, GO LIVE, domain work or live AliExpress call was performed.

## Baseline before cleanup

- main SHA: `6ed75927509672c9e0ea89e6104c9b280973176a`
- deploy SHA: same official SHA; `/srv/lowcost-europa` clean
- root checkout before phase: previous merged builder branch at `bd878114536228ef746e88df8d2635d5100fa372`, clean
- root working branch for this phase: `builder/audit-operational-hygiene-closeout-001`
- disk: 24G total, 15G used, 8.8G available, 63%
- inodes: 311741 used / 2833987 free, 10%
- RAM: 961 MiB total, 333 MiB available
- swap: 4.0 GiB total, 331 MiB used
- `/tmp`: 3.8M
- `/root/.vscode-server`: 2.1G
- `/root/.cursor-server`: 1.6G
- `/root/.cache`: 2.9M
- `/root/.npm`: 13M
- `/var/cache`: 37M
- `/var/log`: 988M
- journal: 812.4M

## Cleanup executed

- Removed audited historical Lowcost Europa `/tmp` runners, QA files, JSON outputs, deploy/test scripts and old Playwright/pip logs individually.
- Preserved the two AliExpress runtime lock/cadence files.
- Runtime API files remain regular files, mode `0600`, owned by the application user.
- Preserved system service temporary state and active sockets.
- Ran `pip cache purge`, `npm cache clean --force` and `apt-get clean`; no packages were removed.
- Ran `journalctl --vacuum-size=250M`: journal went from 812.4M to 215.2M; journalctl reported 597.1M freed.
- Removed the obsolete Nginx pre-staging rollback after confirming current config matched versioned config.
- Active Nginx filename remains `lowcost-europa-temp`; rename was not completed because the execution environment blocked symlink mutation. The prepared unused copy was removed, leaving the known-good active config unchanged.

## Editor server hygiene

VSCode remained approximately 2.1G and Cursor approximately 1.6G. The only observed active editor process was a VSCode agent. The audit could not prove which stored editor build was safe to remove without risking an administration/editor session, so no editor build, user config or extension was removed and no editor process was killed.

This is a hygiene non-blocker, not a claim that editor cleanup was completed.

## Legacy and public webroots

- Legacy AliExpress panel is absent from its former root location.
- Quarantine remains root-only under the existing Lowcost Europa legacy archive.
- The quarantine SHA256 manifest verified every quarantined file successfully.
- Quarantine was not reactivated or moved into a webroot.
- The AliExpress callback PHP file remains present in the Lowcost Europa webroot.
- The default webroot contains only the standard Nginx index file observed in this audit.

## Database integrity

Baseline and final production counts are `5 ProductFamilies / 6 Offers / 15 OfferObservations / 35 OfferClicks`.
OfferClicks did not change during this audit.

Integrity checks:
- invalid primary Offers: 0
- ProductFamilies with duplicate primary Offers: 0
- orphan OfferObservations: 0
- no catalog write was performed

## Backup and recovery

Latest validated backup: `lowcost-europa-20260915T171915Z.dump`.
- SHA256 sidecar verification: PASS
- `pg_restore --list`: PASS
- isolated restore: PASS
- restored counts: 5 / 6 / 15 / 35
- temporary restore DB was dropped after verification
- production DB was never used as a restore target
- off-server second copy remains owner-gated/PENDING

## Services, ports and firewall

Essential units are active and enabled: `lowcost-europa.service`, Nginx, PostgreSQL, PHP-FPM and `lowcost-europa-backup.timer`.
`systemctl --failed` returned no failed units.

Expected listeners were confirmed:
- 22 public SSH
- 80/443 public Nginx
- 8001 loopback Gunicorn
- 5432 loopback PostgreSQL

No listeners were present on legacy 7860, 7861 or 8000.
UFW remains OpenSSH + Nginx Full + explicit 443 for IPv4/IPv6; the redundant explicit 443 rule was intentionally left unchanged.
The unrelated PM2 applications `iptvpn_bot` and `TELEGRAM-IPTVPN` remained online and were not modified.

## Health, DNS and certificates

Final HTTPS checks returned 200 for DuckDNS root, live health, ready health, Contacto, robots, AliExpress callback and static CSS. The sslip root also returned 200.
DuckDNS resolves to `165.22.114.67`.
Both Lowcost Europa certificates are valid: DuckDNS through 2026-12-14 and sslip through 2026-12-11.
`certbot.timer` is active and enabled. No certificate was renewed or removed in this phase.

## Noindex / staging

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=`
- response header: `X-Robots-Tag: noindex, nofollow`
- meta robots: `noindex, nofollow`
- robots: `User-agent: *` + `Disallow: /`
- public launch: NO
- `check --deploy` reports only the accepted staging warning `security.W004` because HSTS remains disabled.

## Django, dependencies and regression

Live-context validation:
- `manage.py check`: PASS
- `makemigrations --check --dry-run`: no changes
- `migrate --plan`: no planned operations
- `pip check`: no broken requirements

Full test suite was rerun with development test settings and the established PostgreSQL Unix-user context: `224 / 224 PASS`.
An earlier run under production settings produced HTTPS-redirect 301 results and was discarded as an invalid test context, not treated as an application regression.

AliExpress live operations during this audit: ZERO.
Ruff: PASS.
`git diff --check`: PASS.
`git fsck --connectivity-only`: PASS with no output.

The 224-test suite includes the merged AliExpress API safety coverage for storefront zero-API, concurrency/lock, minimum interval, timeout, Retry-After seconds/date/cap, exponential backoff, jitter, bounded retries, 429 circuit breaker, batch abort, 5xx/transport retry, 4xx fail-fast, fresh timestamp/signature per retry, secure runtime files, last-known-good and exact-ID refresh behavior.

## Secrets and callback

Only names and permissions were audited; secret values were not printed.
- production env: mode 0600, root-owned
- root secret vault env: mode 0600, root-owned
- restore script: mode 0700, root-owned
- no secret value was intentionally added to Git
- signed AliExpress requests and raw affiliate URLs were not added to this report

The callback remained reachable with HTTP 200 and its external AliExpress configuration was not changed.

## Final resource snapshot

- disk: 24G total, 14G used, 9.4G available, 60%
- inodes: 311683 used / 2834045 free, 10%
- RAM: 961 MiB total, 350 MiB available
- swap: 4.0 GiB total, 340 MiB used
- `/tmp`: 3.6M
- journal: 215.2M
- `/var/log`: 391M
- VSCode server: 2.1G preserved
- Cursor server: 1.6G preserved
- root cache: 2.9M
- npm cache tree: 13M
- `/var/cache`: 37M

The human-readable `df` snapshot moved from 15G used / 8.8G available to 14G used / 9.4G available. The exact directly reported cleanup amount is the journal vacuum's 597.1M; an exact aggregate byte delta was not captured at baseline and is therefore not invented.

## Git and deployment alignment

The phase started from official main `6ed75927509672c9e0ea89e6104c9b280973176a` and the deploy remained on that exact SHA throughout. No unapproved code was deployed.
The final phase commit/PR is documentation-only plus `PROJECT_STATE.md`; the root administrative checkout is returned to clean `main` after push/PR, while the review branch remains remote for Supervisor audit.

## Open non-blockers

- factual HIFU image source remains 123x123
- off-server R2/restic second copy remains owner-gated/PENDING
- GitHub branch protection remains constrained by account/admin capability
- definitive public domain remains pending
- legal/public-launch gate remains pending
- VSCode/Cursor old-build cleanup was conservatively skipped because safe deletion could not be proven without session risk
- Nginx active filename remains the harmless legacy name `lowcost-europa-temp`; obsolete rollback was removed and active content remains the versioned configuration

## Decision boundary

This phase is `READY FOR SUPERVISOR AUDIT`, not `AUDIT CLOSED`.
The Builder does not merge this branch and does not start a new phase.
