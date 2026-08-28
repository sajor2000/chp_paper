"""Fail-closed scientific and manuscript gate evaluation."""

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
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts
from chicagohealthmap.manuscript.ledgers import (
    LedgerError,
    LedgerReport,
    verify_ledgers,
)
from chicagohealthmap.manuscript.models import ManuscriptContracts


class ManuscriptGateError(ValueError):
    """Raised when gate evidence is invalid or does not authorize an action."""


@dataclass(frozen=True, slots=True)
class GateReport:
    """Deterministically ordered scientific and manuscript gate states."""

    passed: tuple[str, ...]
    missing: tuple[str, ...]
    open: tuple[str, ...]
    blocked: tuple[str, ...]
    results_authorized: bool


@dataclass(frozen=True, slots=True)
class _ArtifactEvidence:
    label: str
    artifact_id: str
    path: str
    sha256: str


_SCIENTIFIC_GATES = ("S4", "S5", "S6", "S7", "S8")
_RESULT_GATES = _SCIENTIFIC_GATES[:4]
_MANUSCRIPT_GATES = tuple(f"M{index}" for index in range(8))
_VALID_STATUSES = frozenset({"passed", "open", "blocked"})
_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
_S7_ARTIFACT_FIELDS = frozenset({"artifact_id", "path", "sha256"})
_M_ARTIFACT_FIELDS = frozenset({"label", "artifact_id", "path", "sha256"})
_PASSED_FIELDS = frozenset({"gate", "status", "artifacts", "acceptance", "approval"})
_LEDGER_FILES = (
    "claim_ledger.csv",
    "number_ledger.csv",
    "ai_use_ledger.csv",
    "issue_ledger.csv",
)
_M0_CANONICAL_PATHS = {
    "journal contract": "config/manuscript/jama_health_forum.yml",
    "style contract": "config/manuscript/style_contract.yml",
    "agent contract": "config/manuscript/agents.yml",
    "gate contract": "config/manuscript/gates.yml",
}


def _scientific_gate_path(root: Path, gate: str) -> Path:
    return root / "outputs" / "governance" / "gates" / f"{gate}.json"


def _manuscript_gate_path(root: Path, gate: str) -> Path:
    return root / "outputs" / "manuscript" / "control" / "gates" / f"{gate}.json"


def _read_json_object(path: Path, gate: str) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as error:
        raise ManuscriptGateError(f"{gate} gate record is not valid JSON") from error
    except (OSError, UnicodeError) as error:
        raise ManuscriptGateError(f"{gate} gate record cannot be read") from error
    if not isinstance(loaded, dict):
        raise ManuscriptGateError(f"{gate} gate record must be an object")
    if loaded.get("gate") != gate:
        raise ManuscriptGateError(f"{gate} gate identity mismatch")
    status = loaded.get("status")
    if not isinstance(status, str) or status not in _VALID_STATUSES:
        raise ManuscriptGateError(f"{gate} gate status is invalid")
    return loaded


def _read_scientific_gate(root: Path, gate: str) -> dict[str, Any] | None:
    loaded = _read_json_object(_scientific_gate_path(root, gate), gate)
    if loaded is None:
        return None
    status = loaded["status"]
    expected_fields = {"gate", "status"}
    if gate == "S7" and status == "passed":
        if set(loaded) not in (expected_fields, expected_fields | {"artifacts"}):
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
    elif set(loaded) != expected_fields:
        raise ManuscriptGateError(f"{gate} gate record fields are invalid")
    return loaded


def _read_manuscript_gate(root: Path, gate: str) -> dict[str, Any] | None:
    loaded = _read_json_object(_manuscript_gate_path(root, gate), gate)
    if loaded is None:
        return None
    if loaded["status"] == "passed":
        if set(loaded) != _PASSED_FIELDS:
            raise ManuscriptGateError(f"{gate} passed record fields are invalid")
    elif set(loaded) != {"gate", "status"}:
        raise ManuscriptGateError(f"{gate} {loaded['status']} record fields are invalid")
    return loaded


def _read_scientific_gates(root: Path) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    statuses: dict[str, str] = {}
    records: dict[str, dict[str, Any]] = {}
    for gate in _SCIENTIFIC_GATES:
        record = _read_scientific_gate(root, gate)
        statuses[gate] = "missing" if record is None else record["status"]
        if record is not None:
            records[gate] = record

    for index, gate in enumerate(_RESULT_GATES[1:], start=1):
        if statuses[gate] != "passed":
            continue
        unresolved = tuple(
            predecessor
            for predecessor in _RESULT_GATES[:index]
            if statuses[predecessor] != "passed"
        )
        if unresolved:
            raise ManuscriptGateError(f"{gate} cannot pass before {', '.join(unresolved)}")
    return statuses, records


def _normalized_relative_path(raw_path: str, gate: str) -> tuple[Path, str]:
    relative = Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        raise ManuscriptGateError(f"{gate} artifact escapes repository root")
    normalized = relative.as_posix()
    if normalized in {"", "."}:
        raise ManuscriptGateError(f"{gate} artifact path is invalid")
    return relative, normalized


def _path_uses_symlink(root: Path, relative: Path) -> bool:
    candidate = root
    for part in relative.parts:
        candidate /= part
        if candidate.is_symlink():
            return True
    return False


def _verify_artifact_file(root: Path, gate: str, artifact: _ArtifactEvidence) -> None:
    relative, _ = _normalized_relative_path(artifact.path, gate)
    if _path_uses_symlink(root, relative):
        raise ManuscriptGateError(f"{gate} artifact paths must not use symlinks")
    candidate = root / relative
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        raise ManuscriptGateError(
            f"{gate} artifact checksum mismatch: {artifact.artifact_id}"
        ) from None
    if not resolved.is_file():
        raise ManuscriptGateError(f"{gate} artifact checksum mismatch: {artifact.artifact_id}")
    hasher = sha256()
    try:
        with resolved.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                hasher.update(chunk)
    except OSError as error:
        raise ManuscriptGateError(
            f"{gate} artifact checksum mismatch: {artifact.artifact_id}"
        ) from error
    if hasher.hexdigest() != artifact.sha256:
        raise ManuscriptGateError(f"{gate} artifact checksum mismatch: {artifact.artifact_id}")


def _validate_s7_artifacts(
    root: Path, record: dict[str, Any] | None = None
) -> tuple[_ArtifactEvidence, ...]:
    if record is None:
        record = _read_scientific_gate(root, "S7")
    artifacts = None if record is None else record.get("artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ManuscriptGateError("S7 requires frozen artifact checksums")

    parsed: list[_ArtifactEvidence] = []
    normalized_paths: list[str] = []
    for raw in artifacts:
        if not isinstance(raw, dict) or set(raw) != _S7_ARTIFACT_FIELDS:
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
        artifact_id = raw.get("artifact_id")
        raw_path = raw.get("path")
        digest = raw.get("sha256")
        if (
            not isinstance(artifact_id, str)
            or not artifact_id.strip()
            or artifact_id != artifact_id.strip()
            or not isinstance(raw_path, str)
            or not raw_path.strip()
            or raw_path != raw_path.strip()
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
        ):
            raise ManuscriptGateError("S7 requires frozen artifact checksums")
        _, normalized = _normalized_relative_path(raw_path, "S7")
        normalized_paths.append(normalized)
        parsed.append(_ArtifactEvidence("", artifact_id, raw_path, digest))

    if len({item.artifact_id for item in parsed}) != len(parsed):
        raise ManuscriptGateError("S7 requires frozen artifact checksums")
    if len(set(normalized_paths)) != len(normalized_paths):
        raise ManuscriptGateError("S7 artifact paths must be unique")
    for artifact in parsed:
        _verify_artifact_file(root, "S7", artifact)
    return tuple(parsed)


def _validate_m_artifacts(
    root: Path,
    gate: str,
    raw_artifacts: object,
    expected_labels: tuple[str, ...],
    canonical_paths: dict[str, str] | None = None,
) -> tuple[_ArtifactEvidence, ...]:
    if not isinstance(raw_artifacts, list) or not raw_artifacts:
        raise ManuscriptGateError(f"{gate} artifact evidence is invalid")
    parsed: list[_ArtifactEvidence] = []
    normalized_paths: list[str] = []
    for raw in raw_artifacts:
        if not isinstance(raw, dict) or set(raw) != _M_ARTIFACT_FIELDS:
            raise ManuscriptGateError(f"{gate} artifact evidence is invalid")
        label = raw.get("label")
        artifact_id = raw.get("artifact_id")
        raw_path = raw.get("path")
        digest = raw.get("sha256")
        if (
            not isinstance(label, str)
            or not label.strip()
            or label != label.strip()
            or not isinstance(artifact_id, str)
            or not artifact_id.strip()
            or artifact_id != artifact_id.strip()
            or not isinstance(raw_path, str)
            or not raw_path.strip()
            or raw_path != raw_path.strip()
            or not isinstance(digest, str)
            or _SHA256.fullmatch(digest) is None
        ):
            raise ManuscriptGateError(f"{gate} artifact evidence is invalid")
        _, normalized = _normalized_relative_path(raw_path, gate)
        normalized_paths.append(normalized)
        parsed.append(_ArtifactEvidence(label, artifact_id, raw_path, digest))

    labels = tuple(item.label for item in parsed)
    if len(set(labels)) != len(labels) or set(labels) != set(expected_labels):
        raise ManuscriptGateError(f"{gate} artifact labels do not match contract")
    if canonical_paths is not None and any(
        item.path != canonical_paths[item.label] for item in parsed
    ):
        raise ManuscriptGateError(f"{gate} artifact path does not match canonical contract")
    if len({item.artifact_id for item in parsed}) != len(parsed):
        raise ManuscriptGateError(f"{gate} artifact IDs must be unique")
    if len(set(normalized_paths)) != len(normalized_paths):
        raise ManuscriptGateError(f"{gate} artifact paths must be unique")
    return tuple(parsed)


def _validate_acceptance(gate: str, raw: object, expected: tuple[str, ...]) -> None:
    if not isinstance(raw, list):
        raise ManuscriptGateError(f"{gate} acceptance does not match contract")
    criteria: list[str] = []
    for entry in raw:
        if (
            not isinstance(entry, dict)
            or set(entry) != {"criterion", "state"}
            or not isinstance(entry.get("criterion"), str)
            or entry.get("state") != "accepted"
        ):
            raise ManuscriptGateError(f"{gate} acceptance does not match contract")
        criteria.append(entry["criterion"])
    if len(set(criteria)) != len(criteria) or set(criteria) != set(expected):
        raise ManuscriptGateError(f"{gate} acceptance does not match contract")


def _validate_approval(gate: str, raw: object) -> None:
    if not isinstance(raw, dict) or set(raw) != {"human", "date", "decision"}:
        raise ManuscriptGateError(f"{gate} approval is invalid")
    human = raw.get("human")
    raw_date = raw.get("date")
    if (
        not isinstance(human, str)
        or not human.strip()
        or human != human.strip()
        or not isinstance(raw_date, str)
        or _ISO_DATE.fullmatch(raw_date) is None
        or raw.get("decision") != "accepted"
    ):
        raise ManuscriptGateError(f"{gate} approval is invalid")
    try:
        date.fromisoformat(raw_date)
    except ValueError as error:
        raise ManuscriptGateError(f"{gate} approval is invalid") from error


def _validate_passed_m_gate(
    paths: ProjectPaths,
    gate: str,
    record: dict[str, Any],
    contracts: ManuscriptContracts,
    scientific: dict[str, str],
    manuscript_statuses: dict[str, str],
    s7_artifacts: tuple[_ArtifactEvidence, ...],
    ledger_report: LedgerReport | None,
) -> None:
    contract = contracts.gates[gate]
    resolved = {name for name, status in scientific.items() if status == "passed"} | {
        name for name, status in manuscript_statuses.items() if status == "passed"
    }
    unresolved = tuple(required for required in contract.requires if required not in resolved)
    if unresolved:
        raise ManuscriptGateError(f"{gate} cannot pass before {', '.join(unresolved)}")
    if gate not in {"M0", "M1"}:
        raise ManuscriptGateError(f"{gate} validator is unavailable")
    artifacts = _validate_m_artifacts(
        paths.root,
        gate,
        record["artifacts"],
        contract.artifacts,
        _M0_CANONICAL_PATHS if gate == "M0" else None,
    )
    _validate_acceptance(gate, record["acceptance"], contract.acceptance)
    _validate_approval(gate, record["approval"])

    if gate == "M0":
        for artifact in artifacts:
            _verify_artifact_file(paths.root, gate, artifact)
        return

    if ledger_report is None:
        raise ManuscriptGateError("M1 requires complete manuscript ledgers")
    s7_by_id = {artifact.artifact_id: artifact for artifact in s7_artifacts}
    for artifact in artifacts:
        s7_artifact = s7_by_id.get(artifact.artifact_id)
        if s7_artifact is None:
            raise ManuscriptGateError(f"M1 artifact {artifact.artifact_id} is absent from S7")
        _, m1_path = _normalized_relative_path(artifact.path, "M1")
        _, s7_path = _normalized_relative_path(s7_artifact.path, "S7")
        if m1_path != s7_path or artifact.sha256 != s7_artifact.sha256:
            raise ManuscriptGateError(
                f"M1 artifact {artifact.artifact_id} does not match S7 path and digest"
            )
    if not ledger_report.number_artifacts:
        raise ManuscriptGateError("M1 requires at least one number record")
    for artifact_id, checksum in ledger_report.number_artifacts:
        s7_artifact = s7_by_id.get(artifact_id)
        if s7_artifact is None:
            raise ManuscriptGateError(f"number ledger artifact {artifact_id} is absent from S7")
        if checksum != f"sha256:{s7_artifact.sha256}":
            raise ManuscriptGateError(
                f"number ledger artifact {artifact_id} checksum does not match S7"
            )
    for artifact in artifacts:
        _verify_artifact_file(paths.root, gate, artifact)


def manuscript_ledgers_active(paths: ProjectPaths) -> bool:
    """Return whether any ledger or M1-M7 evidence activates ledger controls."""
    control = paths.root / "outputs" / "manuscript" / "control"
    return any((control / filename).is_file() for filename in _LEDGER_FILES) or any(
        _manuscript_gate_path(paths.root, gate).is_file() for gate in _MANUSCRIPT_GATES[1:]
    )


def verify_active_manuscript_ledgers(
    paths: ProjectPaths, contracts: ManuscriptContracts
) -> LedgerReport | None:
    """Validate the complete ledger set whenever any control artifact activates it."""
    if not manuscript_ledgers_active(paths):
        return None
    try:
        return verify_ledgers(paths.root / "outputs" / "manuscript" / "control", contracts)
    except LedgerError as error:
        raise ManuscriptGateError(str(error)) from error


def assert_results_authorized(paths: ProjectPaths) -> None:
    """Fail unless S4 through S7 passed in order with valid frozen artifacts."""
    statuses, records = _read_scientific_gates(paths.root)
    for gate in _RESULT_GATES:
        if statuses[gate] != "passed":
            raise ManuscriptGateError(f"{gate} must pass before results are authorized")
    _validate_s7_artifacts(paths.root, records["S7"])


def evaluate_manuscript_gates(paths: ProjectPaths) -> GateReport:
    """Evaluate explicit gate evidence without inferring passage from dependencies."""
    contracts = load_manuscript_contracts(paths.root)
    scientific, scientific_records = _read_scientific_gates(paths.root)
    s7_artifacts: tuple[_ArtifactEvidence, ...] = ()
    if scientific["S7"] == "passed":
        s7_artifacts = _validate_s7_artifacts(paths.root, scientific_records["S7"])

    manuscript_records: dict[str, dict[str, Any]] = {}
    manuscript_statuses: dict[str, str] = {}
    for gate in _MANUSCRIPT_GATES:
        record = _read_manuscript_gate(paths.root, gate)
        manuscript_statuses[gate] = "missing" if record is None else record["status"]
        if record is not None:
            manuscript_records[gate] = record

    resolved = {name for name, status in scientific.items() if status == "passed"} | {
        name for name, status in manuscript_statuses.items() if status == "passed"
    }
    for gate in _MANUSCRIPT_GATES:
        if manuscript_statuses[gate] != "passed":
            continue
        unresolved = tuple(
            required for required in contracts.gates[gate].requires if required not in resolved
        )
        if unresolved:
            raise ManuscriptGateError(f"{gate} cannot pass before {', '.join(unresolved)}")

    ledger_report = verify_active_manuscript_ledgers(paths, contracts)
    for gate in _MANUSCRIPT_GATES:
        if manuscript_statuses[gate] == "passed":
            _validate_passed_m_gate(
                paths,
                gate,
                manuscript_records[gate],
                contracts,
                scientific,
                manuscript_statuses,
                s7_artifacts,
                ledger_report,
            )

    all_statuses = {**scientific, **manuscript_statuses}
    order = _SCIENTIFIC_GATES + _MANUSCRIPT_GATES
    return GateReport(
        passed=tuple(gate for gate in order if all_statuses[gate] == "passed"),
        missing=tuple(gate for gate in order if all_statuses[gate] == "missing"),
        open=tuple(gate for gate in order if all_statuses[gate] == "open"),
        blocked=tuple(gate for gate in order if all_statuses[gate] == "blocked"),
        results_authorized=all(scientific[gate] == "passed" for gate in _RESULT_GATES),
    )
