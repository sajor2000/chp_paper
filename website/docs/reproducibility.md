---
title: Reproducibility and provenance
description: How the final aggregate analysis is bound, tested, rendered, and reviewed.
---

# Reproducibility and provenance

## Two executable notebooks

The study has 2 complementary implementations:

- `notebooks/00_master_chicago_healthmap_pipeline.py` is the governed Marimo pipeline.
- `notebooks/RMD_chm_paper_r_Ashley.Rmd` is the R statistical analysis and scientific report.

The R report independently reconstructs the primary pooled descriptive measures
and HCS hypertension triangulation. It imports specialized bootstrap, HC3, and
spatial results from checksum-verified Marimo artifacts to avoid creating a
second undocumented implementation.

## Integrity controls

Every required analytic input is bound by SHA-256 digest. The R render stops if
an expected file is missing or differs from the completed Marimo manifest. It
does not substitute an alternate file.

The final analysis uses:

- random seed `20260715`;
- 1000 community-area cluster-bootstrap replicates; and
- 9999 spatial permutations.

## Reproduce the public checks

```bash
uv sync --frozen
uv run ruff check .
uv run mypy src
./scripts/test_public_release.sh
uv run marimo check --strict notebooks/00_master_chicago_healthmap_pipeline.py
```

The public repository includes a deterministic gzip archive of the aggregate
geography-condition-year analytic CSV. Materialize and checksum it with:

```bash
./scripts/materialize_release_data.sh
```

The R report additionally requires the 3 checksum-matching Chicago Health Atlas
responses listed in `sources/public/CHECKSUMS.sha256`. Those source responses are
not redistributed because their metadata do not state a redistribution license.

## Render the R report

```bash
Rscript -e 'rmarkdown::render(
  "notebooks/RMD_chm_paper_r_Ashley.Rmd",
  output_file = "RMD_chm_paper_r_Ashley.html",
  output_dir = "outputs/statistician-review",
  envir = new.env(parent = globalenv()),
  clean = TRUE
)'
```

## Source and artifacts

- [GitHub repository](https://github.com/sajor2000/chp_paper)
- [Final R Markdown source](https://github.com/sajor2000/chp_paper/blob/main/notebooks/RMD_chm_paper_r_Ashley.Rmd)
- [Statistical analysis plan](https://github.com/sajor2000/chp_paper/blob/main/docs/analysis/statistical_analysis_plan.md)
- [Aggregate output directory](https://github.com/sajor2000/chp_paper/tree/main/outputs/notebooks/chicago_healthmap_master)

The repository contains aggregate artifacts only. Patient-level data, raw
clinical source snapshots, credentials, and identifiers are excluded.
