# Chicago Health Map geographic-resolution study

This repository contains the analysis code, statistical analysis plan, review
notebooks, aggregate review artifacts, and reporting controls for an Original
Investigation evaluating whether direct census-tract measures from Chicago
Health Map add geographic information beyond direct community-area labels.

Chicago Health Map values are EHR-diagnosed proportions among adults observed
in participating CAPriCORN health systems. They are not population prevalence
estimates. The study evaluates whether health-system research data can
supplement public-health surveillance at smaller geographic scales. It does not
propose replacing population-based surveillance.

## Current scientific status

This repository contains the final aggregate statistical analysis and the full
biostatistical review record. Completed results are displayed in the R Markdown
and Marimo reports. Combined diabetes was excluded because the available source
documentation did not establish mutual exclusivity and denominator equivalence.

## Methods website

The public Docusaurus site explains the scientific question, data sources,
analytic cohort, estimands, statistical methods, results, limitations, and
reproducibility workflow:

- [Chicago Health Map Methods](https://sajor2000.github.io/chp_paper/)

The website source is under `website/`. Build it locally with:

```bash
cd website
npm ci
npm run typecheck
npm run build
```

## Primary files

- `notebooks/00_master_chicago_healthmap_pipeline.py`: governed Marimo analysis.
- `notebooks/RMD_chm_paper_r_Ashley.Rmd`: detailed R statistical review notebook.
- `outputs/statistician-review/RMD_chm_paper_r_Ashley.html`: self-contained R review.
- `outputs/statistician-review/00_master_chicago_healthmap_statistician_review.html`:
  self-contained Marimo review.
- `docs/analysis/statistical_analysis_plan.md`: statistical analysis plan.
- `docs/analysis/decision_log.md`: unresolved decisions requiring sign-off.
- `docs/analysis/raw_data_audit_2026-08-27.md`: aggregate source-data audit.
- `config/chm_study_data_contract.yml`: executable study data contract.

## Repository contents

- `src/chicagohealthmap`: reusable acquisition, governance, analysis, reporting,
  and manuscript-control code.
- `tests`: unit, integration, statistical-method, and notebook-contract tests.
- `config`: study, journal, source, and authorization contracts.
- `docs`: methods, analysis, manuscript, provenance, and audit documentation.
- `outputs/notebooks/chicago_healthmap_master`: aggregate statistical tables,
  figures, diagnostics, manifests, and a compressed analytic dataset.
- `sources`: metadata and checksum ledgers only. Source snapshots are not
  redistributed.

No patient-level or row-level clinical data are included. Raw source snapshots,
database credentials, local caches, and temporary render artifacts are excluded.

## Python environment and checks

Python 3.12 and [`uv`](https://docs.astral.sh/uv/) are required.

```bash
uv sync --frozen
uv run ruff check .
uv run mypy src
./scripts/test_public_release.sh
uv run marimo check --strict notebooks/00_master_chicago_healthmap_pipeline.py
```

Some integration tests and a complete Marimo rebuild require governed local
source snapshots that are intentionally absent from this public repository.
The public-release test script runs the source-independent unit suite. The
excluded test modules remain versioned and run in the governed internal
environment with their checksum-verified fixtures. Static checks do not require
credentials.

## Render the R review notebook

The aggregate analytic dataset is stored as a deterministic gzip archive because
the uncompressed CSV exceeds GitHub's single-file limit. Materialize the exact
CSV as follows:

```bash
./scripts/materialize_release_data.sh
```

The R notebook also verifies 3 frozen Chicago Health Atlas API responses before
use: HCS hypertension, HCS diabetes, and the topic metadata file. Those source
responses are not redistributed because the API metadata does not state a
redistribution license. Restore the checksum-matching files at the paths listed
in `sources/public/CHECKSUMS.sha256`, then render:

```bash
Rscript -e 'rmarkdown::render(
  "notebooks/RMD_chm_paper_r_Ashley.Rmd",
  output_file = "RMD_chm_paper_r_Ashley.html",
  output_dir = "outputs/statistician-review",
  envir = new.env(parent = globalenv()),
  clean = TRUE
)'
```

Required R packages are `digest`, `dplyr`, `ggplot2`, `jsonlite`, `knitr`,
`patchwork`, `ragg`, `rmarkdown`, and `scales`.

## Interpretation boundary

All reported quantities describe aggregate geographic records. They do not
identify individuals, estimate causal effects, establish population prevalence,
or validate a clinical prediction model. Public-health datasets remain the basis
for population inference. Chicago Health Map is evaluated as a complementary
health-system data source.

## Reuse

No open-source or data-redistribution license has been assigned. Contact the
study team before reusing code, documentation, or aggregate artifacts.
