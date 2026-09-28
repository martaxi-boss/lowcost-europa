# Lowcost Europa — Project State

Updated: 2026-09-19.

## Current State

- **APPLICATION:** HEALTHY
- **PRE-CLOSEOUT APPLICATION / RUNTIME BASELINE:** `211c2047b408ee85b5b1d139a40a80d510305d2d`
- **CURRENT BRANCH:** `main`
- **RUNTIME APPLICATION BASELINE:** `211c2047b408ee85b5b1d139a40a80d510305d2d`
- **DEPLOYED APPLICATION CODE ALIGNED WITH LAST APPLICATION BASELINE:** YES
- **WORKTREE:** CLEAN
- **Kernel:** `6.8.0-139-generic`
- **Reboot required:** NO
- **Django service:** ACTIVE
- **Nginx:** ACTIVE
- **PostgreSQL:** ACTIVE
- **Remote Desktop Commander:** ACTIVE / ENABLED, version `0.2.51`
- **Catalog maintenance:** ACTIVE; hourly timer scheduled; latest service PASS
- **Local backup:** ACTIVE / ENABLED; latest service PASS
- **Offsite backup:** ACTIVE / ENABLED; latest service PASS
- **Offsite health:** ACTIVE / ENABLED; latest service PASS
- **PHASE 3:** CLOSED / APPROVED
- **PUBLIC LAUNCH:** NO
- **PUBLIC INDEXING:** OFF
- **NOINDEX:** ACTIVE
- **PUBLIC VALIDATION HOSTNAME:** `https://lowcost-europa.duckdns.org`
- **Architecture:** FROZEN / NO REBUILD AUTHORIZED
- **Current action:** Clean technical pilot baseline established and frozen. Platform is technically ready. Final domain, operator/business information and final legal/privacy content remain pending for future activation.
- **Next human action:** Owner decides when to provide final domain and operator/business information and initiate the final activation sequence.
- **Technical controlled pilot baseline:** AUTHORIZED / READY
- **External real-user pilot:** PENDING FINAL ACTIVATION INPUTS
- **New product discovery:** NO
- **HIFU logistics recovery:** PAUSED

`PROJECT_STATE.md` is documentation. A documentation-only merge may advance `main` without changing the deployed application/runtime code. Runtime synchronization, when required by governance, is a separate operation and does not by itself imply an application restart.

The current system is a controlled human-in-the-loop catalog workflow. It is **not** a fully automatic learning system and does not authorize autonomous product publication. Current ranking/learning logic remains deterministic and isolated by product family.

## Current Operational Architecture

Current pipeline:

`DISCOVERY → FAMILY RELEVANCE → GLOBAL DEDUPE → FAMILY-SPECIFIC RANKING / LEARNING → OFFER CANDIDATE → HUMAN OWNER REVIEW → APPROVE / REJECT / MOVE FAMILY → OFFER → EDITORIAL PUBLISH/HIDE → PUBLIC ELIGIBILITY → MAINTENANCE → REVALIDATION / DEACTIVATION`

Human Owner review remains an explicit lifecycle gate. Discovery and ranking can prepare candidates, but approval, editorial publication and initial protocol verification remain controlled human/operational gates.

### Global product identity

Global product identity remains:

`(source, external_product_id)`

- `OfferCandidate` and `Offer` preserve global source/external-product identity.
- Candidate and Offer may coexist as lifecycle phases of the same product.
- Products must not be silently cloned into new identities when moved between families.
- Seller/store uniqueness is **not** assumed because current evidence is insufficient to impose it.

## Owner Panel and Human Approval

The private Owner panel exists under `/painel/` and is restricted to authenticated staff users.

Current capabilities include:

- private login/logout and dashboard;
- family review views;
- approve and reject;
- revalidate protocol;
- hide an Offer from the storefront;
- publish an approved hidden Offer to the storefront;
- move a candidate to another non-retired family;
- move an approved candidate/Offer to another non-retired family while preserving lifecycle history;
- storefront management mode for staff.

Approval remains human protocol attestation. The current approval service:

- requires a staff user;
- creates/updates the Offer;
- generates/preserves the affiliate URL through the existing AliExpress client path;
- records `protocol_verified_at`;
- records a factual observation;
- creates/maintains family placement;
- records a CandidateDecision;
- does **not** automatically publish a newly approved Offer: editorial visibility remains controlled by `owner_hidden`.

## Current Shipping / Commercial Protocol

The sanctioned shipping-origin set remains:

`PL / CZ / FR / ES / DE`

The protocol continues to require human confirmation of delivery to Portugal and the approved commercial/editorial criteria. No unsupported AliExpress search parameter is invented to guarantee shipping origin.

`protocol_verified_at` is the human protocol verification timestamp.

- Initial protocol verification is required.
- Age expiry: **NONE**.
- Time passing alone does not make an otherwise eligible Offer non-public.
- Automatic maintenance must not create or renew human protocol verification.
- Human revalidation remains available as an explicit audit/update action but is not required solely because time passed.
- Factual unavailability controls deactivation; transient/UNKNOWN states do not.

### Public eligibility

Current public eligibility is fail-closed and requires all of:

- `is_active=True`;
- `owner_hidden=False`;
- non-empty `affiliate_url`;
- non-null `protocol_verified_at`;
- protocol verification timestamp not in the future;

Current public eligibility does **not** require a non-null price or a non-`UNKNOWN` availability observation. Those remain editorial/launch-quality concerns rather than a silent change to the eligibility constitution.

Maximum public-eligible Offers per family remains **20** as a cap, not a volume target.

`/go/<offer>/` remains fail-closed through public eligibility.

## Current Taxonomy and Catalog Snapshot

Audited read-only runtime/database snapshot at **2026-09-19T17:44:41Z**:

- ProductFamilies total: **9**
- Non-retired/public-operational families: **5**
- Retired families retained historically: **4**
- Offers: **96**
- Public-eligible Offers: **51**
- Candidates: **359**
- CandidateDecisions: **227**
- OfferObservations: **427**
- OfferFamilyPlacements: **96**
- OfferClicks: **144**

`Public-eligible` is a technical eligibility state, not a declaration that an Offer is commercially launch-ready. A prior launch-readiness audit found incomplete price, availability and logistics evidence across a material part of the technically eligible set. No public-eligibility rule or catalog record is changed by this documentation reconciliation. Commercial launch selection belongs to `PUBLIC CATALOG LAUNCH QUALITY GATE 001`.

Current non-retired family slugs:

1. `cavitacao-rf-vacuum-corpo`
2. `hydrodermoabrasao-aqua-facial-multifuncoes`
3. `pressoterapia-vacuum-drenagem`
4. `hifu`
5. `diodo-laser-remocao-tatuagens-pigmentacao`

The four retired ProductFamily records remain preserved as historical taxonomy records.

OfferClick counts are raw outbound click records. They do not by themselves establish unique users, purchases, commissions or conversions.

## Catalog Maintenance

- Management command: `maintain_catalog_offers`
- Settings/env default/fallback batch size: **5**
- Scheduled systemd maintenance batch: **10** (`--batch-size 10`)
- Command-enforced batch range: **1–20**
- Scheduled cadence: **hourly**
- Concurrency remains single-operation through the existing global AliExpress lock/cadence controls.
- AliExpress safety behavior remains: operation locking, cadence control, retries, exponential backoff, jitter, `Retry-After`, HTTP 429 accounting/breaker, HTTP 5xx handling and transport-error handling.
- Runtime coordination remains under `/run/lowcost-europa/`.
- `PrivateTmp=true` remains compatible with the global `/run` coordination path.
- Factual unavailability may deactivate an active Offer.
- Transient external failures are not treated as factual unavailability.
- Inactive Offers are not automatically reactivated.
- Automatic maintenance does not create or renew human protocol verification.

Latest catalog-maintenance service result: **success**, `ExecMainStatus=0`.

## Discovery / Learning Authorization State

Current Phase 4 state authorizes **no new product discovery** and **no AliExpress live discovery operations**.

Historic HIFU/Cavitation discovery and family-learning evidence remains in dedicated project/audit documents and in the historical section below. Those historic pilot gates must not be interpreted as authorization to start discovery now.

Learning remains deterministic and family-isolated where invoked by an authorized workflow. Country/logistics signals are not to be misused as semantic product-type penalties.

## Backups and Disaster Recovery

Phase 3 is **CLOSED / APPROVED**.

Current architecture remains:

`LOCAL POSTGRESQL BACKUP + ENCRYPTED OFF-SERVER RESTIC/R2`

Current audited operational state:

- local daily PostgreSQL timer: ACTIVE / ENABLED;
- offsite Restic backup timer: ACTIVE / ENABLED;
- offsite health timer: ACTIVE / ENABLED;
- latest local backup service: success;
- latest offsite backup service: success;
- latest offsite health service: success;
- offsite health `ExecMainStatus=0`;
- retention policy remains 7 daily / 4 weekly / 3 monthly;
- repository health and restore drill were validated during Phase 3;
- off-Droplet Restic recovery-password gate was confirmed by the Owner;
- the historical exposed Cloudflare `cfat_` token gate was confirmed revoked, with no current automation depending on the old token.

The bootstrap credentials required to reach/open Restic are intentionally not backed up into their own repository. Historical Phase 3 runbooks may retain their original gate wording as chronology; this Current State records the subsequently confirmed closeout.

## DuckDNS / Public Service Readiness

DuckDNS is the current **PUBLIC SERVICE HOSTNAME FOR NON-INDEXED VALIDATION**:

`https://lowcost-europa.duckdns.org`

Current audited responses:

- `/`: 200
- `/robots.txt`: 200
- `/health/live/`: 200
- `/health/ready/`: 200

DuckDNS is not an authorization for final public launch, Search Console or indexing.

## Phase 4 Security / Hardening Status

Completed Phase 4 milestones relevant to the current state:

- **PR #108 — Phase 4 ChangeSet 2 Documentation Closeout:** CLOSED / MERGED / COMPLETED. Merge commit: `74b94ba59cae71701a933637c91809dd2ab9d313`.
- **PR #109 — Private Login Protection 001:** CLOSED / MERGED / DEPLOYED / PASS. Merge commit: `aea78ebfb5dfebc142a085717d7a4eef69585844`.
  - Protects authentication POSTs on `/painel/entrar/` and `/admin/login/`.
  - Policy: 5 failed authentication POSTs per normalized source within 5 minutes, followed by temporary HTTP 429 throttling with `Retry-After`.
  - No permanent account lockout; username/account identity is not the limiter key.
  - No passwords or credentials are stored/logged by the limiter.
  - No Redis, new database table, migration or new dependency was introduced.
- **PRIVATE LOGIN RATE LIMITING 001:** DUPLICATE / ALREADY IMPLEMENTED / CLOSED through Private Login Protection 001; no second mechanism is authorized or required.
- **PR #110 — Nginx Server Tokens Hardening 001:** CLOSED / MERGED / DEPLOYED / PASS. Merge commit: `ffd4c9563927da3bcd60522a4b2286d130457456`.
  - Public Nginx header before: `Server: nginx/1.24.0 (Ubuntu)`.
  - Current public Nginx header: `Server: nginx`.

These closed controls must not be reimplemented as new Phase 4 work without a separate audited reason.

## Pre-Launch Gates

- **HSTS:** DEFERRED UNTIL FINAL COMMERCIAL DOMAIN.
- **CSP:** PENDING DEDICATED AUDIT.
- **FUTURE CHANGESET:** `CONTENT SECURITY POLICY AUDIT 001`.
- **FINAL COMMERCIAL DOMAIN:** PENDING OWNER DECISION.
- **LEGAL OPERATOR INFORMATION:** PENDING OWNER INPUT.
- **FINAL LEGAL / PRIVACY CONTENT:** PENDING FINAL INPUT / VALIDATION.
- **SEARCH CONSOLE:** NOT YET.
- **LEGAL / PRIVACY FINAL CONTENT:** PENDING FINAL INPUT / VALIDATION for future activation; commercial GO-LIVE remains NO.
- **PUBLIC CATALOG LAUNCH QUALITY GATE 001:** AUDITED / CLOSED FOR CURRENT EVIDENCE.
- **Current launch-evidence-complete Offers:** `#51`, `#59`, `#60`, `#61`, `#62` (5 total, audit evidence as of 2026-09-19).
- **Further HIFU logistics recovery:** PAUSED.
- **LEGAL / PRIVACY AUDIT:** COMPLETED.
- **LEGAL OPERATOR IDENTITY:** PENDING OWNER INPUT / LEGAL VALIDATION.
- **GO-LIVE:** NO.
- **PUBLIC INDEXING:** OFF.

Technical catalog evidence recovery does not authorize publication, external pilot traffic or commercial GO-LIVE. Search-based `<=5 days` evidence remains provenance-aware evidence, not a delivery guarantee.

## Public Launch / Indexing State

Current launch controls:

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=https://lowcost-europa.duckdns.org`
- `X-Robots-Tag: noindex, nofollow`
- `robots.txt`:

```text
User-agent: *
Disallow: /
```

**PUBLIC LAUNCH: NO**

**PUBLIC INDEXING: OFF**

No canonical/indexing activation is currently authorized.

## Current Software / OS Baseline

- Ubuntu 24.04 LTS
- Running kernel: `6.8.0-139-generic`
- Reboot required: NO
- Normal `dist-upgrade`: 0 upgraded / 0 new / 0 removed / 0 not upgraded
- `dpkg --audit`: CLEAN
- `apt-get check`: PASS
- `fwupd`: `2.0.20-1ubuntu2~24.04.2`
- `libfwupd3`: `2.0.20-1ubuntu2~24.04.2`
- legacy `libfwupd2`: `1.9.34-0ubuntu1~24.04.1`, retained only as an autoremove candidate
- `fwupd-refresh.service`: latest result success, `ExecMainStatus=0`
- failed systemd units: **0**
- Ubuntu Pro: **NOT ATTACHED**
- ESM Apps updates still reportable: **21**, not applied by this phase
- Remote Desktop Commander: `0.2.51`, ACTIVE / ENABLED under systemd persistence
- No separate stale/manual persistent `npx ... remote` process is expected or required.

## Tests and Regression Baseline

Most recent final controlled-pilot technical regression evidence:

- Django system check: **PASS**
- production deploy check: **PASS** with only the separately deferred HSTS warning
- `makemigrations --check --dry-run`: **NO CHANGES**
- `migrate --plan`: **NO PLANNED MIGRATIONS**
- `pip check`: **PASS**
- Ruff: **PASS**
- Full automated suite: **532 / 532 PASS**
- `nginx -t`: **PASS**
- `sshd -t`: **PASS**
- homepage / liveness / readiness: **200 / 200 / 200**
- local backup / offsite backup / offsite health: **PASS**
- failed systemd units: **0**

Current deployed application/runtime baseline:

`211c2047b408ee85b5b1d139a40a80d510305d2d`

## Current Open Items

Factual open/deferred items at this reconciliation:

- `libfwupd2` and `libgusb2` remain autoremove candidates; no autoremove is authorized here.
- 21 ESM Apps updates remain available only through Ubuntu Pro/ESM; Ubuntu Pro remains not attached.
- HSTS is **DEFERRED UNTIL FINAL COMMERCIAL DOMAIN**.
- CSP is **PENDING DEDICATED AUDIT**; the future isolated work item is `CONTENT SECURITY POLICY AUDIT 001`.
- final commercial domain: **PENDING**.
- legal/privacy audit: **COMPLETED**; operator identity/final approved legal content remain **PENDING OWNER INPUT / FINAL VALIDATION** for future activation.
- public catalog launch quality audit: **COMPLETED**; 5 Offers currently have complete launch evidence under the approved audit criteria.
- HIFU logistics recovery: **PAUSED**.
- external real-user pilot is **PENDING FINAL ACTIVATION INPUTS**; no technical lock or unblock operation is required.
- technical controlled-pilot baseline is **AUTHORIZED / READY**.
- public launch remains unauthorized.
- public indexing remains disabled.

## Infrastructure

Current core infrastructure remains:

- DigitalOcean Droplet;
- Django;
- PostgreSQL;
- Gunicorn;
- Nginx;
- systemd;
- Remote Desktop Commander systemd-managed remote administration;
- local PostgreSQL backups;
- Restic/R2 encrypted off-server backup.

No architecture rebuild is authorized.

## Security and Honesty Invariants

- Never promise guaranteed delivery without supporting proof.
- ProductFamily remains durable while Offers are lifecycle records.
- Observation history remains factual and append-oriented.
- Affiliate nature must be disclosed.
- No fake reviews, cloaking or invasive fingerprinting.
- Do not infer seller/store identity when API evidence is insufficient.
- Do not fabricate protocol confirmation, country, availability, decision or conversion evidence.
- Do not reinterpret raw OfferClick records as sales/conversions.
- Do not activate public indexing without a separate explicit authorization.

## Historical Milestones

The following chronology is retained as project history. It is **not** the current operational state.

- Phase 0 reconnaissance completed and ADR-001/ADR-002 were accepted.
- LE-001 through LE-004 established the foundation, AliExpress integration, catalog model and controlled persistence.
- LE-005 through LE-009 established controlled Portugal discovery, search precision, provenance-aware logistics evidence, conservative evidence assessment and temporal diagnostics.
- LE-010 introduced read-only longitudinal logistics history diagnostics.
- LE-011 created the first controlled live longitudinal HIFU cohort.
- LE-012 completed the authorized second observation round; Gate 12 closed and MVP transition was authorized. LE-013 longitudinal work was not authorized by default.
- Manual catalog curation Admin, storefront shell and production settings hardening were integrated.
- MVP LIVE CATALOG phases created the first real ProductFamilies and associated real Offers under human editorial control.
- `/go/<offer>/` and privacy-minimal raw outbound `OfferClick` tracking were introduced; raw staging clicks were explicitly not treated as users, sales or conversions.
- Real HTTPS staging was established through Nginx → Gunicorn → Django → PostgreSQL with systemd and fail-closed noindex controls.
- Local daily PostgreSQL backups and a restore drill were completed; off-server recovery remained pending authorization.
- Product imagery and desktop/mobile staging QA were performed; a known low-resolution HIFU source image remained an open non-blocking quality finding.
- VISUAL + COMMERCIAL READINESS, LAUNCH READINESS, CATALOG + COMMERCIAL READINESS, ALIEXPRESS API SAFETY and AUDIT + OPERATIONAL HYGIENE phases were completed and retained in their dedicated audit/project documents.
- CATALOG STRUCTURE 001, EIGHT-FAMILY TAXONOMY 001, STOREFRONT PLACEMENT MIGRATION 001 and STOREFRONT VISUAL & COMMERCIAL ENHANCEMENT 001 were approved, merged, deployed and closed.
- The public catalog moved to `OfferFamilyPlacement` as source of truth.
- Candidate discovery, global dedupe, family-specific deterministic learning, human review, public eligibility, maintenance and revalidation/deactivation were subsequently added and hardened.
- HIFU broad discovery was formally closed after the authorized final push; no further HIFU SEARCH calls are authorized in this phase.
- Automatic maintenance reactivation was prohibited and merged before the current baseline.
- The final five-option multi-signal rejection UI was merged and deployed in PR #80, leading to the then-current baseline `4abc19b636e2bf0b2f6068ee7b1065beb2a39b16`.
- PR #108 completed and merged the Phase 4 ChangeSet 2 documentation closeout at merge commit `74b94ba59cae71701a933637c91809dd2ab9d313`.
- PR #109 implemented, merged and deployed Private Login Protection 001 at merge commit `aea78ebfb5dfebc142a085717d7a4eef69585844`; runtime validation passed.
- PR #110 implemented, merged and deployed Nginx Server Tokens Hardening 001 at merge commit `ffd4c9563927da3bcd60522a4b2286d130457456`; public version disclosure was reduced from `Server: nginx/1.24.0 (Ubuntu)` to `Server: nginx`.
- PR #112 implemented, merged and deployed the existing-offer search/detail logistics observation capability at merge commit `211c2047b408ee85b5b1d139a40a80d510305d2d`; live use remained separately gated.
- Controlled live logistics evidence recovery established current launch-evidence-complete status for Offers `#51`, `#59`, `#60`, `#61`, `#62`; further HIFU recovery is paused.
- OWNER / LEGAL LAUNCH INFORMATION 001 completed read-only; legal operator identity and final legal/privacy content remain pending Owner/counsel input.

Historical detailed evidence remains in repository audit and phase documents. This file now distinguishes those milestones from the live operating state above.

## Current Gate

- **PHASE 4:** PRE-GO-LIVE READINESS.
- **CONTROLLED PILOT READINESS 001:** CLOSED / PASS (technical baseline).
- **REPOSITORY & RUNTIME HYGIENE AUDIT 001:** CLOSED / PASS.
- **HYGIENE CLEANUP 001:** CLOSED / PASS (safe temporary/cache residue only).
- **TECHNICAL CONTROLLED PILOT BASELINE:** AUTHORIZED / READY.
- **EXTERNAL REAL-USER PILOT:** PENDING FINAL ACTIVATION INPUTS.
- **LEGAL / PRIVACY AUDIT:** COMPLETED.
- **LEGAL OPERATOR IDENTITY:** PENDING OWNER INPUT / LEGAL VALIDATION.
- **FINAL COMMERCIAL DOMAIN:** PENDING.
- **HIFU RECOVERY:** PAUSED.
- **NEW MASS DISCOVERY:** NO.
- **ARCHITECTURE REBUILD:** NO.
- **PRIVATE LOGIN PROTECTION 001:** CLOSED / PASS.
- **NGINX SERVER TOKENS HARDENING 001:** CLOSED / PASS.
- **PUBLIC LAUNCH / COMMERCIAL GO-LIVE:** NO.
- **PUBLIC INDEXING:** OFF.
- **NEXT HUMAN ACTION:** Owner/legal counsel supplies and validates the remaining operator/legal information; Supervisor then decides whether an external real-user pilot can be authorized.
