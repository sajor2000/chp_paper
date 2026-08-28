# Chicago Health Map master-notebook manuscript plan

**Target article type:** JAMA Health Forum Original Investigation

**Current authorization state:** `results_authorized=false`; all numeric result narratives are
for internal co-author and S7 review only until human authorization changes.

## Submission scaffold

| Manuscript section | Master-notebook evidence | Writing rule |
| --- | --- | --- |
| Title and Key Points | Central question, complementarity framing, C1/C2 gate status | Avoid declarative, causal, predictive-superiority, or prevalence claims. |
| Structured Abstract | `manuscript_result_narratives.json`, Table 1, Table 2 | Lead with population, source roles, estimand, estimate, CI, and authorization status. |
| Introduction | CHM tract lens and life-expectancy gap rationale | Establish why direct EHR patterns complement, rather than replace, public data. |
| Methods | Data cleaning, quality checks, analytic dataset, SAP, source manifests | State observational unit, adjustment set, frozen-IQR scaling, HC3 covariance, and gates. |
| Results | Tables 1–2, Figures 1–3, concordance and robustness supplements | Report estimates with CIs and eligible `n`; do not report P values alone. |
| Discussion | Complementarity metrics and within-area heterogeneity | Interpret discordance as measurement discordance, not underdiagnosis or unmet need. |
| Limitations | Ecological design, EHR capture, suppression, comparator non-equivalence, no tract life expectancy | Avoid causal or individual-level interpretation. |
| Data Sharing Statement | Frozen public-data artifacts and restricted CHM governance | Describe what can be shared and why raw EHR data cannot be deposited. |
| Supplement | eTable 1–5 index, full coefficients, robustness, spatial, tract outputs | Cite each eTable/eFigure in order of first mention. |

## Results-writing layers

Each case study has two internal prose layers generated from the same governed result object:

1. **Biostatistical interpretation:** estimand, eligible `n`, scaling, adjustment set, estimate,
   CI, diagnostics, sensitivity status, and authorization state.
2. **Co-author interpretation:** a short plain-language explanation of what the pattern means,
   what it does not mean, and why source discordance demonstrates complementarity.

C1 is always described as withheld for maximum VIF above 5. C2 remains a freeze candidate and
is not manuscript-importable while authorization is false.

## JAMA Health Forum formatting targets

The current target is an Original Investigation: 3000-word text limit, no more than 5 main
tables and/or figures, structured abstract, Key Points, Study Type, Data Sharing Statement,
and EQUATOR-consistent reporting. The Methods will identify the observational design and the
Results will use association language rather than causal language. Main figures are exported
as separate PDF vector files; full legends remain in the manuscript handoff. Supplemental
tables and figures are numbered and cited in order.

Source: [JAMA Health Forum Instructions for Authors](https://jamanetwork.com/journals/jama-health-forum/pages/instructions-for-authors).

## Figure style contract

The notebook uses `cividis` for sequential measures and labeled `RdBu_r` for signed rank gaps,
with explicit missing/suppression/qualification encodings. PNG files support notebook QA and
PDF files support submission. Figure QA records dimensions, file size, grayscale renderability,
and the color-vision-safe palette review in `figure_qa.json`.

Matplotlib guidance: [Choosing Colormaps](https://matplotlib.org/stable/tutorials/colors/colormaps.html).
