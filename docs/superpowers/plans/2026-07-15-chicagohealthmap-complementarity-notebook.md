# Chicago Health Map Complementarity Notebook Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the governed 77-area analytic dataset, adjusted C1/C2 ecological models,
spatial and robustness diagnostics, and a publication-quality seven-section marimo notebook
showing how Chicago Health Map complements Chicago Health Atlas life-expectancy data.

**Architecture:** Keep the notebook as a thin presentation layer. Extend the existing frozen
dataset and community-frame builders, place primary-model logic in a focused module, place
result-language and display construction in a separate publication module, and reuse the
existing spatial primitives. Every result is typed, checksum-bound, fail-closed, and separated
from manuscript authorization.

**Tech Stack:** Python 3.12+, pandas, NumPy, SciPy, statsmodels, GeoPandas, Shapely,
Matplotlib, Great Tables, marimo, libpysal, esda, spreg, Pydantic, pytest, ruff, mypy, uv.

## Global Constraints

- Chicago Health Map is the primary novel clinical data source; public sources provide the
  outcome, context, adjustment, or triangulation.
- Use “EHR-diagnosed proportion among observed CAPriCORN adults”; never relabel it population
  prevalence, individual risk, incidence, or a population rate.
- Primary adjustment is percentage aged 65 years or older, percentage female, percentage below
  the federal poverty level, and EHR capture ratio.
- ACS adult population is descriptive and a population-weighted sensitivity variable, not a
  primary adjustment covariate.
- C1 and C2 use two-sided 97.5% confidence intervals; separate hypertension and diabetes
  contrasts use 95% intervals.
- Primary models are equal-area OLS with HC3 covariance. Spatial-error modeling is a mandatory
  sensitivity only when `abs(Moran's I) >= 0.10` and permutation `P < .05`.
- The primary model has at most 6 nonintercept parameters; correlation greater than 0.80, VIF
  greater than 5, rank deficiency, nonfinite HC3 covariance, fewer than 70 complete areas, or
  fewer than 10 distinct exposure values fails closed.
- `results_authorized=false` remains governed by a read-only artifact until independent S7
  review; notebook controls cannot alter it.
- Do not draft empirical manuscript Results, Key Points, abstract findings, or conclusions
  before S7 authorization.
- Use Ref MCP for software documentation and Paperclip/PubMed for biomedical citations.
- Preserve user-owned untracked `Downloads/` and `tmp/` directories.
- Follow red-green-refactor TDD for every behavior change and commit after each task.

---

### Task 1: Freeze journal metadata and carry covariates into the primary frame

**Files:**
- Modify: `config/manuscript/jama_health_forum.yml`
- Modify: `src/chicagohealthmap/analysis/case_studies.py:20-215`
- Modify: `tests/unit/analysis/test_case_studies.py`
- Modify: `tests/unit/test_jama_health_forum_skill.py`
- Modify: `docs/superpowers/specs/2026-07-15-chicagohealthmap-complementarity-analysis-notebook-design.md`

**Interfaces:**
- Consumes: the frozen dataset columns produced by
  `build_chicago_case_study_dataset(root, output_dir)`.
- Produces: `build_primary_community_frame(dataset) -> pd.DataFrame` with one value per area for
  `pct_age_65_plus`, `pct_female`, `pct_below_fpl`, `acs_adult_population`, and
  `capture_rate_mean_2022_2024`.

- [ ] **Step 1: Write failing primary-frame and live-journal metadata tests**

```python
def test_primary_frame_carries_exact_community_covariates() -> None:
    dataset = _dataset()
    dataset["pct_age_65_plus"] = 12.0
    dataset["pct_female"] = 51.0
    dataset["pct_below_fpl"] = 18.0
    dataset["acs_adult_population"] = 47_000.0

    row = build_primary_community_frame(dataset).iloc[0]

    assert row[["pct_age_65_plus", "pct_female", "pct_below_fpl"]].tolist() == [
        12.0,
        51.0,
        18.0,
    ]
    assert row["acs_adult_population"] == 47_000.0
    assert row["capture_rate_mean_2022_2024"] == 0.5


def test_jama_config_records_current_live_check() -> None:
    config = yaml.safe_load(CONFIG.read_text())
    assert config["accessed"] == date(2026, 7, 15)
    assert config["source_last_updated"] == date(2026, 6, 30)
```

- [ ] **Step 2: Run the tests and verify the intended failures**

Run:

```bash
uv run pytest tests/unit/analysis/test_case_studies.py::test_primary_frame_carries_exact_community_covariates tests/unit/test_jama_health_forum_skill.py::test_jama_config_records_current_live_check -v
```

Expected: FAIL because the primary frame drops Census covariates and the config lacks
`source_last_updated`.

- [ ] **Step 3: Add an exact one-value-per-area covariate reducer**

```python
PRIMARY_CONTEXT = (
    "pct_age_65_plus",
    "pct_female",
    "pct_below_fpl",
    "acs_adult_population",
)


def _community_context(rows: pd.DataFrame) -> pd.DataFrame:
    missing = sorted(set(PRIMARY_CONTEXT) - set(rows.columns))
    if missing:
        raise CaseStudyAnalysisError(f"community context is missing columns: {missing}")
    records: list[dict[str, object]] = []
    for geography_id, group in rows.groupby("geography_id", sort=True):
        record: dict[str, object] = {"geography_id": geography_id}
        for column in PRIMARY_CONTEXT:
            values = pd.to_numeric(group[column], errors="coerce").dropna().unique()
            if len(values) != 1:
                raise CaseStudyAnalysisError(
                    f"{column} must have exactly one value for community area {geography_id}"
                )
            record[column] = float(values[0])
        records.append(record)
    return pd.DataFrame.from_records(records).set_index("geography_id")
```

Join `_community_context(community)` to the frame in `build_primary_community_frame` with
`validate="one_to_one"` semantics, and retain the existing capture mean.

- [ ] **Step 4: Record the live JAMA check**

```yaml
official_url: https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors
accessed: 2026-07-15
source_last_updated: 2026-06-30
revalidate_days_before_submission: 30
```

- [ ] **Step 5: Run focused and dataset regression tests**

Run:

```bash
uv run pytest tests/unit/analysis/test_case_studies.py tests/unit/analysis/test_dataset.py tests/unit/test_jama_health_forum_skill.py -q
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add config/manuscript/jama_health_forum.yml docs/superpowers/specs/2026-07-15-chicagohealthmap-complementarity-analysis-notebook-design.md src/chicagohealthmap/analysis/case_studies.py tests/unit/analysis/test_case_studies.py tests/unit/test_jama_health_forum_skill.py
git commit -m "feat: carry governed covariates into primary frame"
```

### Task 2: Implement the adjusted primary-model engine

**Files:**
- Create: `src/chicagohealthmap/analysis/primary_models.py`
- Create: `tests/unit/analysis/test_primary_models.py`
- Modify: `src/chicagohealthmap/analysis/__init__.py`
- Modify: `src/chicagohealthmap/analysis/sap_analyses.py:20-160`
- Modify: `tests/unit/analysis/test_sap_analyses.py`

**Interfaces:**
- Consumes: the model-ready community frame from Task 1.
- Produces:
  `fit_primary_model(frame: pd.DataFrame, model_id: Literal["C1", "C2"])
  -> PrimaryModelResult` and
  `fit_primary_models(frame: pd.DataFrame) -> dict[str, PrimaryModelResult]`.

- [ ] **Step 1: Write failing tests for adjustment, scaling, and covariance contrasts**

```python
def test_primary_adjusted_c1_matches_independent_statsmodels_fit() -> None:
    frame = model_frame()
    result = fit_primary_model(frame, "C1")
    transformed, scaling = independent_scaled_frame(frame, "C1")
    x = sm.add_constant(
        transformed[
            [
                "hypertension_ehr_percent_2022_2024",
                "diabetes_ehr_percent_2022_2024",
                "pct_age_65_plus",
                "pct_female",
                "pct_below_fpl",
                "capture_rate_mean_2022_2024",
            ]
        ]
    )
    expected = sm.OLS(transformed[OUTCOME], x).fit(cov_type="HC3")

    actual = result.coefficients.set_index("term")
    assert actual.loc["beta_h", "estimate"] == pytest.approx(expected.params.iloc[1])
    assert actual.loc["beta_d", "estimate"] == pytest.approx(expected.params.iloc[2])
    joint = np.array([0.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0])
    assert result.contrasts.set_index("estimand_id").loc["C1", "estimate"] == pytest.approx(
        float(joint @ expected.params)
    )
    assert result.scaling.set_index("variable").loc[
        "hypertension_ehr_percent_2022_2024", "scale_method"
    ] == "frozen_iqr"


def test_primary_model_uses_capture_not_adult_population_as_adjustment() -> None:
    result = fit_primary_model(model_frame(), "C2")
    terms = set(result.coefficients["source_variable"])
    assert "capture_rate_mean_2022_2024" in terms
    assert "acs_adult_population" not in terms
```

- [ ] **Step 2: Run tests and verify they fail because the module is absent**

Run: `uv run pytest tests/unit/analysis/test_primary_models.py -v`

Expected: collection error for missing `chicagohealthmap.analysis.primary_models`.

- [ ] **Step 3: Define immutable result interfaces and frozen specifications**

```python
OUTCOME = "life_expectancy_mean_2022_2024"
PRIMARY_COVARIATES = (
    "pct_age_65_plus",
    "pct_female",
    "pct_below_fpl",
    "capture_rate_mean_2022_2024",
)
MODEL_EXPOSURES = {
    "C1": (
        "hypertension_ehr_percent_2022_2024",
        "diabetes_ehr_percent_2022_2024",
    ),
    "C2": ("copd_ehr_percent_2022_2024",),
}


@dataclass(frozen=True)
class PrimaryModelResult:
    model_id: str
    population: pd.DataFrame
    coefficients: pd.DataFrame
    contrasts: pd.DataFrame
    residuals: pd.Series
    fitted_values: pd.Series
    diagnostics: pd.DataFrame
    scaling: pd.DataFrame
```

- [ ] **Step 4: Implement deterministic scaling and fail-closed validation**

```python
def _scaled_model_frame(data: pd.DataFrame, exposures: tuple[str, ...]) -> tuple[pd.DataFrame, pd.DataFrame]:
    transformed = data.copy()
    records: list[dict[str, object]] = []
    for column in exposures:
        center = float(data[column].mean())
        scale = float(data[column].quantile(0.75) - data[column].quantile(0.25))
        if not np.isfinite(scale) or scale <= 0:
            raise CaseStudyAnalysisError(f"{column} has a nonpositive frozen IQR")
        transformed[column] = (data[column] - center) / scale
        records.append({"variable": column, "center": center, "scale": scale, "scale_method": "frozen_iqr"})
    for column in PRIMARY_COVARIATES:
        center = float(data[column].mean())
        scale = float(data[column].std(ddof=1))
        if not np.isfinite(scale) or scale <= 0:
            raise CaseStudyAnalysisError(f"{column} has a nonpositive frozen SD")
        transformed[column] = (data[column] - center) / scale
        records.append({"variable": column, "center": center, "scale": scale, "scale_method": "frozen_sd"})
    return transformed, pd.DataFrame.from_records(records)
```

Use `assess_primary_model_readiness` as the execution gate. Replace
`acs_adult_population` in `sap_analyses.ADJUSTMENT_COVARIATES` with
`capture_rate_mean_2022_2024` so the readiness engine and model engine use one contract.

- [ ] **Step 5: Fit OLS-HC3 and extract alpha, beta, gamma, and contrasts**

Fit `statsmodels.api.OLS(...).fit(cov_type="HC3")`. Store every term with `term`,
`source_variable`, `role`, `estimate`, `standard_error`, `confidence_level`, `ci_low`,
`ci_high`, `p_value`, and `unit`. Use 97.5% intervals for C1/C2 and 95% intervals for C1-H
and C1-D. Construct the C1 joint contrast with `[0, 1, 1, 0, 0, 0, 0]` so the full HC3
covariance is used.

- [ ] **Step 6: Add readiness tests for correlation and VIF gates**

```python
def test_primary_model_withholds_when_vif_exceeds_five() -> None:
    frame = model_frame()
    frame["pct_female"] = frame["pct_age_65_plus"] + np.linspace(0.0, 0.01, len(frame))
    with pytest.raises(CaseStudyAnalysisError, match="VIF greater than 5"):
        fit_primary_model(frame, "C1")
```

Add `maximum_absolute_correlation`, `maximum_vif`, `design_rank`, `n`, `p`, `r_squared`, and
`adjusted_r_squared` to `diagnostics`.

- [ ] **Step 7: Run focused tests and commit**

Run:

```bash
uv run pytest tests/unit/analysis/test_primary_models.py tests/unit/analysis/test_sap_analyses.py -q
```

Expected: all selected tests pass.

```bash
git add src/chicagohealthmap/analysis/primary_models.py src/chicagohealthmap/analysis/__init__.py src/chicagohealthmap/analysis/sap_analyses.py tests/unit/analysis/test_primary_models.py tests/unit/analysis/test_sap_analyses.py
git commit -m "feat: add adjusted ecological primary models"
```

### Task 3: Rebase influence and sensitivity analyses on adjusted fits

**Files:**
- Modify: `src/chicagohealthmap/analysis/primary_models.py`
- Modify: `src/chicagohealthmap/analysis/sap_analyses.py:161-335`
- Modify: `tests/unit/analysis/test_primary_models.py`
- Modify: `tests/unit/analysis/test_sap_analyses.py`

**Interfaces:**
- Consumes: `PrimaryModelResult` from Task 2.
- Produces:
  `summarize_adjusted_influence(result: PrimaryModelResult) -> tuple[pd.DataFrame, pd.DataFrame]`
  and `fit_population_weighted_sensitivity(frame, model_id) -> pd.DataFrame`.

- [ ] **Step 1: Write failing tests for adjusted influence and population weighting**

```python
def test_adjusted_influence_uses_primary_design_and_keeps_frozen_iqrs() -> None:
    result = fit_primary_model(model_frame(), "C1")
    areas, summary = summarize_adjusted_influence(result)
    assert len(areas) == 77
    assert set(["cooks_distance", "leverage", "externally_studentized_residual"]) <= set(areas)
    assert summary.iloc[0]["model_id"] == "C1"
    assert summary.iloc[0]["adjustment_set"] == "age65|female|poverty|capture"


def test_population_weighted_model_is_labeled_as_different_estimand() -> None:
    output = fit_population_weighted_sensitivity(model_frame(), "C2")
    assert set(output["analysis_status"]) == {"supportive_different_estimand"}
    assert set(output["weight_variable"]) == {"acs_adult_population"}
```

- [ ] **Step 2: Run tests and verify missing-function failures**

Run: `uv run pytest tests/unit/analysis/test_primary_models.py -k 'influence or weighted' -v`

Expected: FAIL because the two public functions do not exist.

- [ ] **Step 3: Implement adjusted influence without deleting areas from the principal fit**

Use statsmodels influence diagnostics from the fitted primary design, strict thresholds
`Cook > 4/n`, `leverage > 2p/n`, and `abs(externally studentized residual) > 3`. Refit all
leave-one-area-out models with the Task 2 scaling constants held fixed. Report sign changes,
absolute magnitude changes greater than 30%, leave-one-out range, and the exclude-all-flagged
sensitivity.

- [ ] **Step 4: Implement population-weighted WLS sensitivity**

```python
weights = complete["acs_adult_population"].astype(float)
weights = weights / weights.mean()
fit = sm.WLS(y, x, weights=weights).fit(cov_type="HC3")
```

Return the same contrast schema as the primary model with
`analysis_status="supportive_different_estimand"` and
`estimand_description="population-weighted area association"`.

- [ ] **Step 5: Run regression tests and commit**

Run:

```bash
uv run pytest tests/unit/analysis/test_primary_models.py tests/unit/analysis/test_sap_analyses.py -q
```

Expected: all selected tests pass.

```bash
git add src/chicagohealthmap/analysis/primary_models.py src/chicagohealthmap/analysis/sap_analyses.py tests/unit/analysis/test_primary_models.py tests/unit/analysis/test_sap_analyses.py
git commit -m "feat: add adjusted influence and weighting sensitivities"
```

### Task 4: Add governed spatial-error sensitivity

**Files:**
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Modify: `src/chicagohealthmap/analysis/spatial.py`
- Modify: `tests/unit/analysis/test_spatial.py`
- Modify: `src/chicagohealthmap/analysis/primary_models.py`
- Modify: `tests/unit/analysis/test_primary_models.py`

**Interfaces:**
- Consumes: adjusted residuals and scaled design from `PrimaryModelResult` plus frozen geometry.
- Produces:
  `fit_spatial_error_sensitivity(result, geometry, weights) -> pd.DataFrame | None`, where
  `None` means the prespecified Moran gate was not crossed.

- [ ] **Step 1: Add failing spatial-escalation and coefficient-stability tests**

```python
def test_spatial_error_runs_only_when_moran_gate_crosses(monkeypatch: pytest.MonkeyPatch) -> None:
    result = fit_primary_model(model_frame(), "C2")
    monkeypatch.setattr(spatial, "permutation_moran", lambda *_args, **_kwargs: MoranResult(
        observed_i=0.12, expected_i=-1 / 75, p_value=0.01, permutations=9999,
        seed=20260715, weights_checksum="abc", escalation_required=True,
    ))
    output = fit_spatial_error_sensitivity(result, geometry_frame(), queen_weights())
    assert output is not None
    assert set(output["model_type"]) == {"spatial_error"}


def test_spatial_error_marks_model_sensitive_at_twenty_percent_change() -> None:
    assert classify_spatial_stability(-1.0, -1.21) == "model-sensitive"
    assert classify_spatial_stability(-1.0, 0.1) == "model-sensitive"
    assert classify_spatial_stability(-1.0, -1.20) == "stable_at_prespecified_threshold"
```

- [ ] **Step 2: Run tests and verify failures**

Run: `uv run pytest tests/unit/analysis/test_spatial.py tests/unit/analysis/test_primary_models.py -k spatial -v`

Expected: FAIL because spatial-error interfaces and dependencies are absent.

- [ ] **Step 3: Add documented PySAL components**

Add to `pyproject.toml` dependencies:

```toml
"esda",
"libpysal",
"spreg",
```

Run `uv lock` and record resolved versions in the notebook provenance artifact. Ref MCP review
on 2026-07-15 identified PySAL's component documentation and `spreg` as the model component;
verify exact installed signatures with:

```bash
uv run python -c "from libpysal.weights import Queen; from esda import Moran; from spreg import ML_Error; help(ML_Error)"
```

- [ ] **Step 4: Implement the frozen spatial contract**

Use row-standardized queen weights, 9999 permutations, seed `20260715`, and the existing
weights checksum. Convert the frozen `SpatialWeights.neighbors` mapping to `libpysal.weights.W`
without silently adding neighbors. Fit `spreg.ML_Error` with the same scaled `y` and `x`
columns as OLS, `method="full"`, and `epsilon=1e-7`. Record lambda, coefficients, standard
errors, log likelihood, convergence status, package versions, and contrast stability.

- [ ] **Step 5: Run tests and commit**

Run:

```bash
uv run pytest tests/unit/analysis/test_spatial.py tests/unit/analysis/test_primary_models.py -q
```

Expected: all selected tests pass.

```bash
git add pyproject.toml uv.lock src/chicagohealthmap/analysis/spatial.py src/chicagohealthmap/analysis/primary_models.py tests/unit/analysis/test_spatial.py tests/unit/analysis/test_primary_models.py
git commit -m "feat: add prespecified spatial error sensitivity"
```

### Task 5: Build evidence-bound tables, captions, and result language

**Files:**
- Create: `src/chicagohealthmap/analysis/publication.py`
- Create: `tests/unit/analysis/test_publication.py`
- Modify: `src/chicagohealthmap/analysis/__init__.py`

**Interfaces:**
- Consumes: resource-quality tables, `PrimaryModelResult`, influence, Moran, spatial, and
  sensitivity artifacts.
- Produces:
  `build_table_1(...)`, `build_table_2(...)`, `build_full_coefficient_table(...)`,
  `render_coefficient_sentence(...)`, and `build_output_registry(...)`.

- [ ] **Step 1: Write failing semantic and numeric-binding tests**

```python
def test_coefficient_sentence_is_bound_to_result_and_noncausal() -> None:
    row = pd.Series({
        "condition_label": "diabetes",
        "estimate": -1.25,
        "ci_low": -2.10,
        "ci_high": -0.40,
        "confidence_level": 0.95,
        "n": 77,
    })
    sentence = render_coefficient_sentence(row)
    assert "77 eligible Chicago community areas" in sentence
    assert "1-IQR higher" in sentence
    assert "-1.25-year difference" in sentence
    assert "95% CI, -2.10 to -0.40" in sentence
    assert "age composition, sex composition, poverty, and EHR capture" in sentence
    assert "prevalence" not in sentence.casefold()
    assert "caus" not in sentence.casefold()


def test_unauthorized_registry_blocks_manuscript_results() -> None:
    registry = build_output_registry(result_bundle(), results_authorized=False)
    assert set(registry["authorization_label"]) == {
        "freeze candidate — manuscript use unauthorized"
    }
```

- [ ] **Step 2: Run tests and verify the absent-module failure**

Run: `uv run pytest tests/unit/analysis/test_publication.py -v`

Expected: collection error for missing publication module.

- [ ] **Step 3: Implement typed table schemas and JAMA-style rendering**

Use Great Tables only for presentation; CSV tables remain the canonical numeric artifacts.
Table 1 centers CHM coverage, denominator, capture, suppression, missingness, reliability, and
model eligibility. Table 2 centers primary unadjusted and adjusted contrasts, confidence
intervals, model population, spatial decision, and robustness classification. Full alpha,
beta, and gamma coefficients are exported to an eTable.

- [ ] **Step 4: Implement result-sentence and glossary generators**

Result sentences must source every number from one row, use fixed two-decimal formatting, name
the observational unit and adjustment set, and append:

```text
These estimates are ecological associations and do not represent individual risk, causal effects, or population disease prevalence.
```

Before S7, prepend the authorization label and prohibit export to manuscript-result paths.

- [ ] **Step 5: Run tests and commit**

Run: `uv run pytest tests/unit/analysis/test_publication.py -q`

Expected: all selected tests pass.

```bash
git add src/chicagohealthmap/analysis/publication.py src/chicagohealthmap/analysis/__init__.py tests/unit/analysis/test_publication.py
git commit -m "feat: add evidence-bound publication artifacts"
```

### Task 6: Rebuild the marimo notebook in the approved seven-section sequence

**Files:**
- Modify: `notebooks/02_chicago_case_studies.py`
- Modify: `tests/unit/analysis/test_case_studies_notebook_contract.py`
- Modify: `tests/integration/test_case_studies_notebook.py`

**Interfaces:**
- Consumes: Tasks 1 through 5 public functions.
- Produces: one executable marimo notebook with seven reader-visible sections and deterministic
  manuscript/supplement candidate outputs.

- [ ] **Step 1: Replace old notebook contract expectations with failing approved-design checks**

```python
REQUIRED_SECTION_TITLES = (
    "1. Data cleaning",
    "2. Data quality checks",
    "3. Analytic data set",
    "4. Descriptive statistics",
    "5. Case study one",
    "6. Case study two",
    "7. Tables and figures for both case studies",
)


def test_notebook_uses_approved_visible_sequence() -> None:
    source = _source()
    positions = [source.index(title) for title in REQUIRED_SECTION_TITLES]
    assert positions == sorted(positions)


def test_notebook_executes_adjusted_models_and_explains_parameters() -> None:
    source = _source()
    assert "fit_primary_models(" in source
    assert "alpha" in source
    assert "beta_h" in source
    assert "beta_d" in source
    assert "beta_c" in source
    assert "gamma" in source
    assert "results_authorized = False" not in source
```

- [ ] **Step 2: Run contract tests and verify they fail on the legacy structure**

Run: `uv run pytest tests/unit/analysis/test_case_studies_notebook_contract.py -v`

Expected: FAIL because the notebook still uses the old readiness/sensitivity narrative and
hard-coded authorization.

- [ ] **Step 3: Rewrite notebook imports, parameters, and governance loading**

Keep `app = marimo.App(width="full")`. Use `mo.app_meta().mode == "script"` only to select
noninteractive defaults; always render controls. Load authorization from the frozen dataset or
governance manifest and expose it as read-only text, never as a checkbox or dropdown.

- [ ] **Step 4: Implement sections 1 through 4**

Each section must contain adjacent narration with `Question`, `Data`, `Method`, `Why it
matters`, `Assumptions`, and `Audit role`. Display source-role, checksum, record-flow,
period-alignment, cleaning-audit, quality-gate, analytic-frame, schema, Table 1, distributions,
capture diagnostics, and complementary Atlas/CHM maps.

- [ ] **Step 5: Implement mirrored case-study sections 5 and 6**

Each case displays eligibility, formula, parameter glossary, full coefficient table, primary
contrast, adjusted relationship, forest plot, influence table, residual map, Moran diagnostic,
spatial-error result when triggered, and sensitivity summary. Use the same visual grammar and
caption order in both sections.

- [ ] **Step 6: Implement section 7 and the output registry**

Export exactly these canonical families:

```python
MAIN_OUTPUTS = {
    "table_1_chm_coverage_fitness.csv",
    "table_1_chm_coverage_fitness.html",
    "figure_1_complementary_geographic_lenses.png",
    "figure_2_cardiometabolic_case_study.png",
    "figure_3_respiratory_case_study.png",
    "table_2_primary_estimates_robustness.csv",
    "table_2_primary_estimates_robustness.html",
}
```

Also export full coefficients, model scaling, influence, temporal, concordance, Moran/spatial,
sensitivity, provenance, and output-registry CSV files plus `notebook_run_manifest.json`.

- [ ] **Step 7: Run marimo and integration checks**

Run:

```bash
uv run marimo check notebooks/02_chicago_case_studies.py
uv run pytest tests/unit/analysis/test_case_studies_notebook_contract.py tests/integration/test_case_studies_notebook.py -q
```

Expected: marimo check exits 0 and all selected tests pass.

- [ ] **Step 8: Commit**

```bash
git add notebooks/02_chicago_case_studies.py tests/unit/analysis/test_case_studies_notebook_contract.py tests/integration/test_case_studies_notebook.py
git commit -m "feat: rebuild CHM case study marimo notebook"
```

### Task 7: Verify deterministic outputs and independent numerical agreement

**Files:**
- Create: `tests/integration/test_primary_model_independent_reference.py`
- Modify: `tests/integration/test_case_studies_notebook.py`
- Modify: `docs/analysis/sap_notebook_compliance_audit.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: complete implementation and frozen inputs.
- Produces: deterministic two-run evidence, independent C1/HC3/Moran checks, and an updated S7
  audit record that leaves manuscript authorization false until human sign-off.

- [ ] **Step 1: Write an independent matrix-reference integration test**

```python
def test_frozen_c1_matches_independent_matrix_reference() -> None:
    frame = build_primary_community_frame(load_analytic_dataset(FROZEN_DATASET))
    result = fit_primary_model(frame, "C1")
    x, y, contrast = independent_c1_arrays(frame)
    inverse = np.linalg.inv(x.T @ x)
    beta = inverse @ x.T @ y
    residual = y - x @ beta
    leverage = np.diag(x @ inverse @ x.T)
    covariance = inverse @ (
        x.T @ np.diag((residual / (1.0 - leverage)) ** 2) @ x
    ) @ inverse
    expected_estimate = float(contrast @ beta)
    expected_se = float(np.sqrt(contrast @ covariance @ contrast))
    actual = result.contrasts.set_index("estimand_id").loc["C1"]
    assert actual["estimate"] == pytest.approx(expected_estimate, abs=1e-10)
    assert actual["standard_error"] == pytest.approx(expected_se, abs=1e-10)
```

- [ ] **Step 2: Make the deterministic notebook test compare two complete output trees**

Exclude only the self-referential manifest hash according to the recorded policy. Assert equal
file sets, equal bytes for CSV/HTML/PNG outputs, equal population and weights checksums, and
`results_authorized is False` on both runs.

- [ ] **Step 3: Run the independent and deterministic tests**

Run:

```bash
uv run pytest tests/integration/test_primary_model_independent_reference.py tests/integration/test_case_studies_notebook.py -v
```

Expected: all tests pass and two-run hashes match.

- [ ] **Step 4: Record the S7 status without authorizing manuscript results**

Update the compliance audit and decision log with executed checks, exact commands, output
checksums, outstanding human-review owner, and the explicit state
`freeze_candidate_generated; results_authorized=false`.

- [ ] **Step 5: Commit**

```bash
git add tests/integration/test_primary_model_independent_reference.py tests/integration/test_case_studies_notebook.py docs/analysis/sap_notebook_compliance_audit.md docs/analysis/decision_log.md
git commit -m "test: independently verify adjusted notebook outputs"
```

### Task 8: Run the complete quality, reproducibility, and manuscript-contract gate

**Files:**
- Modify only if a verification failure identifies a defect in a file already listed above.

**Interfaces:**
- Consumes: all implementation commits.
- Produces: fresh evidence for correctness, reproducibility, notebook validity, and clean branch
state while preserving `Downloads/` and `tmp/`.

- [ ] **Step 1: Run formatting, lint, and type checks**

```bash
uv run ruff format --check src tests notebooks
uv run ruff check src tests notebooks
uv run mypy
```

Expected: all commands exit 0.

- [ ] **Step 2: Run the complete automated test suite**

```bash
uv run pytest -q
```

Expected: all tests pass with zero failures.

- [ ] **Step 3: Run notebook-specific verification**

```bash
uv run marimo check notebooks/02_chicago_case_studies.py
uv run notebooks/02_chicago_case_studies.py --output-dir outputs/notebooks/s7-freeze-candidate
```

Expected: both commands exit 0 and the output registry contains all main and supplement
artifacts with `results_authorized=false`.

- [ ] **Step 4: Run a second clean notebook build and compare hashes**

```bash
uv run notebooks/02_chicago_case_studies.py --output-dir outputs/notebooks/s7-freeze-candidate-repeat
diff <(cd outputs/notebooks/s7-freeze-candidate && shasum -a 256 * | sort) <(cd outputs/notebooks/s7-freeze-candidate-repeat && shasum -a 256 * | sort)
```

Expected: `diff` exits 0 after applying the manifest self-hash exclusion policy encoded by the
integration test.

- [ ] **Step 5: Inspect the final diff and repository state**

```bash
git diff --check
git status --short
git log --oneline --decorate -10
```

Expected: no whitespace errors; only intentional branch changes plus untouched untracked
`Downloads/` and `tmp/`.

- [ ] **Step 6: Invoke branch-finishing review**

Use `superpowers:requesting-code-review`, then `superpowers:finishing-a-development-branch`.
Do not merge, push, or authorize manuscript results without the user's explicit final choice.
