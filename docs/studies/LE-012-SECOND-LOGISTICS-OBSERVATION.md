# LE-012 — Second longitudinal logistics observation

## Status

Preparation only. The second live Observation round is blocked until 2026-09-14 19:51 Europe/Lisbon.

No second Observation has been executed while preparing this document.

## Purpose

This study reobserves exactly the three LE-011 professional HIFU Offers for PT / EUR / EN after at least 24 hours of real elapsed time.

It is a descriptive longitudinal technical study only. Two observations do not establish commercial stability, verification, reliability, recommendation or a delivery guarantee.

## Fixed cohort

- `1005012522304882`
- `1005013116584854`
- `1005013002556821`

No product may be added, removed or substituted in LE-012.

## Baseline state confirmed during preparation

- ProductFamily: 0
- Offer: 3
- OfferObservation: 3
- Each fixed Offer has exactly 1 Observation.
## Baseline values

### 1005012522304882
- Baseline observed at: 2026-09-13T18:50:52.565040+00:00
- Price: 711.53 EUR
- Sales count: 3
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence: SEARCH_ONLY

### 1005013116584854
- Baseline observed at: 2026-09-13T18:50:54.501181+00:00
- Price: 216.81 EUR
- Sales count: 0
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence: SEARCH_ONLY

### 1005013002556821
- Baseline observed at: 2026-09-13T18:50:55.969873+00:00
- Price: 893.52 EUR
- Sales count: 0
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence: SEARCH_ONLY
## Pre-live safeguards

Before the second live round:

- confirm at least 24 hours real elapsed time since the baseline;
- confirm DB remains ProductFamily=0, Offer=3, OfferObservation=3;
- run the exact fixed three IDs together in dry-run;
- require zero permanent writes in dry-run;
- require no structural PostgreSQL error;
- preserve search/detail provenance and product ID integrity;
- do not replace a product after an external AliExpress failure;
- execute at most one `--commit` round.

## Second-round results

Pending. Do not populate before the live window opens and the controlled round is actually executed.

Record per Offer: observed timestamp, elapsed interval, price, original price, sales count, commission rate, search delivery days, detail delivery days, evidence state, freshness state, availability and factual errors.

## Database after second round

Pending actual execution.

## History after second round

Pending actual execution. Record observation count, first, last, span, evidence counts, freshness counts, conflict/future flags and latest diagnostics for all three Offers.

## Interpretation

Keep interpretation strictly descriptive. Do not calculate a reliability percentage, confidence score, stability score or commercial-readiness decision.

Even if both observations match, two observations are only two observations.
