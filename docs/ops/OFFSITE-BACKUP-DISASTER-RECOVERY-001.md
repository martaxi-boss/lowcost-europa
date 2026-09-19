# OFFSITE BACKUP DISASTER RECOVERY 001

## Scope

This runbook covers recovery after total loss of the Lowcost Europa Droplet using the private Restic repository stored in Cloudflare R2.

It does not contain credential values. The Restic repository password must be obtained from the authorized off-Droplet recovery copy. R2 credentials must be created or recovered through authorized Cloudflare account access.

## Recovery prerequisites

- authorized access to the Lowcost Europa GitHub repository;
- authorized access to the Cloudflare account and R2 bucket;
- the Restic password from the off-Droplet recovery copy;
- a newly provisioned server suitable for the current application stack;
- DNS changes remain deferred until service validation is complete.

## Disaster recovery sequence

1. Provision a new server with sufficient storage and supported OS packages.
2. Recover authorized access to Cloudflare/R2.
3. Create or obtain authorized R2 credentials for the private backup bucket.
4. Obtain the Restic password from the off-Droplet recovery copy.
5. Install the supported Restic version and PostgreSQL tooling.
6. Configure the Restic repository endpoint and password file with root-only permissions.
7. Run `restic snapshots` and confirm expected Lowcost Europa snapshots are visible.
8. Run `restic check` and stop if repository health is not clean.
9. Restore the selected snapshot into a protected temporary directory.
10. Verify the restored PostgreSQL dump against its SHA256 sidecar.
11. Install or recreate PostgreSQL using the supported project version.
12. Create a new application database and restore the validated custom-format dump with `pg_restore`.
13. Recover `/etc/lowcost-europa/lowcost-europa.env` from the encrypted Restic snapshot and install it with restrictive ownership/mode.
14. Checkout the approved Lowcost Europa GitHub revision.
15. Install application dependencies and run the documented Django/system checks.
16. Install the approved systemd units, Nginx configuration, tmpfiles policy and other versioned operational files.
17. Run migrations/checks required by the approved application revision.
18. Start services and validate application health, PostgreSQL access, static files and public endpoints.
19. Only after service validation, restore DNS/tráfego according to the current Supervisor-approved hostname plan.

## Database validation

Do not restore directly over an unknown or partially recovered database. Validate the restored database before traffic is enabled.

At minimum confirm:
- `django_migrations` exists and can be queried;
- core catalog tables exist;
- ProductFamily and Offer tables can be read;
- Django system checks pass;
- liveness and readiness return 200 after service startup.

No fixed historical row counts are required because catalog data changes over time.
## Secrets and circular dependency

The Restic snapshot intentionally does not contain:
- `/etc/lowcost-europa/r2.env`;
- `/etc/lowcost-europa/restic-password`.

Those files are bootstrap requirements for reaching/opening the repository itself. Recovery therefore depends on authorized Cloudflare/R2 access and the Restic password copy stored outside the lost Droplet.

Never place credential values in Git, tickets, CI logs, documentation or chat.

## Recovery password gate

Phase 3 cannot be declared CLOSED/PASS until the Owner confirms **YES** that the Restic password has a copy stored outside the Droplet.

The confirmation is YES/NO only. The password itself must not be supplied to the Builder.

## Traffic safety

Do not restore public DNS/tráfego until:
- the database restore is validated;
- the application revision is checked out and dependencies are installed;
- migrations/checks pass;
- systemd services are active;
- liveness/readiness pass;
- indexing/public-launch controls match the latest Supervisor-approved state.

## Phase 3 operational proof

The audited implementation has been exercised against the existing initialized R2/Restic repository without running `restic init`.

Validated sequence:
- 7 daily / 4 weekly / 3 monthly retention dry-run: PASS;
- real backup followed by repository validation, retention and prune: PASS;
- atomic success marker created only after the full successful chain: PASS;
- daily health logic using marker + snapshot + repository check: PASS;
- Restic restore from R2: PASS;
- real `pg_restore` into a unique temporary PostgreSQL database: PASS;
- `django_migrations` and core catalog reads: PASS;
- temporary PostgreSQL database dropped: YES;
- temporary restore directory removed: YES;
- live database modified by the drill: NO.

Snapshot counts and repository storage size are operational observations and may change as retention/prune run; they are not recovery invariants.

## Restic repository capacity warning

The offsite health check has an operational warning threshold of exactly **8,000,000,000 bytes**, approximately **8 GB in decimal units**. This is intentionally not 8 GiB.

This threshold is a preventive margin against the approximately 10 GB free-tier reference considered during this phase. The health check measures repository capacity globally with `restic stats --mode raw-data --json --no-cache`, without snapshot tag or host filters, so the observed `total_size` covers the Restic repository as a whole.

The Restic `raw-data` value is an operational repository observation. It must not be treated as an exact Cloudflare R2 billing/storage measurement because provider accounting can use different semantics.

When observed Restic raw-data is below 8,000,000,000 bytes, repository capacity remains health-pass. At or above the threshold, the health check writes a capacity WARNING and exits non-zero so systemd records the health run as failed and the warning remains visible through normal service/journal inspection.

This capacity warning does **not** indicate repository corruption. It does not delete snapshots, change the 7 daily / 4 weekly / 3 monthly retention policy, trigger additional forget/prune operations, alter R2 lifecycle rules or modify the bucket. Human review is required before any capacity-policy change.
