# ChicagoHealthMap Phases 0-4 Foundation and Data Acquisition Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the tested repository foundation, preserve and document all first-party inputs, complete the reproducible evidence search, validate the EHR export semantics, and acquire every approved external dataset through an authoritative API or official versioned fallback with complete citations and lineage.

**Architecture:** A registry defines every source before acquisition. Source adapters write immutable byte-preserved snapshots and request metadata; separate normalization code writes interim and processed Parquet tables while retaining record- and field-level lineage. Thin marimo notebooks render validated outputs from tested package functions and never conceal cleaning or selection logic.

**Tech Stack:** Python 3.12, uv, Typer, Pydantic 2, PyYAML, HTTPX, Tenacity, pandas, PyArrow, GeoPandas, Shapely, Pyogrio, Great Tables, marimo, pytest, respx, Ruff, and mypy.

## Global Constraints

- Population is adults aged 18 years or older.
- First journal target is JAMA Health Forum Original Investigation.
- Primary geography is City of Chicago census tracts and 77 community areas.
- Primary period is 2022-2024; 2019 is the pre-pandemic baseline; 2020-2021 is a temporal disruption period.
- EHR values are diagnosed proportions among observed adults, never population prevalence.
- All claims are ecological and associational; do not use causal language.
- Hypertension/diabetes and COPD are leading case-study candidates, not predetermined winners.
- Raw first-party and public snapshots are immutable and never committed to Git.
- Suppressed zeros are never interpreted as true absence.
- An official API is preferred; only an authoritative versioned bulk endpoint may substitute when no stable API exists.
- Every dataset must identify its originating organization, exact title, release or extract, access date, license or data-use authority, and approved citation.
- No table, figure, model, or manuscript estimate may freeze without field-level lineage to immutable snapshots.
- API credentials are read from environment variables and never appear in tracked files, logs, manifests, notebooks, or outputs.
- Use the official `marimo-notebook` skill when implementing notebooks and run `marimo check` before each notebook task is complete.
- Use Great Tables for analytical table previews while retaining editable structured values for Word and Excel exports.
- Use PubMed MCP for biomedical retrieval, Paperclip for full-text verification, Tavily MCP for current authoritative web documentation, and Ref Context MCP for current API/library documentation.
- **Hard pre-code gate:** do not create the Python package, marimo notebooks, statistical models, tables, or figures until the authoritative public-source snapshots, checksums, and source registry described in P1-P3 are complete.

---

## Plan Suite and Gate Boundaries

This file is the master roadmap and detailed implementation plan for Phases 0-4. It produces working, testable source and evidence infrastructure without running confirmatory life-expectancy models.

| Plan segment | Tasks | Gate produced |
|---|---:|---|
| Mandatory pre-code public-data sourcing | P1-P3 | Gate P: authoritative public data are locally preserved, checksummed, and source-cited before code |
| Phase 0: repository governance | 1-3 | Gate 0: paths, contracts, privacy, and test conventions are explicit |
| Phase 1: immutable first-party preservation | 4-5 | Gate 1: all local exports and website archives are checksummed and documented |
| Phase 2: evidence and novelty | 6-7 | Gate 2: searches, screening, full-text verification, and novelty evidence are auditable |
| Phase 3: EHR ingestion and quality | 8-10 | Gate 3: measure, denominator, suppression, and usable-cell semantics are verified |
| Phase 4: public API acquisition | 11-17 | Gate 4: public data are reproducibly acquired, cited, harmonized, and traceable |

Phases 5-6 will receive a separate plan after Gates 2-4 are approved. Phases 7-9 will receive a separate plan after the case studies and SAP are frozen.

## File Responsibility Map

### Configuration

- `config/analysis.yml`: study periods, adult definition, geography, reliability, suppression, and case-study candidate settings.
- `config/first_party_sources.yml`: exact expected local exports and website archive logical identifiers; no user-specific absolute paths.
- `config/first_party_schemas.yml`: verified positional schemas for headerless pipe-delimited exports.
- `config/literature_queries.yml`: exact PubMed query strings and screening concepts.
- `config/source_registry.yml`: canonical executable public-source registry.
- `sources/public/_registry/acquisition_matrix.csv`: generated human-reviewable registry export frozen at Gate 4.
- `sources/SOURCE_REGISTRY.yml`: pre-code machine-readable record of source origin, release, access route, license/terms status, citation, and acquisition fallback.
- `sources/public/CHECKSUMS.sha256`: SHA-256 for every preserved authoritative public-source file.
- `sources/curated/metopio/CHECKSUMS.sha256`: SHA-256 for the unauthenticated Metopio public-catalog snapshot.

### Python package

- `src/chicagohealthmap/cli.py`: Typer command tree only.
- `src/chicagohealthmap/config.py`: repository paths, environment expansion, and YAML loading.
- `src/chicagohealthmap/sources/models.py`: registry, request, snapshot, and manifest contracts.
- `src/chicagohealthmap/sources/registry.py`: registry validation and matrix export.
- `src/chicagohealthmap/sources/snapshot.py`: checksums, atomic writes, and immutable snapshot finalization.
- `src/chicagohealthmap/sources/http.py`: retries, pagination, rate limits, redacted request records, and byte preservation.
- `src/chicagohealthmap/sources/first_party.py`: local export and website-archive preservation.
- `src/chicagohealthmap/sources/adapters/census.py`: ACS and TIGER/Line adapters.
- `src/chicagohealthmap/sources/adapters/socrata.py`: CDC PLACES and Chicago Data Portal adapter.
- `src/chicagohealthmap/sources/adapters/catalog.py`: metadata-driven API, ArcGIS feature-service, and official-bulk adapters for sources verified at Task 11.
- `src/chicagohealthmap/ingest/schemas.py`: verified positional schema loader.
- `src/chicagohealthmap/ingest/pipe.py`: strict pipe-delimited ingestion.
- `src/chicagohealthmap/quality/ehr.py`: EHR ratio, denominator, suppression, domain, and coverage checks.
- `src/chicagohealthmap/quality/reports.py`: machine-readable and human-readable quality outputs.
- `src/chicagohealthmap/external/normalize.py`: source-faithful public-data normalization.
- `src/chicagohealthmap/external/geography.py`: FIPS validation and tract/community-area harmonization.
- `src/chicagohealthmap/provenance/citations.py`: CSL JSON, BibTeX, and AMA-ready data-source records.
- `src/chicagohealthmap/provenance/lineage.py`: source-to-variable and table/figure lineage.

### Scientific documentation and notebooks

- `docs/methods/chicagohealthmap_methods.md`: validated historical and empirical resource methods.
- `docs/methods/data_sources.md`: exact first-party and public dataset origins and citations.
- `docs/methods/literature_search_protocol.md`: databases, dates, queries, screening rules, and limitations.
- `docs/methods/evidence_matrix.md`: claim-level evidence and novelty assessment.
- `docs/analysis/data_dictionary.md`: verified field and derived-variable definitions.
- `docs/analysis/methods_discrepancies.md`: archived-site/export/empirical discrepancies and resolutions.
- `docs/analysis/decision_log.md`: dated scientific and implementation decisions.
- `notebooks/01_data_review.py`: deterministic marimo presentation of Gate 3 outputs.

### Tests

- `tests/unit/`: pure configuration, checksum, parsing, quality, citation, and lineage tests.
- `tests/integration/`: fixture-backed source adapter and end-to-end snapshot tests.
- `tests/fixtures/`: synthetic, disclosure-safe responses and pipe-delimited records only.

---

## Mandatory Pre-Code Public-Data Sourcing Gate

Tasks 1-17 are prohibited until P1-P3 pass. Gate P does not claim the sources are analysis-ready; it proves that the authoritative raw evidence needed to implement and test the pipeline is locally available, immutable, source-cited, and verifiable.

### P1: Freeze the justified external-source scope

- [x] Restrict population to adults aged 18 years or older.
- [x] Register Chicago Health Atlas life expectancy, mortality, Healthy Chicago Survey hypertension/diabetes, and COPD context.
- [x] Register ACS 2019, 2022, and 2024 covariates and tract vintages needed to prevent silent boundary mismatch.
- [x] Register CDC PLACES 2025, CDC/ATSDR SVI 2022, HRSA health-center sites, and official Chicago community-area boundaries.
- [x] Keep unrelated police, 311, pharmacy, WIC, and other convenience datasets out of scope unless the SAP later supplies a scientific rationale.
- [x] Register Metopio as a curated access layer, not the originating producer of public measures.

### P2: Preserve the authoritative raw files before writing pipeline code

- [x] Download all neighborhood periods advertised by the frozen Chicago Health Atlas coverage responses for `VRLE`, `VRDTHR`, `VRHDR`, `VRDIAR`, `VRDIBR`, `VRLRR`, `VRSTR`, `HCSDIAP`, `HCSHYTP`, and `LNG`.
- [x] Preserve ACS 2019 Illinois tract/block-group bulk data and the selected 2022/2024 national table-based Summary Files for `B01001`, `B03002`, `B15003`, `B17001`, `B19013`, `B23025`, `B25044`, and `B27001`.
- [x] Preserve Illinois TIGER/Line tract archives for 2019, 2020, 2023, and 2024.
- [x] Preserve the CDC PLACES 2025 Illinois tract extract, Socrata metadata, and measure definitions.
- [x] Preserve the corrected CDC/ATSDR SVI 2022 Illinois tract file and documentation.
- [x] Preserve the complete HRSA Health Center Service Delivery and Look-Alike Sites CSV and data dictionary.
- [x] Preserve official Chicago community-area GeoJSON and Socrata metadata.
- [x] Preserve the unauthenticated Metopio public catalog; do not represent it as the subscription-visible catalog.

### P3: Validate, checksum, and cite the acquisition

- [x] Parse every JSON response, test every ZIP/XLSX container, and verify required study columns before registration.
- [x] Record 200 authoritative public files (1,721,318,368 bytes at acquisition) in `sources/public/CHECKSUMS.sha256`.
- [x] Record 15 unauthenticated Metopio catalog files in `sources/curated/metopio/CHECKSUMS.sha256`.
- [x] Record exact publishers, titles, releases, URLs, access dates, geography, terms/license cautions, citations, and fallback reasons in `sources/SOURCE_REGISTRY.yml`.
- [x] Document that the Census API returned an HTTP-200 HTML `Missing Key` response on 2026-07-13 and that official versioned bulk Summary Files were therefore used.
- [x] Confirm that no API credential appears in source files, URLs, manifests, notebooks, logs, or tracked outputs.

**Gate P result:** Passed for all authoritative public sources required by the current study scope. Authenticated Metopio access remains an optional enhancement pending a locally configured `METOPIO_API_TOKEN`; it does not block use of the preserved original public sources.

---

## Phase 0: Repository and Research Governance

### Task 1: Bootstrap the Python package, test toolchain, and CLI

**Files:**
- Create: `pyproject.toml`
- Create: `README.md`
- Create: `src/chicagohealthmap/__init__.py`
- Create: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/test_cli.py`
- Modify: `.gitignore`

**Interfaces:**
- Consumes: Python 3.12 and uv.
- Produces: `chicagohealthmap` console command and importable `chicagohealthmap` package.

- [ ] **Step 1: Write the CLI smoke test**

```python
from typer.testing import CliRunner

from chicagohealthmap.cli import app


def test_cli_reports_version() -> None:
    result = CliRunner().invoke(app, ["version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == "chicagohealthmap 0.1.0"
```

- [ ] **Step 2: Run the test and confirm the package is absent**

Run: `uv run pytest tests/unit/test_cli.py -v`

Expected: FAIL during import with `ModuleNotFoundError: No module named 'chicagohealthmap'`.

- [ ] **Step 3: Create the package metadata and minimal CLI**

`pyproject.toml` must declare Python `>=3.12`, a `src` layout, the console script `chicagohealthmap = "chicagohealthmap.cli:app"`, runtime dependencies listed in the Tech Stack, and development dependencies `pytest`, `pytest-cov`, `respx`, `ruff`, and `mypy`. Configure Ruff for line length 100 and Python 3.12; configure pytest to search `tests`.

```python
# src/chicagohealthmap/__init__.py
__version__ = "0.1.0"
```

```python
# src/chicagohealthmap/cli.py
import typer

from chicagohealthmap import __version__

app = typer.Typer(no_args_is_help=True)


@app.command()
def version() -> None:
    typer.echo(f"chicagohealthmap {__version__}")
```

Add `sources/**/original/`, `sources/**/requests/`, `sources/**/extracted/`, `sources/**/checksums.sha256`, `sources/**/manifest.json`, `data/interim/`, `data/processed/`, and `outputs/` to `.gitignore`; retain tracked configuration, metadata templates, documentation, and disclosure-safe fixtures.

- [ ] **Step 4: Lock dependencies and run all bootstrap checks**

Run:

```bash
uv lock
uv run pytest tests/unit/test_cli.py -v
uv run ruff check src tests
uv run mypy src
```

Expected: all four commands exit 0; the single CLI test passes.

- [ ] **Step 5: Commit the bootstrap**

```bash
git add .gitignore README.md pyproject.toml uv.lock src/chicagohealthmap tests/unit/test_cli.py
git commit -m "build: bootstrap scientific pipeline package"
```

### Task 2: Define repository paths and source contracts

**Files:**
- Create: `src/chicagohealthmap/config.py`
- Create: `src/chicagohealthmap/sources/__init__.py`
- Create: `src/chicagohealthmap/sources/models.py`
- Create: `tests/unit/test_config.py`
- Create: `tests/unit/sources/test_models.py`

**Interfaces:**
- Consumes: repository root and environment variables.
- Produces: `ProjectPaths.discover()`, `SourceSpec`, `RequestRecord`, and `SnapshotManifest`.

- [ ] **Step 1: Write failing path and contract tests**

```python
from pathlib import Path

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.sources.models import SourceSpec, Transport


def test_project_paths_are_rooted(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)
    assert paths.sources == tmp_path / "sources"
    assert paths.processed == tmp_path / "data" / "processed"
    assert paths.provenance == tmp_path / "outputs" / "provenance"


def test_source_spec_requires_authoritative_origin() -> None:
    spec = SourceSpec(
        source_id="census_acs_2024_5y",
        organization="US Census Bureau",
        dataset_title="2024 American Community Survey 5-Year Estimates",
        transport=Transport.census_api,
        landing_url="https://www.census.gov/programs-surveys/acs",
        documentation_url="https://api.census.gov/data/2024/acs/acs5.html",
        license="US government public data",
        snapshot_subdir="census_acs",
    )
    assert spec.source_id == "census_acs_2024_5y"
```

- [ ] **Step 2: Run the tests and confirm missing modules**

Run: `uv run pytest tests/unit/test_config.py tests/unit/sources/test_models.py -v`

Expected: FAIL with missing `config` and `sources.models` modules.

- [ ] **Step 3: Implement focused path and Pydantic contracts**

`ProjectPaths` must expose `root`, `sources`, `interim`, `processed`, `outputs`, and `provenance`. Define `Transport` values `local`, `census_api`, `socrata`, `arcgis`, `http_file`, and `documented_export`. `SourceSpec` must reject missing organization, title, landing URL, documentation URL, license/data-use authority, or snapshot subdirectory. `RequestRecord` must exclude authorization values. `SnapshotManifest` must contain source ID, snapshot ID, retrieval timestamps, files, checksums, byte counts, row/page counts, and validation status.

```python
@classmethod
def from_root(cls, root: Path) -> "ProjectPaths":
    root = root.resolve()
    return cls(
        root=root,
        sources=root / "sources",
        interim=root / "data" / "interim",
        processed=root / "data" / "processed",
        outputs=root / "outputs",
        provenance=root / "outputs" / "provenance",
    )
```

- [ ] **Step 4: Add validation tests for forbidden secrets and malformed identifiers**

Test that source IDs accept lowercase letters, digits, and underscores only; `RequestRecord` rejects headers named `authorization`, `x-api-key`, and `cookie`; snapshot dates use ISO `YYYY-MM-DD`; file records require 64-character lowercase SHA-256 values.

Run: `uv run pytest tests/unit/test_config.py tests/unit/sources/test_models.py -v`

Expected: PASS.

- [ ] **Step 5: Commit the contracts**

```bash
git add src/chicagohealthmap/config.py src/chicagohealthmap/sources tests/unit/test_config.py tests/unit/sources/test_models.py
git commit -m "feat: define source and snapshot contracts"
```

### Task 3: Implement immutable snapshots, checksums, and atomic finalization

**Files:**
- Create: `src/chicagohealthmap/sources/snapshot.py`
- Create: `tests/unit/sources/test_snapshot.py`

**Interfaces:**
- Consumes: `ProjectPaths`, `SourceSpec`, raw bytes or a source file.
- Produces: `sha256_file(path)`, `copy_verified(source, destination)`, and `SnapshotWriter`.

- [ ] **Step 1: Write failing immutability tests**

```python
from pathlib import Path

import pytest

from chicagohealthmap.sources.snapshot import SnapshotExistsError, SnapshotWriter, sha256_file


def test_snapshot_finalization_is_immutable(tmp_path: Path) -> None:
    writer = SnapshotWriter(tmp_path, "example", "2026-07-13")
    writer.write_bytes("original/page-0001.json", b'{"value": 1}')
    manifest = writer.finalize()
    assert manifest.files[0].sha256 == sha256_file(tmp_path / "example" / "snapshots" / "2026-07-13" / "original" / "page-0001.json")
    with pytest.raises(SnapshotExistsError):
        SnapshotWriter(tmp_path, "example", "2026-07-13")
```

- [ ] **Step 2: Run the test and confirm missing snapshot behavior**

Run: `uv run pytest tests/unit/sources/test_snapshot.py -v`

Expected: FAIL with missing `snapshot` module.

- [ ] **Step 3: Implement streaming SHA-256, verified copy, and atomic staging**

Use 1 MiB chunks for hashes. `SnapshotWriter` writes under a UUID4-named directory inside `.staging/`, fsyncs files, writes `manifest.json` and `checksums.sha256`, then atomically renames staging to the ISO-date directory inside `snapshots/`. It must refuse an existing finalized date and remove staging after exceptions.

```python
def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 4: Test copy verification and failed-write cleanup**

Add tests proving that `copy_verified` compares source/destination hashes and that an exception before `finalize()` leaves no completed snapshot.

Run: `uv run pytest tests/unit/sources/test_snapshot.py -v`

Expected: PASS with at least 4 tests.

- [ ] **Step 5: Commit immutable snapshot support**

```bash
git add src/chicagohealthmap/sources/snapshot.py tests/unit/sources/test_snapshot.py
git commit -m "feat: add immutable source snapshots"
```

---

## Phase 1: Immutable First-Party Preservation

### Task 4: Preserve the 21 CAPriCORN/ChicagoHealthMap exports

**Files:**
- Create: `config/first_party_sources.yml`
- Create: `src/chicagohealthmap/sources/first_party.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/sources/test_first_party.py`
- Create locally, ignored: `sources/first_party/capricorn/snapshots/2026-05-27/original/`
- Create: `sources/first_party/capricorn/metadata/source.yml`

**Interfaces:**
- Consumes: `preserve-first-party --source-root PATH --snapshot-date 2026-05-27`.
- Produces: immutable local snapshot, tracked source metadata, and `FirstPartyInventory`.

- [ ] **Step 1: Declare the exact expected export inventory**

`config/first_party_sources.yml` must list these 21 file names exactly:

```yaml
source_id: capricorn_chicagohealthmap_export_2026_05_27
organization: CAPriCORN and CONSCIENCE Project
snapshot_date: "2026-05-27"
files:
  - community_area_description_facts.text
  - dim_aldermanic.text
  - dim_census_tracts.text
  - dim_community_area_reliability_crosswalk.text
  - dim_community_areas.text
  - dim_conditions.text
  - dim_congressional_districts.text
  - dim_tract_reliability_crosswalk.text
  - dim_ward_reliability_crosswalk.text
  - dim_zcta.text
  - dim_zcta_reliability_crosswalk.text
  - drug_providers.text
  - fact_chicago_condition_prevalence.text
  - fact_community_area_condition_stats.text
  - fact_community_area_vulnerability.text
  - fact_congress_condition_stats.text
  - fact_tract_condition_stats.text
  - fact_ward_condition_stats.text
  - fact_zcta_condition_stats.text
  - svi_2020.text
  - wic_locations.text
```

- [ ] **Step 2: Write failing tests for missing, extra, empty, and changed files**

Create synthetic files in `tmp_path`; assert that `inventory_first_party()` reports absent expected files, unexpected `.text` files, zero-byte files, byte counts, and hashes. The two observed zero-byte exports, `drug_providers.text` and `wic_locations.text`, must be recorded as observed-empty and flagged for methods review rather than silently dropped.

Run: `uv run pytest tests/unit/sources/test_first_party.py -v`

Expected: FAIL with missing `first_party` module.

- [ ] **Step 3: Implement inventory and verified preservation**

Expose `inventory_first_party(source_root: Path, expected: tuple[str, ...]) -> FirstPartyInventory` and `preserve_first_party(source_root: Path, snapshot_root: Path, snapshot_date: date, expected: tuple[str, ...]) -> SnapshotManifest`. The command must fail before copying when an expected nonempty file is missing, but must preserve and flag expected zero-byte files. It must not delete or rename source files.

- [ ] **Step 4: Run unit tests and a dry run against the actual source root**

Run:

```bash
uv run pytest tests/unit/sources/test_first_party.py -v
uv run chicagohealthmap sources preserve-first-party \
  --source-root "$PROJECT_ROOT" \
  --snapshot-date 2026-05-27 \
  --dry-run
```

Expected: tests pass; dry run reports 21 expected files, 2 observed-empty files, no missing files, and no writes.

- [ ] **Step 5: Preserve the real snapshot and verify every hash**

Run the same command without `--dry-run`, followed by `uv run chicagohealthmap sources verify --source capricorn_chicagohealthmap_export_2026_05_27`.

Expected: snapshot finalizes under the ignored `original/` directory; verification reports 21 matching checksums and zero unexpected files.

- [ ] **Step 6: Commit code, configuration, and disclosure-safe metadata only**

```bash
git add config/first_party_sources.yml src/chicagohealthmap/cli.py src/chicagohealthmap/sources/first_party.py tests/unit/sources/test_first_party.py sources/first_party/capricorn/metadata/source.yml
git commit -m "feat: preserve first-party health map exports"
```

### Task 5: Preserve and extract the two website-methods archives safely

**Files:**
- Modify: `config/first_party_sources.yml`
- Modify: `src/chicagohealthmap/sources/first_party.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/sources/test_archive.py`
- Create locally, ignored: `sources/first_party/chicagohealthmap/snapshots/2026-07-13/original/`
- Create locally: `sources/first_party/chicagohealthmap/snapshots/2026-07-13/extracted/`
- Create: `sources/first_party/chicagohealthmap/metadata/source.yml`
- Create: `docs/methods/chicagohealthmap_methods.md`
- Create: `docs/analysis/methods_discrepancies.md`

**Interfaces:**
- Consumes: the two named ZIP archives supplied by the user.
- Produces: checksummed archives, safe extraction inventory, canonical glossary selection, methods evidence, and discrepancy log.

- [ ] **Step 1: Write archive-safety and duplicate-content tests**

Tests must reject absolute paths, `..` traversal, symlinks, and duplicate member destinations. A second test creates two archives containing the same glossary bytes and asserts that the deduplication report retains both archive hashes but marks one glossary content hash as duplicate.

Run: `uv run pytest tests/unit/sources/test_archive.py -v`

Expected: FAIL because safe archive extraction is absent.

- [ ] **Step 2: Implement `inspect_zip()` and `extract_zip_verified()`**

```python
def is_safe_member(member: zipfile.ZipInfo) -> bool:
    path = PurePosixPath(member.filename)
    return not path.is_absolute() and ".." not in path.parts and not stat.S_ISLNK(member.external_attr >> 16)
```

Extraction writes a member inventory containing archive hash, member path, uncompressed bytes, and member SHA-256. Do not overwrite an existing extracted member with different bytes.

- [ ] **Step 3: Preserve the two exact archives**

Run:

```bash
uv run chicagohealthmap sources preserve-website-archives \
  --archive "$CHM_ARCHIVE_DIR/f184b065-0187-4d80-a3cb-5ef6af9306c1.zip" \
  --archive "$CHM_ARCHIVE_DIR/8ae30d57-17e8-4d71-a503-ea7b82d90523.zip" \
  --snapshot-date 2026-07-13
```

Expected: 2 archive records, 11 unique website members, 1 duplicate glossary-content record, and no unsafe paths.

- [ ] **Step 4: Create the historical methods and discrepancy documents**

`chicagohealthmap_methods.md` must record the archived site's stated source systems, 2019-2024 coverage, adults denominator, deduplication, ICD-10 phenotypes, suppression below 10, reliability tiers, 2023 capture reference, ACS 2018-2022, TIGER 2020, SVI 2022, study identifier `STUDY2025-0712: CONSCIENCE`, and the site's approved research citation. Each statement must cite the archive snapshot/member path.

`methods_discrepancies.md` must begin with these observed review items: exported zero values versus website `<10` suppression language; website claim of direct age standardization versus reconstructability from released strata; website statement of 38 conditions plus firearm violence versus the observed condition-domain count; and empty `drug_providers.text`/`wic_locations.text` exports. Mark each item `unresolved` until empirical validation in Tasks 8-9; do not guess a resolution.

- [ ] **Step 5: Verify and commit the methods snapshot metadata**

Run: `uv run pytest tests/unit/sources/test_archive.py -v`

Expected: PASS.

```bash
git add config/first_party_sources.yml src/chicagohealthmap/sources/first_party.py tests/unit/sources/test_archive.py sources/first_party/chicagohealthmap/metadata/source.yml docs/methods/chicagohealthmap_methods.md docs/analysis/methods_discrepancies.md
git commit -m "docs: preserve chicago health map methods provenance"
```

---

## Phase 2: Evidence and Novelty Review

### Task 6: Freeze the literature-search protocol and exact PubMed queries

**Files:**
- Create: `config/literature_queries.yml`
- Create: `docs/methods/literature_search_protocol.md`
- Create: `tests/unit/test_literature_config.py`

**Interfaces:**
- Consumes: approved platform goal and six disease candidates.
- Produces: versioned queries, inclusion/exclusion rules, screening fields, and search-update policy.

- [ ] **Step 1: Write the query configuration test**

Test that every query has a stable ID, exact query string, rationale, planned evidence use, and no empty concepts. Require the IDs `ehr_public_health`, `small_area_chronic_disease`, `urban_life_expectancy`, `clinical_network_surveillance`, `local_resource_planning`, and `candidate_conditions`.

- [ ] **Step 2: Create the exact query configuration**

Use these initial PubMed query strings verbatim, preserving later amendments as new versioned entries rather than overwriting them:

```yaml
queries:
  - id: ehr_public_health
    query: '("Electronic Health Records"[MeSH] OR electronic health record*[Title/Abstract] OR EHR[Title/Abstract]) AND ("Public Health Surveillance"[MeSH] OR public health surveillance[Title/Abstract] OR population health surveillance[Title/Abstract])'
    purpose: Resource and informatics precedents
  - id: small_area_chronic_disease
    query: '(neighborhood*[Title/Abstract] OR "small area"[Title/Abstract] OR census tract*[Title/Abstract] OR geospatial[Title/Abstract]) AND (chronic disease*[Title/Abstract] OR hypertension[Title/Abstract] OR diabetes[Title/Abstract] OR COPD[Title/Abstract]) AND (electronic health record*[Title/Abstract] OR health information exchange[Title/Abstract])'
    purpose: Small-area disease mapping precedents
  - id: urban_life_expectancy
    query: '("Life Expectancy"[MeSH] OR life expectancy[Title/Abstract] OR premature mortality[Title/Abstract]) AND (Chicago[Title/Abstract] OR urban[Title/Abstract] OR neighborhood*[Title/Abstract]) AND (inequit*[Title/Abstract] OR disparit*[Title/Abstract] OR gap[Title/Abstract])'
    purpose: Life-expectancy inequity evidence
  - id: clinical_network_surveillance
    query: '(CAPriCORN[Title/Abstract] OR clinical data research network*[Title/Abstract] OR health information exchange*[Title/Abstract] OR PCORnet[Title/Abstract]) AND (surveillance[Title/Abstract] OR population health[Title/Abstract] OR public health[Title/Abstract])'
    purpose: Multisystem network precedents
  - id: local_resource_planning
    query: '(federally qualified health center*[Title/Abstract] OR FQHC[Title/Abstract] OR community-based organization*[Title/Abstract]) AND (geospatial[Title/Abstract] OR neighborhood data[Title/Abstract] OR resource allocation[Title/Abstract] OR service planning[Title/Abstract])'
    purpose: Translation and planning precedents
  - id: candidate_conditions
    query: '(hypertension[Title/Abstract] OR diabetes[Title/Abstract] OR chronic obstructive pulmonary disease[Title/Abstract] OR heart failure[Title/Abstract] OR stroke[Title/Abstract] OR substance use disorder*[Title/Abstract]) AND (life expectancy[Title/Abstract] OR premature mortality[Title/Abstract]) AND (neighborhood*[Title/Abstract] OR census tract*[Title/Abstract] OR small area[Title/Abstract])'
    purpose: Candidate-condition rationale
```

- [ ] **Step 3: Write the screening protocol**

The protocol must define: English-language human studies and relevant methods papers; urban or subregional geography; EHR, claims, HIE, or clinical-network surveillance; disease mapping, life expectancy/mortality, representativeness, or local planning relevance; exclusion of purely individual prediction models without geographic/public-health relevance; dual-status decisions `include`, `exclude`, `background`, or `awaiting_full_text`; and one explicit exclusion reason per excluded record.

- [ ] **Step 4: Run tests and commit**

Run: `uv run pytest tests/unit/test_literature_config.py -v`

Expected: PASS.

```bash
git add config/literature_queries.yml docs/methods/literature_search_protocol.md tests/unit/test_literature_config.py
git commit -m "docs: freeze biomedical evidence search protocol"
```

### Task 7: Execute PubMed MCP searches and Paperclip full-text verification

**Files:**
- Create: `sources/literature/pubmed/snapshots/2026-07-13/search_manifest.json`
- Create: `sources/literature/pubmed/snapshots/2026-07-13/records.csv`
- Create: `sources/literature/pubmed/snapshots/2026-07-13/screening.csv`
- Create: `sources/literature/paperclip/snapshots/2026-07-13/full_text_manifest.csv`
- Create: `docs/methods/evidence_matrix.md`
- Modify: `docs/methods/literature_search_protocol.md`

**Interfaces:**
- Consumes: six exact query definitions from Task 6.
- Produces: deduplicated PMID corpus, screening decisions, full-text verification records, and claim-level evidence matrix.

- [ ] **Step 1: Run every query through PubMed MCP**

For each query, record execution timestamp, complete query string, result count, PubMed update date, retrieved PMIDs, title, journal, publication year, authors, publication type, DOI when present, and retrieval status. Preserve raw MCP result identifiers in `search_manifest.json`.

- [ ] **Step 2: Deduplicate without losing query provenance**

One row per PMID goes in `records.csv`; a semicolon-delimited `query_ids` field records every matching search. Confirm the deduplicated count equals the number of unique PMIDs across all query outputs.

- [ ] **Step 3: Screen titles and abstracts**

`screening.csv` must contain `pmid`, `title`, `query_ids`, `decision`, `exclusion_reason`, `reviewer`, `decision_date`, and `full_text_required`. Do not use journal prestige or association direction as inclusion criteria.

- [ ] **Step 4: Use Paperclip for all included or background full texts**

For each retrieved paper, record full-text availability, source, study design, geography, population, data source, denominator, disease measures, outcome measures, spatial resolution, representativeness methods, main limitations, relevance to novelty, and exact pages/sections supporting extracted claims. Unavailable full texts remain explicit; do not infer details from abstracts.

- [ ] **Step 5: Build the evidence matrix**

Organize claims under: resource precedent; EHR-diagnosed proportion limitations; multisystem deduplication; representativeness; small-area mapping; Chicago life-expectancy inequity; hypertension/diabetes mortality rationale; COPD mortality rationale; FQHC/CBO planning; spatial/ecological limitations; and reporting methods. Each row must label evidence `direct`, `supportive`, `conflicting`, or `gap` and cite PMID/DOI.

- [ ] **Step 6: Run the Gate 2 audit and commit**

Verify that every included citation exists in PubMed or the authoritative publisher, every direct quotation is under the permitted quotation limit, no reference metadata was invented, and any novelty statement is phrased as search-bounded rather than universal.

```bash
git add config/literature_queries.yml sources/literature docs/methods/literature_search_protocol.md docs/methods/evidence_matrix.md
git commit -m "research: document evidence and novelty review"
```

**Gate 2 review:** Stop for investigator review of the search yield, screening decisions, and evidence matrix before treating any pattern as novel.

---

## Phase 3: EHR Ingestion and Data Quality

### Task 8: Verify positional schemas for every headerless export

**Files:**
- Create: `config/first_party_schemas.yml`
- Create: `src/chicagohealthmap/ingest/__init__.py`
- Create: `src/chicagohealthmap/ingest/schemas.py`
- Create: `tests/unit/ingest/test_schemas.py`
- Create: `docs/analysis/data_dictionary.md`
- Modify: `docs/analysis/methods_discrepancies.md`

**Interfaces:**
- Consumes: preserved first-party files, archive methods, export owner documentation, and observed field positions.
- Produces: `TableSchema` for all 21 exports and an evidence status for each field name.

- [ ] **Step 1: Write schema-contract tests**

Tests must require each nonempty export schema to declare exact ordered fields, type, nullable status, key role, unit, and evidence source. A field is not usable when its `evidence_status` is `unverified`. Require explicit `empty_expected: true` for the two observed-empty exports.

- [ ] **Step 2: Implement schema models and field-count inspection**

```python
def observed_field_counts(path: Path) -> set[int]:
    counts: set[int] = set()
    with path.open("rt", encoding="utf-8", newline="") as handle:
        for line in handle:
            counts.add(len(line.rstrip("\n").split("|")))
    return counts
```

Reject tables with multiple field counts unless the schema explicitly documents a validated exception.

- [ ] **Step 3: Establish field positions using evidence, not inference**

Use the archived glossary, any CAPriCORN export specification, source-owner correspondence, and repeated-value invariants to assign fields. Record the evidence source beside each position. Do not promote a guessed field name. At minimum, verify identifiers, year, condition ID, overall numerator, adult denominator, overall diagnosed proportion, source, load timestamp, active flag, and all subgroup numerator/denominator/proportion triplets before using a condition-stat table.

- [ ] **Step 4: Generate and review the data dictionary**

For every table, show file name, observed rows, field count, primary key, foreign keys, field position/name/type/unit, suppression semantics, and evidence status. `data_dictionary.md` must visibly list all unverified positions and state that they block dependent analyses.

- [ ] **Step 5: Run schema tests and commit only verified definitions**

Run: `uv run pytest tests/unit/ingest/test_schemas.py -v`

Expected: PASS; no analysis-critical field is `unverified`.

```bash
git add config/first_party_schemas.yml src/chicagohealthmap/ingest tests/unit/ingest/test_schemas.py docs/analysis/data_dictionary.md docs/analysis/methods_discrepancies.md
git commit -m "feat: verify first-party export schemas"
```

**Scientific stop:** If an analysis-critical position cannot be verified, Gate 3 remains closed. Continue source-owner clarification and document the block; do not implement a plausible schema.

### Task 9: Implement strict pipe ingestion and EHR quality gates

**Files:**
- Create: `src/chicagohealthmap/ingest/pipe.py`
- Create: `src/chicagohealthmap/quality/__init__.py`
- Create: `src/chicagohealthmap/quality/ehr.py`
- Create: `src/chicagohealthmap/quality/reports.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/ingest/test_pipe.py`
- Create: `tests/unit/quality/test_ehr.py`
- Create locally, ignored: `data/interim/first_party/*.parquet`
- Create locally, ignored: `outputs/quality/ehr_quality.json`
- Create: `docs/analysis/ehr_quality_summary.md`
- Modify: `docs/analysis/methods_discrepancies.md`

**Interfaces:**
- Consumes: `TableSchema` and preserved first-party snapshot.
- Produces: typed source-faithful Parquet tables, `QualityFinding`, `QualityReport`, and disclosure-safe summary.

- [ ] **Step 1: Write failing strict-ingestion tests**

Test valid parsing plus failures for field-count mismatch, duplicate key, invalid integer/float/boolean/timestamp, literal `\N`, malformed UTF-8, numerator greater than denominator, and a ratio not equal to numerator/denominator within `1e-10` where both values are known.

```python
def test_ratio_mismatch_is_fatal() -> None:
    frame = pd.DataFrame({"numerator": [20], "denominator": [100], "diagnosed_proportion": [0.3]})
    findings = validate_ratio(frame, "numerator", "denominator", "diagnosed_proportion", tolerance=1e-10)
    assert findings[0].code == "ratio_mismatch"
    assert findings[0].severity == Severity.fatal
```

- [ ] **Step 2: Run tests and confirm missing ingestion/quality modules**

Run: `uv run pytest tests/unit/ingest/test_pipe.py tests/unit/quality/test_ehr.py -v`

Expected: FAIL during import.

- [ ] **Step 3: Implement strict parsing and source-faithful Parquet writes**

`read_pipe_table(path, schema)` must use the verified ordered field names, preserve identifiers as strings, parse booleans `t/f`, treat `\N` as missing, and never coerce invalid values to missing. Attach `source_id`, `snapshot_id`, `source_file`, and one-based `source_row_number`. Write Parquet only after schema and key validation pass.

- [ ] **Step 4: Implement quality checks and severity rules**

Required fatal findings: schema mismatch, duplicate primary key, invalid geography/year/condition domain, numerator greater than denominator, ratio mismatch, denominator inconsistency within geography-year when a shared denominator is asserted, and suppressed/unknown cells represented as known zeros in an analysis-ready output.

Required warning findings: expected-empty file, geographic coverage gap, zero-or-suppressed ambiguity, subgroup nonreconciliation, low capture, demographic misalignment, age-standardization nonreconstructability, and condition/year/geography combinations below reliability thresholds.

- [ ] **Step 5: Run tests, ingest the real snapshot, and generate reports**

Run:

```bash
uv run pytest tests/unit/ingest/test_pipe.py tests/unit/quality/test_ehr.py -v
uv run chicagohealthmap ehr ingest --snapshot-date 2026-05-27
uv run chicagohealthmap ehr quality --snapshot-date 2026-05-27
```

Expected: tests pass; the CLI writes a JSON report and Markdown summary. Any fatal result makes the command exit nonzero and prevents analysis-ready output.

- [ ] **Step 6: Resolve only evidence-supported discrepancies and commit**

Update `methods_discrepancies.md` with empirical counts and dispositions. A discrepancy can move from `unresolved` only when the evidence source and decision date are recorded.

```bash
git add src/chicagohealthmap/ingest src/chicagohealthmap/quality tests/unit/ingest tests/unit/quality docs/analysis/ehr_quality_summary.md docs/analysis/methods_discrepancies.md
git commit -m "feat: validate ehr export quality"
```

### Task 10: Build the deterministic marimo data-review notebook and close Gate 3

**Files:**
- Create: `notebooks/01_data_review.py`
- Create: `src/chicagohealthmap/quality/views.py`
- Create: `tests/unit/quality/test_views.py`
- Create: `tests/integration/test_data_review_notebook.py`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: frozen JSON quality report and typed Parquet summaries.
- Produces: deterministic notebook review, machine-readable Gate 3 decision, and no new cleaning/modeling logic.

- [ ] **Step 1: Read the official `marimo-notebook` skill before editing**

Record the skill version/path in the implementation log. Follow its PEP 723, reactive-dependency, script-mode, and `marimo check` requirements.

- [ ] **Step 2: Write view-model tests before the notebook**

Test pure functions returning data frames for source inventory, table dimensions, year/condition/geography domains, denominator invariants, suppression patterns, reliability distribution, demographic-alignment flags, and candidate coverage. Views must expose explicit `missing`, `suppressed`, and `zero_or_suppressed` states.

- [ ] **Step 3: Implement `quality/views.py` and make tests pass**

Run: `uv run pytest tests/unit/quality/test_views.py -v`

Expected: PASS.

- [ ] **Step 4: Implement the marimo notebook as a thin presentation layer**

The notebook must contain: purpose and measure warning; source inventory; schema/field evidence; denominator checks; suppression/zero audit; coverage and reliability; demographic representation; age-adjustment feasibility; candidate-condition coverage; unresolved discrepancies; and Gate 3 status. Widgets may filter display by year, geography, and condition; script mode must use 2022-2024 and all six candidates.

- [ ] **Step 5: Test notebook structure and deterministic script execution**

The integration test runs the notebook as Python against disclosure-safe fixtures and asserts creation of a Gate 3 summary artifact. It must fail if the notebook imports raw paths directly or writes into `sources/`.

Run:

```bash
uv run marimo check notebooks/01_data_review.py
uv run notebooks/01_data_review.py
uv run pytest tests/integration/test_data_review_notebook.py -v
```

Expected: all commands exit 0 when no fatal fixture finding exists.

- [ ] **Step 6: Record the Gate 3 decision and commit**

`decision_log.md` must state whether measure naming, adult denominator, suppression, reliability, and age-adjustment feasibility are sufficiently understood. If any is unresolved, record Gate 3 as closed and the exact blocked analyses.

```bash
git add notebooks/01_data_review.py src/chicagohealthmap/quality/views.py tests/unit/quality/test_views.py tests/integration/test_data_review_notebook.py docs/analysis/decision_log.md
git commit -m "feat: add marimo ehr data review"
```

**Gate 3 review:** Stop for investigator approval of the notebook and data-quality summary before disease selection or modeling.

---

## Phase 4: External Public Data Acquisition and Harmonization

### Task 11: Codify and test the frozen authoritative source registry

**Files:**
- Create: `config/source_registry.yml`
- Create: `src/chicagohealthmap/sources/registry.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/sources/test_registry.py`
- Create: `sources/public/_registry/acquisition_matrix.csv`
- Create: `docs/methods/data_sources.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: `sources/SOURCE_REGISTRY.yml`, Gate P raw snapshots, analytical requirements, archived ChicagoHealthMap source list, and current authoritative documentation checks.
- Produces: executable canonical `SourceRegistry`, human review matrix, drift evidence, and exact authoritative endpoint evidence.

- [ ] **Step 1: Write failing registry completeness tests**

Require these source IDs:

```python
REQUIRED_SOURCE_IDS = {
    "chicago_health_atlas_life_expectancy",
    "chicago_health_atlas_mortality",
    "census_acs_2019_5y",
    "census_acs_2022_5y",
    "census_acs_2024_5y",
    "census_tiger_2019_tract",
    "census_tiger_2020_tract",
    "census_tiger_2023_tract",
    "census_tiger_2024_tract",
    "cdc_places_current_tract",
    "cdc_svi_2022_tract",
    "hrsa_health_centers_current",
    "chicago_community_areas_current",
    "metopio_catalog",
}
```

Each must have organization, exact dataset title, analytical purpose, transport, official domain, landing/documentation/endpoint URLs, catalog ID when the service uses one, release, years, geography, license, access date, citation, expected grain, primary key, request parameters, and fallback policy.

- [ ] **Step 2: Re-verify Chicago Health Atlas endpoints and detect drift**

Compare current official Chicago Health Atlas/CDPH pages, endpoint traffic, and documentation with the Gate P metadata and coverage snapshots. Verify separate indicator identifiers for life expectancy and mortality, available years, geography, download/API behavior, uncertainty fields, and citation instructions. Fail on unexplained schema or definition drift. Use Tavily MCP when callable; preserve the official-web fallback evidence when it is unavailable.

- [ ] **Step 3: Re-verify Census and CDC endpoints and the frozen fallback**

Use official Census documentation to verify ACS 2019, 2022, and 2024 5-year products; registered tables `B01001`, `B03002`, `B15003`, `B17001`, `B19013`, `B23025`, `B25044`, and `B27001`; the recorded API-key failure; the official bulk fallback; and TIGER/Line 2019, 2020, 2023, and 2024 Illinois tract distributions. Verify CDC PLACES dataset `yjkw-uj5s`, its 2025 release/model version, and the CDC/ATSDR SVI 2022 Illinois bulk URL and correction note.

- [ ] **Step 4: Verify HRSA and City of Chicago endpoints**

Use official HRSA documentation/catalog to identify the current health-center site dataset, stable API/feature-service or official bulk endpoint, location fields, update date, and data dictionary. Use the official Chicago Data Portal catalog to verify the current 77 community-area boundary dataset and any approved service-location datasets needed for the translation demonstration. Do not add police, 311, pharmacy, or WIC layers unless the analysis requirements and decision log explicitly justify them.

- [ ] **Step 5: Implement registry parsing, matrix export, and registry CLI commands**

```python
def load_registry(path: Path) -> SourceRegistry:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return SourceRegistry.model_validate(payload)


def export_acquisition_matrix(registry: SourceRegistry, path: Path) -> None:
    rows = [source.to_review_row() for source in registry.sources]
    pd.DataFrame(rows).sort_values("source_id").to_csv(path, index=False)
```

The test must compare the CSV and YAML source IDs and fail on any discrepancy.

Add `sources list` and `sources matrix --check` commands in `cli.py`. `sources list` prints source ID, organization, transport, release, and verification status without credentials. `sources matrix --check` regenerates the matrix in memory and exits nonzero if it differs from the tracked CSV.

- [ ] **Step 6: Run registry tests and document exact source origins**

Run:

```bash
uv run pytest tests/unit/sources/test_registry.py -v
uv run chicagohealthmap sources list
uv run chicagohealthmap sources matrix --check
```

Expected: all required sources validate; matrix and YAML contain the same IDs; every source uses an authoritative domain.

- [ ] **Step 7: Commit the frozen registry**

```bash
git add config/source_registry.yml src/chicagohealthmap/sources/registry.py tests/unit/sources/test_registry.py sources/public/_registry/acquisition_matrix.csv docs/methods/data_sources.md docs/analysis/decision_log.md
git commit -m "docs: freeze authoritative public source registry"
```

### Task 12: Implement the generic HTTP acquisition engine and CLI

**Files:**
- Create: `src/chicagohealthmap/sources/http.py`
- Create: `src/chicagohealthmap/sources/adapters/__init__.py`
- Create: `src/chicagohealthmap/sources/adapters/base.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/sources/test_http.py`
- Create: `tests/integration/sources/test_acquisition_cli.py`

**Interfaces:**
- Consumes: `SourceSpec`, `SnapshotWriter`, HTTPX transport.
- Produces: `SourceAdapter` protocol, `HttpAcquirer.fetch()`, dry-run plan, redacted requests, and `sources fetch/verify` commands.

- [ ] **Step 1: Write failing HTTP behavior tests with respx**

Cover: successful byte response; JSON page sequence; `429` with `Retry-After`; transient `500` then success; terminal `404`; timeout exhaustion; content-type mismatch; redaction of `Authorization`, `Cookie`, and configured token query parameters; and failure when expected total rows do not equal accumulated rows.

- [ ] **Step 2: Define the adapter interface**

```python
class SourceAdapter(Protocol):
    def plan(self, spec: SourceSpec) -> AcquisitionPlan:
        raise NotImplementedError

    def fetch(self, spec: SourceSpec, writer: SnapshotWriter) -> SnapshotManifest:
        raise NotImplementedError
```

`AcquisitionPlan` contains source ID, sanitized URL, ordered parameters, transport, destination paths, required environment variables, estimated request count when known, and fallback status.

- [ ] **Step 3: Implement HTTPX acquisition with bounded retries**

Use connect/read/write/pool timeouts of 20/120/120/20 seconds. Retry `408`, `425`, `429`, `500`, `502`, `503`, and `504` at most 5 attempts with exponential backoff capped at 60 seconds, honoring `Retry-After`. Never retry other `4xx` responses. Stream response bytes directly to staging files.

- [ ] **Step 4: Implement dry run, fetch, verify, and source selection CLI**

```bash
uv run chicagohealthmap sources fetch --all --snapshot-date 2026-07-13 --dry-run
uv run chicagohealthmap sources fetch --source census_acs_2024_5y --snapshot-date 2026-07-13
uv run chicagohealthmap sources verify --all
```

The CLI must refuse `--all` when any registry source is invalid and refuse a finalized snapshot date.

- [ ] **Step 5: Run unit and integration tests**

Run: `uv run pytest tests/unit/sources/test_http.py tests/integration/sources/test_acquisition_cli.py -v`

Expected: PASS without live network access.

- [ ] **Step 6: Commit the acquisition engine**

```bash
git add src/chicagohealthmap/cli.py src/chicagohealthmap/sources/http.py src/chicagohealthmap/sources/adapters tests/unit/sources/test_http.py tests/integration/sources/test_acquisition_cli.py
git commit -m "feat: add reproducible public data acquisition"
```

### Task 13: Implement Census ACS and TIGER/Line adapters

**Files:**
- Create: `src/chicagohealthmap/sources/adapters/census.py`
- Create: `tests/fixtures/census/acs_group_response.json`
- Create: `tests/fixtures/census/tiger_tract_fixture.zip`
- Create: `tests/unit/sources/adapters/test_census.py`
- Create: `tests/integration/sources/test_census_snapshot.py`

**Interfaces:**
- Consumes: verified Census source specs and generic HTTP engine.
- Produces: immutable ACS group-response snapshots and TIGER/Line ZIP snapshots with Cook County tract validation.

- [ ] **Step 1: Write failing ACS request and parse tests**

Assert that each ACS request uses the configured year/release, `get=NAME,group(<group>)`, `for=tract:*`, `in=state:17 county:031`, and an API key only from `CENSUS_API_KEY`. Parsed rows must preserve 11-digit tract GEOIDs and margins of error. A response header/row length mismatch is fatal.

- [ ] **Step 2: Implement `CensusAcsAdapter`**

Fetch and preserve one raw JSON response per configured group and release. `manifest.json` records group name, URL, redacted parameters, response row count, and header hash. Do not combine or derive ACS variables inside the adapter.

- [ ] **Step 3: Write failing TIGER URL, archive, CRS, and geography tests**

For the 2024 Illinois tract source, assert official file name `tl_2024_17_tract.zip`; for 2020 assert `tl_2020_17_tract.zip`. Reject unsafe ZIP members. Validate required fields `STATEFP`, `COUNTYFP`, `TRACTCE`, `GEOID`, and geometry; filter Cook County only after preserving the original Illinois ZIP.

- [ ] **Step 4: Implement `CensusTigerAdapter`**

Preserve the official ZIP and metadata, validate the archive, inspect the shapefile through Pyogrio, and write a source-faithful interim GeoParquet with original CRS and source identifiers. A separate harmonization task may reproject it; the adapter must not.

- [ ] **Step 5: Run tests and fetch the registered Census snapshots**

Run:

```bash
uv run pytest tests/unit/sources/adapters/test_census.py tests/integration/sources/test_census_snapshot.py -v
uv run chicagohealthmap sources fetch --source census_acs_2019_5y --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source census_acs_2022_5y --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source census_acs_2024_5y --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source census_tiger_2020_tract --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source census_tiger_2024_tract --snapshot-date 2026-07-13
```

Expected: all tests pass; five immutable snapshots verify; each ACS group has the expected Cook County tract grain; TIGER snapshots contain valid Illinois tract geometry and Cook County records.

- [ ] **Step 6: Commit adapter code and fixtures**

```bash
git add src/chicagohealthmap/sources/adapters/census.py tests/fixtures/census tests/unit/sources/adapters/test_census.py tests/integration/sources/test_census_snapshot.py
git commit -m "feat: acquire census demographics and boundaries"
```

### Task 14: Implement the Socrata adapter for CDC PLACES and Chicago Data Portal

**Files:**
- Create: `src/chicagohealthmap/sources/adapters/socrata.py`
- Create: `tests/fixtures/socrata/metadata.json`
- Create: `tests/fixtures/socrata/page_0001.json`
- Create: `tests/fixtures/socrata/page_0002.json`
- Create: `tests/unit/sources/adapters/test_socrata.py`
- Create: `tests/integration/sources/test_socrata_snapshot.py`

**Interfaces:**
- Consumes: verified Socrata domain, dataset ID, `$select`, `$where`, `$order`, and expected grain.
- Produces: metadata snapshot, fully paginated raw pages, and row-count reconciliation.

- [ ] **Step 1: Write failing pagination and query-stability tests**

Require `$limit=50000`, deterministic `$order` using the registered primary key, successive `$offset` values, a separate `count(*)` request, and exact equality between count and deduplicated fetched rows. Test that query changes alter the request-manifest hash.

- [ ] **Step 2: Implement `SocrataAdapter`**

Fetch `/api/views/<dataset_id>` metadata before data pages. Preserve metadata and every page separately. Use an app token only from `SOCRATA_APP_TOKEN`; the adapter must work anonymously at lower rate limits. Reject a dataset whose metadata ID/title differs from the registry.

- [ ] **Step 3: Configure and test CDC PLACES filters**

Use the verified current tract dataset ID from Task 11. Filter to the registered release, Illinois/Cook County or Chicago tract GEOIDs, and the required hypertension, diabetes, and COPD measures while preserving measure IDs, estimates, confidence intervals, data-value types, and model/release fields. The adapter must not rename PLACES estimates as observed prevalence.

- [ ] **Step 4: Configure and test City of Chicago datasets**

Fetch the verified community-area boundary dataset and only the service/facility datasets approved in the source registry. Preserve originating department, dataset ID, metadata update timestamp, license, and geometry fields.

- [ ] **Step 5: Run tests and fetch registered Socrata snapshots**

Run:

```bash
uv run pytest tests/unit/sources/adapters/test_socrata.py tests/integration/sources/test_socrata_snapshot.py -v
uv run chicagohealthmap sources fetch --source cdc_places_current_tract --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source chicago_community_areas_current --snapshot-date 2026-07-13
```

Expected: all tests pass; each count matches fetched rows; manifests include metadata hashes and saved queries.

- [ ] **Step 6: Commit the Socrata adapter**

```bash
git add src/chicagohealthmap/sources/adapters/socrata.py tests/fixtures/socrata tests/unit/sources/adapters/test_socrata.py tests/integration/sources/test_socrata_snapshot.py
git commit -m "feat: acquire cdc and chicago portal data"
```

### Task 15: Implement verified catalog, ArcGIS, and official-bulk adapters

**Files:**
- Create: `src/chicagohealthmap/sources/adapters/catalog.py`
- Create: `tests/fixtures/catalog/arcgis_page.json`
- Create: `tests/fixtures/catalog/official_bulk.csv`
- Create: `tests/unit/sources/adapters/test_catalog.py`
- Create: `tests/integration/sources/test_catalog_snapshot.py`

**Interfaces:**
- Consumes: Task 11 registry entries for Chicago Health Atlas, CDC SVI, and HRSA.
- Produces: immutable API/export snapshots without unverified endpoint assumptions.

- [ ] **Step 1: Write failing transport-policy tests**

Test that `arcgis` sources query service metadata, then paginate `query` with `where=1=1`, `outFields=*`, `returnGeometry=true` when needed, and deterministic object-ID order. Test that `http_file`/`documented_export` sources accept only the registered authoritative domain and exact content type. Reject redirects to an unregistered third-party domain.

- [ ] **Step 2: Implement ArcGIS and official-file transports**

ArcGIS pagination must use service `maxRecordCount` and stop only after `exceededTransferLimit` is false or all registered object IDs are retrieved. Official files must preserve `Last-Modified`, `ETag`, content length, resolved URL, and checksum. A change at the same URL creates a new snapshot date; it never overwrites.

- [ ] **Step 3: Acquire Chicago Health Atlas indicators**

Use only the transport and exact endpoints verified at Task 11. Preserve life-expectancy and mortality indicators, geography, year/period, estimate, uncertainty/suppression fields, indicator metadata, and source organization. If the official endpoint exports a workbook or CSV, preserve it byte-for-byte before extracting tables.

- [ ] **Step 4: Acquire CDC SVI 2022 and HRSA health-center data**

Use their verified official API/feature-service endpoints or registered versioned bulk fallbacks. SVI must retain tract GEOID, overall rank/index, theme values, flags, release year, and documentation. HRSA must retain site identifier, organization/site name, site type, address/geography, coordinates, active/status fields, update date, and program metadata required to identify FQHC/service locations.

- [ ] **Step 5: Run tests and acquire all three source families**

Run:

```bash
uv run pytest tests/unit/sources/adapters/test_catalog.py tests/integration/sources/test_catalog_snapshot.py -v
uv run chicagohealthmap sources fetch --source chicago_health_atlas_life_expectancy --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source chicago_health_atlas_mortality --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source cdc_svi_2022_tract --snapshot-date 2026-07-13
uv run chicagohealthmap sources fetch --source hrsa_health_centers_current --snapshot-date 2026-07-13
```

Expected: tests pass; four verified snapshots exist; each manifest identifies its authoritative organization, dataset title, release/update date, license, request/export route, and citation.

- [ ] **Step 6: Commit adapters and fixtures**

```bash
git add src/chicagohealthmap/sources/adapters/catalog.py tests/fixtures/catalog tests/unit/sources/adapters/test_catalog.py tests/integration/sources/test_catalog_snapshot.py
git commit -m "feat: acquire atlas svi and hrsa sources"
```

### Task 16: Normalize public sources and generate citation and lineage artifacts

**Files:**
- Create: `src/chicagohealthmap/external/__init__.py`
- Create: `src/chicagohealthmap/external/normalize.py`
- Create: `src/chicagohealthmap/external/geography.py`
- Create: `src/chicagohealthmap/provenance/__init__.py`
- Create: `src/chicagohealthmap/provenance/citations.py`
- Create: `src/chicagohealthmap/provenance/lineage.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `tests/unit/external/test_normalize.py`
- Create: `tests/unit/external/test_geography.py`
- Create: `tests/unit/provenance/test_citations.py`
- Create: `tests/unit/provenance/test_lineage.py`
- Create locally, ignored: `data/interim/public/`
- Create locally, ignored: `data/processed/public/`
- Create locally, ignored: `outputs/provenance/`
- Modify: `docs/methods/data_sources.md`
- Modify: `docs/analysis/data_dictionary.md`

**Interfaces:**
- Consumes: all verified source manifests and raw snapshots.
- Produces: source-faithful interim tables, harmonized processed tables, `DataCitation`, `LineageRecord`, and provenance reports.

- [ ] **Step 1: Write normalization tests that preserve source meaning**

Require standardized identifiers and types without changing measure semantics. CDC PLACES model-based estimates remain labeled `model_based_estimate`; ChicagoHealthMap remains `ehr_diagnosed_proportion`; ACS remains estimate/MOE pairs; Chicago Health Atlas retains its published indicator label. Test that no normalizer emits a generic field named `prevalence` without a source-qualified measure type.

- [ ] **Step 2: Implement source-faithful normalizers**

Each normalized row must include `source_id`, `snapshot_id`, `source_record_id`, `source_field_map`, `release_vintage`, `geography_type`, `geography_id`, and `time_period`. Write Parquet with a companion schema/metadata JSON.

- [ ] **Step 3: Write and implement geography validation tests**

Validate 11-digit tract GEOIDs, Illinois `17`, Cook County `031`, geometry validity, and CRS. Preserve both 2020 and 2024 tract vintages. Build tract-to-community-area overlay weights from authoritative boundaries; assert weights sum to 1 within tolerance for included Chicago tracts, record slivers, and never use centroid-only assignment for crossing tracts.

- [ ] **Step 4: Implement dataset citation rendering**

```python
@dataclass(frozen=True)
class DataCitation:
    source_id: str
    organization: str
    title: str
    version: str
    year: str
    url: str
    accessed: date
    catalog_id: str | None
```

Generate one valid CSL JSON item and one BibTeX dataset entry per source snapshot. CAPriCORN/ChicagoHealthMap citation uses the archived approved research citation plus extract date and access restrictions; it must not expose protected paths.

- [ ] **Step 5: Implement variable and artifact lineage**

`LineageRecord` must identify output dataset/field, transformation function/version, input dataset/field, source ID, snapshot ID, and evidence/decision reference. Generate `data_source_inventory.csv`, `variable_lineage.csv`, and `table_figure_sources.csv`. Fail when a processed field has no lineage or when a table/figure references an unregistered artifact.

Add `external normalize --all`, `provenance build --all`, `provenance verify --all`, and `sources citations --format bibtex` commands to `cli.py`. Each command must return a nonzero exit code on incomplete lineage, missing citation fields, or an unverified snapshot.

- [ ] **Step 6: Run tests and materialize provenance**

Run:

```bash
uv run pytest tests/unit/external tests/unit/provenance -v
uv run chicagohealthmap external normalize --all
uv run chicagohealthmap provenance build --all
uv run chicagohealthmap sources citations --format bibtex
```

Expected: tests pass; all processed public fields have lineage; citations exist for every first-party and public snapshot.

- [ ] **Step 7: Commit code, tests, and human-readable documentation**

```bash
git add src/chicagohealthmap/external src/chicagohealthmap/provenance tests/unit/external tests/unit/provenance docs/methods/data_sources.md docs/analysis/data_dictionary.md
git commit -m "feat: add public data lineage and citations"
```

### Task 17: Run the full Phases 0-4 verification and close Gate 4

**Files:**
- Create: `tests/integration/test_offline_rebuild.py`
- Create: `src/chicagohealthmap/pipeline.py`
- Modify: `src/chicagohealthmap/cli.py`
- Create: `docs/analysis/gate_0_4_review.md`
- Modify: `README.md`
- Modify: `docs/analysis/decision_log.md`
- Modify: `notebooks/01_data_review.py`

**Interfaces:**
- Consumes: all code, preserved sources, manifests, normalized tables, citations, and lineage artifacts from Tasks 1-16.
- Produces: reproducibility report, offline rebuild evidence, and explicit Gate 0-4 decisions.

- [ ] **Step 1: Extend the data-review notebook with external-source provenance**

Add sections for registry completeness, acquisition route, source organization, release/update date, exact geography/time coverage, request/page counts, citation status, license, row-count reconciliation, and crosswalk validity. The notebook reads provenance outputs only and does not contact APIs.

- [ ] **Step 2: Implement and test the offline rebuild orchestrator**

Implement `rebuild_through_phase_4(root: Path, offline: bool = True) -> RebuildReport` in `pipeline.py` and expose it as `rebuild --through-phase 4 --offline --root PATH`. The integration test must disable network sockets, delete a temporary copy of interim/processed/output artifacts, rebuild them from fixture-backed raw snapshots, and compare deterministic hashes for schemas, row counts, citations, and lineage. It must prove that no API is contacted.

- [ ] **Step 3: Run all static, unit, integration, and marimo checks**

Run:

```bash
uv run ruff check src tests notebooks
uv run mypy src
uv run pytest -q
uv run chicagohealthmap sources verify --all
uv run chicagohealthmap sources matrix --check
uv run chicagohealthmap provenance verify --all
uv run marimo check notebooks/01_data_review.py
uv run notebooks/01_data_review.py
```

Expected: every command exits 0. The source verifier reports 21 first-party exports, 2 website archives, and every approved public snapshot with matching checksums. The provenance verifier reports zero uncited snapshots and zero untraced processed fields.

- [ ] **Step 4: Perform a clean offline rebuild**

Copy raw snapshots and configuration to a temporary test root, deny network, remove its `data/interim`, `data/processed`, and `outputs`, and run:

```bash
uv run chicagohealthmap rebuild --through-phase 4 --offline --root /tmp/chicagohealthmap-offline-rebuild
```

The automated test uses pytest's unique temporary directory rather than the fixed documentation path. Expected: rebuild exits 0 and matches the pre-deletion manifest counts and hashes.

- [ ] **Step 5: Write the Gate 0-4 review**

`gate_0_4_review.md` must list pass/fail and evidence paths for: repository/privacy boundaries; first-party checksums; archive-method extraction; literature search completeness; field/schema verification; denominator and suppression semantics; external registry completeness; API/bulk acquisition; licenses/citations; geography/time alignment; record/field lineage; marimo validation; and offline rebuild.

- [ ] **Step 6: Record gate decisions and commit**

Gate 4 may close only when every required source is authoritative, citable, licensed, immutable, complete, and traceable. A source failure blocks only dependent analyses, which must be named; it cannot be silently replaced.

```bash
git add README.md src/chicagohealthmap/pipeline.py src/chicagohealthmap/cli.py notebooks/01_data_review.py tests/integration/test_offline_rebuild.py docs/analysis/gate_0_4_review.md docs/analysis/decision_log.md
git commit -m "test: verify source and evidence foundation"
```

---

## Final Plan Verification Checklist

- [ ] All raw first-party exports and website archives remain unmodified and ignored by Git.
- [ ] Every first-party file and public response has a SHA-256 checksum and snapshot manifest.
- [ ] Every headerless export field used analytically has a verified positional meaning.
- [ ] Suppressed and ambiguous zero cells are represented explicitly and never treated as absence.
- [ ] PubMed MCP queries, result counts, PMIDs, screening decisions, and search dates are preserved.
- [ ] Paperclip full-text evidence supports each material methods, novelty, and interpretation claim.
- [ ] Every external source uses an authoritative API or documented official versioned fallback.
- [ ] Census, PLACES, SVI, HRSA, Chicago Health Atlas, TIGER/Line, and approved Chicago Data Portal sources have exact origin metadata.
- [ ] Every dataset has a CSL/BibTeX citation and human-readable source record.
- [ ] Every processed variable has field-level lineage to an immutable snapshot.
- [ ] Every table/figure candidate can resolve its data sources and frozen artifacts.
- [ ] No secrets or protected paths appear in tracked files or public outputs.
- [ ] `pytest`, Ruff, mypy, source verification, provenance verification, `marimo check`, script execution, and offline rebuild all pass.
- [ ] Gates 0-4 have explicit investigator decisions before Phase 5 case-study selection begins.
