from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml  # type: ignore[import-untyped]

from chicagohealthmap.manuscript.models import ManuscriptContracts


def _read_yaml(path: Path) -> dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"{path.name} must contain a mapping")
    return loaded


def _read_wrapped_mapping(path: Path, key: str) -> Mapping[str, Any]:
    loaded = _read_yaml(path)
    value = loaded.get(key)
    if not isinstance(value, dict):
        article = "an" if key == "agents" else "a"
        raise ValueError(f"{path.name} must contain {article} {key} mapping")
    return value


def load_manuscript_contracts(root: Path) -> ManuscriptContracts:
    directory = root / "config" / "manuscript"
    return ManuscriptContracts.model_validate(
        {
            "journal": _read_yaml(directory / "jama_health_forum.yml"),
            "style": _read_yaml(directory / "style_contract.yml"),
            "agents": _read_wrapped_mapping(directory / "agents.yml", "agents"),
            "gates": _read_wrapped_mapping(directory / "gates.yml", "gates"),
        }
    )
