# JAMA Health Forum Style Guide for ChicagoHealthMap

## Scope and Evidence Standard

This is a manuscript-development guide, not a substitute for current JAMA Health Forum instructions. It uses 2 local 2026 Original Investigation exemplars:

- Barsky et al, *Medicaid Expansion and Mortality Among Formerly Incarcerated Individuals*.
- Jiang et al, *Primary Care Cost Sharing in Medicare Advantage*.

The local PDFs, checksums, and metadata are preserved in `sources/literature/jama_health_forum_examples/snapshots/2026-07-14/`; reproducible outputs are in `outputs/manuscript/jama_style_audit/`. The authoritative project limits are in `config/manuscript/jama_health_forum.yml`: 3000 main-text words, a 350-word abstract, 100 title characters, 75 to 100 Key Points words, 50 to 75 references, and no more than 5 combined main tables and figures. Recheck the journal instructions within 30 days of submission.

Read this guide in 3 layers:

1. **Observed in the 2-paper corpus** means the evidence supports a pattern in these exemplars only.
2. **ChicagoHealthMap drafting rule** is a project-specific recommendation grounded in the study design, SAP, and disclosure constraints.
3. **Journal requirement** must be confirmed against the live instructions and submission system.

Do not turn an observed convention into a submission requirement without that final check.

## Audit Findings

### Corpus Shape

Both papers use the main sequence Introduction, Methods, Results, Discussion, Limitations, and Conclusions. Both use multiple descriptive Methods subsections; Results subsectioning varies. Barsky uses 3 main tables and 4 supplemental displays. Jiang uses 1 main figure, 2 main tables, and 3 supplemental displays. This supports a compact main-display strategy with detailed secondary material in the supplement; it does not establish that every JAMA Health Forum article must have exactly 3 main displays.

Both abstracts contain the same functional elements: Importance, Objective, Design/Setting/Participants, Exposure(s), Main Outcomes and Measures, Results, and Conclusions and Relevance. The published PDF renders Design, Setting, and Participants as one combined heading. The project configuration stores those as separate abstract fields, so use the current manuscript template and live journal instructions to decide the final heading rendering.

### Automated Text Metrics

The table below is a **screening description**, not a target and not a claim about all JAMA Health Forum writing. Citation-aware sentence segmentation was checked against rendered pages. Results and Discussion are excluded from this sentence table because displays are interleaved with prose in the PDF text stream and would create false precision. PDF-extracted paragraph boundaries are not used as evidence of paragraph style.

| Article and prose-dominant section | Mean sentence words | Median | Middle 50% | Flesch-Kincaid grade |
| --- | ---: | ---: | ---: | ---: |
| Barsky: Introduction | 20.7 | 18.0 | 16.0-26.3 | 15.6 |
| Barsky: Methods | 26.0 | 23.0 | 16.0-33.0 | 17.5 |
| Barsky: Limitations | 18.6 | 16.0 | 14.5-24.5 | 16.6 |
| Barsky: Conclusions | 21.5 | 21.5 | 19.8-23.3 | 19.1 |
| Jiang: Introduction | 32.0 | 30.0 | 24.5-33.5 | 19.9 |
| Jiang: Methods | 29.7 | 28.0 | 17.0-33.0 | 18.9 |
| Jiang: Limitations | 31.7 | 34.0 | 22.5-36.8 | 20.7 |
| Jiang: Conclusions | 30.7 | 31.0 | 27.0-34.5 | 18.8 |

The defensible conclusion from the sentence length distributions is that the papers use mostly 16- to 34-word sentences, with deliberate shorter sentences amid denser technical ones. They do **not** support imitating long sentences or optimizing to a readability score. Flesch-Kincaid is unstable for medical prose with abbreviations and proper nouns; use it to flag outliers, then edit by meaning and cadence.

Visual review shows paragraphs organized around one argument rather than one fixed length. Many contain 3 to 6 sentences; longer Discussion paragraphs develop one interpretation through several studies. A paragraph should end when its claim changes, not when it reaches a word quota.

### Syntax, Citation, and Claim Discipline

The syntax patterns in the excerpts are recurring rather than mandatory: a concrete subject and claim, an estimate or factual support, then a boundary or comparison. Methods often use investigator action verbs; Results use neutral reporting verbs; Discussion moves from interpretation to prior evidence to bounded implications. The corpus uses association language frequently, especially in observational analyses.

The audit flags passive constructions, nominalizations, hedges, and transition terms only as prompts for human review. They are not errors. For example, passive voice is often clearer for disclosure or eligibility rules, and hedging is required when inference is limited. Citation density is not reported as a numeric metric because PDF reference markers cannot be separated reliably from statistical numbers. Instead, review citation placement manually: cite background claims and comparisons with prior work, not routine analytic actions or every sentence in a results paragraph.

## Writing Style

### Observed Pattern

- Introductions and Discussions carry more conceptual context and can contain long, clause-rich sentences.
- Methods favor named subsections and concrete definitions.
- Results are numerically dense and refer the reader to tables, figures, and supplements rather than reproducing every value.
- Conclusions are brief, qualified, and do not introduce new evidence.

### ChicagoHealthMap Drafting Rules

- Prefer one principal claim per sentence. As a house rule, aim for 18 to 28 words most of the time, mix in shorter sentences, and review any sentence longer than 40 words. A number-heavy Results sentence may be longer when splitting it would separate an estimate from its comparison or CI.
- Use active voice for investigator actions: "We calculated," "We classified," and "We compared." Use passive voice when the actor is irrelevant or disclosure rules are the subject: "Cells were suppressed."
- Use "was associated with," "was higher or lower than," "was spatially aligned with," "was discordant with," and "may inform" for ecological findings.
- Do not use "caused," "drove," "reduced," "improved," "prevented," or "led to" unless the finalized design supports a causal claim.
- Make transitions do analytic work: "In contrast" for a genuine contrast, "However" for a qualifying exception, and "Consistent with" only when measures, populations, and periods are comparable.
- Put the denominator and uncertainty next to the claim they qualify. Do not make the reader infer either from a map legend or a footnote.

A practical paragraph shape is: topic claim, evidence, boundary, then implication. In Discussion, implication should never outrun the boundary.

### Human Scientific Voice

Human writing has judgment and rhythm. It does not sound like every sentence came from the same template.

- Name the actor or object early: "We estimated," "The diagnosed proportion differed," or "Thirty-eight areas met the reliability threshold." Avoid openings such as "It is important to note" and "There is a need to."
- Prefer concrete verbs to noun stacks: "We compared the measures" is clearer than "We conducted a measure-comparison assessment."
- Keep technical terms stable, but do not repeat a full label mechanically in adjacent sentences. After defining the EHR-diagnosed proportion among observed CAPriCORN adults, use a precise short form such as "the EHR-diagnosed proportion" when no ambiguity is possible.
- Vary sentence roles. Follow a dense estimate sentence with a short interpretive boundary. Do not repeat claim-evidence-boundary-implication as a visible four-sentence formula in every paragraph.
- Use emphasis sparingly. Delete "Importantly," "Notably," "Interestingly," and "It should be noted" unless removing the word changes the logic.
- Treat "Taken together," "These findings underscore," "The broader landscape," "a valuable lens," and "may help inform" as warning phrases. Replace them with the actual synthesis, object, or decision.
- Avoid decorative triples and false balance. List 3 items only when the science has 3 items.
- Do not anthropomorphize data: analyses estimate, results show or are consistent with, and data do not "believe," "seek," or "prove."
- Use first-person plural for accountable analytic choices, not to advertise the study. "We prespecified" is useful; "We provide a novel framework" is usually not.

Mechanical version:

> Taken together, these findings underscore the potential utility of ChicagoHealthMap as a valuable lens that may help inform targeted planning conversations.

Human, bounded version:

> The EHR and public measures identified similar patterns in [N] areas, but agreement was lower where CAPriCORN capture was limited. These differences can identify questions for local review; they do not rank community need.

Use bracketed placeholders only during drafting. No placeholder survives the evidence freeze.

### Real Sentences to Model

These short excerpts are craft exemplars, not copy templates. Preserve their function, not their wording.

From Barsky et al:

> People aged 35 years or older had higher ORs than people aged 18 to 34 years, and females had a lower OR than males.

Why it works: the comparison is grammatical and parallel; both groups and both directions appear in one controlled sentence. ChicagoHealthMap pattern: `[Measure] was higher in [group or area type] than in [reference], whereas [second measure] was lower.` Add exact estimates and CIs where this is a primary result.

From Jiang et al:

> Cost sharing can deter utilization of high-value services such as primary care.

> Several findings from this analysis warrant further discussion.

Why they work: the first is a plain topic sentence with a concrete subject and verb. The second is a short pivot that resets the reader before a numbered interpretive sequence. Use such pivots only when the next paragraph genuinely changes the level of analysis.

Additional ChicagoHealthMap sentence patterns:

- **Methods:** `We classified an area-year as reliability-qualified when [prespecified rule].`
- **Results:** `Among [N] eligible areas, [n] ([%]) met the reliability threshold; [n] were withheld because [reason].`
- **Estimate:** `[Exposure or measure] was associated with [outcome] ([estimate]; [CI level] CI, [lower] to [upper]).`
- **Boundary:** `This association is ecological and does not describe individual risk.`
- **Discussion:** `Agreement was lower in areas with limited CAPriCORN capture, suggesting that ascertainment contributed to the observed discordance.`
- **Conclusion:** `Reliability-qualified EHR measures can identify questions for local review, but they do not estimate population prevalence or establish service need.`

Do not use the patterns in consecutive sentences. They are scaffolds for evidence placement, not a house voice.

## Title

The title must be concise, specific, informative, and no longer than 100 characters including spaces. For this observational report, do not use a question, a declarative result, the direction of the finding, or the study design in the title or subtitle. Name the subject and setting rather than the conclusion. Avoid abbreviations.

A suitable pattern is `[Measure or phenomenon] and [policy-relevant outcome] in [setting]`. Verify the final title against the live instructions because title rules differ for trials and meta-analyses.

## Introduction

### Observed Pattern

The exemplar Introductions move from a consequential public-health or policy problem, through what is already known, to a specific evidence gap, then end by naming the design and objective. They cite heavily because the section establishes why the question matters and where prior evidence is incomplete.

### ChicagoHealthMap Drafting Rules

1. Establish a Chicago public-health or planning problem in concrete terms.
2. Explain the decision or measurement gap without implying that existing public surveillance is inadequate or wrong.
3. State what a multisystem EHR measure adds: an observed-care, diagnosis-based lens with explicit coverage and reliability limits.
4. Name the gap: whether reliability-qualified small-area EHR patterns align with independent public-health measures and life-expectancy inequities.
5. End with one objective sentence that names design, population, geography, measures, and analytic aim.

Avoid "first," "unique," "comprehensive," "representative," and "validated" unless the evidence file supports each word. Do not promise that a map will identify need, underdiagnosis, access barriers, or optimal resource allocation.

Objective template:

> In this repeated-period ecological study, we evaluated whether EHR-diagnosed proportions among observed CAPriCORN adults identified reliability-qualified small-area patterns in hypertension, diabetes, and COPD that were associated with independent public-health measures and life-expectancy inequities in Chicago.

Before use, replace any placeholder scope with the final SAP and frozen analytic population.

## Methods

### Observed Pattern

Both exemplar Methods sections name the design, data source, population, measures, and statistical analysis in explicit subsections. In Barsky, the IRB determination and STROBE statement appear in the data-source subsection; they are not presented as a universal end-of-Methods ordering rule. Both papers give the reader the information needed to understand the primary analysis, while secondary detail is carried by tables and supplements.

### ChicagoHealthMap Drafting Rules

Use descriptive subsections in this order unless the final analysis makes another order clearer:

1. **Study Design and Data Sources:** repeated-period ecological design; CAPriCORN/ChicagoHealthMap and public comparator sources; dates of data analysis.
2. **Study Population and Geography:** observed CAPriCORN adults, years, geographic unit and vintage, inclusion rules, and analytic universe.
3. **Measures:** define the EHR numerator, denominator, phenotype, comparator, and life-expectancy construct.
4. **Reliability, Suppression, and Missingness:** thresholds, coverage, withheld outputs, missing public measures, and the meaning of a blank or suppressed geography.
5. **Statistical Analysis:** estimands, prespecified versus exploratory analyses, models, spatial diagnostics, CIs, multiplicity, sensitivity analyses, software, and analysis dates.
6. **Ethics and Reporting:** IRB or waiver determination, privacy/disclosure safeguards, and STROBE/RECORD when applicable.

State the principal denominator exactly at first use: **EHR-diagnosed proportion among observed CAPriCORN adults**. This is not population prevalence. Explain the analytic decisions that change interpretation in the main text. Put field-level schemas, query logs, source manifests, full missingness matrices, and extended diagnostics in the supplement or repository, while citing them precisely from the main text.

At the end of Methods, state the tests, prespecified CI or significance levels, whether tests were 1- or 2-sided, software versions and manufacturers, and relevant packages. Name every model variable and transformation, explain how clustering or repeated observations were handled, and report diagnostics where available. Describe race and ethnicity categories, source, method of classification, and analytic rationale; do not treat these variables as self-explanatory biological attributes.

Methods prose should follow the analysis in executable order. Define a threshold before describing who passed it. Define the primary estimand before sensitivity analyses. Do not hide a consequential exclusion, recoding decision, or outcome definition in the supplement.

## Results

### Observed Pattern

Each exemplar opens Results with the study population or analytic frame, then gives descriptive findings before adjusted associations. Both use displays for exact details and make the text readable without restating every cell. Jiang uses a Results subsection; Barsky does not. Match subsectioning to the number of distinct analytic questions rather than treating it as a mandatory journal convention.

### ChicagoHealthMap Drafting Rules

Begin with analytic eligibility: eligible areas, period, observations, suppressed cells, missing comparators, and reliability-qualified areas. Then report results in the same order as Methods and displays.

For every primary estimate, give the measure, comparison, geography or analytic unit, period, eligible denominator or area count, point estimate, CI level and interval, and whether the analysis is primary or exploratory. Use exact values in text or tables; a map alone is not sufficient for an inferential claim. Refer to a table or figure at the claim, but do not narrate every value already available in that display.

Use "No. (%)" only for frequencies. Pair a proportion with its denominator when disclosure rules permit. Never replace a withheld value with 0, and never let an unshaded map area imply no disease.

Results prose should answer, in order: who or what was analyzed, what was observed, how large the estimate was, how uncertain it was, and where the supporting display appears. Report absolute quantities with relative measures. Do not write "significant" without naming whether the term is statistical, clinical, or policy relevant. Avoid "trend" for a nonsignificant result and avoid "revealed," "demonstrated," and "proved."

Prefer:

> Among [N] eligible community areas, [n] ([%]) met the reliability threshold. The EHR-diagnosed proportion was associated with [outcome] ([estimate]; 97.5% CI, [lower] to [upper]) (Table 2).

Avoid:

> The analysis revealed a robust and highly significant relationship, as shown in Figure 2.

## Discussion, Limitations, and Conclusions

### Observed Pattern

The Discussion in both papers begins with a synthesis of the principal finding, compares it with earlier research, considers interpretation, and moves toward policy relevance. Each has a distinct Limitations section and a short Conclusions section. Discussion language is cautious but not empty: it names plausible interpretations while preserving uncertainty.

### ChicagoHealthMap Drafting Rules

Open with what the resource and primary analysis found, immediately state the interpretive boundary, then state the planning relevance. A suitable order is:

1. Principal finding and boundary.
2. Interpretation of the cardiometabolic analysis.
3. Interpretation of the COPD analysis.
4. Comparison with prior work and independent public measures, including construct differences.
5. Limitations in descending order of threat to inference.
6. Brief conclusion with bounded planning relevance.

Limitations should address EHR capture and denominator definition, phenotype validity, ecological inference, geographic and temporal alignment, suppression and missingness, comparator non-equivalence, model uncertainty, and the absence of implementation evaluation. The conclusion may say that reliability-qualified measures can support hypothesis generation and planning conversations. It must not claim improved care, reduced mortality, unmet need, underdiagnosis, access barriers, care quality, optimal allocation, or intervention impact.

Write each limitation as threat, likely direction or consequence when knowable, and mitigation or residual uncertainty. Do not merely inventory weaknesses, and do not cancel each limitation with "however." Keep the Conclusions section to 2 or 3 sentences: principal finding, boundary, and proportionate relevance. No new mechanism, recommendation, subgroup, or number belongs there.

## Abstract and Key Points

### Journal Requirement to Recheck

Use the structured abstract fields in the project configuration: Importance, Objective, Design, Setting, Participants, Exposures, Main Outcomes and Measures, Results, and Conclusions and Relevance. Keep Design, Setting, and Participants separate at submission; JAMA combines them during editing for accepted papers. The maximum abstract and Key Points word counts are live limits, not stylistic suggestions. Place Key Points before the Abstract.

Do not use abbreviations in the title or abstract. If the full CAPriCORN name or another essential term makes the abstract unwieldy, rewrite the sentence rather than introducing an acronym there.

### ChicagoHealthMap Drafting Rules

- **Importance:** policy or public-health context plus the measurement gap.
- **Objective:** the exact prespecified aim.
- **Design:** exact study type, study years, analysis dates when needed, and any relevant blinding.
- **Setting:** Chicago, data systems, geographic level, and the context needed to judge applicability.
- **Participants:** eligibility, selection, exclusions, and final observed analytic population.
- **Exposures and Main Outcomes and Measures:** the EHR measure, comparator, and estimand; do not imply an individual-level exposure when the analysis is ecological.
- **Results:** analytic denominator and key demographic or area characteristics first, then primary quantitative findings with absolute values and CIs. Do not report a P value alone.
- **Conclusions and Relevance:** one bounded interpretation; add no new number or claim.

Key Points should answer Question, Findings, and Meaning in 3 compact factual statements. Question and Meaning are each 1 sentence; Findings may be 1 or 2. Findings names the design and primary result using basic numbers, but omits CIs, variance, P values, and secondary outcomes. The Meaning statement may say that reliability-qualified EHR measures may support hypothesis generation and planning conversations with FQHCs and community-based organizations. It should not claim that the findings direct service placement or demonstrate benefit.

## Tables and Figures

### Observed Pattern

The exemplar tables use descriptive titles that identify the analytic topic, population or setting, and period. Their frequency columns use "No. (%)" where appropriate; inferential tables display point estimates with 95% CIs and use footnotes for abbreviations and technical qualifications. The corpus uses a compact main-display set and moves stratified, domain-specific, or event-study material to eTables and eFigures.

### ChicagoHealthMap Display Plan

Keep the project within the configured maximum of 5 combined main displays:

1. **Table 1:** resource, observed population, coverage, suppression, and reliability profile.
2. **Figure 1:** study geography, capture, reliability, missingness, and analytic inclusion.
3. **Figure 2:** cardiometabolic and COPD adjusted associations with uncertainty.
4. **Figure 3:** EHR versus independent public-measure concordance and discordance.
5. **Table 2:** primary adjusted estimates, 97.5% CIs where required by the SAP, and clearly labeled secondary estimates.

Use brief descriptive titles, preferably 10 to 15 words, rather than titles that merely repeat the table number. Define units in column headers. Put abbreviations, denominator definitions, suppression rules, reference groups, model covariates, CI level, and data-period notes in footnotes. Keep a figure and table from duplicating the same role: use figures for patterns and uncertainty at a glance, tables for exact values.

Construct tables so the primary comparison reads horizontally. Report frequencies as `No. (%)` and include numerators and denominators for proportions when possible; explain empty cells, suppressed cells, and totals or percentages that do not sum. Focus multivariable tables on the primary exposure or comparison and show unadjusted and adjusted primary estimates. Number displays in citation order and cite each one in the text.

For maps, use a color scale with an explicit ordered meaning, a visible withheld/suppressed category, and a legend that makes missingness distinct from zero. For estimate plots, show CIs and the reference line. Do not use pie charts or 3-dimensional graphs. Use bar charts only for frequencies, avoid stacked bars except for justified ordinal distributions, label every axis and unit, and define every symbol, line, color, and error bar. Avoid complex multipart figures unless each panel is necessary. Put full strata, diagnostics, temporal sensitivity analyses, source provenance, and extended models in the supplement; cite every eTable and eFigure in order from the main text.

## Human Accountability and AI Use

Human authors remain responsible for every claim, number, citation, and wording choice. A human subject-matter author should perform the final evidence read, statistical read, and read-aloud prose edit. Do not use a language model to generate or format references; resolve every reference through a verified reference manager and source record.

Follow the current JAMA disclosure policy for any AI or language-model assistance with manuscript content. Record the tool, version, manufacturer, dates, content created or edited, and confirmation of author responsibility when disclosure is required. AI-assisted prose must still pass the same authorship, originality, confidentiality, copyright, and evidence checks as prose drafted without it.

## Human Revision Pass

1. Read only the first sentence of every paragraph. Together, they should form a coherent argument rather than a list of section labels.
2. Read the manuscript aloud. Break sentences where the voice runs out of breath or the grammatical subject disappears.
3. Circle every "this," "these," and "it." Replace any pronoun with an unclear antecedent.
4. Search for stock phrases and repeated sentence openings. Keep only those carrying real logic.
5. Compare every number with the frozen display and abstract. Check sign, unit, denominator, CI level, rounding, and direction.
6. Ask a domain author to mark any sentence that sounds technically correct but unlike something the team would naturally say. Rewrite it in the team's voice without loosening the claim boundary.

## Final Cross-Artifact Check

- The Abstract, Key Points, text, tables, figures, and supplement use identical population, period, geographic unit, denominator, estimate, and CI level.
- Every Results claim resolves to a frozen artifact, a display cell, or a reproducible calculation.
- Every interpretive claim states or is immediately followed by its relevant boundary.
- Every table and figure is cited in the text, and every supplement citation names the eTable or eFigure.
- The manuscript consistently distinguishes observed EHR-diagnosed proportions from population prevalence.
- Planning language for FQHCs and community-based organizations remains conditional and noncausal.
- The title is nondeclarative, contains no result direction or abbreviation, and is within 100 characters.
- Design, Setting, and Participants remain separate in the submitted abstract.
- Key Points report basic primary numbers without variance estimates, P values, or secondary findings.
- A human author has verified every citation and completed the final read-aloud edit.

## Authoritative Sources

- [JAMA Health Forum Instructions for Authors](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors), accessed July 14, 2026.
- AMA Manual of Style, 11th edition, as required by the journal.
- ICMJE Recommendations and the study-appropriate EQUATOR reporting guideline.
