# MVP LIVE CATALOG 001 — First live ProductFamily curation

Timestamp: 2026-09-14T21:59:40+01:00 (Europe/Lisbon)

Main SHA used: `781654bbc79addde302e93f10e2ddab6cb64ca17`

## Baseline live DB

- ProductFamilies: 0
- Offers: 3
- OfferObservations: 6
- Each fixed Offer had exactly 2 Observations.
- All three Offers were active and unassigned to a ProductFamily.

## Read-only inspection

### 1005012522304882

Title: `7D HIFU Ultrasound RF Skin Care Slimming Device Professional Anti Aging Facial Lifting Salon Beauty Machine`

Product URL: `https://www.aliexpress.com/item/1005012522304882.html`

Latest observation: EUR 713.70; sales 3; commission 7%; search delivery 5 days; detail delivery unavailable; evidence `SEARCH_ONLY`.

Decision: **ASSOCIATE**. The title identifies a 7D HIFU ultrasound/RF machine and is commercially coherent with Offer `1005013116584854`.
### 1005013116584854

Title: `7D HIFU Ultrasound RF Professional Beauty Device for Full Body Slimming Skin Lifting Tightening Anti-Aging Salon Machine`

Product URL: `https://www.aliexpress.com/item/1005013116584854.html`

Latest observation: EUR 226.17; sales 0; commission 7%; search delivery 5 days; detail delivery unavailable; evidence `SEARCH_ONLY`.

Decision: **ASSOCIATE**. The title identifies the same clear 7D HIFU ultrasound/RF product family as Offer `1005012522304882`.

### 1005013002556821

Title: `22D MAX HIFU Beauty Equipment Latest Model Popular Machine for Facial Tightening Slimming Fat Reduction`

Product URL: `https://www.aliexpress.com/item/1005013002556821.html`

Latest observation: EUR 896.24; sales 0; commission 7%; search delivery 5 days; detail delivery unavailable; evidence `SEARCH_ONLY`.

Decision: **DO NOT ASSOCIATE**. It is explicitly a 22D MAX HIFU model, not a 7D HIFU variant. The first live family is intentionally narrower rather than grouping all HIFU equipment together.

## Live write

Created exactly one ProductFamily:

- Name: `Máquinas HIFU 7D`
- Slug: `maquinas-hifu-7d`
- Status: `NEW`
Associated Offers:
- `1005012522304882`
- `1005013116584854`

Excluded Offer:
- `1005013002556821` — kept unassigned because it is a distinct 22D MAX model.

The write was executed atomically with ORM preconditions. No factual Offer field was changed and the complete ordered Observation snapshot remained identical before and after the write.

## Final live DB

- ProductFamilies: 1
- Offers: 3
- OfferObservations: 6
- New Offers: 0
- New Observations: 0

## Storefront verification

Using Django's test client against the real curated data, without public deployment:

- `/` returned HTTP 200 and rendered `Máquinas HIFU 7D`.
- `/products/maquinas-hifu-7d/` returned HTTP 200.
- Both associated 7D Offer titles rendered.
- Latest factual prices rendered as `226,17 EUR` and `713,70 EUR`.
- SEARCH_ONLY logistics rendered conservatively as `Estimativa indicada pela pesquisa: 5 dias`.
- `Vendas indicadas pela fonte` remained the sales label.
- `Ver oferta` remained a disabled button.
- No `/go/` route or affiliate URL was exposed in the rendered CTA.
- Inactive-Offer hiding remains covered by the storefront automated test suite; no live Offer was modified merely to exercise that case.

## Commercial uncertainty

This curation establishes only that the two 7D Offers are sufficiently coherent to share one presentation family. It does not identify a winner, recommended Offer, primary editorial Offer, commercial stability threshold, or guaranteed delivery promise. The 22D MAX Offer remains available for later separate curation if authorized.
