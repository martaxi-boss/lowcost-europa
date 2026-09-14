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

## Rollback / limits
The live database is not modified by the restore drill. Local backups do not replace an off-server copy.
**BACKUP OFF-SERVER = PENDING.** The Supervisor/owner must authorize the external destination before public MVP launch.
