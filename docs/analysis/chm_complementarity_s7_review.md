# Chicago Health Map Complementarity S7 Verification Review

**Review date:** 2026-07-15
**Implementation branch:** `codex/chm-paper-master-redesign`
**Implementation baseline commit:** `fd760ac`
**Final verification run:** `outputs/notebooks/final-verification/notebook_run_manifest.json`
**Initial implementation commit:** `5a92a04`
**Review result:** computational traceability reviewed; human S7 authorization remains open
**Authorization:** `results_authorized=false` remains in force.

## Scope and current model authority

This is an ecological, cross-sectional/repeated-period analysis and resource evaluation. The
central claim is complementarity of direct CHM EHR-diagnosed tract patterns with secondary public
comparators and community-area life-expectancy summaries—not predictive superiority, validation,
prevalence, causality, or service need.

- C1 is `withheld_vif_above_5`. Any fitted C1 estimate, coefficient, residual, or contrast is
  `audit_only_exploratory` and cannot produce manuscript-facing prose.
- C2 is `freeze_candidate_primary_model_unsecured`. Candidate adjusted fits and diagnostics may
  have executed for audit/diagnostic purposes, but they remain unauthorized.
- `results_authorized=false` means no Results/Abstract/Key Points/Discussion text is authorized.
  This review does not convert a computational candidate into an approved primary result.
- Added tract-lens outputs are `descriptive_measurement_discordance` / exploratory descriptive
  triangulation, added after initial result inspection. Neither CHM nor the public comparator is
  a gold standard.

## Verified implementation and artifact controls

- Full regression, focused contract tests, Ruff, Mypy, and Marimo checks are recorded by the
  implementation reports. The notebook manifest binds the 58 named output artifacts plus itself
  to input, SAP, lockfile, notebook, analysis sources, provenance, topology, seed, time zone,
  commit, and output hashes.
- Robustness artifacts cover model gates, weighted and leave-one-out variants, annual/disruption
  checks, alternative rook and connected-distance topology, adjusted diagnostic data, spatial
  diagnostics, and spatial-error sensitivity. They are audit artifacts, not authorization.
- Tract complementarity artifacts cover rank concordance/discordance, measurement rank gaps,
  within-community heterogeneity, and seeded community-area bootstrap uncertainty. Their
  denominators, units, periods, source roles, and uncertainty fields are recorded in the evidence
  and display ledgers.
- Compact Table 1/Table 2, full eTables, figure legends, figures, and the manuscript handoff are
  named and provenance-bound. Generated local result directories remain untracked.

## Author decision needed

Human authors must independently review every empirical estimate and sentence before any Results,
Abstract, Key Points, or Discussion text is populated. Human authors must decide whether the
freeze-candidate diagnostics are acceptable under the S7 process; until then, no manuscript
import is permitted.

The official JAMA Health Forum instructions were checked directly on July 15, 2026; Tavily's
separate quota failure remains recorded. A new official-page check is required within 30 days of
submission. Ethics, data access, data sharing, funding,
conflicts, contributor, reporting-checklist, and AI-disclosure fields also remain human-owned.

## Not checked or not authorized

- No causal interpretation, intervention effect, service-placement recommendation, or population
  disease estimate was authorized or inferred.
- No new CHM phenotype validation or external clinical adjudication was performed.
- No public-data download was required; the frozen approved dataset remains the source of truth.
- Spatial-error sensitivity is conditional on the prespecified residual Moran gate and remains
  supportive even when executed.

## Handoff boundary

This artifact verifies computational execution and traceability. It does not authorize manuscript
Results, Abstract, Key Points, or Discussion text. The next governance action is an independent
human S7 authorization decision, followed by a complete JAMA-specific submission audit.
