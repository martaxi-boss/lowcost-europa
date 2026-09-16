# LOWCOST EUROPA — ARQUITETURA DO SITE

Status: DATA CAPABILITY AUDIT 001 — READY FOR SUPERVISOR AUDIT
Repository baseline: `6dabc5955c5cb2c0df4088c2a8c63b870b1a6801`
Audit scope: architecture + seller / European-origin data capability; no application changes.

## 1. Objetivo comercial

Lowcost Europa is an affiliate storefront. It selects, organizes and compares external offers; it has no own checkout, does not process the partner purchase, and redirects the visitor to the partner platform.

The strategic objective is to find credible offers that use European origin, shipping or warehouses when that fact can be technically evidenced. The commercial objective is not itself evidence: a short delivery estimate to Portugal does not prove European origin, a European warehouse, European stock or customs treatment.

Public claims must therefore follow factual provenance. Missing evidence stays unknown.

## 2. Arquitetura técnica

The application is a Django 5.2 LTS modular monolith on Python 3.12 with PostgreSQL 16. The current staging path is HTTPS Nginx -> Gunicorn -> Django production settings -> PostgreSQL, managed by systemd on the existing DigitalOcean Droplet.

The initial server remains 1 vCPU / 1 GB RAM / 25 GB. Current architecture does not require Redis, Celery, Kubernetes, microservices, a second Droplet or a separate SPA. Scaling requires measured need and Supervisor approval.

Staging remains fail-closed for indexing: `DJANGO_PUBLIC_INDEXING_ENABLED=false` and `DJANGO_PUBLIC_SITE_URL=`. Public launch is not authorized.
## 3. Modelo de catálogo

`ProductFamily` is the permanent editorial category entity. `Offer` represents one concrete external listing and is unique by `source + external_product_id`. `OfferObservation` is a temporal factual snapshot. `OfferFamilyPlacement` is the editorial many-family presentation relation. `OfferClick` stores only a minimal outbound click event.

`Offer` currently has no Seller, Store, SKU/variant, Warehouse or raw-response model. `OfferObservation` stores price, original price, currency, evaluation percentage, sales count, commission, destination country, search/detail logistics and a conservative availability enum.

Current `Offer.equipment_type` states are `UNKNOWN`, `DEDICATED` and `COMBO`. No equipment type is inferred from a title when evidence is insufficient.

## 4. Arquitetura multi-family

`OfferFamilyPlacement` is the public source of truth for family membership. One Offer can appear in multiple ProductFamilies without duplicating the Offer, its external identity, observations or click history.

`selection_position` values 1..5 identify the editorial `Seleções Lowcost Europa` block. A NULL position identifies `Outras ofertas selecionadas`. These positions are editorial ordering only and are not an objective ranking, seller score or product score.

## 5. Arquitetura do storefront

The homepage exposes the eight active database-driven categories. Family detail pages separate `Seleções Lowcost Europa` from `Outras ofertas selecionadas`, and empty families remain visible with a preparation state.

Offer CTAs use the internal `/go/<offer_id>/` route. The HTML does not expose raw affiliate destination URLs. `/go/` records one minimal `OfferClick` and redirects to the affiliate URL already persisted on the Offer; it does not call AliExpress.
## 6. Arquitetura AliExpress

All external AliExpress traffic is centralized in `AliExpressClient`. Supported operations are category retrieval, SEARCH (`aliexpress.affiliate.product.query`), DETAIL (`aliexpress.affiliate.productdetail.get`) and affiliate-link generation. Business services do not implement signing or direct HTTP independently.

`normalize_product()` converts supported raw fields into `AliExpressProduct`. The current normalized type contains product identity, title, image/product URL, price, currency, original price, evaluation percentage, sales count, commission, raw/interpreted delivery evidence, destination country and optional affiliate URL.

Persistence separates current Offer metadata from temporal OfferObservation facts. Search logistics and detail logistics retain separate provenance. The storefront is isolated from AliExpress and reads PostgreSQL only.

## 7. Evidência logística

The project explicitly distinguishes search and detail evidence. Derived states are `UNKNOWN`, `SEARCH_ONLY`, `DETAIL_ONLY`, `CONSISTENT` and `CONFLICT`.

`SEARCH_ONLY` means only search supplied interpretable days; `DETAIL_ONLY` means only detail did; `CONSISTENT` means both supplied the same value; `CONFLICT` means both exist and differ. No precedence or synthetic effective delivery value exists.

Freshness is evaluated separately as `FRESH`, `STALE` or `FUTURE`. The current 24-hour window is diagnostic rather than a public commercial promise.

`destination_country` is request/context provenance for the market being queried. It is not shipment origin. Delivery-day evidence is temporal and destination-dependent.

## 8. Limitação atual europeia

A delivery estimate to Portugal is not evidence that the item ships from Portugal, Spain, the EU or a European warehouse. Likewise, destination country, price, title, sales count or commission cannot be used to infer origin or warehouse.

The current integration therefore does not authorize claims such as `Armazém europeu`, `Stock europeu`, `Enviado da Europa`, `Enviado de Espanha`, `Sem alfândega` or `Entrega garantida`.
## 9. Seller / Store capability audit

Static audit found no `seller_id`, `store_id`, `seller_name` or `store_name` field in `Offer`, `OfferObservation`, `AliExpressProduct`, `normalize_product()` or the current AliExpress client mapping.

A bounded live diagnostic used three existing catalog product IDs through the central `AliExpressClient` DETAIL operation. The observed DETAIL result structures did not expose seller/store fields. No raw payload was retained.

One authorized bounded SEARCH for Portugal with `page_size=5` also did not expose seller/store fields in the observed result structures. This establishes that seller/store data is **not available through the current implemented and observed capability**. It does not claim that no AliExpress API product or future endpoint can ever expose seller data.

No seller reputation, certification, verification or trust score can be derived from product evaluation rate or sales count. Those are product/source metrics, not seller identity or seller reputation.

## 10. European origin / warehouse capability audit

Static audit found no `ship_from_country`, `origin_country`, `warehouse`, `warehouse_id` or `local_stock` field in the current catalog model, normalized product type or normalizer mapping.

The same three live DETAIL probes and one bounded SEARCH did not expose ship-from, origin, warehouse or stock fields in the observed result structures. Therefore European origin, warehouse identity and local stock are **not available through the current implemented and observed capability**.

`availability` exists as an `OfferObservation` enum, but current AliExpress persistence writes it as `UNKNOWN`; no current normalized/API mapping supplies a factual availability value. Availability capability is therefore partial at the data-model level but not source-backed today.

If future official source data shows origin, warehouse or inventory varying by SKU, variant, destination or time, it must be treated as observation/provenance data rather than promoted automatically to a permanent Offer fact.
## 11. Capability Matrix

Status semantics used here: `CONFIRMED` means the current system has factual source/provenance support; `PARTIAL` means some system support exists but source coverage is incomplete; `NOT AVAILABLE` means absent from current model/normalization/API mapping and absent from the bounded observed payload structures; `UNKNOWN` means evidence is insufficient to classify.

| Campo | Estado | Fonte / endpoint | Já normalizado? | Proveniência | Temporal? | Persistível? | Publicável? |
|---|---|---|---|---|---|---|---|
| `seller_id` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Unknown | No current field; conditional future Offer field only if stable | No |
| `store_id` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Unknown | No current field | No |
| `seller_name` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Unknown | No current field; conditional future Offer field only if factual/stable | No |
| `store_name` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Unknown | No current field | No |
| `ship_from_country` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Treat as temporal/variant-dependent if ever sourced | No current field | No |
| `origin_country` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Unknown; do not assume permanence | No current field | No |
| `warehouse` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Treat as temporal/variant-dependent if ever sourced | No current field | No |
| `warehouse_id` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Treat as temporal/variant-dependent if ever sourced | No current field | No |
| `local_stock` | NOT AVAILABLE | No current source observed in SEARCH/DETAIL | No | None established | Yes if ever sourced | No current field | No |
| `availability` | PARTIAL | Catalog schema only; persistence currently writes `UNKNOWN` | No source mapping | Observation field without factual upstream value | Yes | Yes, already on OfferObservation | No factual claim while UNKNOWN |
| `destination_country` | CONFIRMED | Client request context for SEARCH/DETAIL | Yes | Caller/request market (`PT` in current flows), not response origin | Yes/request-specific | Yes, OfferObservation | Only as destination context; never as origin |
| `search_delivery_days` | CONFIRMED | SEARCH `ship_to_days`/supported equivalent | Yes | Search endpoint; historically observed and persisted separately | Yes | Yes, OfferObservation | Only conservative observed-estimate wording, never guarantee/origin |
| `detail_delivery_days` | PARTIAL | DETAIL `ship_to_days`/supported equivalent when present | Yes | Detail endpoint; optional and repeatedly absent in observed cohorts | Yes | Yes, OfferObservation | Only when factually present, with conservative wording |

The classifications above are capability statements for this repository and the bounded official API observations, not universal claims about every AliExpress API product or future endpoint.
## 12. Modelo mínimo proposto

No schema change is recommended **now** because the required seller/origin/warehouse source data is not currently established. The following is a conditional design only, not an implementation decision.

If a future official endpoint provides a stable factual seller identity consistently associated with an Offer, minimally evaluate `seller_external_id` and `seller_name` on Offer (or a dedicated Seller relation only when reuse/integrity actually justifies an entity).

Do not create a Store or Warehouse entity merely to model an unproven concept. If future origin/warehouse/stock data varies by SKU, variant, destination or time, prefer observation-level provenance or a variant-specific observation model rather than a permanent Offer field.

Do not add `stock` while the source does not provide factual inventory. Do not populate seller/origin/warehouse fields from title, price or delivery speed.

`OfferFamilyPlacement` remains the multi-family presentation source of truth and requires no change for seller/origin capability.

Current equipment types remain `UNKNOWN`, `DEDICATED` and `COMBO`. A future `MULTIFUNCTION` distinction may be useful only if it has a stable semantic difference from `COMBO` and can be supported by structured source specifications or explicit human-validated factual evidence. Title text alone is insufficient. No `MULTIFUNCTION` state is added in this audit.

## 13. Claims públicos permitidos/proibidos

Permitted when backed by the stored observation include factual observed price, source sales/evaluation labels, conservative observed logistics wording, external-partner purchase disclosure and affiliate disclosure.

A search/detail delivery value may be described only with its provenance and uncertainty. It must not be transformed into a guarantee or origin assertion.

Without new source evidence, prohibited claims include European warehouse/stock, shipment from Europe/Spain/Portugal, customs-free status, guaranteed delivery, seller certification, guaranteed seller or officially verified seller.

Seller trust/reputation must not be synthesized from product evaluation, sales count, commission, price or delivery time. No seller score or trust score exists.
## 14. API safety

All AliExpress operations remain serialized by local `flock`, with shared cadence, bounded retries, Retry-After handling, exponential backoff, jitter, consecutive-429 breaker, batch abort and safe metrics. No API safety configuration was changed in this audit.

This audit executed only the minimum authorized read-only diagnostic: three DETAIL operations for existing product IDs, followed by one bounded SEARCH for PT with `page_size=5` because DETAIL did not resolve the seller/origin gaps.

Live diagnostic totals: 4 logical operations, 4 HTTP attempts, 0 retries, 0 HTTP 429, 0 HTTP 5xx, 0 transport failures, rate-limit abort NO, aggregate operation duration 4862 ms, aggregate lock wait 0 ms. No affiliate-link generation, category call, auto-pagination or `/go/` request occurred.

No raw payload, signed request, credential value, private integration secret, tracking identifier value, authentication header or raw affiliate URL was written to this document or repository. Temporary diagnostic scripts were outside the repository and removed.

## 15. Infraestrutura e scaling

The existing low-cost DigitalOcean Droplet remains the correct MVP target while the business is being validated. Django, PostgreSQL, Gunicorn and Nginx currently coexist without a demonstrated requirement for distributed infrastructure.

Do not add Redis, Celery, managed database, Kubernetes, microservices, a second Droplet or other paid infrastructure by convention. Scale only when measured traffic, CPU, RAM, latency, background-work contention, database growth or revenue justifies it.

## GATE 1 — RESULTADO DA DATA CAPABILITY AUDIT

`OUTCOME: CURRENT OFFICIAL IMPLEMENTED CAPABILITY INSUFFICIENT FOR EUROPEAN-ORIGIN PROOF`

The audit demonstrated that, across the currently implemented official endpoints and the bounded live sample authorized for this phase, seller identity, store identity, ship-from country, origin country, warehouse / warehouse ID and local stock were not found.

This does **not** abandon the European objective of Lowcost Europa. It means only that the project does not yet have a sufficiently factual source to publish European-origin or European-warehouse claims. These findings remain scoped to the **current implemented and bounded observed capability** and are not universal claims about the whole AliExpress platform or future official capabilities.

The fact that the current integration cannot prove European origin does **not** redefine the project as simple selection by delivery time. The commercial priority remains: `EUROPEAN ORIGIN / EUROPEAN WAREHOUSE WHEN FACTUALLY PROVABLE`. Delivery estimates to Portugal remain only complementary logistics signals and never proof of origin.

## AUTHORIZED EVIDENCE SOURCE PATH

### A. Official AliExpress API / Affiliate API capability research

A future, separately authorized investigation may review only official documentation, endpoints or capabilities officially available to the account/integrator to determine whether seller/store identity, SKU/variant, ship-from, warehouse or local inventory can be supplied. No endpoint name is assumed or invented, and existence must be confirmed before any implementation claim.

### B. Official partner-provided structured data

If AliExpress later provides official feeds, exports, partner datasets, API extensions or structured seller/store information, those sources may be evaluated for provenance, object semantics and stability before any model or ingestion work is authorized.

### C. Human-verifiable partner evidence

Information officially presented by the partner on an offer/page may in the future be evaluated as manual evidence only under a separate provenance protocol and Supervisor order. This does **not** authorize mass scraping, browser automation for catalog extraction, improvised scraping, inference from text/images, or bypassing partner API/protections.

### D. Other suppliers / affiliate partners

The commercial architecture must not assume that AliExpress is permanently the only provider. If another officially authorized partner can provide seller identity, dispatch country, EU warehouse or inventory as structured factual data, a future provider-specific adapter may be considered. No Banggood or other supplier integration is authorized in this operation.

## 16. Próxima sequência autorizável

This document records a possible Supervisor-controlled sequence; it does not authorize execution:

1. `SELLER & EUROPEAN ORIGIN DATA CAPABILITY AUDIT 001` — current phase;
2. `EUROPEAN EVIDENCE SOURCE DECISION` — decide whether an additional authorized source can provide seller/origin/warehouse evidence;
3. `MINIMAL MODEL DECISION` — only if factual source data justifies model change;
4. `HIFU CONTROLLED CATALOG PILOT`;
5. `HIFU AUDIT`;
6. `CAVITAÇÃO + RF + VACUUM PILOT`;
7. `PROGRESSIVE EIGHT-FAMILY EXPANSION`;
8. `FINAL PUBLIC-LAUNCH GATE` — separate authorization.

No next phase starts automatically.
## 17. Estado de lançamento

`PUBLIC LAUNCH NOT AUTHORIZED`

Staging remains noindex. This audit does not activate indexing, change the public domain, import products, expand catalog families or alter storefront behavior.

## Audit evidence and conclusions

Static audit result: seller/store/origin/warehouse/stock are absent from the current catalog schema, normalized AliExpress product type and normalizer/client field mapping. Destination and delivery evidence are implemented with explicit provenance. Availability has storage semantics but no factual upstream mapping and remains `UNKNOWN` in current persistence.

Historical repository evidence confirms that SEARCH has previously supplied interpretable five-day delivery evidence for PT while DETAIL repeatedly returned no interpretable delivery value for the same HIFU cohort. This is logistics evidence only, never origin evidence.

Bounded live diagnostic result: three existing product DETAIL responses and one five-result PT SEARCH exposed no seller/store/ship-from/origin/warehouse/stock fields in the inspected result structures. Current capability therefore cannot substantiate the project's desired European-origin claims.

Database counts before live diagnostic: ProductFamily=9, Offer=6, OfferObservation=15, OfferFamilyPlacement=6, OfferClick=43. The diagnostic path used no ORM writes, persistence service, affiliate generation or `/go/` route. Counts must remain identical at the final validation gate.

Immediate model-change recommendation: NO. Preserve the current schema until an official, repeatable source for the missing identity/origin fields is demonstrated and its object-level semantics are understood.

Application code changes: ZERO. Model changes: ZERO. Migrations: ZERO. Schema changes: ZERO. Storefront changes: ZERO. Infrastructure changes: ZERO. Deploy: ZERO.
