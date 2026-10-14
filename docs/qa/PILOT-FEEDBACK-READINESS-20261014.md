# LOWCOST EUROPA — Pilot feedback and quality gates (2026-10-14)

Status: PROPOSED / NOT DEPLOYED / NO COMMERCIAL GO-LIVE.

## Pilot boundary
- Keep the current test hostname and `DJANGO_PUBLIC_INDEXING_ENABLED=false`.
- No new commercial domain, indexing, Search Console, paid campaign, or release authorization.
- Do not treat OfferClick records as unique people, purchases, revenue, or affiliate commissions.
- Keep all existing Owner approval and editorial publication gates.

## Functional regression sequence
1. Homepage on Android/mobile and desktop: images, headings, links and contrast.
2. Visit all 5 operational product families; inspect featured and other offers.
3. Verify one valid remote image, broken remote image fallback, low-resolution notice and HTTPS-only media.
4. Check observed prices, sources, conflicting/unknown delivery fields and affiliate disclosure.
5. Use a known valid Offer's `/go/<id>/`: GET redirects; HEAD, speculative prefetch and POST must not create OfferClick records.
6. Owner login, candidate review, manual intake, approval, publication/hide, logout and Admin authentication.
7. AliExpress errors, rate limit, maintenance timers, backup and restore health without calling production endpoints unnecessarily.
8. Privacy, Terms, Affiliates and Contact pages; confirm real operator details remain a commercial-launch gate.

## Feedback sampling (manual, no new third-party trackers)
- Record test date, viewport/device, page, expected vs observed behavior, broken photo URLs (without secrets), screenshots and severity.
- Collect voluntary qualitative feedback about trust in images, understanding of price/estimated delivery, navigation and willingness to open an offer.
- Keep outbound click counts as raw technical events; compare only like-for-like periods and exclude known automated/test sessions when reporting.
- Do not assert conversion, revenue or profitability without verified partner-side attribution.
- Record known blockers and test evidence before deciding whether the concept merits wider public testing.

## Release gate
All automated tests and QA checks must pass on the exact branch intended for integration. CI may remain administratively blocked by GitHub account billing; a queued/failed job without steps is not evidence of test failure or success.
