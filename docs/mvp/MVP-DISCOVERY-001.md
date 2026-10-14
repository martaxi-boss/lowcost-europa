# MVP DISCOVERY 001 — Controlled Commercial Candidate Scan

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Timestamp: 2026-09-15T00:17:58Z
Main SHA: `be6fb1bf497c73a2a8d0e153af7ec3e1206a8a21`
Mode: READ-ONLY DISCOVERY
Country: PT
Currency: EUR
Target language: EN
Primary delivery filter: 5 days
Page size: 5
Pages per query: 1

## DB safeguard before

- ProductFamilies: 2
- Offers: 3
- OfferObservations: 6
- OfferClicks: 1
- Each existing Offer had exactly 2 Observations.

No persistence operation was authorized or executed.
## Search results

| Query | Delivery filter | Valid | Invalid |
| --- | ---: | ---: | ---: |
| RF microneedling machine | 5 | 1 | 0 |
| diode laser hair removal machine | 5 | 4 | 0 |
| hydrafacial machine | 5 | 3 | 0 |
| cavitation RF slimming machine | 5 | 4 | 0 |

Total valid search candidates: 12.
Unique product IDs after deduplication: 12.
Duplicates: 0.
Search API failures: 0.

No 7-day fallback was required because every query returned at least one commercially useful machine candidate under the 5-day filter.

The search result `1005004987512166` was excluded commercially because its title identifies a 3pcs/Lot Hydra liquid serum consumable, not a machine.
## Detail calls

Seven detail calls were attempted, within the authorized maximum of eight.

Successful detail normalization: 5.
Failed detail normalization: 2.

Successful detail candidates all retained search delivery = 5 days and returned detail delivery = NULL, therefore evidence remained `SEARCH_ONLY` under the existing evidence semantics.

Two detail calls failed with `AliExpressResponseError: Missing required product identifier`:

- `1005013015748491` — RF microneedling candidate;
- `1005012450097098` — 7-in-1 Hydro Face candidate.

No manual retry loop or silent candidate substitution was performed.
## Shortlist — non-persisted

### 1. Proposed family: Máquinas RF Microneedling
- product_id: `1005013015748491`
- title: RF Microneedle Beauty Machine Morpheus 8 Microneedling Stretch Mark Remover Fractional Micro Needling By Medical Spa Equipmen
- price: 343.03 EUR (search)
- commission: 7.0%
- sales_count: 0
- evaluation: unavailable
- search delivery: 5 days
- detail delivery: unavailable because detail normalization failed
- evidence: `SEARCH_ONLY`
- image: present
- reason to keep: clear full-machine identity and the only valid result returned for the authorized RF microneedling query.
- risk: detail response could not be normalized; commercial identity must be revalidated before any import.

### 2. Proposed family: Máquinas Diode Laser Hair Removal
- product_id: `1005013068402043`
- title: 2 IN 1 Diode Laser Removal Machine Beauty Equipment Permanent Hair Reduction Device With Cooling System For Salon Spa
- price: 1713.40 EUR (detail; search returned 2170.71 EUR)
- commission: 7.0%
- sales_count: 1
- evaluation: 100.0%
- search delivery: 5 days
- detail delivery: NULL
- evidence: `SEARCH_ONLY`
- image: present
- reason to keep: explicit diode-laser hair-removal machine for salon/spa, with clean commercial identity and successful detail normalization.
- risk: price differed materially between search and detail calls; logistics remains search-only.
### 3. Proposed family: Máquinas Hydro Dermabrasion / Aqua Peel
- product_id: `1005013069446413`
- title: New Arrival 7 in 1 Hydro Dermabrasion Hydra Machine for Facial Aqua Peel Microdermabrasion Machine Skin Rejuvenation
- price: 540.38 EUR (detail; search returned 664.67 EUR)
- commission: 7.0%
- sales_count: 0
- evaluation: unavailable
- search delivery: 5 days
- detail delivery: NULL
- evidence: `SEARCH_ONLY`
- image: present
- reason to keep: full hydro-dermabrasion/aqua-peel machine identity and successful detail normalization.
- risk: no observed sales/evaluation signal and search/detail price changed; logistics remains search-only.

### 4. Proposed family: Máquinas Cavitation + RF Body Shaping
- product_id: `1005012828137048`
- title: Slimming Machine Body Shaping Equipment Fat Burning Beauty Device with Cryo Cooling Vacuum Cavitation Lipo RF Light Therapy
- price: 993.77 EUR (detail; search returned 1259.01 EUR)
- commission: 7.0%
- sales_count: 1
- evaluation: 100.0%
- search delivery: 5 days
- detail delivery: NULL
- evidence: `SEARCH_ONLY`
- image: present
- reason to keep: complete body-shaping machine with explicit cavitation/RF identity, successful detail normalization, and a small factual sales/evaluation signal.
- risk: multi-technology configuration needs careful ProductFamily boundaries; search/detail price changed and logistics remains search-only.
## Other exclusions / not shortlisted

- `1005004987512166`: excluded — consumable Hydra serum, not a machine.
- `1005012588706867`: not shortlisted — mixed Diode/Picosecond/RF/IPL identity makes a clean diode-family interpretation weaker.
- `1005013087686056`: not shortlisted — title combines diode hair removal and pico tattoo removal, creating commercial-family ambiguity.
- `1005012798018368`: inspected in detail but not shortlisted — clear diode machine, but the other diode candidate had a cleaner salon/spa identity and a small observed sales signal.
- `1005012450097098`: clear Hydro Face machine with sales_count 3 and evaluation 100% in search, but detail normalization failed; retained as a notable non-shortlisted candidate rather than silently replacing the failed detail call.
- `1005013003271191`: inspected in detail but not shortlisted — valid cavitation/RF machine, with no observed sales/evaluation signal in this scan.
- `1005012193878441`: not shortlisted — title explicitly includes home-use massage-device positioning, weaker fit for the professional-esthetics focus.
- `1005012684135880`: not shortlisted — plausible beauty machine, but remained search-only under the bounded two-detail-per-keyword cap.

No numeric score or ranking was created.

## DB safeguard after

- ProductFamilies: 2
- Offers: 3
- OfferObservations: 6
- OfferClicks: 1
- Observation counts remain exactly 2 per existing Offer.

Persistence during this task: ZERO.
No ProductFamily, Offer, OfferObservation, OfferClick, affiliate link, or catalog field was created or changed.
No `/go/` request was made.
