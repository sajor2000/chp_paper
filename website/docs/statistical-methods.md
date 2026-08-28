---
title: Statistical methods
description: Estimation, uncertainty, diagnostics, spatial analyses, and sensitivities.
---

# Statistical methods

## Primary descriptive analysis

The primary analysis compared direct tract-level and direct community-area
Chicago Health Map values for hypertension and COPD. It reported:

- eligible tract counts;
- within-community variance share;
- Spearman rank correlation;
- median absolute percentile-rank gap;
- exact quartile agreement and disagreement;
- movement into or out of Q4; and
- quadratic weighted kappa and Gwet AC1.

Combined diabetes was not analyzed because the 2 source components could not be
shown to be mutually exclusive with equivalent denominators.

## Cluster bootstrap uncertainty

The uncertainty analysis resampled the 77 community areas with replacement and
retained all member tracts. Ranks and classification statistics were recomputed
inside each replicate. The final analysis used:

- 1000 replicates;
- random seed `20260715`; and
- percentile 95% intervals defined by the 2.5th and 97.5th percentiles.

This preserves within-area clustering. It does not completely represent spatial
dependence or uncertainty in the source estimates themselves.

## Geographic sensitivity

The tract-versus-coarser-area comparison was repeated with direct Census ZCTA
values and documented dominant tract-ZCTA links. ZCTA is a Census statistical
geography and was not described as a USPS ZIP Code.

## Cross-source triangulation

CDC PLACES tract estimates and Healthy Chicago Survey community-area estimates
were used to examine whether distinct data systems similarly ordered places.
The analyses did not treat either public source as a gold standard.

For Healthy Chicago Survey hypertension, the analysis reported Spearman
correlation, median absolute percentile-rank gap, and exact quartile agreement
across 77 pairwise-complete community areas. Survey standard errors were shown.
No joint-source confidence interval was constructed because compatible Chicago
Health Map uncertainty was unavailable.

## Supplementary ecological model

The COPD model estimated the community-area mean difference in aligned
2022–2024 life expectancy associated with a 1-IQR higher pooled COPD diagnosed
proportion, adjusted for the locked covariate set. The model used unweighted
ordinary least squares with HC3 covariance.

The model was checked for design rank, exposure variation, variance inflation,
pairwise correlation, finite covariance, residual patterns, influence, and
residual spatial autocorrelation. It remained supplementary and ecological.

The generated model artifact used a 97.5% exposure interval and 95% adjustment
intervals. This mismatch is disclosed. A manuscript sensitivity should
harmonize all intervals to 95%.

## Spatial analyses

Supplementary spatial analyses used row-standardized queen-contiguity weights
and 9999 permutations. They included Global Moran I, local Moran I, Getis-Ord
statistics, and a spatial-error sensitivity where indicated. Benjamini-Hochberg
correction was applied within declared local-test families.

Spatial statistics described residual or local structure. They did not identify
geographic mechanisms or causal effects.

## Sensitivity analyses

The final package records annual estimates, leave-one-year-out summaries,
noncrossing-tract restrictions, ZCTA comparison, population weighting for the
ecological model, alternative spatial weights, spatial-error modeling, and the
status of the incomplete 50%-area tract frame.
