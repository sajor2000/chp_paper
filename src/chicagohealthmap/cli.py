from dataclasses import asdict
import json
from datetime import date
from json import JSONDecodeError
from pathlib import Path
from typing import Any

import typer
import yaml  # type: ignore[import-untyped]
from pydantic import ValidationError

from chicagohealthmap import __version__
from chicagohealthmap.analysis.dataset import (
    AnalyticDatasetError,
    build_chicago_case_study_dataset,
)
from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import (
    NormalizationError,
    normalize_all_public,
)
from chicagohealthmap.pipeline import RebuildError, rebuild_through_phase_4
from chicagohealthmap.ingest.schemas import SchemaContractError, load_schema_catalog
from chicagohealthmap.literature.audit import EvidenceAuditError, audit_gate_2_evidence
from chicagohealthmap.literature.screening import (
    ScreeningWorkbenchError,
    build_screening_batches,
    validate_screening_batches,
)
from chicagohealthmap.governance.readiness import ReadinessError, assess_readiness
from chicagohealthmap.governance.s4_dictionary import (
    S4DictionaryError,
    write_s4_dictionary_packet,
)
from chicagohealthmap.governance.s5_scorecard import (
    S5ScorecardError,
    write_s5_reconciliation_draft_packet,
    write_s5_scoring_artifacts_packet,
    write_s5_scorecard_packet,
)
from chicagohealthmap.sources.first_party import (
    SOURCE_ID,
    SNAPSHOT_SUBDIR,
    WEBSITE_SOURCE_SPEC,
    ArchiveSafetyError,
    FirstPartyInventory,
    FirstPartyValidationError,
    WebsiteArchiveExpectation,
    WebsiteArchiveSettings,
    inventory_first_party,
    preserve_first_party,
    preserve_website_archives,
)
from chicagohealthmap.sources.http import AcquisitionError, HttpAcquirer
from chicagohealthmap.sources.adapters.census import CensusAcsAdapter, CensusTigerAdapter
from chicagohealthmap.sources.adapters.catalog import (
    CatalogAdapter,
    CatalogResponseError,
    verify_frozen_catalog_snapshot,
)
from chicagohealthmap.sources.adapters.socrata import (
    SocrataAdapter,
    SocrataResponseError,
    verify_frozen_socrata_snapshot,
)
from chicagohealthmap.sources.models import SnapshotManifest, SourceSpec, Transport
from chicagohealthmap.sources.registry import (
    export_acquisition_matrix_bytes,
    load_registry,
)
from chicagohealthmap.sources.snapshot import (
    SnapshotWriter,
    SnapshotError,
    SnapshotExistsError,
    sha256_file,
)
from chicagohealthmap.provenance.citations import CitationError, write_citations
from chicagohealthmap.provenance.lineage import (
    LineageError,
    build_project_provenance,
    verify_project_provenance,
)
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.audit import (
    ManuscriptAuditError,
    audit_manuscript_control,
)
from chicagohealthmap.manuscript.gates import (
    ManuscriptGateError,
    evaluate_manuscript_gates,
    verify_active_manuscript_ledgers,
)
from chicagohealthmap.manuscript.handoffs import HandoffError, build_agent_handoff
from chicagohealthmap.manuscript.ledgers import LedgerError, initialize_ledgers
from chicagohealthmap.manuscript.packets import build_control_packets

app = typer.Typer(no_args_is_help=True)
sources_app = typer.Typer(no_args_is_help=True)
ehr_app = typer.Typer(no_args_is_help=True)
external_app = typer.Typer(no_args_is_help=True)
provenance_app = typer.Typer(no_args_is_help=True)
manuscript_app = typer.Typer(no_args_is_help=True)
evidence_app = typer.Typer(no_args_is_help=True)
screening_app = typer.Typer(no_args_is_help=True)
governance_app = typer.Typer(no_args_is_help=True)
s4_dictionary_app = typer.Typer(no_args_is_help=True)
s5_scorecard_app = typer.Typer(no_args_is_help=True)
analysis_app = typer.Typer(no_args_is_help=True)
app.add_typer(sources_app, name="sources")
app.add_typer(ehr_app, name="ehr")
app.add_typer(external_app, name="external")
app.add_typer(provenance_app, name="provenance")
app.add_typer(manuscript_app, name="manuscript")
app.add_typer(evidence_app, name="evidence")
evidence_app.add_typer(screening_app, name="screening")
app.add_typer(governance_app, name="governance")
governance_app.add_typer(s4_dictionary_app, name="s4-dictionary")
governance_app.add_typer(s5_scorecard_app, name="s5-scorecard")
app.add_typer(analysis_app, name="analysis")


@app.callback()
def main() -> None:
    """Run Chicago Health Map scientific pipelines."""


@app.command()
def version() -> None:
    typer.echo(f"chicagohealthmap {__version__}")


@analysis_app.command("build-dataset")
def analysis_build_dataset_command(
    output_dir: Path = typer.Option(..., "--output-dir", file_okay=False),
    root: Path = typer.Option(Path.cwd(), "--root", file_okay=False),
    output_stem: str = typer.Option(
        "chicago_case_studies_analytic",
        "--output-stem",
        help="Artifact filename stem; the historical default is preserved.",
    ),
) -> None:
    """Build the frozen Chicago case-study analytic dataset from local snapshots."""

    try:
        artifacts = build_chicago_case_study_dataset(
            root=root,
            output_dir=output_dir,
            output_stem=output_stem,
        )
        assert artifacts.source_join_manifest_path is not None
        assert artifacts.data_book_csv_path is not None
        assert artifacts.data_book_html_path is not None
        manifest = json.loads(artifacts.manifest_path.read_text(encoding="utf-8"))
    except (AnalyticDatasetError, OSError, ValueError, JSONDecodeError) as error:
        typer.echo(f"Analytic dataset build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(
        json.dumps(
            {
                "dataset_id": manifest["dataset_id"],
                "row_count": manifest["row_count"],
                "parquet_path": artifacts.parquet_path.as_posix(),
                "csv_path": artifacts.csv_path.as_posix(),
                "schema_path": artifacts.schema_path.as_posix(),
                "lineage_path": artifacts.lineage_path.as_posix(),
                "manifest_path": artifacts.manifest_path.as_posix(),
                "source_join_manifest_path": artifacts.source_join_manifest_path.as_posix(),
                "data_book_csv_path": artifacts.data_book_csv_path.as_posix(),
                "data_book_html_path": artifacts.data_book_html_path.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )


@evidence_app.command("audit")
def evidence_audit_command(
    gate: int = typer.Option(..., "--gate"),
    snapshot_date: str = typer.Option(..., "--snapshot-date"),
    check: bool = typer.Option(False, "--check"),
) -> None:
    """Audit frozen literature/evidence artifacts without authorizing analysis."""

    if gate != 2:
        raise typer.BadParameter("only --gate 2 is currently supported")
    try:
        report = audit_gate_2_evidence(ProjectPaths.discover().root, snapshot_date)
    except (EvidenceAuditError, OSError, ValidationError, yaml.YAMLError, ValueError) as error:
        typer.echo(f"Evidence audit failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))
    if check and report.status != "passed":
        typer.echo("Evidence audit check failed: Gate 2 remains open", err=True)
        raise typer.Exit(code=1)


@screening_app.command("build")
def evidence_screening_build_command(
    snapshot_date: str = typer.Option(..., "--snapshot-date"),
    batch_size: int = typer.Option(..., "--batch-size"),
    output_dir: Path = typer.Option(..., "--output-dir", file_okay=False),
    force: bool = typer.Option(False, "--force"),
) -> None:
    """Build PubMed title/abstract screening batch CSVs."""

    try:
        report = build_screening_batches(
            ProjectPaths.discover().root,
            snapshot_date,
            output_dir,
            batch_size=batch_size,
            force=force,
        )
    except (ScreeningWorkbenchError, OSError, ValueError) as error:
        typer.echo(f"Evidence screening build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))


@screening_app.command("validate")
def evidence_screening_validate_command(
    snapshot_date: str = typer.Option(..., "--snapshot-date"),
    input_dir: Path = typer.Option(..., "--input-dir", file_okay=False),
    require_complete: bool = typer.Option(False, "--require-complete"),
) -> None:
    """Validate returned PubMed screening batch CSVs without closing Gate 2."""

    try:
        report = validate_screening_batches(
            ProjectPaths.discover().root,
            snapshot_date,
            input_dir,
            require_complete=require_complete,
        )
    except (ScreeningWorkbenchError, OSError, ValueError) as error:
        typer.echo(f"Evidence screening validation failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))


@governance_app.command("readiness")
def governance_readiness_command(
    through: str = typer.Option(..., "--through"),
    check: bool = typer.Option(False, "--check"),
) -> None:
    """Assess non-authorizing readiness for scientific gate progression."""

    try:
        report = assess_readiness(ProjectPaths.discover().root, through=through)
    except (ReadinessError, OSError, ValueError) as error:
        typer.echo(f"Governance readiness failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))
    if check and not report.analysis_authorized:
        typer.echo("Governance readiness check failed: S4-S6 readiness remains blocked", err=True)
        raise typer.Exit(code=1)


@s4_dictionary_app.command("build")
def governance_s4_dictionary_build_command(
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Write the accepted ChicagoHealthMap S4 methods dictionary packet."""

    paths = ProjectPaths.discover()
    try:
        path = write_s4_dictionary_packet(paths.root, output)
    except (S4DictionaryError, OSError, ValueError) as error:
        typer.echo(f"S4 dictionary build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    try:
        rendered = path.resolve().relative_to(paths.root.resolve()).as_posix()
    except ValueError:
        rendered = path.resolve().as_posix()
    typer.echo(json.dumps({"output_path": rendered}, indent=2, sort_keys=True))


@s5_scorecard_app.command("build")
def governance_s5_scorecard_build_command(
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Write the non-authorizing S5 outcome-blinded scorecard template."""

    paths = ProjectPaths.discover()
    try:
        path = write_s5_scorecard_packet(paths.root, output)
    except (S5ScorecardError, OSError, ValueError) as error:
        typer.echo(f"S5 scorecard build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    try:
        rendered = path.resolve().relative_to(paths.root.resolve()).as_posix()
    except ValueError:
        rendered = path.resolve().as_posix()
    typer.echo(json.dumps({"output_path": rendered}, indent=2, sort_keys=True))


@s5_scorecard_app.command("worksheets")
def governance_s5_scorecard_worksheets_command(
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Write blinded scorer worksheets and reconciliation templates."""

    paths = ProjectPaths.discover()
    try:
        path = write_s5_scoring_artifacts_packet(paths.root, output)
    except (S5ScorecardError, OSError, ValueError) as error:
        typer.echo(f"S5 worksheet build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    try:
        rendered = path.resolve().relative_to(paths.root.resolve()).as_posix()
    except ValueError:
        rendered = path.resolve().as_posix()
    typer.echo(json.dumps({"output_path": rendered}, indent=2, sort_keys=True))


@s5_scorecard_app.command("reconcile")
def governance_s5_scorecard_reconcile_command(
    input_path: Path = typer.Option(..., "--input", dir_okay=False),
    output: Path = typer.Option(..., "--output", dir_okay=False),
) -> None:
    """Write a non-authorizing S5 reconciliation draft from completed worksheets."""

    paths = ProjectPaths.discover()
    try:
        path = write_s5_reconciliation_draft_packet(input_path, output, root=paths.root)
    except (S5ScorecardError, OSError, ValueError) as error:
        typer.echo(f"S5 reconciliation draft build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    try:
        rendered = path.resolve().relative_to(paths.root.resolve()).as_posix()
    except ValueError:
        rendered = path.resolve().as_posix()
    typer.echo(json.dumps({"output_path": rendered}, indent=2, sort_keys=True))


@app.command("rebuild")
def rebuild_command(
    through_phase: int = typer.Option(..., "--through-phase"),
    offline: bool = typer.Option(False, "--offline"),
    root: Path = typer.Option(Path.cwd(), "--root", file_okay=False),
) -> None:
    """Rebuild and verify the offline source/provenance foundation through Phase 4."""

    if through_phase != 4:
        raise typer.BadParameter("only --through-phase 4 is currently authorized")
    if not offline:
        typer.echo(
            "Offline rebuild requires --offline; network rebuild is not authorized", err=True
        )
        raise typer.Exit(code=1)
    try:
        report = rebuild_through_phase_4(root, offline=True)
    except (
        RebuildError,
        NormalizationError,
        CitationError,
        LineageError,
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Offline rebuild failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(report.to_jsonable(), indent=2, sort_keys=True))


@manuscript_app.command("init")
def manuscript_init_command() -> None:
    """Initialize empty, version-bound manuscript control ledgers."""
    paths = ProjectPaths.discover()
    try:
        contracts = load_manuscript_contracts(paths.root)
        created = initialize_ledgers(
            paths.root / "outputs" / "manuscript" / "control",
            contracts,
        )
    except (
        LedgerError,
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Manuscript initialization failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Initialized manuscript control artifacts: {len(created)}")


@manuscript_app.command("gates")
def manuscript_gates_command(
    check: bool = typer.Option(False, "--check"),
) -> None:
    """Report manuscript/scientific gate state and fail on blocked authority."""
    if not check:
        raise typer.BadParameter("gate validation requires --check", param_hint="--check")
    try:
        paths = ProjectPaths.discover()
        report = evaluate_manuscript_gates(paths)
        contracts = load_manuscript_contracts(paths.root)
        ledger_report = verify_active_manuscript_ledgers(paths, contracts)
        if ledger_report is not None:
            if ledger_report.open_critical_issues:
                raise ManuscriptGateError("open critical manuscript issue")
            if ledger_report.open_important_issues:
                raise ManuscriptGateError("open important manuscript issue")
    except (
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Manuscript gates failed: {error}", err=True)
        raise typer.Exit(code=1) from None

    typer.echo(json.dumps(asdict(report), indent=2, sort_keys=True))
    if "M0" not in report.passed or "M1" not in report.passed:
        typer.echo("Manuscript gates failed: required authority remains blocked", err=True)
        raise typer.Exit(code=1)


@manuscript_app.command("packets")
def manuscript_packets_command(
    build: bool = typer.Option(False, "--build"),
) -> None:
    """Build deterministic pre-result outline and case packets."""
    if not build:
        raise typer.BadParameter("packet generation requires --build", param_hint="--build")
    try:
        created = build_control_packets(ProjectPaths.discover())
    except (
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Manuscript packet build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Built manuscript control packets: {len(created)}")


@manuscript_app.command("handoff")
def manuscript_handoff_command(
    role: str = typer.Option(..., "--role"),
) -> None:
    """Build one role-scoped, disclosure-safe agent handoff."""
    paths = ProjectPaths.discover()
    try:
        path = build_agent_handoff(paths, role)
    except (
        HandoffError,
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Manuscript handoff failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(path.relative_to(paths.root).as_posix())


@manuscript_app.command("audit")
def manuscript_audit_command(
    control: bool = typer.Option(False, "--control"),
) -> None:
    """Audit manuscript-control artifacts without authorizing results."""
    if not control:
        raise typer.BadParameter("control audit requires --control", param_hint="--control")
    try:
        report = audit_manuscript_control(ProjectPaths.discover())
    except (
        ManuscriptAuditError,
        OSError,
        ValidationError,
        yaml.YAMLError,
        ValueError,
    ) as error:
        typer.echo(f"Manuscript control audit failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(json.dumps(asdict(report), indent=2, sort_keys=True))


def _require_all(value: bool) -> None:
    if not value:
        raise typer.BadParameter("this offline operation requires --all", param_hint="--all")


@external_app.command("normalize")
def normalize_external_command(all_sources: bool = typer.Option(False, "--all")) -> None:
    """Normalize all verified frozen public snapshots without network access."""

    _require_all(all_sources)
    try:
        report = normalize_all_public(ProjectPaths.discover())
    except (NormalizationError, OSError, ValidationError, yaml.YAMLError) as error:
        typer.echo(f"Public normalization failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Normalized public tables: {len(report.row_counts)}")
    typer.echo(f"Normalized public rows: {sum(report.row_counts.values())}")


@provenance_app.command("build")
def build_provenance_command(all_sources: bool = typer.Option(False, "--all")) -> None:
    """Build complete citations and field-level provenance reports."""

    _require_all(all_sources)
    try:
        artifacts = build_project_provenance(ProjectPaths.discover())
    except (CitationError, LineageError, NormalizationError, OSError, ValidationError) as error:
        typer.echo(f"Provenance build failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Provenance artifacts: {len(artifacts)}")


@provenance_app.command("verify")
def verify_provenance_command(all_sources: bool = typer.Option(False, "--all")) -> None:
    """Fail unless public fields, citations, and artifact references are complete."""

    _require_all(all_sources)
    try:
        verify_project_provenance(ProjectPaths.discover())
    except (CitationError, LineageError, NormalizationError, OSError, ValidationError) as error:
        typer.echo(f"Provenance verification failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo("Provenance verification passed")


@sources_app.command("citations")
def source_citations_command(citation_format: str = typer.Option("bibtex", "--format")) -> None:
    """Render disclosure-safe citations for all registered source snapshots."""

    if citation_format not in {"bibtex", "csl-json"}:
        raise typer.BadParameter("must be bibtex or csl-json", param_hint="--format")
    try:
        csl_path, bib_path = write_citations(ProjectPaths.discover())
        selected = bib_path if citation_format == "bibtex" else csl_path
        typer.echo(selected.read_text(encoding="utf-8"), nl=False)
    except (CitationError, NormalizationError, OSError, ValidationError, yaml.YAMLError) as error:
        typer.echo(f"Citation rendering failed: {error}", err=True)
        raise typer.Exit(code=1) from None


def _first_party_config(paths: ProjectPaths) -> dict[str, Any]:
    config_path = paths.root / "config" / "first_party_sources.yml"
    loaded = yaml.safe_load(config_path.read_text())
    if not isinstance(loaded, dict):
        raise typer.BadParameter("first-party source configuration must be a mapping")
    return loaded


def _load_first_party_config(paths: ProjectPaths) -> dict[str, Any]:
    try:
        return _first_party_config(paths)
    except (OSError, yaml.YAMLError):
        typer.echo("First-party source configuration is missing or invalid", err=True)
        raise typer.Exit(code=1) from None


def _first_party_settings(paths: ProjectPaths) -> tuple[str, date, tuple[str, ...]]:
    config = _load_first_party_config(paths)
    try:
        configured_source = config["source_id"]
        raw_snapshot_date = config["snapshot_date"]
        raw_files = config["files"]
        if not isinstance(configured_source, str) or not configured_source:
            raise ValueError
        if not isinstance(raw_snapshot_date, str):
            raise ValueError
        configured_date = date.fromisoformat(raw_snapshot_date)
        if raw_snapshot_date != configured_date.isoformat():
            raise ValueError
        if (
            not isinstance(raw_files, list)
            or not raw_files
            or any(not isinstance(name, str) or not name for name in raw_files)
            or len(set(raw_files)) != len(raw_files)
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        typer.echo("First-party source configuration is missing or invalid", err=True)
        raise typer.Exit(code=1) from None
    return configured_source, configured_date, tuple(raw_files)


def _website_archive_settings(paths: ProjectPaths) -> WebsiteArchiveSettings:
    config = _load_first_party_config(paths)
    try:
        raw = config["website_methods"]
        if not isinstance(raw, dict):
            raise ValueError
        source_id = raw["source_id"]
        raw_date = raw["snapshot_date"]
        expected_archive_count = raw["expected_archive_count"]
        expected_member_count = raw["expected_member_count"]
        expected_duplicate_count = raw["expected_duplicate_content_count"]
        raw_archives = raw["archives"]
        if not isinstance(source_id, str) or source_id != WEBSITE_SOURCE_SPEC.source_id:
            raise ValueError
        if not isinstance(raw_date, str):
            raise ValueError
        snapshot_date = date.fromisoformat(raw_date)
        if raw_date != snapshot_date.isoformat():
            raise ValueError
        counts = (expected_archive_count, expected_member_count, expected_duplicate_count)
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts
        ):
            raise ValueError
        if not isinstance(raw_archives, list) or len(raw_archives) != expected_archive_count:
            raise ValueError
        archive_settings: list[WebsiteArchiveExpectation] = []
        for item in raw_archives:
            if not isinstance(item, dict) or set(item) != {"filename", "sha256"}:
                raise ValueError
            filename = item["filename"]
            digest = item["sha256"]
            if (
                not isinstance(filename, str)
                or not filename
                or Path(filename).name != filename
                or not isinstance(digest, str)
                or len(digest) != 64
                or any(character not in "0123456789abcdef" for character in digest)
            ):
                raise ValueError
            archive_settings.append(WebsiteArchiveExpectation(filename=filename, sha256=digest))
        if len({archive.filename.casefold() for archive in archive_settings}) != len(
            archive_settings
        ):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        typer.echo("Website archive configuration is missing or invalid", err=True)
        raise typer.Exit(code=1) from None
    return WebsiteArchiveSettings(
        source_id=source_id,
        snapshot_date=snapshot_date,
        expected_archive_count=expected_archive_count,
        expected_member_count=expected_member_count,
        expected_duplicate_content_count=expected_duplicate_count,
        archives=tuple(archive_settings),
    )


def _print_inventory(inventory: FirstPartyInventory) -> None:
    typer.echo(f"Expected files: {inventory.expected_count}")
    typer.echo(f"Observed files: {inventory.observed_count}")
    typer.echo(f"Observed empty files: {len(inventory.observed_empty_files)}")
    typer.echo(f"Missing files: {len(inventory.missing_files)}")
    typer.echo(f"Unexpected files: {len(inventory.unexpected_files)}")
    if inventory.methods_review_files:
        typer.echo("Methods review: " + ", ".join(inventory.methods_review_files))


def _ehr_blocker_payload(paths: ProjectPaths, snapshot_date: date) -> dict[str, Any]:
    """Build a disclosure-safe schema-evidence checkpoint without reading source rows."""

    catalog = load_schema_catalog(paths.root / "config" / "first_party_schemas.yml")
    fields = [field for table in catalog.tables.values() for field in table.fields]
    verified = sum(field.evidence_status.value == "verified" for field in fields)
    usable = sum(table.analysis_usable for table in catalog.tables.values())
    evidence = {
        "tables": len(catalog.tables),
        "field_positions": len(fields),
        "verified_positions": verified,
        "unverified_positions": len(fields) - verified,
        "analysis_usable_tables": usable,
    }
    findings: list[dict[str, Any]] = []
    if evidence["unverified_positions"] or usable != len(catalog.tables):
        findings.append(
            {
                "code": "unverified_schema",
                "severity": "fatal",
                "message": "semantic field contracts are not fully evidence-verified",
                "affected_row_count": 0,
            }
        )
    return {
        "source_id": SOURCE_ID,
        "snapshot_id": f"{SOURCE_ID}_{snapshot_date.isoformat()}",
        "gate_3_status": "closed" if findings else "eligible_for_review",
        "source_rows_read": 0,
        "schema_evidence": evidence,
        "findings": findings,
    }


def _write_ehr_checkpoint(paths: ProjectPaths, payload: dict[str, Any]) -> None:
    quality_dir = paths.outputs / "quality"
    quality_dir.mkdir(parents=True, exist_ok=True)
    (quality_dir / "ehr_quality.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    evidence = payload["schema_evidence"]
    summary = (
        "# EHR quality checkpoint\n\n"
        f"**Gate 3: {str(payload['gate_3_status']).upper()}**\n\n"
        "No source rows or values were read. This report contains schema-evidence counts only.\n\n"
        f"- tables: {evidence['tables']}\n"
        f"- field positions: {evidence['field_positions']}\n"
        f"- verified positions: {evidence['verified_positions']}\n"
        f"- unverified positions: {evidence['unverified_positions']}\n"
        f"- analysis-usable tables: {evidence['analysis_usable_tables']}\n"
    )
    (quality_dir / "ehr_quality_summary.md").write_text(summary, encoding="utf-8")


def _run_ehr_schema_checkpoint(snapshot_date: str) -> None:
    paths = ProjectPaths.discover()
    _, configured_date, _ = _first_party_settings(paths)
    try:
        parsed_date = date.fromisoformat(snapshot_date)
    except ValueError as error:
        raise typer.BadParameter(
            "must use ISO YYYY-MM-DD format", param_hint="--snapshot-date"
        ) from error
    if snapshot_date != parsed_date.isoformat() or parsed_date != configured_date:
        raise typer.BadParameter(
            f"must match configured snapshot date {configured_date.isoformat()}",
            param_hint="--snapshot-date",
        )
    try:
        payload = _ehr_blocker_payload(paths, parsed_date)
        _write_ehr_checkpoint(paths, payload)
    except (OSError, SchemaContractError):
        typer.echo("EHR schema checkpoint could not be generated", err=True)
        raise typer.Exit(code=1) from None
    if payload["gate_3_status"] == "closed":
        evidence = payload["schema_evidence"]
        typer.echo(
            "Gate 3 closed: "
            f"{evidence['unverified_positions']} unverified field positions across "
            f"{evidence['tables']} tables; no source rows read and no Parquet written",
            err=True,
        )
        raise typer.Exit(code=1)
    typer.echo("Schema evidence checkpoint is eligible for scientific review")


@ehr_app.command("ingest")
def ehr_ingest_command(snapshot_date: str = typer.Option(...)) -> None:
    """Stop before EHR ingestion unless every semantic position is verified."""

    _run_ehr_schema_checkpoint(snapshot_date)


@ehr_app.command("quality")
def ehr_quality_command(snapshot_date: str = typer.Option(...)) -> None:
    """Write a disclosure-safe Gate 3 checkpoint without guessing source semantics."""

    _run_ehr_schema_checkpoint(snapshot_date)


@sources_app.command("preserve-first-party")
def preserve_first_party_command(
    source_root: Path = typer.Option(..., exists=True, file_okay=False, readable=True),
    snapshot_date: str = typer.Option(...),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Inventory and immutably preserve the CAPriCORN/ChicagoHealthMap exports."""
    paths = ProjectPaths.discover()
    _, configured_snapshot_date, expected = _first_party_settings(paths)
    try:
        parsed_snapshot_date = date.fromisoformat(snapshot_date)
    except ValueError as error:
        raise typer.BadParameter(
            "must use ISO YYYY-MM-DD format", param_hint="--snapshot-date"
        ) from error
    if snapshot_date != parsed_snapshot_date.isoformat():
        raise typer.BadParameter("must use ISO YYYY-MM-DD format", param_hint="--snapshot-date")
    if parsed_snapshot_date != configured_snapshot_date:
        raise typer.BadParameter(
            f"must match configured snapshot date {configured_snapshot_date.isoformat()}",
            param_hint="--snapshot-date",
        )
    try:
        inventory = inventory_first_party(source_root, expected)
    except (OSError, ValidationError):
        typer.echo("Could not inventory the supplied source exports", err=True)
        raise typer.Exit(code=1) from None
    _print_inventory(inventory)

    if inventory.missing_files:
        typer.echo("Cannot preserve: missing expected export(s)", err=True)
        raise typer.Exit(code=1)
    if dry_run:
        typer.echo("Dry run: no files written")
        return

    try:
        manifest = preserve_first_party(source_root, paths.sources, parsed_snapshot_date, expected)
    except SnapshotExistsError:
        typer.echo(f"Snapshot already finalized for {parsed_snapshot_date.isoformat()}", err=True)
        raise typer.Exit(code=1) from None
    except FirstPartyValidationError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except (SnapshotError, OSError, ValidationError):
        typer.echo("Snapshot preservation could not be completed", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Preserved files: {len(manifest.files)}")
    typer.echo(
        "Snapshot: "
        + str(paths.sources / SNAPSHOT_SUBDIR / "snapshots" / parsed_snapshot_date.isoformat())
    )


def _canonical_registry_paths(paths: ProjectPaths) -> tuple[Path, Path]:
    return (
        paths.root / "config" / "source_registry.yml",
        paths.root / "sources" / "public" / "_registry" / "acquisition_matrix.csv",
    )


def _load_canonical_registry(paths: ProjectPaths):
    registry_path, _ = _canonical_registry_paths(paths)
    try:
        return load_registry(registry_path)
    except (OSError, UnicodeError, yaml.YAMLError, ValidationError):
        typer.echo("Canonical source registry is missing or invalid", err=True)
        raise typer.Exit(code=1) from None


def _public_source_spec(source) -> SourceSpec:
    try:
        transport = Transport(source.transport)
    except ValueError:
        transport = Transport.http_file
    return SourceSpec(
        source_id=source.source_id,
        organization=source.organization,
        dataset_title=source.dataset_title,
        transport=transport,
        landing_url=source.landing_url,
        documentation_url=source.documentation_url,
        license=source.license,
        snapshot_subdir=f"public/{source.source_id}",
    )


def _expected_content_types(endpoint: str) -> tuple[str, ...]:
    suffix = Path(endpoint.split("?", 1)[0]).suffix.casefold()
    return {
        ".csv": ("text/csv", "application/csv", "application/octet-stream"),
        ".geojson": ("application/geo+json", "application/json"),
        ".json": ("application/json",),
        ".zip": ("application/zip", "application/octet-stream"),
    }.get(suffix, ())


def _parse_snapshot_date(value: str) -> date:
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter(
            "must use ISO YYYY-MM-DD format", param_hint="--snapshot-date"
        ) from error
    if value != parsed.isoformat():
        raise typer.BadParameter("must use ISO YYYY-MM-DD format", param_hint="--snapshot-date")
    return parsed


def _select_registry_sources(registry, *, all_sources: bool, source_id: str | None):
    if all_sources == (source_id is not None):
        raise typer.BadParameter("select exactly one of --all or --source")
    if all_sources:
        return tuple(sorted(registry.sources, key=lambda item: item.source_id))
    source = registry.by_id.get(source_id)
    if source is None:
        raise typer.BadParameter(f"unknown source: {source_id}", param_hint="--source")
    return (source,)


def _census_adapter(source):
    parts = source.source_id.split("_")
    if source.source_id.startswith("census_acs_"):
        year = int(parts[2])
        groups = tuple(source.request.parameters["tables"].split(","))
        return CensusAcsAdapter(year=year, groups=groups)
    if source.source_id.startswith("census_tiger_"):
        return CensusTigerAdapter(year=int(parts[2]))
    return None


def _socrata_adapter(source):
    if source.transport == "socrata":
        return SocrataAdapter()
    return None


def _catalog_adapter(source):
    if source.source_id in {
        "chicago_health_atlas_life_expectancy",
        "chicago_health_atlas_mortality",
        "cdc_svi_2022_tract",
        "hrsa_health_centers_current",
    }:
        return CatalogAdapter()
    return None


@sources_app.command("fetch")
def fetch_sources_command(
    all_sources: bool = typer.Option(False, "--all"),
    source_id: str | None = typer.Option(None, "--source"),
    snapshot_date: str = typer.Option(...),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    """Plan or acquire canonical public sources into immutable dated snapshots."""
    paths = ProjectPaths.discover()
    registry = _load_canonical_registry(paths)
    selected = _select_registry_sources(registry, all_sources=all_sources, source_id=source_id)
    parsed_date = _parse_snapshot_date(snapshot_date)

    for source in selected:
        final_path = (
            paths.sources / "public" / source.source_id / "snapshots" / parsed_date.isoformat()
        )
        if final_path.exists():
            typer.echo(
                f"Snapshot already finalized for {source.source_id} on {parsed_date.isoformat()}",
                err=True,
            )
            raise typer.Exit(code=1)

    for source in selected:
        census_adapter = _census_adapter(source)
        socrata_adapter = _socrata_adapter(source)
        catalog_adapter = _catalog_adapter(source)
        acquirer = HttpAcquirer(
            expected_content_types=_expected_content_types(str(source.endpoint_url))
        )
        if census_adapter is not None:
            plan = census_adapter.plan(source)
        elif socrata_adapter is not None:
            plan = socrata_adapter.plan(source)
        elif catalog_adapter is not None:
            plan = catalog_adapter.plan(source)
        else:
            plan = acquirer.plan(source)
        if dry_run:
            typer.echo(json.dumps(plan.model_dump(mode="json"), sort_keys=True))
            continue
        if census_adapter is not None:
            typer.echo(
                "Census live fetch is disabled; verify and reuse the frozen 2026-07-13 snapshot",
                err=True,
            )
            raise typer.Exit(code=1)
        if socrata_adapter is not None:
            if parsed_date.isoformat() != "2026-07-13":
                typer.echo(
                    "Socrata live fetch is disabled; use the verified frozen 2026-07-13 snapshot",
                    err=True,
                )
                raise typer.Exit(code=1)
            try:
                frozen = verify_frozen_socrata_snapshot(paths.root, source)
            except (SocrataResponseError, OSError, ValidationError):
                typer.echo(f"Frozen Socrata verification failed for {source.source_id}", err=True)
                raise typer.Exit(code=1) from None
            typer.echo(
                f"Reused verified frozen {source.source_id} snapshot {frozen.snapshot_date}: "
                f"{frozen.file_count} file(s), {frozen.row_count} row(s); "
                "no live download performed"
            )
            continue
        if catalog_adapter is not None:
            try:
                frozen_catalog = verify_frozen_catalog_snapshot(
                    paths.root, source, parsed_date.isoformat()
                )
            except (CatalogResponseError, OSError, ValidationError):
                typer.echo(f"Frozen catalog verification failed for {source.source_id}", err=True)
                raise typer.Exit(code=1) from None
            typer.echo(
                f"Reused verified frozen {source.source_id} snapshot "
                f"{frozen_catalog.snapshot_date}: {frozen_catalog.file_count} file(s), "
                f"{frozen_catalog.row_count} row(s); "
                "legacy layout retained; no live download performed"
            )
            continue
        try:
            with SnapshotWriter(paths, _public_source_spec(source), parsed_date) as writer:
                manifest = acquirer.fetch(source, writer)
        except SnapshotExistsError:
            typer.echo(
                f"Snapshot already finalized for {source.source_id} on {parsed_date.isoformat()}",
                err=True,
            )
            raise typer.Exit(code=1) from None
        except (AcquisitionError, SnapshotError, OSError, ValidationError):
            typer.echo(f"Acquisition failed for {source.source_id}", err=True)
            raise typer.Exit(code=1) from None
        typer.echo(f"Fetched {source.source_id}: {len(manifest.files)} file(s)")


@sources_app.command("list")
def list_sources_command() -> None:
    """List credential-free public-source identity and verification metadata."""
    paths = ProjectPaths.discover()
    registry = _load_canonical_registry(paths)
    for source in sorted(registry.sources, key=lambda item: item.source_id):
        typer.echo(
            "\t".join(
                (
                    source.source_id,
                    source.organization,
                    source.transport,
                    source.release,
                    source.verification.status,
                )
            )
        )


@sources_app.command("matrix")
def source_matrix_command(check: bool = typer.Option(False, "--check")) -> None:
    """Render or check the deterministic acquisition review matrix."""
    paths = ProjectPaths.discover()
    registry_path, matrix_path = _canonical_registry_paths(paths)
    try:
        rendered = export_acquisition_matrix_bytes(load_registry(registry_path))
        if check:
            if matrix_path.read_bytes() != rendered:
                typer.echo("Acquisition matrix differs from canonical registry", err=True)
                raise typer.Exit(code=1)
            typer.echo("Acquisition matrix matches canonical registry")
            return
        matrix_path.parent.mkdir(parents=True, exist_ok=True)
        matrix_path.write_bytes(rendered)
    except (OSError, yaml.YAMLError, ValidationError):
        typer.echo("Canonical source registry or acquisition matrix is unavailable", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Wrote acquisition matrix: {matrix_path}")


@sources_app.command("preserve-website-archives")
def preserve_website_archives_command(
    archives: list[Path] = typer.Option(
        ..., "--archive", exists=True, dir_okay=False, readable=True
    ),
    snapshot_date: str = typer.Option(...),
) -> None:
    """Preserve and safely extract exact Chicago Health Map website captures."""
    try:
        parsed_snapshot_date = date.fromisoformat(snapshot_date)
    except ValueError as error:
        raise typer.BadParameter(
            "must use ISO YYYY-MM-DD format", param_hint="--snapshot-date"
        ) from error
    if snapshot_date != parsed_snapshot_date.isoformat():
        raise typer.BadParameter("must use ISO YYYY-MM-DD format", param_hint="--snapshot-date")

    paths = ProjectPaths.discover()
    settings = _website_archive_settings(paths)
    if parsed_snapshot_date != settings.snapshot_date:
        raise typer.BadParameter(
            f"must match configured snapshot date {settings.snapshot_date.isoformat()}",
            param_hint="--snapshot-date",
        )
    try:
        report = preserve_website_archives(
            tuple(archives), paths.sources, parsed_snapshot_date, settings
        )
    except SnapshotExistsError:
        typer.echo(f"Snapshot already finalized for {snapshot_date}", err=True)
        raise typer.Exit(code=1) from None
    except (ArchiveSafetyError, SnapshotError, OSError, ValidationError) as error:
        typer.echo(f"Website archive preservation failed: {error}", err=True)
        raise typer.Exit(code=1) from None
    typer.echo(f"Archive records: {len(report.archives)}")
    typer.echo(f"Website members: {len(report.members)}")
    typer.echo(f"Duplicate content records: {len(report.duplicate_contents)}")
    typer.echo("Unsafe members: 0")
    typer.echo(
        "Snapshot: "
        + str(
            paths.sources
            / WEBSITE_SOURCE_SPEC.snapshot_subdir
            / "snapshots"
            / parsed_snapshot_date.isoformat()
        )
    )


def _verify_first_party_source(source: str) -> None:
    """Verify the finalized first-party snapshot against its manifest."""
    paths = ProjectPaths.discover()
    configured_source, snapshot_date, expected_files = _first_party_settings(paths)
    if source != configured_source or source != SOURCE_ID:
        raise typer.BadParameter(f"unknown source: {source}", param_hint="--source")

    snapshot = paths.sources / SNAPSHOT_SUBDIR / "snapshots" / snapshot_date.isoformat()
    try:
        manifest = SnapshotManifest.model_validate(
            json.loads((snapshot / "manifest.json").read_text())
        )
    except (OSError, JSONDecodeError, ValidationError):
        typer.echo("Snapshot metadata is missing or invalid", err=True)
        raise typer.Exit(code=1) from None

    identity_errors: list[str] = []
    if manifest.source_id != configured_source:
        identity_errors.append("Manifest source mismatch")
    if manifest.snapshot_date != snapshot_date:
        identity_errors.append("Manifest snapshot date mismatch")
    expected_snapshot_id = f"{configured_source}_{snapshot_date.isoformat()}"
    if manifest.snapshot_id != expected_snapshot_id:
        identity_errors.append("Manifest snapshot identity mismatch")

    expected_paths = {f"original/{name}" for name in expected_files}
    records = {record.path: record for record in manifest.files}
    manifest_duplicates = len(manifest.files) - len(records)
    manifest_paths = set(records)
    manifest_missing = expected_paths - manifest_paths
    manifest_unexpected = manifest_paths - expected_paths

    original = snapshot / "original"
    try:
        observed = {
            path.relative_to(snapshot).as_posix() for path in original.rglob("*") if path.is_file()
        }
    except OSError:
        typer.echo("Snapshot files could not be inventoried", err=True)
        raise typer.Exit(code=1) from None
    missing_paths = expected_paths - observed
    unexpected_paths = observed - expected_paths

    matching = 0
    mismatching = 0
    try:
        for relative_path in sorted(expected_paths & manifest_paths & observed):
            record = records[relative_path]
            candidate = snapshot / relative_path
            if (
                candidate.stat().st_size == record.byte_count
                and sha256_file(candidate) == record.sha256
            ):
                matching += 1
            else:
                mismatching += 1
    except OSError:
        typer.echo("Snapshot files could not be read", err=True)
        raise typer.Exit(code=1) from None

    for message in identity_errors:
        typer.echo(message)
    typer.echo(f"Manifest duplicate entries: {manifest_duplicates}")
    typer.echo(f"Manifest missing entries: {len(manifest_missing)}")
    typer.echo(f"Manifest unexpected entries: {len(manifest_unexpected)}")
    typer.echo(f"Matching checksums: {matching}")
    typer.echo(f"Mismatching checksums: {mismatching}")
    typer.echo(f"Missing files: {len(missing_paths)}")
    typer.echo(f"Unexpected files: {len(unexpected_paths)}")
    if (
        identity_errors
        or manifest_duplicates
        or manifest_missing
        or manifest_unexpected
        or mismatching
        or missing_paths
        or unexpected_paths
    ):
        raise typer.Exit(code=1)


def _verify_public_snapshot(snapshot: Path, source_id: str) -> None:
    try:
        if (
            snapshot.is_symlink()
            or (snapshot / "manifest.json").is_symlink()
            or (snapshot / "checksums.sha256").is_symlink()
        ):
            raise ValueError("snapshot metadata must not use symlinks")
        manifest = SnapshotManifest.model_validate_json((snapshot / "manifest.json").read_text())
        if manifest.source_id != source_id or manifest.snapshot_date.isoformat() != snapshot.name:
            raise ValueError("snapshot identity mismatch")
        if manifest.snapshot_id != f"{source_id}_{snapshot.name}":
            raise ValueError("snapshot ID mismatch")
        paths = [record.path for record in manifest.files]
        if len(paths) != len(set(paths)):
            raise ValueError("duplicate manifest paths")
        snapshot_root = snapshot.resolve(strict=True)
        for record in manifest.files:
            candidate = snapshot / record.path
            if (
                candidate.is_symlink()
                or candidate.resolve(strict=True).parent != snapshot_root / Path(record.path).parent
            ):
                raise ValueError("snapshot path escape")
            if candidate.stat().st_size != record.byte_count:
                raise ValueError("snapshot byte count mismatch")
            if sha256_file(candidate) != record.sha256:
                raise ValueError("snapshot checksum mismatch")
        expected_checksums = "".join(
            f"{record.sha256}  {record.path}\n"
            for record in sorted(manifest.files, key=lambda x: x.path)
        )
        if (snapshot / "checksums.sha256").read_text() != expected_checksums:
            raise ValueError("checksum inventory mismatch")
        observed = {
            path.relative_to(snapshot).as_posix()
            for path in snapshot.rglob("*")
            if path.is_file() and path.name not in {"manifest.json", "checksums.sha256"}
        }
        if observed != set(paths):
            raise ValueError("snapshot file inventory mismatch")
    except (OSError, UnicodeError, ValueError, ValidationError):
        typer.echo("Public snapshot verification failed", err=True)
        raise typer.Exit(code=1) from None


@sources_app.command("verify")
def verify_source(
    all_sources: bool = typer.Option(False, "--all"),
    source: str | None = typer.Option(None, "--source"),
) -> None:
    """Verify finalized first-party or canonical public-source snapshots."""
    if not all_sources and source == SOURCE_ID:
        _verify_first_party_source(source)
        return

    paths = ProjectPaths.discover()
    registry = _load_canonical_registry(paths)
    selected = _select_registry_sources(registry, all_sources=all_sources, source_id=source)
    snapshots: list[tuple[Path, str]] = []
    for selected_source in selected:
        public_root = paths.sources / "public"
        source_root = public_root / selected_source.source_id
        root = source_root / "snapshots"
        try:
            if (
                paths.sources.is_symlink()
                or public_root.is_symlink()
                or source_root.is_symlink()
                or root.is_symlink()
            ):
                raise ValueError("public snapshot collection path escape")
            if not root.exists():
                continue
            if source_root.resolve(strict=True).parent != public_root.resolve(
                strict=True
            ) or root.resolve(strict=True).parent != source_root.resolve(strict=True):
                raise ValueError("public snapshot collection path escape")
            snapshots.extend(
                (candidate, selected_source.source_id)
                for candidate in sorted(root.iterdir())
                if candidate.is_dir()
            )
        except (OSError, ValueError):
            typer.echo("Public snapshot verification failed", err=True)
            raise typer.Exit(code=1) from None
    for snapshot, source_id in snapshots:
        _verify_public_snapshot(snapshot, source_id)
    typer.echo(f"Verified public snapshots: {len(snapshots)}")
