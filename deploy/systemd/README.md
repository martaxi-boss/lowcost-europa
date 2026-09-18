# Catalog maintenance systemd policy

`lowcost-europa-catalog-maintenance.timer` runs catalog availability maintenance hourly after an initial 15 minute boot delay. The timer is persistent.

`lowcost-europa-catalog-maintenance.service` runs:

```text
/srv/lowcost-europa/.venv/bin/python manage.py maintain_catalog_offers --batch-size 10
```

This means **up to 10 eligible Offers per hourly execution**, not a guarantee that 10 Offers are always checked. A run may have fewer eligible Offers or stop early when the existing AliExpress rate-limit breaker aborts the batch.

Maintenance remains single-concurrency and keeps the existing AliExpress cadence/operation locking, retry/backoff/jitter, `Retry-After`, HTTP 429 breaker/accounting, HTTP 5xx handling and transport-error handling.

Only factual unavailability deactivates an Offer. Transient failures do not deactivate it and are recorded as `UNKNOWN`. Normal maintenance selects only active Offers, so inactive Offers are never auto-reactivated.

## Shared AliExpress runtime state

AliExpress operation locking and cadence use `/run/lowcost-europa/aliexpress.lock` and `/run/lowcost-europa/aliexpress.last-start`. The directory is defined by `deploy/tmpfiles.d/lowcost-europa.conf` as `0750`, owned by `le001_1789265592:le001_1789265592`.

Deployment must install the versioned tmpfiles rule under the system tmpfiles configuration and run the normal `systemd-tmpfiles --create` provisioning step **before** starting/restarting application or maintenance processes that may instantiate `AliExpressClient`. The client deliberately does not create the parent directory itself.

`PrivateTmp=true` remains enabled on both `lowcost-europa.service` and `lowcost-europa-catalog-maintenance.service`. `/run/lowcost-europa` is outside those private `/tmp` namespaces, so Django, hourly maintenance and direct management commands share the same lock/cadence inodes. State files remain `0600` through `_secure_state_open()`.

## Offsite backup and disaster recovery

The existing local PostgreSQL timer remains unchanged at 03:15 UTC. The versioned offsite timer runs at 03:45 UTC and invokes `/usr/local/sbin/lowcost-europa-offsite-backup`.

The offsite script is root-only at runtime because it must read `/etc/lowcost-europa/r2.env`, `/etc/lowcost-europa/restic-password` and the application environment. It validates the two Restic bootstrap secret files as regular, non-symlink files owned by `root:root` with mode `0600`.

Before any upload, the newest local PostgreSQL dump must be non-empty, have a valid SHA256 sidecar and be no older than 6 hours. A dedicated `/run/lock/lowcost-europa-restic.lock` prevents concurrent Restic operations.

The offsite snapshot contains the local daily backup directory and `/etc/lowcost-europa/lowcost-europa.env`. It deliberately excludes `r2.env` and `restic-password` to avoid circular recovery dependencies.

A weekly health timer runs the repository health script. The restore drill is manual and restores only into a temporary directory; it validates checksum and `pg_restore --list` without touching the live database.

Runtime installation/enabling of these new units is performed only after the corresponding implementation has been audited and merged.
