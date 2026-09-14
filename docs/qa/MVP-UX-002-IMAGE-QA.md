# MVP UX 002 — Product imagery QA readiness

## Implemented behavior

The storefront now renders the factual remote `Offer.image_url` when it is structurally usable as an HTTP(S) URL.

- Homepage ProductFamily cards use the image of `family.display_offer`.
- Therefore an eligible editorial primary controls the homepage image; otherwise the existing deterministic display-offer fallback applies.
- ProductFamily detail cards render each Offer's own image independently.
- Product images are presentation only; they do not change `/go/` routing or affiliate destinations.

## Fallback

If `image_url` is NULL, empty, or does not begin with `http://` or `https://`, the existing Lowcost Europa placeholder is rendered instead of an `<img>` element.

The Django request path does not probe remote images with HEAD/GET. A syntactically acceptable external image may still fail at the remote origin in the browser.

## HTML and CSS expectations

- `<img>` uses the factual Offer title as `alt` text.
- Detail images use `loading="lazy"`; the homepage display image is not lazy-loaded.
- Explicit width/height plus a 4:3 CSS aspect ratio reduce layout shift.
- `object-fit: contain` avoids distortion while preserving the full product image.
- Layout remains mobile-first with no new CSS framework or JavaScript dependency.

## Privacy and hosting

Images remain remote and are not downloaded, mirrored, proxied, or stored by Lowcost Europa. No image-request metadata, cookies, fingerprinting, or additional tracking is introduced.

## QA limitation

This change is implementation + automated-test readiness only. It has not yet been deployed to staging, and no pixel-level graphical browser QA is claimed. Remote-origin availability, image composition, and final visual balance must be checked after a future audited staging deployment.
