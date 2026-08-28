# Socrata acquisition adapter and frozen-snapshot compatibility

## Problem

The source registry approved exactly two Socrata datasets: CDC PLACES tract estimates
(`yjkw-uj5s`) and Chicago community-area boundaries (`igwz-8jzy`). The inherited 2026-07-13
files were source-faithful downloads protected by the repository-wide checksum inventory, but
they predated the current per-source `SnapshotWriter` manifest layout. Re-downloading would add
unnecessary source drift and would violate the frozen-snapshot preference.

## Evidence and decision

The adapter now binds metadata identity, exact selected field types, registered query, primary
key, and response schema before accepting pages. It uses the shared bounded HTTP transport, a
separate filtered count, fixed 50,000-row pages, deterministic primary-key ordering, and fatal
duplicate/count/order/schema/content-type/geometry checks. The optional `SOCRATA_APP_TOKEN` is
a runtime-only header. GeoJSON is structurally parsed and must be valid, nonempty, polygonal,
and finite.

The PLACES request is restricted to Illinois Cook County tracts and only source identifiers,
population fields, and the source-native `bphigh`, `diabetes`, and `copd` crude-estimate and
95% CI columns. These source field IDs and Socrata data types are preserved. The request
manifest records the 2025 release/model inputs and labels the values as **model-based small-area
estimates, not observed prevalence**. No additional PLACES measures are requested.

The Chicago request is restricted to `igwz-8jzy` and preserves `the_geom`, `area_numbe`,
`community`, `area_num_1`, `shape_area`, and `shape_len`, together with the raw metadata's City
attribution, catalog ID, update timestamp, license, and multipolygon type. No police, 311,
pharmacy, WIC, or other service layer is registered or fetched.

## Rejected alternatives

- A live refresh was rejected because neither corruption nor documented drift was found.
- A 100,000-row PLACES request was rejected because the approved paging contract is 50,000.
- Implicit API order was rejected because Socrata documents that paged results are not
  implicitly stable.
- Copying the inherited files into a new synthetic snapshot was rejected because it would
  mutate provenance and imply a new retrieval date.

## Legacy compatibility and verification

`verify_frozen_socrata_snapshot` checks every relevant inherited file against
`sources/public/CHECKSUMS.sha256`, then validates dataset identity and content semantics. The
PLACES legacy CSV remains byte-for-byte unchanged with 3,258 unique Illinois tract rows and its
original wide 40-measure layout; verification requires consistent Illinois county/tract IDs,
finite required model estimates, unique keys, stable row fields, and a Cook County subset. Those
extra legacy columns remain historical raw bytes and are not the future selected query. The
Chicago GeoJSON remains byte-for-byte unchanged with exact IDs 1–77, exact required properties,
and structurally valid polygonal geometry. Both legacy
directories lack per-source `manifest.json`/`checksums.sha256`; the repository-wide checksum
inventory is therefore the documented compatibility boundary.

The CLI dry-run uses `SocrataAdapter.plan`. Non-dry execution accepts only the 2026-07-13 date,
verifies the inherited bytes, reports reuse, and performs no network download. A future live
refresh requires an explicit policy change after corruption or documented source drift.

## Reusable pattern

When a trustworthy frozen artifact predates a new immutable-snapshot layout, verify the old
layout in place against its original checksum authority, document the compatibility boundary,
and make the acquisition CLI reuse it without republishing. New adapter behavior can be fully
tested with synthetic responses without rewriting historical bytes.

## Gate status

This work supplies the Socrata component of Phase 4. **Gate 4 remains open** pending the other
registered public-source adapters, cross-source harmonization, and the complete Phase 4 review.
