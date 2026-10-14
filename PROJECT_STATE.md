# Lowcost Europa — Project State

Reconciled: 2026-10-03. Scope: repository hygiene; no application/runtime changes.

## Addendum — technical pilot revalidation (2026-10-14)

- GitHub repository visibility is **PUBLIC**. This is a repository-access change, **not** permission for commercial GO-LIVE or website indexing.
- **Current integrated application baseline:** `main` commit `ed067409c997daacee7c19d6a8ca36fa98494e82` (PR #152). Older baseline `82ff2d68835bf083de3b4da6ce674ae24631b3c5` below is historical; a later docs-only commit can change the HEAD without changing application code. No live VPS SHA is certified.
- Technical pilot improvements are **MERGED in PR #152** on `main`, but **NOT DEPLOYED** to the VPS: photographs, factual price/logistics display, click quality, manual AliExpress link safety and consolidated CI.
- On merged `main` application commit `ed067409c997daacee7c19d6a8ca36fa98494e82`, GitHub Actions run `38583874116` completed **SUCCESS**: 638/638 Django tests, 6/6 Node image tests, Ruff, Django checks and PostgreSQL migrations.
- Repository/CI testing is green. A read-only HTTPS probe on 2026-10-14 (run `38582509781`) found all five family routes and health endpoints HTTP 200, `X-Robots-Tag: noindex, nofollow`, homepage HTML meta `noindex` and `robots.txt` with `Disallow: /`. The live homepage **did not include** the new `product-images.js`; new code is **not installed on the VPS**. Independent VPS deployed SHA, Android/desktop imagery and production backups still require verification; no external-user feedback has been collected.
- Pilot work items/feedback: issue #151. Documentation-hygiene PR #147 was **MERGED** at `4b2a96cbcd3a101e1f65ceea11072d58328195e9` and removed four SHA-identical archived screenshots. Neither PR #147 nor #152 authorizes commercial launch or performs a VPS deploy.
- Commercial deployment, final domain, public indexing, changes to Owner approval/publication gates and a marketing launch all remain **unauthorized**.


## Completed baseline

- Owner status: completed / fully operational within the accepted project scope.
- Verified GitHub application baseline: `82ff2d68835bf083de3b4da6ce674ae24631b3c5`.
- PR #146 merged on 2026-09-30. PR-head CI runs `36763343523` and `36763348828`: success; accepted closeout: 623 tests.
- Runtime equality was accepted in the prior closeout; this task does not renew live VPS evidence.
- Architecture frozen: Python 3.12, Django 5.2 LTS, PostgreSQL, Gunicorn, Nginx, systemd, OVH.
- Administration: GitHub workflows. Desktop Commander/self-hosted runners are not the current operating path.
- Documentation-only commits advance main without changing/restarting the runtime.

The accepted technical scope stays closed. No new construction, architecture rebuild, public launch or indexing activation follows from this document. Final commercial domain, operator/legal inputs and commercial activation remain separate Owner decisions.

## Catalog and human workflow

`DISCOVERY → FAMILY RELEVANCE → GLOBAL DEDUPE → FAMILY RANKING → PENDING / A REVER → HUMAN APPROVAL → HIDDEN OFFER → HUMAN PUBLICATION → PUBLIC ELIGIBILITY → FACTUAL MAINTENANCE`

Product identity: `(source, external_product_id)`. ProductFamily is durable; OfferFamilyPlacement supplies public family membership. Retired taxonomy and decision/observation/click/move history remain preserved.

Operational family order/public names come from the database. Five operational slugs:

1. `cavitacao-rf-vacuum-corpo`
2. `hydrodermoabrasao-aqua-facial-multifuncoes`
3. `pressoterapia-vacuum-drenagem`
4. `hifu`
5. `diodo-laser-remocao-tatuagens-pigmentacao`

Owner panel: `/painel/`, authenticated staff only. Approval, rejection, revalidation, publication, hiding and family moves remain human actions.

Approval attests delivery to Portugal and ship-from within PL/CZ/FR/ES/DE, verified on the actual listing. Individual country metadata is optional and never fabricated. Approval uses the official AliExpress affiliate path, persists verified promotion, hides newly approved Offers and preserves existing editorial visibility.

Approval is not a positive discovery-learning signal. Semantic rejections and classification moves remain family-isolated; factual/logistics failures do not become semantic rejection signals.

## Public eligibility and lifecycle

Central gate: `apps/catalog/services/public_eligibility.py`.

- `is_active=True`, `owner_hidden=False`, non-empty affiliate URL;
- `affiliate_promotion_status=ELIGIBLE` and non-null `affiliate_promotion_verified_at`;
- non-null `protocol_verified_at`, not in the future.

Protocol age expiry: **NONE**. Time alone never hides an eligible Offer. Ship-from metadata is optional; human attestation remains mandatory. Price/observation availability are separate editorial concerns.

Public placement/publication respects operational families and cap 20 per family. Storefront and `/go/<offer_id>/` share the central gate; ineligible Offers do not redirect or create valid clicks.

Only factual unavailability deactivates Offers. Transient errors/rate limits/insufficient detail do not establish unavailability. Maintenance never renews human protocol, auto-publishes, clears Owner hiding or auto-reactivates inactive Offers.

## Discovery and maintenance

- Weekly discovery: Monday 23:40 UTC, five families sequentially, Persistent=true.
- Creates PENDING candidates only; no auto-approval/publication, final affiliate generation or Offer editorial mutation.
- Weekly intake pauses at 20 pending candidates per family. This is a campaign budget guard, distinct from public cap 20; existing candidates are not deleted.
- Hourly maintenance: scheduled batch 10; command range 1–20; settings fallback 5.
- Shared AliExpress locking/cadence/retries/backoff/jitter/Retry-After/rate-limit breaker remain unchanged.
- Shared state: `/run/lowcost-europa/`; preserve tmpfiles provisioning and PrivateTmp=true.
- HIFU logistics recovery remains paused independently of weekly discovery.

## Accepted storefront

- `VER EQUIPAMENTOS E PREÇOS` → `#familias`.
- Existing five public family names/order preserved.
- `VER PREÇO E COMPRAR NO ALIEXPRESS` → `/go/<offer_id>/` only.
- WhatsApp: `/contactar/whatsapp/` → `351965471236`.
- Public reads use PostgreSQL, not AliExpress. Purchase/payment/order support belongs to the partner.
- OfferClicks are outbound clicks, not sales/commission evidence.

## Infrastructure and evidence boundaries

Owner policy: one OVH VPS, GitHub-hosted workflows, credentials outside source control in the VPS cofre. Historical documents do not authorize paid provider backups or old administration tooling.

Versioned PostgreSQL/Restic scripts, systemd units and regression tests remain recovery implementations. Their presence does not prove active timers or authorize reinstating old backup policy. Current backup health, packages/kernel, systemd state and runtime SHA require live host verification; September snapshots are historical.

Technical closeout did not authorize public launch/indexing. Fail-closed indexing controls remain. No legal/commercial activation is certified by this cleanup.

## Document authority

Read PROJECT_CONSTITUTION.md, PROJECT_STATE.md and AGENTS.md in order. Catalog rules: docs/catalog/CATALOG-CONSTITUTION.md. Architecture: docs/ARQUITETURA-DO-SITE.md.

Phase reports, initial ADRs, old runbooks and QA captures are checkpoint evidence only. They cannot reopen completed tasks, supersede current authorization or restore old rules/infrastructure. See docs/README.md. Git history retains superseded versions.
