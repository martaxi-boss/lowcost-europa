# MVP LIVE CATALOG 002 — SECOND REAL PRODUCTFAMILY

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Main base SHA: `2add105e2fdfaa671b1ee10baddf270cf117f994`

## DB before

- ProductFamilies: 1
- Offers: 3
- OfferObservations: 6
- OfferClicks: 1

## Existing Offer inspection

External product ID: `1005013002556821`

Title: `22D MAX HIFU Beauty Equipment Latest Model Popular Machine for Facial Tightening Slimming Fat Reduction`

Before curation:
- product_family: NULL
- is_active: true
- is_primary: false
- affiliate_url: present
- image_url: present
Latest observation:
- price: 896.24 EUR
- commission_rate: 7.0000%
- sales_count: 0
- search_delivery_days: 5
- delivery_days: NULL
- evidence: SEARCH_ONLY (derived from search=5/detail=NULL)

Commercial interpretation: the title explicitly identifies a 22D MAX HIFU beauty machine for facial tightening/slimming/fat reduction. It is materially distinct from the existing 7D HIFU family and does not read as an accessory, cartridge, spare part, consumable, or different technology.

## New ProductFamily

- name: `Máquinas HIFU 22D MAX`
- slug: `maquinas-hifu-22d-max`
- status: `NEW`

Only `1005013002556821` was associated with this family.

Because it is the only active Offer in the family, `1005013002556821.is_primary` was set to `True` as an explicit editorial display choice. This does not mean winner, best product, best offer, proven, or verified.
## Image quality

The factual image URL is hosted on `ae-pic-a1.aliexpress-media.com`.

Chromium validation:
- HTTP status: 200
- natural dimensions: 529x529

No replacement, mirroring, download, or live data edit was performed.

## DB after

- ProductFamilies: 2
- Offers: 3
- OfferObservations: 6
- OfferClicks: 1
- `1005013002556821.product_family`: `maquinas-hifu-22d-max`
- `1005013002556821.is_primary`: true

The two 7D Offers remained associated with `maquinas-hifu-7d`.
No Offer, Observation, or OfferClick was created.
No AliExpress live call or `/go/` request occurred.
## Storefront verification

Read-only Django client validation against the live DB:
- homepage: HTTP 200
- ProductFamily cards rendered: 2
- both `Máquinas HIFU 7D` and `Máquinas HIFU 22D MAX` present
- `/products/maquinas-hifu-22d-max/`: HTTP 200
- 22D detail Offer cards rendered: 1
- factual 22D title present
- display_offer resolves to `1005013002556821`
- OfferClicks remained exactly 1

The current SEARCH_ONLY logistics wording remains conservative; no 5-day guarantee is inferred.

Public MVP launch remains unauthorized and staging remains noindex.
