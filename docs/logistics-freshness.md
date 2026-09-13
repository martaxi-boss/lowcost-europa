# Temporal validity of logistics evidence — LE-009

LE-009 adds a derived, non-persisted assessment of how recent one `OfferObservation` is. It is a separate dimension from LE-008 evidence quality.

## States

- `FRESH`: `0 <= as_of - observed_at <= max_age`.
- `STALE`: `as_of - observed_at > max_age`.
- `FUTURE`: `observed_at > as_of`; the inconsistency is reported and never clamped to zero.

`FRESH` means only that the observation is within the supplied diagnostic window. It does not mean the logistics estimate is correct or guaranteed.

## Pure assessment

`apps/catalog/services/logistics_freshness.py` receives timezone-aware `observed_at`, timezone-aware `as_of` and a positive `timedelta` `max_age`. Naive datetimes and non-positive windows raise `ValueError`.

The service is deterministic and O(1). It performs no ORM query, network call, save, mutation or persistence. No freshness value is stored in the database.

## Provisional 24-hour diagnostic window

Controlled discovery in LE-009 uses `timedelta(hours=24)` for diagnostics. This is a provisional engineering window for learning system behaviour, not a final commercial freshness policy.

The service itself is not hard-coded to 24 hours; callers must supply `max_age` explicitly.

## Composition with LE-008

Evidence quality and freshness remain independent. The internal diagnostic composition is:

```text
supports_current_5d_candidate =
    evidence.supports_within_5_days
    AND freshness.is_fresh
```

Therefore fresh conflicting/unknown evidence is false, stale positive evidence is false, and any `FUTURE` observation is false.

This value is diagnostic only. It does not filter persistence, rank products, create a score, choose a winner or authorize a customer-facing delivery claim.
