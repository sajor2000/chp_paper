---
title: Data sources and variables
description: Source roles, measures, periods, geographies, and variables used in the review analysis.
---

# Data sources and variables

## Chicago Health Map and CAPriCORN

The primary source was Chicago Health Map aggregate data derived from
participating CAPriCORN health systems. The study team specified the annual crude
diagnosed proportion as:

> unique adults diagnosed with the condition ÷ unique CAPriCORN adults observed
> that year with at least 1 of the represented conditions.

The upstream process was described as deduplicating adults across participating
systems within each year. The review analysis received only aggregate
geography-condition-year records and could not independently reconstruct the
person-level deduplication sequence.

### Primary fields used

| Field group | Use |
|---|---|
| `geography_id`, `geography_type`, `time_period` | Define tract or community-area records and annual period |
| `condition_id` | Identify hypertension, COPD, and the 2 separate diabetes components |
| `numerator`, `denominator` | Construct annual and pooled diagnosed proportions |
| suppression and observable-value fields | Separate usable values from missing or unresolved zero/suppression states |
| tract eligibility and boundary fields | Construct the primary Chicago tract frame |
| community-area and ZCTA linkage fields | Attach direct coarser-area labels without mathematically aggregating tract disease values |
| capture fields | Describe participating-system coverage and support the locked ecological adjustment set |

## Public comparison and contextual sources

| Source | Geography and period | Role | Interpretation boundary |
|---|---|---|---|
| CDC PLACES 2025 release | Census tract, source periods documented by CDC | Secondary tract-level concordance | Model-based small-area estimate, not a gold standard |
| Healthy Chicago Survey | Community area, rolling 2023–2024 | Hypertension rank triangulation | Self-reported survey estimate with sampling standard error |
| Chicago Health Atlas life expectancy | Community area, aligned 2022–2024 | Supplementary ecological outcome | Area-level outcome, not individual survival |
| ACS 5-year | Tract and derived community-area covariates | Age, sex, poverty, and population context | Sixty-month estimates with release-specific margins of error |
| Census TIGER/Line | 2019, 2020, 2023, and 2024 tract vintages | Geography and vintage control | Tract vintages cannot be joined silently |
| City of Chicago community areas | Official 77-area layer | Community-area geometry | Used to define the Chicago analysis frame |

## Adjustment variables

The locked supplementary ecological adjustment set was:

- percentage aged 65 years or older;
- percentage female;
- percentage below the federal poverty level; and
- mean Chicago Health Map capture rate for 2022–2024.

Adult population was retained for weighting sensitivities, not included as a
routine covariate in the principal unweighted ecological model.

## Data that were deliberately not combined

Diabetes with complication and diabetes without complication remained separate.
The review analysis did not add their numerators or denominators because the
available source documentation did not establish mutual exclusivity and
denominator equivalence.
