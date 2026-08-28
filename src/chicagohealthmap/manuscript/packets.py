"""Deterministic, gate-aware manuscript outline and case control packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256
import json
from json import JSONDecodeError
from pathlib import Path
import re
from typing import Any

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.gates import evaluate_manuscript_gates


class ManuscriptPacketError(ValueError):
    """Raised when packet authority or a destination is unsafe or invalid."""


CASE_HEADINGS = (
    "Why this case",
    "Prespecified estimand",
    "Eligibility and data quality",
    "Pattern and comparator contract",
    "Primary estimate contract",
    "Supportive analyses contract",
    "Interpretive boundary",
    "Platform lesson",
)

_PROVISIONAL_NAMES = (
    "Cardiometabolic hypertension and diabetes",
    "Respiratory COPD",
)
_SELECTION_PATH = Path("outputs/governance/case_selection.json")
_SIGNED_SAP_PATH = Path("outputs/governance/signed_sap.json")
_OUTPUT_PATH = Path("outputs/manuscript/control")
_SELECTION_FIELDS = frozenset(
    {
        "record_type",
        "gate",
        "status",
        "outcome_blinded",
        "cases",
        "approval",
    }
)
_SAP_FIELDS = frozenset(
    {
        "record_type",
        "status",
        "version",
        "path",
        "sha256",
        "case_ids",
        "approval",
    }
)
_APPROVAL_FIELDS = frozenset({"human", "date", "decision"})
_CASE_FIELDS = frozenset({"order", "case_id", "display_name"})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_CASE_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
_DISPLAY_NAME = re.compile(r"[A-Za-z][A-Za-z0-9 /(),.&+=\-'\u2013\u2014]{1,119}\Z")
_LEAKAGE = re.compile(
    r"(?:\bresults?\b|\bfindings?\b|\bassociated\b|\bsignificant\b|"
    r"\bcorrelat(?:e|ed|es|ion)\b|\beffect\s+sizes?\b|\bp\s*[<=>]|"
    r"\b(?:r|rho|beta|coefficient|estimate|odds ratio|hazard ratio|risk ratio)\s*"
    r"[=<=>]\s*-?\d|\b(?:tbd|placeholder)\b|"
    r"\b(?:improv(?:e|ed|es)|caus(?:e|ed|es)|dr(?:ive|ives|ove)|"
    r"impact(?:ed|s)?|reduc(?:e|ed|es)|prevent(?:ed|s)?|led|leads?)\b|"
    r"\b\d+(?:\.\d+)?\s*%|\b0\.\d+\b|\b(?:ci|confidence interval)\b)",
    re.IGNORECASE,
)
_SECTION_TEXT = (
    "Complete only from the outcome-blinded selection record, signed SAP, source "
    "contracts, and the applicable manuscript contract. Do not add empirical "
    "statements before S7 authorization."
)


@dataclass(frozen=True, slots=True)
class _SelectedCase:
    order: int
    case_id: str
    display_name: str


def _assert_no_symlink_path(root: Path, relative: Path, label: str) -> None:
    cursor = root
    for part in relative.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ManuscriptPacketError(f"{label} must not use symlinks")


def _read_json_object(root: Path, relative: Path, label: str) -> dict[str, Any]:
    _assert_no_symlink_path(root, relative, label)
    path = root / relative
    if not path.is_file():
        raise ManuscriptPacketError(f"{label} is required after S5 passes")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise ManuscriptPacketError(f"{label} is not valid JSON") from error
    except (OSError, UnicodeError) as error:
        raise ManuscriptPacketError(f"{label} cannot be read") from error
    if not isinstance(loaded, dict):
        raise ManuscriptPacketError(f"{label} must be a JSON object")
    return loaded


def _parse_approval(value: object, label: str) -> None:
    if not isinstance(value, dict) or set(value) != _APPROVAL_FIELDS:
        raise ManuscriptPacketError(f"{label} approval is invalid")
    human = value.get("human")
    raw_date = value.get("date")
    if (
        not isinstance(human, str)
        or not human.strip()
        or human != human.strip()
        or not isinstance(raw_date, str)
        or value.get("decision") != "approved"
    ):
        raise ManuscriptPacketError(f"{label} approval is invalid")
    if _ISO_DATE.fullmatch(raw_date) is None:
        raise ManuscriptPacketError(f"{label} approval date is invalid")
    try:
        date.fromisoformat(raw_date)
    except ValueError as error:
        raise ManuscriptPacketError(f"{label} approval date is invalid") from error


def _parse_selection(root: Path) -> tuple[_SelectedCase, ...]:
    label = "case-selection record"
    record = _read_json_object(root, _SELECTION_PATH, label)
    if set(record) != _SELECTION_FIELDS:
        raise ManuscriptPacketError(f"{label} fields are invalid")
    if (
        record.get("record_type") != "outcome_blinded_case_selection"
        or record.get("gate") != "S5"
        or record.get("status") != "approved"
        or record.get("outcome_blinded") is not True
    ):
        raise ManuscriptPacketError(f"{label} does not authorize blinded selection")
    _parse_approval(record.get("approval"), label)
    raw_cases = record.get("cases")
    if not isinstance(raw_cases, list) or len(raw_cases) != 2:
        raise ManuscriptPacketError(f"{label} must approve exactly two cases")
    cases: list[_SelectedCase] = []
    for expected_order, raw in enumerate(raw_cases, start=1):
        if not isinstance(raw, dict) or set(raw) != _CASE_FIELDS:
            raise ManuscriptPacketError(f"{label} case fields are invalid")
        case_id = raw.get("case_id")
        display_name = raw.get("display_name")
        if raw.get("order") != expected_order:
            raise ManuscriptPacketError(f"{label} case order is invalid")
        if not isinstance(case_id, str) or _CASE_ID.fullmatch(case_id) is None:
            raise ManuscriptPacketError(f"{label} case identifier is invalid")
        if (
            not isinstance(display_name, str)
            or display_name != display_name.strip()
            or _DISPLAY_NAME.fullmatch(display_name) is None
        ):
            raise ManuscriptPacketError(f"{label} display name is invalid")
        if _LEAKAGE.search(display_name):
            raise ManuscriptPacketError(f"{label} contains result leakage")
        cases.append(_SelectedCase(expected_order, case_id, display_name))
    if len({case.case_id for case in cases}) != 2:
        raise ManuscriptPacketError(f"{label} case identifiers must be unique")
    return tuple(cases)


def _safe_authority_path(root: Path, raw_path: object) -> Path:
    if not isinstance(raw_path, str) or raw_path != raw_path.strip():
        raise ManuscriptPacketError("signed SAP path is invalid")
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts or relative.as_posix() in {"", "."}:
        raise ManuscriptPacketError("signed SAP path escapes repository root")
    candidate = root / relative
    _assert_no_symlink_path(root, relative, "signed SAP path")
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        raise ManuscriptPacketError("signed SAP document is missing") from None
    if not resolved.is_file():
        raise ManuscriptPacketError("signed SAP document is missing")
    return resolved


def _parse_signed_sap(root: Path, cases: tuple[_SelectedCase, ...]) -> None:
    label = "signed SAP record"
    record = _read_json_object(root, _SIGNED_SAP_PATH, label)
    if set(record) != _SAP_FIELDS:
        raise ManuscriptPacketError(f"{label} fields are invalid")
    version = record.get("version")
    digest = record.get("sha256")
    if (
        record.get("record_type") != "signed_statistical_analysis_plan"
        or record.get("status") != "signed"
        or not isinstance(version, str)
        or not version.strip()
        or version != version.strip()
        or not isinstance(digest, str)
        or _SHA256.fullmatch(digest) is None
    ):
        raise ManuscriptPacketError(f"{label} does not authorize the SAP")
    _parse_approval(record.get("approval"), label)
    case_ids = record.get("case_ids")
    expected_ids = [case.case_id for case in cases]
    if case_ids != expected_ids:
        raise ManuscriptPacketError("signed SAP case order does not match selection")
    sap_path = _safe_authority_path(root, record.get("path"))
    if sha256(sap_path.read_bytes()).hexdigest() != digest:
        raise ManuscriptPacketError("signed SAP checksum does not match document")


def _case_packet(case: _SelectedCase, provisional: bool) -> str:
    status = "PROVISIONAL — PENDING S5" if provisional else "SELECTED AT S5 — OUTCOME BLINDED"
    lines = [
        f"# Case Study {case.order}: {case.display_name}",
        "",
        f"**Status:** {status}",
        "",
    ]
    for heading in CASE_HEADINGS:
        lines.extend((f"## {heading}", "", _SECTION_TEXT, ""))
    return "\n".join(lines)


def _assert_no_pre_s7_leakage(payloads: dict[str, bytes]) -> None:
    for filename in ("case_1.md", "case_2.md"):
        body = payloads[filename].decode("utf-8")
        if _LEAKAGE.search(body) or "## Results" in body:
            raise ManuscriptPacketError(f"pre-S7 packet contains result leakage: {filename}")


def _validate_output_area(root: Path, filenames: tuple[str, ...]) -> Path:
    output = root / _OUTPUT_PATH
    cursor = root
    for part in _OUTPUT_PATH.parts:
        cursor /= part
        if cursor.is_symlink():
            raise ManuscriptPacketError("packet output path must not use symlinks")
    output.mkdir(parents=True, exist_ok=True)
    if output.is_symlink() or not output.is_dir():
        raise ManuscriptPacketError("packet output path must not use symlinks")
    for filename in filenames:
        destination = output / filename
        if destination.is_symlink():
            raise ManuscriptPacketError("packet writer must not overwrite symlinks")
        if destination.exists() and not destination.is_file():
            raise ManuscriptPacketError("packet destination must be a regular file")
    return output


def _outline_bytes(root: Path) -> bytes:
    relative = Path("docs/manuscript/outline.md")
    _assert_no_symlink_path(root, relative, "outline template")
    source = root / relative
    if not source.is_file():
        raise ManuscriptPacketError("outline template must be a regular repository file")
    try:
        source.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        raise ManuscriptPacketError("outline template escapes repository root") from None
    return source.read_bytes()


def build_control_packets(paths: ProjectPaths) -> tuple[Path, ...]:
    """Build deterministic pre-drafting controls from current gate authority."""
    report = evaluate_manuscript_gates(paths)
    if "S5" in report.passed:
        selected = _parse_selection(paths.root)
        _parse_signed_sap(paths.root, selected)
        provisional = False
    else:
        selected = tuple(
            _SelectedCase(order, f"provisional-{order}", display_name)
            for order, display_name in enumerate(_PROVISIONAL_NAMES, start=1)
        )
        provisional = True

    payloads = {
        "outline.md": _outline_bytes(paths.root),
        "case_1.md": _case_packet(selected[0], provisional).encode("utf-8"),
        "case_2.md": _case_packet(selected[1], provisional).encode("utf-8"),
    }
    if not report.results_authorized:
        _assert_no_pre_s7_leakage(payloads)
    output = _validate_output_area(paths.root, tuple(payloads))
    destinations: list[Path] = []
    for filename, payload in payloads.items():
        destination = output / filename
        destination.write_bytes(payload)
        destinations.append(destination)
    return tuple(destinations)
