# Census acquisition adapters

## Problem

The approved plan required exact ACS group requests and validated TIGER/Line geometry,
while the inherited 2026-07-13 Census evidence was already frozen in an authoritative
bulk layout. Re-fetching would have discarded useful provenance and risked representing
new bytes as the historical acquisition.

## Evidence

- All 56 Census checksum records match their files: 52 ACS artifacts and four TIGER ZIPs,
  totaling 1,696,367,614 bytes.
- All four TIGER ZIPs pass CRC inspection and use the official Illinois tract filenames.
- The legacy ACS evidence contains the 2019 sequence-based and 2022/2024 table-based
  releases, not one API JSON response per group.
- Ref MCP returned no result for the version-specific Pyogrio query. Official Pyogrio,
  GeoPandas, and Arrow documentation plus installed signatures were used as the recorded
  fallback.

## Decision

Implement the new adapters as independently testable contracts without mutating or
re-fetching the frozen evidence. The ACS adapter constructs exact Cook County tract group
requests, reads an optional key only from `CENSUS_API_KEY`, disables redirects, preserves
raw JSON, and embeds typed, ordered, credential-free per-group request provenance directly
in `manifest.json` while retaining auditable sidecars. The TIGER adapter accepts an
explicit local archive, validates it before copying, preserves the statewide ZIP before
filtering, and writes original-CRS Cook County GeoParquet with provenance only.

The source CLI exposes these contracts in dry-run mode and rejects live Census fetches by
default. Existing frozen bytes remain classified as verified legacy snapshots.

## Rejected alternatives

- Re-downloading the sources: unnecessary because checksum and container validation found
  no corruption or documented drift.
- Rewriting bulk files into synthetic API responses: would destroy acquisition truth.
- Filtering or extracting before preserving the ZIP: would lose the statewide authority
  file and make the Cook subset impossible to audit independently.
- Reprojecting in the adapter: belongs to the explicit geography-harmonization phase.

## Verification

Fixture tests cover exact ACS queries, unique 11-digit GEOIDs, margins of error,
header/row failure, typed manifest provenance, credential redaction, redirect refusal,
all registered TIGER filenames, one coherent Shapefile component set, archive safety,
exact and unique geography identifiers, nonnull/nonempty/valid polygon geometry,
ZIP-before-filter order, original CRS, provenance, and staging-alias cleanup. Full-suite,
lint, type, frozen-checksum, and secret-scan results are recorded in the Task 13 execution
report.

## Reusable pattern

When an inherited immutable snapshot differs from a newly approved adapter format,
validate and label the inherited format explicitly. Test the new contract with synthetic
fixtures, refuse silent mutation, and keep format migration separate from source
provenance.
