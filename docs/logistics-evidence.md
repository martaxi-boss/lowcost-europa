# Conservative logistics evidence assessment — LE-008

LE-008 adds a derived, non-persisted assessment for the delivery evidence already stored with explicit search/detail provenance on one observation. It does not create a final delivery estimate, a score, a ranking signal or a customer-facing claim.

## States

- `UNKNOWN`: neither search nor detail has interpreted delivery days. It does not support the <=5-day candidate criterion.
- `SEARCH_ONLY`: only search has interpreted delivery days. It supports the candidate criterion only when the search value is <=5.
- `DETAIL_ONLY`: only detail has interpreted delivery days. It supports the candidate criterion only when the detail value is <=5.
- `CONSISTENT`: search and detail both have the same interpreted value. It supports the candidate criterion only when that common value is <=5.
- `CONFLICT`: search and detail both exist but differ. It never supports the <=5-day candidate criterion automatically, even when both values are <=5.

`supports_within_5_days=True` means only that this single observation contains non-conflicting evidence reported by the source that is compatible with the strategic <=5-day candidate criterion. It is not independent confirmation and is not a delivery guarantee.

## Pure assessment

`apps/catalog/services/logistics_evidence.py` contains a deterministic O(1) pure function that receives the two delivery-day values and returns a small assessment containing the state, both source values, the boolean support flag and a short factual reason. It performs no database query, network call, save or mutation.

No precedence exists between search and detail. No `effective_delivery_days`, `resolved_delivery_days`, confidence score or logistics score is produced. A conflict remains a conflict for human review.

## Discovery diagnostics

Controlled discovery may display the derived `evidence_state` and `supports_5d` for successful candidates. These values are diagnostic only: discovery does not exclude, reorder, deactivate or avoid persisting a candidate because the assessment is false.

Use factual language such as: “the observation contains source evidence compatible with <=5 days.” Do not state or imply guaranteed delivery.
