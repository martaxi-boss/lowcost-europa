# Lowcost Europa — Project State

Updated: 2026-09-17.

## Current State

- **APPLICATION:** HEALTHY
- **CURRENT MAIN/STAGING BASELINE:** `4abc19b636e2bf0b2f6068ee7b1065beb2a39b16`
- **Django service:** ACTIVE
- **Catalog maintenance:** ACTIVE
- **Backup timer:** ACTIVE
- **PUBLIC LAUNCH:** NO
- **NOINDEX:** ACTIVE
- **Architecture:** FROZEN FOR CURRENT PILOT PHASE
- **Current action:** documentation reconciliation only
- **Next human action:** Owner reviews the 7 current Cavitation candidates
- **New discovery before that review:** NO

The current system is a controlled human-in-the-loop catalog workflow. It is **not** a fully automatic system, **not** ML and **not** AI-based learning. Current learning is deterministic and isolated by product family.

## Current Operational Architecture

Current pipeline:

`DISCOVERY → FAMILY RELEVANCE → GLOBAL DEDUPE → FAMILY-SPECIFIC RANKING / LEARNING → OFFER CANDIDATE → HUMAN OWNER REVIEW → APPROVE / REJECT / MOVE FAMILY → OFFER → PUBLIC ELIGIBILITY → MAINTENANCE → REVALIDATION / DEACTIVATION`

Human Owner review remains an explicit lifecycle gate. Discovery and ranking can prepare candidates, but publication eligibility depends on the sanctioned protocol and human confirmation.

### Global product identity

Global product identity is:

`(source, external_product_id)`

- `OfferCandidate` is globally unique by that identity.
- `Offer` is globally unique by that identity.
- A Candidate and an Offer may coexist as different phases of the same product lifecycle.
- A product already known in another family must not be silently cloned into a new identity.
- `external_product_id` uniqueness: **YES**.
- Seller/store uniqueness guarantee: **NO**.

Seller/store identity has not been recovered with sufficient reliability to impose seller uniqueness. Do not infer seller identity.

## Owner Approval and Commercial Protocol

### Owner approval

**OWNER APPROVAL: ONE CLICK**

`APROVAR` means the human Owner confirms that the real listing fully complies with the Lowcost Europa protocol. Normal approval does not require selecting an individual country and no country is invented by the system.

### Current protocol

The commercial protocol currently includes:

- suitable product;
- acceptable listing;
- delivery to Portugal confirmed by the Owner;
- dispatch from one of `PL / CZ / FR / ES / DE`;
- the Owner's commercial/editorial criteria.

The five countries represent **ELIGIBILITY**, not ranking preference.

There is currently no documented/sanctioned Affiliate API filter reliable enough to search directly for `ship_from_country ∈ PL/CZ/FR/ES/DE`. Do not invent such a parameter. Protocol confirmation therefore remains human.

## Protocol Freshness and Public Eligibility

`protocol_verified_at` records human protocol verification time.

- Current freshness window: **7 DAYS**.
- The window is configurable.
- A stale Offer stops being public-eligible.
- The Owner can revalidate it humanly.
- Automatic maintenance must **not** renew `protocol_verified_at`.

### Maximum per family

**MAX PUBLIC-ELIGIBLE OFFERS PER FAMILY: 20**

`20` is a **CAP**, not a target. The system must never force volume merely to reach 20.

### `/go/<offer>/`

`/go/<offer>/` remains fail-closed through public eligibility. An inactive or otherwise non-eligible Offer must not continue redirecting.

## Rejection UI — Final Model

The normal `REJEITAR` block is **CLOSED** with exactly five options:

1. `Sim, entrega em Portugal`
2. `Não entrega em Portugal`
3. `Não envia para Portugal`
4. `País de envio fora dos cinco permitidos`
5. `Anúncio indisponível`

- **MULTI-SELECT:** YES
- One human submission creates exactly **1 `CandidateDecision`**.
- Every selected signal is persisted in `review_signals`.
- The normal rejection flow does not invent a legacy primary reason.
- Historic legacy `reason` data remains preserved and supported.

### Five-option product decision

Do **not** add `Acessório / peça / consumível` as a sixth normal rejection option. The five normal rejection topics are closed.

### Candidate #34 historical exception

Cavitation Candidate `#34` entered before accessory-filter hardening. The filter was later corrected to block future occurrences of that pattern. The existing Candidate was deliberately preserved for human review.

If the Owner confirms that Candidate #34 is an accessory/part, use the already-existing historical technical classification:

`ACCESSORY_OR_PART`

Do not create a sixth normal UI option, do not alter Candidate #34 merely because of this documentation, and do not fabricate a decision.

## Learning Rules

Learning is deterministic and isolated by family.

- HIFU does not score Cavitation.
- Cavitation does not score HIFU.
- Country does not affect score.
- Logistics/availability rejection signals must not semantically penalize the machine/product type.
- `DELIVERS_TO_PT_CONFIRMED` is a positive protocol fact, not semantic negative learning.
- Legacy semantic negative history remains available when applicable, including historical semantic reasons such as `WRONG_FAMILY`, `ACCESSORY_OR_PART`, `IRRELEVANT` and `POOR_LISTING`.

## Current Family State

### HIFU — formal closeout

- **PILOT:** CLOSED
- **DISCOVERY:** CLOSED
- **TOTAL CANDIDATES:** 35
- **PENDING:** 0
- **APPROVED:** 14
- **REJECTED:** 21
- **CURRENT ELIGIBLE:** 14
- **MAX:** 20

Do not run new HIFU SEARCH discovery in the current phase.

HIFU discovery being closed does **not** mean approved Offers are abandoned. Approved HIFU Offers remain subject to protocol freshness, human revalidation, catalog maintenance, factual availability and public eligibility.

Therefore:

- **HIFU DISCOVERY:** CLOSED
- **HIFU OFFER LIFECYCLE:** ACTIVE

### Cavitação + RF + Vacuum Corpo — second pilot

- **SECOND PILOT:** ACTIVE / AWAITING OWNER REVIEW
- **Candidates:** 7
- **Pending:** 7
- **Approved:** 0
- **Rejected:** 0

No new Cavitation discovery is authorized until these 7 Candidates have been reviewed.

Authorized sequence:

1. Owner reviews the 7 current Candidates.
2. Decisions are persisted.
3. Supervisor audits the resulting family-specific learning.
4. Only then may a new limited Cavitation discovery be authorized.
5. Compare the quality of the second discovery with the first.

The objective is to prove reuse of the same engine on a second family without rebuilding architecture.

### Cavitation accessory hardening

The Cavitation profile was hardened to exclude future accessory patterns including:

- `accessory`;
- `accessories`;
- `accesories`;
- `stowage plate`;
- `stand support`;
- `replacement parts`;
- `consumables`;
- probes/handles when they are accessories.

Real Cavitation/RF/Vacuum combination machines must not be excluded merely because they are combos.

## Catalog Maintenance

- Management command: `maintain_catalog_offers`
- Current batch: **5**
- Current cadence: **6h**
- Service user: `le001_1789265592`
- Concurrency: **1**
- AliExpress safety layer: preserved

### Reactivation rule

Normal maintenance selects only `is_active=True` Offers.

Maintenance may perform:

`ACTIVE → INACTIVE`

when strong factual unavailability is established.

Maintenance must **not** perform:

`INACTIVE → ACTIVE`

Automatic reactivation is prohibited.

### Transient external errors

The following do not automatically deactivate an Offer:

- timeout;
- HTTP 429;
- HTTP 5xx;
- transport error;
- generic `AliExpressAPIError`.

Only strong factual unavailability may cause automatic deactivation.

## Current Global Data Snapshot

Audited current snapshot:

- ProductFamilies: **9**
- Offers: **20**
- Candidates: **42**
- CandidateDecisions: **37**
- OfferObservations: **41**
- OfferFamilyPlacements: **20**
- OfferClicks: **48**
- Candidate duplicates: **ZERO**
- Offer duplicates: **ZERO**

Staging `OfferClicks` do not necessarily represent unique users, purchases, sales or conversions.

## Tests and Current Software Baseline

- **FULL SUITE:** 345 / 345 PASS
- Django system check: **PASS**
- Latest Candidate rejection UI: **merged and deployed**
- Current reconciled application baseline: `4abc19b636e2bf0b2f6068ee7b1065beb2a39b16`

## Backups and Recovery

- Local daily PostgreSQL backup: **ACTIVE**.
- Pre-migration backup discipline: **MANDATORY**.
- Latest migration `0012`: validated backup was completed **before** migration application.
- Historical process issues from earlier migrations remain part of the audit history and must not be erased or rewritten.
- **OFF-SERVER BACKUP:** PENDING / NOT YET AUTHORIZED OR COMPLETED.

Off-server backup remains a pre-launch task and is not implemented by this reconciliation.

## Public Launch State

Current launch controls:

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`
- `DJANGO_PUBLIC_SITE_URL=`
- `X-Robots-Tag: noindex, nofollow`
- `robots.txt`:

```text
User-agent: *
Disallow: /
```

**PUBLIC LAUNCH: NO**

## Current Open Items

Pre-launch items still open, without being blockers for the second Cavitation pilot:

- off-server backup;
- final public domain;
- legal/public launch readiness;
- sales/commission attribution;
- conversion/revenue analytics;
- remaining image-quality issues;
- remaining family pilots.

## Infrastructure

Current infrastructure remains:

- DigitalOcean Droplet;
- Django;
- PostgreSQL;
- Gunicorn;
- Nginx;
- systemd.

Not currently authorized:

- Redis;
- Celery;
- Docker;
- new Droplet;
- new architecture.

No architecture rebuild is authorized for the current pilot phase.

## Security and Honesty Invariants

- Never promise guaranteed delivery without supporting proof.
- ProductFamily remains permanent while Offers are replaceable lifecycle records.
- Observation history remains factual and append-oriented.
- Affiliate nature must be disclosed.
- No fake reviews, cloaking or invasive fingerprinting.
- Do not infer seller/store identity when the API evidence is insufficient.
- Do not fabricate protocol confirmation, country, availability, decision or conversion evidence.

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
- The final five-option multi-signal rejection UI was merged and deployed in PR #80, leading to the current baseline `4abc19b636e2bf0b2f6068ee7b1065beb2a39b16`.

Historical detailed evidence remains in repository audit and phase documents. This file now distinguishes those milestones from the live operating state above.

## Current Gate

- **ARCHITECTURE:** FROZEN FOR CURRENT PILOT PHASE
- **HIFU:** CLOSED
- **REJECTION UI:** 5 OPTIONS — CLOSED
- **CAVITATION:** NEXT PILOT / AWAITING OWNER REVIEW
- **CURRENT ACTION:** DOCUMENTATION RECONCILIATION ONLY
- **AFTER THAT:** OWNER REVIEWS 7 CAVITATION CANDIDATES
- **NO NEW DISCOVERY UNTIL REVIEW COMPLETE**
- **PUBLIC LAUNCH:** NO
