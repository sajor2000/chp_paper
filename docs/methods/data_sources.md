# Authoritative public data sources

## Registry scope and status

The executable registry is `config/source_registry.yml`; the generated review view is
`sources/public/_registry/acquisition_matrix.csv`. Both contain exactly the 14 sources
prespecified for Phase 4. The registry records origin, release, geography, request,
fallback, citation, and verification evidence before any adapter code or new bulk
download is run. Police, 311, pharmacy, and WIC layers are deliberately absent.

All URLs below were checked on 2026-07-14 against the named publisher's domain. Existing
2026-07-13 raw snapshots remain frozen. A successful endpoint check does not authorize a
replacement download, and a daily-source update is not silently substituted for the
frozen snapshot.

## Registered source decisions

| Registry IDs | Official evidence and release | Decision supported |
|---|---|---|
| `chicago_health_atlas_life_expectancy`, `chicago_health_atlas_mortality` | Chicago Health Atlas [topic metadata](https://chicagohealthatlas.org/api/v1/topics/?limit=10000), [VRLE coverage](https://chicagohealthatlas.org/api/v1/coverage/VRLE/), and [VRDTHR coverage](https://chicagohealthatlas.org/api/v1/coverage/VRDTHR/) | Keep VRLE annual 2010–2024 life expectancy separate from VRDTHR five-year 2010–2014 through 2020–2024 age-adjusted all-cause mortality. Both use community-area (`neighborhood`) geography. Preserve `v` and `se`; life-expectancy `se` may be null. |
| `census_acs_2019_5y` | Census [2019 ACS 5-year developer page](https://www.census.gov/data/developers/data-sets/acs-5year/2019.html) and [sequence-based Summary File documentation](https://www.census.gov/programs-surveys/acs/data/summary-file/sequence-based.html) | Use the frozen Illinois tract/block-group archive for the pre-2020 vintage. |
| `census_acs_2022_5y`, `census_acs_2024_5y` | Census [table-based Summary File documentation](https://www.census.gov/programs-surveys/acs/data/summary-file.html), [2022](https://www.census.gov/data/developers/data-sets/acs-5year/2022.html), and [2024](https://www.census.gov/data/developers/data-sets/acs-5year/2024.html) developer pages | Use official table-based files and retain estimates, margins of error, and annotations. Across all ACS releases, register exactly B01001, B03002, B15003, B17001, B19013, B23025, B25044, and B27001. The 2026-07-13 observation request returned HTTP-200 HTML “Missing Key”; this remains the recorded reason for the bulk fallback even though credential-free metadata endpoints work. |
| `census_tiger_2019_tract`, `census_tiger_2020_tract`, `census_tiger_2023_tract`, `census_tiger_2024_tract` | Official Census TIGER/Line Illinois tract ZIPs for [2019](https://www2.census.gov/geo/tiger/TIGER2019/TRACT/tl_2019_17_tract.zip), [2020](https://www2.census.gov/geo/tiger/TIGER2020/TRACT/tl_2020_17_tract.zip), [2023](https://www2.census.gov/geo/tiger/TIGER2023/TRACT/tl_2023_17_tract.zip), and [2024](https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_17_tract.zip) | Retain all four exact vintages. The 2019 vintage supports 2019 ACS; 2023 is required by PLACES 2025; 2020 and 2024 make tract-vintage transitions explicit. All four URLs returned HTTP 200. |
| `cdc_places_current_tract` | CDC Socrata [dataset metadata](https://data.cdc.gov/api/views/yjkw-uj5s), dataset `yjkw-uj5s` | Register the 2025 release as model-based, not observed prevalence. Metadata specifies 2023 BRFSS for 35 measures, 2022 BRFSS for five biennial measures, Census 2020 population, ACS 2019–2023/2018–2022 inputs, and 2023 tract boundaries. Preserve crude estimates and confidence intervals for hypertension, diagnosed diabetes, and COPD. |
| `cdc_svi_2022_tract` | CDC/ATSDR [SVI documentation and downloads](https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html) and [Illinois CSV](https://svi.cdc.gov/Documents/Data/2022/csv/states/Illinois.csv) | Use SVI 2022. The official notice says `MP_CROWD` values were corrected 2024-12-11 because the earlier denominator used housing units rather than occupied housing units; rankings were unaffected. Do not treat release percentiles as an invariant longitudinal scale. |
| `hrsa_health_centers_current` | HRSA [Health Centers page](https://data.hrsa.gov/topics/health-centers), [official CSV](https://data.hrsa.gov/DataDownload/DD_Files/Health_Center_Service_Delivery_and_LookAlike_Sites.csv), and [ArcGIS layer 0](https://gisportal.hrsa.gov/server/rest/services/HealthCareFacilities/PrimaryHealthCareFacilities_FS/MapServer/0/) | Register Health Center Service Delivery and Look-Alike Sites. The page reported a daily refresh and update date of 2026-07-14. The file includes site address, state, ZIP, county/FIPS, and X/Y coordinates. Preserve the 2026-07-13 snapshot; treat the newer daily update as expected cadence, not unexplained drift. |
| `chicago_community_areas_current` | City of Chicago [Socrata metadata](https://data.cityofchicago.org/api/views/igwz-8jzy), dataset `igwz-8jzy` | Register the current, updated-as-needed boundary dataset and require exactly 77 community areas keyed by `area_numbe`. |
| `metopio_catalog` | Metopio [API v1 root](https://metop.io/api/v1/) | Register only the public catalog. Authenticated observation access remains pending a local user-supplied `METOPIO_API_TOKEN`; no credential is stored in the registry or command output. Cite originating agencies for analytical measures. |

## Tool fallbacks and gate interpretation

The required Tavily retry failed on 2026-07-14 with
`monthly_cap_reached_bonus_eligible`; it was not retried again and no credits, signup, or
bonus enrollment were used. Ref MCP required OAuth authorization and was unavailable.
Direct official pages, API metadata, and endpoint responses therefore provide the
implementation evidence. Chicago Health Atlas also blocked the general web search
crawler, but its first-party API responded directly.

No unexplained identifier, schema-definition, geography, or release drift was found in
this registry pass. HRSA's daily update is recorded explicitly. Gate 4 remains open:
Task 11 verifies the acquisition contract only; later tasks must acquire or validate each
authorized release, preserve checksums, harmonize vintages, and prove traceability.

## Required interpretation carried forward from Gate P

- ChicagoHealthMap EHR values are percentages diagnosed among observed adults represented
  in contributing systems. They are not population prevalence.
- PLACES estimates are model-based small-area estimates, not direct local survey estimates
  or EHR diagnosed percentages.
- Healthy Chicago Survey hypertension and diabetes values are self-reported clinician
  diagnoses among noninstitutionalized Chicago adults.
- ACS 5-year estimates cover 60 months; margins of error and exact release periods remain
  part of the analytical contract.
- Crude and age-adjusted measures remain distinct. Missing, suppressed, unreliable, and
  true-zero values remain distinct.
- Tract vintages must be matched or explicitly crosswalked before joining.

## Registry and integrity artifacts

- `config/source_registry.yml`: executable canonical 14-source acquisition contract.
- `sources/public/_registry/acquisition_matrix.csv`: deterministic human-review export.
- `sources/SOURCE_REGISTRY.yml`: inherited Gate P source and snapshot narrative.
- `sources/public/CHECKSUMS.sha256`: frozen public-source byte checksums.
- `sources/curated/metopio/CHECKSUMS.sha256`: frozen Metopio public-catalog checksums.

## Census adapter and frozen-snapshot reconciliation

Task 13 rechecked all 56 Census entries in `sources/public/CHECKSUMS.sha256`: 52 ACS
files and four TIGER/Line ZIPs were present and all 56 SHA-256 values matched. Together
they contain 1,696,367,614 bytes. Each 2019, 2020, 2023, and 2024 TIGER ZIP also passed
`ZipFile.testzip()` and contained seven members. This is a corruption and byte-identity
check, not proof that releases can be joined without later geography harmonization.

The frozen 2026-07-13 evidence predates the per-source `SnapshotManifest` contract. ACS
is stored as a combined `us_census_acs` bulk snapshot: the 2019 sequence-based Illinois
archive and the 2022/2024 table-based national files, with group metadata. TIGER is stored
as a combined `us_census_tiger_line` snapshot with all four registered official ZIPs.
Neither combined snapshot has a per-source `manifest.json`. They are therefore explicitly
classified as **verified legacy snapshots**, not silently relabeled or rewritten into the
new adapter's per-group API and per-source manifest format.

The five Task 13 acquisition targets—ACS 2019, 2022, and 2024 plus TIGER 2020 and 2024—are
present in the verified legacy evidence. TIGER 2019 and 2023 are also retained because
they remain registered dependencies for the 2019 ACS and PLACES 2025 vintages. The CLI
renders exact Census adapter dry-runs but disables live Census fetching by default and
directs reviewers to this frozen snapshot. No Census request or bulk download was made
during Task 13.

## Offline normalization, citations, and lineage

Task 16 verifies every record in `sources/public/CHECKSUMS.sha256` and
`sources/curated/metopio/CHECKSUMS.sha256` before reading a public snapshot. It then writes
source-faithful Parquet plus `.schema.json` companions under ignored
`data/interim/public/` and `data/processed/public/`. No live endpoint is contacted.

The materialization contains 15 tables and 645,421 rows: a 14-record registered-source
inventory; exact Atlas VRLE and VRDTHR observations; Cook County PLACES hypertension,
diagnosed-diabetes, and COPD model-based estimates; Cook County SVI ranks; Illinois HRSA
sites; 77 community-area boundaries; all four registered Cook County TIGER tract vintages;
paired estimate/MOE records for every registered 2022 and 2024 ACS detailed-table cell;
and authoritative 2020/2024 tract-to-community-area intersection overlays with conditional
unit weights, city-covered fractions, crossing-tract flags, and recorded slivers.
The legacy 2019 ACS sequence archive remains inventory/citation-only because no record-level
table is emitted until its sequence templates are decoded through an explicit, tested
positional contract.

`outputs/provenance/` contains a 16-record data-source inventory (14 public registry
snapshots, the restricted CAPriCORN/ChicagoHealthMap extract, and the archived website
methods), 16 CSL JSON/BibTeX dataset citations, 2,709 field-lineage records, and an empty
header-only table/figure registry because no Task 16 table or figure is registered for
publication. CAPriCORN citations use the archived approved CONSCIENCE citation, extract
date, and access restriction without exposing an absolute path. The methods glossary
informs that citation and source interpretation only; it cannot promote any of the 549
unverified export positions. Gate 3 therefore remains closed.

## 2024 ACS community-area covariate reconstruction

The governed community-area covariate artifact uses official 2024 ACS 5-year B01001 and
B17001 tract variance-replicate tables, 2020 TIGER Cook County block internal points, 2020
PL 94-171 P1 total block population, and the frozen City community-area boundary artifact.
Each block is assigned whole to one community area by its official internal point. Within
each tract, every ACS count component and each of its 80 replicates uses the same fixed P1
population weight; percentages are calculated only after allocated counts are aggregated.
The credential-free Census API did not supply the planned P12 sex-age block table, so the
implemented P1 fallback is labeled in the row-level provenance and manifest. Chicago Health
Atlas values remain secondary comparison data and are not used to define these covariates.
