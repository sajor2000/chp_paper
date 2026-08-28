# SAP handoff stabilization

## Problem

The branch inherited six uncommitted changes spanning the ChicagoHealthMap SAP JSON source, two generated workbooks, the reusable builder and validator, and the schema reference. The batch needed to become a reproducible baseline without erasing its scientific intent or implying that the draft SAP authorized analysis.

The inherited change narrows the status vocabulary so Excel can represent it as an inline list, adds accessible red/yellow/green status cues for the new values, and makes the validator reject overlong lists and status values outside the declared vocabulary. The source specification continues to state that gates S4-S6 are not passed, while S7 remains a later validation gate.

## Evidence

- The complete textual diff was reviewed, including every status substitution in `docs/analysis/sap_workbook_spec.json`, the conditional-format additions in `build_sap.mjs`, the status-contract additions in `validate_sap.mjs`, and the schema documentation update.
- The inherited study status list serialized to 309 characters. The stabilized list serializes to 151 characters including Excel's surrounding quotes, below the 255-character inline-list limit. The generic example serializes to 55 characters.
- The generated study workbook contains 19 sheets in the required order: `Overview`, `Outputs`, `Master Variables`, then `Biostat Handoff`. The generic template contains 12 sheets with the same required first three sheets.
- The generic validator passed for both workbooks. The adversarial hardening validator passed for the study workbook and confirmed the principal OLS rule, 97.5% confidence-interval contract, model-sensitive labeling, fixed scoring rule, and handoff-sheet order.
- Formula/error-token searches matched zero cells in both workbooks.
- All 19 study sheets and all 12 template sheets were rendered and inspected. There were no blank/default sheets, clipped key text, unreadable colors, broken section bands, excessive used ranges, or missing front-sheet filters. Status cells combine visible text, validation dropdowns, and restrained color cues rather than relying on color alone.

## Decision

Preserve the inherited scientific and tooling changes, regenerate both binaries from their JSON sources with the loader-provided Node runtime and `@oai/artifact-tool`, and commit the six-file batch together with this record. No scientific design decision was changed during stabilization.

Two fresh independent builds had different SHA-256 hashes. Package-level comparison showed that the differences were randomized relationship identifiers. After normalizing those identifiers, the unpacked XLSX packages were identical for both the study workbook and the generic template. The baseline therefore claims semantic and structural reproducibility, not deterministic byte identity.

## Rejected alternatives

- Hand-editing either `.xlsx` file was rejected because the JSON specification is the editable source of truth.
- Reverting the inherited status vocabulary was rejected because the longer prior vocabulary exceeded the practical inline-list constraint and included near-duplicate workflow labels.
- Moving statuses to a hidden lookup sheet was rejected for this focused stabilization because it would broaden the builder contract and change the inherited design without evidence that the compact inline list is insufficient.
- Claiming byte-for-byte determinism was rejected because fresh builds contain nondeterministic relationship IDs.
- Promoting a spatial or weighted estimator was rejected because diagnostics and sensitivity results cannot replace principal unweighted OLS by convenience.

## Verification

The commands were run from a writable temporary directory whose `node_modules` symlink targeted the loader-provided package directory.

```text
node skills/create-statistical-analysis-plan/scripts/build_sap.mjs --spec docs/analysis/sap_workbook_spec.json --output outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
node skills/create-statistical-analysis-plan/scripts/build_sap.mjs --spec skills/create-statistical-analysis-plan/references/example_spec.json --output skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx
node skills/create-statistical-analysis-plan/scripts/validate_sap.mjs --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx --spec docs/analysis/sap_workbook_spec.json
node skills/create-statistical-analysis-plan/scripts/validate_sap.mjs --workbook skills/create-statistical-analysis-plan/assets/SAP_Analysis_Plan_Template.xlsx --spec skills/create-statistical-analysis-plan/references/example_spec.json
node scripts/qa/validate_sap_hardening.mjs --spec docs/analysis/sap_workbook_spec.json --narrative docs/analysis/statistical_analysis_plan.md --workbook outputs/019f5d68-66a6-74a1-8692-aa10ec6f8497/ChicagoHealthMap_Draft_SAP.xlsx
git diff --check
```

Results: study validator passed with 19 sheets; generic-template validator passed with 12 sheets; hardening contract passed; formula/error-token scans found zero matches; `git diff --check` reported no errors.

## Remaining scientific gates

- S4 must resolve EHR numerator, denominator, phenotype, deduplication, suppression, capture, reliability, geography, and outcome-semantic evidence.
- S5 must complete outcome-blinded candidate scoring and approval.
- S6 must freeze and sign the final variables, estimands, models, weights, multiplicity, sensitivities, environment, and unresolved decisions before confirmatory execution.
- S7 must independently validate numerical outputs and diagnostics before manuscript result freeze.

The workbook remains draft/not frozen, and confirmatory analysis remains unauthorized.

## Reusable lesson

When a controlled vocabulary feeds Excel inline validation, validate both membership and serialized length in the source contract. Treat generated workbook binaries as reproducible semantic artifacts: compare fresh packages structurally and disclose nondeterministic identifiers instead of overstating byte determinism.
