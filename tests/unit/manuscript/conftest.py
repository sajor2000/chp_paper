from dataclasses import dataclass
import json
from pathlib import Path
import shutil

import pandas as pd
import pytest

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.manuscript.contracts import load_manuscript_contracts


@dataclass
class SandboxProject:
    root: Path

    @property
    def paths(self) -> ProjectPaths:
        return ProjectPaths.from_root(self.root)

    def write_gate(self, gate: str, status: str) -> None:
        destination = self.root / "outputs" / "governance" / "gates"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / f"{gate}.json").write_text(
            json.dumps({"gate": gate, "status": status}, sort_keys=True) + "\n",
            encoding="utf-8",
        )


@pytest.fixture
def tmp_project(tmp_path: Path) -> SandboxProject:
    root = Path(__file__).resolve().parents[3]
    (tmp_path / "config").mkdir()
    (tmp_path / "docs").mkdir()
    shutil.copytree(root / "config" / "manuscript", tmp_path / "config" / "manuscript")
    if (root / "docs" / "manuscript").is_dir():
        shutil.copytree(root / "docs" / "manuscript", tmp_path / "docs" / "manuscript")
    (tmp_path / "pyproject.toml").write_text(
        "[project]\nname='test'\nversion='0'\n", encoding="utf-8"
    )
    return SandboxProject(tmp_path)


@pytest.fixture
def authorized_project(tmp_project: SandboxProject) -> SandboxProject:
    for gate in ("S4", "S5", "S6", "S7", "S8"):
        tmp_project.write_gate(gate, "passed")
    return tmp_project


@pytest.fixture
def contracts():
    return load_manuscript_contracts(Path(__file__).resolve().parents[3])


@pytest.fixture
def control_dir(tmp_path: Path) -> Path:
    headers = {
        "claim_ledger.csv": [
            "claim_id",
            "section",
            "draft_claim",
            "claim_class",
            "source_or_artifact_id",
            "exact_support_location",
            "population_geography_measure_period_match",
            "support_strength",
            "conflict_or_gap",
            "allowed_wording",
            "prohibited_inference",
            "result_status",
            "owner",
            "verified_by",
            "verified_date",
            "final_text_location",
        ],
        "number_ledger.csv": [
            "number_id",
            "artifact_id",
            "checksum",
            "artifact_field",
            "code_version",
            "population",
            "exclusions",
            "geography",
            "time_period",
            "measure",
            "unit",
            "denominator",
            "raw_value",
            "display_value",
            "uncertainty",
            "result_status",
            "manuscript_locations",
        ],
        "ai_use_ledger.csv": [
            "ai_use_id",
            "platform",
            "model",
            "manufacturer",
            "start_date",
            "end_date",
            "use",
            "affected_artifact",
            "human_verifier",
            "verified_date",
        ],
        "issue_ledger.csv": [
            "issue_id",
            "severity",
            "gate",
            "description",
            "evidence",
            "owner",
            "status",
            "resolution",
        ],
    }
    for filename, columns in headers.items():
        pd.DataFrame(columns=columns).to_csv(tmp_path / filename, index=False)
    return tmp_path
