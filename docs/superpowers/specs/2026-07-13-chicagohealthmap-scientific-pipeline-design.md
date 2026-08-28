# ChicagoHealthMap Scientific Analysis Pipeline Design

**Date:** 2026-07-13

**First journal target:** JAMA Health Forum, Original Investigation

**Population:** Adults aged 18 years or older

**Primary geography:** City of Chicago census tracts and 77 community areas

**Primary period:** 2022-2024, with 2019 as a pre-pandemic baseline and 2020-2021 treated as a temporal disruption period

## 1. Program Goal and First Research Product

Design, build, and validate a reusable urban-health informatics research platform that converts ChicagoHealthMap/CAPriCORN electronic health record exports and public data into scientifically auditable evidence. The platform must support source preservation, phenotype and denominator validation, data-quality and representativeness assessment, disease discovery across all available conditions, prespecified statistical analysis, high-impact original research, local FQHC and community-based-organization planning, and adaptation by other cities with clinical data research networks.

The platform is broader than a single manuscript. Its first research product will target a JAMA Health Forum Original Investigation describing the informatics resource and evaluating whether multisystem EHR-derived diagnosed proportions reveal reliability-qualified small-area patterns associated with life-expectancy inequities. Any operational implication will be framed as a planning demonstration or hypothesis unless actual health-system, FQHC, or CBO use and outcomes are evaluated.

Three disease targets are leading candidates for two case studies, subject to a formal data-review, evidence-review, and statistical-analysis-plan gate:

1. **Cardiometabolic burden:** hypertension and diabetes without documented complication, examined jointly and separately.
2. **Respiratory burden:** chronic obstructive pulmonary disease.

Heart failure, cerebrovascular disease/stroke, and drug use disorder are comparator candidates. Hypertension, diabetes, and COPD will not be promoted merely because they produce the largest, most visually striking, or most statistically significant associations.

### Program workstreams

The platform will coordinate six linked but independently reviewable workstreams:

1. **Evidence and novelty:** reproducible biomedical and current-web searches, full-text verification, and a claim-level evidence matrix.
2. **Data resource:** immutable preservation, source provenance, phenotype definitions, denominator reconstruction, suppression handling, and geographic harmonization.
3. **Scientific discovery:** quality-qualified screening of all available chronic-disease conditions before final case-study selection.
4. **Statistical governance:** a versioned statistical analysis plan, explicit estimands, temporal alignment, spatial methods, multiplicity rules, and deviation logging.
5. **Translation:** careful assessment of how disclosure-safe results could inform FQHC/CBO inquiry, with no claim of improved allocation or outcomes unless evaluated.
6. **Dissemination:** reproducible marimo notebooks, Great Tables, JAMA-compatible figures and tables, a manuscript rule system, and reusable documentation for other cities.

## 2. Scientific Positioning

The EHR measure is an **EHR-diagnosed proportion among observed adults**, not population prevalence. The numerator is the exported number of adults with the specified diagnosis, and the denominator is the exported adult denominator shared by conditions within each geography-year. The resource reflects diagnosis, care access, coding, participating-system capture, and the underlying burden of disease.

All analyses are ecological, associational, and hypothesis-generating. Manuscript and notebook language must not claim that the selected conditions cause or drive the life-expectancy gap. Permitted language includes “associated with,” “spatially aligned with,” “correlated with,” and “identified areas where measures were discordant.”

The main novelty is not another disease map. It is a reproducible framework that:

- documents a multisystem EHR surveillance resource;
- quantifies coverage, reliability, suppression, and representativeness;
- triangulates EHR-diagnosed proportions with independent public-health measures;
- identifies concordant and discordant small-area patterns;
- shows how reliability-qualified information can guide local hypothesis generation and resource-planning conversations; and
- can be adapted by other cities with clinical data research networks.

## 3. Preliminary Decisions Requiring Formal Confirmation

Preliminary reconnaissance indicates that the current export contains six years, 39 conditions, 77 community areas, and more than 342,000 tract-condition records. These counts and all following observations must be reproduced by the tested data-review pipeline before they may enter the manuscript. Hypertension, diabetes, and COPD currently lead because they appear to combine scientific relevance, external comparability, coverage, and potential actionability.

- Hypertension has the strongest tract-level coverage and provides a stable small-area cardiometabolic signal.
- Diabetes is completely available at the community-area level and sufficiently available at the tract level to examine overlap and divergence from hypertension.
- COPD is nearly complete at the community-area level and aligns strongly with independent respiratory and mortality indicators, although tract-level small-cell suppression is more extensive.

Preliminary inspection suggests that the released age-specific numerators cannot support direct age standardization for all three targets. Suppressed age cells appear as zeros or otherwise lack enough information for reconstruction, especially for COPD. The formal data review must confirm the export convention and document the evidence. Unless a more complete authorized source resolves this limitation:

- exported overall diagnosed proportions are the primary EHR measures;
- area-level age composition is included as a covariate in adjusted ecological models;
- direct age-standardized estimates are used only if an authorized source supplies unsuppressed age-stratum aggregates or verified precomputed adjusted estimates; and
- age-specific descriptive results are limited to cells that meet the source disclosure rules.

## 4. Analytical Architecture

The project will use a layered architecture. Immutable source snapshots feed tested ingestion and validation modules. Those modules produce analysis-ready Parquet tables. Thin marimo notebooks call reusable package functions and display decisions, diagnostics, tables, maps, and model results. Notebook cells will not contain hidden data-cleaning logic that is absent from the tested Python package.

```text
immutable source snapshots
        |
        v
schema-aware ingestion --> provenance + quality reports
        |
        v
analysis-ready Parquet tables
        |
        +--> data-review marimo notebook
        +--> case-study selection marimo notebook
        +--> combined two-case-study marimo notebook
        +--> manuscript-output marimo notebook
```

### Proposed project structure

```text
ChicagoHealthMap-Data V1/
├── README.md
├── pyproject.toml
├── uv.lock
├── config/
│   ├── analysis.yml
│   ├── manuscript/
│   │   ├── core_integrity.yml
│   │   ├── observational_ehr.yml
│   │   └── jama_health_forum.yml
│   └── source_registry.yml
├── docs/
│   ├── analysis/
│   │   ├── statistical_analysis_plan.md
│   │   ├── data_dictionary.md
│   │   └── decision_log.md
│   ├── methods/
│   │   ├── chicagohealthmap_methods.md
│   │   ├── data_sources.md
│   │   ├── evidence_matrix.md
│   │   ├── manuscript_rules.md
│   │   ├── research_tools.md
│   │   └── visual_style.md
│   └── superpowers/
│       ├── specs/
│       └── plans/
├── sources/
│   ├── first_party/
│   │   ├── capricorn/snapshots/2026-05-27/original/
│   │   └── chicagohealthmap/snapshots/2026-07-13/
│   │       ├── original/
│   │       └── extracted/
│   └── public/
│       ├── _registry/
│       ├── chicago_health_atlas/snapshots/<date>/
│       │   ├── original/
│       │   ├── requests/
│       │   └── metadata/
│       ├── census_acs/snapshots/<date>/
│       ├── census_tiger_line/snapshots/<date>/
│       ├── cdc_places/snapshots/<date>/
│       ├── cdc_atsdr_svi/snapshots/<date>/
│       ├── hrsa/snapshots/<date>/
│       └── chicago_data_portal/snapshots/<date>/
├── data/
│   ├── interim/
│   └── processed/
├── src/chicagohealthmap/
│   ├── config.py
│   ├── schemas.py
│   ├── ingest.py
│   ├── provenance.py
│   ├── quality.py
│   ├── measures.py
│   ├── geography.py
│   ├── external.py
│   ├── acquire.py
│   ├── selection.py
│   ├── models.py
│   ├── tables.py
│   ├── figures.py
│   ├── style.py
│   └── manuscript.py
├── notebooks/
│   ├── 01_data_review.py
│   ├── 02_case_study_selection.py
│   ├── 03_case_studies.py
│   └── 04_manuscript_outputs.py
├── outputs/
│   ├── quality/
│   ├── provenance/
│   ├── tables/
│   ├── figures/
│   ├── models/
│   └── manuscript/
└── tests/
```

## 5. Source Preservation and Provenance

The existing pipe-delimited `.text` files will be copied without byte modification into the dated CAPriCORN snapshot. Source and snapshot SHA-256 checksums will be compared, and the original files will remain in place unless later cleanup is explicitly approved. The two supplied website scrape archives will be copied into the dated ChicagoHealthMap snapshot, extracted without overwriting either archive, and checksummed.

The archived ChicagoHealthMap website content will be treated as the definitive historical first-party record of how the displayed resource was described at that snapshot date. It will ground the resource Methods section, terminology, and interface behavior. If archived descriptions, exported fields, and empirical data behavior disagree, the discrepancy log will preserve all three sources and the manuscript will report the validated interpretation rather than silently privileging one.

Every source snapshot will include a machine-readable manifest recording:

- source name and owner;
- acquisition date and original path or URL;
- file name, byte size, SHA-256 checksum, and row count where applicable;
- observed delimiter, field count, and encoding;
- geographic and temporal coverage;
- privacy and suppression notes; and
- known methodological ambiguities.

Public external sources will be cached as dated, immutable API or official bulk-download snapshots. Acquisition code will never silently replace a prior snapshot. Processed tables will retain source-snapshot identifiers and variable-level lineage.

## 6. Data Ingestion and Quality Gates

Explicit schemas will be defined for every first-party table. Ingestion must fail with a clear error when a file has an unexpected field count, duplicate primary key, invalid year, invalid geography identifier, nonnumeric count, denominator below a numerator, or diagnosed proportion materially inconsistent with numerator divided by denominator.

The quality report will include:

- file inventory, checksums, dimensions, and schema results;
- unique-key and referential-integrity results;
- years, geographies, conditions, sources, and active-status domains;
- missingness and suppression patterns by condition, year, and geography;
- numerator, denominator, and diagnosed-proportion consistency;
- confirmation that condition denominators are shared within geography-year;
- subgroup denominator and numerator reconciliation diagnostics;
- capture and reliability distributions;
- demographic-representation flags;
- tract and community-area analytic coverage for each candidate condition; and
- discrepancies between exported fields and the archived website methods.

Suppressed zero values will not be interpreted as true absence. Until the export convention is documented, the pipeline will expose a `zero_or_suppressed` state and exclude those cells from analyses requiring known positive counts. No imputation of suppressed disease counts will be used in primary descriptive estimates.

## 7. External Public Data Acquisition, Organization, and Citation

The pipeline will implement an API-first, registry-driven acquisition system. Every required external dataset must be retrievable programmatically from its authoritative publisher, saved as an immutable raw snapshot, organized under a consistent source folder, and accompanied by enough metadata to cite its exact origin. If an authoritative agency does not provide a stable API for the required release or geographic file, the only permitted fallback is a scripted download from the agency's official versioned bulk-download endpoint. Manual browser downloads and third-party mirrors may be used for exploration but cannot be the final reproducible source.

### Expected acquisition matrix

| Source family | Required content | Preferred acquisition route | Required origin record |
|---|---|---|---|
| Chicago Health Atlas | Life expectancy, cause-specific mortality, chronic-disease and demographic indicators | Official machine-readable API or documented export endpoint | Publishing organization, dataset and indicator title, definition, period, geography, URL, access date, and release/update date |
| US Census Bureau ACS | Adult population, age, race and ethnicity, poverty, income, education, insurance, and housing | Official Census Data API using an explicit 5-year release and variable groups | US Census Bureau, survey/release, table and variable codes, query, geography, access date, and documentation URL |
| US Census Bureau TIGER/Line | Tract and other required boundary geometries and geographic identifiers | Official programmatic or versioned TIGER/Line distribution | US Census Bureau, product/vintage, geography, file URL, access date, and technical documentation |
| CDC PLACES | Hypertension, diabetes, COPD, and related model-based measures | Official Data.CDC.gov/Socrata API with dataset identifier, pagination, and release filters | CDC, PLACES release/model version, measure IDs, catalog ID, query, geography, access date, and methods URL |
| CDC/ATSDR SVI | Overall and theme-level vulnerability measures | Official API/catalog endpoint when stable; otherwise official versioned bulk file | CDC/ATSDR, release year, geography, dataset identifier, URL, access date, and documentation |
| HRSA | FQHC and service-delivery locations and approved organizational attributes | Official HRSA API, GIS feature service, or catalog endpoint when stable; otherwise official versioned bulk file | HRSA, dataset/program title, release/update date, endpoint/file URL, access date, and data dictionary |
| Chicago Data Portal | Approved health, service, or facility-location datasets | Official Socrata API using the dataset identifier and a saved query | Originating City department, dataset title/ID, query, update date, URL, license, and access date |

The matrix describes source families rather than asserting unverified endpoint URLs. During implementation, Tavily MCP will locate current authoritative documentation and Ref Context MCP will verify API behavior. A connector can be implemented only after its endpoint, versioning behavior, license, pagination, and geographic grain have been verified.

Other Illinois, Cook County, CDC/NCHS, or public mortality and health datasets may be added only after the source registry documents why each is required, how it differs from Chicago Health Atlas measures, and which organization is authoritative.

Before connector implementation, `sources/public/_registry/acquisition_matrix.csv` will record for every required dataset:

1. analytical purpose and variables required;
2. authoritative publishing organization and exact dataset title;
3. official landing page, documentation URL, API endpoint, and catalog identifier;
4. API query, geography, years, release/version, and expected row grain;
5. authentication, rate-limit, and terms-of-use requirements;
6. pagination or bulk-download method;
7. license, official citation, update cadence, and retention requirements;
8. expected schema, primary key, uncertainty fields, and suppression conventions;
9. snapshot destination and original response format; and
10. official fallback decision if the API is unavailable.

`config/source_registry.yml` is the canonical executable registry. The acquisition-matrix CSV is a generated, human-reviewable export frozen at Gate 4; discrepancies between the two block acquisition.

### Snapshot folder contract

Each `sources/public/<source_id>/snapshots/<YYYY-MM-DD>/` directory will contain:

- `original/`: byte-preserved API responses or official bulk files;
- `requests/`: endpoint, method, redacted headers, ordered query parameters, body when applicable, pagination sequence, retrieval timestamps, status codes, and response content types;
- `metadata/source.yml`: organization, dataset title, catalog ID, release, version, years, geography, definitions, license, update date, access date, and official landing/documentation URLs;
- `metadata/citation.csl.json`: machine-readable dataset citation metadata;
- `metadata/schema.json`: observed fields, types, row grain, keys, units, and suppression/uncertainty fields;
- `checksums.sha256`: checksums for every preserved response or file; and
- `manifest.json`: row counts, page counts, byte counts, retrieval status, parent snapshot identifiers, and validation results.

Raw API responses will never be cleaned or reformatted in `sources/`. Normalized but source-faithful tables will be written to `data/interim/`; analysis-ready harmonized tables will be written to `data/processed/`. Every interim and processed row will retain `source_id`, `snapshot_id`, `source_record_id` when available, release/vintage, and geographic-vintage fields.

### Acquisition command and network behavior

The package will expose one acquisition interface with source-specific adapters:

```bash
uv run chicagohealthmap sources list
uv run chicagohealthmap sources fetch --all --snapshot-date YYYY-MM-DD
uv run chicagohealthmap sources fetch --source census_acs --snapshot-date YYYY-MM-DD
uv run chicagohealthmap sources verify --all
uv run chicagohealthmap sources citations --format bibtex
```

Each adapter will implement explicit timeouts, bounded retries with backoff, rate-limit handling, pagination completeness checks, content-type validation, schema-version checks, and atomic writes. API tokens, if required, will come from environment variables and will never be written to logs, manifests, notebooks, or Git. A completed snapshot will be immutable; a later retrieval creates a new dated snapshot even when the upstream service uses the same URL.

Tests will replay stored fixtures and will not require a live network. A `--dry-run` mode will display endpoints, parameters, expected destinations, and required credentials without downloading data. An offline rebuild will use preserved raw responses rather than contacting external services.

### Data origin, citation, and lineage

Every first-party and public dataset will be cited as data, not merely mentioned by agency name. `docs/methods/data_sources.md` and generated files in `outputs/provenance/` will record the exact data-resource and dataset title, originating organization, release/extract/version, years, persistent or catalog identifier when available, landing and documentation URLs when disclosure permits, access date, license or data-use authority, local snapshot identifier, and official suggested citation when available.

CAPriCORN and ChicagoHealthMap extracts will follow the same lineage requirements. Their source records will name the originating consortium/resource, extract date, geographic and temporal scope, methods snapshot, governance restrictions, and approved citation. Protected paths, credentials, and restricted metadata will not be exposed in public outputs; the public citation and data-availability statement will describe the resource and access conditions without revealing protected information.

Every analysis variable will map to its original field name, definition, unit, geographic vintage, transformation steps, and source snapshot. The pipeline will generate:

- `outputs/provenance/data_source_inventory.csv`, one row per source snapshot;
- `outputs/provenance/variable_lineage.csv`, one row per analysis variable and contributing source field;
- `outputs/provenance/table_figure_sources.csv`, mapping every table and figure to source snapshots and frozen result artifacts;
- `outputs/provenance/data_sources.bib`, containing dataset citations; and
- a human-readable Data Sources section for the manuscript or supplement.

No table, figure, model, or manuscript estimate will be frozen unless all contributing variables resolve through the lineage files to immutable source snapshots. Public data will be cited to the originating organization and exact dataset/release, not merely to a website homepage, intermediary software package, or secondary aggregator.

External variables will be joined only after confirming geography vintages. Crosswalks, boundary mismatches, and area-weighted transformations will be documented. Community-area analyses will not be created by naively assigning a tract to an area when a tract crosses a boundary.

### Research retrieval stack

The methods and novelty review will deliberately triangulate four complementary retrieval systems:

- **PubMed MCP** for reproducible NCBI searches, PubMed identifiers, metadata, and related-article discovery;
- **Paperclip** for full-text biomedical reading and claim-level citation verification;
- **Tavily MCP** for current web discovery, extraction, crawling, and site mapping beyond the biomedical literature; and
- **Ref Context MCP** for token-efficient retrieval of current technical and API documentation.

Search dates, exact queries, source restrictions, result identifiers, screening decisions, and cited records will be preserved in `docs/methods/research_tools.md` or machine-readable companion files. PubMed and Paperclip remain authoritative for biomedical claims. Tavily complements rather than replaces database searching, and Ref is used for software and API documentation rather than epidemiologic evidence.

The evidence workflow will proceed from broad retrieval to claim-level verification:

1. PubMed MCP records reproducible searches for EHR-based public-health surveillance, small-area chronic-disease mapping, urban life-expectancy inequities, health-information exchange or clinical-data-research-network surveillance, and local resource allocation.
2. Titles and abstracts are screened against documented inclusion and exclusion criteria, with reasons retained.
3. Paperclip retrieves and reads eligible full texts and verifies methods, populations, geographic resolution, limitations, and novelty claims.
4. Tavily MCP identifies current journal requirements, public agency methods, dataset documentation, city programs, and non-indexed reports; each material claim is traced to the originating authoritative page.
5. Ref Context MCP verifies current marimo, Python, Great Tables, geospatial, statistical, and export APIs during implementation.
6. `docs/methods/evidence_matrix.md` maps every important background, methods, novelty, and interpretation claim to a verified source and records whether evidence is direct or inferential.

The manuscript may describe a pattern as novel or previously unreported only after the evidence matrix documents the search scope and finds no materially equivalent published analysis. Absence from a search will not be presented as proof that no prior work exists.

## 8. Disease Discovery and Case-Study Selection Framework

The case-study selection notebook will score the six prespecified candidates—hypertension, diabetes, COPD, heart failure, stroke, and drug use disorder—using criteria fixed before outcome modeling:

1. community-area and tract analytic coverage;
2. stability across 2022-2024;
3. availability of independent comparator measures;
4. prior epidemiologic evidence linking the condition to premature mortality and availability of aligned life-expectancy or cause-specific mortality outcomes;
5. actionability for FQHCs and CBOs;
6. phenotype interpretability and coding sensitivity; and
7. novelty without overclaiming.

The notebook will evaluate whether hypertension, diabetes, and COPD remain the strongest defensible choices while showing the results for all six candidates. It will not be designed to reproduce a predetermined winner and will not use the magnitude or significance of the confirmatory life-expectancy association to choose targets. If investigators authorize outcome-informed discovery, the SAP must either define an independent discovery/validation split or label all resulting association analyses exploratory.

### Case-study promotion gate

A target may be promoted only when all of the following are satisfied:

- its phenotype and denominator can be explained without mislabeling diagnosed proportion as prevalence;
- community-area coverage supports comparative modeling and tract coverage supports the proposed descriptive use;
- missingness and suppression are sufficiently characterized;
- temporal alignment with external comparators and life-expectancy outcomes is defensible;
- an independent public comparator or aligned mortality measure is available;
- the evidence review identifies a meaningful scientific or implementation gap;
- results remain interpretable after prespecified reliability and influential-area checks; and
- the case study contributes a distinct lesson rather than duplicating another target.

If a leading candidate fails the gate, the analysis will document the failure and select the highest-ranked defensible alternative before the confirmatory SAP is frozen. A disease will not be replaced after confirmatory outcome modeling merely because its association is null.

## 9. Statistical Analysis Plan Framework

The full statistical analysis plan will be finalized after the data-quality and source-harmonization notebooks have run, but before confirmatory case-study models are fit. The plan will be versioned in `docs/analysis/statistical_analysis_plan.md`, and later deviations will be logged.

### Primary units and periods

- Community-area/year is the primary unit for comparative association models because disclosure-compliant data are nearly complete.
- Census tract/year is used for higher-resolution descriptive and reliability-qualified targeting analyses.
- The primary period is a pooled or repeated-measures analysis of 2022-2024.
- Year 2019 is the pre-pandemic baseline.
- Years 2020-2021 enter through period indicators and sensitivity analyses, not as the main contemporary estimate.

### Provisional primary measures

- Cardiometabolic diagnosed proportions, expected to include hypertension and diabetes without documented complication if they pass Gate 5.
- Respiratory diagnosed proportion, expected to be COPD if it passes Gate 5.
- Community-area life expectancy and aligned cause-specific mortality outcomes from public sources.

The case-study decision at Gate 5 will replace this provisional list with the final measures before the SAP is frozen.

### Adjustment domains

Models will account for adult age composition, socioeconomic conditions, racialized neighborhood composition as a marker of structural context rather than biological risk, insurance/access measures, EHR capture, source reliability, calendar year, and spatial dependence. Covariates will be chosen from a documented conceptual model rather than univariable significance screening.

### Analysis sequence

1. Describe resource coverage, suppression, capture, and representativeness.
2. Map three-year EHR-diagnosed proportions with reliability information.
3. Quantify temporal stability and pandemic-period disruption.
4. Triangulate EHR measures with CDC PLACES and Chicago Health Atlas measures.
5. Estimate unadjusted and adjusted ecological associations with life expectancy and aligned mortality.
6. Identify prespecified concordance and discordance patterns.
7. Overlay FQHC and service locations for an explicitly descriptive planning demonstration.
8. Run sensitivity analyses for reliability thresholds, year definitions, spatial dependence, and influential areas.

Discordance categories will require directional agreement across prespecified measures and uncertainty/reliability thresholds. They will be labeled as planning hypotheses, not proof of underdiagnosis or unmet need.

## 10. Marimo Notebook Design

Each notebook will be a valid marimo Python script with PEP 723 dependency metadata, explicit reactive dependencies, and a deterministic script mode. There is no limit on the total number of cells. Every individual marimo cell is limited to 30 source lines so each cell remains focused, reviewable, and auditable; larger operations must be split across cells or moved into tested package functions.

- `01_data_review.py` presents the inventory, schemas, denominators, suppression, reliability, and demographic-representation results.
- `02_case_study_selection.py` applies the prespecified candidate rubric and records the scientific selection decision.
- `03_case_studies.py` contains both approved case studies in mirrored sections. It is expected to compare hypertension and diabetes overlap, divergence, temporal stability, external concordance, and life-expectancy associations if the cardiometabolic case passes Gate 5, and to evaluate COPD respiratory patterns, external concordance, mortality alignment, and appropriate geographic-resolution limits if COPD passes Gate 5.
- `04_manuscript_outputs.py` assembles only frozen, analysis-approved tables and figures; it does not refit models with different options.

Widgets will control display choices such as year, condition, geography, and reliability threshold. Script mode will use prespecified defaults and execute without waiting for interaction. Heavy logic will remain in `src/chicagohealthmap/` so it can be unit-tested independently.

### Official marimo skill routing

The implementation will use the official `marimo-team/skills` installation under `~/.agents/skills` without copying those skills into the repository.

- `marimo-notebook` governs notebook structure, PEP 723 metadata, reactive cells, script mode, and `marimo check`.
- `marimo-batch` governs typed CLI parameters and reproducible noninteractive runs after the user approves the configurable parameters.
- `implement-paper` informs the focused scientific narrative and interactive explanation once the analysis is frozen.
- `anywidget-generator` is used only if standard marimo controls cannot express a scientifically useful map or linked-selection interaction.
- `auto-paper-demo` and `implement-paper-auto` are reserved for a separate dissemination demo, not the confirmatory analysis notebook.
- `add-molab-badge` is used only after a public GitHub remote exists and disclosure-safe notebook sessions have been exported.
- `wasm-compatibility` is run only for notebooks intended for browser-only Molab/WASM execution; full local analysis notebooks may legitimately remain non-WASM because they read local protected data and use geospatial libraries.
- `jupyter-to-marimo` and `streamlit-to-marimo` activate only if a legacy `.ipynb` or Streamlit application is introduced. They are not used to manufacture an unnecessary conversion step.

## 11. JAMA Health Forum Visual Output Contract

Great Tables will be the canonical rendering layer for analytical tables in marimo, HTML review artifacts, and PDF previews. The underlying table data and formatting metadata will remain structured so the same values can be exported as editable Word tables and Excel supplemental tables. Main-manuscript tables will never be submitted as PNG or other image files.

### Table requirements

- Titles will be descriptive phrases of 10 to 15 words whenever feasible.
- Primary comparisons will read horizontally across columns, with at least 2 columns.
- Counts and percentages will appear together as `No. (%)`; percentages will include numerators and denominators when required for interpretation.
- Estimates will include prespecified uncertainty, such as SD, IQR, or 95% CI.
- Missing, unavailable, inapplicable, and suppressed values will use explicit labels rather than blank cells or numeric zeros.
- Table footnotes will use superscript letters and will define abbreviations, suppression, nonadditivity, denominators, and reasons totals may differ.
- Notebook previews will use a restrained white-background style, Arial-compatible sans serif typography, 10- to 12-point-equivalent body text, single spacing, and minimal rules.
- Editable DOCX tables will be appended to the manuscript file; eTables may additionally be written to a single structured Excel workbook with a table-of-contents sheet.

### Figure requirements

- Figures will be limited to results necessary to support the paper and will not duplicate tables.
- Titles and legends will be stored separately from the plot and will use brief 10- to 15-word descriptive titles when feasible.
- Every axis will be labeled; continuous axes will include units.
- Point estimates will use markers with uncertainty intervals rather than bars. Ratio estimates will display untransformed values on logarithmic axes.
- Bars will be limited to frequencies or rates and will start at zero. Pie charts, 3-dimensional graphs, and stacked bars will not be used.
- Symbols, line types, colors, reliability categories, suppression, and missingness will be defined in the legend.
- Color choices will be color-vision-deficiency aware and distinguishable in grayscale. Maps will use perceptually ordered scales and visually distinct missing/suppressed categories.
- Composite figures will contain no more than 4 panels unless scientifically justified.
- Publication candidates will be exported as editable vector PDF files, with high-resolution PNG previews for review. The pipeline will preserve the code and source data needed for journal graphics staff to recreate the figures.
- The visual system is a submission-ready approximation of JAMA Network conventions, not a claim to reproduce the journal's internal proprietary color palette. Accepted figures are recreated by JAMA Network graphics staff.

The exact style tokens, Great Tables helper functions, figure theme, export dimensions, and examples will be documented in `docs/methods/visual_style.md` and implemented centrally in `src/chicagohealthmap/style.py`, `tables.py`, and `figures.py`.

This contract is grounded in the [JAMA Health Forum Instructions for Authors](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors), the [JAMA Network Technical Requirements for Figures](https://jamanetwork.com/DocumentLibrary/InstructionsForAuthors/TechnicalRequirementsforFigures.pdf), and the official [Great Tables documentation](https://posit-dev.github.io/great-tables/), all accessed July 13, 2026.

## 12. Manuscript Governance and Journal Adapters

The manuscript system will not use a trial-specific prompt as a universal writing template. It will compose five explicit layers so scientific claims remain stable when a journal target changes.

```text
scientific-integrity core
        |
        v
study-design module
        |
        v
journal adapter
        |
        v
study manifest + frozen results
        |
        v
automated and human manuscript audit
```

### Scientific-integrity core

Rules applying across journals will require:

- no invented numbers, citations, study decisions, or results;
- explicit placeholders and a consolidated missing-input report when information is unavailable;
- a single source of truth for denominators, estimates, uncertainty, rounding, and terminology;
- design-appropriate causal language;
- clear distinction among prespecified, data-review-informed, exploratory, and post hoc decisions;
- quantitative results with uncertainty rather than P values alone;
- disclosure of multiplicity handling, null findings, fragile findings, and sensitivity-analysis consequences;
- traceability from every manuscript number to a frozen output artifact;
- interpretation confined to claims supported by the analysis and evidence matrix; and
- reproducible software, package, source-snapshot, SAP, and manuscript-rule versions.

Drafting Results before the Abstract and Title is the preferred internal workflow, but it is not treated as a journal requirement. Methods and Results will report outcomes and analyses in matching order. Results will quantify major findings early and avoid interpretive claims, but no mechanical rule will require every sentence to begin with a number.

### Observational EHR and small-area design module

The first design module will implement STROBE and the RECORD extension for routinely collected health data. It will require the manuscript to report:

- study design, setting, dates, analytic geography, and unit of analysis;
- adult inclusion criteria and the observed-health-system denominator;
- source health systems and capture limitations to the extent disclosure rules permit;
- diagnosis phenotype definitions, code lists, lookback periods when applicable, and validation evidence;
- suppression, missingness, linkage, geography vintage, and temporal-alignment methods;
- ecological and spatial-model assumptions and diagnostics;
- differences between EHR-diagnosed proportions and population prevalence;
- selection, access, coding, encounter-intensity, and representativeness limitations;
- privacy and data-governance restrictions; and
- whether each objective or hypothesis was formulated before outcome modeling or after results were known.

The module will prohibit causal claims about chronic diseases and life expectancy. It will also prohibit claims that the resource improves allocation, access, or health outcomes unless those effects are directly evaluated.

### JAMA Health Forum adapter

The first journal adapter will enforce the current JAMA Health Forum Original Investigation requirements verified on July 13, 2026:

- main text no longer than 3000 words;
- no more than 5 combined main tables and figures;
- 50 to 75 references for the Original Investigation article type;
- a structured abstract no longer than 350 words with separate submission headings for Importance, Objective, Design, Setting, Participants, Exposures, Main Outcomes and Measures, Results, and Conclusions and Relevance;
- a 75- to 100-word Key Points section containing Question, Findings, and Meaning;
- a concise, nondeclarative research title no longer than 100 characters including spaces;
- no observational study-design label in the title or subtitle;
- a declared study type, Data Sharing Statement, and applicable EQUATOR checklists;
- JAMA/AMA statistical presentation, including absolute quantities or rates and uncertainty before P values when applicable;
- health-policy or health-care-delivery relevance without speculation or overgeneralization;
- editable tables in the manuscript file and separately supplied figures in accepted formats; and
- acknowledgments covering contributions, data access and responsibility, funding and sponsor role, conflicts, and reportable AI-assisted writing or editing.

Trial Registration, CONSORT-AI, treatment arms, intention-to-treat analysis, intervention fidelity, adverse-event reporting, number needed to treat, and trial power calculations will not activate for this observational resource study. The title, abstract, and section rules will be reverified against the live journal instructions immediately before submission.

### Study manifest and frozen-result contract

Before manuscript drafting, a machine-readable study manifest must identify:

1. primary and secondary objectives and estimands;
2. final study-design classification;
3. population, geography, study period, and data cut;
4. phenotype, denominator, suppression, reliability, and exclusion definitions;
5. public sources and temporal/geographic crosswalks;
6. covariates, models, diagnostics, multiplicity, and sensitivity analyses;
7. case-study selection decision and its date;
8. IRB, data-use, privacy, and sharing constraints;
9. SAP, code, package, and source-snapshot versions; and
10. authorship, funding, data-access responsibility, and AI-disclosure inputs.

`04_manuscript_outputs.py` will read only the approved manifest and frozen outputs. It will not choose outcomes, refit models, modify precision, or infer missing values while rendering the paper.

### Manuscript audit

The final audit will check:

- all required inputs and unresolved placeholders;
- objective, estimand, denominator, terminology, and numerical consistency;
- text-table-figure-supplement agreement;
- traceability of every principal estimate to a model artifact;
- unlicensed causal verbs, prevalence mislabeling, and unsupported novelty claims;
- prespecification and post hoc labels;
- multiplicity language and sensitivity-result disclosure;
- word, title-character, abstract, Key Points, reference, and table/figure limits;
- JAMA abstract headings and title restrictions;
- STROBE and RECORD checklist coverage;
- Data Sharing Statement, funding, conflicts, data-access statement, and AI disclosure; and
- reference existence and claim support, with no language-model-generated reference metadata accepted without source verification.

Rules such as banning all semicolons, banning all digits from Methods, requiring identical wording in every section, requiring every Results sentence to begin with a number, or requiring the Discussion to end with a particular hedge word will not be implemented because they are not reliable scientific or JAMA requirements.

## 13. Execution Phases and Decision Gates

Execution will be divided into auditable phases. A later phase cannot silently repair or bypass a failed earlier gate.

The program is too broad for a single safe implementation plan. After this design is approved, Superpowers `writing-plans` will create a master roadmap and a detailed implementation plan for Phases 0 through 4, including every external API connector, folder contract, citation artifact, and lineage check. Later detailed plans will cover Phases 5 through 6 and Phases 7 through 9 after their prerequisite gates are reviewed. This decomposition does not narrow the program goal; it prevents later scientific choices from being buried inside a single implementation task.

### Phase 0: Repository and research governance

- confirm the isolated Git worktree and branch;
- inventory existing files without modifying source content;
- record data-use and privacy constraints;
- establish configuration, decision-log, provenance, testing, and output conventions; and
- verify availability and roles of Superpowers, PubMed MCP, Paperclip, Tavily MCP, Ref Context MCP, and the official marimo skills.

**Gate 0:** repository boundaries, source ownership, and protected-data rules are explicit.

### Phase 1: Immutable source preservation

- checksum and preserve CAPriCORN exports;
- copy, checksum, and extract both ChicagoHealthMap website archives without overwriting originals;
- create first-party manifests and methods provenance; and
- identify duplicates, unexplained versions, and missing expected files.

**Gate 1:** every first-party byte is accounted for and reproducibly traceable.

### Phase 2: Evidence and novelty review

- execute and save PubMed MCP searches;
- screen results and use Paperclip for full-text verification;
- use Tavily MCP for public-agency methods, current journal rules, and non-indexed urban-health reports;
- use Ref Context MCP for current technical documentation when implementation choices are evaluated; and
- build the evidence matrix and novelty map.

**Gate 2:** each proposed case study has a documented literature gap, comparator evidence, and defensible public-health rationale.

### Phase 3: Schema, denominator, phenotype, and quality review

- implement schema-aware ingestion with test fixtures;
- validate keys, field types, ratios, denominators, dates, and geographic identifiers;
- characterize suppression, zero semantics, missingness, reliability, capture, and representation;
- reconcile archived website methods with exported fields; and
- produce the deterministic `01_data_review.py` notebook and quality report.

**Gate 3:** the team can state exactly what each measure means, what it does not mean, and which cells are analytically usable. Unresolved denominator or suppression semantics block modeling.

### Phase 4: Public-data acquisition and harmonization

- complete and approve the acquisition matrix before downloading analytical data;
- verify official endpoints, catalog identifiers, versions, licenses, pagination, and citation guidance using authoritative documentation;
- implement and test registry-driven adapters for Chicago Health Atlas, Census ACS, Census TIGER/Line, CDC PLACES, CDC/ATSDR SVI, HRSA, and approved Chicago Data Portal datasets;
- run dry-run acquisition and inspect the planned queries, variables, years, geographies, and destinations;
- retrieve dated snapshots through official APIs or documented official bulk fallbacks;
- preserve exact responses, request logs, checksums, schemas, manifests, and citation metadata;
- validate page and row completeness, primary keys, definitions, years, uncertainty, suppression, geography vintages, update dates, and licenses;
- normalize source-faithful interim tables while retaining record-level provenance;
- construct reproducible tract/community-area crosswalks and analysis-ready tables with variable-level lineage;
- generate the data-source inventory, citation bibliography, and table/figure source map; and
- document temporal mismatch instead of treating asynchronous measures as contemporaneous.

**Gate 4:** every required external dataset can be reacquired from an authoritative programmatic endpoint or approved official bulk fallback; every variable has an originating organization, exact dataset/release, citation, license, definition, vintage, immutable snapshot, transformation record, and explicit use decision.

### Phase 5: Disease discovery and case-study decision

- apply the prespecified six-candidate rubric without using confirmatory outcome significance as the selector;
- review coverage, stability, comparators, phenotype interpretability, novelty, distinct scientific contribution, and potential local relevance;
- run only selection-authorized descriptive diagnostics; and
- document the promoted and rejected targets with reasons in `02_case_study_selection.py` and the decision log.

**Gate 5:** investigators approve the two case studies before confirmatory models are run. The leading expectation remains cardiometabolic hypertension/diabetes plus respiratory COPD, but the gate may select a defensible alternative if data or evidence fail.

### Phase 6: Statistical analysis plan freeze

- finalize objectives, estimands, units, periods, covariates, interactions, spatial methods, reliability thresholds, multiplicity treatment, diagnostics, and sensitivity analyses;
- distinguish confirmatory, supportive, exploratory, and post hoc analyses;
- define table and figure shells before viewing confirmatory results;
- version and sign the SAP and study manifest; and
- record any later deviation with date, reason, and effect on interpretation.

**Gate 6:** no confirmatory association model runs until the SAP and manifest are approved.

### Phase 7: Analysis implementation and validation

- implement models and result schemas with test-driven development;
- execute community-area primary models and tract-level descriptive analyses;
- quantify temporal stability and pandemic-period disruption;
- assess spatial dependence, influential areas, missingness, reliability thresholds, and model fit;
- triangulate with independent public measures; and
- generate frozen model artifacts for scientific review.

**Gate 7:** independent numerical and scientific validation confirms that outputs match the SAP, diagnostics are acceptable, and null or fragile findings are retained.

### Phase 8: Translation demonstration

- overlay disclosure-safe reliability-qualified patterns with FQHC/CBO or service locations;
- define examples of questions local organizations might investigate;
- document false-positive, stigma, ecological-inference, and data-refresh risks; and
- separate observed association from proposed use.

**Gate 8:** translation language is approved as a planning demonstration, not evidence of improved allocation or health outcomes.

### Phase 9: Publication artifacts

- build one combined marimo notebook containing both approved case studies using the official marimo skills, with no total cell-count cap and no more than 30 source lines per cell;
- freeze Great Tables and JAMA-style figures from approved results;
- assemble Key Points, abstract, manuscript, supplement, reporting checklists, and data-sharing material through the journal adapter;
- verify every reference and novelty claim through the evidence matrix; and
- run the manuscript audit and a clean rebuild.

**Gate 9:** all reproducibility, scientific, reporting, privacy, and journal-format checks pass before the manuscript is considered submission-ready.

## 14. Testing and Verification

Development will follow test-driven implementation. Tests will cover:

- schema and delimiter detection;
- exact field mapping for fact and dimension tables;
- ratio and denominator invariants;
- suppression-state classification;
- candidate coverage summaries;
- geography and year filters;
- immutable snapshot checksums;
- acquisition-registry completeness and schema validation;
- redaction of secrets from request manifests and logs;
- API pagination, retry, timeout, rate-limit, and atomic-write behavior using fixtures;
- source and snapshot row/page/count reconciliation;
- official-bulk fallback behavior without silent source substitution;
- external-source manifest validation;
- dataset citation completeness and valid CSL/BibTeX generation;
- variable-level lineage from processed fields to original source fields;
- table/figure source-map completeness;
- deterministic case-study scores;
- model-input construction without outcome leakage;
- expected notebook output artifacts;
- Great Tables output with explicit missing/suppression labels, denominators, uncertainty, and footnotes;
- editable DOCX/XLSX table exports that preserve values from the canonical table data; and
- figure-style checks for axis labels, units, uncertainty, panel counts, prohibited chart types, and vector export.

Completion requires all of the following fresh checks:

```bash
uv run pytest -q
uv run chicagohealthmap sources verify --all
uv run chicagohealthmap sources citations --format bibtex
uv run marimo check notebooks/*.py
uv run notebooks/01_data_review.py
uv run notebooks/02_case_study_selection.py
uv run notebooks/03_case_studies.py
uv run notebooks/04_manuscript_outputs.py
```

The pipeline will also be rerun after deleting `data/interim/`, `data/processed/`, and generated outputs to demonstrate that all derived artifacts can be rebuilt from preserved sources.

## 15. Error Handling and Scientific Stop Rules

The pipeline will stop rather than silently continue when:

- a source checksum changes unexpectedly;
- a schema or primary-key assertion fails;
- a denominator definition changes across conditions within geography-year;
- geography vintages cannot be reconciled reproducibly;
- an external source lacks a usable date or definition;
- an external dataset lacks a verified originating organization, exact title, release/vintage, license, or citable landing page;
- an API response is incomplete, unpaginated, schema-incompatible, or cannot be tied to the saved request manifest;
- acquisition would overwrite an existing immutable snapshot;
- a required API is unavailable and no authoritative versioned bulk fallback has been approved;
- an API credential appears in a log, manifest, notebook, output, or tracked file;
- a processed external variable lacks field-level lineage to an original snapshot;
- a model includes suppressed cells as known zeros;
- notebook and frozen-model specifications disagree;
- a manuscript table is reduced to an image-only artifact;
- a primary figure omits uncertainty, units, or a definition for suppression/reliability encoding.

Scientific outputs will be withheld when effective coverage is inadequate under the prespecified reliability rule. The notebook will display the reason for withholding instead of returning a blank map or a misleading zero.

## 16. Deliverables and Success Criteria

The implementation is successful when it produces:

1. immutable, checksummed first-party snapshots and source manifests;
2. an explicit data dictionary and methods discrepancy log;
3. tested analysis-ready tables for adults aged 18 years or older;
4. a reproducible data-quality report;
5. a transparent six-candidate selection notebook documenting the approved case-study decision;
6. a reviewed and versioned statistical analysis plan;
7. one marimo notebook containing both approved case studies, expected to be cardiometabolic hypertension/diabetes and respiratory COPD if they pass the promotion gate, with no total cell-count cap and no more than 30 source lines per cell;
8. Great Tables review artifacts plus editable JAMA-compatible Word/Excel tables;
9. publication-quality, source-traceable vector figures within JAMA Health Forum limits; and
10. a clean scripted rebuild with passing tests and marimo validation;
11. a reproducible literature search record and claim-level evidence matrix;
12. a frozen study manifest linking every manuscript estimate to an approved output;
13. STROBE and RECORD checklists plus a JAMA Health Forum compliance audit;
14. a disclosure-safe translation demonstration that clearly separates potential use from evaluated impact;
15. an approved external-data acquisition matrix covering every required API or official fallback;
16. immutable public-data snapshots with request manifests, checksums, schemas, licenses, and machine-readable citations;
17. generated data-source inventory, dataset bibliography, variable-lineage file, and table/figure source map; and
18. a verified offline rebuild that uses cached raw external responses without contacting live APIs.

The first implementation cycle will establish repository governance, preserve first-party sources, complete the evidence/novelty search infrastructure, build the ingestion and data-quality layers, and acquire and organize all approved external public datasets with citations and lineage. Case-study selection and confirmatory modeling will begin only after the prerequisite evidence, data-review, and external-source gates are approved.
