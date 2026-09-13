# LE-006 study — HIFU search precision and delivery filter

Date: 2026-09-13. Market: PT. Currency: EUR. Target language: EN. Search delivery filter: 5 days. Requested limit: 10 per manual run. Mode: dry-run.

This study records source observations only. `delivery_days=5` is a search filter sent to AliExpress and is not a delivery guarantee. Search and detail values are kept separate and no data fusion is performed.

## Study A — `HIFU machine`

### Results received

Search results 8; unique 8; duplicates 0; invalid IDs 0. Attempted 8; successful 8; failed 0. Projected Offers 8 and Observations 8; dry-run kept DB at Offers=0 / Observations=0.

### Sanitized titles

| product_id | title (truncated) | price | currency | eval % | sales | commission % | search days | detail days | outcome |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| 1005009117420765 | 7D HIFU Machine Ultrasound Machine RF Radio Frequency EMS Skin Care | 479.44 | EUR | 94.7 | 55 | 7.0 | 5 | — | success |
| 1005011594450687 | New Mini HIFU Ultrasonic Machine EMS Micro Current Facial Beauty | 42.86 | EUR | 100.0 | 52 | 7.0 | 5 | — | success |
| 1005013116584854 | 7D HIFU Ultrasound RF Professional Beauty Device for Full Body | 266.68 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005013004139522 | 22D MAX Professional HIFU Beauty Machine - Face Lift Body Slimming | 242.43 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005013002556821 | 22D MAX HIFU Beauty Equipment Latest Model Popular Machine | 1099.03 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005012895303549 | 7D HIFU SMAS Lifting Machine Anti-Aging Wrinkle Removal | 1790.81 | EUR | 100.0 | 3 | 7.0 | 5 | — | success |
| 1005012433133617 | New 3.0 Version MVS Anti Aging Machine with RF EMS HIFU | 3845.47 | EUR | 100.0 | 4 | 7.0 | 5 | — | success |
| 1005012522304882 | 7D HIFU Ultrasound RF Skin Care Slimming Device Professional | 442.81 | EUR | — | 3 | 7.0 | 5 | — | success |

### Data coverage

Detail: price 8/8, currency 8/8, evaluation rate 4/8, sales 8/8, commission 8/8.

### Search logistics

Raw shipping 8/8; interpreted delivery days 8/8; <=5 days 8.

### Detail logistics

Raw shipping 0/8; interpreted delivery days 0/8; <=5 days 0.

### Search/detail mismatches

8. In every successful candidate search reported 5 days while detail returned no interpretable delivery days.

### Errors / rate limits

No errors or confirmed rate limits.

### Performance

15.20 s; max RSS 57,628 KB. Available memory about 350 MB before and 354 MB after; swap 270 MB before/after; load approximately 0.06/0.07/0.02 before and 0.01/0.05/0.01 after.

### Interpretation factual

The observed titles are HIFU/beauty-equipment oriented and do not show the Hanfu/cosplay ambiguity seen with the plain `HIFU` query in LE-005. This is human-review evidence, not a relevance score.

## Study B — `7D HIFU machine`

### Results received

Search results 9; unique 9; duplicates 0; invalid IDs 0. Attempted 9; successful 8; failed 1. Projected Offers 8 and Observations 8; dry-run kept DB at Offers=0 / Observations=0.

### Sanitized titles

| product_id | title (truncated) | price | currency | eval % | sales | commission % | search days | detail days | outcome |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| 1005012775097611 | Professional 22D MAX HIFU Beauty Equipment Machine | 734.13 | EUR | — | 14 | 7.0 | 5 | — | success |
| 1005009117420765 | 7D HIFU Machine Ultrasound Machine RF Radio Frequency EMS | 479.44 | EUR | 94.7 | 55 | 7.0 | 5 | — | success |
| 1005013116584854 | 7D HIFU Ultrasound RF Professional Beauty Device | 266.68 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005003049988859 | MINI Hifu 2.0 Machine Ultrasound Machine RF EMS Microcurrent | 44.59 | EUR | 100.0 | 84 | 7.0 | 5 | — | success |
| 1005009238480705 | 7D HIFU Machine facial/body instrument | 138.17 | EUR | 100.0 | 19 | 7.0 | 5 | — | external_error |
| 1005012775803675 | Beauty Salon Equipment 360MAX 25D HIFU 3 In 1 | 391.20 | EUR | 100.0 | 1 | 7.0 | 5 | — | success |
| 1005012895303549 | 7D HIFU SMAS Lifting Machine Anti-Aging | 1790.81 | EUR | 100.0 | 3 | 7.0 | 5 | — | success |
| 1005012838813120 | Beauty Salon 7D HIFU SPA Machine Body Sculpting | 155.16 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005012522304882 | 7D HIFU Ultrasound RF Skin Care Slimming Device | 442.81 | EUR | — | 3 | 7.0 | 5 | — | success |

### Data coverage

Detail among 8 successes: price 8/8, currency 8/8, evaluation rate 4/8, sales 8/8, commission 8/8.

### Search logistics

Raw shipping 9/9; interpreted delivery days 9/9; <=5 days 9.

### Detail logistics

Raw shipping 0/8; interpreted delivery days 0/8; <=5 days 0.

### Search/detail mismatches

8 successful details mismatched: search reported 5 days and detail returned no interpretable delivery days. The failed candidate has no detail value to compare and is not counted as a mismatch.

### Errors / rate limits

One candidate returned a sanitized `AliExpressAPIError`; the rest of the batch continued. The error subtype was intentionally not retained in output, so this study does not claim that it was an `ApiCallLimit`. No rate limit was confirmed from the retained evidence.

### Performance

16.71 s; max RSS 57,500 KB. Available memory about 354 MB before and 352 MB after; swap 270 MB before/after; load approximately 0.01/0.05/0.01 before and 0.01/0.03/0.00 after.

### Interpretation factual

Observed titles are HIFU/beauty-equipment oriented. One external product-detail/API failure did not abort successful candidates.

## Study C — `professional HIFU machine`

### Results received

Search results 8; unique 8; duplicates 0; invalid IDs 0. Attempted 8; successful 8; failed 0. Projected Offers 8 and Observations 8; dry-run kept DB at Offers=0 / Observations=0.

### Sanitized titles

| product_id | title (truncated) | price | currency | eval % | sales | commission % | search days | detail days | outcome |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| 1005012476776786 | Professional Beauty Equipment Machine 25D HIFU 360MAX | 1186.10 | EUR | 100.0 | 9 | 7.0 | 5 | — | success |
| 1005012775097611 | Professional 22D MAX HIFU Beauty Equipment Machine | 734.13 | EUR | — | 14 | 7.0 | 5 | — | success |
| 1005009925120797 | 22D MAX HIFU Machine Professional Ultrasonic Lifting Equipment | 932.24 | EUR | 96.4 | 9 | 7.0 | 5 | — | success |
| 1005013116584854 | 7D HIFU Ultrasound RF Professional Beauty Device | 266.68 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005013004139522 | 22D MAX Professional HIFU Beauty Machine | 242.43 | EUR | — | 0 | 7.0 | 5 | — | success |
| 1005012619444699 | Professional 22D MAX HIFU Beauty Equipment Machine | 734.13 | EUR | 100.0 | 36 | 7.0 | 5 | — | success |
| 1005012518438669 | 360MAX 25D HIFU 3 In 1 Non Invasive Beauty Equipment | 249.70 | EUR | 100.0 | 6 | 7.0 | 5 | — | success |
| 1005012522304882 | 7D HIFU Ultrasound RF Skin Care Slimming Device Professional | 442.81 | EUR | — | 3 | 7.0 | 5 | — | success |

### Data coverage

Detail: price 8/8, currency 8/8, evaluation rate 4/8, sales 8/8, commission 8/8.

### Search logistics

Raw shipping 8/8; interpreted delivery days 8/8; <=5 days 8.

### Detail logistics

Raw shipping 0/8; interpreted delivery days 0/8; <=5 days 0.

### Search/detail mismatches

8. Every successful candidate had search=5 days and detail=None.

### Errors / rate limits

No errors or confirmed rate limits.

### Performance

14.99 s; max RSS 57,748 KB. Available memory about 352 MB before and 363 MB after; swap 270 MB before/after; load approximately 0.01/0.03/0.00 before and 0.00/0.01/0.00 after.

### Interpretation factual

Observed titles are professional HIFU/beauty-equipment oriented. Search supplied a normalized five-day value for all candidates; detail did not supply interpretable logistics for the same successful product IDs.

## Cross-study factual findings

Across the three separate manual searches, 25 search candidates were received and all 25 had normalized search `delivery_days=5`. There were 24 successful detail operations; all 24 returned `delivery_days=None`, creating 24 search/detail mismatches. One candidate in Study B failed with a sanitized external API error.

The specific keywords removed the obvious Hanfu/cosplay semantic noise observed with plain `HIFU` in LE-005. No automatic relevance percentage, score, ranking or winner selection was calculated.

The source therefore demonstrated a useful delivery filter at search level in these observations, but detail did not reproduce that logistics evidence. No policy is introduced here to merge or promote search logistics into persisted observations. A future provenance decision is required before any customer-facing delivery claim.
