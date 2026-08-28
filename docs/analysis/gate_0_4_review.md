# Gate 0-4 review

Review date: 2026-07-14.

This checkpoint verifies the source and evidence foundation through Phase 4. It
does not authorize case promotion, first-party analytic use, confirmatory
modeling, Results prose, or manuscript claims. Gate decisions are fail-closed:
missing semantic or investigator evidence remains blocking even when engineering
checks pass.

## Gate decisions

| Gate | Status | Evidence | Interpretation |
| --- | --- | --- | --- |
| Gate 0: repository governance | Passed | `docs/solutions/2026-07-14-phase-0-repository-governance.md`; `.superpowers/sdd/progress.md` | Passed only for repository paths, contracts, privacy/credential boundaries, test conventions, and immutable snapshot primitives. |
| Gate 1: first-party preservation | Passed | `docs/solutions/2026-07-14-phase-1-first-party-preservation.md`; `config/first_party_sources.yml` | Passed only for byte accounting, immutable local preservation, exact configured inventories, safe archive extraction, and unresolved discrepancy records. |
| Gate 2: evidence and novelty | Open | `docs/methods/literature_search_protocol.md`; `docs/methods/evidence_matrix.md`; `.superpowers/sdd/task-7-report.md` | PubMed/Paperclip search artifacts exist, but 1,178 records remain pending investigator screening and full-text/comparator adjudication. No novelty or interpretation claim is authorized. |
| Gate 3: first-party field semantics | Closed | `docs/analysis/data_dictionary.md`; `docs/analysis/ehr_quality_summary.md`; `outputs/quality/gate_3_decision.json` when materialized | The first-party export has 21 cataloged tables and 549 nonempty positions, with zero semantically verified positions and zero analysis-usable tables. No source rows are read for analysis. |
| Gate 4: public-source acquisition/provenance | Passed for the public-source foundation | `config/source_registry.yml`; `sources/public/_registry/acquisition_matrix.csv`; `data/processed/public/*.schema.json`; `outputs/provenance/*`; `src/chicagohealthmap/pipeline.py`; `tests/integration/test_offline_rebuild.py` | The registered public-source foundation is authoritative, cited, immutable, normalized where permitted, and field-lineage traced. This does not override Gate 2 or Gate 3 blocks; 2019 ACS remains inventory/citation-only until a tested sequence decoder is added. |

## Required review points

| Review point | Status | Evidence paths | Notes |
| --- | --- | --- | --- |
| Repository and privacy boundaries | Pass | `src/chicagohealthmap/config.py`; `src/chicagohealthmap/sources/models.py`; `docs/solutions/2026-07-14-phase-0-repository-governance.md`; `.gitignore` | Raw snapshots, derived data, and outputs remain outside version control. Contracts reject traversal, unsafe replacement, credential-bearing URLs, and protected local paths in public provenance. |
| First-party checksums | Pass | `config/first_party_sources.yml`; `.superpowers/sdd/task-4-report.md`; `docs/solutions/2026-07-14-phase-1-first-party-preservation.md` | The preservation checkpoint recorded 21 configured exports, including 2 observed-empty exports, with matching source/snapshot hashes. The raw bytes are local and ignored. |
| Archive-method extraction | Pass | `config/first_party_sources.yml`; `.superpowers/sdd/task-5-report.md`; `docs/analysis/methods_discrepancies.md` | Two website-method ZIP archives and 11 extracted members were preserved safely. Historical website methods remain provenance only and do not establish EHR semantics. |
| Literature search completeness | Open | `docs/methods/literature_search_protocol.md`; `docs/methods/evidence_matrix.md`; `.superpowers/sdd/task-7-report.md` | Six PubMed query families yielded 1,178 unique PMIDs, but screening and investigator adjudication remain pending. |
| Field/schema verification | Guarded S4 mapping; fail closed for general ingestion | `config/first_party_schemas.yml`; `docs/analysis/data_dictionary.md`; `docs/analysis/s4_methods_mapping.json`; `docs/analysis/ehr_quality_summary.md` | The S4 packet now records guarded core mappings for geography, year, condition, diagnosed count, source-published measure, capture rate, and City of Chicago case-study frame. The general first-party schema remains unpromoted for broad analytic ingestion. |
| Denominator and suppression semantics | Guarded | `docs/analysis/s4_methods_mapping.json`; `docs/analysis/methods_discrepancies.md`; `docs/analysis/ehr_quality_summary.md`; `outputs/quality/gate_3_decision.json` when materialized | The website glossary defines capture rate and fewer-than-10 suppression. Adult-denominator reconstruction, subgroup count/rate blocks, zero-vs-missing interpretation, and public suppression application remain guarded for tested downstream code. |
| External registry completeness | Pass | `config/source_registry.yml`; `sources/public/_registry/acquisition_matrix.csv`; `docs/methods/data_sources.md` | The canonical registry contains exactly the 14 prespecified public source IDs and excludes unsupported police, 311, pharmacy, and WIC sources. |
| API or approved bulk acquisition | Pass | `src/chicagohealthmap/sources/adapters/`; `sources/public/CHECKSUMS.sha256`; `sources/curated/metopio/CHECKSUMS.sha256`; `.superpowers/sdd/task-11-report.md` through `.superpowers/sdd/task-16-report.md` | Public sources use authoritative endpoints or documented official bulk fallbacks. Frozen snapshots are reused offline; no live download is required for rebuild. |
| Licenses and citations | Pass | `outputs/provenance/data_source_inventory.csv`; `outputs/provenance/data_sources.csl.json`; `outputs/provenance/data_sources.bib`; `src/chicagohealthmap/provenance/citations.py` | The provenance build emits 16 source records: 14 public registry snapshots plus restricted extract and website-method records. Citations are disclosure-safe and reject protected paths. |
| Geography and time alignment | Pass with explicit limits | `src/chicagohealthmap/external/geography.py`; `data/processed/public/tract_community_overlay_2020.schema.json`; `data/processed/public/tract_community_overlay_2024.schema.json`; `docs/analysis/data_dictionary.md` | 2020/2024 tract-community overlays use projected polygon intersections and preserve TIGER/community-area vintage provenance. The 2019 ACS sequence archive is not emitted as record-level values pending a tested decoder. |
| Record and field lineage | Pass | `outputs/provenance/variable_lineage.csv`; `outputs/provenance/table_figure_sources.csv`; `src/chicagohealthmap/provenance/lineage.py` | Every emitted public processed field is traced to source-specific field maps. No publication table or figure source is claimed at this phase. |
| Marimo validation | Pass for Gate 3 review, no Task 17 notebook edit | `notebooks/01_data_review.py`; `tests/integration/test_data_review_notebook.py`; `.superpowers/sdd/task-10-report.md` | The notebook reads disclosure-safe Gate 3 outputs only and produces a closed Gate 3 decision. Task 17 did not need notebook changes; no external-source notebook batch behavior was added. |
| Offline rebuild | Pass | `src/chicagohealthmap/pipeline.py`; `src/chicagohealthmap/cli.py`; `tests/integration/test_offline_rebuild.py` | `chicagohealthmap rebuild --through-phase 4 --offline --root PATH` denies network-authorizing mode, rebuilds public normalization and provenance from frozen snapshots, and reports deterministic counts/hashes without absolute protected paths. |

## Offline rebuild evidence

The Task 17 rebuild path verifies the current public-source foundation through
Phase 4 without contacting APIs:

```bash
uv run chicagohealthmap rebuild --through-phase 4 --offline --root .
```

The report is JSON and disclosure-safe. It records:

- `Gate 2: open`
- `Gate 3: closed`
- `Gate 4: passed`
- 15 processed public tables and 645,421 processed public rows
- 5 provenance artifacts under `outputs/provenance/`
- 14 registered public source records in `source_inventory`
- first-party schema evidence of 21 tables, 549 positions, 0 verified positions, and 0 analysis-usable tables

Blocked analyses remain explicitly named by the rebuild report: novelty and
interpretation claims pending Gate 2; disease candidate scoring and
analysis-ready EHR publication pending Gate 3; and confirmatory modeling pending
both Gate 2 and Gate 3.

## Remaining boundaries

- Gate 2 remains open until investigator title/abstract screening, full-text
  extraction, comparator adjudication, and novelty review are complete.
- Gate 3 remains closed for broad analysis-ready field use. The S4 mapping packet
  now promotes guarded core positions for the Chicago case-study frame, but adult
  denominator reconstruction, subgroup blocks, suppression application, S5 case
  scoring, and S6 SAP authorization remain prerequisites for final analytic data
  construction and confirmatory modeling.
- Gate 4 passing is limited to public-source acquisition, normalization,
  citations, immutable provenance, and field lineage. It is not permission to use
  unresolved first-party fields analytically.
- The 2019 ACS sequence-based archive is preserved and cited, but record-level
  values remain withheld until a tested positional decoder exists.
