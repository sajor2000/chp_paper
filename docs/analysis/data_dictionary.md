# First-party export data dictionary

Snapshot: `capricorn_chicagohealthmap_export_2026_05_27` (2026-05-27).

## Scientific status

**Gate 3: CLOSED for analysis-ready field use.** The ChicagoHealthMap website
data glossary is now accepted as the authoritative S4 methods dictionary for
measure definitions, geography, capture-rate, suppression, and standardized mean
difference semantics. The generated S4 packet is
`docs/analysis/s4_methods_mapping.json`.

The remaining blocker is narrower: the S4 packet now records guarded, defensible
position mappings for core case-study fields (geography, year, condition,
diagnosed-condition count, source-published measure, and capture rate). It also
records the spatial frame explicitly: CAPriCORN/ChicagoHealthMap source
provenance spans six-county Chicagoland, but case-study analytic shapefiles and
mapped outputs are restricted to City of Chicago geographies.

The schema catalog below intentionally remains generic until the downstream
analytic-dataset builder applies those guarded mappings, denominator safeguards,
and suppression rules in tested code. Observed values can establish file shape
and support candidate mappings, but they should not silently convert every
subgroup or denominator position into a final analysis contract.

No primary key or foreign key is final-analysis verified yet. Nullability is
conservatively true; unit is `source_text`. Suppression semantics are defined by
the website dictionary as fewer-than-10 display/output suppression; no dedicated
raw suppression flag is mapped. Adult-denominator reconstruction and subgroup
count/rate blocks remain guarded. These declarations prevent a plausible
positional interpretation from becoming an overbroad analysis contract.

## Public normalized table contract

Public-source normalization is independent of the blocked first-party export. Every row
has `source_id`, `snapshot_id`, `source_record_id`, a JSON `source_field_map`,
`release_vintage`, `geography_type`, `geography_id`, and `time_period`. Every Parquet file
has a `.schema.json` companion recording its columns, logical types, row count, and schema
version. No normalized table has an unqualified field named `prevalence`.

| Table family | Source-faithful value fields | Interpretation |
| --- | --- | --- |
| `chicago_health_atlas_life_expectancy` | `indicator_id`, `indicator_label`, `estimate`, `standard_error` | Exact published label `Life expectancy` and topic `VRLE`; not mortality. |
| `chicago_health_atlas_mortality` | `indicator_id`, `indicator_label`, `estimate`, `standard_error` | Exact published label `All-cause mortality rate` and topic `VRDTHR`; not life expectancy. |
| `cdc_places_current_tract` | `measure_id`, `measure_type`, `model_based_estimate`, `confidence_interval` | `measure_type` is always `model_based_estimate`; values are not direct survey or EHR prevalence. |
| `census_acs_2022_5y`, `census_acs_2024_5y` | `variable_id`, `estimate`, `estimate_state`, `margin_of_error`, `margin_of_error_state` | Each estimate remains paired with its exact ACS margin-of-error source field. Documented negative Census sentinel codes become missing values with explicit unavailable, not-applicable, controlled, or open-ended-median states; they are never published as measurements. |
| `cdc_svi_2022_tract` | `variable_id`, `svi_percentile_rank`, `svi_percentile_rank_state` | Release-specific overall/theme ranks; `-999` becomes missing with `not_available` state and is not an index value. Ranks are not an invariant longitudinal scale. |
| `hrsa_health_centers_current` | `site_name`, `site_type`, `longitude`, `latitude` | Illinois site records; officially suppressible coordinates remain missing. |
| `chicago_community_areas_current` | `community_area_name`, `geometry_wkt` | Exact valid 77-area polygon snapshot. |
| `census_tiger_{2019,2020,2023,2024}_tract` | `state_fips`, `county_fips`, `geometry_wkt`, `crs`, `tract_vintage` | Cook County tract polygons retain their exact vintage; vintages are never silently joined. |
| `tract_community_overlay_{2020,2024}` | `community_area_id`, `intersection_area`, `weight`, `covered_fraction`, crossing/sliver flags | Projected polygon intersections from frozen TIGER and City boundaries; weights sum to one across each tract's Chicago-intersecting area and retain both source snapshots. |
| `source_inventory` | organization, title, catalog ID, license | One record for each of the 14 verified public registry sources; this is provenance, not an observation table. |

The reusable geography contract requires 11-digit Illinois tract GEOIDs (`17`), Cook
County FIPS `031` for included Chicago tracts, valid nonempty geometry, and a declared
projected CRS for area weighting. Tract-to-community-area weights use polygon
intersection area, record slivers and crossing tracts, and must sum to one within tolerance;
centroid-only assignment is prohibited.

The 2019 ACS sequence-based archive is not emitted as record-level Parquet in Task 16.
Its citation and immutable snapshot inventory are complete, but positional decoding is
withheld pending a tested template/sequence contract. This limitation does not relabel or
discard the source bytes.

## Table inventory

| File | Rows | Observed field counts | Primary key | Foreign keys | Suppression | Status |
| --- | ---: | --- | --- | --- | --- | --- |
| `community_area_description_facts.text` | 77 | 20 | none verified | none verified | unverified | 20 unverified positions; analysis blocked |
| `dim_aldermanic.text` | 50 | 18 | none verified | none verified | unverified | 18 unverified positions; analysis blocked |
| `dim_census_tracts.text` | 3265 | 20 | none verified | none verified | unverified | 20 unverified positions; analysis blocked |
| `dim_community_area_reliability_crosswalk.text` | 77 | 7 | none verified | none verified | unverified | 7 unverified positions; analysis blocked |
| `dim_community_areas.text` | 77 | 17 | none verified | none verified | unverified | 17 unverified positions; analysis blocked |
| `dim_conditions.text` | 39 | 11 | none verified | none verified | unverified | 11 unverified positions; analysis blocked |
| `dim_congressional_districts.text` | 17 | 17 | none verified | none verified | unverified | 17 unverified positions; analysis blocked |
| `dim_tract_reliability_crosswalk.text` | 3265 | 7 | none verified | none verified | unverified | 7 unverified positions; analysis blocked |
| `dim_ward_reliability_crosswalk.text` | 50 | 7 | none verified | none verified | unverified | 7 unverified positions; analysis blocked |
| `dim_zcta.text` | 400 | 16 | none verified | none verified | unverified | 16 unverified positions; analysis blocked |
| `dim_zcta_reliability_crosswalk.text` | 400 | 7 | none verified | none verified | unverified | 7 unverified positions; analysis blocked |
| `drug_providers.text` | 0 | none | none verified | none verified | unverified | expected empty; semantics unresolved |
| `fact_chicago_condition_prevalence.text` | 234 | 7 | none verified | none verified | unverified | 7 unverified positions; analysis blocked |
| `fact_community_area_condition_stats.text` | 17836 | 67 | none verified | none verified | unverified | 67 unverified positions; analysis blocked |
| `fact_community_area_vulnerability.text` | 77 | 40 | none verified | none verified | unverified | 40 unverified positions; analysis blocked |
| `fact_congress_condition_stats.text` | 3096 | 67 | none verified | none verified | unverified | 67 unverified positions; analysis blocked |
| `fact_tract_condition_stats.text` | 342273 | 67 | none verified | none verified | unverified | 67 unverified positions; analysis blocked |
| `fact_ward_condition_stats.text` | 11698 | 67 | none verified | none verified | unverified | 67 unverified positions; analysis blocked |
| `fact_zcta_condition_stats.text` | 66903 | 67 | none verified | none verified | unverified | 67 unverified positions; analysis blocked |
| `svi_2020.text` | 3263 | 20 | none verified | none verified | unverified | 20 unverified positions; analysis blocked |
| `wic_locations.text` | 0 | none | none verified | none verified | unverified | expected empty; semantics unresolved |

## Ordered field contracts

Every entry below is one-based and exact. Each has type `string`, nullable `true`,
key role `none`, unit `source_text`, evidence status `unverified`, and evidence
source “2026-05-27 export: observed position and field count only; semantic owner
evidence absent.” The five 67-field condition-stat tables additionally lack positional
owner evidence for subgroup and measure semantics.

### `community_area_description_facts.text`

- `community_area_description_facts.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `community_area_description_facts.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.

### `dim_aldermanic.text`

- `dim_aldermanic.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `dim_aldermanic.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.

### `dim_census_tracts.text`

- `dim_census_tracts.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `dim_census_tracts.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.

### `dim_community_area_reliability_crosswalk.text`

- `dim_community_area_reliability_crosswalk.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_community_area_reliability_crosswalk.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.

### `dim_community_areas.text`

- `dim_community_areas.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `dim_community_areas.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.

### `dim_conditions.text`

- `dim_conditions.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_conditions.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.

### `dim_congressional_districts.text`

- `dim_congressional_districts.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `dim_congressional_districts.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.

### `dim_tract_reliability_crosswalk.text`

- `dim_tract_reliability_crosswalk.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_tract_reliability_crosswalk.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.

### `dim_ward_reliability_crosswalk.text`

- `dim_ward_reliability_crosswalk.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_ward_reliability_crosswalk.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.

### `dim_zcta.text`

- `dim_zcta.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `dim_zcta.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.

### `dim_zcta_reliability_crosswalk.text`

- `dim_zcta_reliability_crosswalk.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `dim_zcta_reliability_crosswalk.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.

### `drug_providers.text`

No fields observed. `empty_expected: true`; the absence of rows does not establish an intended production schema.

### `fact_chicago_condition_prevalence.text`

- `fact_chicago_condition_prevalence.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_chicago_condition_prevalence.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.

### `fact_community_area_condition_stats.text`

- `fact_community_area_condition_stats.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_41` — position 41; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_42` — position 42; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_43` — position 43; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_44` — position 44; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_45` — position 45; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_46` — position 46; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_47` — position 47; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_48` — position 48; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_49` — position 49; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_50` — position 50; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_51` — position 51; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_52` — position 52; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_53` — position 53; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_54` — position 54; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_55` — position 55; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_56` — position 56; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_57` — position 57; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_58` — position 58; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_59` — position 59; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_60` — position 60; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_61` — position 61; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_62` — position 62; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_63` — position 63; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_64` — position 64; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_65` — position 65; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_66` — position 66; string; nullable; no key role; source_text; unverified.
- `fact_community_area_condition_stats.text:unverified_position_67` — position 67; string; nullable; no key role; source_text; unverified.

### `fact_community_area_vulnerability.text`

- `fact_community_area_vulnerability.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_community_area_vulnerability.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.

### `fact_congress_condition_stats.text`

- `fact_congress_condition_stats.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_41` — position 41; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_42` — position 42; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_43` — position 43; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_44` — position 44; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_45` — position 45; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_46` — position 46; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_47` — position 47; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_48` — position 48; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_49` — position 49; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_50` — position 50; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_51` — position 51; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_52` — position 52; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_53` — position 53; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_54` — position 54; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_55` — position 55; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_56` — position 56; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_57` — position 57; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_58` — position 58; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_59` — position 59; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_60` — position 60; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_61` — position 61; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_62` — position 62; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_63` — position 63; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_64` — position 64; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_65` — position 65; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_66` — position 66; string; nullable; no key role; source_text; unverified.
- `fact_congress_condition_stats.text:unverified_position_67` — position 67; string; nullable; no key role; source_text; unverified.

### `fact_tract_condition_stats.text`

- `fact_tract_condition_stats.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_41` — position 41; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_42` — position 42; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_43` — position 43; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_44` — position 44; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_45` — position 45; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_46` — position 46; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_47` — position 47; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_48` — position 48; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_49` — position 49; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_50` — position 50; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_51` — position 51; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_52` — position 52; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_53` — position 53; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_54` — position 54; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_55` — position 55; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_56` — position 56; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_57` — position 57; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_58` — position 58; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_59` — position 59; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_60` — position 60; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_61` — position 61; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_62` — position 62; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_63` — position 63; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_64` — position 64; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_65` — position 65; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_66` — position 66; string; nullable; no key role; source_text; unverified.
- `fact_tract_condition_stats.text:unverified_position_67` — position 67; string; nullable; no key role; source_text; unverified.

### `fact_ward_condition_stats.text`

- `fact_ward_condition_stats.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_41` — position 41; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_42` — position 42; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_43` — position 43; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_44` — position 44; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_45` — position 45; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_46` — position 46; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_47` — position 47; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_48` — position 48; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_49` — position 49; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_50` — position 50; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_51` — position 51; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_52` — position 52; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_53` — position 53; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_54` — position 54; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_55` — position 55; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_56` — position 56; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_57` — position 57; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_58` — position 58; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_59` — position 59; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_60` — position 60; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_61` — position 61; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_62` — position 62; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_63` — position 63; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_64` — position 64; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_65` — position 65; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_66` — position 66; string; nullable; no key role; source_text; unverified.
- `fact_ward_condition_stats.text:unverified_position_67` — position 67; string; nullable; no key role; source_text; unverified.

### `fact_zcta_condition_stats.text`

- `fact_zcta_condition_stats.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_21` — position 21; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_22` — position 22; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_23` — position 23; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_24` — position 24; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_25` — position 25; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_26` — position 26; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_27` — position 27; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_28` — position 28; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_29` — position 29; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_30` — position 30; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_31` — position 31; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_32` — position 32; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_33` — position 33; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_34` — position 34; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_35` — position 35; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_36` — position 36; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_37` — position 37; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_38` — position 38; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_39` — position 39; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_40` — position 40; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_41` — position 41; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_42` — position 42; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_43` — position 43; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_44` — position 44; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_45` — position 45; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_46` — position 46; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_47` — position 47; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_48` — position 48; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_49` — position 49; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_50` — position 50; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_51` — position 51; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_52` — position 52; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_53` — position 53; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_54` — position 54; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_55` — position 55; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_56` — position 56; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_57` — position 57; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_58` — position 58; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_59` — position 59; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_60` — position 60; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_61` — position 61; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_62` — position 62; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_63` — position 63; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_64` — position 64; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_65` — position 65; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_66` — position 66; string; nullable; no key role; source_text; unverified.
- `fact_zcta_condition_stats.text:unverified_position_67` — position 67; string; nullable; no key role; source_text; unverified.

### `svi_2020.text`

- `svi_2020.text:unverified_position_01` — position 1; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_02` — position 2; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_03` — position 3; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_04` — position 4; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_05` — position 5; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_06` — position 6; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_07` — position 7; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_08` — position 8; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_09` — position 9; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_10` — position 10; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_11` — position 11; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_12` — position 12; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_13` — position 13; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_14` — position 14; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_15` — position 15; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_16` — position 16; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_17` — position 17; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_18` — position 18; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_19` — position 19; string; nullable; no key role; source_text; unverified.
- `svi_2020.text:unverified_position_20` — position 20; string; nullable; no key role; source_text; unverified.

### `wic_locations.text`

No fields observed. `empty_expected: true`; the absence of rows does not establish an intended production schema.

## Evidence required to unblock Gate 3

A data owner must provide a versioned, export-specific ordered column definition for
all 19 nonempty files, including names, types, null rules, keys, units, and suppression
encoding. For each 67-field condition-stat table, evidence must identify the geography,
year, condition, overall numerator, adult denominator, overall diagnosed proportion,
source, load timestamp, active flag, and every subgroup numerator/denominator/proportion
triplet. The two empty exports require an owner statement of intended schema and whether
empty delivery was expected. Until then Task 9 ingestion must not treat these positions
as semantic fields.
