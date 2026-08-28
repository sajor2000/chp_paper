---
id: overview
title: Study methods at a glance
slug: /
sidebar_position: 1
description: A concise map of the Chicago Health Map geographic-resolution study.
---

# Study methods at a glance

This site explains what we studied, which data we used, how we constructed the
analytic populations, why each statistical method was selected, and how to
reproduce the final aggregate analysis.

## The central question

Among Chicago census tracts with usable 2022–2024 Chicago Health Map data, do
direct tract-level EHR-diagnosed proportions retain geographic information that
is not conveyed by a direct community-area label for the same condition and
period?

The study evaluates **geographic resolution**, not whether Chicago Health Map is
a substitute for population surveillance. Chicago Health Map describes
diagnoses recorded among adults observed in participating CAPriCORN health
systems. It does not estimate disease prevalence among all Chicago residents.

:::info The paper's scientific pitch

Health-system research data can supplement public-health surveillance by
showing clinically recorded variation within larger reporting areas. The value
is complementary. Population-based public-health data remain the basis for
population inference.

:::

## What we did

1. Audited source definitions, denominators, suppression, geography, and years.
2. Defined a primary Chicago tract frame and condition-specific eligibility.
3. Pooled annual EHR counts by summing numerators and denominators before division.
4. Compared direct tract values with direct community-area labels.
5. Quantified within-area heterogeneity, rank gaps, quartile disagreement, and movement into or out of the highest quartile.
6. Used community-area cluster bootstrap intervals for dependence among tracts in the same area.
7. Repeated the classification comparison with Census ZCTAs as a geographic sensitivity.
8. Used CDC PLACES and Healthy Chicago Survey data for cross-source triangulation, not validation.
9. Examined supplementary ecological life-expectancy and spatial models.
10. Preserved all inputs and outputs through SHA-256 checksums and deterministic notebook builds.

## Main analysis boundary

| Component | Final role |
|---|---|
| Tract versus community-area comparison | Primary geographic-resolution analysis |
| Tract versus ZCTA comparison | Prespecified geographic sensitivity |
| CDC PLACES concordance | Secondary cross-source context |
| Healthy Chicago Survey hypertension | Secondary community-area triangulation |
| Area-label AUC | Exploratory separation measure |
| Life-expectancy and spatial models | Supplementary ecological analyses |
| Combined diabetes | Excluded because mutual exclusivity and denominator equivalence were not documented |
| 2025 holdout and external network | Prespecified future replication analyses |

Use the navigation at left for the complete data and statistical specification.
