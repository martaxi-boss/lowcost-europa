# MVP LIVE PRIMARY 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Date: 2026-09-14 Europe/Lisbon
Main SHA: `bf653099b61fcee647796665292f275a2d8d24b6`

## Live DB before

- ProductFamilies: 1
- Offers: 3
- OfferObservations: 6
- `catalog.0003_offer_is_primary_and_more`: not applied
- `1005012522304882`: family `maquinas-hifu-7d`, active, not primary
- `1005013116584854`: family `maquinas-hifu-7d`, active, not primary
- `1005013002556821`: no ProductFamily, not primary

## Pre-migration backup

A PostgreSQL custom-format snapshot was created outside the repository before the schema change.

- size: 42,805 bytes
- SHA256: `277c515d1c45963b41eb5ec31d78b8ba2b8baee9c4cd4a4a00874aa6b583f8a6`
- permissions: restricted (`600`)
- backup contained data and was non-empty

## Migration and primary selection

`catalog.0003_offer_is_primary_and_more` was the only pending catalog migration and applied successfully.
Post-migration counts remained 1 ProductFamily / 3 Offers / 6 OfferObservations, and factual Offer/Observation fingerprints were unchanged.

The Supervisor-authorized initial editorial primary is `1005012522304882`.
Rationale: both 7D Offers have observed commission 7% and SEARCH_ONLY delivery evidence of 5 days; this Offer has observed sales_count 3 versus 0 for `1005013116584854`.
This is an editorial, reversible presentation choice, not a winner, proven result, verified recommendation, score, or ranking.

Final primary state:
- `1005012522304882`: primary = true
- `1005013116584854`: primary = false
- `1005013002556821`: primary = false, ProductFamily = NULL

No Offer or Observation was created or modified beyond the single authorized `is_primary` field change.

## Storefront verification

Without public deployment, Django test client against live curated data confirmed:
- `/` returned 200 and `display_offer` is `1005012522304882`;
- `/products/maquinas-hifu-7d/` returned 200;
- detail order is `1005012522304882`, then `1005013116584854`;
- `Estimativa indicada pela pesquisa: 5 dias` remains visible;
- `Vendas indicadas pela fonte` remains visible;
- CTA `Ver oferta` remains disabled;
- affiliate URL is not exposed in rendered HTML.

No `/go/`, click tracking, affiliate redirect, public deployment, new Offer, new Observation, scoring, ranking, scheduler, or LE-013 work was performed.
