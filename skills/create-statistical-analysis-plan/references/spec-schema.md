# SAP JSON Specification

The builder accepts a UTF-8 JSON object with:

- `metadata`: title, protocol ID, version, status, target journal, date, and optional source URL.
- `overview`: rows keyed by the eight fixed Overview headers.
- `outputs`: array of `{section, rows}` objects; rows use the seven fixed Outputs headers.
- `variableNotes`: exactly two note strings.
- `analysisColumns`: one or more study-specific membership columns inserted after `File`.
- `variables`: rows with fixed Master Variables fields, every analysis column, and `Notes / Resolved Decisions`.
- `annexes`: array of `{name, title, note, columns, rows}`. Sheet names must be unique and at most 31 characters.
- `validation.requiredAnnexes`: annex names that must exist.
- `validation.statusValues`: controlled vocabulary applied as Excel list validation to every annex column whose header contains `Status`; its quoted comma-separated serialization must not exceed Excel's 255-character inline-list limit.

Values are strings, numbers, booleans, or null. Use strings for identifiers and exact status labels. Prefer one row per atomic decision. Put URLs in explicit `Source` or `Reference` columns where possible.

The workbook is reproducibly rebuilt from this file with semantically and structurally equivalent sheets, values, controls, and formatting. Byte identity is not guaranteed because the workbook library may generate nondeterministic package metadata or relationship identifiers; claim deterministic bytes only after two fresh independent builds match. Status values must include every value used in a status column. Do not add study logic to the generic builder.
