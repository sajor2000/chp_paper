"""Evidence-bound tables and figure data for the JAMA-structured master notebook."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd  # type: ignore[import-untyped]
from scipy import stats  # type: ignore[import-untyped]

from chicagohealthmap.analysis.case_studies import CaseStudyAnalysisError
from chicagohealthmap.analysis.sap_analyses import COPD, GovernedModelResult

if TYPE_CHECKING:
    import geopandas as gpd  # type: ignore[import-not-found,import-untyped]


# The manuscript has exactly five primary displays.  Keeping this contract in
# the display module lets the notebook and export code validate the same order.
MAIN_DISPLAY_IDS = ("table_1", "figure_1", "figure_2", "figure_3", "table_2")

READER_ANALYSIS_NAMES = {
    "C1": "Cardiometabolic joint analysis",
    "C2": "COPD association analysis",
}


def reader_analysis_name(model_id: str) -> str:
    """Return the descriptive name used in reader-facing displays."""

    try:
        return READER_ANALYSIS_NAMES[model_id]
    except KeyError as exc:
        raise CaseStudyAnalysisError(f"unknown internal analysis id: {model_id}") from exc


def draw_flow_panel(
    axis: Any,
    coverage: pd.DataFrame,
    *,
    case_denominators: Mapping[str, int],
) -> None:
    """Render Figure 1's non-additive source-flow panel.

    C1 and C2 use overlapping community-area populations.  They are therefore
    rendered as branches from the shared pooled-area stage rather than summed
    into an apparent analytic denominator.
    """

    flow = build_flow_summary(coverage, case_denominators=case_denominators)
    source = int(flow.loc[flow["stage"].eq("source_condition_year_records"), "count"].iloc[0])
    eligible = int(flow.loc[flow["stage"].eq("eligible_condition_year_records"), "count"].iloc[0])
    suppressed = int(flow.loc[flow["stage"].eq("suppressed_or_missing_records"), "count"].iloc[0])
    pooled = int(flow.loc[flow["stage"].eq("pooled_community_areas"), "count"].iloc[0])
    c1 = int(flow.loc[flow["branch"].eq("C1"), "count"].iloc[0])
    c2 = int(flow.loc[flow["branch"].eq("C2"), "count"].iloc[0])
    stages = (
        ("Source\ncondition-year\nrecords", source, "#2166AC"),
        ("Eligible\ncondition-year\nrecords", eligible, "#1A9850"),
        ("Pooled\ncommunity areas", pooled, "#762A83"),
    )
    axis.set(xlim=(-0.5, 3.7), ylim=(0, 1))
    for index, (label, count, color) in enumerate(stages):
        axis.text(
            index,
            0.56,
            f"{count:,}",
            ha="center",
            va="center",
            fontsize=10,
            fontweight="bold",
            color="white",
            bbox={"boxstyle": "round,pad=0.45", "facecolor": color, "edgecolor": "#333333"},
        )
        axis.text(index, 0.22, label, ha="center", va="center", fontsize=7)
        if index < 2:
            axis.annotate(
                "",
                xy=(index + 0.38, 0.56),
                xytext=(index + 0.18, 0.56),
                arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.2},
            )
    for y, label, count in (
        (0.70, "Cardiometabolic joint analysis\nwithheld for collinearity", c1),
        (0.38, "COPD association analysis\ncandidate adjusted estimate; not authorized", c2),
    ):
        axis.annotate(
            "",
            xy=(2.65, y),
            xytext=(2.25, 0.56),
            arrowprops={"arrowstyle": "->", "color": "#333333", "lw": 1.0},
        )
        axis.text(
            3.05,
            y,
            f"{count}\n{label}",
            ha="center",
            va="center",
            fontsize=7,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "#E69F00", "edgecolor": "#333333"},
        )
    axis.text(
        0.02,
        0.95,
        f"Capture: {eligible:,}/{source:,} eligible; suppressed/missing={suppressed:,}",
        transform=axis.transAxes,
        fontsize=6.5,
        va="top",
    )
    axis.set_title("A. Source → eligibility → pooled overlapping analysis populations", fontsize=9)
    axis.set_axis_off()


def draw_map_panel(
    axis: Any, coverage: "gpd.GeoDataFrame", column: str, title: str, cmap: str
) -> None:
    """Render a qualification-safe map with a readable missingness legend."""

    from matplotlib.patches import Patch

    observed = coverage.loc[coverage[column].notna()]
    missing = coverage.loc[coverage[column].isna()]
    coverage.plot(ax=axis, color="#eef2f6", edgecolor="white", linewidth=0.4)
    if not observed.empty:
        observed.plot(
            ax=axis,
            column=column,
            cmap=cmap,
            edgecolor="white",
            linewidth=0.4,
            legend=True,
            legend_kwds={
                "label": "EHR-diagnosed proportion (%)",
                "orientation": "horizontal",
                "shrink": 0.68,
                "pad": 0.01,
            },
        )
    if not missing.empty:
        missing.plot(ax=axis, color="#fecaca", edgecolor="#991b1b", hatch="xxx", linewidth=0.6)
        axis.legend(
            handles=[
                Patch(
                    facecolor="#fecaca",
                    edgecolor="#991b1b",
                    hatch="xxx",
                    label="Suppressed/missing",
                )
            ],
            frameon=False,
            fontsize=5.5,
            loc="upper right",
        )
    axis.set_title(title, loc="left", fontweight="bold")
    axis.set_axis_off()


def build_flow_summary(
    resource_quality: pd.DataFrame,
    *,
    case_denominators: Mapping[str, int],
) -> pd.DataFrame:
    """Build Figure 1 flow counts without summing overlapping case populations.

    ``resource_quality`` contains source condition-year rows; C1 and C2 are
    overlapping analyses of the same pooled community-area frame and therefore
    are represented as branches, not additive stages.
    """

    required = {"rows", "disease_measure_eligible_rows", "suppressed_rows"}
    missing = sorted(required - set(resource_quality.columns))
    if missing:
        raise CaseStudyAnalysisError(f"flow source is missing columns: {missing}")
    if set(case_denominators) != {"C1", "C2"}:
        raise CaseStudyAnalysisError("flow summary requires C1 and C2 denominators")
    try:
        c1 = int(case_denominators["C1"])
        c2 = int(case_denominators["C2"])
    except (TypeError, ValueError) as exc:
        raise CaseStudyAnalysisError("case denominators must be integers") from exc
    if c1 < 0 or c2 <= 0:
        raise CaseStudyAnalysisError("C1 must be nonnegative and C2 must be positive")
    source = int(resource_quality["rows"].sum())
    eligible = int(resource_quality["disease_measure_eligible_rows"].sum())
    suppressed = int(resource_quality["suppressed_rows"].sum())
    return pd.DataFrame(
        [
            {"stage": "source_condition_year_records", "count": source, "branch": "shared"},
            {"stage": "eligible_condition_year_records", "count": eligible, "branch": "shared"},
            {"stage": "pooled_community_areas", "count": max(c1, c2), "branch": "shared"},
            {"stage": "case_eligible", "count": c1, "branch": "C1"},
            {"stage": "case_eligible", "count": c2, "branch": "C2"},
            {"stage": "suppressed_or_missing_records", "count": suppressed, "branch": "shared"},
        ]
    )


def build_resolution_heatmap_data(
    geographic_resolution_matrix: pd.DataFrame,
    condition_id: str,
    *,
    noncrossing_only: bool = False,
) -> pd.DataFrame:
    """Return a complete 4-by-4 community-vs-tract quartile matrix.

    Values are percentages of direct tract records, not interpolated or
    aggregated disease values.  Missing quartile combinations are explicit
    zeroes so a plotted heat map has stable axes and deterministic labels.
    """

    required = {
        "condition_id",
        "community_quartile",
        "tract_quartile",
        "tract_percent",
        "noncrossing_only",
    }
    missing = sorted(required - set(geographic_resolution_matrix.columns))
    if missing:
        raise CaseStudyAnalysisError(f"resolution matrix is missing columns: {missing}")
    rows = geographic_resolution_matrix.loc[
        geographic_resolution_matrix["condition_id"].eq(condition_id)
        & geographic_resolution_matrix["noncrossing_only"].eq(noncrossing_only)
    ]
    if rows.empty:
        raise CaseStudyAnalysisError(f"resolution matrix has no rows for {condition_id}")
    values = rows.pivot_table(
        index="community_quartile",
        columns="tract_quartile",
        values="tract_percent",
        aggfunc="sum",
        fill_value=0.0,
    )
    return values.reindex(index=range(1, 5), columns=range(1, 5), fill_value=0.0).astype(float)


def build_true_tract_gap_frame(
    tract_gap: pd.DataFrame,
    geometry_frame: pd.DataFrame,
) -> "gpd.GeoDataFrame":
    """Join rank gaps only to actual tract polygons for Figure 3.

    The helper deliberately rejects community-area geometries; this prevents a
    community mean rank gap from being mislabeled as a tract map.
    """

    required_gap = {"geography_id", "paired_percentile_rank_gap"}
    required_geometry = {"geography_id", "geometry_wkt"}
    if missing := sorted(required_gap - set(tract_gap.columns)):
        raise CaseStudyAnalysisError(f"tract gap source is missing columns: {missing}")
    if missing := sorted(required_geometry - set(geometry_frame.columns)):
        raise CaseStudyAnalysisError(f"geometry source is missing columns: {missing}")
    if (
        "geography_type" in geometry_frame
        and not geometry_frame["geography_type"].eq("census_tract").all()
    ):
        raise CaseStudyAnalysisError("true tract gap map cannot include non-tract geometry")
    if (
        tract_gap["geography_id"].duplicated().any()
        or geometry_frame["geography_id"].duplicated().any()
    ):
        raise CaseStudyAnalysisError("tract gap and geometry keys must be unique")
    joined = geometry_frame[["geography_id", "geometry_wkt"]].merge(
        tract_gap[["geography_id", "paired_percentile_rank_gap"]],
        on="geography_id",
        how="inner",
        validate="one_to_one",
    )
    if joined.empty:
        raise CaseStudyAnalysisError("tract gap and geometry frames have no common records")
    import geopandas as gpd  # type: ignore[import-not-found]

    return gpd.GeoDataFrame(
        joined,
        geometry=gpd.GeoSeries.from_wkt(joined["geometry_wkt"], crs="EPSG:4326"),
        crs="EPSG:4326",
    )


def confidence_interval_label(level: float) -> str:
    """Render a confidence level from serialized model metadata."""

    if not 0 < level < 1:
        raise ValueError("confidence level must be between 0 and 1")
    percent = 100 * level
    digits = 0 if percent.is_integer() else 1
    return f"{percent:.{digits}f}% CI"


def draw_copd_gap_map(axis: Any, gap_map: Any, encoding_contract: Mapping[str, Any]) -> None:
    """Draw the true-tract signed rank-gap map with redundant hatch encoding."""

    from matplotlib.patches import Patch

    gap_map.plot(ax=axis, color="#eef2f6", edgecolor="white", linewidth=0.4)
    available = gap_map.dropna(subset=["paired_percentile_rank_gap"])
    available.plot(
        ax=axis,
        column="paired_percentile_rank_gap",
        cmap="RdBu_r",
        vmin=-1,
        vmax=1,
        edgecolor="white",
        linewidth=0.4,
        legend=True,
        legend_kwds={
            "label": "Signed tract percentile-rank gap (CHM − public)",
            "orientation": "horizontal",
            "shrink": 0.8,
        },
    )
    hatches = encoding_contract["rank_gap_hatches"]
    signs = (
        (available["paired_percentile_rank_gap"].ge(0), "nonnegative", "CHM higher/equal rank"),
        (available["paired_percentile_rank_gap"].lt(0), "negative", "CHM lower rank"),
    )
    for mask, hatch_key, _ in signs:
        available.loc[mask].plot(
            ax=axis, color="none", edgecolor="#555555", hatch=hatches[hatch_key], linewidth=0.2
        )
    axis.legend(
        handles=[
            Patch(facecolor="white", hatch=hatches[key], label=label) for _, key, label in signs
        ],
        frameon=False,
        fontsize=5.5,
        loc="upper left",
    )
    missing = gap_map.loc[gap_map["paired_percentile_rank_gap"].isna()]
    if not missing.empty:
        missing.plot(ax=axis, color="#fecaca", edgecolor="#991b1b", hatch="xxx", linewidth=0.6)
    axis.set_title(
        f"D. Tract rank-gap map; n={len(available):,} tracts", loc="left", fontweight="bold"
    )
    axis.set_axis_off()


def draw_adjusted_association(axis: Any, prediction: pd.DataFrame) -> None:
    """Draw covariate-standardized COPD predictions without duplicating the coefficient."""

    ci_label = confidence_interval_label(float(prediction["confidence_level"].iloc[0]))
    axis.plot(prediction["exposure"], prediction["prediction"], color="#0072B2")
    axis.fill_between(
        prediction["exposure"],
        prediction["ci_low"],
        prediction["ci_high"],
        color="#56B4E9",
        alpha=0.35,
        label=f"{ci_label} HC3 confidence band",
    )
    axis.set(
        xlabel="EHR-diagnosed COPD (CHM condition-record denominator, %)",
        ylabel="Covariate-standardized life expectancy (years)",
        title=f"B. Adjusted association; n={int(prediction['n'].iloc[0])} areas",
    )
    axis.legend(frameon=False, fontsize=5.5)


def _count_percent(count: pd.Series, denominator: pd.Series) -> pd.Series:
    if denominator.le(0).any() or count.lt(0).any() or count.gt(denominator).any():
        raise CaseStudyAnalysisError("table count and denominator fields are inconsistent")
    return pd.Series(
        [f"{int(n):,} ({100 * n / d:.1f})" for n, d in zip(count, denominator, strict=True)],
        index=count.index,
    )


def build_compact_table_1(resource_quality: pd.DataFrame) -> pd.DataFrame:
    """Create the CHM-only community-area resource-accounting table."""

    required = {
        "geography_type",
        "condition_id",
        "rows",
        "geographies",
        "years",
        "denominator_median",
        "denominator_iqr",
        "disease_measure_eligible_rows",
        "percentage_denominator_rows",
        "suppressed_rows",
        "suppression_percentage_denominator_rows",
        "capture_median",
        "capture_iqr",
        "reliability_qualification_status",
    }
    missing = sorted(required - set(resource_quality.columns))
    if missing:
        raise CaseStudyAnalysisError(f"Table 1 source is missing columns: {missing}")
    frame = resource_quality.loc[
        resource_quality["geography_type"].eq("chicago_community_area")
    ].copy()
    if len(frame) != 4 or frame["condition_id"].nunique() != 4:
        raise CaseStudyAnalysisError("Table 1 requires four community-area condition rows")
    table = pd.DataFrame(index=frame.index)
    condition_labels = {
        "copd": "COPD",
        "diabetes_with_complication": "Diabetes with complication",
        "diabetes_without_complication": "Diabetes without complication",
        "hypertension": "Hypertension",
    }
    table["Condition"] = frame["condition_id"].map(condition_labels)
    table["Years, No."] = frame["years"].astype(int)
    table["Condition-year records, No."] = frame["rows"].astype(int)
    table["Community areas represented, No."] = frame["geographies"].astype(int)
    table["CHM condition-record denominator, median (IQR)"] = [
        f"{median:,.0f} ({iqr:,.0f})"
        for median, iqr in zip(frame["denominator_median"], frame["denominator_iqr"], strict=True)
    ]
    table["Eligible, No. (%)"] = _count_percent(
        frame["disease_measure_eligible_rows"], frame["percentage_denominator_rows"]
    )
    table["Suppressed, No. (%)"] = _count_percent(
        frame["suppressed_rows"], frame["suppression_percentage_denominator_rows"]
    )
    table["Source-published capture, median (IQR), %"] = [
        f"{100 * median:.1f} ({100 * iqr:.1f})"
        for median, iqr in zip(frame["capture_median"], frame["capture_iqr"], strict=True)
    ]
    table["Reliability status"] = frame["reliability_qualification_status"].str.replace("_", " ")
    return table.reset_index(drop=True)


def build_geographic_main_evidence(
    agreement: pd.DataFrame,
    partition: pd.DataFrame,
    resolution: pd.DataFrame,
    transitions: pd.DataFrame,
) -> pd.DataFrame:
    """Assemble the unauthorized cross-condition evidence used by main displays."""

    conditions = ["hypertension", "diabetes", "copd"]
    frames = (agreement, partition, resolution, transitions)
    # Geographic evidence may include descriptive partitioning estimates (VPC
    # and AUC), but it must never carry model contracts or inferential outputs.
    forbidden = {
        "model_id",
        "model_key",
        "coefficient",
        "model_ci_low",
        "model_ci_high",
        "adjustment_set",
        "readiness_status",
        "model_readiness",
        "residual_diagnostic",
    }
    for label, frame in zip(
        ("agreement", "partition", "resolution", "transitions"), frames, strict=True
    ):
        leaked = sorted(forbidden & set(frame.columns))
        if leaked:
            raise CaseStudyAnalysisError(
                f"{label} geographic evidence cannot contain model fields: " + ", ".join(leaked)
            )
    if any("results_authorized" not in frame for frame in frames):
        raise CaseStudyAnalysisError("geographic evidence requires authorization fields")
    if any(frame["results_authorized"].fillna(True).astype(bool).any() for frame in frames):
        raise CaseStudyAnalysisError("geographic evidence must remain unauthorized")
    agreement_primary = agreement.loc[agreement["noncrossing_only"].eq(False)]
    if "stratum" in agreement_primary:
        agreement_primary = agreement_primary.loc[agreement_primary["stratum"].eq("overall")]
    agree = agreement_primary.set_index("condition_id")
    if (
        "comparison_geography_type" not in resolution
        or "comparison_geography_type" not in transitions
    ):
        raise CaseStudyAnalysisError(
            "geographic evidence requires an explicit comparison geography"
        )
    compare = resolution.loc[
        resolution["noncrossing_only"].eq(False)
        & resolution["comparison_geography_type"].eq("chicago_community_area")
    ].set_index("condition_id")
    partition_primary = partition
    if "sensitivity_status" in partition:
        partition_primary = partition.loc[partition["sensitivity_status"].eq("primary")]
    vpc = partition_primary.loc[partition_primary["analysis_id"].eq("A1")].set_index("condition_id")
    auc = partition_primary.loc[partition_primary["analysis_id"].eq("A2")].set_index("condition_id")
    vpc_column = "vpc_icc" if "vpc_icc" in vpc else "estimate"
    auc_column = "auc" if "auc" in auc else "estimate"
    if any(frame.index.has_duplicates for frame in (agree, compare, vpc, auc)):
        raise CaseStudyAnalysisError("geographic evidence has duplicate primary condition rows")
    moves = transitions.loc[
        transitions["sensitivity_status"].eq("all_eligible")
        & transitions["comparison_geography_type"].eq("chicago_community_area")
        & transitions["transition_state"].isin(
            ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
        )
    ].pivot(index="condition_id", columns="transition_state", values="tract_count")
    transition_denominators = (
        transitions.loc[
            transitions["sensitivity_status"].eq("all_eligible")
            & transitions["comparison_geography_type"].eq("chicago_community_area")
        ]
        .groupby("condition_id")["tract_count"]
        .sum()
    )
    denominator_by_condition = {}
    if "mean_annual_source_denominator" in transitions:
        denominator_by_condition = (
            transitions.loc[
                transitions["comparison_geography_type"].eq("chicago_community_area")
                & transitions["sensitivity_status"].eq("all_eligible")
            ]
            .groupby("condition_id")["mean_annual_source_denominator"]
            .median()
            .to_dict()
        )
    source_artifacts = (
        "|".join(
            str(frame.get("source_artifact", pd.Series(dtype=object)).dropna().iloc[0])
            for frame in frames
            if "source_artifact" in frame and not frame["source_artifact"].dropna().empty
        )
        or "agreement|partition|resolution|transitions"
    )
    source_checksums = (
        "|".join(
            str(frame.get("source_checksum", pd.Series(dtype=object)).dropna().iloc[0])
            for frame in frames
            if "source_checksum" in frame and not frame["source_checksum"].dropna().empty
        )
        or "not_provided_in_frame"
    )
    rows: list[dict[str, object]] = []
    for condition in conditions:
        into = moves.get("moves_into_highest_quartile", pd.Series(dtype=float)).get(
            condition, np.nan
        )
        out = moves.get("moves_out_of_highest_quartile", pd.Series(dtype=float)).get(
            condition, np.nan
        )
        metrics = {
            "spearman_r": agree.get("spearman_r", pd.Series(dtype=float)).get(condition),
            "weighted_kappa": agree.get("quadratic_weighted_kappa", pd.Series(dtype=float)).get(
                condition
            ),
            "gwet_ac1": agree.get("gwet_ac1", pd.Series(dtype=float)).get(condition),
            "vpc_icc": vpc.get(vpc_column, pd.Series(dtype=float)).get(condition),
            "within_variance_share": (
                vpc.get("within_variance_share", pd.Series(dtype=float)).get(condition)
                if "within_variance_share" in vpc
                else 1 - vpc.get(vpc_column, pd.Series(dtype=float)).get(condition, np.nan)
            ),
            "area_label_auc": auc.get(auc_column, pd.Series(dtype=float)).get(condition),
            "exact_quartile_agreement_count": compare.get(
                "exact_quartile_agreement_count", pd.Series(dtype=float)
            ).get(condition),
            "exact_quartile_agreement_pct": compare.get(
                "exact_quartile_agreement_pct", pd.Series(dtype=float)
            ).get(condition),
            "quartile_disagree_count": compare.get(
                "quartile_disagree_count", pd.Series(dtype=float)
            ).get(condition),
            "quartile_disagree_pct": compare.get(
                "quartile_disagree_pct", pd.Series(dtype=float)
            ).get(condition),
            "q4_moves_into_n": into,
            "q4_moves_out_n": out,
            "q4_movers_n": into + out,
            "q4_transition_eligible_n": transition_denominators.get(condition, np.nan),
        }
        metrics["q4_movers_pct"] = (
            100 * metrics["q4_movers_n"] / metrics["q4_transition_eligible_n"]
            if pd.notna(metrics["q4_movers_n"])
            and pd.notna(metrics["q4_transition_eligible_n"])
            and metrics["q4_transition_eligible_n"] > 0
            else np.nan
        )
        if condition == "diabetes":
            for metric in ("spearman_r", "weighted_kappa", "gwet_ac1"):
                metrics[metric] = np.nan
        unavailable = [name for name, value in metrics.items() if pd.isna(value)]
        rows.append(
            {
                "condition_id": condition,
                "agreement_eligible_n": (
                    np.nan
                    if condition == "diabetes"
                    else agree.get("sample_n", pd.Series(dtype=float)).get(condition)
                ),
                "resolution_eligible_n": compare.get("tract_sample_n", pd.Series(dtype=float)).get(
                    condition
                ),
                **metrics,
                "estimand": "Cross-source rank alignment and direct tract/community classification difference",
                "unit": "condition-specific eligible census tracts",
                "availability_status": (
                    "complete_metric_availability"
                    if not unavailable
                    else "partial_metric_availability"
                ),
                "availability_reason": "|".join(
                    (["combined_components_not_primary_places_comparator_pending_phenotype_and_period_mapping"]
                     if condition == "diabetes" else [])
                    + [f"{name}:not_available" for name in unavailable]
                ),
                "geography": "Chicago census tract linked to direct community-area CHM value",
                "period": (
                    "CHM 2022-2024 denominator-pooled proportion for descriptive ranks; "
                    "source-specific comparator period retained"
                ),
                "comparison_geography_type": "chicago_community_area",
                "comparability_gate_status": "cross_frame_only_no_literal_aggregation",
                "comparability_gate_reason": (
                    "Direct tract and direct community-area CHM values are linked for "
                    "classification comparison; tract disease values are never aggregated."
                ),
                "mean_annual_source_denominator": denominator_by_condition.get(condition, np.nan),
                "denominator_unit": "mean annual CHM condition-record denominators (repeated geography-period units)",
                "mixed_extreme_community_area_n": np.nan,
                "uncertainty_status": (
                    "metric-specific 95% community-area cluster-bootstrap intervals in eTable 7; "
                    "joint source-uncertainty agreement not run"
                ),
                "uncertainty_aware_agreement_status": "not_run",
                "uncertainty_aware_agreement_reason": (
                    "Compatible PLACES intervals and denominator uncertainty were not available"
                ),
                "sensitivity_status": "annual and noncrossing analyses reported in supplement",
                "annual_sensitivity_status": "reported_separately",
                "noncrossing_sensitivity_status": "reported_separately",
                "source_artifacts": source_artifacts,
                "source_checksums": source_checksums,
                "source_artifact": source_artifacts,
                "source_checksum": source_checksums,
                "field_role": "derived",
                "results_authorized": False,
                "manuscript_import_allowed": False,
            }
        )
    return pd.DataFrame(rows)


def build_compact_table_2(evidence: pd.DataFrame) -> pd.DataFrame:
    """Format primary tract-versus-community-area evidence with explicit denominators."""

    labels = {
        "hypertension": "Hypertension",
        "diabetes": "Combined diabetes components",
        "copd": "COPD",
    }
    table = pd.DataFrame({"Condition": evidence["condition_id"].map(labels)})
    table["Tract/community eligible tracts, No."] = evidence["resolution_eligible_n"].astype("Int64")
    table["Exact quartile agreement, No. (%)"] = [
        "—" if pd.isna(count) or pd.isna(percent) else f"{int(count):,} ({float(percent):.1f})"
        for count, percent in zip(
            evidence["exact_quartile_agreement_count"],
            evidence["exact_quartile_agreement_pct"],
            strict=True,
        )
    ]
    table["Quartile disagreement, No. (%)"] = [
        "—" if pd.isna(count) or pd.isna(percent) else f"{int(count):,} ({float(percent):.1f})"
        for count, percent in zip(
            evidence["quartile_disagree_count"], evidence["quartile_disagree_pct"], strict=True
        )
    ]
    table["Within-community variance share"] = pd.to_numeric(
        evidence["within_variance_share"], errors="coerce"
    ).round(3)
    table["Q4 transition eligible tracts, No."] = evidence[
        "q4_transition_eligible_n"
    ].astype("Int64")
    table["Q4 movers, No. (%)"] = [
        "—" if pd.isna(count) or pd.isna(percent) else f"{int(count):,} ({float(percent):.1f})"
        for count, percent in zip(
            evidence["q4_movers_n"], evidence["q4_movers_pct"], strict=True
        )
    ]
    return table


def build_geographic_consequence_display_data(
    transitions: pd.DataFrame,
    mixed_extremes: pd.DataFrame,
    stability: pd.DataFrame,
    resolution: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Prepare the four panels for the direct cross-frame figure."""

    geography = "chicago_community_area"
    transition_rows = transitions.loc[
        transitions["comparison_geography_type"].eq(geography)
        & transitions["sensitivity_status"].eq("all_eligible")
        & transitions["transition_state"].isin(
            ["moves_into_highest_quartile", "moves_out_of_highest_quartile"]
        )
    ].copy()
    mixed_rows = mixed_extremes.loc[
        mixed_extremes["comparison_geography_type"].eq(geography)
        & mixed_extremes["sensitivity_status"].eq("all_eligible")
    ].copy()
    mixed_counts = (
        mixed_rows.groupby("condition_id", as_index=False)["comparison_geography_id"]
        .nunique()
        .rename(columns={"comparison_geography_id": "community_area_n"})
    )
    annual = stability.loc[
        stability["comparison_geography_type"].eq(geography)
        & stability["sensitivity_status"].eq("all_eligible")
        & stability["result_type"].eq("annual_jaccard")
    ].copy()
    noncrossing = resolution.loc[resolution["noncrossing_only"].eq(True)].copy()
    return {
        "transitions": transition_rows,
        "mixed_extremes": mixed_rows,
        "mixed_counts": mixed_counts,
        "annual": annual,
        "noncrossing": noncrossing,
    }


def _hc3_covariance(design: np.ndarray, outcome: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    inverse = np.linalg.inv(design.T @ design)
    beta = inverse @ design.T @ outcome
    residual = outcome - design @ beta
    leverage = np.einsum("ij,jk,ik->i", design, inverse, design)
    scaled = residual / (1 - leverage)
    meat = design.T @ (design * scaled[:, None] ** 2)
    return beta, inverse @ meat @ inverse


def build_adjusted_prediction_data(
    result: GovernedModelResult,
    primary_frame: pd.DataFrame,
    *,
    points: int = 100,
    confidence_level: float = 0.975,
) -> pd.DataFrame:
    """Predict C2 life expectancy across observed COPD values at mean covariates."""

    if result.model_id != "C2" or points < 2:
        raise CaseStudyAnalysisError("adjusted prediction requires C2 and at least 2 points")
    eligible = primary_frame.loc[primary_frame["copd_exposure_complete"].astype(bool), COPD]
    exposure = np.linspace(float(eligible.min()), float(eligible.max()), points)
    scaling = result.scaling[COPD]
    standardized = (exposure - float(scaling["center"])) / float(scaling["scale"])
    prediction_design = np.zeros((points, result.design.shape[1]), dtype=float)
    prediction_design[:, 0] = 1.0
    prediction_design[:, 1] = standardized
    beta, covariance = _hc3_covariance(result.design, result.outcome.to_numpy(dtype=float))
    prediction = prediction_design @ beta
    variance = np.einsum("ij,jk,ik->i", prediction_design, covariance, prediction_design)
    critical = float(stats.norm.ppf(1 - (1 - confidence_level) / 2))
    standard_error = np.sqrt(np.maximum(variance, 0))
    return pd.DataFrame(
        {
            "exposure": exposure,
            "prediction": prediction,
            "ci_low": prediction - critical * standard_error,
            "ci_high": prediction + critical * standard_error,
            "confidence_level": confidence_level,
            "n": len(eligible),
            "unit": "life_expectancy_years",
            "covariate_standardization": "adjustment_covariates_at_sample_means",
            "results_authorized": False,
        }
    )
