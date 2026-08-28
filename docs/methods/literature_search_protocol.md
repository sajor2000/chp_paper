# Biomedical Literature Search Protocol

## Status and scope

This protocol was frozen on 2026-07-14 before any search in this phase was
executed. The initial search was executed on 2026-07-14 and remains pending
investigator screening and adjudication. PubMed is the authoritative discovery database. The six exact initial
queries and their immutable version records are in
`config/literature_queries.yml`. The search will run from database inception to
the execution date, with the date, original query, effective query, result
count, pagination offsets, PMIDs, and tool provenance captured for every query.

The review will include English-language human studies and relevant methods
papers. Eligible subject matter has urban or subregional geography and uses
EHR, claims, HIE, or clinical-network surveillance. Records must contribute to
at least one prespecified evidence use: disease mapping; life expectancy or
mortality; representativeness, denominator, or health-care-capture assessment;
or local planning and resource allocation.

Purely individual prediction models without geographic or public-health
relevance will be excluded. Records outside the stated language, population,
geography, data-system, or evidence-use scope may be retained only as
`background` when they provide necessary methods or interpretation context.

## Query control and amendments

Each query has a stable ID and one active, numbered version. The initial query
strings are frozen verbatim. A change must append a new numbered version with
its complete query string, freeze date, status, and amendment reason; no prior
version may be edited, replaced, or deleted. Any MeSH lookup or database syntax
translation will be recorded separately and will not silently replace the
original query. Every appended version must identify the approval record in
`approved_by` and record `screening_phase` as either `before_screening` or
`after_screening_started`. The initial prespecified freeze uses
`approval_status: initial_prespecified_freeze` and a null `approved_by`, because
no later amendment approval occurred; it records `screening_phase:
before_screening`. The null is the only policy exception: every version record
must otherwise contain nonempty `version`, `query`, `status`, `frozen_on`,
`amendment_reason`, `approved_by`, and `screening_phase` fields. Thus the
amendment history states who approved each actual
change and whether it occurred before or after screening began without
inventing an approver for the initial freeze.

An update search will be run immediately before scientific gate S6 and again
within 30 days of submission. Each update uses the then-active version, records
its inclusive date window, and preserves the same query-level provenance as the
initial search. Europe PMC may be used only as a labeled expansion for preprints
or records unavailable through PubMed.

## Screening workflow

Each deduplicated record receives one screening decision: `include`, `exclude`,
`background`, or `awaiting_full_text`. Title/abstract and full-text decisions
are retained as separate status fields so the history is not overwritten. An
excluded record must have exactly one explicit exclusion reason selected from a
controlled vocabulary. Notes may clarify that reason but may not substitute for
it. An inaccessible article remains `awaiting_full_text`; lack of access is not
negative evidence.

The screening record contains:

- stable record ID and PMID or other identifier;
- query ID and query version that retrieved the record;
- title/abstract and full-text statuses, reviewer, and decision date;
- exactly one exclusion reason when the final status is `exclude`;
- evidence-use categories, condition tags, and geography tags;
- full-text availability and Paperclip verification status; and
- free-text adjudication notes and amendment linkage, when applicable.

Conflicts are preserved until adjudication. Duplicate retrieval across queries
retains every query-to-record link. Scientific claims may advance to the
evidence matrix only after Paperclip full-text verification or verification
against an official primary source.

## Initial execution record: 2026-07-14

The six version-1 queries were executed exactly as frozen with the PubMed MCP
English-language filter and without a PubMed humans filter. Human eligibility
remains a screening decision so incomplete indexing does not remove relevant
methods papers. Each result set fit in one actual MCP page requested with a
maximum of 500 records. Query yields were 328 (`ehr_public_health`), 141
(`small_area_chronic_disease`), 352 (`urban_life_expectancy`), 337
(`clinical_network_surveillance`), 49 (`local_resource_planning`), and 26
(`candidate_conditions`). The combined result set contained 1,178 unique PMIDs.

Bounded metadata retrieval used 24 batches of at most 50 PMIDs. PubMed returned
metadata for 1,165 PMIDs and identified 13 as unavailable. Their fields remain
empty; no metadata was inferred. PubMed MCP did not return a database update
date or raw result-set identifier, so those manifest fields are null rather than
invented. The dated search manifest retains the exact original and effective
queries, filter, offsets, PMIDs, timestamps, URLs, and MCP identity.

The screening file is an initial queue, not a completed title/abstract screen.
Every row is conservatively marked `awaiting_full_text`, with investigator
review pending; none is treated as included or excluded. This status records
that no eligibility conclusion has been made, not that full text is known to be
available. Accordingly, `full_text_required` is `unknown` until title/abstract
screening establishes whether full-text review is needed. Investigator
screening must assign final protocol decisions and the
single controlled exclusion reason required for every exclusion.

Paperclip used the dedicated `chicagohealthmap-evidence` repository. Nine
separate five-paper PMC searches covered multisystem EHR surveillance,
small-area EHR measurement, denominator/capture bias, hypertension/diabetes
comparisons, COPD comparisons, ecological/spatial limitations, life-expectancy
inequities, prespecification/missingness/estimands, and FQHC/CBO planning.
Recovered result exports show that focused maps succeeded for 41 of 45 candidate
tasks; four timeouts are retained in the workflow manifest and failure log. Six
seed claims are authoritative live `[OK]` records. A transient local status
reported the FQHC candidate as `[OK]`, but the controller's later authoritative
status returned an empty verifier response; it is therefore unverified. The
remaining corpus may not support manuscript claims.

Tavily was not used as evidence. The controller's single retry returned
`monthly_cap_reached_bonus_eligible`; no purchase, bonus enrollment, sign-up, or
credential exposure occurred. Direct official-source review is deferred to a
later update milestone.

Gate 2 remains open pending investigator screening of all 1,178 records,
full-text expansion for included/background records, comparator and novelty
adjudication, and acceptance of the evidence matrix. No modeling or novelty
claim is authorized by this checkpoint.

## Gate 2 audit command

The frozen 2026-07-14 evidence checkpoint can be re-audited without advancing
the gate:

```bash
uv run chicagohealthmap evidence audit --gate 2 --snapshot-date 2026-07-14
```

The command validates the PubMed, Paperclip, and tool-failure artifacts and
reports the open blockers in deterministic JSON. It also checks the concise
Tavily-discovered official ChicagoHealthMap glossary artifact at
`sources/literature/web/snapshots/2026-07-14/chicagohealthmap_data_glossary.json`;
that artifact records the first-party methods source for capture rate,
tract geography, small-cell suppression, standardized mean difference, and the
capture-rate metric. `--check` intentionally exits nonzero while Gate 2 remains
pending investigator screening, full-text expansion, comparator and novelty
adjudication, current official/gray-literature update, and evidence-matrix
acceptance.

## Investigator screening workbench

The frozen PubMed records can be converted into deterministic reviewer batches:

```bash
uv run chicagohealthmap evidence screening build \
  --snapshot-date 2026-07-14 \
  --batch-size 100 \
  --output-dir outputs/literature/screening/2026-07-14
```

The generated batch CSVs contain only PubMed bibliographic and abstract
metadata plus blank reviewer fields. They do not contain protected
ChicagoHealthMap/CAPriCORN source rows and do not close Gate 2.

Returned batch files can be checked without advancing the gate:

```bash
uv run chicagohealthmap evidence screening validate \
  --snapshot-date 2026-07-14 \
  --input-dir outputs/literature/screening/2026-07-14
```

Use `--require-complete` only when every row has been investigator-screened.
Validation preserves `gate_status: open`; Gate 2 can close only after screening,
full-text expansion, comparator/novelty adjudication, official/gray-literature
update, and evidence-matrix acceptance are complete.
