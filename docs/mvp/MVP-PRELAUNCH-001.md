# MVP PRELAUNCH 001 — transparency, technical SEO and five-family audit

Main base SHA: `f38faf4ef80253fba7978721cf96090cf2b5eaee`

This task prepares code and documentation only. It does not deploy this branch, remove noindex, or authorize public launch.

## Transparency pages

Implemented routes:
- `/como-funciona/` — explains selection, factual information, seller redirect, seller checkout/payment/shipping/post-sale, and possible affiliate commission.
- `/afiliados/` — states that some links are affiliate links and commission may be received on eligible purchases; no commission is described as guaranteed.
- `/privacidade/` — documents current OfferClick fields, storefront cookie findings and the distinction from infrastructure logs.
- `/termos/` — explicitly marked `PRE-LAUNCH / NOT PUBLIC READY`; no legal operator identity is invented.

The footer links to all four pages while retaining a short affiliate disclosure.

## Commercial claims used

The storefront may state that Lowcost Europa curates offers, redirects the buyer to the seller, does not process the purchase payment, may receive affiliate commission, and that seller price/availability/logistics can change.

SEARCH_ONLY logistics remain an observed estimate, not a delivery guarantee.

## Privacy and cookie audit

Application-level `OfferClick` contains only `offer` and `clicked_at`. It does not store IP, user-agent, session ID, fingerprint, referrer, email, location or another persistent identifier. One row means one valid redirect request, not one person, purchase, conversion or commission.

Django includes session and CSRF middleware, but the current public storefront does not access `request.session`, render CSRF tokens or include analytics code. Live GET checks of homepage and product detail emitted no `Set-Cookie` header. `/go/` was not called live; its implementation and existing tests show no session/CSRF dependency.

Nginx uses the global access log and error log. The staging proxy also forwards `X-Real-IP` and `X-Forwarded-For`, so server/security logs are treated separately from OfferClick tracking and may include network/request metadata such as IP and requested URL.

No claim of absolute IP non-processing or complete cookie-freedom is made.

## Technical SEO baseline

- useful page titles and meta descriptions;
- Open Graph title/description/type;
- robots meta driven by `PUBLIC_INDEXING_ENABLED`, defaulting to `noindex, nofollow`;
- canonical emitted only when an explicit `DJANGO_PUBLIC_SITE_URL` is configured;
- no final domain is invented and the temporary staging host is not promoted as the public canonical;
- simple `/sitemap.xml` for homepage, non-retired ProductFamilies and institutional pages;
- simple `/robots.txt`; default pre-launch behavior is `Disallow: /`;
- no Product/Review schema, fake ratings, keyword stuffing or aggressive commercial SEO.

## Five-family catalog audit

All five family detail pages returned HTTP 200 on staging; all relevant Offers are active, have affiliate URLs and image URLs, and direct affiliate destinations are absent from rendered HTML.

1. `maquinas-hifu-7d` — primary `1005012522304882`; latest primary observation PK 57; 713.70 EUR; commission 7%; search delivery 5 / detail NULL. Second active Offer `1005013116584854` remains non-primary with observation PK 58, 226.17 EUR, commission 7%, search 5 / detail NULL.
2. `maquinas-hifu-22d-max` — primary `1005013002556821`; observation PK 59; 896.24 EUR; commission 7%; search 5 / detail NULL.
3. `maquinas-cavitation-rf-body-shaping` — primary `1005012828137048`; observation PK 60; 993.77 EUR; commission 7%; search 5 / detail NULL.
4. `maquinas-diode-laser-hair-removal` — primary `1005012991431121`; observation PK 61; 969.45 EUR; commission 7%; search 5 / detail NULL.
5. `maquinas-hydro-dermabrasion-aqua-peel` — primary `1005012839981986`; observation PK 62; 930.69 EUR; commission 7%; search 5 / detail NULL.

All five families therefore remain `SEARCH_ONLY` for the displayed current observation where detail delivery is NULL; no 5-day guarantee is made.

Image checks in Chromium:
- HIFU 7D primary: HTTP 200, 1080x1080.
- HIFU 7D second Offer: HTTP 200, 123x123.
- HIFU 22D MAX: HTTP 200, 529x529.
- Cavitation + RF: HTTP 200, 400x400.
- Diode Laser: HTTP 200, 1873x1873.
- Hydro Dermabrasion: HTTP 200, 2000x2000.

## Quick visual QA — three newest families

Chromium real-browser checks were run at desktop 1440x900 and mobile 390x844 for Cavitation + RF, Diode Laser and Hydro Dermabrasion. All six page/viewport combinations returned HTTP 200, rendered their factual image, title, price/logistics content and `Ver oferta` CTA, and had no horizontal overflow. No CTA was clicked and `/go/` was not requested.

Known finding: Offer `1005013116584854` still uses a factual 123x123 image that is enlarged substantially at card size. It is not broken (HTTP 200), but remains a **PRE-LAUNCH DATA QUALITY FINDING** for later treatment. No replacement was made.

## Legal/operator input still needed

Before public launch the owner must supply or validate, as applicable:
- legal/operator name or entity;
- NIF/VAT or registration data;
- legal/commercial address that must be published;
- official contact email;
- telephone if required or chosen;
- definitive legal terms/policies based on those facts.

The current Terms page is intentionally pre-launch and not represented as complete legal compliance.

## Remaining public-launch blockers / pending items

- public launch is still not authorized and staging remains noindex;
- final public domain/canonical is not configured;
- legal/operator identity and contact details remain PENDING OWNER INPUT;
- off-server backup remains pending;
- HIFU second-Offer 123x123 image-quality finding remains open;
- this branch still requires merge and a separate staging deployment order before its new pages/SEO code appear on staging.

Live DB remained 5 ProductFamilies / 6 Offers / 9 OfferObservations / 1 OfferClick. No catalog write, AliExpress live call, Observation, OfferClick or `/go/` request occurred in this task.
