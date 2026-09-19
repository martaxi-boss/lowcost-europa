# Lowcost Europa — Project State

Updated: 2026-09-19.

## Current State

- **APPLICATION:** HEALTHY
- **CURRENT MAIN/STAGING BASELINE:** `d86343e0ca1fcd4b12f7da81b4b710798674fb02`
- **BRANCH:** `main`
- **origin/main = deployed runtime:** YES
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
- **PUBLIC SERVICE HOSTNAME:** `https://lowcost-europa.duckdns.org`
- **Architecture:** FROZEN FOR CURRENT PILOT / VALIDATION PHASE
- **Current action:** Phase 4 ChangeSet 2 documentation closeout
- **Next human action:** Supervisor audits the documentation-only closeout PR
- **New product discovery:** NO
- **AliExpress live discovery/operations for this closeout:** NO

The current system is a controlled human-in-the-loop catalog workflow. It is **not** a fully automatic learning system and does not authorize autonomous product publication. Current ranking/learning logic remains deterministic and isolated by product family.

## Current Operational Architecture

Current pipeline:

`DISCOVERY → FAMILY RELEVANCE → GLOBAL DEDUPE → FAMILY-SPECIFIC RANKING / LEARNING → OFFER CANDIDATE → HUMAN OWNER REVIEW → APPROVE / REJECT / MOVE FAMILY → OFFER → EDITORIAL PUBLISH/HIDE → PUBLIC ELIGIBILITY → MAINTENANCE → REVALIDATION / DEACTIVATION`

Human Owner review remains an explicit lifecycle gate. Discovery and ranking can prepare candidates, but approval, editorial publication and protocol freshness remain controlled human/operational gates.

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

`protocol_verified_at` is the human protocol freshness timestamp.

- Current freshness window: **7 DAYS**.
- Automatic maintenance must not renew it.
- Human revalidation can renew it.
- A stale Offer becomes non-public-eligible until revalidated.

### Public eligibility

Current public eligibility is fail-closed and requires all of:

- `is_active=True`;
- `owner_hidden=False`;
- non-empty `affiliate_url`;
- non-null `protocol_verified_at`;
- protocol verification timestamp not in the future;
- protocol verification no older than the configured 7-day freshness window.

Current public eligibility does **not** require a non-null price or a non-`UNKNOWN` availability observation. Those remain editorial/launch-quality concerns rather than a silent change to the eligibility constitution.

Maximum public-eligible Offers per family remains **20** as a cap, not a volume target.

`/go/<offer>/` remains fail-closed through public eligibility.

## Current Taxonomy and Catalog Snapshot

Audited runtime snapshot on 2026-09-19:

- ProductFamilies total: **9**
- Non-retired/public-operational families: **5**
- Retired families retained historically: **4**
- Offers: **96**
- Public-eligible Offers: **51**
- Candidates: **359**
- CandidateDecisions: **227**
- OfferObservations: **407**
- OfferFamilyPlacements: **96**
- OfferClicks: **144**

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
- Current configured default batch size: **5**
- Command-enforced batch range: **1–20**
- Current cadence: **hourly**
- Concurrency remains single-operation through the existing global AliExpress lock/cadence controls.
- AliExpress safety behavior remains: operation locking, cadence control, retries, exponential backoff, jitter, `Retry-After`, HTTP 429 accounting/breaker, HTTP 5xx handling and transport-error handling.
- Runtime coordination remains under `/run/lowcost-europa/`.
- `PrivateTmp=true` remains compatible with the global `/run` coordination path.
- Factual unavailability may deactivate an active Offer.
- Transient external failures are not treated as factual unavailability.
- Inactive Offers are not automatically reactivated.
- Automatic maintenance does not renew human protocol freshness.

Latest catalog-maintenance service result: **success**, `ExecMainStatus=0`.

## Discovery / Learning Authorization State

Current Phase 4 closeout authorizes **no new product discovery** and **no AliExpress live discovery operations**.

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

No canonical/indexing activation is authorized by this documentation closeout.

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

Documentation closeout pre-edit regression audit on 2026-09-19:

- Django system check: **PASS**
- `makemigrations --check --dry-run`: **NO CHANGES**
- `migrate --plan`: **NO PLANNED MIGRATIONS**
- `pip check`: **PASS**
- Ruff: **PASS**
- Full automated suite: **494 / 494 PASS**

Current reconciled application baseline:

`d86343e0ca1fcd4b12f7da81b4b710798674fb02`

## Current Open Items

Factual open items after ChangeSet 2 / 2A:

- Phase 4 continues; this documentation closeout still requires Supervisor audit and merge authorization.
- `libfwupd2` and `libgusb2` remain autoremove candidates; this closeout does not remove them.
- 21 ESM Apps updates remain available only through Ubuntu Pro/ESM; Ubuntu Pro remains not attached.
- public launch remains unauthorized;
- public indexing remains disabled;
- legal/Owner launch review remains a human gate;
- later Phase 4 hardening/storefront/editorial work requires separate authorization.

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

No architecture rebuild is authorized by this documentation closeout.

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

Historical detailed evidence remains in repository audit and phase documents. This file now distinguishes those milestones from the live operating state above.

## Current Gate

- **PHASE 4 CHANGESET 2:** DOCUMENTATION CLOSEOUT IN PROGRESS
- **CURRENT ACTION:** DOCUMENTATION-ONLY RECONCILIATION
- **NEXT HUMAN ACTION:** SUPERVISOR AUDIT OF THE CLOSEOUT PR
- **NEW PRODUCT DISCOVERY:** NO
- **ALIEXPRESS LIVE DISCOVERY/OPERATIONS:** NO
- **PUBLIC LAUNCH:** NO
- **PUBLIC INDEXING:** OFF

[executed on device: ubuntu-s-1vcpu-1gb-lon1 (e3b7c8dd-8316-4238-9b0d-04b6728902ad)]