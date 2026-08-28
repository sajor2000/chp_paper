---
title: Analytic cohort and denominators
description: Eligibility, exclusions, pooling, suppression, and geographic linkage.
---

# Analytic cohort and denominators

## Unit of analysis

The primary unit was an aggregate census-tract record for a named condition and
period. Tracts were nested within community areas for the primary uncertainty
analysis. Supplementary outcome models used the community area as the unit and
contained at most 77 observations.

No patient-level rows, encounters, addresses, dates of service, diagnosis codes,
or identifiers are included in the analysis notebooks or this website.

## Chicago tract frame

The primary frame used 2024 TIGER tracts whose representative points were
covered by the frozen union of Chicago's 77 community areas. Of 867 tracts with
any intersection, 782 met this rule. An any-intersection rule was rejected
because boundary slivers can include tracts with negligible Chicago area.

A separate 50% tract-area definition identified 779 tracts and agreed with the
primary rule for 777. The complete alternative-frame rerun requires 2 tracts
that were absent from the primary-prefiltered analytic file.

## Annual eligibility

An annual tract-condition record entered pooled estimation when:

1. the tract met the Chicago boundary rule;
2. the numerator and denominator were present;
3. the annual captured-adult denominator was at least 30; and
4. the value remained observable after the source suppression rule.

A stored zero was excluded because the aggregate export could not distinguish a
true zero from a suppressed value. Missing, suppressed, unresolved zero, and
true zero were not treated as interchangeable states.

## Period pooling

The primary period was 2022–2024. A tract-only estimand required all 3 eligible
annual records. The pooled proportion was:

```math
100 \times \frac{\sum_{t=2022}^{2024} N_{jt}}
{\sum_{t=2022}^{2024} D_{jt}},
```

where $N_{jt}$ and $D_{jt}$ are the annual numerator and denominator for
geography $j$. This is not an unweighted mean of annual percentages and is not
a unique-person 3-year prevalence measure.

## Coarser-area linkage

The primary comparison joined each eligible tract to its dominant community
area and attached the **direct community-area Chicago Health Map value**. The
tract disease values were not aggregated to recreate the community-area value.
The ZCTA sensitivity used the same direct-value principle.

Cross-source analyses used separate pairwise-complete populations. Missing CDC
PLACES data could not remove a tract from a Chicago Health Map-only estimand.
