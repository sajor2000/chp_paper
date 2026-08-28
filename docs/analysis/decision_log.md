# Scientific decision log

## 2026-07-14 — ChicagoHealthMap is the primary spatial and clinical base

The study's base spatial data are the first-party ChicagoHealthMap.com/CAPriCORN
exports. Every approved case study must begin with the verified ChicagoHealthMap
geography, time, condition, numerator, denominator, and published measure semantics.
The master analytic dataset and case-study views must retain the ChicagoHealthMap
source record, snapshot, geography identifier, and lineage as their primary keys of
interpretation.

Census ACS, TIGER/Line, CDC PLACES, SVI, Chicago Health Atlas, HRSA, and City of
Chicago boundaries are secondary layers. They may supply contextual covariates,
geographic crosswalks, external comparison, equity context, or service-planning
demonstrations. They may not silently replace the ChicagoHealthMap outcome,
denominator, geography, or case definition, and a secondary model-based estimate
must never be relabeled as an observed ChicagoHealthMap measure.

**Decision:** case-study selection, analytic-dataset construction, marimo notebooks,
tables, figures, and manuscript claims are anchored to ChicagoHealthMap.com data.
The ChicagoHealthMap website data glossary is accepted as authoritative S4
methods evidence. External-source availability does not authorize analysis while
Gate 3 and S4-S6 safeguards remain active; guarded S4 core position mappings
exist for the Chicago case-study frame, but denominator reconstruction, subgroup
labels, suppression handling, S5 case scoring, and S6 SAP approval are still
required before the first-party base can be made analysis-ready.

## 2026-07-14 — Census adapters implemented; Gate 4 remains open

Exact ACS group requests and exact 2019/2020/2023/2024 Illinois TIGER tract filenames
are now executable, fixture-tested contracts. ACS raw JSON and margins of error remain
uncombined; request provenance excludes `CENSUS_API_KEY`. TIGER ZIPs are preserved before
Pyogrio inspection and Cook County filtering, and interim geometry remains in the source
CRS with no reprojection or harmonization.

The 2026-07-13 Census evidence is a verified but legacy combined bulk layout: all 56
registered checksum entries match, but it has no new per-source manifests and does not
pretend to be an API group-response snapshot. **Decision: retain it immutably, disable
live Census fetch by default, and document the format difference rather than rewriting
history. Gate 4 remains OPEN** until every public source is normalized, harmonized, cited,
and traced through the later Phase 4 tasks.

## 2026-07-14 — Phase 4 source registry frozen; Gate 4 remains open

The canonical public-source registry now contains exactly the 14 prespecified source IDs.
Official endpoints and documentation were rechecked on 2026-07-14 without credentials.
No unexplained source-definition drift was found. HRSA's 2026-07-14 daily update is an
expected refresh and does not replace the preserved 2026-07-13 snapshot. Chicago Health
Atlas life expectancy (`VRLE`) and all-cause mortality (`VRDTHR`) remain separate
indicators, periods, estimands, and uncertainty contracts.

The ACS bulk fallback remains justified by the recorded 2026-07-13 HTTP-200 HTML “Missing
Key” observation response. Public API metadata working now does not erase that provenance.
The registered ACS tables are exactly B01001, B03002, B15003, B17001, B19013, B23025,
B25044, and B27001. PLACES `yjkw-uj5s` is explicitly model-based. SVI uses the corrected
2022 Illinois file. Only HRSA service sites and the 77 official community-area boundaries
are admitted for the bounded planning demonstration; police, 311, pharmacy, and WIC are
not admitted.

Tavily was unavailable with `monthly_cap_reached_bonus_eligible`, and Ref MCP was blocked
by OAuth authorization. Official primary pages and endpoint metadata were used as the
documented fallback. **Decision: Gate 4 remains OPEN.** No new live bulk acquisition or
confirmatory modeling is authorized by this registry checkpoint.

## 2026-07-14 — Gate 3 remains closed after deterministic data review

The deterministic review consumes only the frozen, disclosure-safe schema-evidence
checkpoint. It confirms 21 cataloged tables, 549 nonempty field positions, zero verified
positions, zero analysis-usable tables, and zero source rows or values read.

The evidence is insufficient to establish:

- measure naming or phenotype meaning;
- the adult denominator, numerator, or healthcare-capture semantics;
- the distinction among missing, suppressed, and observed zero cells;
- reliability measures or an analysis-ready reliability threshold; or
- whether direct or indirect age adjustment can be reconstructed.

**Decision: Gate 3 remains CLOSED.** Disease candidate scoring, analysis-ready EHR
publication, and confirmatory modeling remain blocked. The notebook does not convert an
unverified positional catalog into a semantic schema and does not treat an unevaluated
quality domain as negative evidence. Source-owner documentation and investigator review
are required before this gate can be reconsidered.

## 2026-07-15 — ChicagoHealthMap website glossary accepted as S4 methods authority

The investigator instructed Codex to treat the ChicagoHealthMap website data dictionary
as the authoritative S4 methods dictionary. The repository now records that decision in
`docs/analysis/s4_methods_mapping.json`, using the official glossary snapshot for
capture rate, census tract geography, small-cell suppression, standardized mean
difference, and capture-rate metric definitions.

**Decision: the website dictionary is authoritative for S4 methods definitions.** This
narrows the remaining blocker to exact source-position mapping. It does not authorize
confirmatory modeling, Results prose, the final analytic dataset, or the combined marimo
case-study notebook before S4-S6 readiness is satisfied.

## 2026-07-15 — S4 core mapping uses a City of Chicago case-study frame

The investigator confirmed that the case studies are within Chicago and that the
Chicago case-study frame may limit the shapefile. The repository now records the
distinction directly in `docs/analysis/s4_methods_mapping.json`: the
CAPriCORN/ChicagoHealthMap source universe remains six-county Chicagoland, while
case-study analytic shapefiles and mapped outputs are restricted to City of Chicago
geographies.

The same S4 packet records guarded core position mappings for geography, year,
condition, diagnosed-condition count, source-published measure, and capture rate.
Adult-denominator reconstruction, subgroup count/rate blocks, and public
fewer-than-10 suppression remain guarded and must be applied or audited in tested
downstream code.

**Decision: S4 has moved from dictionary-only acceptance to guarded core position
mapping for the Chicago case-study frame.** This still does not authorize
confirmatory modeling, Results prose, final analytic dataset construction, or the
combined marimo case-study notebook before S5/S6 authority.

## 2026-07-15 — S5 outcome-blinded scorecard template prepared

The repository now records a non-authorizing S5 scorecard template at
`docs/analysis/s5_case_selection_scorecard.json`. The template extracts the fixed
100-point case-selection anchors from the SAP workbook source of truth, preserves
the City of Chicago case-study frame, and creates candidate shells for the
cardiometabolic bundle and respiratory COPD candidate.

The template is explicitly outcome-blinded. It records forbidden information:
life-expectancy values, mortality values, outcome maps, outcome correlations,
model results, and outcome-linked residuals. It contains no reconciled scores,
case approval, outcome linkage, analytic dataset authorization, or Results
permission.

**Decision: S5 infrastructure is ready for two independent blinded scorers, but
S5 has not passed.** The next evidence required is original scorer worksheets,
reconciled scores, disagreement disposition, and a signed S5 portfolio decision.

## 2026-07-15 — S5 blinded scorer worksheets and approval format prepared

The repository now records `docs/analysis/s5_blinded_scoring_artifacts.json`.
It contains two blinded scorer worksheet templates, each with candidate-domain
rows for the cardiometabolic bundle and respiratory COPD candidate. Scoring rows
now prefill allowed outcome-blinded evidence references to S4/source/literature
artifacts so scorers do not need outcome data to find the admissible inputs. All
score, rationale, hard-gate, and reconciliation fields remain blank or pending.
Each row explicitly records that outcome information was not used.

The same artifact records the reconciliation shell and the exact
`outputs/governance/case_selection.json` approval-record format expected by
manuscript control after S5 is genuinely approved. This is a format/template,
not an approval record.

**Decision: S5 can now be completed by humans without outcome leakage, but S5 is
still pending.** The artifact does not authorize outcome unblinding, model
execution, Results prose, the final analytic dataset, or the combined marimo
case-study notebook.

## 2026-07-15 — S5 reconciliation draft control added

The repository now includes a non-authorizing S5 reconciliation-draft builder for
future completed blinded scorer worksheets. The builder validates that exactly
two scorers completed the worksheets without outcome information, that every
candidate-domain row has an in-range score, nonblank rationale, admissible
evidence references, and a strict hard-gate status, and that the input does not
claim S5 approval or results authorization.

The generated draft is written as
`outputs/governance/case_selection_reconciliation_draft.json` when executed. It
records reconciled totals, scorer totals, hard-gate dispositions, and the
required future approval path `outputs/governance/case_selection.json`, while
preserving `results_authorized=false`. Governance readiness may report
`reconciled_pending_human_approval` only for a valid draft; S6 remains blocked
until human S5 approval and a signed S6 SAP exist.

**Decision: a reconciliation draft can make the human approval packet auditable,
but it is not the S5 approval record.** The draft does not authorize outcome
unblinding, confirmatory modeling, Results prose, the final analytic dataset, or
the combined marimo case-study notebook.

## 2026-07-15 — S5/S6 authority accepted with AI review limitations

The investigator explicitly approved proceeding through S5/S6 unless catastrophic
concerns appear and instructed that the AI S5 scoring review should not remain a
blocking gate. Two independent AI blinded scorers reviewed the S5 worksheet using
only allowed S4/source/provenance and literature references. Their concerns are
retained as advisory limitations and sensitivity/audit targets, especially
candidate-specific quantitative eligibility, suppression, denominator,
tract-precision, and predictor-stability checks.

**Decision: human S5/S6 approval now governs the analytic-dataset and notebook
phase.** AI scoring is advisory rather than dispositive. S6 may authorize
analysis execution, the final analytic dataset, and the combined marimo
case-study notebook while `results_authorized=false` continues to block Results
prose and manuscript drafting until the later result freeze/review.

Machine-readable decision: ignored local artifact
`outputs/quality/gate_3_decision.json`, produced deterministically by
`notebooks/01_data_review.py` from `outputs/quality/ehr_quality.json`.

For reproducibility, this project-coupled notebook is executed through the locked project
environment (`pyproject.toml` and `uv.lock`) rather than a partial PEP 723 dependency
block. This is a deliberate deviation from the generic notebook-plan recommendation:
isolating marimo and pandas would omit the local `chicagohealthmap` package whose reviewed
view logic defines the decision. Notebook input and output are confined to the resolved
repository `outputs/quality` tree.

## 2026-07-14 — Gate 0-4 closeout and offline rebuild

The Task 17 closeout adds an offline rebuild command:

```bash
chicagohealthmap rebuild --through-phase 4 --offline --root PATH
```

The command rejects network-authorizing mode, materializes public-source
normalization from frozen snapshots, rebuilds citations and field lineage, verifies
project provenance, and emits a deterministic disclosure-safe JSON summary. The
current foundation records 15 processed public tables, 645,421 processed public
rows, 5 provenance artifacts, and a 14-record registered public-source inventory.

**Decision: Gate 0 remains PASSED** for repository paths, contracts,
privacy/credential boundaries, test conventions, and immutable snapshot primitives.

**Decision: Gate 1 remains PASSED** for exact configured first-party inventories,
checksum-backed local preservation, safe archive extraction, historical methods
provenance, and explicit unresolved discrepancy records.

**Decision: Gate 2 remains OPEN.** The PubMed/Paperclip universe is preserved, but
1,178 records still require investigator screening, full-text expansion,
comparator adjudication, and novelty review. No novelty, interpretation, or Results
claim is authorized.

**Decision: Gate 3 remains CLOSED.** The first-party schema checkpoint still has 21
tables, 549 nonempty positions, zero verified positions, zero analysis-usable
tables, and zero source rows read for analysis. Disease candidate scoring,
analysis-ready EHR publication, and confirmatory modeling remain blocked.

**Decision: Gate 4 is PASSED for the public-source foundation only.** The 14
registered public source records are authoritative, citable, checksum-backed,
offline-rebuildable, and traceable through emitted processed fields and provenance
artifacts. This public-source decision does not open Gate 2 or Gate 3 and does not
authorize first-party analytic use, case promotion, confirmatory modeling, Results
prose, or manuscript claims. The 2019 ACS sequence-based archive remains preserved
and cited but inventory/citation-only until a tested sequence decoder is added.
