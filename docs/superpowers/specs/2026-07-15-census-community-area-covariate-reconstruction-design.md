# Census Community-Area Covariate Reconstruction Design

**Date:** 2026-07-15  
**Status:** Approved and implemented
**Scope:** Reconstruct four governed 2020–2024 ACS covariates for Chicago's 77 community areas without relying on undocumented Chicago Health Atlas transformations.

## Decision

The pipeline will derive `pct_female`, `pct_age_65_plus`, `pct_below_fpl`, and `acs_adult_population` from frozen official Census inputs. Chicago Health Atlas values remain a secondary comparison dataset and never become the source of record for these covariates.

The reconstruction will not area-weight percentages or assign whole census tracts to community areas. It will allocate tract-level ACS component counts through 2020 Census block population distributions, aggregate allocated component counts to community areas, and calculate percentages only after aggregation.

## Alternatives considered

1. **Population-weighted block allocation (selected).** Allocate every ACS sex-age component using matching 2020 Decennial Census block sex-age counts within its tract. This is reproducible, preserves numerator/denominator structure, avoids direct area-weighting of rates, and supports explicit diagnostics.
2. **City of Chicago tract-area algorithm (rejected).** The City publishes an adjacent community-area ACS product whose notebook weights tract estimates by polygon overlap. This is not the documented Atlas method and conflicts with the SAP prohibition on area-weighting percentages or unsupported tract aggregation.
3. **Atlas values as final covariates (rejected for primary use).** The Atlas extract is complete and mechanically usable, but its source geography, allocation method, boundary vintage, fractional counts, count uncertainty, and age-65 discrepancy remain undocumented.

## Authoritative inputs

All inputs will be acquired from official, credential-free endpoints and frozen with URLs, access time, response identity, byte count, SHA-256, and release metadata.

- 2024 ACS 5-year detailed-table estimates for Illinois census tracts:
  - B01001, Sex by Age.
  - B17001, Poverty Status in the Past 12 Months by Sex by Age.
- 2024 ACS 5-year variance replicate estimates for B01001 and B17001 at tract level when the tables and tract summary level are available.
- 2020 Decennial Census P12, Sex by Age, at census-block level for Cook County.
- 2020 TIGER/Line census-block geometry or official internal-point coordinates and the official block-to-tract identity encoded in block GEOIDs.
- Frozen City of Chicago community-area boundaries already registered by the project, with their source and access vintage retained.

The pipeline must fail closed if any registered input changes identity, contains incomplete Chicago coverage, or cannot be matched to the expected release and geography.

## Geographic allocation

Each 2020 Census block will be assigned to exactly one Chicago community area using its official Census internal point against the frozen community-area polygons. Internal-point assignment is a whole-block rule; polygon overlap is used only to audit boundary-crossing blocks, never to weight ACS values.

Within each tract, each ACS B01001 estimate cell will be allocated to blocks in proportion to the matching P12 sex-age block count. B17001 cells will use the closest exact sex-age P12 partition supported by the two tables. When an ACS category spans multiple P12 categories, the matching P12 categories will be summed before weights are calculated.

For a tract/component pair, block weights must be finite, nonnegative, and sum to one across eligible Chicago blocks. A zero ancillary-population denominator is a hard diagnostic: the implementation may use total tract block population only if the component estimate is also zero; otherwise it must fail rather than silently invent a distribution.

Allocated component counts are summed by community area. Percentages are then derived from allocated counts:

- `pct_female = 100 * female_population / total_population`.
- `pct_age_65_plus = 100 * population_age_65_plus / total_population`.
- `pct_below_fpl = 100 * population_below_fpl / population_for_whom_poverty_status_is_determined`.
- `acs_adult_population = population_age_18_plus` from B01001 components.

The poverty field will retain the exact B17001 universe and must not be labeled as a percentage of all residents.

## Uncertainty

When Census variance replicate estimates are available, the same fixed block-allocation weights will be applied independently to the published estimate and all 80 replicate estimates. Community-area covariates will be recalculated for every replicate, and standard errors and 90% margins of error will be derived using the Census replicate-table formula. This preserves covariance among cells represented by the replicate estimates.

If the required replicate table or tract summary level is unavailable, the corresponding uncertainty field will remain missing with a machine-readable `unavailable_no_variance_replicates` reason. Approximate root-sum-of-squares uncertainty may be reported only as a separately labeled diagnostic; it cannot silently replace replicate-based uncertainty.

## Quality gates

The derived table must satisfy all of the following before dataset integration:

- exactly 77 unique community areas with IDs 1 through 77;
- no missing or nonfinite required covariates;
- no negative count, numerator, or denominator;
- percentages between 0 and 100;
- adult population not greater than total population;
- component and allocation weights reconcile within explicit floating-point tolerances;
- every contributing tract and block has frozen source lineage;
- block assignment is one-to-one, with crossing and boundary-touch diagnostics retained;
- totals reconcile to the Chicago portion of the tract inputs, with residuals reported;
- direct comparison against Atlas and the separate City product is descriptive only and cannot redefine the Census-derived values;
- the governed analysis dataset remains `results_authorized=false` and adjusted primary models remain unexecuted.

## Pipeline integration

A focused external-data module will build a 77-row covariate artifact plus schema, field-lineage, allocation-diagnostic, uncertainty, and comparison artifacts. The analysis dataset builder will join these fields one-to-one by normalized community-area ID and will fail closed on duplicate, missing, or out-of-scope rows.

The notebook readiness table may change from `withheld_missing_covariates` to a mechanically ready status after integration. That status is not results authorization. Model execution remains controlled by the existing S4–S7 governance sequence and human review.

## Testing

Implementation will follow test-driven development. Unit tests will cover variable-cell mappings, block weights, zero-population behavior, replicate calculations, ratios, and validation failures. Integration tests will freeze miniature tract/block/community fixtures and verify deterministic 77-row output contracts. Existing offline rebuild, dataset, notebook, provenance, privacy, and authorization tests must remain green.

## Recorded limitations

This is a transparent small-area estimation procedure, not a direct Census-published community-area estimate. The implemented production build uses one fixed within-tract weight based on 2020 PL 94-171 P1 total block population for every ACS component. The planned P12 sex-age ancillary file could not be acquired through the credential-free Census API, which returned the recorded `Missing Key` response, and the downloaded DHC archive was therefore not used to claim unavailable sex-age weights. The P1 fallback preserves component numerators and denominators, applies the same geography rule to all 80 replicates, and is explicitly labeled in every output row and manifest. It assumes that the 2020 total block population distribution is an appropriate ancillary distribution for 2020–2024 tract estimates. Whole-block internal-point assignment, 42 zero-population edge blocks, boundary diagnostics, and Atlas/City comparisons remain disclosed limitations rather than hidden transformations.
