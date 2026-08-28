# Methods discrepancies

1. **exported zero values versus website `<10` suppression language**

   Task 8 observation (2026-07-14): all five 67-field condition-stat exports contain
   literal zero values, but the absence of an owner-supplied positional schema means
   neither numerator positions nor suppression encoding can be established from those
   values alone. The website archive says suppressed values display as `N/A` or `<10`,
   but that interface statement does not define the headerless export encoding.

   Status: `guarded`; the website glossary is now authoritative for the public
   fewer-than-10 display rule, and the S4 packet maps the total and subgroup count
   blocks. No dedicated raw suppression-state flag is mapped, so public outputs must
   apply the glossary rule and cannot treat small literal values as publication-ready
   without tested suppression handling.

2. **website claim of direct age standardization versus reconstructability from released strata**

   Task 8 observation (2026-07-14): each condition-stat export has exactly 67 fields,
   consistently shaped across every row. Repeated numeric patterns are insufficient to
   assign any position to the archived site's seven stated age strata, and the archive
   does not give export column order.

   Status: `unresolved`; the S4 packet identifies the count, denominator-like, and
   rate/proportion-like blocks, but subgroup labels and age-standardization
   reconstructability cannot be evaluated until subgroup positions are explicitly
   identified or excluded from the analytic contract.

3. **website statement of 38 conditions plus firearm violence versus the observed condition-domain count**

   Task 8 observation (2026-07-14): `dim_conditions.text` contains 39 rows and 11 fields
   per row, consistent in count with the website statement of 38 chronic conditions plus
   firearm violence. Because the headerless positions have no owner-supplied schema,
   row count agreement does not verify condition identifiers, active-state semantics, or
   one-to-one membership.

   Status: `guarded`; count concordance plus website authority supports S4 condition
   mapping for the case-study frame. Exact phenotype construction details—lookback,
   encounter requirements, residence anchor, and condition-specific exclusions—remain
   unresolved for manuscript methods and sensitivity planning.

4. **empty `drug_providers.text`/`wic_locations.text` exports**

   Task 8 observation (2026-07-14): both files contain exactly zero rows and zero bytes in
   the preserved 2026-05-27 snapshot. They are declared `empty_expected: true` for this
   snapshot so the absence is handled explicitly, not silently. This declaration
   describes observed delivery and does not claim that the source tables are intended
   to be empty.

   Status: `unresolved`; intended schemas and expected production population require
   owner confirmation.

The S4 mapping packet now narrows the discrepancies: geography, condition key,
annual time, total count, paired denominator/rate blocks, and reliability-display
positions are defensible for guarded S4 case-study mapping. Suppression state,
subgroup labels, aggregate denominator semantics, SMD numerics, and phenotype
construction remain unresolved or guarded. Gate 3 remains closed for broad
analysis-ready ingestion because the schema catalog is intentionally not promoted
until tested downstream code applies these boundaries.

Task 9 checkpoint (2026-07-14): the strict parser and quality rules were exercised only
against synthetic, fully verified contracts. The real-snapshot CLI inspected catalog
evidence counts before source bytes, found 549 unverified positions, read zero source
rows, wrote no Parquet, and exited nonzero. Consequently Task 9 supplies no new empirical
count or disposition that could resolve any discrepancy above.
