# STOREFRONT PLACEMENT MIGRATION 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Status: READY FOR SUPERVISOR AUDIT

Base: `f23e2866f2c412095373c057a92dbb27ea5a1a58`

## Source of truth

Before this phase, the public storefront read Offer membership from the legacy `Offer.product_family` relation and used `Offer.is_primary` to choose representative Offers.

After this phase, public catalog membership is determined only by `OfferFamilyPlacement` for active Offers in non-retired ProductFamilies.

The legacy fields remain in the model for internal/historical compatibility but are not the public catalog source of truth.

## Read path

The storefront prefetches:

`ProductFamily -> OfferFamilyPlacement -> Offer -> latest OfferObservation`.

This avoids per-Offer queries inside template loops and keeps the existing architecture small.

## Family detail grouping

Placements with `selection_position IS NOT NULL` appear under **Seleções Lowcost Europa**, ordered by ascending `selection_position`.

Placements with `selection_position IS NULL` appear under **Outras ofertas selecionadas**, ordered by `display_order`, then deterministic Offer recency/PK fallback.

Selection position is described as editorial organization, not ranking, superiority or an automated recommendation.

A non-empty `selection_reason` may appear as **Porque está aqui**. Empty reasons render no empty block.

## Homepage representative Offer

The family card uses the first non-null `selection_position` placement when available. Otherwise it uses the first normal placement by editorial ordering. A family with no placements remains visible with the existing empty state.

`Offer.is_primary` is not consulted for the public representative Offer.

## Multi-family and retired behavior

One Offer can be published in multiple ProductFamilies through multiple placements without duplicating the Offer, its external product identity, observations or click history.

A RETIRED family is excluded from the homepage. Its historical detail URL may still return HTTP 200, but public Offer groups are empty even if historical placements exist.

## CTA and visitor API behavior

CTA text remains **Ver oferta no parceiro**. The page continues to state that the visitor leaves Lowcost Europa, purchase/payment happen with the external partner, and affiliate commission may exist.

`/go/<offer_id>/` still records the minimal `OfferClick` and redirects to the persisted affiliate URL. Eligibility now requires an active Offer with at least one placement in a non-retired family. It does not generate an affiliate URL and makes no API call.

Homepage, family detail and `/go/` remain zero-AliExpress request paths.

## Validation

The dedicated storefront suite passes 57/57 tests. The full project suite passes 257/257 tests.

Validation gate:

- `python manage.py check`: PASS
- `makemigrations --check --dry-run`: No changes detected
- `migrate --plan`: No planned migration operations
- Ruff: PASS
- `git diff --check`: PASS
- `pip check`: no broken requirements

Read-only smoke against the current catalog confirmed eight active families in `display_order`, HIFU with Offer 51 and 53 in selections and Offer 52 in other offers, four empty families returning HTTP 200, transparent CTA copy, and OfferClick count unchanged at 41.

No live AliExpress call, schema migration, catalog data mutation or staging deployment was performed by this phase.
