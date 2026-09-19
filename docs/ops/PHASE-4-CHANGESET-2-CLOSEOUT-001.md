# PHASE 4 — CHANGESET 2 CLOSEOUT 001

## Authority / Scope

Authority: Supervisor / Engineering Authority. Consultant / Owner approval confirmed.

This document closes the **documentation reconciliation** for Phase 4 ChangeSet 2 after OS maintenance, controlled reboot, Remote Desktop Commander recovery and the dedicated fwupd ChangeSet 2A.

This closeout is documentation-only. It does not authorize application, runtime, systemd, Nginx, SSH, firewall, database, catalog, AliExpress, backup, R2/Restic, DNS, legal, storefront, GO-LIVE or indexing changes.

Production baseline audited for this closeout:

`d86343e0ca1fcd4b12f7da81b4b710798674fb02`

At audit time: `main = origin/main = deployed runtime`, branch `main`, worktree clean.

## OS Maintenance Result

Phase 4 ChangeSet 2 applied **62 standard Ubuntu 24.04 updates** from the already configured official repositories.

No Ubuntu Pro attachment, ESM enablement, additional repository, PPA, distribution upgrade or autoremove was authorized or performed.

A controlled DigitalOcean reboot completed.

Post-reboot/current audited state:

- running kernel: `6.8.0-139-generic`;
- reboot-required: NO;
- `dpkg --audit`: clean;
- `apt-get check`: pass;
- normal `apt-get -s dist-upgrade`: 0 upgraded, 0 newly installed, 0 removed, 0 not upgraded;
- root filesystem approximately 55% used with approximately 11 GB free;
- `/boot` healthy.

## Remote Desktop Commander Incident

After the controlled reboot, the previous Remote Desktop Commander agent did not reconnect automatically, temporarily blocking post-reboot host validation through that management channel.

The incident was repaired separately before this closeout:

- Desktop Commander was upgraded from **0.2.50 to 0.2.51**;
- the stale old device registration was revoked;
- a new device registration became operational;
- `desktop-commander-remote.service` is now **ACTIVE / ENABLED**;
- systemd owns the persistent remote process;
- no separate stale/manual persistent `npx ... remote` process is required.

No private device authentication material, token or credential is recorded in this document.

## FWUPD Incident and ChangeSet 2A

The OS update/reboot audit exposed an fwupd daemon/library mismatch:

- daemon package: `fwupd 1.9.30-0ubuntu1~24.04.1`;
- installed legacy library: `libfwupd2 1.9.34-0ubuntu1~24.04.1`.

The mismatch produced a failed fwupd refresh state and required a dedicated, bounded remediation rather than unrelated package changes.

Phase 4 **ChangeSet 2A — FWUPD PACKAGE RECONCILIATION** used only the already configured official Ubuntu Noble repositories.

The approved transition was:

- install `libfwupd3 2.0.20-1ubuntu2~24.04.2`;
- upgrade `fwupd` to `2.0.20-1ubuntu2~24.04.2`;
- remove zero packages;
- perform no autoremove;
- perform no reboot.

Final audited state:

- `fwupd`: `2.0.20-1ubuntu2~24.04.2`;
- `libfwupd3`: `2.0.20-1ubuntu2~24.04.2`;
- legacy `libfwupd2`: `1.9.34-0ubuntu1~24.04.1`, retained only as an autoremove candidate;
- `fwupdmgr` runtime: 2.0.20;
- `fwupdmgr get-devices`: PASS;
- `fwupd.service`: functional/active when invoked;
- a fresh `fwupd-refresh.service` run: `Result=success`, `ExecMainStatus=0`;
- failed systemd units after reconciliation: **0**;
- daemon/library mismatch: **RESOLVED**;
- reboot required after reconciliation: **NO**.

No `systemctl reset-failed` was used to conceal the original fault; a real successful refresh superseded the historical failed execution.

## Application Validation

Current audited service state:

- SSH: ACTIVE;
- Nginx: ACTIVE;
- PostgreSQL: ACTIVE;
- `lowcost-europa.service`: ACTIVE.

Current approved hostname:

`https://lowcost-europa.duckdns.org`

Audited HTTP results:

- `/`: 200;
- `/robots.txt`: 200;
- `/health/live/`: 200;
- `/health/ready/`: 200.

## Backups and Catalog Maintenance

Current audited backup state:

- `lowcost-europa-backup.timer`: ACTIVE / ENABLED;
- `lowcost-europa-offsite-backup.timer`: ACTIVE / ENABLED;
- `lowcost-europa-offsite-backup-health.timer`: ACTIVE / ENABLED;
- latest local backup service: `Result=success`, `ExecMainStatus=0`;
- latest offsite backup service: `Result=success`, `ExecMainStatus=0`;
- latest offsite health service: `Result=success`, `ExecMainStatus=0`.

Catalog maintenance remains scheduled hourly. Latest audited service result:

- `Result=success`;
- `ExecMainStatus=0`.

Phase 3 backup/disaster-recovery architecture remains **CLOSED / APPROVED** and is not modified by this closeout.

## Noindex / Public Launch

Search indexing remains fail-closed:

- `DJANGO_PUBLIC_INDEXING_ENABLED=false`;
- `robots.txt` returns:

```text
User-agent: *
Disallow: /
```

- HTTP header: `X-Robots-Tag: noindex, nofollow`.

**PUBLIC LAUNCH: NO**

**PUBLIC INDEXING: OFF**

This closeout does not authorize canonical/indexing activation, Search Console, GO-LIVE or live product discovery.

## Git / Regression Evidence

Exact current production baseline:

`d86343e0ca1fcd4b12f7da81b4b710798674fb02`

At the pre-document audit:

- branch: `main`;
- HEAD = origin/main = deployed staging;
- worktree: CLEAN.

Regression audit completed before documentation changes:

- Django system check: PASS;
- `makemigrations --check --dry-run`: NO CHANGES;
- `migrate --plan`: NO PLANNED MIGRATION OPERATIONS;
- `pip check`: PASS;
- Ruff: PASS;
- full automated test suite: **494 / 494 PASS**.

## Open Non-Blockers / Deferred Items

The following remain factual open/deferred items and are not resolved by this closeout:

- `libfwupd2` and `libgusb2` remain autoremove candidates; no autoremove is authorized here;
- 21 ESM Apps updates remain available only through Ubuntu Pro/ESM;
- Ubuntu Pro remains **NOT ATTACHED**;
- public launch remains unauthorized;
- public indexing remains OFF;
- later Phase 4 security/storefront/editorial/legal work requires separate Supervisor authorization.

These items do not reopen Phase 3 and are not permission to perform additional package or application changes.

## Closeout State

- OS MAINTENANCE: PASS
- CONTROLLED REBOOT: PASS
- FWUPD RECONCILIATION: PASS / CLOSED
- REMOTE DESKTOP COMMANDER: PASS
- APPLICATION HEALTH: PASS
- BACKUPS: PASS
- NOINDEX: PASS
- GIT ALIGNMENT: PASS
- DOCUMENTATION RECONCILIATION: READY FOR SUPERVISOR AUDIT
- GO-LIVE: NO
- PUBLIC INDEXING: OFF

Only the Supervisor may declare Phase 4 ChangeSet 2 final closeout accepted/closed after auditing the dedicated documentation PR.
