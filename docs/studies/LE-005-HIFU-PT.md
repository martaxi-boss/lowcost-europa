# LE-005 first study — HIFU / Portugal

Date: 2026-09-13. Market: PT. Currency: EUR. Requested limit: 10. Mode: dry-run.

## Result

The AliExpress search returned 9 normalized candidates. All 9 had valid unique product IDs; duplicates: 0; invalid IDs: 0. All 9 candidates completed the controlled detail/persistence path successfully in dry-run; failures: 0.

Data coverage after the detail path: price 9/9, currency 9/9, evaluation rate 4/9, sales count 9/9, commission rate 9/9, raw shipping 0/9, interpreted delivery days 0/9. Because no candidate exposed interpretable `delivery_days`, the <=5-day metric was not observable in this batch: within 5 days = 0, over 5 days = 0, missing = 9.

Dry-run projected 9 new Offers and 9 new Observations. Database counts were Offers=0 and Observations=0 before the study and remained 0/0 after the final confirmation run.

## Search-quality observation

The `HIFU` query returned titles dominated by `Hanfu`, cosplay and hair-accessory products rather than the intended professional HIFU equipment niche. This is factual search-quality evidence from this batch only. LE-005 does not filter, score, rank or label these products as good/bad.

## Performance

A measured bounded run completed in 18.31 seconds with maximum RSS 57,752 KB (~56.4 MB). The final confirmation run against the stabilized code completed in 18.06 seconds with maximum RSS 57,748 KB (~56.4 MB).

Before the measured study the Droplet had 346 MB memory available, 269 MB swap used and load average 0.02/0.01/0.00. After that study it had 355 MB available, swap still 269 MB and load average 0.06/0.02/0.00. No material pressure was observed from this bounded batch.

## Interpretation

This study measures data availability only. It does not rank candidates or conclude that any product is good, bad, a winner or commercially suitable. Missing logistics is unknown data rather than evidence of slow delivery. No secrets, raw payloads or full affiliate/product URLs are recorded here.
