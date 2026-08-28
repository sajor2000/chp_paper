from pathlib import Path

import pytest

from chicagohealthmap.config import ProjectPaths


def test_project_paths_are_rooted(tmp_path: Path) -> None:
    paths = ProjectPaths.from_root(tmp_path)

    assert paths.root == tmp_path.resolve()
    assert paths.sources == tmp_path / "sources"
    assert paths.interim == tmp_path / "data" / "interim"
    assert paths.processed == tmp_path / "data" / "processed"
    assert paths.outputs == tmp_path / "outputs"
    assert paths.provenance == tmp_path / "outputs" / "provenance"


def test_project_paths_discover_uses_environment_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    monkeypatch.setenv("CHICAGOHEALTHMAP_ROOT", str(repository))

    assert ProjectPaths.discover().root == repository.resolve()


def test_project_paths_discover_finds_repository_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = tmp_path / "repository"
    nested = repository / "data" / "nested"
    nested.mkdir(parents=True)
    (repository / "pyproject.toml").touch()
    monkeypatch.delenv("CHICAGOHEALTHMAP_ROOT", raising=False)

    assert ProjectPaths.discover(start=nested).root == repository.resolve()


def test_project_paths_discover_rejects_unmarked_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CHICAGOHEALTHMAP_ROOT", raising=False)

    with pytest.raises(FileNotFoundError, match="pyproject.toml"):
        ProjectPaths.discover(start=tmp_path)
