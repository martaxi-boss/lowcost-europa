# MVP LIVE CATALOG 004 — fresh Diode and Hydro curation

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Operation time (UTC): `2026-09-15T07:25:58Z`

Main SHA: `ae0e564eecc3bbe7955683ba75a6ced6377c7139`

## Safety gates

- Latest daily backup: `lowcost-europa-20260915T031500Z.dump`.
- Backup size: 94,565 bytes; dump/sidecar modes: 600.
- `sha256sum -c`: PASS.
- PostgreSQL custom-format validation: PASS.
- DB before: 3 ProductFamilies / 4 Offers / 7 OfferObservations / 1 OfferClick.
- Slugs `maquinas-diode-laser-hair-removal` and `maquinas-hydro-dermabrasion-aqua-peel` were free.
- Only the existing `AliExpressClient` was used; country PT, currency EUR, language EN.
- RF Microneedling remained HOLD and was not searched or imported.

## Diode search

Keyword: `diode laser hair removal machine`

- delivery filter: 5 days; page size: 5; one page.
- valid: 5; invalid: 0.
- Editorial inspection was limited to 3 candidates; 2 received detail calls.
### Diode candidates inspected

1. `1005012991431121` — clear diode laser hair-removal identity; full detail succeeded.
2. `1005012798018368` — clear diode laser identity; full detail also succeeded.
3. `1005012791309665` — title materially mixes diode and picosecond/tattoo-removal use; excluded from final selection.

Other search results with dominant picosecond/tattoo-removal mixing were not advanced to detail.

### Diode detail calls

- `1005012991431121`: SUCCESS.
- `1005012798018368`: SUCCESS.

Final selection: `1005012991431121`.

Rationale: commercially clear diode hair-removal machine, complete product, factual image/product URL present, and no stronger factual reason to prefer the inspected alternative. The selected current prices were also lower than the inspected alternative; this was supporting context, not an automatic ranking rule.

Search price: 1,112.55 EUR.
Detail price: 969.45 EUR.
Detail original price: 3,127.24 EUR.
Commission: 7%.
Sales: 0.
Evaluation: NULL.
Search logistics: `Ship to PT in 5 days` / 5 days.
Detail logistics: NULL / NULL.
Evidence: `SEARCH_ONLY`.
Image: present; HTTP 200; host `ae-pic-a1.aliexpress-media.com`; natural dimensions 1873x1873.
Affiliate link generation: SUCCESS; full link intentionally not documented.
Imported: YES.

ProductFamily:
- PK 4
- name `Máquinas Diode Laser Hair Removal`
- slug `maquinas-diode-laser-hair-removal`
- status `NEW`

Offer:
- PK 55
- external product ID `1005012991431121`
- active=True
- primary=True only because it is the sole current Offer in the family.

Initial OfferObservation:
- PK 61
- price 969.45 EUR; original price 3,127.24 EUR
- commission 7.0000%; sales 0; evaluation NULL
- search delivery 5; detail delivery NULL; availability UNKNOWN

## Hydro search

Keyword: `hydrafacial machine`

- delivery filter: 5 days; page size: 5; one page.
- valid: 2; invalid: 0.
- Both returned candidates were inspected and both received permitted detail calls.
### Hydro candidates inspected

1. `1005012450097098` — complete Hydro/dermabrasion-style machine by title; detail call failed with `AliExpressAPIError` because the API rate limit was exceeded for 1 second. No manual retry was performed.
2. `1005012839981986` — complete Hydra Oxygen facial machine; detail succeeded.

Final selection: `1005012839981986`.

Search price: 1,179.09 EUR.
Detail price: 930.69 EUR.
Detail original price: 1,692.16 EUR.
Commission: 7%.
Sales: 1.
Evaluation: NULL.
Search logistics: `Ship to PT in 5 days` / 5 days.
Detail logistics: NULL / NULL.
Evidence: `SEARCH_ONLY`.

Image: present; HTTP 200; host `ae-pic-a1.aliexpress-media.com`; natural dimensions 2000x2000.
Affiliate link generation: SUCCESS; full link intentionally not documented.
Imported: YES.

ProductFamily:
- PK 5
- name `Máquinas Hydro Dermabrasion / Aqua Peel`
- slug `maquinas-hydro-dermabrasion-aqua-peel`
- status `NEW`
Offer:
- PK 56
- external product ID `1005012839981986`
- active=True
- primary=True only because it is the sole current Offer in the family.

Initial OfferObservation:
- PK 62
- price 930.69 EUR; original price 1,692.16 EUR
- commission 7.0000%; sales 1; evaluation NULL
- search delivery 5; detail delivery NULL; availability UNKNOWN

## Atomicity and provenance

Each family was imported in its own `transaction.atomic()` block after rechecking that the ProductFamily slug and external product ID were still absent.

Search and detail price/logistics were kept separate. No averages or delivery guarantees were created. Both imported Offers remain `SEARCH_ONLY` because search delivery was 5 days while detail delivery was NULL.

Exactly one initial OfferObservation was created for each new Offer. No second observation, scheduler, scoring, ranking, or LE-013 work was performed.

## Storefront verification

- HTTPS homepage: HTTP 200; 5 ProductFamily cards.
- Diode detail: HTTP 200; one active Offer; display_offer `1005012991431121`.
- Hydro detail: HTTP 200; one active Offer; display_offer `1005012839981986`.
- Factual image and CTA are present on both details.
- Direct affiliate URLs are absent from rendered HTML.
- `X-Robots-Tag: noindex, nofollow` remains present.
- `/go/` was not called and no CTA was clicked.

## Final live state

- ProductFamilies: 5
- Offers: 6
- OfferObservations: 9
- OfferClicks: 1

Net additions from this task:
- ProductFamilies: +2
- Offers: +2
- OfferObservations: +2
- OfferClicks: +0

No application code, model, schema, migration, Nginx, systemd, scheduler, scoring, ranking, or public-launch change was made.

RF Microneedling `1005013015748491` remains HOLD and was not searched or imported in this task.
