# EHR quality checkpoint

**Gate 3: CLOSED**

Task 9 stopped before reading any source row or value. The 2026-05-27 schema catalog
contains 21 tables and 549 nonempty field positions; zero positions have verified
semantic evidence and zero tables are analysis-usable. The two observed-empty exports
also lack intended owner-verified schemas.

Strict ingestion and quality primitives have been tested only with explicit synthetic,
fully verified contracts. They do not convert the positional checkpoint into a semantic
schema. No analysis-ready Parquet was written from the real snapshot, and no empirical
quality result was inferred from filenames or value patterns.

The local commands

```text
chicagohealthmap ehr ingest --snapshot-date 2026-05-27
chicagohealthmap ehr quality --snapshot-date 2026-05-27
```

exit nonzero and write an ignored, disclosure-safe JSON/Markdown checkpoint under
`outputs/quality/`. That checkpoint contains schema-evidence counts only and explicitly
records that zero source rows were read.

Gate 3 can be reconsidered only after source-owner evidence identifies every required
field, type, null rule, key, unit, suppression state, and analysis role.
