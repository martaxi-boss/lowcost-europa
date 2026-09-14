# MVP QA VISUAL 001

## Scope

This QA validates the merged product-imagery storefront on the existing noindex staging host. It does not authorize a public MVP launch and did not call `/go/` or click any commercial CTA.

## Deploy

- Main/deploy SHA: `0a0c79be959665b75b4911b1ae5f25ed8424eb7a`
- Staging: `lowcost-europa.165-22-114-67.sslip.io`
- Migration plan: no planned operations
- `collectstatic`: success; 1 changed static file copied, 127 unchanged
- `lowcost-europa.service`: active after controlled restart
- Nginx: unchanged and active
- `X-Robots-Tag`: `noindex, nofollow`

## Browser and viewports

- Browser engine: Chromium 140.0.7339.16 via Playwright 1.55.0
- Desktop viewport: 1440 x 900
- Mobile viewport: 390 x 844
- QA used real browser rendering and screenshots, not curl/HTML-only inspection.
## Desktop result

Homepage: PASS.

- Primary ProductFamily image renders correctly and matches the editorial primary Offer.
- Image is not distorted; card balance, title, price, logistics and CTAs are readable.
- Header/footer render correctly and no horizontal overflow was measured.

Detail: PASS with one non-blocking image-quality finding.

- Exactly two active Offers are rendered and primary appears first.
- Each Offer uses a distinct remote image URL.
- Both images loaded successfully with HTTP 200 and no broken-image icon.
- Primary image natural size: 1080 x 1080.
- Second Offer image natural size: 123 x 123; it is visibly pixelated/low-detail when enlarged to the card area. This is a source-data quality limitation, not a template failure.
- Prices, conservative logistics text, CTAs and disclosure remain readable with no overlap.

## Mobile result

Homepage: PASS.

- No horizontal overflow at 390 px width.
- Image fits the viewport and title/price/logistics remain readable.
- CTA size and spacing are usable; header and footer remain intact.
Detail: PASS with the same non-blocking second-image quality finding.

- Cards stack cleanly with no horizontal scroll or overlap.
- Both Offer images fit the viewport; the second remains visibly low-resolution because its source is 123 x 123.
- Long titles wrap without breaking the layout.
- Prices, logistics and disclosure remain legible.

## Remote image behavior

Both live 7D image URLs are served from `ae-pic-a1.aliexpress-media.com` and returned HTTP 200 in Chromium.

- `1005012522304882`: rendered=yes, 1080 x 1080.
- `1005013116584854`: rendered=yes, 123 x 123.
- Broken image icon: no.
- Images remain remote; no mirror, proxy or server-side download was introduced.

## Accessibility quick check

- Alt text exists for every rendered product image.
- Keyboard focus on CTA retains a visible 3 px outline with 3 px offset.
- CTA labels are explicit and text does not depend only on colour.
- Visual contrast is reasonable for the current staging baseline.
- This is not a full WCAG audit.
## Screenshots

- `docs/qa/screenshots/homepage-desktop.png`
- `docs/qa/screenshots/detail-desktop.png`
- `docs/qa/screenshots/homepage-mobile.png`
- `docs/qa/screenshots/detail-mobile.png`

## Logs and DB safeguard

- No current application 500/traceback/error was found after deploy/QA.
- No relevant Nginx upstream/static error was found for the staging host.
- Final live counts: 1 ProductFamily / 3 Offers / 6 OfferObservations / 1 OfferClick.
- `/go/` was not called and no commercial CTA was clicked.

## Result and limitations

Overall visual QA result: PASS for staging readiness.

No functional visual blocker was found. One non-blocking pre-launch data-quality finding remains: the second Offer's factual remote image is only 123 x 123 and appears visibly pixelated at storefront display size. No replacement was invented or written to live data.

Public MVP launch remains unauthorized and noindex must remain in place.
