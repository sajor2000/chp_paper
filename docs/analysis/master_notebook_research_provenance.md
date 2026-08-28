# Master Notebook Research Provenance

This record binds the master notebook's framing and implementation choices to checked sources.
It is not a manuscript reference list. Bibliographic details and claim language were retrieved
from Paperclip, PubMed/NCBI, Ref documentation results, and the project's dated journal snapshot;
they were not generated from memory. `results_authorized=false` remains binding.

## Biomedical claim trail

| Notebook claim or design role | Verified source | Permitted use |
| --- | --- | --- |
| EHR surveillance can complement public surveillance but has data-quality, missingness, and representativeness limitations. | Ghildayal et al, *Public Health Surveillance in Electronic Health Records: Lessons From PCORnet*, PMID 38991533, PMCID PMC11262136, DOI 10.5888/pcd21.230417. Paperclip verification: [PMC11262136#L22,L32](https://citations.gxl.ai/papers/PMC11262136#L22,L32). | Supports complementarity and limitations only; not validation or population prevalence. |
| Small-area EHR estimates depend on local coverage and participating providers and cannot replace population surveys. | Chen et al, *Small-area estimation for public health surveillance using electronic health record data: reducing the impact of underrepresentation*, PMID 35945537, PMCID PMC9364501, DOI 10.1186/s12889-022-13809-2. Paperclip verification: [PMC9364501#L49-L50](https://citations.gxl.ai/papers/PMC9364501#L49-L50). | Supports the noninterchangeability and capture limitations. |
| EHR-derived hypertension measures can be compared with survey measures, but phenotype and source composition affect interpretation. | Allen et al, *Electronic Health Records for Population Health Management: Comparison of Electronic Health Record-Derived Hypertension Prevalence Measures Against Established Survey Data*, PMID 38478904, DOI 10.2196/48300. | Supports comparator-alignment rationale; the CHM notebook does not claim equivalence. |
| EHR- and PLACES-derived small-area measures can be similar yet differ; source-specific denominator and phenotype definitions must be made visible. | Winkelman et al, *Population Estimates and Hypertension and Diabetes Prevalence: Cross-Sectional Quantitative Study Comparing Electronic Health Record–Derived Counts, Census, and Centers for Disease Control and Prevention Population Level Analysis and Community Estimates*, PMID 42097616, PMCID PMC13195376, DOI 10.2196/86337. PubMed/PMC full text verified August 13, 2026. | Supports the cross-source comparison rationale and transparent denominator reporting only; it does not validate CHM, establish population prevalence, or support diabetes–PLACES comparison before phenotype and period mapping are approved. |
| Distributed EHR surveillance has been studied against state and small-area survey estimates. | Klompas et al, *State and Local Chronic Disease Surveillance Using Electronic Health Record Systems*, PMID 28727539, DOI 10.2105/AJPH.2017.303874. | Historical feasibility context, not a performance claim for CHM. |
| Chicago community-area life expectancy varies spatially and is an area-level summary. | Hunt et al, *Life Expectancy Varies in Local Communities in Chicago: Racial and Spatial Disparities and Correlates*, PMID 26863550, DOI 10.1007/s40615-015-0089-8. | Supports the rationale for pairing tract detail with community-area context; not causality. |
| EHR population measures require explicit attention to bias and representativeness. | Dixon et al, *Measuring Population Health Using Electronic Health Records: Exploring Biases and Representativeness in a Community Health Information Exchange*, PMID 26262310. | Supports the capture and inference boundary. |

Paperclip repository `chicago-healthmap-complementarity` was reverified on July 15, 2026 at
commit `53c7acd8`; both line-pinned claims returned `[OK]`. PubMed identifiers and titles were
checked through PubMed/NCBI records. No public comparator is treated as a gold standard.

## Ref documentation trail

| Implementation choice | Official documentation checked through Ref |
| --- | --- |
| Reactive, dependency-ordered notebook cells and script execution | [marimo dataflow](https://docs.marimo.io/guides/understanding_dataflow/) and [marimo checkbox input](https://docs.marimo.io/api/inputs/checkbox/) |
| Deterministic vector/raster exports and metadata | [Matplotlib `savefig`](https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.savefig.html) |
| HC3 covariance | [statsmodels robust covariance results](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html) |
| Prespecified multicollinearity gate | [statsmodels variance inflation factor](https://www.statsmodels.org/stable/generated/statsmodels.stats.outliers_influence.variance_inflation_factor.html) |
| Conditional spatial-error sensitivity | [PySAL `spreg.ML_Error`](https://pysal.org/spreg/generated/spreg.ML_Error.html) |

These documentation checks support software usage, not scientific authorization. The tested code,
lockfile, topology checksums, and artifact manifest remain the executable source of truth.

## JAMA Health Forum instruction status

The official Instructions for Authors page was opened directly on July 15, 2026. The live page
confirmed the Original Investigation requirements used here: 3000 words, no more than 5 combined
main tables and figures, a structured abstract, Key Points, and a Data Sharing Statement. Tavily
separately returned `monthly_cap_reached_bonus_eligible`; that tool failure remains in the research
log but did not prevent direct official-page verification. The instructions must be revalidated
within 30 days of submission, and this check does not authorize results or establish that every
submission component is complete.

A separate direct official-page check was performed on July 16, 2026 for this audit turn; it
returned the same Original Investigation limits. This current check is recorded independently
of the July 15 project snapshot and does not change the authorization gate.

The official page was rechecked directly on August 13, 2026 while adding the notebook manuscript
front matter. It continued to list Original Investigation requirements of 3000 words, no more
than 5 combined tables and figures, a structured abstract, Key Points, a Data Sharing Statement,
and an applicable EQUATOR checklist. This verification does not authorize results or establish
submission readiness.

The official page was rechecked directly on August 26, 2026 for the statistician review package.
The same Original Investigation limits and reporting requirements remained in effect. The package
remains a methods-review artifact, and this current verification does not authorize results or
establish submission readiness.

The official page was rechecked directly on August 27, 2026 while restructuring the notebook as an
executable SAP and Original Investigation. The same limits remained in effect. The check also
confirmed the need to name the observational design and applicable reporting guideline. STROBE and
RECORD remain the selected guidance. This verification does not authorize results or establish
submission readiness.

The JAMA manuscript skill auditor was run on a normalized extraction of the notebook prose on
July 15, 2026. It found 2647 main-text words and populated Introduction, Methods, Results,
Discussion, Limitations, and Conclusions sections. Its only warnings were absent structured
Abstract and Key Points elements, which are intentionally outside this executable notebook rather
than evidence of a complete submission package.

## Inference and authorization boundary

These sources support the question of whether direct CHM EHR-diagnosed tract patterns are aligned
with, but not interchangeable with, public comparators and community-area life-expectancy
summaries. They do not authorize claims of predictive superiority, validation, population
prevalence, causality, underdiagnosis, unmet need, access failure, measurement error, or service
need. C1 remains withheld at maximum VIF 5.016 (>5); C2 remains a freeze candidate. Neither may be
imported as an authorized manuscript result while `results_authorized=false`.
