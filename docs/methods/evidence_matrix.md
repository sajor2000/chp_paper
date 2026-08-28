# Evidence and Novelty Matrix

Execution date: 2026-07-14

Paperclip repository: `chicagohealthmap-evidence`, branch `main`; original seven-paper
claim commit `aa21fec7`. The accepted corpus below is the six-claim subset confirmed
`[OK]` by the controller's final live-status check.

Investigator review: **pending**

This is a bounded seed-based full-text checkpoint, not a completed systematic
screen. The six frozen PubMed searches yielded 1,178 unique PMIDs; their initial
screening and investigator adjudication remain pending. Nine separate PMC theme
searches (five candidates each) and nine focused maps demonstrated the full-text
workflow. Six claims are accepted because the authoritative live Paperclip state
marked them `[OK]`; the FQHC candidate returned a verifier error and is a gap.

| Category | Claim | Evidence | PMID / DOI / PMCID | Exact supporting location | Tool | Query or search identifier | Access date | Screening decision | Verification status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| EHR-diagnosed proportion limitations; representativeness | EHRs contain information only on people receiving care, and local validity varies with participating-system coverage. | direct | 35945537 / 10.1186/s12889-022-13809-2 / PMC9364501 | Paperclip L49 | Paperclip CLI | `ehr_public_health`; `small_area_chronic_disease`; `s_35a3b8cb` | 2026-07-14 | awaiting full-text investigator adjudication | OK |
| Small-area mapping; spatial/ecological limitations | Zip-code correlations were ecological and hypothesis-generating, and cells under 15 people were excluded. | direct | 27463641 / 10.1371/journal.pone.0159227 / PMC4963128 | Paperclip L36 | Paperclip CLI | `small_area_chronic_disease`; `s_06eacba5` | 2026-07-14 | awaiting full-text investigator adjudication | OK |
| Chicago life-expectancy inequity; hypertension/diabetes mortality rationale | Chicago's pre-COVID life-expectancy gap and cause-specific contributions differed by sex; this is contextual and does not establish a disease-to-life-expectancy causal effect. | direct | 36973497 / 10.1007/s40615-023-01566-w / PMC10042425 | Paperclip L11 and L15 | Paperclip CLI | `urban_life_expectancy`; `s_fd7d8be5` | 2026-07-14 | awaiting full-text investigator adjudication | OK |
| Resource precedent; reporting methods | A six-study scoping review found unclear evidence that real-world-data surveillance tools improved policy or practice decisions. | direct | 36434553 / 10.1186/s12889-022-14452-7 / PMC9694563 | Paperclip L18 | Paperclip CLI | `ehr_public_health`; `small_area_chronic_disease`; `s_6343ea9a` | 2026-07-14 | awaiting full-text investigator adjudication | OK |
| EHR denominator/capture; missingness | Standard missing-data approaches may incompletely control EHR selection bias because observation reflects patient, provider, and system decisions. | direct | 27668265 / 10.13063/2327-9214.1203 / PMC5013936 | Paperclip L6 and L12 | Paperclip CLI | `s_35a3b8cb` (theme expansion) | 2026-07-14 | pending investigator screening | OK |
| Reporting methods; prespecification | With few amendments, clinical-trial SAP guidance can be applied to observational studies to improve transparency and validity. | direct | 31818263 / 10.1186/s12874-019-0879-5 / PMC6902479 | Paperclip L13 | Paperclip CLI | `s_292eaf6a` (theme expansion) | 2026-07-14 | pending investigator screening | OK |
| FQHC/CBO planning | A candidate geographic-access precedent was located, but its latest authoritative Paperclip verification returned a verifier error; no material claim is accepted. | gap | 35321700 / 10.1186/s12913-022-07685-0 / PMC8942056 | verifier error; no accepted support location | Paperclip CLI | `s_91ef3cc2` (theme expansion) | 2026-07-14 | pending investigator screening | unverified |
| Multisystem deduplication | The seed corpus does not yet verify a material claim about cross-system person deduplication. | gap | — | — | PubMed MCP and Paperclip CLI | six frozen queries plus nine theme searches | 2026-07-14 | pending investigator screening | unverified |
| Hypertension/diabetes comparator inventory | Comparator candidates were retrieved, but no claim beyond the six verified seed claims has been accepted for manuscript use. | gap | — | — | PubMed MCP and Paperclip CLI | `small_area_chronic_disease`; `s_a2015688` | 2026-07-14 | pending investigator screening | unverified |
| COPD mortality rationale | COPD candidates were mapped, but no material COPD mortality claim has been verified in the dedicated repository. | gap | — | — | Paperclip CLI | `candidate_conditions`; `s_1ac839f3` | 2026-07-14 | pending investigator screening | unverified |
| Evaluated FQHC/CBO implementation impact | No verified seed evidence establishes that ChicagoHealthMap use improved resource allocation, access, care, or outcomes. | gap | — | — | Paperclip CLI | `local_resource_planning`; `s_91ef3cc2` | 2026-07-14 | pending investigator screening | unverified |
| Novelty | No novelty claim is authorized. Within the six PubMed query families searched through 2026-07-14 and the nine focused PMC searches, the distinguishing combination remains a candidate for investigator review. | gap | — | — | PubMed MCP and Paperclip CLI | complete dated manifests | 2026-07-14 | pending investigator screening | unverified |

## Gate 2 audit

- PubMed paging and unique-PMID reconciliation: passed for the six frozen searches.
- Metadata integrity: 1,165 records retrieved; 13 unavailable records remain blank rather than inferred.
- Paperclip verification: six seed claims are `[OK]`; the FQHC verifier error and every other material claim are gaps or unverified.
- Quotations: the matrix paraphrases evidence and records exact line locations; it does not reproduce long quotations.
- Novelty: wording is explicitly bounded by databases, searches, and date.
- Screening: 1,178 records remain pending investigator review; no confirmatory modeling is authorized.

Gate 2 status: **pending investigator review**. Gate 2 is not closed and this
checkpoint does not authorize modeling, a novelty assertion, or manuscript use
of unverified claims.
