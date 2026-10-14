# MVP OPERATIONAL CLOSEOUT 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

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

The initial pass stopped at Gate C as required. A later Supervisor final-completion order explicitly authorized continuing with all other possible gates while keeping R2 owner-gated; the final statuses below supersede that initial stop state.

## Safety status

- Tokens exposed: ZERO.
- Private operator data exposed: ZERO.
- `/go/` called: NO.
- New catalog data: ZERO.
- Unexpected migrations: ZERO.
- Noindex: PRESERVED.
- Public launch: NO.
- Direct main write: ZERO.
## Final completion pass

### State before

- GitHub main: `1b5e9f30d2606bf030463a4f5a571e7b4fcb4bb6`.
- Staging before final reconciliation: `04dc3005ee046f453c8d525780927d7e26c17955`.
- Live database: 5 ProductFamilies / 6 Offers / 9 OfferObservations / 5 OfferClicks.
- Services required by the project were active and enabled.
- UFW still allowed 7860/tcp, 7861/tcp and 8000/tcp in IPv4 and IPv6, with no active listeners.
- `/root/Painel_AliExpress` still existed but was inactive.

### Gate C — OFF-SERVER RECOVERY: OWNER BLOCKED

No explicit owner authorization to create/configure Cloudflare R2 exists in this execution context. No R2 account, bucket, credential, paid obligation or remote repository was created.

The approved design remains private R2 object storage plus restic encryption, covering PostgreSQL dumps and encrypted AliExpress secret recovery. **OFF-DROPLET RECOVERY KEY REQUIRED.**

### Gate D — FIREWALL AND LEGACY: PASS

Immediately before change there were no listeners on 7860, 7861 or 8000 and no active Nginx, systemd, cron, PM2, Django or callback dependency on the legacy panel. PM2 contained only unrelated active processes.

Only UFW rules for 7860/tcp, 7861/tcp and 8000/tcp were removed, including IPv6 counterparts. OpenSSH and Nginx/HTTPS access remain allowed.
The legacy `/root/Painel_AliExpress` tree was moved, not deleted, to `/root/archive/lowcost-europa-legacy/Painel_AliExpress`. The quarantine directory is root-only and a SHA-256 manifest was created and verified. Legacy bot-detection/cloaking code was not imported or reactivated.

### Gate E — GITHUB / RECOVERY: BLOCKED

The existing `builder/mvp-operational-closeout-001` branch was cleanly merged forward from current `origin/main`. The merged commercial validation report remains present, as do the valid closeout documentation and PROJECT_STATE changes.

Tracked-file scanning found no real AliExpress credential assignment. `.env.example` and code/docs refer only to variable names.

Main protection could not be configured with available capabilities. The GitHub integration cannot access the branch-protection endpoint, and repository rulesets report that the feature requires a plan upgrade or a public repository. No PAT was created and no bypass was attempted. **OWNER/GITHUB ADMIN ACTION REQUIRED.**

### Gate F — FINAL DEPLOY RECONCILIATION: PASS

Staging was reconciled to current official main `1b5e9f30d2606bf030463a4f5a571e7b4fcb4bb6`, tree `daae83d42d3f1bceb7106bec5ff157166a39a051`, using the verified local Git-bundle mechanism. The deploy worktree is clean.

The only main delta since the previous staging SHA was documentation from Commercial Validation 001, so no application service restart was performed.

### Gate G — FINAL TECHNICAL VALIDATION: PASS WITH EXPLICIT BLOCKERS

- Django check: PASS.
- Migration drift: no changes detected.
- Migration plan: no planned operations.
- Live health, ready health, homepage, Contacto, robots and AliExpress callback: HTTP 200.
- Live database: 5 / 6 / 9 / 5.
- Nginx configuration test: PASS.
- Required services and backup timer: active and enabled.
- Latest daily PostgreSQL dump checksum: PASS; `pg_restore --list`: PASS.
- Noindex remains fail-closed: indexing disabled, public site URL empty, `X-Robots-Tag: noindex, nofollow`, robots disallows all.
- Firewall has no 7860/7861/8000 rules and no listeners on those ports.
- Legacy panel quarantine checksum verification: PASS.
- Off-server backup: OWNER BLOCKED.
- Main protection: BLOCKED — OWNER/GITHUB ADMIN ACTION REQUIRED.

### Resources

Final resource snapshot: 961 MiB RAM total, 335 MiB available; 4 GiB swap with 335 MiB used; root filesystem 24 GiB total, 16 GiB used, 7.6 GiB available (68%). No infrastructure increase was made.

### Open problems and risks

1. Off-server recovery does not exist until the owner authorizes R2/restic and retains a recovery key outside the Droplet.
2. GitHub `main` remains without enforceable protection until account/admin capability is available.
3. Public launch remains unauthorized and staging remains noindex.
4. Existing product-image quality finding for one HIFU offer remains outside this operational closeout.

### Recommendation

Supervisor should audit this branch. If accepted, merge through the normal PR/CI flow. After any future merge that changes official main again, staging should be reconciled to that new main SHA; documentation-only merges do not require an application restart.

The Builder does not declare MVP OPERATIONAL CLOSEOUT 001 closed. Only the Supervisor may declare CLOSED or NOT CLOSED after audit.
