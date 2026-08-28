# Agentic JAMA Health Forum Manuscript Blueprint Design

**Date:** 2026-07-14  
**Status:** Approved design pending final written-spec review  
**Target:** JAMA Health Forum Original Investigation  
**Primary resource:** ChicagoHealthMap.com / CAPriCORN  
**Style reference:** Rojas et al, “A common longitudinal intensive care unit data
format (CLIF) for critical illness research,” *Intensive Care Medicine* (2025),
doi:10.1007/s00134-025-07848-7.

## 1. Purpose

Create a reproducible, agent-assisted manuscript workflow that presents Chicago Health
Map as an urban-health informatics resource and demonstrates its scientific value
through two outcome-blinded case studies. The manuscript will learn from the supplied
CLIF paper's problem-solution-two-demonstration architecture and the author's direct,
technical voice without copying sentences, distinctive phrases, or journal-specific
formatting.

The finished paper must be a JAMA Health Forum Original Investigation, not a platform
advertisement. Every result must originate in the frozen analytic dataset and every
material non-result claim must have verified evidence. Human authors retain scientific,
authorship, disclosure, and submission responsibility.

## 2. Governing decisions

1. **Article type:** Original Investigation. The work contains new empirical analyses,
   whereas JAMA Health Forum describes a Special Communication as an authoritative
   synthesis that does not present new data or analyses.
2. **Manuscript strategy:** integrated platform plus mirrored case studies. The platform
   is the central contribution; the cases provide contrasting empirical demonstrations.
3. **Primary data authority:** ChicagoHealthMap.com/CAPriCORN exports are the clinical
   and spatial base. Public sources are contextual, validation, covariate, or planning
   layers and cannot replace or relabel the Chicago Health Map outcome, denominator,
   geography, phenotype, or suppression semantics.
4. **Provisional cases:** the anticipated cases are cardiometabolic hypertension and
   diabetes, jointly and separately, and respiratory COPD. They remain provisional until
   the outcome-blinded S5 gate. A candidate cannot be selected, retained, or replaced
   because of an outcome association, P value, visual appeal, or narrative convenience.
5. **Scientific authority:** the signed SAP, source-owner semantics, case-selection
   record, frozen study manifest, and independently reproduced outputs outrank prose.
6. **No premature drafting:** factual manuscript shells may be prepared only when their
   inputs are authoritative. Results prose is prohibited until the analytic outputs pass
   S7 and are frozen.

## 3. Transferable style from the reference paper

The design adopts these structural habits:

- frame a bounded research workflow problem before introducing the resource;
- acknowledge existing infrastructure before specifying the unresolved gap;
- describe governance, data structure, and execution in operational layers;
- pair general technical rules with concrete examples;
- announce the manuscript sequence explicitly;
- use two deliberately contrasting demonstrations rather than two repetitions;
- mirror the order of Methods, Results, and Discussion;
- interpret findings using the sequence **finding -> boundary -> implication**;
- use declarative topic sentences and first-person plural for investigator actions;
- give every main display one argument-level function; and
- separate unavailable patient-level data from shareable schema, code, and aggregate
  evidence.

The design rejects verbatim imitation, repeated promotional slogans, expansive future
applications unsupported by results, and the reference paper's longer platform
exposition. JAMA's main-text limit requires greater compression.

## 4. Manuscript architecture

### 4.1 Front matter

- Nondeclarative research title no longer than 100 characters including spaces.
- Key Points no longer than 100 words using Question, Findings, and Meaning.
- Structured abstract using Importance, Objective, Design, Setting, Participants,
  Exposures, Main Outcomes and Measures, Results, and Conclusions and Relevance.
- Abstract and Key Points are written only after the main text and all numbers are frozen.

### 4.2 Introduction: 250-300 words

1. Opportunity: neighborhood-scale multisystem EHR data for local health assessment.
2. Problem: capture, representativeness, suppression, and comparator nonequivalence.
3. Gap: limited reproducible evaluation of whether such data support reliable
   small-area assessment and health-policy inquiry.
4. Resource and objective: Chicago Health Map, its reliability framework, and the two
   prespecified demonstrations.

### 4.3 Methods: 850-950 words

1. Study design, setting, dates, ethics, and consent or waiver.
2. Chicago Health Map/CAPriCORN source and eligible population.
3. Deduplication, phenotype, time, residence, geography, numerator, denominator,
   suppression, and reliability semantics.
4. Public-source harmonization, geography, provenance, and access restrictions.
5. Outcome-blinded case-study selection.
6. Shared analytic population, outcomes, covariates, missingness, and spatial methods.
7. Mirrored Case Study 1 and Case Study 2 methods.
8. Multiplicity, sensitivity analyses, software, reproducibility, and reporting guidance.

### 4.4 Results: 850-950 words

1. Resource scale and analytic eligibility.
2. Coverage, reliability, missingness, and representativeness.
3. Case Study 1 in the approved mirrored sequence.
4. Case Study 2 in the same sequence and compression.
5. No policy interpretation beyond the prespecified results.

### 4.5 Discussion, including Limitations: 850-950 words

1. Principal platform finding.
2. Case Study 1 interpretation.
3. Case Study 2 interpretation.
4. Joint lesson from the contrasting cases.
5. Conditional FQHC/CBO planning relevance.
6. Limitations ordered by threat to inference.
7. Brief conclusion containing no claim absent from Results.

The word allocation retains at least 100 words of reserve for compliance edits.

### 4.6 Main displays

The manuscript uses no more than five combined main tables and figures:

1. **Table 1:** resource, population, coverage, and reliability profile.
2. **Figure 1:** study flow plus coverage and reliability map or panels.
3. **Figure 2:** Case Study 1 patterns and public-comparator concordance.
4. **Figure 3:** Case Study 2 patterns and public-comparator concordance.
5. **Table 2:** primary unadjusted and adjusted estimates, uncertainty, spatial model
   decision, and robustness classification for both cases.

Detailed schemas, missingness, scorecards, annual analyses, aligned mortality,
diagnostics, crosswalks, and FQHC/CBO planning demonstrations belong in the supplement.
The same result is not duplicated in a main table and figure.

## 5. Mirrored case-study contract

Each selected case uses this exact conceptual sequence:

1. **Why this case:** the distinct scientific and informatics test, without results.
2. **Prespecified estimand:** exposure, outcome, geography, period, population, model,
   uncertainty interval, and multiplicity status.
3. **Eligibility and data quality:** analyzable areas and periods, suppression,
   reliability, missingness, and exclusions.
4. **Pattern and comparator:** Chicago Health Map diagnosed proportion followed by the
   source-qualified public comparator. Discordance is information, not proof that one
   source is wrong.
5. **Primary estimate:** eligible sample, unadjusted and adjusted estimate, confidence
   interval, spatial diagnostic and model decision, and robustness classification.
6. **Supportive analyses:** explicitly secondary or exploratory and normally in the
   supplement.
7. **Interpretive boundary:** case-specific selection, measurement, ecological,
   temporal, and comparator limitations.
8. **Platform lesson:** what the case establishes about reliability, triangulation, or
   transfer across phenotypes, never an intervention effect.

Case 1 is expected to test the joint cardiometabolic contrast, with conditional
hypertension and diabetes estimates as secondary. Case 2 is expected to test transfer to
a respiratory phenotype with different suppression and comparator behavior. The
structure remains valid if S5 promotes a different defensible second candidate.

## 6. Agent roles and boundaries

| Role | Responsibility | Prohibited action |
|---|---|---|
| Orchestrator/editor | Own outline, assignments, budgets, integration, issue log, and gates | Invent results or silently resolve scientific conflicts |
| Artifact/lineage agent | Map every number and variable to frozen sources, transformations, and outputs | Interpret findings or alter frozen outputs |
| Methods/reporting agent | Draft from SAP and maintain reporting/ethics/data-sharing crosswalks | Back-fit methods to observed results |
| Results agent | Convert frozen outputs into concise factual statements and maintain the number ledger | Add literature interpretation or causal wording |
| Case-study agents | Populate the identical case templates and identify case-specific limits | Change estimands, outcomes, candidates, or multiplicity |
| Evidence/claims agent | Verify sources and maintain claim support, conflicts, gaps, and language bounds | Use abstracts alone for material claims or generate references from memory |
| Discussion/policy agent | Interpret within evidence bounds and synthesize the two cases | Claim implementation benefit, need, optimal allocation, access, or outcomes |
| Statistical QA agent | Independently verify estimates, denominators, intervals, diagnostics, and reconciliation | Strengthen narrative by changing scientific content |
| JAMA/style QA agent | Enforce live journal rules, reporting, files, disclosures, and voice | Change scientific content without a logged query |
| Human accountable authors | Approve science, authorship, access statement, disclosures, AI use, and submission | Delegate accountability to an agent |

## 7. Stage gates

| Gate | Required inputs | Acceptance output |
|---|---|---|
| M0 authority freeze | Signed authority hierarchy, target article type, current journal audit | Dated requirements record; unresolved scope blocks drafting |
| M1 artifact freeze | Passed S4-S7, analytic dataset, outputs, hashes, study manifest | Authorized result set; every primary number has an artifact ID |
| M2 evidence freeze | Evidence matrix, Paperclip verification, novelty update search | Claim ledger; unsupported claims removed or labeled gaps |
| M3 section shells | Frozen outline, budgets, case template, disclosure inputs | Matching Methods/Results shells without rhetorical embellishment |
| M4 integration | Section shells, number ledger, claim ledger, deviation log | One coherent draft without duplicate or inconsistent claims |
| M5 independent QA | Draft, outputs, code, manifest, checklists | Numerical reproduction, traceability, privacy/equity/ecological review, offline rebuild |
| M6 JAMA compliance | Live instruction recheck and complete disclosure inputs | Compliant title, abstract, Key Points, displays, files, statements, and forms |
| M7 author sign-off | Final package and closed issue log | Named human approvals and no unresolved scientific decision |

M0-M7 are manuscript gates. They do not replace scientific Gates S4-S8; the stricter
applicable gate governs.

## 8. Claim and number ledgers

### 8.1 Claim ledger fields

Each material claim records:

- `claim_id`, section, proposed claim, and claim class;
- evidence role and source or artifact identifier;
- exact supporting location;
- population, geography, measure, and period match;
- support strength, conflict, or gap;
- allowed wording and prohibited inference;
- prespecified, secondary, exploratory, post hoc, or not-applicable status;
- owner and independent verifier/date; and
- final manuscript location.

Result claims require frozen artifacts rather than literature citations. Novelty claims
must be bounded to the frozen searches. A null result is not evidence of equivalence.
References cannot enter the reference manager until identifier, title, author, year, and
support have been independently checked.

### 8.2 Number ledger fields

Every manuscript number records:

- artifact path, artifact identifier, checksum, table/field, and code version;
- population, exclusions, geography, period, measure, unit, and denominator;
- raw precision and approved display rounding;
- confidence interval or uncertainty definition;
- prespecified or exploratory status; and
- all abstract, text, display, and supplement locations.

## 9. Voice and language contract

- Lead each paragraph with its function or claim; one main claim per paragraph.
- Prefer concrete verbs: included, estimated, compared, differed, and was associated.
- Use first-person plural for investigator decisions and actions.
- Use **EHR-diagnosed proportion among observed CAPriCORN adults** when that is the
  verified estimand; do not substitute unqualified prevalence, burden, risk, or rate.
- State estimate, unit, interval, and eligible sample before a P value.
- Use associational language for ecological results.
- Do not anthropomorphize data, models, maps, or neighborhoods.
- Treat comparator discordance as a measurement and interpretation problem, not a
  winner-loser comparison.
- Use planning language conditionally: findings may formulate questions; they do not
  establish need, underdiagnosis, access, capacity, optimal allocation, care improvement,
  or outcomes.
- Avoid novel, first, unique, representative, validated, robust, scalable, comprehensive,
  and actionable unless the ledger defines and supports the term.
- Ban effect, impact, drives, leads to, improves, prevents, and reduces for the study's
  observational ecological results.
- Define abbreviations once and retain only those that materially reduce repetition.
- Do not reproduce distinctive wording from the reference paper.

## 10. Failure behavior

The writing workflow stops when:

- a result lacks a frozen artifact and checksum;
- a claim lacks verified full text or an official primary source;
- Methods and Results differ in population, period, estimand, eligibility, or exclusion;
- S5, S6, or S7 has not passed for case-study results;
- suppression, missingness, and observed zero are not distinguishable;
- diagnosed proportions are relabeled as population prevalence;
- a policy implication exceeds evaluated evidence;
- text, tables, figures, abstract, or supplement disagree;
- a reporting, privacy, stigma, ethics, access, funding, conflict, authorship, or AI
  disclosure is unresolved; or
- a human author has not approved a scientific decision reserved for humans.

Agents record the blocker and required authority. They do not draft around it.

## 11. Verification and acceptance

The final package must pass all of the following:

1. **Journal:** live official instructions rechecked and dated; current main-text,
   abstract, title, reference, display, heading, and file constraints satisfied.
2. **Numbers:** every number traces to a frozen artifact and reconciles across all uses.
3. **Design:** case selection remains outcome-blinded; primary, secondary, exploratory,
   and post hoc labels match the SAP; deviations are logged.
4. **Spatial/ecological:** geography/vintage and diagnostics are correct; no individual or
   causal inference is made.
5. **EHR semantics:** deduplication, phenotype, capture, denominator, suppression,
   reliability, and selection limitations are explicit.
6. **Comparators:** releases, periods, universes, methods, and geographies are retained;
   no comparator is labeled a gold standard.
7. **Equity/demographics:** source, rationale, categories, classification, terminology,
   privacy, and stigma review are complete.
8. **Evidence:** material claims have verified support; conflicts and gaps remain visible;
   novelty is search-bounded; references are independently checked.
9. **Policy:** FQHC/CBO content remains a planning demonstration unless implementation
   outcomes are evaluated.
10. **Reproducibility:** source/output/code/environment hashes exist; offline rebuild and
    independent numerical reproduction pass.
11. **Disclosures:** ethics, consent/waiver, full-data-access responsibility, data/code
    sharing, funding/role, conflicts, contributions, related work, and AI use are complete.
12. **Voice:** paragraphs have one job; unsupported superlatives, copied phrasing,
    repeated slogans, causal overreach, and rhetorical cancellation of limitations are
    absent.

## 12. Current JAMA Health Forum planning contract

The journal requirements were checked against the official JAMA Health Forum
Instructions for Authors on 2026-07-14. The planning contract is:

- Original Investigation with a main text of no more than 3000 words;
- structured abstract of no more than 350 words;
- Key Points using Question, Findings, and Meaning;
- concise, nondeclarative title within 100 characters;
- no more than five combined main tables and figures;
- 50-75 references for the cross-sectional/observational study type, without adding weak
  citations merely to reach the lower planning bound, plus applicable EQUATOR guidance;
- STROBE as the base checklist, with RECORD for routinely collected EHR data and
  STROBE-Equity/SAGER crosswalks as project-selected extensions;
- Data Sharing Statement covering data, dictionary, documentation, and analytic code;
- exact named-author data-access/responsibility statement;
- ethics/IRB and consent/waiver language;
- complete funding, role-of-funder, conflict, contribution, related-work, and prior-
  presentation disclosures; and
- AI-assistance disclosure in the required location, including tool/platform,
  version/extensions, manufacturer, dates, use, and confirmation of human review and
  responsibility. If the interface does not expose a required version detail, the ledger
  records that it was unavailable rather than inferring one.

The official page must be rechecked within 30 days of submission. If a live rule differs
from this planning contract, the official rule controls and the change is logged.

Official sources:

- https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors
- https://jamanetwork.com/journals/jama-health-forum/fullarticle/2850472

## 13. Deliverables

1. Frozen manuscript outline and word/display budget.
2. Study manifest plus claim, number, source, and AI-use ledgers.
3. Two mirrored case-study evidence packets.
4. JAMA compliance and reporting-guideline matrices.
5. Manuscript, structured abstract, Key Points, and supplement.
6. Editable tables and publication-quality vector figures.
7. Data/code sharing, access, ethics, funding, conflict, contribution, and AI statements.
8. Reproducibility report and final submission audit.

The manuscript is complete only when all applicable scientific and manuscript gates pass,
the worktree is clean, the final artifact hashes are recorded, and named human authors
approve the submission package.
