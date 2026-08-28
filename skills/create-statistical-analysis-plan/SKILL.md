---
name: create-statistical-analysis-plan
description: Create, audit, refine, or regenerate rigorous statistical analysis plans and reference-pattern Excel SAP workbooks for biomedical, public-health, epidemiologic, EHR, clinical, and health-services studies. Use when a user asks for a SAP, analysis plan, output shell, master variable list, estimands, prespecification, journal-ready methods governance, or a reusable SAP template in .xlsx form.
---

# Create Statistical Analysis Plan

Build a study-specific SAP as a versioned JSON specification and a generated Excel workbook. Preserve the compact `Overview` / `Outputs` / `Master Variables` pattern while adding scientific governance annexes.

## Required companion skills

Use `superpowers:brainstorming` before changing the scientific design, `superpowers:writing-plans` for multi-step work, `spreadsheets:Spreadsheets` for workbook operations, and `superpowers:verification-before-completion` before delivery. Use literature and domain tools appropriate to the study; for biomedical work prefer PubMed for reproducible bibliographic search and Paperclip for claim-level full text.

## Workflow

1. Read the protocol, approved design, source registry, data dictionary, target-journal instructions, and any reference workbook. Do not restart an approved design; audit and refine it.
2. Read [workbook-pattern.md](references/workbook-pattern.md), [scientific-rigor.md](references/scientific-rigor.md), and [spec-schema.md](references/spec-schema.md).
3. Render and inspect every supplied workbook before reproducing its conventions.
4. Separate fixed decisions from unresolved decisions. Label unresolved items `PENDING` with an owner, evidence requirement, and freeze gate; never invent them.
5. Write or update a versioned JSON study specification. Keep confidential data and credentials out of it.
6. Build the workbook from a writable temporary directory containing a `node_modules` symlink to the bundled workspace dependency directory:

   `node <skill>/scripts/build_sap.mjs --spec <study-spec.json> --output <output.xlsx>`

7. Validate it:

   `node <skill>/scripts/validate_sap.mjs --workbook <output.xlsx> --spec <study-spec.json>`

8. Render every sheet, inspect legibility and clipping, scan formula errors, and regenerate from source to correct issues. Never hand-fix the binary workbook.
9. Record material post-freeze changes in the deviation log and regenerate.

## Scientific rules

- State population, unit, period, geography, exposure, outcome, contrast, summary measure, and adjustment set for each estimand.
- Distinguish observed-data measures from target-population quantities. EHR-diagnosed proportions are not population prevalence unless a validated transport/standardization estimand establishes that interpretation.
- Keep missing, suppressed, unreliable, structural-zero, and true-zero states distinct.
- Prespecify analysis families, primary/secondary status, model diagnostics, escalation gates, missing-data handling, multiplicity, sensitivity analyses, and any negative-control decision.
- For observational work, use associational and noncausal language unless the design and estimand justify causal identification.
- Preserve outcome blinding for candidate selection when the protocol requires it.
- Map target-journal and relevant reporting rules to exact workbook rows; recheck live requirements near submission.
- Treat translation or planning demonstrations as demonstrations unless implementation and outcomes were actually evaluated.

## Workbook contract

The first three sheets must be `Overview`, `Outputs`, and `Master Variables`, in that order. Use Calibri 10, `#1F4E79` headers, white bold header text, alternating white/light-gray rows, dark-blue section bands, restrained category colors, wrapped text, filters, and frozen panes. `Overview` and `Master Variables` must be filterable Excel tables. `Outputs` is the deliberate filter exception because merged section bands organize its handoff inventory. Annex status columns must use the spec's controlled vocabulary, Excel list validation, and restrained red/yellow/green status cues. Add only useful scientific annexes; do not add decorative dashboards or charts.

Minimum annexes for a governed analytical study are `Protocol`, `Estimands`, `Measure Semantics`, `Analysis Methods`, `Sensitivity Analyses`, `Reporting Checklist`, `Decision Log`, `Deviation Log`, and `Freeze Gates`. Add geography, selection, multiplicity, table/figure, or interpretation annexes when relevant.

## Reuse and ownership

Use [SAP_Analysis_Plan_Template.xlsx](assets/SAP_Analysis_Plan_Template.xlsx) as a visual starter only. The JSON specification is the editable source of truth. Keep the canonical skill in version control and expose it globally by symlink when desired; do not maintain divergent copies.
