# LE-012 — Second longitudinal logistics observation

## Status

Executed on 2026-09-14 after the authorized live window opened.

The fixed LE-011 cohort was reobserved exactly once with no substitutions.

## Purpose

This study reobserves exactly the three LE-011 professional HIFU Offers for PT / EUR / EN after at least 24 hours of real elapsed time.

It is a descriptive longitudinal technical study only. Two observations do not establish commercial stability, verification, reliability, recommendation or a delivery guarantee.

## Fixed cohort

- `1005012522304882`
- `1005013116584854`
- `1005013002556821`

No product was added, removed or substituted.

## Pre-live verification

Before any live write, the branch HEAD was `99fc0489ed7de57c2d7da734f5432697059b338f` and the live DB was confirmed as ProductFamily=0, Offer=3, OfferObservation=3, with exactly one Observation per fixed Offer.
The latest baseline timestamp was `2026-09-13T18:50:55.969873+00:00`. At the execution checkpoint, local time was `2026-09-14T20:01:22+01:00` (`19:01:22 UTC`), so the minimum 24-hour cadence had elapsed.

## Dry-run

The exact three IDs were executed together with `--dry-run`.

Result:

- successful: 3
- failed: 0
- Offers created: 0
- Offers reused: 3
- projected Observations: 3
- search delivery days: 5 for all three
- detail delivery days: NULL for all three
- evidence: SEARCH_ONLY for all three
- freshness: FRESH for all three
- OperationalError: 0
- structural PostgreSQL errors: 0

After dry-run, the live DB remained ProductFamily=0, Offer=3, OfferObservation=3, with exactly one Observation per Offer. No permanent dry-run write occurred.

## Single live second round

After the dry-run safeguards passed, one and only one `--commit` round was executed for the same fixed cohort.

Result: 3 successful, 0 failed, 0 Offers created, 3 Offers reused, 3 Observations created.
## Baseline vs second observation

### 1005012522304882
- baseline: `2026-09-13T18:50:52.565040+00:00`, price 711.53 EUR, original price 748.98 EUR, sales 3, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- second: `2026-09-14T19:06:24.275927+00:00`, price 713.70 EUR, original price 751.26 EUR, sales 3, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- elapsed: 1d 15m 31s
- factual change: price +2.17 EUR; original price +2.28 EUR; sales, commission, search/detail logistics and availability unchanged
- evidence remained SEARCH_ONLY; latest freshness is FRESH

### 1005013116584854
- baseline: `2026-09-13T18:50:54.501181+00:00`, price 216.81 EUR, original price 289.08 EUR, sales 0, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- second: `2026-09-14T19:06:26.200344+00:00`, price 226.17 EUR, original price 289.96 EUR, sales 0, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- elapsed: 1d 15m 31s
- factual change: price +9.36 EUR; original price +0.88 EUR; sales, commission, search/detail logistics and availability unchanged
- evidence remained SEARCH_ONLY; latest freshness is FRESH

### 1005013002556821
- baseline: `2026-09-13T18:50:55.969873+00:00`, price 893.52 EUR, original price 893.52 EUR, sales 0, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- second: `2026-09-14T19:06:27.944023+00:00`, price 896.24 EUR, original price 896.24 EUR, sales 0, commission 7.0000%, search days 5, detail days NULL, availability UNKNOWN
- elapsed: 1d 15m 31s
- factual change: price +2.72 EUR; original price +2.72 EUR; sales, commission, search/detail logistics and availability unchanged
- evidence remained SEARCH_ONLY; latest freshness is FRESH
## Database after second round

- ProductFamily: 0
- Offer: 3
- OfferObservation: 6
- each fixed Offer: 2 Observations
- no third Observation executed

## History after second round

For all three Offers:

- observation_count: 2
- evidence counts: SEARCH_ONLY=2; all other evidence states=0
- freshness counts: FRESH=1, STALE=1, FUTURE=0
- supports <=5 count: 2
- supports current <=5 count: 1
- conflict: no
- future timestamp: no
- latest search days: 5
- latest detail days: NULL
- latest evidence: SEARCH_ONLY
- latest freshness: FRESH

Observed spans were approximately `1d 15m 31s` for each Offer. The baseline Observation is now diagnostically STALE because the provisional 24-hour freshness window elapsed; this is not a commercial rule.

## Interpretation

The second round reproduced the same search/detail logistics provenance for all three Offers: search reported 5 days and detail remained unavailable. Prices increased for all three Offers, while sales count and commission rate did not change in this sample.
No external AliExpress failure occurred in the controlled second round. Command wall-clock performance was not separately instrumented, so no invented elapsed runtime is reported.

No stability score, reliability score, confidence percentage, ranking, winner or commercial-readiness decision was calculated.

**Two observations do not, by themselves, constitute proof of commercial logistics stability.**

After Gate 12, the default direction is transition to MVP, not an automatic third longitudinal research round. A further research round would require a concrete blocker and new Supervisor authorization.
