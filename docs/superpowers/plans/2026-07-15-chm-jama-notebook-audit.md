# Chicago Health Map JAMA-Structured Notebook Audit

This implementation executes the user-approved plan to audit and refine the master
Marimo notebook into a schema-first, claim-driven JAMA Health Forum narrative.

The governed scientific conclusion is geographic-resolution complementarity. Direct
CHM census-tract patterns may align with public comparators while retaining information
that is lost when tracts inherit a community-area summary. The analysis does not claim
validation, population prevalence, causality, predictive superiority, or service need.

Global constraints:

- Preserve `results_authorized=false`.
- Keep C1 withheld because maximum VIF is 5.016 (>5).
- Keep C2 as an unauthorized freeze candidate.
- Preserve dataset-builder CLI compatibility and its default output stem.
- Use community areas as the governed coarser geography; do not add an ungoverned
  tract-to-ZCTA crosswalk.
- Retain exactly 5 main displays: Table 1, Figures 1-3, and Table 2.
- Keep every Marimo cell at 30 source lines or fewer.
- Use test-driven implementation, verified milestone commits, final Compound
  Engineering review, and complete verification without pushing or opening a PR.

Implementation milestones:

1. Add schema-first data-quality, claim-evidence, and geographic-resolution audits.
2. Build compact evidence-bound Tables 1 and 2 and eliminate hard-coded CI labels.
3. Correct the main and supplementary display semantics and accessibility.
4. Reorder the notebook story and reconcile governance, evidence, and display ledgers.
5. Run full deterministic, interactive, visual, and code-review verification.
