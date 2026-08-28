# ChicagoHealthMap Raw Aggregate Data Audit

**Audit date:** August 27, 2026  
**Purpose:** Establish the data contract before statistical modeling  
**Authorization:** Methods and aggregate quality-control review only. `results_authorized=false` remains unchanged.

## Scope and evidence boundary

The read-only Neon PostgreSQL audit examined relation metadata, columns, keys,
geometries, relation comments, aggregate counts, and aggregate reconciliation
queries. The role reported `transaction_read_only=on`. No database objects were
created or modified, and no patient-level records were copied into the repository.

The database is not a patient-level extract. It contains aggregate
geography-condition-year records. It can establish the stored schema and test
internal aggregate consistency. It cannot independently verify MRAIA
deduplication, one contribution per adult per year, patient-level construction of
the annual denominator, or mutual exclusivity of diabetes phenotypes.

The machine-readable study contract is
`config/chm_study_data_contract.yml`. The executable audit is
`src/chicagohealthmap/analysis/raw_data_contract.py` and may be run with:

```bash
uv run python scripts/qa/audit_chm_raw_data.py --root .
```

## Stored analysis fields

The three 67-field condition tables share one ordered schema. The fields used by
the study are:

| Position | Database column | Study meaning |
| ---: | --- | --- |
| 2 | geography key | Tract GEOID, community-area identifier, or ZCTA |
| 3 | `dx_year` | Calendar year, 2019-2024 |
| 4 | `condition_key` | One of 39 condition definitions |
| 5 | `total_count` | Stored overall diagnosed-condition numerator |
| 25 | `denom_total_count` | Stored overall denominator |
| 45 | `prev_total_count` | Stored overall diagnosed proportion |
| 65 | `data_source` | `capricorn_ehr` in all condition facts |
| 66 | `loaded_at` | Database load timestamp |
| 67 | `is_active` | Source activity field |

Positions 6-24 contain numerator demographic strata, positions 26-44 contain
the corresponding denominator strata, and positions 46-64 contain the
corresponding stored proportions. All 67 names are retained in the machine-readable
contract.

## Geography inventory

| Geography | Dimension rows | Geometry | Fact geographies | Finding |
| --- | ---: | --- | ---: | --- |
| Census tract | 3,265 | Valid EPSG:4326 multipolygons | 2,168 | Dimension is statewide; facts include 2,047 six-county tracts plus 121 zero-only residual tracts |
| Community area | 77 | Valid EPSG:4326 multipolygons | 77 | Complete official Chicago frame |
| ZCTA | 400 | Valid EPSG:4326 multipolygons | 374 | Six-county and surrounding source frame |

Every tract, community-area, and ZCTA geometry in the frozen export was present,
nonempty, valid, and keyed uniquely.

The 121 fact tracts outside Cook, DuPage, Kane, Lake, McHenry, and Will Counties
contributed 684 rows. Every one had a zero numerator and zero denominator. They
are excluded from the study frame and must never be interpreted as observed
zero-diagnosis tracts.

## Primary tract contract

The tract table passed the primary raw-data contract:

- 342,273 rows, 2,168 stored tract identifiers, 39 conditions, and 2019-2024.
- No duplicate tract-condition-year keys.
- No negative numerators or denominators.
- No numerator exceeded its denominator.
- Every stored proportion was between 0 and 1.
- The denominator was constant across available conditions in all 12,477
  tract-years.
- For every positive denominator, `prev_total_count` exactly equaled
  `total_count / denom_total_count` within numerical tolerance.
- No positive tract numerator was between 1 and 9.

The tract estimand is therefore the crude annual EHR-diagnosed proportion among
observed CAPriCORN adults represented by the supplied denominator. It is not
population prevalence.

The stored tract denominator also exactly matched
`chm_tract_capture_annual.captured_patient_n` in all 12,124 tract-years linked
between the two relations. This establishes that the analysis denominator is the
annual captured-adult count supplied by the source. It does not independently
verify the upstream person-level eligibility or deduplication process. The
primary tract-year eligibility rule requires this denominator to be at least 30.

## Suppression and missingness

The condition facts contain no explicit suppression-status field. The tract table
contains 220,716 rows with a zero numerator and positive denominator, but no
positive numerator from 1 through 9. A stored zero may represent a true zero, a
suppressed count, or another source transformation. The analysis now labels this
state `zero_or_suppressed_unresolved`.

A missing geography-condition-year row is `not_observed_not_zero`. It must not be
imputed as zero. Positive counts below 10 in the higher-geography tables are
retained as source values but flagged as conflicting with the public suppression
description.

## Higher-geography reconciliation

The database relation comments describe community-area and ZCTA condition tables
as density-weighted. The database does not contain a tract-to-community-area or
tract-to-ZCTA weight table, transformation function, trigger, or view that
reconstructs those values.

| Check | Community area | ZCTA |
| --- | ---: | ---: |
| Geography-years | 462 | 1,978 |
| Geography-years with condition-varying denominator | 456 | 1,765 |
| Rows where stored proportion differs from numerator/denominator | 1,876 | 22,008 |
| Positive numerators below 10 | 12 | 2,958 |

These tables are not authorized as interchangeable estimates of the tract-level
annual denominator estimand. They may be used as labeled source-provided
density-weighted sensitivity measures after the source owner documents the exact
weighting, rounding, suppression, and denominator rules.

The 234 Chicago-wide condition-year rows exactly equal the ratio of summed
community-area numerators to summed community-area denominators. This establishes
internal reproducibility of the Chicago table but does not repair the underlying
condition-varying community-area denominators.

## Geographic linkage decisions

Any-intersection tract eligibility is prohibited. Boundary slivers can assign
tracts with negligible Chicago area to the city. Among 867 2024 TIGER tracts
with any overlap with the frozen union of 77 Chicago community areas, 782 had a
representative point covered by the city union and 779 had at least 50% of their
area covered by the union. The rules agreed for 777 tracts. The provisional
primary rule retains the 782 representative-point tracts. The 50% tract-area
rule is the prespecified sensitivity definition. Both require statistician
sign-off. A population-based crosswalk remains the preferred supplement if a
validated, vintage-compatible source becomes available.

Tract vintage must be explicit. The database linkage audit identifies 2010-to-2020
tract changes among otherwise eligible records. These records require a validated
population-weighted crosswalk or explicit exclusion.

## Capture and reliability

The annual tract condition denominator equals the linked annual captured-patient
count, as documented above. The separate static reliability `capture_rate` is a
supplied source field. It did not equal the annual captured-patient count divided
by the locally stored ACS adult count. The study must retain the supplied value
and its source label. It must not call the static field a 2022-2024 mean or
recompute it without the source formula.

## Required source-owner or statistician sign-off

1. Confirm whether tract zeroes represent true zero counts, suppression, or both.
2. Supply the exact community-area and ZCTA density-weighting and rounding algorithm.
3. Explain why higher-geography denominators vary by condition when the tract annual denominator does not.
4. Reconcile positive higher-geography counts below the stated suppression threshold.
5. Confirm the capture-rate numerator, denominator, reference year, and aggregation procedure.
6. Approve or revise the provisional representative-point Chicago tract rule and 50% area sensitivity.
7. Select exclusion or population-weighted crosswalking for 2010-to-2020 tract changes.
8. Confirm patient-level mutual exclusivity and denominator equivalence before combining diabetes categories.

Until these items are resolved, the primary inferential analysis is restricted to
the validated tract-level crude diagnosed proportion and all higher-geography
condition estimates remain descriptive or sensitivity-only.
