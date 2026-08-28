"""Reconstruct Chicago community-area covariates from official Census components."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
import re
import zipfile
from pathlib import Path

import pandas as pd  # type: ignore[import-untyped]
from shapely import wkt  # type: ignore[import-untyped]
from shapely.geometry import Point  # type: ignore[import-untyped]


class CensusCovariateError(ValueError):
    """A Census covariate input or derivation violates its scientific contract."""


_BLOCK_GEOID = re.compile(r"^\d{15}$")
_TRACT_GEOID = re.compile(r"^\d{11}$")
_COMPONENTS = frozenset(
    {
        "total_population",
        "female_population",
        "age_65_plus_population",
        "adult_population",
        "poverty_numerator",
        "poverty_denominator",
    }
)
_COVARIATES = (
    "pct_female",
    "pct_age_65_plus",
    "pct_below_fpl",
    "acs_adult_population",
)
_B01001_MALE_LEAVES = frozenset(range(3, 26))
_B01001_FEMALE_LEAVES = frozenset(range(27, 50))
_B01001_ADULT_LEAVES = frozenset((*range(7, 26), *range(31, 50)))
_B01001_AGE65_LEAVES = frozenset((*range(20, 26), *range(44, 50)))
_B17001_BELOW_MALE = frozenset(range(4, 17))
_B17001_BELOW_FEMALE = frozenset(range(18, 31))
_B17001_ABOVE_MALE = frozenset(range(33, 46))
_B17001_ABOVE_FEMALE = frozenset(range(47, 60))
_ACS_CELL = re.compile(r"^(B01001|B17001)_E(\d{3})$")


def read_pl_block_population(archive_path: Path, *, county_fips: str = "031") -> pd.DataFrame:
    """Read block total population from an official 2020 PL state archive."""

    try:
        with zipfile.ZipFile(archive_path) as archive:
            names = set(archive.namelist())
            if not {"ilgeo2020.pl", "il000012020.pl"}.issubset(names):
                raise CensusCovariateError("PL archive lacks geography or segment-one data")
            logrec_to_block: dict[str, str] = {}
            with archive.open("ilgeo2020.pl") as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|")
                for row in reader:
                    if len(row) < 9 or row[2] != "750":
                        continue
                    geoid = row[8].removeprefix("7500000US")
                    if len(geoid) != 15 or not geoid.startswith(f"17{county_fips}"):
                        continue
                    if row[7] in logrec_to_block:
                        raise CensusCovariateError("PL geography contains a duplicate LOGRECNO")
                    logrec_to_block[row[7]] = geoid
            if not logrec_to_block:
                raise CensusCovariateError("PL archive contains no requested county blocks")
            populations: dict[str, float] = {}
            with archive.open("il000012020.pl") as raw:
                reader = csv.reader(io.TextIOWrapper(raw, encoding="latin-1"), delimiter="|")
                for row in reader:
                    if len(row) < 6 or row[4] not in logrec_to_block:
                        continue
                    block_geoid = logrec_to_block[row[4]]
                    if block_geoid in populations:
                        raise CensusCovariateError("PL segment contains a duplicate block record")
                    population = float(row[5])
                    if not math.isfinite(population) or population < 0:
                        raise CensusCovariateError("PL block population is invalid")
                    populations[block_geoid] = population
    except (OSError, zipfile.BadZipFile, UnicodeError, csv.Error) as error:
        raise CensusCovariateError("PL archive cannot be read safely") from error
    if set(populations) != set(logrec_to_block.values()):
        raise CensusCovariateError("PL block population coverage is incomplete")
    return pd.DataFrame.from_records(
        [
            {
                "block_geoid": block_geoid,
                "tract_geoid": block_geoid[:11],
                "ancillary_count": populations[block_geoid],
            }
            for block_geoid in sorted(populations)
        ]
    )


def read_variance_replicates(
    archive_path: Path,
    table_id: str,
    *,
    geography_ids: set[str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read published ACS tract point and 80-replicate cell estimates."""

    if table_id not in {"B01001", "B17001"}:
        raise CensusCovariateError("unsupported variance-replicate table")
    try:
        frame = pd.read_csv(archive_path, compression="zip", dtype="string")
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile) as error:
        raise CensusCovariateError("variance-replicate archive cannot be read") from error
    required = {
        "TBLID",
        "GEOID",
        "ORDER",
        "ESTIMATE",
        *{f"Var_Rep{index}" for index in range(1, 81)},
    }
    _require_columns(frame, required, "variance-replicate table")
    data = frame.loc[
        frame["TBLID"].eq(table_id)
        & frame["GEOID"].str.startswith("1400000US17", na=False)
        & frame["ORDER"].str.fullmatch(r"\d+", na=False)
    ].copy()
    if data.empty:
        raise CensusCovariateError("variance-replicate table contains no Illinois tracts")
    data["geography_id"] = data["GEOID"].str.removeprefix("1400000US")
    if geography_ids is not None:
        data = data.loc[data["geography_id"].isin(geography_ids)].copy()
        if data.empty:
            raise CensusCovariateError("variance-replicate table contains no requested tracts")
    data["source_variable_id"] = data["ORDER"].astype(int).map(
        lambda value: f"{table_id}_E{value:03d}"
    )
    data["estimate"] = pd.to_numeric(data["ESTIMATE"], errors="coerce")
    if data["estimate"].isna().any():
        raise CensusCovariateError("variance-replicate point estimate is invalid")
    if data.duplicated(["geography_id", "source_variable_id"]).any():
        raise CensusCovariateError("variance-replicate table contains duplicate tract cells")
    point = data[["geography_id", "source_variable_id", "estimate"]].copy()
    point["estimate_state"] = "reported"
    point = point[["geography_id", "source_variable_id", "estimate", "estimate_state"]]
    replicate_fields = [f"Var_Rep{index}" for index in range(1, 81)]
    replicates = data[
        ["geography_id", "source_variable_id", *replicate_fields]
    ].melt(
        id_vars=["geography_id", "source_variable_id"],
        value_vars=replicate_fields,
        var_name="replicate_id",
        value_name="replicate_estimate",
    )
    replicates["replicate_id"] = replicates["replicate_id"].str.removeprefix("Var_Rep").astype(int)
    replicates["replicate_estimate"] = pd.to_numeric(
        replicates["replicate_estimate"], errors="coerce"
    )
    if replicates["replicate_estimate"].isna().any():
        raise CensusCovariateError("variance replicate estimate is invalid")
    return point.reset_index(drop=True), replicates.reset_index(drop=True)


def assign_blocks_to_communities(
    blocks: pd.DataFrame, communities: pd.DataFrame, *, require_all: bool = True
) -> pd.DataFrame:
    """Assign each Census block as a whole using its official internal point."""

    block_fields = {
        "block_geoid",
        "tract_geoid",
        "internal_longitude",
        "internal_latitude",
    }
    community_fields = {"community_area_id", "geometry_wkt"}
    if not block_fields.issubset(blocks.columns):
        raise CensusCovariateError("block input is missing required internal-point fields")
    if not community_fields.issubset(communities.columns):
        raise CensusCovariateError("community input is missing required geometry fields")
    if blocks["block_geoid"].astype(str).duplicated().any():
        raise CensusCovariateError("block input contains a duplicate block GEOID")
    if communities["community_area_id"].astype(str).duplicated().any():
        raise CensusCovariateError("community input contains a duplicate community-area ID")

    polygons: list[tuple[str, object]] = []
    for row in communities.itertuples(index=False):
        area_id = str(row.community_area_id).zfill(2)
        geometry = wkt.loads(str(row.geometry_wkt))
        if geometry.is_empty or not geometry.is_valid:
            raise CensusCovariateError("community input contains invalid geometry")
        polygons.append((area_id, geometry))

    records: list[dict[str, object]] = []
    for row in blocks.itertuples(index=False):
        block_geoid = str(row.block_geoid)
        tract_geoid = str(row.tract_geoid)
        if not _BLOCK_GEOID.fullmatch(block_geoid) or not _TRACT_GEOID.fullmatch(tract_geoid):
            raise CensusCovariateError("block input contains an invalid Census GEOID")
        longitude = float(row.internal_longitude)
        latitude = float(row.internal_latitude)
        if not (math.isfinite(longitude) and math.isfinite(latitude)):
            raise CensusCovariateError("block input contains a nonfinite internal point")
        point = Point(longitude, latitude)
        within = [area_id for area_id, geometry in polygons if point.within(geometry)]
        boundary_touch = False
        matches = within
        if not matches:
            matches = [area_id for area_id, geometry in polygons if point.intersects(geometry)]
            boundary_touch = bool(matches)
        if not matches:
            if require_all:
                raise CensusCovariateError(f"block {block_geoid} is outside every community area")
            continue
        if len(matches) != 1:
            raise CensusCovariateError(
                f"block {block_geoid} internal point has ambiguous community assignment"
            )
        records.append(
            {
                "block_geoid": block_geoid,
                "tract_geoid": tract_geoid,
                "community_area_id": matches[0],
                "boundary_touch": boundary_touch,
            }
        )
    return pd.DataFrame.from_records(records)


def build_block_weights(
    block_counts: pd.DataFrame, assignments: pd.DataFrame
) -> pd.DataFrame:
    """Calculate sex-age population weights within each tract and allocation group."""

    count_fields = {
        "block_geoid",
        "tract_geoid",
        "allocation_group",
        "ancillary_count",
    }
    assignment_fields = {
        "block_geoid",
        "tract_geoid",
        "community_area_id",
        "boundary_touch",
    }
    if not count_fields.issubset(block_counts.columns):
        raise CensusCovariateError("block counts are missing required allocation fields")
    if not assignment_fields.issubset(assignments.columns):
        raise CensusCovariateError("block assignments are missing required fields")
    if block_counts.duplicated(["block_geoid", "allocation_group"]).any():
        raise CensusCovariateError("block counts contain a duplicate allocation group")
    if assignments["block_geoid"].astype(str).duplicated().any():
        raise CensusCovariateError("block assignments contain a duplicate block GEOID")

    counts = block_counts.copy()
    counts["ancillary_count"] = pd.to_numeric(counts["ancillary_count"], errors="coerce")
    if counts["ancillary_count"].isna().any() or not counts["ancillary_count"].map(
        lambda value: math.isfinite(float(value))
    ).all():
        raise CensusCovariateError("ancillary population must be finite and nonnegative")
    if (counts["ancillary_count"] < 0).any():
        raise CensusCovariateError("ancillary population must be finite and nonnegative")

    joined = counts.merge(
        assignments[list(assignment_fields)],
        on="block_geoid",
        how="left",
        suffixes=("", "_assignment"),
        indicator=True,
        validate="many_to_one",
    )
    if joined["_merge"].ne("both").any():
        raise CensusCovariateError("block count exists without a community assignment")
    if joined["tract_geoid"].astype(str).ne(
        joined["tract_geoid_assignment"].astype(str)
    ).any():
        raise CensusCovariateError("block count and assignment tract GEOIDs disagree")
    joined = joined.drop(columns=["_merge", "tract_geoid_assignment"])

    group_fields = ["tract_geoid", "allocation_group"]
    totals = joined.groupby(group_fields, sort=False)["ancillary_count"].transform("sum")
    if (totals <= 0).any():
        raise CensusCovariateError("tract allocation group has zero ancillary population")
    joined["weight"] = joined["ancillary_count"] / totals
    sums = joined.groupby(group_fields)["weight"].sum()
    if not sums.map(lambda value: math.isclose(float(value), 1.0, abs_tol=1e-12)).all():
        raise CensusCovariateError("block allocation weights do not sum to one")
    return joined.sort_values(
        ["tract_geoid", "allocation_group", "block_geoid"], kind="mergesort"
    ).reset_index(drop=True)


def _require_columns(frame: pd.DataFrame, required: set[str], label: str) -> None:
    missing = sorted(required - set(frame.columns))
    if missing:
        raise CensusCovariateError(f"{label} is missing required columns: {', '.join(missing)}")


def standardize_acs_components(frame: pd.DataFrame) -> pd.DataFrame:
    """Expand reported B01001/B17001 leaves into governed count components."""

    required = {"geography_id", "source_variable_id", "estimate", "estimate_state"}
    _require_columns(frame, required, "normalized ACS input")
    records: list[dict[str, object]] = []
    for row in frame.itertuples(index=False):
        variable_id = str(row.source_variable_id)
        match = _ACS_CELL.fullmatch(variable_id)
        if match is None or str(row.estimate_state) != "reported":
            continue
        table, rendered_cell = match.groups()
        cell = int(rendered_cell)
        estimate = float(row.estimate)
        if not math.isfinite(estimate) or estimate < 0:
            raise CensusCovariateError("ACS leaf estimate must be finite and nonnegative")
        components: list[str] = []
        allocation_group: str | None = None
        if table == "B01001" and cell in (_B01001_MALE_LEAVES | _B01001_FEMALE_LEAVES):
            components.append("total_population")
            if cell in _B01001_FEMALE_LEAVES:
                components.append("female_population")
            if cell in _B01001_ADULT_LEAVES:
                components.append("adult_population")
            if cell in _B01001_AGE65_LEAVES:
                components.append("age_65_plus_population")
            allocation_group = f"p12_{cell:03d}"
        elif table == "B17001" and cell in (
            _B17001_BELOW_MALE
            | _B17001_BELOW_FEMALE
            | _B17001_ABOVE_MALE
            | _B17001_ABOVE_FEMALE
        ):
            if cell in (_B17001_BELOW_MALE | _B17001_BELOW_FEMALE):
                components.append("poverty_numerator")
            components.append("poverty_denominator")
            allocation_group = (
                "p12_male_total"
                if cell in (_B17001_BELOW_MALE | _B17001_ABOVE_MALE)
                else "p12_female_total"
            )
        for component in components:
            records.append(
                {
                    "tract_geoid": str(row.geography_id),
                    "component": component,
                    "allocation_group": allocation_group,
                    "estimate": estimate,
                    "source_variable_id": variable_id,
                }
            )
    if not records:
        raise CensusCovariateError("normalized ACS input has no supported reported leaf cells")
    return pd.DataFrame.from_records(records)


def standardize_p12_block_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Convert wide Decennial P12 block leaves into reusable allocation groups."""

    leaf_cells = (*range(3, 26), *range(27, 50))
    required = {"block_geoid", "tract_geoid"} | {
        f"P12_{cell:03d}N" for cell in leaf_cells
    }
    _require_columns(frame, required, "P12 block input")
    records: list[dict[str, object]] = []
    for row in frame.itertuples(index=False):
        block_geoid = str(row.block_geoid)
        tract_geoid = str(row.tract_geoid)
        if not _BLOCK_GEOID.fullmatch(block_geoid) or not _TRACT_GEOID.fullmatch(tract_geoid):
            raise CensusCovariateError("P12 block input contains an invalid GEOID")
        values: dict[int, float] = {}
        for cell in leaf_cells:
            value = float(getattr(row, f"P12_{cell:03d}N"))
            if not math.isfinite(value) or value < 0:
                raise CensusCovariateError("P12 block count must be finite and nonnegative")
            values[cell] = value
            records.append(
                {
                    "block_geoid": block_geoid,
                    "tract_geoid": tract_geoid,
                    "allocation_group": f"p12_{cell:03d}",
                    "ancillary_count": value,
                }
            )
        for group, cells in (
            ("p12_male_total", _B01001_MALE_LEAVES),
            ("p12_female_total", _B01001_FEMALE_LEAVES),
        ):
            records.append(
                {
                    "block_geoid": block_geoid,
                    "tract_geoid": tract_geoid,
                    "allocation_group": group,
                    "ancillary_count": sum(values[cell] for cell in cells),
                }
            )
    return pd.DataFrame.from_records(records)


def _component_wide(allocated: pd.DataFrame, value: str) -> pd.DataFrame:
    grouped = (
        allocated.groupby(["community_area_id", "component"], sort=True)[value]
        .sum()
        .unstack("component")
    )
    missing = sorted(_COMPONENTS - set(grouped.columns))
    if missing:
        raise CensusCovariateError(
            f"allocated ACS components are incomplete: {', '.join(missing)}"
        )
    return grouped


def _derive_from_components(wide: pd.DataFrame) -> pd.DataFrame:
    if (wide[["total_population", "poverty_denominator"]] <= 0).any().any():
        raise CensusCovariateError("derived percentage denominator must be positive")
    output = wide.copy()
    output["pct_female"] = 100 * output["female_population"] / output["total_population"]
    output["pct_age_65_plus"] = (
        100 * output["age_65_plus_population"] / output["total_population"]
    )
    output["pct_below_fpl"] = (
        100 * output["poverty_numerator"] / output["poverty_denominator"]
    )
    output["acs_adult_population"] = output["adult_population"]
    return output


def derive_community_covariates(
    acs_components: pd.DataFrame,
    weights: pd.DataFrame,
    replicates: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Allocate tract count components, derive ratios, and propagate ACS replicates."""

    component_fields = {"tract_geoid", "component", "allocation_group", "estimate"}
    weight_fields = {
        "tract_geoid",
        "allocation_group",
        "block_geoid",
        "community_area_id",
        "weight",
    }
    _require_columns(acs_components, component_fields, "ACS components")
    _require_columns(weights, weight_fields, "block weights")
    components = acs_components.copy()
    if components.duplicated(["tract_geoid", "component", "allocation_group"]).any():
        raise CensusCovariateError("ACS components contain a duplicate tract component")
    if not set(components["component"].astype(str)).issubset(_COMPONENTS):
        raise CensusCovariateError("ACS components contain an unsupported component")
    components["estimate"] = pd.to_numeric(components["estimate"], errors="coerce")
    if components["estimate"].isna().any() or (components["estimate"] < 0).any():
        raise CensusCovariateError("ACS component estimates must be finite and nonnegative")

    normalized_weights = weights.copy()
    normalized_weights["weight"] = pd.to_numeric(normalized_weights["weight"], errors="coerce")
    if normalized_weights["weight"].isna().any() or (normalized_weights["weight"] < 0).any():
        raise CensusCovariateError("block weights must be finite and nonnegative")
    weight_sums = normalized_weights.groupby(["tract_geoid", "allocation_group"])[
        "weight"
    ].sum()
    if not weight_sums.map(lambda value: math.isclose(float(value), 1.0, abs_tol=1e-12)).all():
        raise CensusCovariateError("block allocation weights do not sum to one")

    allocated = components.merge(
        normalized_weights,
        on=["tract_geoid", "allocation_group"],
        how="left",
        validate="many_to_many",
        indicator=True,
    )
    if allocated["_merge"].ne("both").any():
        raise CensusCovariateError("ACS component has no matching block allocation weights")
    allocated = allocated.drop(columns="_merge")
    allocated["allocated_estimate"] = allocated["estimate"] * allocated["weight"]
    wide = _derive_from_components(_component_wide(allocated, "allocated_estimate"))
    output = wide.reset_index()

    for covariate in _COVARIATES:
        output[f"{covariate}_standard_error"] = pd.NA
        output[f"{covariate}_moe90"] = pd.NA
    output["uncertainty_status"] = "unavailable_no_variance_replicates"

    if replicates is not None:
        replicate_fields = {
            "tract_geoid",
            "component",
            "allocation_group",
            "replicate_id",
            "replicate_estimate",
        }
        _require_columns(replicates, replicate_fields, "ACS variance replicates")
        replicate_frame = replicates.copy()
        replicate_frame["replicate_id"] = pd.to_numeric(
            replicate_frame["replicate_id"], errors="coerce"
        )
        expected_ids = set(range(1, 81))
        grouped_ids = replicate_frame.groupby(
            ["tract_geoid", "component", "allocation_group"], sort=False
        )["replicate_id"].agg(lambda values: set(int(value) for value in values))
        if grouped_ids.empty or any(values != expected_ids for values in grouped_ids):
            raise CensusCovariateError("each ACS component must contain exactly 80 replicates")
        replicate_frame["replicate_estimate"] = pd.to_numeric(
            replicate_frame["replicate_estimate"], errors="coerce"
        )
        if replicate_frame["replicate_estimate"].isna().any():
            raise CensusCovariateError("ACS replicate estimates must be finite")
        replicate_allocated = replicate_frame.merge(
            normalized_weights,
            on=["tract_geoid", "allocation_group"],
            how="left",
            validate="many_to_many",
            indicator=True,
        )
        if replicate_allocated["_merge"].ne("both").any():
            raise CensusCovariateError("ACS replicate has no matching block allocation weights")
        replicate_allocated["allocated_replicate"] = (
            replicate_allocated["replicate_estimate"] * replicate_allocated["weight"]
        )
        replicate_grouped = (
            replicate_allocated.groupby(
                ["replicate_id", "community_area_id", "component"], sort=True
            )["allocated_replicate"]
            .sum()
            .unstack("component")
        )
        if not _COMPONENTS.issubset(replicate_grouped.columns):
            raise CensusCovariateError("ACS replicate components are incomplete")
        replicate_derived = _derive_from_components(replicate_grouped)
        point = output.set_index("community_area_id")
        for area_id in point.index:
            area_replicates = replicate_derived.xs(area_id, level="community_area_id")
            if set(area_replicates.index.astype(int)) != expected_ids:
                raise CensusCovariateError("community area does not contain exactly 80 replicates")
            for covariate in _COVARIATES:
                deviations = area_replicates[covariate].astype(float) - float(
                    point.loc[area_id, covariate]
                )
                standard_error = math.sqrt(4.0 / 80.0 * float((deviations**2).sum()))
                point.loc[area_id, f"{covariate}_standard_error"] = standard_error
                point.loc[area_id, f"{covariate}_moe90"] = 1.645 * standard_error
        point["uncertainty_status"] = "available_variance_replicates"
        output = point.reset_index()

    diagnostics = allocated[
        [
            "tract_geoid",
            "block_geoid",
            "community_area_id",
            "component",
            "allocation_group",
            "estimate",
            "weight",
            "allocated_estimate",
        ]
    ].copy()
    return output.sort_values("community_area_id").reset_index(drop=True), diagnostics


def validate_community_covariates(frame: pd.DataFrame) -> None:
    """Enforce the production 77-community-area covariate contract."""

    required = {
        "community_area_id",
        "total_population",
        "pct_female",
        "pct_age_65_plus",
        "pct_below_fpl",
        "acs_adult_population",
    }
    _require_columns(frame, required, "community covariates")
    identifiers = frame["community_area_id"].astype(str)
    if identifiers.duplicated().any() or set(identifiers) != {
        f"{index:02d}" for index in range(1, 78)
    }:
        raise CensusCovariateError("community covariates must contain exactly IDs 01 through 77")
    numeric_fields = sorted(required - {"community_area_id"})
    numeric = frame[numeric_fields].apply(pd.to_numeric, errors="coerce")
    if numeric.isna().any().any() or not numeric.map(
        lambda value: math.isfinite(float(value))
    ).all().all():
        raise CensusCovariateError("community covariates contain missing or nonfinite values")
    if (numeric < 0).any().any():
        raise CensusCovariateError("community covariates contain a negative value")
    for field in ("pct_female", "pct_age_65_plus", "pct_below_fpl"):
        if (numeric[field] > 100).any():
            raise CensusCovariateError(f"{field} is outside zero to 100")
    if (numeric["acs_adult_population"] > numeric["total_population"]).any():
        raise CensusCovariateError("adult population exceeds total population")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_census_covariate_artifacts(
    *, root: Path, input_dir: Path, output_dir: Path
) -> dict[str, Path]:
    """Build governed 2024 ACS covariates for all 77 Chicago community areas."""

    try:
        import pyogrio  # type: ignore[import-untyped]
    except ImportError as error:  # pragma: no cover - packaging guard
        raise CensusCovariateError("pyogrio is required to read TIGER blocks") from error

    sources = {
        "pl": input_dir / "il2020.pl.zip",
        "tiger": input_dir / "tl_2020_17031_tabblock20.zip",
        "B01001": input_dir / "B01001_17.csv.zip",
        "B17001": input_dir / "B17001_17.csv.zip",
    }
    missing = [str(path) for path in sources.values() if not path.is_file()]
    if missing:
        raise CensusCovariateError(f"required Census inputs are missing: {', '.join(missing)}")
    boundary_path = root / "data/processed/public/chicago_community_areas_current.parquet"
    if not boundary_path.is_file():
        raise CensusCovariateError("community-area boundary artifact is missing")
    communities = pd.read_parquet(boundary_path)
    _require_columns(
        communities,
        {"geography_id", "geometry_wkt", "snapshot_id", "release_vintage"},
        "community-area boundary artifact",
    )
    community_geometry = communities.rename(
        columns={"geography_id": "community_area_id"}
    )[["community_area_id", "geometry_wkt"]]

    tiger = pyogrio.read_dataframe(
        f"/vsizip/{sources['tiger']}",
        columns=["GEOID20", "INTPTLON20", "INTPTLAT20"],
        read_geometry=False,
        use_arrow=True,
    )
    blocks = pd.DataFrame(
        {
            "block_geoid": tiger["GEOID20"].astype(str),
            "tract_geoid": tiger["GEOID20"].astype(str).str[:11],
            "internal_longitude": pd.to_numeric(tiger["INTPTLON20"], errors="coerce"),
            "internal_latitude": pd.to_numeric(tiger["INTPTLAT20"], errors="coerce"),
        }
    )
    assignments = assign_blocks_to_communities(
        blocks, community_geometry, require_all=False
    )
    if set(assignments["community_area_id"]) != {f"{index:02d}" for index in range(1, 78)}:
        raise CensusCovariateError("block assignment does not cover all 77 community areas")

    population = read_pl_block_population(sources["pl"])
    assigned_population = population.merge(
        assignments,
        on=["block_geoid", "tract_geoid"],
        how="inner",
        validate="one_to_one",
    )
    tract_population = assigned_population.groupby("tract_geoid")["ancillary_count"].transform(
        "sum"
    )
    positive_population = assigned_population.loc[tract_population.gt(0)].copy()
    positive_assignments = positive_population[
        ["block_geoid", "tract_geoid", "community_area_id", "boundary_touch"]
    ]
    block_counts = positive_population[
        ["block_geoid", "tract_geoid", "ancillary_count"]
    ].assign(allocation_group="p1_total")
    weights = build_block_weights(block_counts, positive_assignments)
    tract_ids = set(weights["tract_geoid"].astype(str))

    point_parts: list[pd.DataFrame] = []
    replicate_parts: list[pd.DataFrame] = []
    for table_id in ("B01001", "B17001"):
        point, raw_replicates = read_variance_replicates(
            sources[table_id], table_id, geography_ids=tract_ids
        )
        standardized = standardize_acs_components(point)
        mapping = standardized[
            ["tract_geoid", "source_variable_id", "component"]
        ].drop_duplicates()
        point_parts.append(standardized)
        mapped_replicates = raw_replicates.rename(
            columns={"geography_id": "tract_geoid"}
        ).merge(
            mapping,
            on=["tract_geoid", "source_variable_id"],
            how="inner",
            validate="many_to_many",
        )
        replicate_parts.append(mapped_replicates)

    components = pd.concat(point_parts, ignore_index=True)
    components["allocation_group"] = "p1_total"
    components = (
        components.groupby(
            ["tract_geoid", "component", "allocation_group"], as_index=False
        )["estimate"]
        .sum()
    )
    replicates = pd.concat(replicate_parts, ignore_index=True)
    replicates["allocation_group"] = "p1_total"
    replicates = (
        replicates.groupby(
            [
                "tract_geoid",
                "component",
                "allocation_group",
                "replicate_id",
            ],
            as_index=False,
        )["replicate_estimate"]
        .sum()
    )
    covariates, diagnostics = derive_community_covariates(
        components, weights, replicates
    )
    validate_community_covariates(covariates)
    covariates["source_id"] = "census_acs_2024_5y"
    covariates["snapshot_id"] = "census_acs_2024_5y_2026-07-13"
    covariates["source_record_id"] = covariates["community_area_id"]
    covariates["geography_type"] = "chicago_community_area_reconstructed"
    covariates["geography_id"] = covariates["community_area_id"]
    covariates["time_period"] = "2020-2024"
    covariates["release_vintage"] = "2024 ACS 5-year"
    covariates["allocation_method"] = (
        "whole_2020_census_block_internal_point_then_within_tract_p1_population_weight"
    )
    covariates["allocation_weight_source"] = "2020 Census PL 94-171 P1 total population"
    covariates["poverty_universe"] = (
        "population for whom poverty status is determined (ACS B17001)"
    )
    covariates["boundary_snapshot_id"] = str(communities["snapshot_id"].iloc[0])
    covariates["boundary_release_vintage"] = str(
        communities["release_vintage"].iloc[0]
    )
    lineage_inputs = (
        "census_acs_2024_5y:B01001/B17001 variance replicates|"
        "census_tiger_2020_tract:GEOID20/INTPTLON20/INTPTLAT20"
    )
    required_provenance = {
        "source_id",
        "snapshot_id",
        "source_record_id",
        "source_field_map",
        "release_vintage",
        "geography_type",
        "geography_id",
        "time_period",
    }
    covariates["source_field_map"] = json.dumps(
        {
            column: lineage_inputs
            for column in covariates.columns
            if column not in required_provenance
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    diagnostics["source_id"] = "census_acs_2024_5y"
    diagnostics["snapshot_id"] = "census_acs_2024_5y_2026-07-13"
    diagnostics["source_record_id"] = diagnostics.index.map(
        lambda index: f"allocation-{index + 1}"
    )
    diagnostics["release_vintage"] = "2024 ACS 5-year"
    diagnostics["geography_type"] = "chicago_community_area_reconstructed"
    diagnostics["geography_id"] = diagnostics["community_area_id"]
    diagnostics["time_period"] = "2020-2024"
    diagnostics["source_field_map"] = json.dumps(
        {
            column: lineage_inputs
            for column in diagnostics.columns
            if column not in required_provenance
        },
        sort_keys=True,
        separators=(",", ":"),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    covariate_path = output_dir / "census_acs_2024_community_area_covariates.parquet"
    diagnostics_path = output_dir / "census_acs_2024_allocation_diagnostics.parquet"
    schema_path = output_dir / "census_acs_2024_community_area_covariates.schema.json"
    manifest_path = output_dir / "census_acs_2024_community_area_covariates.manifest.json"
    covariates.to_parquet(covariate_path, index=False)
    diagnostics.to_parquet(diagnostics_path, index=False)
    schema = {
        "dataset_id": "census_acs_2024_community_area_covariates",
        "grain": "one row per Chicago community area",
        "primary_key": ["community_area_id"],
        "row_count": int(len(covariates)),
        "columns": [
            {"name": column, "dtype": str(covariates[column].dtype)}
            for column in covariates.columns
        ],
    }
    schema_path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "dataset_id": schema["dataset_id"],
        "method_status": "implemented_official_census_reconstruction",
        "row_count": int(len(covariates)),
        "community_area_count": int(covariates["community_area_id"].nunique()),
        "assigned_block_count": int(len(assignments)),
        "positive_weight_block_count": int(len(weights)),
        "zero_population_edge_block_count": int(len(assigned_population) - len(weights)),
        "tract_count": int(len(tract_ids)),
        "replicate_count": 80,
        "source_sha256": {
            key: _sha256(path) for key, path in {**sources, "boundary": boundary_path}.items()
        },
        "artifact_sha256": {
            covariate_path.name: _sha256(covariate_path),
            diagnostics_path.name: _sha256(diagnostics_path),
            schema_path.name: _sha256(schema_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "covariates": covariate_path,
        "diagnostics": diagnostics_path,
        "schema": schema_path,
        "manifest": manifest_path,
    }
