# MVP QA BASELINE 001

> HISTORICAL CHECKPOINT — Evidence and instructions below apply only to the recorded phase. Current rules and authorization: PROJECT_STATE.md and docs/README.md. This report does not certify today's runtime or authorize repeating old operations.

## Scope
Technical staging QA only. No `/go/` request and no CTA click were performed in this task.
Host: `lowcost-europa.165-22-114-67.sslip.io`.

## Desktop baseline
- homepage: HTTP 200, 2,486-byte HTML, ~0.06 s response;
- ProductFamily detail: HTTP 200, 3,545-byte HTML, ~0.06 s response;
- header and footer present;
- primary CTA present on homepage;
- two separate CTA routes present on detail;
- affiliate destination URL absent from HTML;
- disclosure and conservative logistics copy present.

## Mobile baseline
Android/Chrome mobile user-agent returned the same successful pages and content sizes.
Viewport meta is `width=device-width, initial-scale=1`.
Storefront CSS contains responsive media queries and no obvious fixed-width >=1000px overflow rule.
CTA routes were inspected as markup only and were not requested.

## Findings / limitations
- no graphical browser renderer is installed on the Droplet, so this is a technical responsive baseline rather than pixel-level visual QA;
- current storefront shell renders no `<img>` product elements on homepage or detail; placeholder media remains, so product imagery is a known UX gap for later work;
- no obvious horizontal-overflow risk was found in the current CSS scan;
- no current application 5xx, traceback, proxy or database error was found after reconciliation;
- one Gunicorn worker SIGTERM in logs corresponds to the controlled service restart;
- Nginx error log contains unrelated internet scanning/default-host noise, not staging-host application failures.

## Result
Desktop: PASS with the product-imagery visual gap noted.
Mobile: PASS technical baseline with the same limitation.
No new OfferClick was generated during QA.
