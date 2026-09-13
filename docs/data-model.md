# Lowcost Europa — Minimal catalog data model

LE-003 introduces the smallest relational model needed for permanent product families, replaceable external offers and factual historical observations.

## Relationship

```text
ProductFamily
    | 0..N
    v
  Offer
    | 0..N
    v
OfferObservation
```

`Offer.product_family` is nullable because a future discovery process may find a candidate before it is assigned to a family. Deletion is protected when a family already has offers. `OfferObservation.offer` is also protected so historical facts cannot disappear through cascade deletion.

## ProductFamily

`ProductFamily` is a permanent Lowcost Europa entity with stable unique `slug`, name and lifecycle status: NEW, TESTING, VERIFIED, PROVEN, WINNER, OBSERVATION or RETIRED. Status transitions are not automated in LE-003. A family is not deleted merely because external offers become inactive; normal retirement is represented by `RETIRED`.

## Offer

`Offer` represents one concrete external listing. `source` is currently `ALIEXPRESS` using simple choices. The pair `source + external_product_id` is unique and the external ID cannot be blank. An Offer may temporarily have no ProductFamily, may later be linked to one, and remains stored when `is_active=False`.

Current URLs/title are lightweight current metadata only. No Seller, SKU/variant model or raw API payload is stored.

## OfferObservation

`OfferObservation` records what was factually observed at one moment. It is history, not scoring and not a recommendation.

Money uses `DecimalField`; missing prices stay `NULL`. `evaluation_rate_percent` is a source percentage such as `96.5` meaning 96.5%, never stars. `commission_rate` is the percentage/rate supplied by the source and is nullable; LE-003 does not calculate revenue.

`ship_to_days_raw` preserves the source logistics text. `delivery_days` is nullable and is only populated when the integration layer interpreted a day count safely. The <=5-day commercial selection rule is not applied here.

`destination_country` is a simple ISO alpha-2 value when known. `availability` distinguishes UNKNOWN, AVAILABLE and UNAVAILABLE so missing information is not misrepresented as confirmed unavailability.

A single composite index on Offer + descending `observed_at` supports normal historical lookups without redundant indexing.

## History accumulation

Future tasks may create new observations over time for the same Offer. They must append factual snapshots rather than overwrite history. LE-003 deliberately does not connect the AliExpress API to these models and creates no importer, discovery command, cron job, scoring or frontend.
