# CATALOG STRUCTURE 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Scope

Phase 1 prepares the catalog data model for a future storefront without changing the current public read path.

The invariant remains: one real partner listing is one `Offer`, identified uniquely by `source + external_product_id`. A single Offer may be editorially placed in more than one `ProductFamily` without duplicating the Offer or its observation history.

No AliExpress live operations, discovery, imports, new ProductFamilies, storefront redesign, indexing change, or staging database migration were performed in this phase.

## Model design

`OfferFamilyPlacement` is the explicit editorial association between an existing `Offer` and a `ProductFamily`.

Fields:
- `offer`
- `product_family`
- `selection_position`
- `display_order`
- `selection_reason`
- `created_at`
- `updated_at`

A placement means only that the Offer was editorially selected to appear in that family. It does not mean winner, best seller, highest commission, automatic recommendation, or algorithmic ranking.

## Editorial selection semantics

`selection_position` is nullable.

- `1..5` means the placement belongs to the future "Seleções Lowcost Europa" block.
- `NULL` means a normal selected Offer outside that highlighted block.
- Position `1` is an editorial ordering position only; it is not a product ranking.

`display_order` is a simple non-negative editorial ordering field for normal placements. It is not derived from sales, commission, price, ratings, or any scoring system.

`selection_reason` is optional editorial text. This phase does not auto-generate commercial claims.

## Dedicated versus combo

`Offer.equipment_type` adds the intrinsic classification:

- `UNKNOWN` — not yet validated;
- `DEDICATED` — mainly oriented to one technology/function;
- `COMBO` — combines relevant technologies/functions.

The default is `UNKNOWN`. No value is inferred from the product title in this phase.

## Database constraints

The database enforces:

- one placement per `offer + product_family` pair;
- `selection_position` is either `NULL` or between 1 and 5;
- one non-null selection position per ProductFamily;
- `equipment_type` is one of `UNKNOWN`, `DEDICATED`, or `COMBO`.

The product identity constraint on `Offer(source, external_product_id)` remains unchanged.

No hard database limit of 20 placements per family was added; that future number remains an editorial/UX target rather than a structural rule.

## Transitional legacy fields

`Offer.product_family` and `Offer.is_primary` are deliberately preserved. The existing storefront continues to read its current model and therefore remains backward compatible during this phase.

A later Supervisor-approved phase may migrate the public read path to placements. This phase does not do that.

## Migrations and backfill

`0005_offerfamilyplacement_offer_equipment_type_and_more` contains the schema changes.

`0006_backfill_offer_family_placements` creates one placement for every existing Offer that has a legacy `product_family`.

Backfill rules:

- placement family = existing `Offer.product_family`;
- legacy `is_primary=True` -> `selection_position=1`;
- legacy non-primary -> `selection_position=NULL`;
- `display_order=0`;
- `selection_reason` blank;
- `equipment_type` remains the schema default `UNKNOWN`.

The migration does not change Offer identity/source/title/image/product URL/affiliate URL/active state, ProductFamily data, OfferObservation, or OfferClick.

The data backfill is intentionally forward-only. Reversing `0006` uses a no-op reverse and does not delete existing placements, because the migration cannot safely distinguish historical backfill rows from later editorial placements.

An isolated clone of the current staging database was migrated successfully. Counts remained `5 ProductFamilies / 6 Offers / 15 OfferObservations / 35 OfferClicks`, and exactly `6 OfferFamilyPlacement` rows were produced with selection positions `[1, NULL, 1, 1, 1, 1]`. The temporary database was then dropped.

## Admin

Django Admin now exposes `equipment_type` on Offer and a simple `OfferFamilyPlacement` interface showing Offer, ProductFamily, selection position, display order, selection reason, and the Offer equipment type through filters.

The interface remains manual/editorial. Django Admin permissions allow creating, editing, and deleting an `OfferFamilyPlacement`; deleting a placement removes only the editorial relation. The `Offer` and `ProductFamily` foreign keys remain protected and OfferObservation/OfferClick history is not deleted. No automated scoring or ranking was added.

## Validation

New model/backfill/Admin tests cover multi-family placement, duplicate prevention, valid and invalid selection positions, unique highlighted positions per family, repeated NULL positions, authorized equipment types, six-row backfill, history preservation, safe no-op reverse behavior, Admin rendering, and placement deletion without deleting related catalog/history records.

The complete project test suite passes with 240 tests. `python manage.py check`, migration drift check, Ruff, `git diff --check`, and `pip check` also pass.

The current storefront regression suite remains green and continues to instantiate no AliExpress client during visitor requests. No AliExpress live operation was made during this phase.

## Deployment status

The migrations are versioned only on the review branch. They were **not** applied to the staging/live database. Staging therefore remains on the existing schema until PR review, merge, and a later explicit Supervisor deployment approval.

Public noindex state and launch authorization are unchanged.
