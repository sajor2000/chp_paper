# Reproducible SAP Skill Implementation Plan

> Execute with Superpowers test-first and verification-before-completion discipline. The approved ChicagoHealthMap design and SAP remain scientifically authoritative.

**Goal:** Produce a reference-pattern ChicagoHealthMap SAP workbook and a repository-owned, globally discoverable skill that reproduces rigorous SAP workbooks for future studies.

## Task 1: Freeze evidence and contracts

- [x] Inspect all sheets, columns, styling, and section logic in `SBTSAP_Analysis_Plan_v4.xlsx`.
- [x] Audit the existing ChicagoHealthMap SAP workbook and narrative SAP.
- [x] Verify observational-SAP, prespecification, missing-data, and estimand evidence with PubMed and Paperclip.
- [x] Recheck live official JAMA Health Forum and EQUATOR/RECORD sources.
- [x] Attempt Tavily and record its quota failure; use primary official sources as fallback.
- [x] Use Ref Context for technical-skill research and defer to installed official skill instructions when results are nonauthoritative.
- [x] Run the workbook/skill contract before implementation and retain the expected RED result.

## Task 2: Scaffold the canonical skill

- [ ] Run `skill-creator/scripts/init_skill.py create-statistical-analysis-plan --path skills --resources scripts,references,assets` with user-facing interface metadata.
- [ ] Replace scaffold placeholders with concise trigger-rich `SKILL.md` instructions.
- [ ] Add the workbook-pattern, scientific-rigor, and JSON-schema references.
- [ ] Implement a deterministic artifact-tool builder and validator.
- [ ] Generate the generic template using the builder itself.
- [ ] Run `quick_validate.py` and executable contract tests.

## Task 3: Create the ChicagoHealthMap study specification

- [ ] Encode the reference-pattern `Overview`, `Outputs`, and `Master Variables` rows.
- [ ] Encode governance annexes for protocol, estimands, semantics, selection, methods, sensitivity, reporting, decisions, deviations, and freeze gates.
- [ ] Preserve `PENDING Gate S4/S5/S6` states rather than fabricating decisions.
- [ ] Preserve EHR-diagnosed-proportion, ecological, noncausal, and FQHC/CBO demonstration boundaries.
- [ ] Record the official JAMA Health Forum limits with access date and a pre-submission recheck requirement.

## Task 4: Generate and inspect the deliverables

- [ ] Build `ChicagoHealthMap_Draft_SAP.xlsx` from the committed study specification.
- [ ] Build `assets/SAP_Analysis_Plan_Template.xlsx` from a generic example specification.
- [ ] Validate required sheet order, columns, statuses, and formula-error absence.
- [ ] Render every sheet and visually inspect clipping, wrapping, section bands, widths, and category colors.
- [ ] Correct issues in the builder/specification and regenerate; never hand-fix the binary workbook.

## Task 5: Install, verify, and commit

- [ ] Create a global symlink to the canonical repository skill after confirming the destination is absent or already correct.
- [ ] Invoke the skill validator through the global path.
- [ ] Re-run the original RED contract and require GREEN.
- [ ] Review `git diff --check`, generated-file inventory, and repository status.
- [ ] Commit only the design, plan, skill, specification, template, and regenerated ChicagoHealthMap workbook.

## Freeze and maintenance rules

The JSON study specification is the editable source; generated `.xlsx` files are reproducible products. A workbook change requires a specification or builder change, regeneration, validation, and a decision/deviation entry when scientifically material. Before each new project, copy the generic specification—not the ChicagoHealthMap specification—and rerun current journal/reporting checks. Before manuscript submission, reverify all live journal limits within 30 days.
