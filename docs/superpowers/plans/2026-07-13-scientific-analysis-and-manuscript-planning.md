# ChicagoHealthMap Scientific Analysis and Manuscript Planning Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Freeze a source-grounded, outcome-blinded scientific protocol for selecting two ChicagoHealthMap case studies, estimating ecological associations with life expectancy, triangulating EHR measures with public data, and producing a JAMA Health Forum Original Investigation without writing analysis code before the scientific gates close.

**Architecture:** Evidence, journal rules, EHR semantics, geography/outcome alignment, case-study selection, and the statistical analysis plan are separate reviewable artifacts. Each artifact has a fail-closed gate and a dated deviation record; confirmatory analysis cannot begin until the case-study decision and SAP are frozen while blinded to life-expectancy and cause-specific mortality results.

**Tech Stack:** PubMed MCP; Paperclip MCP; official JAMA Network, EQUATOR, RECORD, Census, CDC, City of Chicago, and Chicago Health Atlas sources; frozen Metopio public catalog; YAML/CSV/Markdown/JSON planning artifacts; later Python, geospatial libraries, marimo, Great Tables, and JAMA-compatible DOCX/XLSX/PDF outputs.

## Global Constraints

- First journal target is **JAMA Health Forum, Original Investigation**.
- Population is adults aged 18 years or older.
- Primary geography is the City of Chicago: direct community-area estimates for 77 community areas and reliability-qualified census-tract estimates.
- Primary EHR period is 2022-2024; 2019 is the pre-pandemic baseline; 2020-2021 is a temporal-disruption period.
- EHR measures are diagnosed proportions among observed CAPriCORN adults, never population prevalence.
- CDC PLACES estimates are model-based small-area estimates, not direct survey estimates and not interchangeable with EHR diagnosed proportions.
- All life-expectancy and mortality analyses are ecological, associational, and noncausal.
- The planned translation product demonstrates questions and planning priorities; it does not claim improved care, allocation, access, or outcomes without an implementation evaluation.
- The leading case studies remain cardiometabolic burden (hypertension and diagnosed diabetes jointly and separately) and respiratory burden (COPD), subject to a formal blinded promotion gate.
- No analysis package, notebook, model, table, or figure code is written while executing the planning tasks in this document.
- Authenticated Metopio access may read a token only from `METOPIO_API_TOKEN`. Never put a token in a prompt, command argument, URL, file, notebook, manifest, log, or chat.
- Cite the originating agency for every public measure and identify Metopio or Chicago Health Atlas only as an access/curation platform when applicable.
- Missing, suppressed, unreliable, and true-zero observations remain distinct at every stage.
- Use the official `marimo-notebook` and `marimo-batch` skills only when notebook implementation begins after Gate S6; they are not activated by this planning-only task.

---

## Baseline Audit and Refinements

This plan audits and operationalizes the already-approved design in `docs/superpowers/specs/2026-07-13-chicagohealthmap-scientific-pipeline-design.md`; it does not reopen the study direction. It supersedes only less-specific future-work language in `docs/superpowers/plans/2026-07-13-phases-0-4-foundation-and-data-acquisition.md` where this document defines a tighter scientific rule.

The following refinements are fixed before analysis:

1. **Study design label:** use “ecological cross-sectional study using routinely collected EHR and public data” in Methods and the structured abstract. Do not put the study type in the title or subtitle.
2. **Primary outcome geography:** use the direct 77-community-area EHR export with community-area life expectancy. Do not aggregate tract EHR counts to community areas for the primary models.
3. **Tract outcome boundary:** the frozen sources do not contain tract-level life expectancy. Tracts support resource description, reliability-qualified mapping, and EHR-versus-PLACES comparison only; they do not support tract-level life-expectancy models.
4. **Primary time alignment:** summarize EHR diagnosed proportions over 2022-2024 and align them with the mean of annual community-area life-expectancy estimates for 2022, 2023, and 2024, subject to the outcome-definition audit in Task 5.
5. **Case-study blindness:** no person scoring candidates may see life-expectancy values, cause-specific mortality values, their maps, correlations, model results, or outcome-linked residuals until Gate S5 is signed.
6. **Discordance interpretation:** EHR/public-data discordance is a difference between measures with different ascertainment and target populations. It is not proof of underdiagnosis, overdiagnosis, unmet need, poor quality, or survey error.
7. **Negative controls:** do not manufacture a negative-control condition or period. Use one only if the evidence review and conceptual model identify a measure with a defensible shared-bias structure and no plausible pathway to the outcome; otherwise record “no valid negative control identified.”

## Source-Grounding Record for This Plan

### Required research tools

| Tool | Status on 2026-07-13 | Use in plan development | Required execution behavior |
|---|---|---|---|
| PubMed MCP | Available | Re-ran the six baseline query families; filtered reconnaissance counts were 255, 102, 279, 211, 39, and 21 before deduplication; verified all 10 named PMIDs and metadata | Save exact effective query, filters, count, paging, PMIDs, and timestamp; PubMed is the bibliographic source of record |
| Paperclip MCP | Available | Loaded the Paperclip skill; reviewed full-text methods/limitations for EHR small-area, selection-bias, COPD spatial, Chicago life-expectancy, and comparator papers | Use full text for methods, limitations, novelty, and claim lines; unavailable full text stays explicit |
| Tavily MCP | Exposed but unavailable | Call returned `monthly_cap_reached_bonus_eligible` and no evidence | Record the quota failure; do not imply Tavily verification occurred; use official primary web pages directly |
| Ref Context MCP | Available, no relevant result | Search for JAMA Health Forum instructions returned no result | Record the zero-result query; use only exact returned documentation URLs when results exist |
| Metopio skill/client | Available | Read the complete skill and its API/provenance references; inspected the frozen 15-file public catalog | Use the frozen catalog first; authenticated access is optional and can occur only through the environment-token client contract |

The initial filtered PubMed reconnaissance returned 907 records across query families before deduplication. That number is not the formal review yield. The formal search removes the `humans` and `has abstract` API filters because incomplete indexing can omit recent papers and relevant methods reports; eligibility is applied during screening.

### Verified comparator implications

- Klompas et al. (PMID 28727539) established a multisystem EHR chronic-disease surveillance precedent and compared adjusted EHR estimates with BRFSS small-area estimates.
- Nielsen et al. (PMID 38447855) showed that EHR and survey small-area estimates can differ systematically because their ascertainment and target populations differ; agreement is not expected by construction.
- Chen et al. (PMID 35945537) used coverage weighting and multilevel regression with poststratification to reduce underrepresentation, while noting that EHR data include only people receiving care.
- Chan et al. (PMID 32487918) compared neighborhood hypertension and diabetes measures from EHR/claims sources with survey estimates in New York City.
- Gabert et al. (PMID 27463641) used aggregated clinical data for local diabetes planning but explicitly treated ecological correlations as hypothesis-generating and suppressed cells with fewer than 15 people.
- Winkelman et al. (PMID 42097616) is the closest comparator: it compared deduplicated multisystem EHR population counts and tract hypertension/diabetes estimates with Census and PLACES, documented demographic coverage differences, and acknowledged understated uncertainty from ignoring spatial correlation.
- Bishop-Royse et al. (PMID 36973497) supports Chicago-specific, pre-pandemic life-expectancy and cause-specific mortality context, not a causal disease-to-life-expectancy claim.
- Blazel et al. (PMID 39177999) and Thomas et al. (PMID 39806634) support neighborhood EHR/spatial precedents while also illustrating selection, modifiable-areal-unit, boundary, and ecological limitations.
- Canfell et al. (PMID 36434553) found sparse evidence that real-world-data surveillance tools had changed practice or policy; this directly supports the planning-demonstration boundary.
- Paperclip also surfaced selection-bias evidence showing that demographic adjustment may improve citywide EHR estimates yet fail at neighborhood level when care-seeking is nonignorable, plus COPD studies using Moran’s I, Getis-Ord Gi*, empirical Bayes, BYM, and geographically weighted approaches. These methods are candidates for diagnostic evaluation, not automatic requirements.

### Official current journal and reporting sources

Use only the live official sources below to freeze requirements, and save an access-date snapshot or checksum where terms permit:

- [JAMA Health Forum Instructions for Authors](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors)
- [JAMA Network Technical Requirements for Figures](https://jamanetwork.com/DocumentLibrary/InstructionsForAuthors/TechnicalRequirementsforFigures.pdf)
- [RECORD statement](https://www.record-statement.org/)
- [STROBE](https://www.equator-network.org/reporting-guidelines/strobe/)
- [STROBE-Equity](https://www.equator-network.org/reporting-guidelines/strobe-equity/)
- [SAGER](https://www.equator-network.org/reporting-guidelines/sager-guidelines/)
- [JAMA updated race and ethnicity guidance](https://jamanetwork.com/journals/jama/fullarticle/2783090)

Current official JAMA Health Forum rules verified on 2026-07-13 are: 3000 main-text words; no more than 5 combined main tables/figures; 50-75 references for observational Original Investigations; structured abstract no longer than 350 words; Key Points of 75-100 words or less using Question, Findings, and Meaning; research title no longer than 100 characters including spaces; no study type/design in the title or subtitle for this nontrial/non-meta-analysis report; Data Sharing Statement; EQUATOR guideline compliance; Word manuscript rather than PDF; figures as separate files; and statistical reporting that presents estimates and uncertainty before P values. Reverify the live page within 30 days before submission and log any change rather than silently editing a frozen rule.

---

## File Responsibility Map

### Evidence and journal governance

- `config/literature_queries.yml`: versioned exact PubMed query strings, API filters, update policy, and query purposes.
- `docs/methods/literature_search_protocol.md`: reproducible search, deduplication, screening, full-text, and citation protocol.
- `sources/literature/pubmed/snapshots/<date>/search_manifest.json`: immutable search calls, effective queries, counts, pages, and PMIDs.
- `sources/literature/pubmed/snapshots/<date>/records.csv`: one bibliographic record per PMID with all query provenance.
- `sources/literature/pubmed/snapshots/<date>/screening.csv`: title/abstract/full-text decisions and exclusion reasons.
- `sources/literature/paperclip/snapshots/<date>/full_text_manifest.csv`: full-text availability, Paperclip identifiers, sections/lines, and claim verification status.
- `docs/methods/evidence_matrix.md`: claim-level evidence, conflicting evidence, gaps, and novelty boundaries.
- `docs/methods/journal_and_reporting_requirements.md`: dated JAMA, STROBE, RECORD, STROBE-Equity, SAGER, and demographic-reporting rules.
- `config/manuscript/core_integrity.yml`, `config/manuscript/observational_ehr.yml`, `config/manuscript/jama_health_forum.yml`: machine-readable rule layers created only after the human-readable requirements are approved.

### Data semantics and harmonization

- `docs/analysis/ehr_measure_semantics.md`: numerator, denominator, observation, suppression, reliability, capture, coverage, and representativeness audit.
- `docs/analysis/geography_harmonization.md`: geography identifiers, vintages, Chicago inclusion rule, direct community areas, and tract crosswalk decisions.
- `docs/analysis/outcome_alignment.md`: exact life-expectancy and mortality definitions, periods, populations, uncertainty, and eligible uses.
- `docs/analysis/data_dictionary.md`: approved analytic names, definitions, source fields, units, universes, vintages, and transformations.
- `docs/analysis/methods_discrepancies.md`: archived-site, export, empirical-behavior, and external-metadata discrepancies.

### Selection and statistical governance

- `config/case_study_selection.yml`: fixed hard gates, scoring rubric, tie-breakers, blindness fields, and portfolio rule.
- `docs/analysis/case_study_selection_protocol.md`: narrative selection protocol and reviewer instructions.
- `outputs/selection/candidate_scorecard.csv`: locked scores and evidence references for all six candidates; created during execution, before outcome access.
- `outputs/selection/case_study_decision.md`: signed promotion/rejection decision and outcome-unblinding authorization.
- `docs/analysis/conceptual_model.md`: causal/structural context diagram used only to choose adjustment domains and interpret noncausal associations.
- `docs/analysis/statistical_analysis_plan.md`: estimands, models, diagnostics, multiplicity, sensitivity analyses, and stop rules.
- `config/analysis.yml`: machine-readable frozen analysis choices created only after the SAP is approved.
- `docs/analysis/decision_log.md`: all scientific decisions with date, decision maker, evidence, and affected artifacts.
- `docs/analysis/deviation_log.md`: departures from the frozen protocol/SAP and their consequences.
- `config/study_manifest.yml`: final study/data/SAP/source/output versions used for manuscript production.

### Translation and publication shells

- `docs/translation/fqhc_cbo_planning_demonstration.md`: allowed uses, prohibited claims, stakeholder questions, and stigma/privacy review.
- `docs/manuscript/table_figure_shells.md`: prespecified main and supplement output shells.
- `docs/manuscript/claim_language_lexicon.md`: allowed and prohibited scientific/translation language.
- `docs/manuscript/submission_checklist.md`: JAMA, reporting, authorship, ethics, data sharing, AI disclosure, and artifact traceability checks.

---

## Task 1: Freeze the Reproducible Literature Protocol

**Files:**
- Create: `config/literature_queries.yml`
- Create: `docs/methods/literature_search_protocol.md`
- Create: `sources/literature/pubmed/snapshots/<search-date>/search_manifest.json`
- Create: `sources/literature/pubmed/snapshots/<search-date>/records.csv`
- Create: `sources/literature/pubmed/snapshots/<search-date>/screening.csv`

**Interfaces:**
- Consumes: approved scientific direction, the six baseline query families, and named seed papers.
- Produces: a deduplicated, screened, updateable PubMed corpus whose search-bounded novelty claims can be audited.

- [ ] **Step 1: Freeze protocol metadata before running the formal search**

Record protocol version, reviewer names, search date/time/time zone, database/tool version when exposed, coverage dates, English-language rationale, inclusion/exclusion criteria, and planned update date. Define `include`, `background`, `exclude`, and `awaiting_full_text`; require one primary exclusion reason from `wrong_geography`, `wrong_data_source`, `wrong_use`, `wrong_population`, `not_empirical_or_methods`, `duplicate`, `no_relevant_outcome`, or `insufficient_report`.

- [ ] **Step 2: Preserve the six baseline queries verbatim as version 1**

Use the exact query strings already printed in Task 6 of `2026-07-13-phases-0-4-foundation-and-data-acquisition.md`. Do not overwrite them. Record the 2026-07-13 filtered reconnaissance counts as a feasibility note only.

- [ ] **Step 3: Add version 2 query amendments**

Run the six baseline strings with `language=english`, publication date from `2000/01/01` through the search date, and **without** PubMed API `species` or `hasAbstract` filters. Add these exact supplemental searches:

```text
selection_and_representativeness:
("Electronic Health Records"[MeSH] OR electronic health record*[Title/Abstract] OR EHR[Title/Abstract]) AND (selection bias[Title/Abstract] OR representativeness[Title/Abstract] OR underrepresentation[Title/Abstract] OR coverage[Title/Abstract] OR capture[Title/Abstract] OR poststratification[Title/Abstract]) AND (neighborhood*[Title/Abstract] OR "small area"[Title/Abstract] OR census tract*[Title/Abstract] OR municipalit*[Title/Abstract])

ehr_public_concordance:
(electronic health record*[Title/Abstract] OR EHR[Title/Abstract] OR health information exchange*[Title/Abstract]) AND (PLACES[Title/Abstract] OR BRFSS[Title/Abstract] OR census[Title/Abstract] OR survey estimate*[Title/Abstract]) AND (hypertension[Title/Abstract] OR diabetes[Title/Abstract] OR COPD[Title/Abstract] OR chronic disease*[Title/Abstract])

copd_spatial_surveillance:
(COPD[Title/Abstract] OR chronic obstructive pulmonary disease[Title/Abstract] OR chronic lower respiratory disease[Title/Abstract]) AND (electronic health record*[Title/Abstract] OR primary care data[Title/Abstract] OR claims[Title/Abstract]) AND (spatial[Title/Abstract] OR geospatial[Title/Abstract] OR neighborhood*[Title/Abstract] OR "small area"[Title/Abstract])

ecological_spatial_methods:
(electronic health record*[Title/Abstract] OR routinely collected health data[Title/Abstract]) AND (spatial autocorrelation[Title/Abstract] OR Moran*[Title/Abstract] OR spatial error[Title/Abstract] OR conditional autoregressive[Title/Abstract]) AND (ecological[Title/Abstract] OR neighborhood*[Title/Abstract] OR census tract*[Title/Abstract])

urban_translation_evidence:
(electronic health record*[Title/Abstract] OR geospatial[Title/Abstract] OR neighborhood data[Title/Abstract]) AND (federally qualified health center*[Title/Abstract] OR FQHC[Title/Abstract] OR community-based organization*[Title/Abstract] OR public health department*[Title/Abstract]) AND (planning[Title/Abstract] OR implementation[Title/Abstract] OR intervention[Title/Abstract] OR evaluation[Title/Abstract])
```

- [ ] **Step 4: Page every PubMed MCP query to completion**

Use deterministic offsets and a fixed page size. Continue until retrieved PMIDs equal the returned `totalCount`; fail if a page repeats, the count changes within the same run, or the union is incomplete. Save the original query, effective query, applied filters, search URL, total count, offset, page PMIDs, summaries, and retrieval timestamp. Do not save only top-ranked results.

- [ ] **Step 5: Verify and tag the 10 named seed papers**

Require PMIDs `28727539`, `38447855`, `35945537`, `32487918`, `27463641`, `42097616`, `36973497`, `39177999`, `36434553`, and `39806634` in `records.csv`, tagged `seed_verification`. A missing seed triggers a query-sensitivity note; it is not silently inserted as if retrieved.

- [ ] **Step 6: Deduplicate without losing provenance**

Create one row per PMID. Preserve every matching `query_id`, query version, page, rank, and seed status. Reconcile `unique(PMID)` against the set union of all page manifests.

- [ ] **Step 7: Screen title/abstract and full-text eligibility**

Include human urban/subregional EHR, HIE, claims, clinical-network, small-area, representativeness, ecological/spatial, life-expectancy/mortality, public-comparator, and planning/evaluation studies. Include reporting and methods papers even when PubMed has no `humans` tag. Exclude individual risk-prediction studies without geographic/public-health relevance and purely clinical interventions without a resource, surveillance, or planning contribution. Do not use journal prestige, effect direction, statistical significance, or similarity to expected Chicago results as criteria.

- [ ] **Step 8: Run citation chasing and an update search**

For every included systematic/scoping review and the closest comparator, screen references and PubMed related articles. Repeat all queries within 90 days before manuscript submission; add a new dated snapshot and do not modify the original.

- [ ] **Step 9: Audit and commit the literature protocol batch**

Verify complete paging, deduplication, all seed dispositions, exclusion reasons, and date-bounded language.

```bash
git add config/literature_queries.yml docs/methods/literature_search_protocol.md sources/literature/pubmed
git commit -m "research: freeze reproducible literature protocol"
```

**Gate S1:** The corpus is reproducible and all records have query provenance and a screening status. Search absence may support only “we did not identify,” never “no study exists.”

---

## Task 2: Build the Full-Text Evidence and Novelty Matrix

**Files:**
- Create: `sources/literature/paperclip/snapshots/<search-date>/full_text_manifest.csv`
- Create: `docs/methods/evidence_matrix.md`
- Modify: `docs/methods/literature_search_protocol.md`

**Interfaces:**
- Consumes: included/background PubMed records.
- Produces: verified claim-level support, conflicting evidence, gaps, and bounded novelty statements.

- [ ] **Step 1: Confirm the Paperclip repository is related before reuse**

Run `paperclip repo status`. Reuse `chicago-ehr-small-area-evidence` only if its contents remain limited to this review; otherwise initialize a new topic repository. Record the repository/branch name in the full-text manifest.

- [ ] **Step 2: Retrieve full text and record availability**

For each included/background paper, use Paperclip `lookup`, `search -s pmc`, and section/line reads. Record `available`, `abstract_only`, `not_found`, or `access_limited`. Use PubMed Central full text through PubMed MCP as a documented fallback when Paperclip has not indexed a valid PMCID, as occurred for PMID 42097616 during planning. Never infer full-text methods from an abstract.

- [ ] **Step 3: Extract a fixed set of fields**

For every paper record study design, place, years, population, eligibility/lookback, EHR source/systems, deduplication, numerator/phenotype, denominator, geography, vintage/crosswalk, suppression, missingness, capture, representativeness adjustment, external comparator, outcome, spatial method, temporal method, limitations, evaluated implementation outcome, and exact supporting section/lines.

- [ ] **Step 4: Create claim-level rows**

Use one claim per row with columns: `claim_id`, `claim_text`, `claim_class`, `evidence_role`, `pmid`, `pmcid`, `doi`, `study_design`, `population_match`, `geography_match`, `measure_match`, `full_text_status`, `support_location`, `support_strength`, `conflict`, `limitations`, `allowed_manuscript_use`, `prohibited_inference`, and `verified_by/date`.

Required claim classes are: resource precedent; multisystem deduplication; EHR denominator/capture; selection and representativeness; phenotype validity; suppression and missingness; small-area estimation; EHR/public concordance; discordance interpretation; Chicago life-expectancy context; cardiometabolic rationale; COPD rationale; spatial/ecological limitations; FQHC/CBO planning; evaluated implementation impact; RECORD/STROBE reporting; and novelty gap.

- [ ] **Step 5: Verify material claims in Paperclip**

Add each planned material claim to the Paperclip repository with exact line ranges when available, commit the claim set, and run `repo status`. Only `[OK]` claims may be labeled `direct`; revise, downgrade, or remove `[X]` claims. PubMed metadata verification does not substitute for claim verification.

- [ ] **Step 6: Write a novelty map with bounded language**

Compare ChicagoHealthMap against: single-system maps; multisystem surveillance networks; EHR-versus-BRFSS/PLACES studies; Chicago mortality/life-expectancy studies; disease-specific hotspot studies; and implemented/evaluated planning studies. Candidate novelty wording must state the databases, end date, geography, measures, and distinguishing combination. The informatics contribution—not mere mapping—is the primary novelty claim.

- [ ] **Step 7: Commit the evidence batch**

```bash
git add sources/literature/paperclip docs/methods/literature_search_protocol.md docs/methods/evidence_matrix.md
git commit -m "research: verify full-text evidence and novelty boundaries"
```

**Gate S2:** Every material Methods, limitations, novelty, and interpretation claim has a verified citation or is explicitly labeled a gap. Translation claims distinguish proposed use from evaluated impact.

---

## Task 3: Freeze JAMA and Reporting Requirements

**Files:**
- Create: `docs/methods/journal_and_reporting_requirements.md`
- Create: `config/manuscript/core_integrity.yml`
- Create: `config/manuscript/observational_ehr.yml`
- Create: `config/manuscript/jama_health_forum.yml`
- Create: `docs/manuscript/submission_checklist.md`

**Interfaces:**
- Consumes: live official sources only for current JAMA requirements.
- Produces: dated human- and machine-readable manuscript/reporting rules.

- [ ] **Step 1: Record source/tool provenance**

Log the official URL, page title, access timestamp, relevant section, and checksum/snapshot if permitted. Record Tavily’s quota failure and Ref Context’s zero-result query; do not cite either as evidence. Reject blogs, author-service summaries, cached snippets without the official page, and requirements copied from another JAMA journal when JAMA Health Forum has a specific rule.

- [ ] **Step 2: Freeze the Original Investigation adapter**

Encode the current 3000-word, 5-table/figure, 50-75-reference, 350-word structured-abstract, 75-100-word Key Points, 100-character title, study-type, Data Sharing Statement, Word-file, separate-figure, and EQUATOR rules. Keep `Design`, `Setting`, and `Participants` separate at submission even if JAMA later combines them in editing. Use `Exposures`, `Main Outcomes and Measures`, `Results`, and `Conclusions and Relevance` for this observational study.

- [ ] **Step 3: Create a reporting-guideline crosswalk**

Use STROBE cross-sectional as the base checklist and RECORD as a required extension for routinely collected EHR data. Add STROBE-Equity because health equity is central, and SAGER/JAMA demographic guidance because sex/gender and race/ethnicity are present in resource/representation analyses. Map each item to manuscript section, supplement, table/figure, source artifact, owner, and status.

- [ ] **Step 4: Fix sex/gender and race/ethnicity rules**

Report the exact source variable and ascertainment method; never relabel a field called `gender` as biological sex or vice versa. Report all observed categories, define unknown/other categories without treating them as persons’ identities, explain why variables are used, and describe race/ethnicity as social classifications and markers of structural context rather than biological risk. If main outcomes cannot be reported by sex/gender because only aggregate area data exist or suppression prevents it, state the limitation and do not fabricate stratified estimates.

- [ ] **Step 5: Fix equity-reporting rules**

Define the equity-relevant question, population, structural context, comparator, and potential intervention level. Report who is absent from EHR capture, how geography and structural racism may shape measures, and whether results are likely transportable beyond CAPriCORN/Chicago. Avoid deficit framing, stigmatizing map labels, and causal interpretations of racialized neighborhood composition.

- [ ] **Step 6: Add current-JAMA revalidation gates**

Recheck the official page at SAP freeze, manuscript freeze, and within 30 days before submission. Any difference produces a dated rule-version increment and deviation entry; scientific results do not change to fit a journal rule.

- [ ] **Step 7: Commit the journal/reporting batch**

```bash
git add docs/methods/journal_and_reporting_requirements.md config/manuscript docs/manuscript/submission_checklist.md
git commit -m "docs: freeze journal and observational reporting rules"
```

**Gate S3:** Current JAMA requirements are supported only by official JAMA sources; STROBE, RECORD, STROBE-Equity, SAGER, and demographic-reporting obligations have an artifact destination.

---

## Task 4: Complete the EHR Measure Semantic Audit

**Files:**
- Create: `docs/analysis/ehr_measure_semantics.md`
- Create: `docs/analysis/data_dictionary.md`
- Create: `docs/analysis/methods_discrepancies.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: immutable CAPriCORN exports, archived ChicagoHealthMap methods, source manifests, and empirical invariants.
- Produces: a signed meaning and usability decision for every analytic field without modeling outcomes.

- [ ] **Step 1: Create a three-source semantic ledger**

For every field, place archived-site wording, export/schema wording, and empirical behavior side by side. Record agreement, contradiction, unresolved question, decision owner, and evidence. No interpretation wins silently.

- [ ] **Step 2: Resolve the numerator**

Determine whether a numerator is unique adults, diagnoses, encounters, or another count; whether a person can appear in multiple systems; whether cross-system deduplication occurred; diagnosis-code/value-set definition and version; active/inactive condition logic; lookback; multiple-diagnosis requirement; laboratory/medication inclusion; age anchor; residence anchor; and condition-specific exclusions. Resolve hypertension, diabetes without documented complication, COPD, heart failure, stroke, and drug use disorder separately.

- [ ] **Step 3: Resolve the denominator**

Determine exactly what makes an adult “observed,” encounter type, lookback, alive/resident requirements, assigned system, duplication, condition-specific versus shared denominator, year boundary, and whether annual denominators can be summed. Confirm empirically that denominators are shared within geography-year before using that statement. If annual adults can repeat across years, call a summed 2022-2024 denominator `observed adult-years`, not unique adults.

- [ ] **Step 4: Resolve diagnosed-proportion arithmetic**

Verify `numerator / denominator` against every exported percentage within a prespecified rounding tolerance. Separate exact values from display rounding. Any inconsistent file/year/geography is withheld until explained.

- [ ] **Step 5: Resolve suppression and zero semantics**

Identify the disclosure threshold and whether `0`, blank, sentinel values, missing rows, or flags encode suppressed counts. Cross-tabulate numerator, percentage, age cells, totals, and file presence. Never reverse-engineer a suppressed numerator from a rounded percentage for primary analysis. Until resolved, use `zero_or_suppressed`; an unresolved convention blocks Gate S4.

- [ ] **Step 6: Resolve reliability**

Document the source reliability field/algorithm if one exists. Independently calculate a Wilson 95% interval for usable binomial-like diagnosed proportions as a descriptive precision diagnostic, not proof of unbiasedness. Predefine display tiers after source validation: high precision when half-width is at most 5 percentage points; moderate when greater than 5 and at most 10; withhold inferential display when greater than 10 or suppressed. Source disclosure/reliability rules override a looser calculated tier.

- [ ] **Step 7: Resolve coverage and capture**

Define:

```text
annual EHR coverage ratio = observed adult denominator / ACS adult population estimate
```

Call it a coverage ratio, not sampling probability or population coverage, until deduplication/residency/time semantics are proven. Inspect values above 1, denominator discontinuities, system additions/removals, and geographic migration. For 2022-2024, use mean annual denominator divided by an aligned ACS adult estimate for coverage; do not divide summed adult-years by a one-year population estimate.

- [ ] **Step 8: Audit representativeness**

Compare EHR and ACS distributions for aligned age, sex/gender, and race/ethnicity categories using absolute percentage-point differences and standardized differences. Preserve ACS margins of error. Mark categories that cannot be aligned. Do not “correct” EHR diagnosed proportions through poststratification unless a separate approved estimand and validation plan is added; selection may be nonignorable at neighborhood level.

- [ ] **Step 9: Define analytic states and stop rules**

Every geography-condition-year receives exactly one state: `usable`, `suppressed`, `zero_confirmed`, `missing_expected`, `not_covered`, `unreliable`, or `semantic_hold`. No primary model uses anything except `usable`. Model-specific coverage thresholds are frozen in the SAP after the state audit, without viewing outcomes.

- [ ] **Step 10: Commit the semantic-audit batch**

```bash
git add docs/analysis/ehr_measure_semantics.md docs/analysis/data_dictionary.md docs/analysis/methods_discrepancies.md docs/analysis/decision_log.md
git commit -m "research: resolve EHR measure and denominator semantics"
```

**Gate S4:** Investigators can state what numerator, denominator, proportion, suppression, reliability, coverage, and representativeness mean and do not mean. Any unresolved numerator, denominator, deduplication, or suppression ambiguity blocks selection and modeling.

---

## Task 5: Freeze Geography, Vintage, and Outcome Alignment

**Files:**
- Create: `docs/analysis/geography_harmonization.md`
- Create: `docs/analysis/outcome_alignment.md`
- Modify: `docs/analysis/data_dictionary.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: EHR geography fields; TIGER/Line 2019, 2020, 2023, 2024; official community areas; PLACES 2025; Chicago Health Atlas life expectancy/mortality.
- Produces: one approved geography and period contract for every planned comparison.

- [ ] **Step 1: Determine the EHR tract vintage rather than infer it from study year**

Compare all EHR GEOIDs and geometries, if available, against each frozen TIGER vintage. Report exact matches, retired/new GEOIDs, split/merged tracts, geometry-only changes, and unmatched values. Study year does not prove boundary vintage.

- [ ] **Step 2: Define the Chicago tract universe**

Use the official City boundary/community-area geometry and a documented inclusion rule. Preferred rule: include tracts whose population-weighted representative point lies within Chicago when official Census place assignment is available; otherwise require a prespecified spatial intersection threshold and sensitivity analysis. Report boundary-crossing tracts separately.

- [ ] **Step 3: Use direct community-area EHR data for primary models**

Validate that all community-area IDs map one-to-one to the official 77 areas. Do not derive primary community-area disease counts from tracts. Compare direct community-area totals with any tract rollup only as a quality diagnostic.

- [ ] **Step 4: Restrict primary tract concordance to stable geography**

CDC PLACES 2025 uses 2023 tract boundaries. Use exact stable GEOID/geometry matches for the primary EHR-versus-PLACES tract analysis. If EHR tracts require crosswalking, use an official Census relationship file or population-weighted block crosswalk; do not allocate disease counts by centroid. Report stable-only results as primary and population-weighted crosswalk results as sensitivity. If no authoritative population crosswalk is available, do not create one from land area and call it population preserving.

- [ ] **Step 5: Document tract-to-community-area limitations**

Community areas and tracts are not assumed to nest exactly. A split tract cannot be assigned wholly by centroid for count aggregation. If a descriptive tract-to-community-area summary is required, use population-weighted fractions, show weight sums, preserve denominators/numerators within tolerance, and label the allocation assumption; it remains secondary because direct community-area estimates exist.

- [ ] **Step 6: Audit life expectancy**

Confirm that `VRLE` is life expectancy at birth, annual, community-area based, unstratified population code blank for the primary outcome, and available for all 77 areas in 2022-2024. Verify formula/method documentation, suppression, impossible values, and the absence of standard errors in frozen responses. If “at birth” or annual methodology cannot be confirmed from the originating agency, describe the outcome only using the verified Chicago Health Atlas definition and record the limitation.

- [ ] **Step 7: Freeze primary alignment**

Primary predictor: 2022-2024 pooled direct community-area EHR diagnosed proportion, calculated from summed usable numerators and denominators only if denominator semantics allow adult-year pooling. Primary outcome: arithmetic mean of the same area’s 2022, 2023, and 2024 annual life-expectancy values. If a year is missing, do not average the remaining two for primary analysis; mark the area incomplete.

- [ ] **Step 8: Freeze baseline and disruption alignment**

Use 2019 EHR and 2019 life expectancy as the pre-pandemic baseline. Treat 2020 and 2021 as separate annual disruption observations. Do not include 2020-2021 in the main contemporary pool. Describe changes relative to 2019 and 2022-2024 without attributing them to the pandemic absent a causal design.

- [ ] **Step 9: Freeze supportive mortality alignment**

Use Chicago Health Atlas 2020-2024 age-adjusted mortality windows, if complete and verified, as supportive outcomes: heart disease and diabetes mortality for cardiometabolic burden; chronic lower respiratory disease mortality for COPD; all-cause mortality for context. State that these 5-year outcomes overlap but are not identical to the 2022-2024 EHR window. Do not describe chronic lower respiratory disease mortality as COPD mortality.

- [ ] **Step 10: Commit the harmonization batch**

```bash
git add docs/analysis/geography_harmonization.md docs/analysis/outcome_alignment.md docs/analysis/data_dictionary.md docs/analysis/decision_log.md
git commit -m "research: freeze geography and outcome alignment"
```

**Gate S5-ready prerequisite:** Every comparison has explicit source/target geography, vintage, period, population, units, and crosswalk status. No tract-level life-expectancy model is authorized.

---

## Task 6: Run the Outcome-Blinded Case-Study Scorecard

**Files:**
- Create: `config/case_study_selection.yml`
- Create: `docs/analysis/case_study_selection_protocol.md`
- Create during execution: `outputs/selection/candidate_scorecard.csv`
- Create during execution: `outputs/selection/case_study_decision.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: Gate S2 evidence, Gate S4 semantic states, predictor-only coverage/stability summaries, and comparator metadata.
- Produces: signed case-study promotion and outcome-unblinding decision.

- [ ] **Step 1: Enforce blindness**

Create separate predictor-only and outcome data permissions. Candidate reviewers receive EHR disease summaries, coverage/reliability, definitions, literature evidence, and comparator availability only. They do not receive life expectancy, mortality, outcome maps, outcome correlations, model fit, association P values, or outcome-linked residuals. Hash the outcome files before selection and record that they were not opened.

- [ ] **Step 2: Apply hard gates to all six candidates**

A candidate fails regardless of score if any of the following applies:

1. numerator/denominator/phenotype or suppression remains unresolved;
2. fewer than 90% of 231 community-area-years in 2022-2024 are usable, or any single year has less than 85% usable community areas;
3. fewer than 60% of in-scope tracts are displayable at moderate-or-better precision in each contemporary year, unless investigators predeclare a community-area-only case study;
4. no independent comparator or aligned supportive mortality construct exists;
5. the literature matrix has no defensible public-health rationale;
6. the candidate duplicates another promoted case study without a distinct informatics lesson; or
7. privacy/disclosure rules prevent the promised analysis.

- [ ] **Step 3: Score each passing candidate out of 100**

| Domain | Points | Fixed scoring rule |
|---|---:|---|
| Community-area usability | 15 | 15 for at least 98%; 12 for 95-97.9%; 8 for 90-94.9%; hard fail below 90% |
| Tract usability/precision | 15 | 15 for at least 90%; 12 for 80-89.9%; 8 for 70-79.9%; 4 for 60-69.9%; hard fail below 60% unless community-only predeclared |
| Predictor temporal stability | 10 | 10 if median area rank correlation across 2022, 2023, 2024 is at least 0.80 and no system discontinuity; 7 for 0.60-0.79; 3 below 0.60; 0 with unexplained discontinuity |
| Phenotype interpretability | 15 | 15 for validated/stable definition and exclusions; 10 for stable diagnosis-only definition with documented sensitivity; 5 for material coding ambiguity; hard fail if unresolved |
| Comparator definition/period availability | 15 | 15 for aligned crude adult comparator at both tract and community-area levels; 10 for one level; 5 for a materially different but interpretable comparator; 0 for none |
| Evidence and novelty gap | 15 | 15 direct rationale plus search-bounded gap; 10 supportive rationale/gap; 5 crowded literature with limited distinct contribution; 0 no rationale |
| Translation questionability | 10 | 10 for concrete FQHC/CBO questions supported by measure semantics; 5 for general public-health relevance; 0 if only speculative action claims are available |
| Distinct portfolio contribution | 5 | 5 for a different phenotype/ascertainment/reliability lesson; 2 for partial overlap; 0 for duplication |

Scores use only prespecified thresholds and documented evidence. Do not score observed EHR/public correlation magnitude, life-expectancy association, mortality association, map appearance, hot-spot count, P value, or preferred narrative.

- [ ] **Step 4: Evaluate the cardiometabolic bundle**

Hypertension and diabetes must each pass hard gates and score at least 70. The joint case study additionally requires at least 85% usable joint community-area-years and variance-inflation factor below 5 in a predictor-only collinearity audit. If it passes, its component scores remain visible and the case study must report hypertension and diabetes jointly and separately.

- [ ] **Step 5: Select a two-case-study portfolio**

Promote the cardiometabolic bundle if its rule passes. Select the highest-scoring nonduplicative second candidate with score at least 70; COPD remains the expected respiratory choice. If COPD fails, document the failed gate and use the highest-scoring defensible alternative. Do not replace any promoted candidate after unblinding because an association is null, weak, or inconvenient.

- [ ] **Step 6: Use fixed tie-breakers**

For equal total scores use, in order: higher semantic/phenotype score; higher community-area usability; stronger comparator-definition alignment; greater portfolio distinctiveness; then investigator adjudication with a written rationale. Outcome information is never a tie-breaker.

- [ ] **Step 7: Sign and commit the decision before unblinding**

`case_study_decision.md` records all six scores, hard-gate results, reviewer conflicts, promoted/rejected candidates, date/time, file hashes, and signatures/approvals. Only then authorize access to outcome files.

```bash
git add config/case_study_selection.yml docs/analysis/case_study_selection_protocol.md outputs/selection docs/analysis/decision_log.md
git commit -m "research: freeze blinded case study selection"
```

**Gate S5:** Two case studies are fixed while blinded to outcomes. Null results cannot trigger substitution.

---

## Task 7: Freeze the Conceptual Model and Explicit Estimands

**Files:**
- Create: `docs/analysis/conceptual_model.md`
- Create: `docs/analysis/statistical_analysis_plan.md`
- Create: `config/analysis.yml`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: promoted case studies and harmonization rules.
- Produces: an outcome-aware but result-blind SAP with explicit estimands and model families.

- [ ] **Step 1: State the scientific questions without causal wording**

Primary resource question: how do EHR diagnosed proportions, coverage, reliability, and public-data concordance vary across Chicago? Primary association question: what ecological difference in community-area life expectancy is associated with higher contemporary EHR-diagnosed burden after prespecified area-level adjustment? Translation question: which reliability-qualified concordant/discordant patterns can formulate local questions?

- [ ] **Step 2: Define the observed-EHR estimand**

For condition `k`, area `g`, and period `t`:

```text
p_EHR(k,g,t) = diagnosed observed adults / observed adult denominator
```

The target is the observed CAPriCORN adult population under the verified encounter/lookback/residence rule. It is not all Chicago adults and not population prevalence.

- [ ] **Step 3: Define primary community-area association estimands**

Use one row per community area for the 2022-2024 primary analysis.

- Cardiometabolic joint estimand: adjusted mean difference in life expectancy, in years, comparing a simultaneous predictor-only interquartile-range increase in hypertension and diabetes diagnosed proportions, calculated from the covariance matrix of their jointly modeled coefficients.
- Hypertension estimand: adjusted mean difference in life expectancy per hypertension IQR, conditional on diabetes and covariates.
- Diabetes estimand: adjusted mean difference in life expectancy per diabetes IQR, conditional on hypertension and covariates.
- COPD estimand: adjusted mean difference in life expectancy per COPD IQR and, secondarily, per 10 percentage-point increase if 10 points lies within observed support.

Freeze predictor IQRs before fitting outcome models. Report IQR-scaled and raw percentage-point coefficients; do not interpret an unsupported extrapolation.

- [ ] **Step 4: Define descriptive public-comparator estimands**

For each disease/geography report Spearman rank correlation, Pearson correlation as supportive, median signed percentage-point difference, median absolute percentage-point difference, and rank-quartile classification. Because measures differ, call these concordance/discordance summaries rather than validation accuracy. Do not use Lin concordance or Bland-Altman as proof of interchangeable measurement; if shown for comparability with Winkelman et al., label the construct mismatch explicitly.

- [ ] **Step 5: Freeze adjustment domains from a conceptual model**

Use adult age composition, socioeconomic conditions, insurance/access, racialized neighborhood composition as structural context, EHR coverage/reliability, and calendar alignment. Do not select covariates by univariable P value, automated stepwise selection, or improvement in the preferred exposure result. Limit the 77-area primary model to prespecified parsimonious representatives, normally no more than 1 variable per domain and no more than 6 nonintercept degrees of freedom for the COPD model or 7 for the joint cardiometabolic model.

- [ ] **Step 6: Predefine collinearity and support gates**

If VIF is at least 5, condition index is at least 30, or hypertension/diabetes correlation exceeds 0.90, withhold conditional component interpretation and retain only a prespecified joint contrast or separate models. Use restricted cubic splines only if predictor-only distribution and at least 10 observations per spline degree support them; otherwise use linear terms and show binned descriptive plots without fitting outcome-selected cut points.

- [ ] **Step 7: Freeze noncausal language**

Allowed: `associated with`, `correlated with`, `spatially aligned`, `higher/lower diagnosed proportion`, `concordant`, `discordant`, `planning hypothesis`. Prohibited: `effect`, `impact`, `caused`, `drove`, `explained the gap`, `risk factor` when referring to the ecological EHR exposure, `underdiagnosed`, `unmet need`, `improved allocation`, or `targeted successfully` without direct evidence.

- [ ] **Step 8: Commit the estimand/SAP foundation**

```bash
git add docs/analysis/conceptual_model.md docs/analysis/statistical_analysis_plan.md config/analysis.yml docs/analysis/decision_log.md
git commit -m "research: freeze estimands and conceptual model"
```

---

## Task 8: Freeze Spatial and Model Decision Gates

**Files:**
- Modify: `docs/analysis/statistical_analysis_plan.md`
- Modify: `config/analysis.yml`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: explicit estimands and official community-area/tract geometry.
- Produces: deterministic baseline, diagnostic, escalation, and withholding rules.

- [ ] **Step 1: Define spatial weights before outcome modeling**

Use first-order queen contiguity for community areas and tracts, row-standardized, with island handling documented. Run rook-contiguity and distance-band weights as sensitivity analyses. Do not choose weights by the strongest disease-outcome association.

- [ ] **Step 2: Define the baseline primary model**

Fit an unweighted community-area ordinary least squares model with HC3 robust standard errors because the estimand gives each community area equal policy weight and outcome precision is unavailable. Report unadjusted and adjusted exposure estimates. EHR denominator weighting is a sensitivity analysis, not primary, because it changes the target toward high-capture areas.

- [ ] **Step 3: Test residual spatial dependence**

Calculate global Moran’s I on adjusted-model residuals using 9999 conditional permutations. Record I, permutation P value, residual map, and sensitivity across fixed weight matrices. Do not use local clusters to select covariates or exclude areas.

- [ ] **Step 4: Apply a prespecified spatial escalation gate**

If residual absolute Moran’s I is at least 0.10 and permutation `P < .05`, fit a spatial-error model with the same covariates and weights. Do not use a spatial lag of life expectancy as primary because its coefficient has a different and potentially causal-spillover interpretation. If the spatial-error estimate changes direction or differs by more than 20% from OLS on the IQR scale, present the spatial model as primary and OLS as sensitivity; otherwise retain OLS primary and show the spatial estimate as robustness. Report both regardless of convenience.

- [ ] **Step 5: Predefine influence and fit diagnostics**

Flag, but do not automatically delete, areas with Cook’s distance above `4/n`, leverage above `2p/n`, or absolute studentized residual above 3. Primary results retain all eligible areas. Leave-one-area-out and leave-one-region-cluster-out analyses are sensitivities; any sign change or greater-than-30% estimate change marks the finding fragile.

- [ ] **Step 6: Define tract spatial analyses as descriptive**

Report global Moran’s I for reliability-qualified EHR and PLACES measures. Local Moran/Getis-Ord results require at least 9999 permutations, Benjamini-Hochberg false-discovery-rate control within disease-year, and explicit `high-high`, `low-low`, `high-low`, `low-high`, `not significant`, `suppressed`, and `unreliable` labels. These are exploratory patterns, not confirmatory hotspots for intervention.

- [ ] **Step 7: Define withholding rules**

Withhold a model if fewer than 70 community areas are complete, any hard-gate candidate condition no longer meets Gate S5, outcome variance is degenerate, model matrix is rank deficient, influential-area sensitivity changes the scientific conclusion, or spatial dependence remains materially unexplained. Publish the reason for withholding.

- [ ] **Step 8: Commit spatial/model gates**

```bash
git add docs/analysis/statistical_analysis_plan.md config/analysis.yml docs/analysis/decision_log.md
git commit -m "research: freeze spatial model decision gates"
```

---

## Task 9: Freeze Concordance, Discordance, and Temporal Analyses

**Files:**
- Modify: `docs/analysis/statistical_analysis_plan.md`
- Modify: `config/analysis.yml`
- Create: `docs/analysis/concordance_discordance_protocol.md`

**Interfaces:**
- Consumes: EHR measures, PLACES 2025, Healthy Chicago Survey topics, geography/period alignment.
- Produces: interpretable comparison categories and temporal-disruption analyses.

- [ ] **Step 1: Match comparator constructs explicitly**

- Hypertension: EHR-diagnosed proportion vs crude adult PLACES hypertension and Healthy Chicago Survey self-reported clinician diagnosis.
- Diabetes: EHR diagnosed diabetes without complication vs crude adult PLACES diagnosed diabetes and Healthy Chicago Survey diabetes excluding prediabetes/gestational-only definitions.
- COPD: EHR diagnosis vs crude adult PLACES/Chicago Health Atlas ever-told COPD, emphysema, or chronic bronchitis.

Keep source, universe, diagnosis definition, crude/adjusted status, period, and geography in every output.

- [ ] **Step 2: Define comparable periods**

Use the closest verified public period, not the API release year alone. Document that PLACES release/model periods can lag. Community-area HCS rolling periods and annual COPD/PLACES periods are paired to EHR 2022-2024 using overlap tables; exact-match and nearest-period analyses are separate.

- [ ] **Step 3: Define continuous discordance**

Regress within-Chicago EHR ranks on public-measure ranks using predictor/comparator data only. Flag an area as `large positive residual` or `large negative residual` when the absolute externally studentized residual is at least 2 and both measures pass reliability rules. Do not label direction as under/overdiagnosis.

- [ ] **Step 4: Define policy-readable rank categories**

Use within-source quartiles:

| Category | Rule |
|---|---|
| Concordant high | Both sources at or above the 75th percentile |
| Concordant low | Both sources at or below the 25th percentile |
| EHR-high/public-not-high | EHR at or above 75th and public below 50th |
| Public-high/EHR-not-high | Public at or above 75th and EHR below 50th |
| Intermediate | All other usable pairs |

Report sensitivity to terciles and continuous residuals. Percentiles are city-relative, not clinical thresholds.

- [ ] **Step 5: Freeze temporal stability analysis**

For each condition report annual coverage, median/IQR, area ranks, Spearman rank correlation, and within-area change. Use 2019 as baseline; show 2020 and 2021 separately; show 2022-2024 individually plus pooled. Avoid interrupted-time-series or pandemic-effect language with only six annual points and concurrent system/care changes.

- [ ] **Step 6: Define temporal-disruption flags**

Flag area-condition series with a 2020 or 2021 change exceeding both 10 percentage points and 2 times the condition’s median absolute year-to-year change, provided denominator/capture is stable. Treat the flag as a data/care disruption diagnostic, not disease incidence change.

- [ ] **Step 7: Commit the comparison protocol**

```bash
git add docs/analysis/statistical_analysis_plan.md config/analysis.yml docs/analysis/concordance_discordance_protocol.md
git commit -m "research: freeze concordance and temporal protocols"
```

---

## Task 10: Freeze Missingness, Robustness, Multiplicity, and Negative-Control Decisions

**Files:**
- Modify: `docs/analysis/statistical_analysis_plan.md`
- Modify: `config/analysis.yml`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: semantic states, primary estimands, and model families.
- Produces: exact sensitivity families and interpretive downgrade rules.

- [ ] **Step 1: Freeze missingness handling**

Do not impute suppressed or ambiguous EHR disease numerators. Primary analysis is complete-area analysis after semantic/reliability rules. If any covariate has at most 5% missingness, use complete cases and report it; if greater than 5% and at most 20%, use multiple imputation only when the missing-at-random rationale and imputation variables are prespecified; if greater than 20%, replace the covariate with a justified domain alternative or withhold the adjusted model. Never impute life expectancy across community areas for primary analysis.

- [ ] **Step 2: Freeze denominator/coverage sensitivities**

Repeat models using: source reliability only; high-precision tier only; coverage ratio at least 0.25, 0.50, and 0.75 where interpretable; EHR-denominator weighted estimates; exclusion of coverage ratios above 1 pending semantic resolution; and direct community-area estimates only. Thresholds are reliability/representation diagnostics, not optimized cut points.

- [ ] **Step 3: Freeze period sensitivities**

Repeat community-area estimates for 2022, 2023, and 2024 separately; 2019 baseline; 2022-2023 excluding the most recent year; and public-outcome overlap alternatives documented in Task 5. A result is temporally fragile if direction changes or IQR-scaled magnitude changes by more than 30% across defensible contemporary windows.

- [ ] **Step 4: Freeze geography sensitivities**

For tract concordance compare stable-GEOID primary results with official population-weighted crosswalk results. For community areas compare direct export with tract-rollup only as a diagnostic. Test queen, rook, and fixed-distance spatial weights. Do not use a geography choice selected after viewing the desired association.

- [ ] **Step 5: Freeze primary multiplicity**

Treat the joint cardiometabolic-life-expectancy contrast and COPD-life-expectancy contrast as 2 primary case-study estimands. Report two-sided 97.5% Bonferroni-compatible confidence intervals for simultaneous primary inference and nominal 95% intervals for estimation context. Hypertension- and diabetes-specific conditional estimates are prespecified secondary estimates with 95% intervals and no binary confirmatory claim.

- [ ] **Step 6: Freeze supportive/exploratory multiplicity**

Cause-specific mortality, annual-period, subgroup, local-cluster, and alternative-weight analyses are supportive or exploratory. Apply Benjamini-Hochberg FDR within each explicitly named family when P values are used; always report family membership, number of tests, raw estimate/CI, and adjusted status. No isolated nominal P value upgrades a conclusion.

- [ ] **Step 7: Make the negative-control decision explicitly**

Before outcome fitting, review the conceptual model and evidence matrix for a negative-control exposure/outcome satisfying: shared measurement/selection structure, no plausible pathway, comparable geography/period, and adequate reliability. If none satisfies all four—as expected for correlated ecological chronic-disease measures—record `not used: no valid negative control` and do not relabel temporal leads, random permutations, or unrelated convenience variables as negative controls. Spatial permutations remain calibration diagnostics only.

- [ ] **Step 8: Define robustness interpretation**

Classify a primary result as `robust`, `qualified`, or `fragile` using direction, magnitude-change thresholds, spatial escalation, influence, coverage, period, and missingness sensitivities. Null results remain reportable. A fragile result cannot anchor the title, Key Points Meaning, or translation demonstration.

- [ ] **Step 9: Commit the robustness batch**

```bash
git add docs/analysis/statistical_analysis_plan.md config/analysis.yml docs/analysis/decision_log.md
git commit -m "research: freeze robustness and multiplicity rules"
```

**Gate S6:** The complete SAP, model shells, sensitivity families, multiplicity rule, and negative-control decision are signed before any confirmatory outcome model runs.

---

## Task 11: Bound the FQHC/CBO Planning Demonstration

**Files:**
- Create: `docs/translation/fqhc_cbo_planning_demonstration.md`
- Create: `docs/manuscript/claim_language_lexicon.md`
- Modify: `docs/analysis/decision_log.md`

**Interfaces:**
- Consumes: reliability-qualified patterns, HRSA health-center site data, evidence matrix.
- Produces: disclosure-safe questions and prohibited operational claims.

- [ ] **Step 1: Define the unit of demonstration**

Overlay public HRSA FQHC/look-alike service-delivery locations with reliability-qualified area patterns. A point indicates a listed service site, not capacity, catchment, quality, utilization, accessibility, or organizational endorsement. Do not infer that the nearest site serves the mapped area.

- [ ] **Step 2: Predefine allowed planning questions**

Examples may ask whether organizations want to examine local screening/diagnosis workflows, compare their own patient panel with the area signal, investigate transportation/access barriers, review smoking-cessation or cardiometabolic prevention partnerships, or seek community interpretation of discordant measures. Phrase every item as a question or hypothesis requiring local validation.

- [ ] **Step 3: Prohibit unsupported claims**

Do not state that a map identifies unmet need, proves underdiagnosis, identifies an intervention target, optimizes resources, improves equity, predicts outcomes, or recommends opening/closing services. Do not rank communities as deficient. Do not publish small cells or site-sensitive protected information.

- [ ] **Step 4: Add stigma and false-positive review**

For each demonstration output document who may be harmed by misclassification, how suppression/coverage is visible, whether labels imply blame, whether neighborhood composition is biologized, and what local knowledge is required. Withhold examples that cannot be interpreted without stigmatizing language.

- [ ] **Step 5: Define the implementation-evidence boundary**

State that actual resource allocation, adoption, care processes, and outcomes require a future implementation study with stakeholder participation, process measures, comparison strategy, and equity outcomes. Canfell et al.’s evidence gap supports this restraint.

- [ ] **Step 6: Commit translation boundaries**

```bash
git add docs/translation/fqhc_cbo_planning_demonstration.md docs/manuscript/claim_language_lexicon.md docs/analysis/decision_log.md
git commit -m "docs: bound the local planning demonstration"
```

**Gate S8:** FQHC/CBO material is a planning demonstration and passes privacy, stigma, ecological-inference, and unsupported-impact review.

---

## Task 12: Freeze Manuscript Tables, Figures, and JAMA Style Shells

**Files:**
- Create: `docs/manuscript/table_figure_shells.md`
- Create: `docs/methods/visual_style.md`
- Modify: `docs/manuscript/submission_checklist.md`

**Interfaces:**
- Consumes: estimands, reporting rules, and translation boundaries.
- Produces: output shells fixed before confirmatory results.

- [ ] **Step 1: Reserve the 5 main display slots**

Use this default allocation, changing it only before results or through a logged deviation:

1. **Table 1:** CAPriCORN resource, adult denominator, coverage, suppression, reliability, and representativeness by period/geography.
2. **Figure 1:** study/data flow and reliability-qualified Chicago coverage/resource map; no outcome results.
3. **Figure 2:** cardiometabolic hypertension/diabetes joint and separate spatial patterns plus public comparator concordance.
4. **Figure 3:** COPD spatial pattern plus public comparator concordance.
5. **Table 2:** unadjusted/adjusted primary life-expectancy estimates, spatial diagnostic/model result, simultaneous CI, and robustness classification for both case studies.

Do not add a sixth main display. Move aligned mortality, annual disruption, model diagnostics, detailed scorecards, crosswalks, missingness, and FQHC/CBO demonstration to the supplement.

- [ ] **Step 2: Define supplement shells**

Include source/variable lineage; phenotype/denominator definitions; RECORD/STROBE/STROBE-Equity/SAGER crosswalk; candidate scorecard; missingness/suppression; geography vintage/crosswalk; annual trends; public comparator metrics; spatial diagnostics; cause-specific mortality; sensitivity analyses; and translation caveats.

- [ ] **Step 3: Freeze table rules**

Use editable Word tables and a structured Excel supplement; Great Tables is the review-rendering layer, not an image-only submission. Show `No. (%)` with numerator/denominator where appropriate, estimates with CI, units, exact denominators, and explicit `suppressed`, `unreliable`, `not available`, and `not applicable` states. Define every abbreviation and population.

- [ ] **Step 4: Freeze figure rules**

Use separate editable vector files, at most 4 panels unless justified, labeled units/axes, uncertainty for estimates, perceptually ordered/color-vision-safe maps, grayscale-distinguishable categories, and visually distinct suppression/missingness/reliability. Do not use pie charts, 3D charts, or choropleths that render missing/suppressed as zero.

- [ ] **Step 5: Freeze manuscript ordering and JAMA language**

Draft Results from frozen outputs first, then Methods, Discussion, Key Points, Abstract, and title. Match Methods and Results order. Keep main text within 3000 words and 50-75 verified references. Title is concise, nondeclarative, no direction, no question, at most 100 characters, and omits study design.

- [ ] **Step 6: Commit output shells**

```bash
git add docs/manuscript/table_figure_shells.md docs/methods/visual_style.md docs/manuscript/submission_checklist.md
git commit -m "docs: freeze JAMA manuscript output shells"
```

---

## Task 13: Establish Deviation, Reproducibility, Citation, and Freeze Gates

**Files:**
- Create: `docs/analysis/deviation_log.md`
- Create: `config/study_manifest.yml`
- Modify: `docs/analysis/decision_log.md`
- Modify: `docs/manuscript/submission_checklist.md`

**Interfaces:**
- Consumes: all approved planning artifacts and frozen source registries.
- Produces: a complete chain from source and decision to manuscript claim.

- [ ] **Step 1: Define decision-log fields**

Every decision records `decision_id`, date/time/time zone, phase/gate, question, alternatives, evidence, decision, rationale, owner/approver, files affected, outcome-blind status, and superseded decision if any.

- [ ] **Step 2: Define deviation-log fields**

Every post-freeze departure records `deviation_id`, original rule, observed issue, date discovered, whether outcomes were visible, proposed change, scientific reason, alternatives, analyses affected, bias direction, interpretation consequence, approval, and version/commit. “Improves significance” is never a scientific reason.

- [ ] **Step 3: Define the study manifest**

Record source snapshot/checksum IDs; EHR data cut; public releases; literature snapshot; case-study decision; outcome-unblinding time; SAP version; estimands; eligibility/suppression/reliability; geography/vintage/crosswalk; periods; covariates; model/weights; multiplicity; sensitivities; software/lockfile; notebook versions; output hashes; ethics/IRB; data sharing; authorship/funding; and AI disclosure inputs.

- [ ] **Step 4: Define citation lineage**

Every external variable links to publisher, exact dataset/release/topic/table, definition, universe, period, geography, access date, original URL/DOI, platform access if any, and transformation. Every manuscript number links to a frozen table/model artifact. Every prose scientific claim links to an evidence-matrix claim ID.

- [ ] **Step 5: Define Metopio branches without exposing credentials**

The frozen public catalog is sufficient to document limited unauthenticated access: 19 topics, 1 layer, and 1 geography, with no public hypertension/diabetes/COPD topic visible. If `METOPIO_API_TOKEN` is absent, record `authenticated catalog not run` and proceed with frozen authoritative original sources. If present, use only the bundled `scripts/metopio_api.py snapshot` client, bounded page/item budgets, a new immutable directory, and redacted ledgers. Full catalogs must page to `next: null`; ambiguous topic/dataset/source/unit/universe/vintage candidates block selection. Authenticated Metopio is an enhancement, not permission to replace authoritative frozen sources or redistribute curated copies.

- [ ] **Step 6: Define freeze gates**

| Gate | Required evidence | Failure consequence |
|---|---|---|
| S1 Literature protocol | Complete paged PubMed manifests and screening schema | No novelty claims |
| S2 Evidence | Verified full-text claims and conflicts/gaps | Unsupported claim removed |
| S3 Journal/reporting | Official dated rules and checklist crosswalk | No manuscript adapter |
| S4 EHR semantics | Resolved numerator/denominator/suppression/reliability | No candidate scoring/modeling |
| S5 Selection | Outcome-blinded signed scorecard | No outcome unblinding |
| S6 SAP | Signed estimands/models/sensitivities/multiplicity | No confirmatory model run |
| S7 Analysis validation | Reproducible results, diagnostics, independent numerical review | No result freeze |
| S8 Translation | Privacy/stigma/claim-boundary approval | No FQHC/CBO display |
| S9 Manuscript | Traceability, checklists, JAMA audit, clean rebuild | No submission-ready claim |

- [ ] **Step 7: Define clean-rebuild requirements for later implementation**

After code exists, rebuild from immutable sources in a clean environment with the lockfile; run tests, source verification, marimo checks, deterministic notebook script mode, table/figure audits, manuscript traceability, and hash comparison. Network access is forbidden for the offline rebuild. The official marimo skills must be read before notebook work begins.

- [ ] **Step 8: Commit governance artifacts**

```bash
git add docs/analysis/deviation_log.md config/study_manifest.yml docs/analysis/decision_log.md docs/manuscript/submission_checklist.md
git commit -m "docs: establish scientific freeze and deviation governance"
```

---

## Task 14: Conduct Final Scientific and Manuscript Planning Review

**Files:**
- Review: every artifact listed in this plan
- Create: `docs/reviews/scientific_planning_gate_review.md`

**Interfaces:**
- Consumes: completed Tasks 1-13.
- Produces: explicit authorization or blocking findings for implementation.

- [ ] **Step 1: Run requirement coverage review**

Check literature protocol/evidence matrix; current JAMA rules; RECORD/STROBE/STROBE-Equity/SAGER; EHR semantics; blinded scorecard; estimands/noncausal language; geography/vintage; outcome alignment; spatial gates; concordance/discordance; temporal disruption; missingness/suppression/coverage; robustness/multiplicity/negative controls; translation boundaries; displays/JAMA style; deviation/reproducibility/citation/freeze gates.

- [ ] **Step 2: Run scientific contradiction review**

Search for population prevalence labels applied to EHR measures, tract-level life-expectancy claims, causal verbs, community-area results derived from tracts despite direct exports, PLACES treated as gold standard, release year treated as observation year, suppressed zeros, race treated biologically, unsupported intervention claims, or outcome-informed selection.

- [ ] **Step 3: Run placeholder and ambiguity review**

Search tracked planning artifacts for `TBD`, `TODO`, `later`, `appropriate`, `as needed`, `etc.`, unresolved alternatives, missing owners, and unversioned external rules. Replace each with a decision, explicit gate, or named unresolved blocker.

- [ ] **Step 4: Run traceability review**

Sample every primary estimand, planned table/figure, dataset, and key manuscript claim. Confirm a path from source snapshot through definition/decision/SAP to final artifact and citation.

- [ ] **Step 5: Record pass/fail by gate**

`scientific_planning_gate_review.md` lists evidence paths, reviewer, date, pass/fail, open blockers, and authorized next phase. A partial pass cannot be summarized as complete.

- [ ] **Step 6: Commit the gate review**

```bash
git add docs/reviews/scientific_planning_gate_review.md
git commit -m "review: verify scientific manuscript planning gates"
```

**Final planning condition:** Implementation may start only for artifacts whose prerequisite gates pass. Case-study outcome analysis remains blocked until S4, S5, and S6 all pass in order.

---

## Plan Self-Review Checklist

- [ ] Every requirement in the approved design maps to a task and gate.
- [ ] Every exact current JAMA claim comes from the official JAMA Health Forum instructions.
- [ ] Tavily quota failure and Ref Context zero result are recorded without overstating verification.
- [ ] PubMed searches are fully paged and updateable; Paperclip full text supports material claims.
- [ ] Metopio credentials can never enter a prompt, command argument, URL, file, log, notebook, or chat.
- [ ] Community-area models use direct community-area EHR data.
- [ ] No tract-level life-expectancy outcome is invented or imported without a new source gate.
- [ ] The case-study score excludes all outcome information and fixes substitutions before unblinding.
- [ ] Estimands identify population, exposure contrast, outcome, geography, period, and adjustment.
- [ ] Spatial escalation, influence, missingness, multiplicity, and robustness rules cannot be selected for favorable results.
- [ ] Negative controls are used only when scientifically valid; absence is documented.
- [ ] Discordance never implies underdiagnosis, error, or unmet need by itself.
- [ ] FQHC/CBO claims remain questions and planning hypotheses unless implementation outcomes are evaluated.
- [ ] Main displays fit the 5-item JAMA limit and preserve reliability/suppression/uncertainty.
- [ ] Every decision, deviation, variable, number, and scientific claim has lineage.
- [ ] No analysis/pipeline code is created while executing the planning-only assignment that produced this plan.
