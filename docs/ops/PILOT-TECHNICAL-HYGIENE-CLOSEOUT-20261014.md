# Lowcost Europa — Pilot Technical Hygiene / Closeout

Date: 2026-10-14  
Scope: technical controlled pilot only. Commercial activation **NOT authorized**.

## Source of truth and audit boundary

- Repository: `martaxi-boss/lowcost-europa` (**public since 2026-10-14**, without authorizing public site indexing or commercial launch).
- Frozen integration base: `main` commit `82ff2d68835bf083de3b4da6ce674ae24631b3c5`.
- Integration branch: `builder/pilot-integration-preflight-20261014`.
- No code, data, services, application restart or DNS changes applied to the VPS by this branch.
- Operational runtime is **NOT VERIFIED** by this work; the dated runtime snapshot in `PROJECT_STATE.md` must not be reinterpreted as current live evidence.
- PR #147 **MERGED** the documentation-only hygiene at `4b2a96cbcd3a101e1f65ceea11072d58328195e9`. PR #152 **MERGED** the tested application code at `ed067409c997daacee7c19d6a8ca36fa98494e82`. Neither commit is a VPS deployment.
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
- A temporary **read-only** HTTP probe was added, executed, and deleted from CI. Its observations are preserved in GitHub Actions run `38582509781`, not as permanent workflow complexity.
- CI triggers only for pull requests to `main`, pushes to `main` and explicitly requested manual runs. Branch pushes with an open PR no longer cause an unnecessary second job.
- CI uses read-only repository contents permission, disables checkout credential persistence, and cancels superseded runs.
- Compared the 16 non-conflicting source/test file blobs from PRs #148/#149/#150 to the integration tree: **16/16 exact SHA matches**. Only the combined storefront view and consolidated CI intentionally differ from individual branches.
- Historical binary screenshots, backups, operator information, catalog records and migrations are **not deleted or rewritten** by this branch; PR #147 handles its own documented duplicate screenshot cleanup.
- Public-source spot-check of deployment scripts, Django settings, AliExpress configuration, workflow, backup notes and current project documents found **no exact secret-token/private-key pattern matches**. This limited scan does **not** certify the entire Git history or VPS secrets.

## Evidence — what has and has not passed

| Check | Result | Evidence scope |
| --- | --- | --- |
| Product image JavaScript syntax | PASS | Local Node.js `node --check`, GitHub-exact JS blob |
| Product image regression cases | 6/6 PASS | Local Node.js `node --test`, test file and code SHA verified against GitHub |
| 16 source/test files from component branches | 16/16 MATCH | Git tree SHA comparison |
| Integrated storefront code markers and duplicate decorator | CHECKED | Combined source inspection |
| Django full suite on merged `main` | **638/638 PASS** | GitHub Actions run `38583874116`, merged commit `ed067409c997daacee7c19d6a8ca36fa98494e82` |
| Django checks, Ruff, migration drift, PostgreSQL migrations and Node image QA | **PASS** | Same post-merge GitHub CI run `38583874116`, all required steps success |
| Owner storefront navigation test after factual copy change | **FIXED / PASS** | Updated stale assertion to require the approved factual headline; checked absence of old unsupported claim |
| External HTTPS staging reachability | **PASS (read-only)** | GitHub Actions `38582509781`: homepage, robots, two health URLs and all five category pages HTTP 200; unauthenticated `/painel/` returned HTTP 302 |
| Staging non-indexing controls | **PASS** | Same run: header `X-Robots-Tag: noindex, nofollow`, HTML meta `noindex`, robots `User-agent: *; Disallow: /` |
| Runtime of new image JavaScript | **DEPLOYED, HTTP VERIFIED** | Run `38591194575`: staged Git SHA pinned, collectstatic PASS, homepage references script and HTTPS `/static/storefront/product-images.js` returns its new source |
| VPS runtime and backup basics | **PASS** | Runs `38588262630`, `38588855170`, `38591194575`: exact deploy SHA, services/timers active, recent local dump SHA256 and `pg_restore --list`, offsite success marker (full restore NOT repeated) |
| Real Android/desktop device/browser experience, Owner interactions and participant feedback | **PENDING** | HTTP, Django/Node unit tests and deployment checks are not a human-device acceptance test |
| GitHub Actions | **PASS** | Re-running after public repository visibility enabled real job steps, then 638 Django tests passed. Earlier zero-step failures remain historical evidence only |
| User feedback, commercial conversion or revenue | NOT COLLECTED | Separate real pilot required |

Earlier GitHub runs with no executed steps were not evidence of application failures. The **successful 2026-10-14 GitHub CI** is the valid current code-test evidence; it is **not a live VPS/runtime test**.

## Integration and pilot validation sequence

1. **Completed:** public repository GitHub-hosted runner executes genuine steps; test workflow now operates.
2. **Completed:** candidate application commit `75af0e77b6e13977cd01a857db2d187076e07a61` passed Django check/deploy check, migration drift, Ruff, PostgreSQL migrations, **638/638 Django tests** and **6/6 Node image cases** in run `38580359411`.
3. **Completed:** PR #152 reviewed and squash-merged after CI green; Owner approval and publication gates unchanged.
4. **Completed:** the existing VPS had a clean checkout, verified local backup and recent offsite success marker; controlled staging-only rollout reached exact Git commit `f0d520d31ef6a3aa06ee11f2793be50f75d58a2c`. Failed first attempt auto-rolled back (run `38590194547`); corrected staging-URL assertion and successful rollout/health and static verification (run `38591194575`). No migrations or data mutation were executed.
5. **Staging deployed and read-only HTTP acceptance passed**, including five family URLs, new static JS, health, nonindex and robots controls. Still inspect real image quality/broken image fallback, affiliate `/go/`, WhatsApp/contact and Owner workflows in real Android and desktop browsers.
6. Check system health, scheduled maintenance, backups, alerting and `robots.txt`/noindex without deleting or mutating production data.
7. Gather human feedback on trust, pricing clarity, logistics uncertainty, navigation and external purchase disclosure. Record evidence in issue #151.
8. Decide whether the pilot concept merits subsequent commercial work. Commercial launch stays a separate Owner decision.

## Rollback, privacy and clean state

- No force pushes, no database migrations, no deletions of actual product media and no production deploy are required by this hygiene operation.
- Keep older PR history for audit. Close only genuinely superseded proposals after the consolidated replacement is available and cross-referenced.
- No personal visitor fingerprinting, third-party analytics, API secrets or payment simulation was added.
- Rollback of repository integration is by reverting the application squash commit `ed067409c997daacee7c19d6a8ca36fa98494e82`. VPS staging rollback to the former deployed SHA `82ff2d68835bf083de3b4da6ce674ae24631b3c5` was actually exercised on the first attempt and returned PASS; successful deployment is `f0d520d31ef6a3aa06ee11f2793be50f75d58a2c`.
- Open status remains explicit: **CI GREEN; STAGING DEPLOYED AND HTTP VERIFIED; HUMAN DEVICE/OWNER WORKFLOW & FEEDBACK PENDING; PUBLIC INDEXING OFF; COMMERCIAL GO-LIVE NO**.
