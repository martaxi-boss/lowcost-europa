# Lowcost Europa — Pilot Technical Hygiene / Closeout

Date: 2026-10-14  
Scope: technical controlled pilot only. Commercial activation **NOT authorized**.

## Source of truth and audit boundary

- Repository: `martaxi-boss/lowcost-europa` (private).
- Frozen integration base: `main` commit `82ff2d68835bf083de3b4da6ce674ae24631b3c5`.
- Integration branch: `builder/pilot-integration-preflight-20261014`.
- No code, data, services, application restart or DNS changes applied to the VPS by this branch.
- Operational runtime is **NOT VERIFIED** by this work; the dated runtime snapshot in `PROJECT_STATE.md` must not be reinterpreted as current live evidence.
- PR #147 concerns historical documentation hygiene and remains a **separate, unmerged** work item.
- No launch-domain, legal operator, production HSTS, public indexing, Search Console or commercial launch changes are made.

## Technical pilot corrections prepared

1. Product photographs are displayed only from HTTPS URLs; absent/unusable URLs use a neutral placeholder. A small photo retains its actual identity and is labelled as low resolution. Browser loading failures are recovered without displaying images of other products.
2. Landing-page text avoids unsupported all-products claims about European shipping and relative price advantages.
3. Price and logistics displays label the observation date and show a non-blocking warning when the latest renderable observation is more than seven days old. This is **not** a protocol expiry and does **not** alter the historical human approval or publication gates.
4. Only ordinary GET requests are counted as raw affiliate click events; HEAD, POST and identified browser prefetch/prerender are excluded. Counts remain raw events, not unique buyers, purchases, sales or commissions.
5. Manual AliExpress shortlinks are restricted to validated HTTPS AliExpress hops before following a redirect; direct product links are normalized without fetching external content.
6. CI covers Django, migration drift, Ruff, PostgreSQL tests, Node syntax and product image regression tests.

## Hygiene completed on the integration branch

- Combined the image, click and redirect-safety changes while preserving existing lifecycle behavior.
- Removed a duplicated `@require_safe` decorator caused by the first integration overlay.
- Replaced three overlapping CI workflows with one existing `.github/workflows/ci.yml` workflow; no additional image runner or dedicated pilot runner is retained.
- CI triggers only for pull requests to `main`, pushes to `main` and explicitly requested manual runs. Branch pushes with an open PR no longer cause an unnecessary second job.
- CI uses read-only repository contents permission, disables checkout credential persistence, and cancels superseded runs.
- Compared the 16 non-conflicting source/test file blobs from PRs #148/#149/#150 to the integration tree: **16/16 exact SHA matches**. Only the combined storefront view and consolidated CI intentionally differ from individual branches.
- Historical binary screenshots, backups, operator information, catalog records and migrations are **not deleted or rewritten**; PR #147 handles its own documented duplicate screenshot cleanup.

## Evidence — what has and has not passed

| Check | Result | Evidence scope |
| --- | --- | --- |
| Product image JavaScript syntax | PASS | Local Node.js `node --check`, GitHub-exact JS blob |
| Product image regression cases | 6/6 PASS | Local Node.js `node --test`, test file and code SHA verified against GitHub |
| 16 source/test files from component branches | 16/16 MATCH | Git tree SHA comparison |
| Integrated storefront code markers and duplicate decorator | CHECKED | Combined source inspection |
| Django suite, migrations and Ruff on combined branch | NOT RUN | Hosted CI unavailable; no local Django/PostgreSQL baseline |
| Real browser Android/desktop and live pilot services | NOT VERIFIED | No authorized live environment session with repeatable evidence |
| GitHub Actions | BLOCKED | Latest pilot jobs conclude failure with zero steps executed; GitHub administrative/billing gate remains |
| User feedback, commercial conversion or revenue | NOT COLLECTED | Separate real pilot required |

A GitHub run with no executed steps is not proof of passing or failing application tests.
Historical successes in `PROJECT_STATE.md` are not current evidence for the new combined code.

## Integration and pilot validation sequence

1. Resolve GitHub Actions administrative/billing or spending-limit restrictions. Confirm that real job steps execute.
2. On the **exact candidate commit**, obtain green Django check, production deploy check, migration drift check, Ruff, PostgreSQL migrations/tests and Node test results.
3. Review the consolidated draft PR and preserve separate Owner editorial gates. Do not merge merely because the code is present.
4. Integrate once, following a reversible, documented change. Verify deployed commit independently.
5. Check `/`, five current non-retired product families, a known real image, broken image, 123x123 photo handling, affiliate `/go/`, WhatsApp/contact and owner workflows on Android and desktop.
6. Check system health, scheduled maintenance, backups, alerting and `robots.txt`/noindex without deleting or mutating production data.
7. Gather human feedback on trust, pricing clarity, logistics uncertainty, navigation and external purchase disclosure. Record evidence in issue #151.
8. Decide whether the pilot concept merits subsequent commercial work. Commercial launch stays a separate Owner decision.

## Rollback, privacy and clean state

- No force pushes, no database migrations, no deletions of actual product media and no production deploy are required by this hygiene operation.
- Keep older PR history for audit. Close only genuinely superseded proposals after the consolidated replacement is available and cross-referenced.
- No personal visitor fingerprinting, third-party analytics, API secrets or payment simulation was added.
- Rollback, if ever deployed after validation, is by reversing the eventual application merge or redeploying the pre-change application commit; take an independently verified backup beforehand.
- Open blocking status remains explicit: **CI RED/NOT RUN, LIVE PILOT UNVERIFIED, PUBLIC INDEXING OFF, COMMERCIAL GO-LIVE NO**.
