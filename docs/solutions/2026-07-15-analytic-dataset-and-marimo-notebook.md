# Analytic dataset and marimo notebook

Date: 2026-07-15

## Problem

The study needed one auditable analytic dataset and one marimo notebook that a
biostatistician can run from top to bottom. The dataset had to support the primary
Chicago community-area case studies and a census-tract sensitivity layer without
inventing disease values from interpolation, census covariates, or shapefile logic.

## Evidence

- The first-party ChicagoHealthMap/CAPriCORN export includes direct community-area
  and census-tract condition-stat tables.
- The local S4 methods dictionary accepts ChicagoHealthMap website definitions for
  geography, capture, suppression, and source-position mappings.
- The repo contains authoritative 2024 tract-to-community-area overlay weights
  generated from projected polygon intersections between TIGER tracts and official
  Chicago community-area boundaries.
- The direct primary paper frame is the 77 City of Chicago community areas; tract
  rows are retained only when their tract GEOID appears in the authoritative Chicago
  overlay.

## Decision

Build `outputs/frozen/chicago_case_studies_analytic.*` as a long-form table with
grain:

`geography_type / geography_id / time_period / condition_id`

The dataset includes:

- direct community-area disease rows from `fact_community_area_condition_stats.text`;
- direct census-tract disease rows from `fact_tract_condition_stats.text`;
- no disease interpolation, rollup, centroid assignment, or census-derived disease
  values;
- tract-to-community-area linkage metadata from `tract_community_overlay_2024.parquet`;
- direct source labels, source geography IDs, source-position contracts, suppression
  flags, reliability/capture fields, comparator-role fields, schema JSON, lineage
  CSV, and a study manifest.

The paper-ordered marimo notebook `notebooks/00_master_chicago_healthmap_pipeline.py` derives model
and concordance frames visibly from the frozen dataset and writes deterministic CSV,
HTML, PNG, and JSON outputs under `outputs/notebooks/chicago_case_studies/`. Statistical
logic lives in tested modules; the notebook is a narrated orchestration and presentation
surface.

## Source boundary

- ChicagoHealthMap/CAPriCORN is the sole disease and EHR-exposure source.
- Chicago Health Atlas is a secondary public source used only for the life-expectancy
  outcome and reference validation. It is not CHP data and does not validate or replace
  CHP/CAPriCORN numerators, denominators, or disease measures.
- The user-supplied Chicago Health Atlas CSV was not ingested. Its 77 `VRLE_2024`
  values independently matched the already-frozen secondary Atlas outcome exactly;
  this check did not change the analytic dataset.
- Neither the Chicago Health Atlas file nor its total-population field is an ACS
  community-area covariate source. The approved adjustment covariates remain absent.

## Rejected alternatives

- Reconstruct community-area disease values from tract rows: rejected because direct
  community-area rows exist and the SAP prohibits replacing them with tract rollups.
- Assign tracts to community areas by centroid or guessed name: rejected because the
  authoritative overlay is available.
- Hide the 2022-2024 model-frame derivation inside helper code only: rejected; the
  notebook includes an explicit section describing the transformation.

## Verification

- The rebuilt dataset has 22,540 rows and 90 columns, 1,848 community-area records and
  20,692 census-tract records spanning 77 and 866 unique geographies, respectively,
  and zero duplicate primary keys. All 22,540 rows have
  `disease_value_derivation=direct_first_party_export_not_interpolated`.
- All four dataset-manifest checksums were recomputed successfully: CSV, Parquet,
  schema JSON, and lineage CSV.
- Focused dataset tests: `uv run pytest tests/unit/analysis/test_dataset.py -q`.
- Dataset build: `uv run chicagohealthmap analysis build-dataset --root . --output-dir outputs/frozen`.
- Notebook checks: `uv run marimo check --strict notebooks/00_master_chicago_healthmap_pipeline.py`
  and `uv run notebooks/00_master_chicago_healthmap_pipeline.py`.
- Two clean freeze runs produced the governed master output inventory. Every file,
  including the run manifest, was byte-identical across runs; the manifest records
  `git_dirty=false` and
  preserves `results_authorized=false` and
  `primary_adjusted_models_executed=false`.
- WASM audit: `docs/analysis/wasm_compatibility_case_studies.md`.

The requirement-level evidence and remaining gates are recorded in
`docs/analysis/sap_notebook_compliance_audit.md`.

## Analytic disposition

The notebook now emits governed resource, readiness, supported sensitivity, spatial,
influence, temporal, concordance, discordance, and multiplicity artifacts. Adjusted
primary C1 and C2 are intentionally withheld because the four approved
community-area covariates are not frozen. Unadjusted estimates are labeled
`supported_sensitivity_not_primary`; they are audit evidence, not manuscript results.
Reliability qualification is also withheld until a governed rule exists.

S7 independent numerical review and the results freeze remain open. Consequently,
`results_authorized` remains false, and no Results or Discussion claims are authorized.

## Reusable pattern

For scientific notebooks, keep source-faithful long-form frozen data separate from
model-ready derived frames. Derived frames may be created in the notebook when the
notebook visibly documents the purpose, method, and source columns used. Geographic
crosswalks should be metadata/linkage sources unless the SAP explicitly authorizes
weighted aggregation.
