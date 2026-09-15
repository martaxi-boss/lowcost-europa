# MVP OPERATIONAL CLOSEOUT 001

## Scope

Operational closeout only. No new product features, catalog data, tracking, analytics, Docker, public launch or indexing enablement are part of this task.

## Gate A — SAFE DEPLOY RECONCILIATION: PASS

- Official GitHub main: `04dc3005ee046f453c8d525780927d7e26c17955`.
- Previous staging SHA: `d6537da40110b6431bab15d4b191752fc1a18f24`.
- Current staging SHA: `04dc3005ee046f453c8d525780927d7e26c17955`.
- Official GitHub tree and deployed tree: `6caef6c5eb60ab8a53b449868f94d45faba3128d`.
- The deploy worktree was clean before reconciliation and remained clean after it.
- The previous staging commit remains recoverable from the administrative clone.

The deploy account cannot authenticate directly to the private HTTPS origin. No PAT was created, embedded in a URL or stored in the repository.

Reconciliation used a local Git bundle generated from the already-authenticated administrative clone's `origin/main`. The bundle ref, target commit and tree were verified before the deploy workspace fetched the local bundle and checked out the authorized commit. The deploy `origin` was not changed.

`migrate --plan` reported no planned operations. Base requirements were already satisfied. `collectstatic` reported 128 files unmodified. Only `lowcost-europa.service` was restarted.
## Gate A validation

All required staging endpoints returned HTTP 200: live health, ready health, homepage, Contacto, Como funciona, Afiliados, Privacidade, Termos, sitemap, robots and AliExpress callback.

Live database remained:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 9
- OfferClicks = 5

Staging remains fail-closed: `DJANGO_PUBLIC_INDEXING_ENABLED=false`, `DJANGO_PUBLIC_SITE_URL=`; HTML meta robots and `X-Robots-Tag` remain `noindex, nofollow`; `robots.txt` remains `Disallow: /`. No `/go/` request was made.

The latest daily PostgreSQL backup validated before reconciliation was `lowcost-europa-20260915T031500Z.dump`, size 94,565 bytes, with mode 600. Its checksum sidecar validated successfully and `pg_restore --list` passed.

## Gate B — SECRET RECOVERY HARDENING: PASS

The AliExpress secret source remains local and root-only at `/root/project-secrets/lowcost-europa/.env`, mode 600, owner root:root. Only the expected AliExpress variable names are present; secret values were not printed.

`/root/project-secrets/restore-project-secrets.sh` now supports `lowcost-europa` while preserving existing project support. It links `/root/lowcost-europa/.env` to the root-only vault instead of duplicating values.

The restore flow was tested in an isolated temporary directory with dummy data. Source discovery, mode enforcement, symlink creation, non-disclosure on stdout and cleanup all passed.
This is LOCAL recovery only. It does not protect against total loss of the Droplet.

## Gate C — OFF-SERVER BACKUP DESIGN: WAITING OWNER AUTHORIZATION

Preferred design: private Cloudflare R2 storage with restic encryption. No explicit owner authorization to activate R2 was found, so no account, bucket, external credential, paid service or remote secret was created.

When authorized, the recovery design must include:

- a private R2 bucket;
- restic encryption;
- least-privilege external credentials stored outside GitHub;
- defined retention;
- off-server PostgreSQL backup transfer;
- restore/download test and checksum verification;
- failure alerting;
- encrypted recovery coverage for the AliExpress secrets as well as PostgreSQL.

The restic password or other recovery key must not exist only on the Droplet. **OFF-DROPLET RECOVERY KEY REQUIRED.** This document does not prescribe where the owner stores that key.

Because R2 activation is owner-dependent, execution stops at Gate C. Gates D, E and F were not executed in this run.

## Safety status

- Tokens exposed: ZERO.
- Private operator data exposed: ZERO.
- `/go/` called: NO.
- New catalog data: ZERO.
- Unexpected migrations: ZERO.
- Noindex: PRESERVED.
- Public launch: NO.
- Direct main write: ZERO.
