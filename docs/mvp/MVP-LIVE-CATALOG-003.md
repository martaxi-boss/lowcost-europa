# MVP LIVE CATALOG 003 — Import 3 Approved Commercial Families

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Timestamp UTC: `2026-09-15T02:24:41Z`
Main SHA: `695537965bf9845a945c781cc2f7ed17ccf56543`

## Backup health

Latest recurring backup: `lowcost-europa-20260914T224300Z.dump`
Size: 94,230 bytes.
Dump mode: 600. Sidecar mode: 600.
`sha256sum -c`: PASS.
`pg_restore --list`: PASS (custom-format dump).
No additional pre-import backup was required.

## DB before

- ProductFamilies: 2
- Offers: 3
- OfferObservations: 6
- OfferClicks: 1
- None of the three approved product IDs existed.
- None of the three proposed ProductFamily slugs existed.

## Candidate A — Diode Laser

- Product ID: `1005013068402043`
- Fresh search keyword: `diode laser hair removal machine`
- Country/currency: PT/EUR
- Delivery filter: 5 days
- Fresh search valid/invalid: 5 / 0
- Exact product ID refound: NO
- Detail call: NOT PERFORMED after failed exact-ID refind
- Search price: not available for the approved ID in this fresh bounded search
- Detail price: not available
- Affiliate link generated: NO
- Imported: NO
- Failure reason: exact approved product ID was not present in the one-page bounded fresh search; no substitute was selected.
- Proposed ProductFamily was therefore not created.

## Candidate B — Hydro Dermabrasion / Aqua Peel

- Product ID: `1005013069446413`
- Fresh search keyword: `hydrafacial machine`
- Country/currency: PT/EUR
- Delivery filter: 5 days
- Fresh search valid/invalid: 2 / 0
- Exact product ID refound: NO
- Detail call: NOT PERFORMED after failed exact-ID refind
- Search price: not available for the approved ID in this fresh bounded search
- Detail price: not available
- Affiliate link generated: NO
- Imported: NO
- Failure reason: exact approved product ID was not present in the one-page bounded fresh search; no substitute was selected.
- Proposed ProductFamily was therefore not created.

## Candidate C — Cavitation + RF Body Shaping

- Product ID: `1005012828137048`
- Fresh search keyword: `cavitation RF slimming machine`
- Country/currency: PT/EUR
- Delivery filter: 5 days
- Fresh search valid/invalid: 4 / 0
- Exact product ID refound: YES
- Search title: `Slimming Machine Body Shaping Equipment Fat Burning Beauty Device with Cryo Cooling Vacuum Cavitation Lipo RF Light Therapy`
- Detail title: same semantic product identity
- Search price: 1,259.01 EUR
- Detail price: 993.77 EUR
- Detail original price: 1,528.88 EUR
- Commission: 7.0%
- Sales count: 1
- Evaluation: 100.0%
- Search logistics: `Ship to PT in 5 days` / interpreted 5
- Detail logistics: raw NULL / interpreted NULL
- Evidence: SEARCH_ONLY
- Image URL present: YES
- Image host: `ae-pic-a1.aliexpress-media.com`
- Image HTTP status: 200
- Image natural dimensions: 400x400
- Affiliate link generated: YES; URL value intentionally not documented.
- Imported: YES
- ProductFamily: `Máquinas Cavitation + RF Body Shaping`
- Slug: `maquinas-cavitation-rf-body-shaping`
- Status: NEW
- Offer PK: 54
- Offer is_active: True
- Offer is_primary: True
- Observation PK: 60
- Observation destination_country: PT
- Observation availability: UNKNOWN
- Exactly one initial Observation was created.
- Primary means only that this is the sole current editorial Offer in the family; it does not mean winner, best, proven, or verified.

## Atomicity / partial import

Each candidate was evaluated independently. Only Candidate C passed every fresh validation gate, so only Candidate C was persisted in its own `transaction.atomic()` unit.

Candidate A and Candidate B were not imported and did not receive ProductFamilies, Offers, Observations, or affiliate links. No automatic substitute was chosen.

## RF Microneedling hold

Product ID `1005013015748491`: NOT IMPORTED.
Reason: detail normalization failure in MVP DISCOVERY 001.
No revalidation or attempted workaround was performed in this task.

## DB after

- ProductFamilies: 3
- Offers: 4
- OfferObservations: 7
- OfferClicks: 1

Observation counts by Offer:
- `1005012522304882`: 2
- `1005013002556821`: 2
- `1005013116584854`: 2
- `1005012828137048`: 1

## Storefront verification

HTTPS staging remained noindex.
- Homepage: HTTP 200
- Homepage ProductFamily count: 3
- Cavitation family card present: YES
- Cavitation image present: YES
- Cavitation CTA present: YES
- Direct affiliate URL exposed in HTML: NO
- `/products/maquinas-cavitation-rf-body-shaping/`: HTTP 200
- Detail active Offers: 1
- Detail display_offer: `1005012828137048`
- Detail primary: True
- `/go/` was not called.
- OfferClicks remained 1.

## Scope safeguards

- New ProductFamilies: 1
- New Offers: 1
- New OfferObservations: 1
- New OfferClicks: 0
- Migrations: 0
- No code/schema change.
- Public MVP launch remains unauthorized.
