# Catalog maintenance systemd policy

`lowcost-europa-catalog-maintenance.timer` runs catalog availability maintenance hourly after an initial 15 minute boot delay. The timer is persistent.

`lowcost-europa-catalog-maintenance.service` runs:

```text
/srv/lowcost-europa/.venv/bin/python manage.py maintain_catalog_offers --batch-size 10
```

This means **up to 10 eligible Offers per hourly execution**, not a guarantee that 10 Offers are always checked. A run may have fewer eligible Offers or stop early when the existing AliExpress rate-limit breaker aborts the batch.

Maintenance remains single-concurrency and keeps the existing AliExpress cadence/operation locking, retry/backoff/jitter, `Retry-After`, HTTP 429 breaker/accounting, HTTP 5xx handling and transport-error handling.

Only factual unavailability deactivates an Offer. Transient failures do not deactivate it and are recorded as `UNKNOWN`. Normal maintenance selects only active Offers, so inactive Offers are never auto-reactivated.
