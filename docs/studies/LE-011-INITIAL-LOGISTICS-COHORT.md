# LE-011 — Initial logistics cohort

## Purpose

This is a small internal technical sample for longitudinal observation of professional HIFU offers for Portugal. It is not a public catalog, ranking, winner selection, recommendation, delivery guarantee or commercial stability decision.

A single baseline Observation does not demonstrate longitudinal logistics stability.

## Execution

- Date: 2026-09-13
- Market: PT / EUR
- Target language: EN
- Search query: `HIFU machine`
- Search delivery filter: 5 days
- Maximum cohort size: 3 Offers
- Processing: sequential
- Baseline command mode: one explicit `--commit` execution
- Performance: 7.06 s elapsed; 57,620 KB max RSS

## Pre-live controls

The live PostgreSQL runner was corrected to use the approved environment configuration. The earlier `OperationalError` was an execution-context problem, not schema corruption.

Catalog migrations `0001` and `0002` are applied, `migrate --plan` has no pending catalog work, the two search-logistics columns exist, and `makemigrations --check --dry-run` reports no changes.

The persistence layer also rejects a detail response whose `product_id` differs from the requested ID before affiliate generation, transaction entry or database writes.

Before the baseline, the final three IDs each passed an individual LE-011 dry-run. The exact same three IDs then passed the cohort dry-run with 3 successes, 0 failures, no PostgreSQL error and zero permanent writes.

## Cohort baseline

### 1005012522304882

- Title: `7D HIFU Ultrasound RF Skin Care Slimming Device Professional Anti Aging Facial Lifting Sal...`
- Inclusion reason: product technically relevant to the professional HIFU sample.
- Observed at: 2026-09-13T18:50:52.565040+00:00
- Price: 711.53 EUR
- Evaluation rate: unavailable in the persisted baseline
- Sales count: 3
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence state: SEARCH_ONLY
- Freshness state: FRESH
- Supports <=5 days diagnostic: yes
- History observations: 1
- History span: 0s

### 1005013116584854

- Title: `7D HIFU Ultrasound RF Professional Beauty Device for Full Body Slimming Skin Lifting Tight...`
- Inclusion reason: product technically relevant to the professional HIFU sample.
- Observed at: 2026-09-13T18:50:54.501181+00:00
- Price: 216.81 EUR
- Evaluation rate: unavailable in the persisted baseline
- Sales count: 0
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence state: SEARCH_ONLY
- Freshness state: FRESH
- Supports <=5 days diagnostic: yes
- History observations: 1
- History span: 0s

### 1005013002556821

- Title: `22D MAX HIFU Beauty Equipment Latest Model Popular Machine for Facial Tightening Slimming ...`
- Inclusion reason: product technically relevant to the professional HIFU sample.
- Observed at: 2026-09-13T18:50:55.969873+00:00
- Price: 893.52 EUR
- Evaluation rate: unavailable in the persisted baseline
- Sales count: 0
- Commission rate: 7.0000%
- Search delivery days: 5
- Detail delivery days: NULL
- Evidence state: SEARCH_ONLY
- Freshness state: FRESH
- Supports <=5 days diagnostic: yes
- History observations: 1
- History span: 0s

## Database before / after
Before all dry-runs and the live baseline:

- ProductFamily: 0
- Offer: 0
- OfferObservation: 0

After the cohort dry-run: unchanged at 0 / 0 / 0.

After the single live baseline execution:

- ProductFamily: 0
- Offer: 3
- OfferObservation: 3

No cleanup was performed because these three baseline Observations are intentionally persistent.

## Errors observed during preparation

An earlier diagnostic runner produced PostgreSQL `OperationalError` because it used the wrong local execution context/database configuration. The database schema itself was healthy. The corrected runner produced zero PostgreSQL errors.

One earlier product attempt returned `AliExpressAPIError`. It was treated as an external per-candidate failure, not retried in a loop, and no Observation was invented. Later controlled runs succeeded for the final cohort.

## Interpretation

For all three baseline Observations the source search reported 5 delivery days, while product detail did not provide an interpreted delivery-day value. The persisted provenance therefore remains search=5 and detail=NULL, with no fallback or effective delivery value.

The resulting `SEARCH_ONLY` / `FRESH` diagnostics are internal evidence facts only. They do not authorize a customer-facing delivery promise.

A single Observation baseline does not demonstrate longitudinal logistics stability.
