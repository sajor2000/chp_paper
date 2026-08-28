# Adversarial Manuscript Audit Rubric

## Review order

Review high-consequence failures before prose polish.

| Priority | Question |
| --- | --- |
| 0. Scope | Are target journal, article type, study design, task, and governing sources established? |
| 1. Evidence | Does every number and factual claim resolve to verified evidence? |
| 2. Inference | Does wording match design, estimand, unit, population, and uncertainty? |
| 3. Consistency | Do title, Key Points, abstract, text, displays, and supplement agree? |
| 4. Completeness | Are prespecified outcomes, exclusions, missingness, diagnostics, deviations, and limitations reported? |
| 5. Journal | Are current article-type and reporting requirements satisfied? |
| 6. Human style | Is the prose concrete, natural, compressed, and free of visible templates? |

## Audit procedure

1. Run `scripts/audit_manuscript.py` for deterministic structure, limit, title, abbreviation, causal-term, and stock-phrase warnings.
2. Build a claim-to-evidence map for every Results and Abstract sentence: location, claim, source artifact, denominator, estimate, uncertainty, analysis status, and verification status.
3. Compare the protocol/SAP sequence with Methods, Results, displays, and supplement.
4. Recalculate or source-check every displayed primary number. Verify numerator, denominator, unit, period, sign, rounding, and CI level.
5. Search interpretation terms: causal verbs, population claims, significant/trend, validated, representative, robust, actionable, need, access, and impact. Test whether removing a hedge reveals an unsupported claim rather than clearer prose.
6. Check whether limitations name the most serious threats and their consequences rather than merely listing caveats.
7. Inspect displays visually. Check withheld/missing/zero distinctions, axis units, reference lines, legends, footnotes, panel necessity, and exact-value availability.
8. Run a contradiction pass: compare sample sizes, directions, reference groups, outcome definitions, time windows, rounding, and null/significance language across every artifact.
9. Apply the human revision sequence from `writing-style.md` only after scientific issues are resolved.

## Section questions

### Introduction

- Does the first paragraph establish a specific policy or public-health problem?
- Is the evidence gap supported and narrower than a novelty claim?
- Does the final sentence state one exact objective or hypothesis?

### Methods

- Could a knowledgeable analyst reproduce the primary analysis?
- Are population, setting, period, unit, exposure, outcome, eligibility, missingness, and statistical methods explicit?
- Are ethics, reporting guideline, analysis dates, software, multiplicity, and sensitivity status present?
- Are decisions that alter interpretation visible in the main text?

### Results

- Does the section begin with the analyzed sample and exclusions?
- Does every primary result include exact estimate and uncertainty?
- Are absolute quantities paired with relative measures?
- Does order match Methods and displays, without policy interpretation?

### Discussion and conclusion

- Does the first paragraph synthesize rather than repeat?
- Are mechanisms labeled as interpretations rather than findings?
- Are comparisons with literature construct-compatible?
- Are limitations ordered by threat to inference?
- Does the conclusion add no result, subgroup, mechanism, or recommendation?

### Abstract and Key Points

- Are submission headings complete and separate?
- Does Abstract Results begin with the analyzed sample and quantify primary findings?
- Do Key Points omit variance, P values, and secondary outcomes?
- Is Meaning no stronger than the Discussion conclusion?

## Findings format

Use these severities:

- **Blocker:** submission or drafting cannot safely proceed because evidence, scope, ethics, or an author decision is missing.
- **Major:** likely changes scientific interpretation, primary reporting, or journal eligibility.
- **Moderate:** creates ambiguity, inconsistency, or reproducibility risk without changing the central result.
- **Minor:** local clarity, style, or formatting defect.

Report findings first, ordered by severity. For each finding provide: severity; artifact and exact location; evidence; why it matters; exact correction; verification needed. Separate verified defects from questions. If no defects are found, state residual risks and checks that could not be performed.
