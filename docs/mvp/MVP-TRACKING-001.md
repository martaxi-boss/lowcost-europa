# MVP TRACKING 001 — affiliate redirect + privacy-minimal click tracking

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

Base main SHA: `d81e43c0ad8c98515160340ced0c9a302bcc63d0`.

## Metric definition

One `OfferClick` row equals one valid request to the commercial redirect endpoint for an eligible Offer.
This is a raw outbound click only.
It is not a unique person, unique session, purchase, conversion, revenue, or confirmed commission.
No impression metric is created in this task.

## Stored data

`OfferClick` stores only:
- `offer` — protected ForeignKey to `Offer`;
- `clicked_at` — server-side creation timestamp.

It stores no IP, hashed IP, user-agent, cookie/session ID, fingerprint, device/browser ID,
email/login, location, referrer, user querystring, or persistent user identifier.

## Redirect eligibility

`/go/<offer_id>/` returns a normal HTTP 302 only when the Offer:
- exists;
- is active;
- belongs to a ProductFamily;
- belongs to a ProductFamily that is not RETIRED;
- has a non-empty `affiliate_url`.

The Offer does not need to be editorial primary.
The redirect destination comes only from `Offer.affiliate_url`; user-supplied destination parameters are ignored.
There is no product URL fallback and the affiliate URL is never placed directly in storefront HTML.

## Persistence and fail-open

The endpoint resolves the eligible Offer first, then attempts to create one `OfferClick` row.
If click persistence raises `IntegrityError` or `OperationalError`, a minimal technical warning with only the Offer database ID is logged and the valid commercial redirect still proceeds.
Programming/generic exceptions are not swallowed.

## Storefront and admin

Eligible Offers render `Ver oferta` as an internal `/go/<id>/` link.
The homepage uses `family.display_offer`; detail pages keep each eligible Offer linked to its own redirect.
Affiliate disclosure remains visible and logistics language remains conservative.
`OfferClick` is registered in Django Admin for inspection only; add/change/delete are disabled.

## Scope

This implementation does not add impressions, aggregate counters, CTR, conversion, revenue, commission reconciliation, external analytics, cookies, fingerprinting, scoring, ranking, or scheduling.
`catalog.0004_offerclick` is code-only in this task and must not be applied to the live database before Supervisor authorization.
No public deployment or live click event is part of MVP TRACKING 001.
