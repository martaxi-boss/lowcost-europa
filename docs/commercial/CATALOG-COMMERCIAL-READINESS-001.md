# CATALOG + COMMERCIAL READINESS 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Scope

Commercial freshness audit of the six existing AliExpress Offers only.

- Authorized base: `ab7d47c816af164a58c3a9522db0d028f963a38e`.
- Branch: `builder/catalog-commercial-readiness-001`.
- No new ProductFamily, Offer, discovery candidate or replacement product was created.
- Staging DNS, certificates, noindex and public-launch state were not changed.

## Baseline

Before API calls the live database was:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 9
- OfferClicks = 34

OfferClicks are not used as a commercial metric in this phase.

## API call budget

Exactly 6 initial detail calls were made, one per existing Offer. No detail retry loop was used.

- Detail success: 4
- Detail failure: 2 (`AliExpressAPIError`)
- Search calls: 5 bounded family searches, page 1 / page size 10 / PT / EUR / EN / delivery filter 5 days
- Search calls were only used to try to re-find the same existing product IDs.
- No broad substitute discovery was performed.
## Offer decisions

### Offer 51 — `1005012522304882`

- Family: Máquinas HIFU 7D
- Primary: yes, editorial/internal only
- Detail identity: exact product ID match; title remains clearly HIFU 7D
- Historical price: 713.70 EUR
- Current detail price: 715.86 EUR (+0.30%)
- Current search price for same ID: 906.93 EUR; material search/detail divergence, so price volatility is documented and no discount claim is authorized
- Sales indicated by source: 3
- Evaluation: unavailable
- Commission: 7%
- Logistics: SEARCH_ONLY; current search returned the same ID with 5 days while detail remains NULL
- Availability: UNKNOWN
- Warehouse / European stock / European shipping: UNKNOWN
- Image: HTTP 200, image/webp, 1080x1080 — GOOD
- Decision: **KEEP**

### Offer 52 — `1005013116584854`

- Family: Máquinas HIFU 7D
- Primary: no
- Detail identity: exact product ID match; title remains clearly HIFU 7D
- Historical price: 226.17 EUR
- Current detail price: 226.86 EUR (+0.31%)
- Sales indicated by source: 0
- Evaluation: unavailable
- Commission: 7%
- Current bounded search did not re-find this exact ID; detail delivery remains NULL, therefore current logistics = UNKNOWN
- Availability: UNKNOWN
- Warehouse evidence: UNKNOWN
- Image: HTTP 200, image/webp, 123x123 — WEAK
- Known image finding remains OPEN / NON-BLOCKING; no substitute image was used
- Decision: **KEEP WITH FINDING**
### Offer 53 — `1005013002556821`

- Family: Máquinas HIFU 22D MAX
- Primary: yes, editorial/internal only
- Detail identity: exact product ID match; title remains clearly HIFU 22D MAX
- Historical price: 896.24 EUR
- Current detail price: 898.96 EUR (+0.30%)
- Sales indicated by source: 0
- Evaluation: unavailable
- Commission: 7%
- Current bounded search did not re-find this exact ID; detail delivery remains NULL, therefore current logistics = UNKNOWN
- Availability: UNKNOWN
- Warehouse evidence: UNKNOWN
- Image: HTTP 200, image/webp, 529x529 — ACCEPTABLE
- Decision: **KEEP**

### Offer 54 — `1005012828137048`

- Family: Máquinas Cavitation + RF Body Shaping
- Primary: yes, editorial/internal only
- Detail identity: exact product ID match; title remains coherent with Cavitation / RF body shaping
- Historical price: 993.77 EUR
- Current detail price: 996.79 EUR (+0.30%)
- Sales indicated by source: 1
- Evaluation: 100% as indicated by the source
- Commission: 7%
- Current bounded search did not re-find this exact ID; detail delivery remains NULL, therefore current logistics = UNKNOWN
- Availability: UNKNOWN
- Warehouse evidence: UNKNOWN
- Image: HTTP 200, image/webp, 400x400 — ACCEPTABLE
- Decision: **KEEP**
### Offer 55 — `1005012991431121`

- Family: Máquinas Diode Laser Hair Removal
- Primary: yes, editorial/internal only
- Initial detail call: failed with `AliExpressAPIError`; it was not retried
- Bounded same-family search: did not re-find this exact product ID
- Existing family/title association remains coherent with diode laser hair removal, but current API identity could not be refreshed
- Latest historical price remains 969.45 EUR; no fresh price is asserted
- Latest historical sales indicated by source: 0
- Latest historical evaluation: unavailable
- Latest historical commission: 7%
- Current logistics: UNKNOWN; no current exact-ID search evidence and no successful detail evidence
- Availability: UNKNOWN
- Warehouse evidence: UNKNOWN
- Existing image URL: HTTP 200, image/webp, 1873x1873 — GOOD
- No new OfferObservation was persisted
- Decision: **REVIEW REQUIRED**

### Offer 56 — `1005012839981986`

- Family: Máquinas Hydro Dermabrasion / Aqua Peel
- Primary: yes, editorial/internal only
- Initial detail call: failed with `AliExpressAPIError`; it was not retried
- Bounded same-family search: did not re-find this exact product ID
- Existing family/title association remains coherent with hydro / aqua peel, but current API identity could not be refreshed
- Latest historical price remains 930.69 EUR; no fresh price is asserted
- Latest historical sales indicated by source: 1
- Latest historical evaluation: unavailable
- Latest historical commission: 7%
- Current logistics: UNKNOWN
- Availability: UNKNOWN
- Warehouse evidence: UNKNOWN
- Existing image URL: HTTP 200, image/webp, 2000x2000 — GOOD
- No new OfferObservation was persisted
- Decision: **REVIEW REQUIRED**
## Persistence

After read-only collection, exactly one new factual OfferObservation was created for each validated detail-success Offer 51–54.

- New OfferObservations: 4
- Offers changed: 0
- ProductFamilies changed: 0
- Offer identity/family/primary/affiliate URL/active changed: 0
- Offers 55–56 received no new observation because current detail failed

The persisted observations use the fresh detail facts. Only Offer 51 has current search logistics attached because it was the only exact ID re-found by the bounded searches.

## Price and logistics findings

The four successful detail prices are all approximately 0.30–0.31% above their previous stored observation. No promotion, discount, usual-price or savings inference is made.

Offer 51 also showed a material search/detail price disagreement (906.93 EUR search vs 715.86 EUR detail), reinforcing that AliExpress price snapshots are volatile and source-context dependent.

Current logistics classification:

- Offer 51: SEARCH_ONLY (search 5 days; detail NULL)
- Offers 52–56: UNKNOWN in this refresh

No delivery guarantee is authorized. No European warehouse, European stock or European shipping claim is supported by this audit.

## Safety / launch status

No `/go/` request was intentionally made in this phase. OfferClicks remain an external-traffic counter, not a commercial outcome metric.

No raw affiliate URL, secret, token or private operator data is included in this report.

DuckDNS remains staging, noindex remains required and public launch is not authorized.

## Final snapshot and cleanup

Final audited live database snapshot:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 13
- OfferClicks = 34

OfferClicks remained unchanged from the phase baseline; no `/go/` request was made by this phase.

Phase-specific temporary scripts, downloaded images and the exact-branch test workspace were removed from `/tmp`. No permanent Chromium/Playwright cache or heavy stack was created. Root filesystem remains approximately 64% used with about 8.5 GB free.
