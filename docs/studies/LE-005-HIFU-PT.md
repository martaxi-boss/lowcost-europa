# LE-005 first study — HIFU / Portugal

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Date: 2026-09-13. Market: PT. Currency: EUR. Requested limit: 10. Mode: dry-run.

## Result

The AliExpress search returned 9 normalized candidates. All 9 had valid unique product IDs; duplicates: 0; invalid IDs: 0. All 9 candidates completed the controlled detail/persistence path successfully in dry-run; failures: 0.

Data coverage after the detail path: price 9/9, currency 9/9, evaluation rate 4/9, sales count 9/9, commission rate 9/9, raw shipping 0/9, interpreted delivery days 0/9. Because no candidate exposed interpretable `delivery_days`, the <=5-day metric was not observable in this batch: within 5 days = 0, over 5 days = 0, missing = 9.

Dry-run projected 9 new Offers and 9 new Observations. Database counts were Offers=0 and Observations=0 before the study and remained 0/0 after the final confirmation run.

## Search-quality observation

The `HIFU` query returned titles dominated by `Hanfu`, cosplay and hair-accessory products rather than the intended professional HIFU equipment niche. This is factual search-quality evidence from this batch only. LE-005 does not filter, score, rank or label these products as good/bad.

## Performance — final Gate 5 confirmation

The final confirmation run against the corrected Gate 5 code completed in 18.16 seconds with maximum RSS 57,756 KB (~56.4 MB).

Immediately before that run the Droplet had 365 MB memory available, 270 MB swap used and load average 0.03/0.03/0.00. Immediately after it had 367 MB available, swap still 270 MB and load average 0.06/0.04/0.00. No material pressure was observed from this bounded batch.

## Interpretation

This study measures data availability only. It does not rank candidates or conclude that any product is good, bad, a winner or commercially suitable. Missing logistics is unknown data rather than evidence of slow delivery. No secrets, raw payloads or full affiliate/product URLs are recorded here.
