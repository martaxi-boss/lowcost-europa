# COMMERCIAL VALIDATION 001 — HIFU + CAVITATION

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Scope

Base main SHA: `04dc3005ee046f453c8d525780927d7e26c17955`.
Branch: `builder/commercial-validation-001-hifu-cavitation`.
Mode: read-only, bounded, no persistence.

No ProductFamily, Offer, OfferObservation or OfferClick was created. No candidate was imported or published. `/go/` was not called. No automatic scoring or ranking was performed.

The live deployment, Nginx, systemd, UFW, PM2, PostgreSQL schema, branch protection, backup infrastructure and noindex configuration were not changed.

## Search contract

The validation reused the project's established controlled discovery contract:

- country: PT
- currency: EUR
- target language: EN
- delivery filter: 5 days
- page: 1 only
- page size: 5

Two bounded search calls were made:

1. `professional HIFU machine`
2. `cavitation slimming machine`
## Search results

### HIFU

Search returned 2 valid products and 0 invalid items.

| Product ID | Search title | Search price | Sales indicated | Commission | Evaluation | Search delivery |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1005012476776786` | Professional Beauty Equipment Machine 25D Hifu 360MAX For Face Lifting Slimming And Fat Reduction Latest Model For Beauty Salon | EUR 1097.86 | 9 | 7.0% | 100.0% | 5 days |
| `1005009925120797` | 22D MAX HIFU Machine Professional Ultrasonic Lifting Equipment Face Tightening Slimming Fat Reduction Latest Anti-Aging Model | EUR 2063.40 | 9 | 7.0% | 96.4% | 5 days |

### Cavitation

Search returned 3 valid products and 0 invalid items.

| Product ID | Search title | Search price | Sales indicated | Commission | Evaluation | Search delivery |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `1005012711088780` | Professional 6 in 1 Cavitation Vacuum Body Slimming Machine Cavitation Lipolaser System Fat Removal Weight Loss Machine | EUR 654.39 | 0 | 7.0% | unavailable | 5 days |
| `1005013134531129` | K2 Multifunctional Slimming Machine 40K Cavitation Vacuum RF EMS Laser Lipolysis Body Reshaping Skin Tightening Equipment | EUR 780.51 | 0 | 7.0% | unavailable | 5 days |
| `1005012639969093` | V10 Multifunctional VELABODY Shape Body Slimming Cavitation Cellulite Fat Removal Vacuum Roller Eye care Weight loss machine | EUR 2071.60 | 0 | 7.0% | unavailable | 5 days |

All five titles identify professional/multifunction beauty machines rather than consumables. This is a title-level identity check only, not a product-quality certification.
## Detail validation

Exactly 5 detail calls were made, one for each returned candidate. Every detail response returned the same product ID as requested.

| Product ID | Detail price | Sales indicated | Commission | Evaluation | Detail delivery |
| --- | ---: | ---: | ---: | ---: | ---: |
| `1005012476776786` | EUR 866.57 | 9 | 7.0% | 100.0% | NULL |
| `1005009925120797` | EUR 1785.10 | 9 | 7.0% | 96.4% | NULL |
| `1005012711088780` | EUR 532.02 | 0 | 7.0% | unavailable | NULL |
| `1005013134531129` | EUR 634.56 | 0 | 7.0% | unavailable | NULL |
| `1005012639969093` | EUR 1684.23 | 0 | 7.0% | unavailable | NULL |

Each detail price was lower than the corresponding search price observed in this same bounded run. This demonstrates price volatility between API surfaces/calls and does not justify a stable-price claim.

All five candidates had search delivery = 5 days and detail delivery = NULL. Logistics evidence is therefore `SEARCH_ONLY`; no delivery guarantee is supported.

## Commercial interpretation

HIFU showed the stronger observed commercial signal in this bounded snapshot: both returned HIFU machines showed 9 sales, 7.0% commission and evaluation data (100.0% and 96.4%).

Cavitation returned three coherent machines at the same 7.0% commission, but all three showed 0 sales and no evaluation value in the observed API response. On this evidence alone, cavitation does not show the same sales signal as HIFU.

This is not an automatic ranking, winner selection, profitability proof, conversion proof or market-size conclusion. Sales counts are source-indicated values, not verified customers, orders attributable to Lowcost Europa, or commissions earned by the project.
## Safeguards and final state

Live DB remained unchanged after the API calls:

- ProductFamilies = 5
- Offers = 6
- OfferObservations = 9
- OfferClicks = 5

Deployment SHA remained `04dc3005ee046f453c8d525780927d7e26c17955`.

Staging noindex configuration remained unchanged:

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=`

Secrets were used only as runtime API credentials and no secret values were printed or written to this report.

`PROJECT_STATE.md` is intentionally not changed in this branch while MVP OPERATIONAL CLOSEOUT 001 remains open.

Public launch remains unauthorized.
