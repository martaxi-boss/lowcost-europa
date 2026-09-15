# EIGHT-FAMILY TAXONOMY 001

## Scope

This phase establishes the approved eight-family commercial taxonomy without redesigning the storefront or changing AliExpress integration behavior.

No discovery, product import, equipment classification, live AliExpress API call, staging migration, deployment, or public indexing change is part of this phase.

## Canonical active taxonomy

1. `Cavitação + RF + Vacuum (corpo)` — `cavitacao-rf-vacuum-corpo`
2. `Hydrodermoabrasão / Aqua Facial / Multifunções faciais` — `hydrodermoabrasao-aqua-facial-multifuncoes`
3. `Radiofrequência facial` — `radiofrequencia-facial`
4. `Pressoterapia / Vacuum / Drenagem` — `pressoterapia-vacuum-drenagem`
5. `Microcorrente / Ultrassons` — `microcorrente-ultrassons`
6. `HIFU` — `hifu`
7. `Depilação Laser Triple Wave` — `depilacao-laser-triple-wave`
8. `Remoção de tatuagens / pigmentação` — `remocao-tatuagens-pigmentacao`

## Existing-family mapping

The historical HIFU 7D family (PK 1) becomes canonical `HIFU` and keeps its PK. The historical HIFU 22D MAX family (PK 2) is preserved and marked `RETIRED` with display order 99.

Existing families are renamed in place where possible:

- PK 3 -> `Cavitação + RF + Vacuum (corpo)`;
- PK 5 -> `Hydrodermoabrasão / Aqua Facial / Multifunções faciais`;
- PK 4 -> `Depilação Laser Triple Wave`.

Four new initially empty families are created for display positions 3, 4, 5 and 8. No products are invented to populate them.

## HIFU consolidation

Offer 51 remains the legacy primary in canonical HIFU. Offer 52 remains non-primary. Offer 53 moves from historical HIFU 22D MAX to canonical HIFU and becomes `is_primary=False` before the family move to avoid violating the legacy one-primary-per-family constraint.

HIFU placements after migration are editorial positions only:

- Offer 51 -> selection position 1;
- Offer 52 -> selection position `NULL`;
- Offer 53 -> selection position 2.

## Schema and ordering

Migration `0007_productfamily_display_order` adds `ProductFamily.display_order` with a safe default and changes model ordering to `display_order`, then `name`, then `pk`.

Migration `0008_eight_family_taxonomy` is the deterministic taxonomy data migration. It validates the expected historical baseline before transforming data and fails loudly on any unexpected non-empty state. A completely empty installation/test database is treated as a known no-op state so clean test database creation remains valid.

The data migration is atomic under Django's normal migration transaction behavior on PostgreSQL. Its reverse is intentionally a no-op: after editorial work exists, an automatic rollback cannot safely infer which later taxonomy/placement edits should be destroyed.

## Data preservation

The migration preserves:

- six Offers and unique `source + external_product_id` identity;
- fifteen OfferObservations in the audited baseline;
- all OfferClick rows present at migration time;
- six OfferFamilyPlacements;
- `equipment_type=UNKNOWN` for all six current Offers.

No duplicate Offer/Family placements or duplicate non-null selection positions are introduced.

## Storefront compatibility

The public storefront still reads legacy `Offer.product_family`; that read path is not migrated in this phase. Only the previously hardcoded factual sentence about five families is changed to say that the project has eight initial families and that the catalog is selected and still developing.

New empty families render normally. The retired historical HIFU family remains preserved and may remain accessible on staging/noindex until a later storefront redirect policy is authorized.

## Isolated migration proof

A temporary restored clone of the current staging database was migrated through `0007` and `0008`.

Before: `5 families / 6 offers / 15 observations / 35 clicks / 6 placements`.

After: `9 total families / 8 active / 1 retired / 6 offers / 15 observations / 35 clicks / 6 placements`.

Canonical HIFU contained Offers 51, 52 and 53; Offer 51 remained primary, Offer 53 became non-primary; placement positions were `1 / NULL / 2`; duplicate placement checks were zero. The temporary database and dump were removed after validation.

## Validation and deployment status

The full project suite passes 249/249 tests. Django check, migration drift check, Ruff, `git diff --check`, and `pip check` pass. The staging migration plan contains only catalog `0007` and `0008` as pending.

Staging/live remains applied only through `catalog.0006`; no migration or deployment from this phase has been applied there. AliExpress live operations during this phase: ZERO. Public noindex remains unchanged.
