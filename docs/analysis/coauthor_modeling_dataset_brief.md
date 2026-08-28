# Co-Author Brief: Modeling & Dataset Plan

**Study:** Do directly-measured Chicago Health Map (CHM) census-tract EHR-diagnosed patterns add information that *complements* — is aligned with but not interchangeable with — public health comparators and community-area life-expectancy summaries?

**Target journal:** JAMA Health Forum, Original Investigation (cross-sectional / ecological; ≤3000 words, ≤5 main displays, structured abstract, Key Points, STROBE/RECORD).

**Status:** Internal co-author review only. Results are **not authorized** for release; numbers below are preliminary and for our discussion.

**What we need from you:** a thumbs-up on three decisions in Section 6.

---

## 1. The "so what" (why this matters)

Chicago has up to a **~30-year life-expectancy gap** between neighborhoods. The tools communities and health departments use most — the **Chicago Health Atlas (77 community areas)** and **ZIP-code summaries** — average health over large areas. A single community-area number can hide very different blocks inside it. Even **CDC PLACES**, which publishes census-tract estimates, produces them from a statistical *model* of survey data that pulls each tract toward its demographic average, so it can miss a genuinely unusual small area.

The Chicago Health Map measures something different: the **directly-observed, EHR-diagnosed proportion** of a condition among ~2.8M adults seen across **7 Chicago health systems (CAPriCORN)**, reported at the **census-tract** level. Our question is not "which source is right" — it's whether the CHM tract lens **adds a layer** the public summaries can't show, so communities can ask sharper questions about their own blocks.

**Framing guardrail:** we claim **complementarity**, not superiority, validation, true prevalence, causation, underdiagnosis, or unmet need. Language is always "diagnosed proportion among observed adults" and "was associated with."

---

## 2. What we did (in plain terms)

- Built one governed analytic dataset joining CHM tract + community-area EHR-diagnosed proportions to public comparators.
- Chose **two case studies** that drive the life-expectancy gap and exist in every source, so head-to-head comparison is possible:
  - **Case 1 — Cardiometabolic:** hypertension + diabetes.
  - **Case 2 — Respiratory:** COPD.
- For each, we compare the CHM tract pattern against **CDC PLACES** (tract) and against **community-area life expectancy** (Chicago Health Atlas), and we measure how much neighborhood detail is lost when tracts are averaged up to community areas.

**Preliminary internal signal (not for release):** roughly **half** the tract-level variation in diabetes (~51%) and COPD (~45%) lives *inside* community areas — invisible at the community-area scale — versus only ~24% for hypertension. CHM and PLACES rank tracts similarly (Spearman 0.6–0.85) but differ in level, as expected for diagnosed-vs-modeled measures. This is why we lead the "hidden micro-community" story with diabetes and COPD.

---

## 3. How we built it (dataset)

| Piece | Detail |
|---|---|
| Primary source | CHM / CAPriCORN EHR-diagnosed proportions (7 systems, ~2.8M adults, 2019–2024), tract + 77 community areas |
| Public comparators | CDC PLACES (tract, model-based); Chicago Health Atlas life expectancy & mortality (community area) |
| Reference & geography | ACS 5-year (population, covariates); Census TIGER tracts; official 77-community-area boundaries; CDC/ATSDR SVI |
| Contract | 22,540 rows × 90 columns; 20,692 tract + 1,848 community-area records; unique geography–period–condition key; **direct CHM values never interpolated** |
| Governance | Frozen source snapshots + checksums; deterministic two-run reproducibility; per-tract **reliability tiers** (capture rate) and equity notes; small-cell suppression (<10) |
| Outputs | Parquet/CSV, schema, column lineage, source-join manifest, data book — all versioned |

**Why this build matters:** every number traces to a frozen source and a code commit, so the analysis is reproducible and auditable — a requirement for JAMA/RECORD and for responsibly publishing clinical-network data.

---

## 4. The analytic plan (models) — proposed

We propose leading with the **descriptive complementarity** layer (fully supportable, no strong assumptions) and treating the life-expectancy models as a secondary "so-what" bridge.

**Core (descriptive — the primary contribution):**
1. **Variance partition (VPC/ICC) + discriminatory accuracy** — how much tract variation is hidden inside community areas, and how poorly a community-area label predicts its own tracts. *(Established "averages-to-heterogeneity" method; Merlo 2026.)*
2. **Concordance / discordance vs PLACES** — rank agreement (Spearman), agreement categories, with **uncertainty propagated** (PLACES CIs + ACS margins) so divergence isn't just noise.
3. **Scale (MAUP) sensitivity** — the same metrics recomputed at tract vs community-area vs ZIP, showing the picture changes with the unit.

**Spatial (supplement):**
4. **Local clustering (LISA / Gi\*, bivariate EHR×PLACES) and spatial scan** — where hotspots appear at tract scale and disappear when averaged up.

**Life-expectancy bridge (community area, secondary):**
5. **C1 cardiometabolic** and **C2 COPD** associations with community-area life expectancy (OLS, robust SEs, spatial checks). **Honest status:** C1 is currently *withheld* (statistical collinearity above our prespecified limit); C2 is a *candidate*. We present these transparently rather than overstate them. *(Optional fix for C1: combine hypertension + diabetes into one cardiometabolic index — requires a plan amendment.)*

---

## 5. Why it's helpful (who uses it, and its limits)

- **FQHCs / community organizations:** a block-level lens to ask where to look, compare to their own panels, and pair with local knowledge.
- **Researchers / health departments:** a reproducible, tract-level clinical-data complement to survey products.
- **Honest limits:** ecological (neighborhoods, not people); diagnosed ≠ true prevalence; coverage varies by neighborhood (reliability flags); discordance is *measurement difference*, not error or unmet need.

---

## 6. Decisions we're asking co-authors to approve

1. **Lead with the tract complementarity story** (descriptive), with the life-expectancy models as a secondary bridge — because that's where the evidence is strongest and fully reportable.
2. **Add the methods in Section 4** (variance partition + discriminatory accuracy, uncertainty-propagated concordance, scale sensitivity, spatial supplement).
3. **C1 handling:** present as withheld, **or** amend the plan to use a combined cardiometabolic index so a result can be reported.

*(Optional, for the stats-minded: full specifications, gates, and citations are in `statistical_analysis_plan.md` and `analytic_plan_status_and_next_steps.md`.)*
