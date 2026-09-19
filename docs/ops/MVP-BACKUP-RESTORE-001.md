# MVP BACKUP / RESTORE 001

## Scope
This runbook validates PostgreSQL backup and restore for the current Lowcost Europa staging/live database without restoring over the live database.

## Validated backup
- custom-format pg_dump;
- protected location outside the repository;
- mode 600;
- size 43,500 bytes;
- SHA256 `d80315ae7129f692feec69b434a5f44070235cb6086ff38755fc9f17f5053727`.

## Restore drill
Temporary database used: `lowcost_europa_restore_test_20260914_2323`.
The pre-0004 dump restored to 1 ProductFamily, 3 Offers and 6 OfferObservations.
`catalog.0003` was applied, `catalog.0004` was not applied, and primary remained `1005012522304882`.

The restored database was then migrated forward to `catalog.0004_offerclick` successfully.
Final restored state was 1 ProductFamily / 3 Offers / 6 OfferObservations / 0 OfferClicks.
The temporary database was dropped after validation.

## Recurring local backup
A simple systemd timer runs one local custom-format pg_dump daily at 03:15 UTC.
Retention is 7 days. Dumps and SHA256 sidecars are mode 600.
The versioned script is `deploy/scripts/backup-postgres.sh` with matching systemd service/timer units.
A manual validation run succeeded and produced a non-empty dump.

## Recovery procedure
1. Verify backup size, format, permissions and checksum.
2. Create a new temporary database; never overwrite live without explicit authorization.
3. Restore the dump into the temporary database.
4. Validate core counts, primary selection and migration state.
5. Run migrations forward using the current application code.
6. Validate counts again, then drop only the temporary database.

## Off-server disaster recovery

The local PostgreSQL backup remains the first layer and is not replaced. A second, independent Restic layer targets the already initialized private R2 repository.

The off-server snapshot includes:
- `/var/backups/lowcost-europa/daily/` with local `.dump` and `.sha256` files;
- `/etc/lowcost-europa/lowcost-europa.env`, encrypted inside Restic.

The off-server snapshot deliberately excludes the bootstrap credentials needed to reach/open its own repository:
- `/etc/lowcost-europa/r2.env`;
- `/etc/lowcost-europa/restic-password`.

Recovery therefore requires authorized Cloudflare/R2 access plus the Restic recovery password held outside this Droplet. The Builder never prints, copies or validates that external password copy.

The daily offsite timer is scheduled for 03:45 UTC, after the existing 03:15 UTC local PostgreSQL backup. The latest local dump must be non-empty, have a valid SHA256 sidecar and be no older than 6 hours. Otherwise offsite backup fails closed. After a successful snapshot and repository validation, retention keeps 7 daily, 4 weekly and 3 monthly matching snapshots, followed by prune and another repository check. The atomic success marker is written only after that full chain succeeds. A daily 05:15 UTC health check requires both marker and snapshot to be no older than 36 hours. Restic operations share a dedicated non-blocking lock at `/run/lock/lowcost-europa-restic.lock`.

The restore drill restores the latest offsite snapshot into a temporary root-only directory, validates the restored dump checksum and then performs a real `pg_restore` into a uniquely named PostgreSQL temporary database. It validates `django_migrations`, core catalog tables and readable catalog counts, then drops only the temporary database and removes the temporary directory. It explicitly refuses a temporary database name equal to the live database name.

## Recovery password gate

**RECOVERY PASSWORD GATE = PENDING.**

Phase 3 cannot be declared CLOSED/PASS until the Owner explicitly confirms YES that a copy of the Restic password exists outside this Droplet. The password itself must never be pasted into chat, Git, CI, logs or project documentation.

## Rollback / limits
The live database is not modified by the restore drill. The off-server repository is not reinitialized and the local backup system remains authoritative as the source feeding offsite snapshots.
