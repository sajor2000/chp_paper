"""Repository-relative project path configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT_ENV = "CHICAGOHEALTHMAP_ROOT"
REPOSITORY_MARKER = "pyproject.toml"


@dataclass(frozen=True, slots=True)
class ProjectPaths:
    """Absolute paths derived from one repository root."""

    root: Path
    sources: Path
    interim: Path
    processed: Path
    outputs: Path
    provenance: Path

    @classmethod
    def from_root(cls, root: Path) -> ProjectPaths:
        """Build all project paths from ``root`` without creating directories."""
        root = root.resolve()
        return cls(
            root=root,
            sources=root / "sources",
            interim=root / "data" / "interim",
            processed=root / "data" / "processed",
            outputs=root / "outputs",
            provenance=root / "outputs" / "provenance",
        )

    @classmethod
    def discover(cls, start: Path | None = None) -> ProjectPaths:
        """Discover the repository root from the environment or an ancestor marker."""
        configured_root = os.environ.get(PROJECT_ROOT_ENV)
        if configured_root:
            return cls.from_root(Path(configured_root))

        candidate = (start or Path.cwd()).resolve()
        if candidate.is_file():
            candidate = candidate.parent

        for directory in (candidate, *candidate.parents):
            if (directory / REPOSITORY_MARKER).is_file():
                return cls.from_root(directory)

        raise FileNotFoundError(
            f"Could not find {REPOSITORY_MARKER!r} from {candidate}; "
            f"set {PROJECT_ROOT_ENV} to the repository root"
        )
