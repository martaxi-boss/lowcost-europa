# LE-005 first study — HIFU / Portugal

Date: 2026-09-13. Market: PT. Currency: EUR. Requested limit: 10. Mode: dry-run.

## Result

The AliExpress search returned 9 normalized candidates. All 9 had valid unique product IDs; duplicates: 0; invalid IDs: 0. All 9 candidates completed the controlled detail/persistence path successfully in dry-run; failures: 0.

Data coverage after the detail path: price 9/9, currency 9/9, evaluation rate 4/9, sales count 9/9, commission rate 9/9, raw shipping 0/9, interpreted delivery days 0/9. Because no candidate exposed interpretable `delivery_days`, the <=5-day metric was not observable in this batch: within 5 days = 0, over 5 days = 0, missing = 9.

The normalized search response showed the same aggregate coverage in this run: price 9/9, currency 9/9, evaluation rate 4/9, sales 9/9, commission 9/9, raw shipping 0/9 and delivery days 0/9. This is an observation about this single batch, not a general rule about search versus detail.

Dry-run projected 9 new Offers and 9 new Observations. Database counts remained Offers=0 and Observations=0 after the command.

## Performance

Elapsed time: 18.16 seconds. Maximum command RSS: 57,624 KB (~56 MB). Before the run the Droplet had ~344 MB memory available, 269 MB swap used and load average 0.04/0.03/0.00. After the run it had ~372 MB available, swap still 269 MB and load average 0.10/0.05/0.01. No material pressure was observed from this bounded batch.

## Interpretation

This study measures data availability only. It does not rank candidates or conclude that any product is good, bad, a winner or commercially suitable. In particular, missing logistics is unknown data rather than evidence of slow delivery. No secrets, raw payloads or full affiliate/product URLs are recorded here.
