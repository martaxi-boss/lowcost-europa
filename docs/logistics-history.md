# Longitudinal logistics history diagnostics — LE-010

LE-010 summarizes the existing `OfferObservation` history for one `Offer`. It is read-only and diagnostic: it measures what happened across observations without declaring that a product is stable, verified, approved or commercially usable.

## Chronological history

Observations are ordered by `observed_at ASC` and then `pk ASC` for deterministic ties. A single `as_of` and explicit `max_age` are used for the entire assessment. The diagnostic default remains 24 hours, inherited as a provisional internal window from LE-009 rather than a commercial policy.

For each observation the service reuses LE-008 `assess_logistics_evidence()` and LE-009 `assess_logistics_freshness()`. It does not duplicate those rules.

## Summary facts

The assessment reports observation count, first/last timestamps, observation span, counts for every evidence and freshness state, counts supporting <=5 days and supporting current <=5 days, conflict/future flags, and the diagnostics for the latest known observation.

Empty history is valid and reports zero observations with no first/last/span/latest value. A single observation has a zero-length span. Multiple observations remain factual history only; no threshold converts them into commercial stability.

## Read-only command

Use:

```text
python manage.py aliexpress_logistics_history --product-id <ALIEXPRESS_PRODUCT_ID>
```

The command assumes the AliExpress source for this phase and performs only PostgreSQL reads. It never creates or updates an Offer/Observation, calls the AliExpress API, generates affiliate links or prints product/affiliate URLs, credentials or raw payloads.

If the Offer does not exist it exits clearly with `Offer not found`. If the Offer exists without observations it prints `Observations: 0` and `No logistics history available`.

## No commercial threshold

LE-010 deliberately does not calculate percentages, confidence, reliability, scores or booleans such as `stable`, `verified_delivery`, `commercially_usable` or `safe_to_publish`. `latest` means only the most recent known observation and does not erase earlier history. Conflict and future-timestamp flags remain visible independently.

The implementation is one ordered database query for the history plus O(n) in-memory assessment. No schema, migration, cache, scheduler or infrastructure is added.
