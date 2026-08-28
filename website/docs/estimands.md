---
title: Estimands and decision rules
description: Mathematical definitions of the primary geographic-resolution measures.
---

# Estimands and decision rules

Each estimand answers a different part of the geographic-resolution question.
No single statistic is treated as definitive by itself.

## Within-community variance share

For tract value $y_{ij}$ in community area $j$, the observed-scale
method-of-moments decomposition estimates between-area variance
$\hat\sigma_B^2$ and within-area variance $\hat\sigma_W^2$. The reported
within-community share is:

```math
\frac{\hat\sigma_W^2}{\hat\sigma_B^2 + \hat\sigma_W^2}.
```

A value near 0 indicates that community-area labels retain most observed tract
variation. A larger value indicates more heterogeneity among tracts assigned to
the same community area.

## Percentile-rank gap

Within each condition-specific eligible tract population, average ranks were
scaled to $(0,1]$. The absolute rank gap was:

```math
\left|R^{tract}_{ij} - R^{area}_{ij}\right|.
```

This compares relative position, not absolute percentage-point agreement.

## Quartile disagreement

Fixed rank boundaries defined Q1 through Q4 at 0.25, 0.50, and 0.75. Exact
agreement required the tract and linked coarser-area label to fall in the same
quartile. The disagreement proportion was:

```math
\frac{\#\{Q^{tract}_{ij} \ne Q^{area}_{ij}\}}{n}.
```

Average ranks resolved ties before applying the fixed boundaries.

## Highest-quartile movement

The analysis counted tracts that moved into or out of Q4 after applying the
coarser-area label. This was prespecified because the highest category is often
used for prioritization. It remains a classification consequence, not a service
need or intervention rule.

## Concordance measures

- Spearman correlation described rank alignment.
- Quadratic weighted kappa described ordinal quartile agreement.
- Exact agreement reported the directly interpretable matched proportion.
- Unweighted Gwet AC1 was retained as a nominal sensitivity.

## Area-label AUC

Leave-one-tract-out area-label AUC described whether tract values separated area
labels after removing each tract from its own area summary. It was exploratory.
It did not evaluate patient prediction, clinical discrimination, or external
validity.
