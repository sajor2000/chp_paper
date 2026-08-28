# SAP notebook compliance audit

Audit date: 2026-07-15
Implementation baseline commit: `c9fb3bb` (paper-redesign lineage; final verification commit recorded in the run manifest)
Implementation branch: `codex/chm-paper-master-redesign`
Disposition: **implementation/freeze candidate for independent human S7 review; results not authorized**

## Interpretation of status

- **Implemented** means the requirement is present, tested, and exercised against the
  frozen data.
- **Implemented with boundary** means the supported part is present while an explicit
  fail-closed limitation remains.
- **Withheld** means the software generated a machine-readable withholding record
  instead of substituting an unsupported analysis.
- **Open** means human review, authorization, or a later data/governance decision is
  still required.

This document is an implementation and reproducibility audit. Numerical values below
are recorded only to make the run independently checkable. They are not manuscript
claims and must not be copied into Results or Discussion while
`results_authorized=false`.

## Binding source and authorization boundaries

| Requirement | Status | Verified evidence |
| --- | --- | --- |
| CHP/CAPriCORN is the source of truth for disease values | Implemented | All 22,540 frozen rows identify `capricorn_chicagohealthmap_export_2026_05_27`; numerators, denominators, and measures remain direct first-party values. |
| No disease interpolation, census derivation, tract rollup, or centroid assignment | Implemented | Every row has `disease_value_derivation=direct_first_party_export_not_interpolated`; the tract-community overlay supplies linkage metadata only. |
| Chicago Health Atlas role is secondary public outcome/reference only | Implemented | Notebook provenance separates CHP exposure IDs from `chicago_health_atlas_life_expectancy` outcome IDs. Atlas is never labeled CHP and is never used to validate CHP disease fields. |
| User-supplied Atlas CSV remains outside ingestion | Implemented | The file (SHA-256 `12bd0aef4167967df900e1c6a32be7c18e99ae76cd0aaffeee438f757c9c9570`) was used only for a read-only 77-area `VRLE_2024` equality check against the already-frozen Atlas outcome. It is not an ACS source, and its total population field is not used as `acs_adult_population`. |
| Primary frame contains all 77 community areas and retains direct tract observations | Implemented | Freeze contains 1,848 community-area records across 77 areas and 20,692 tract records across 866 tracts. C1 has 77 exposure-outcome-complete areas; C2 has 76 because one area is incomplete after suppression handling. |
| Suppression and source metadata are preserved | Implemented | Suppressed values are excluded from analytic numerators and denominators while suppression, missingness, capture, reliability, source, snapshot, position, and lineage fields remain auditable. |
| Results/manuscript authorization remains closed | Open | Dataset and notebook manifests record `results_authorized=false`. Adjusted candidate fits and diagnostics may have executed for audit/diagnostic purposes; C1 is `audit_only_exploratory`, C2 is `freeze_candidate_primary_model_unsecured`, and no manuscript-facing prose is authorized. Human S7 and results freeze remain open. |

## Frozen dataset verification

| Check | Observed | Status |
| --- | --- | --- |
| Shape | 22,540 rows × 90 columns | Pass |
| Community-area geography count | 77 | Pass |
| Census-tract record count | 20,692 | Pass |
| Duplicate primary keys | 0 | Pass |
| Disease derivation | 22,540/22,540 `direct_first_party_export_not_interpolated` | Pass |
| Source-manifest validation | `passed` | Pass |
| CSV SHA-256 | `7730b47ac9e3b7aae6671b2396e0a0bf763ea77dfcf70e8cd6144e80777db606` | Pass |
| Parquet SHA-256 | `83ef20728fc5677de82f67d3bf4b257261e7901d4e50765ba8c6e3354f226956` | Pass |
| Schema SHA-256 | `582189989ec62f63d4a1c695018244ba497b8caf8b3c5049e41ef98680780d18` | Pass |
| Lineage SHA-256 | `7d0e0277f75c78e825c7f85d5da71483028b7488aaccf5382a2196a1d68c134e` | Pass |

## Requirement-by-requirement analysis compliance

| Plan/SAP requirement | Status | Audit evidence and boundary |
| --- | --- | --- |
| Source proportion-to-percentage-point conversion | Implemented | A source value of `0.20` is validated and converted once to `20.0` percentage points; missing, mixed, or unknown unit contracts fail closed. |
| Suppression-aware community pooling | Implemented | Suppressed condition-years do not contribute to pooled exposures. Complete annual counts and explicit eligibility fields are retained. |
| Combined diabetes completeness | Implemented | Both source-published diabetes components must be present, unsuppressed, and denominator-compatible. Unexpected or unidentified diabetes-family components fail closed. |
| Resource-quality audit | Implemented with boundary | Table 1 reports exact rows, geographies, years, denominator and measure summaries, capture, missingness, suppression, provenance, and units. Reliability availability is reported separately; qualification is `withheld_pending_reliability_rule`. |
| Tract concordance and discordance | Implemented | Pairwise-complete common sets drive Spearman, Pearson, median differences, common-set cut points, quadratic weighted kappa, five frozen categories, and quartile/tertile outputs. Neither comparator is treated as a gold standard. |
| Multiplicity | Implemented | All six tract Spearman/Pearson tests share one named comparator family and one BH denominator of 6; raw and adjusted P values are retained. |
| Adjusted C1/C2 readiness and fail-closed gates | Implemented with boundary | The four approved covariates (`pct_age_65_plus`, `pct_female`, `pct_below_fpl`, and `acs_adult_population`) are complete for 1,848 eligible community-area rows. C1 is withheld because maximum VIF exceeds 5; C2 passes the readiness gate. No proxy covariates were substituted. |
| Supported C1/C2 sensitivity estimands | Implemented with boundary | Tested HC3 unadjusted sensitivities use exact model-specific populations, frozen IQRs, the full joint C1 covariance, and 97.5%/95% intervals. Every output is labeled `supported_sensitivity_not_primary` and noncausal. |
| Influence diagnostics | Implemented | Cook's distance, leverage, externally studentized residuals, leave-one-area-out ranges, sign change, >30% fragility, and exclude-all-flagged summaries are emitted without deleting areas from the principal frame. |
| Temporal robustness | Implemented with boundary | Annual 2019–2024, leave-one-primary-year-out, disruption-candidate, and most-recent-common-outcome alignment outputs use exact paired flows and frozen primary-population IQRs. Unreviewed continuity states remain pending and cannot authorize exclusions. |
| Spatial diagnostics | Implemented with boundary | Deterministic queen weights, immutable matrices, no-island validation, topology-bound checksums, and 9,999 seeded conditional permutations are implemented. Moran output is supportive only; any escalation applies to a future adjusted model. |
| Notebook as tested presentation layer | Implemented | Task 1–4 helpers own statistical logic. The master notebook has more than 100 short cells (maximum 30 source lines) and an AST contract requiring the paper sequence and governed analytic/display Markdown. |
| Governed Tables 1–2 and Figures 1–3 | Implemented | Interactive final expressions render both tables and all figures. Figure 1 contains exact flow counts and an official 77-area map with distinct incomplete, unavailable, and qualification-withheld states. Figures 2–3 preserve EHR/public comparator roles. |
| Deterministic supplementary outputs and manifest | Implemented | Each clean master run emits the frozen 58-file output inventory plus `notebook_run_manifest.json`. The manifest binds input, SAP, lock, notebook, analysis-source, output, provenance, topology, seed, time-zone, commit, and authorization fields. |
| Browser/WASM delivery | Implemented with boundary | Audit verdict remains FAIL for browser/WASM and PASS for intended local batch execution because repository-local packages, Parquet/filesystem writes, and git subprocesses are required. |
| Results freeze and manuscript drafting | Open | No Results prose is authorized. S7 requires independent numerical and artifact review before any flag may change. |

## Display and freeze-candidate checks

- Table 1 has 8 rows and 44 governed fields. It distinguishes suppression,
  unavailable/missing values, and reliability qualification. Community-area COPD has
  457/462 eligible disease rows; each other community source condition has 462/462.
  The map frame has 77 areas, 76 C2-complete areas, 1 incomplete area, 0 unavailable
  areas, and 77 areas with reliability qualification withheld. Tract rows do not
  inherit community-map counts.
- Table 2 has explicit readiness and withholding rows plus four supported sensitivity
  contrasts. It records exact N, IQR scale, CI level, adjustment status, interpretation,
  Moran residual model, topology checksum, escalation decision, and influence fields.
- The full-77 queen topology checksum is
  `f1a9b8ade1bf4ed1258b54f97dd78a8c710dc51cc03350053c99df59b2de7922`.
  The eligible-C2-76 checksum is
  `927384844fbace67e43cd79a2aa757420e026cac1a063f7b4968b784c7e417b5`.
- Independent Task 5 review closed all Important and Minor display, narration,
  provenance, and contract-test findings. Full branch/S7 scientific review remains a
  separate open gate.

## Determinism and run binding

The final verification run emits the governed master output inventory plus
`notebook_run_manifest.json`. The deterministic integration test ran the
notebook twice and matched all output digests, including the manifest; there are no runtime
timestamp exceptions. The final manifest records:

- the exact clean-checkout `git_commit` recorded by the final run;
- `git_dirty=false`;
- `results_authorized=false`;
- `primary_adjusted_models_executed=true` for audit/diagnostic execution only; this does not
  authorize any primary result;
- `seed=20260715`, `permutations=9999`, and `time_zone=America/Chicago`;
- input Parquet SHA-256
  `83ef20728fc5677de82f67d3bf4b257261e7901d4e50765ba8c6e3354f226956`;
- notebook SHA-256
  `0e4c5032dd5d6e1e14bd3f98a3b7f67786c31ae99690e1b2f1185049cfb548a7`;
- SAP SHA-256, captured directly in the manifest;
- `uv.lock` SHA-256
  `5d94e3cd5372017d1b59740e990e002a1d02a3868eb44779437c9591cd733657`.

The final verification manifest records its own output hashes and is the authoritative
source for the exact digest values.

## Surprising audit directions after unit correction

These are directional checks, not findings for publication:

- After converting the frozen tract EHR proportions to percentage points once, the
  median signed EHR-minus-public differences are positive for hypertension
  (`+14.913863`) and combined diabetes (`+17.884336`) but negative for COPD
  (`-0.889255`). Correct scaling therefore reverses the earlier, invalid negative
  exploratory direction for the cardiometabolic comparisons that had treated EHR
  proportions as if they were already percentage points. COPD points in the opposite
  direction from the corrected cardiometabolic differences; code or prose must not
  assume a common sign.
- The conditional diabetes component of the unadjusted cardiometabolic sensitivity is
  near zero (`+0.050401` life-expectancy years per frozen IQR; 95% interval crosses
  zero), while the conditional hypertension component and joint contrast are negative.
  This differs materially from treating the two exposures as interchangeable or
  reporting separate univariable slopes.
- Both unadjusted residual Moran diagnostics cross the prespecified audit gate
  (C1: `I=0.207227`, permutation `P=0.0020`; C2: `I=0.316857`, permutation
  `P=0.0001`). The machine-readable decision is
  `escalate_future_adjusted_model`; it does not retroactively authorize a spatial-error
  model for the `freeze_candidate_primary_model_unsecured` C2 audit candidate. These diagnostics
  remain unauthorized and do not produce manuscript-facing prose.
- C1 remains complete for all 77 areas, whereas C2 uses 76 because suppression makes
  one COPD area incomplete. Annual/temporal denominators also vary when suppression or
  exact diabetes-denominator mismatch rules apply; a nominal 77-area calendar frame is
  not equivalent to an eligible model frame.

## Open gates and noncompliance that must remain visible

1. Freeze a reliability qualification rule before any area can be labeled reliable or
   qualified.
2. Complete independent S7 numerical review, including at least one independent C1
   covariance/interval calculation and one Moran reproduction.
3. Review the supportive Moran escalation against the future adjusted specifications;
   do not interpret the current unadjusted residual results as primary.
4. Keep generated result-bearing files local and untracked, keep
   `results_authorized=false`, and do not draft manuscript Results or Discussion until
   the human results-freeze decision is recorded.

## Audit commands

The freeze checkpoint uses the following command families:

```bash
uv run chicagohealthmap analysis build-dataset --root . --output-dir outputs/frozen
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src
uv run marimo check --strict notebooks/00_master_chicago_healthmap_pipeline.py
uv run notebooks/00_master_chicago_healthmap_pipeline.py --output-dir outputs/notebooks/freeze-a
uv run notebooks/00_master_chicago_healthmap_pipeline.py --output-dir outputs/notebooks/freeze-b
git diff --check
```

The browser/local execution decision is maintained separately in
`docs/analysis/wasm_compatibility_case_studies.md`.
