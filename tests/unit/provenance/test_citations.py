import json
from datetime import date

import pytest

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import NormalizationError
from chicagohealthmap.provenance import citations as citations_module
from chicagohealthmap.provenance.citations import (
    CitationError,
    DataCitation,
    citations_for_project,
)

ROOT = ProjectPaths.discover()


def _citation(**overrides: object) -> DataCitation:
    values = {
        "source_id": "cdc_places_current_tract",
        "organization": "Centers for Disease Control and Prevention",
        "title": "PLACES: Census Tract Data, 2025 release",
        "version": "2025",
        "year": "2025",
        "url": "https://data.cdc.gov/d/yjkw-uj5s",
        "accessed": date(2026, 7, 14),
        "catalog_id": "yjkw-uj5s",
    }
    values.update(overrides)
    return DataCitation(**values)  # type: ignore[arg-type]


def test_citation_renders_valid_csl_json_and_bibtex_dataset() -> None:
    citation = _citation()
    csl = json.loads(citation.to_csl_json())
    bibtex = citation.to_bibtex()

    assert csl["type"] == "dataset"
    assert csl["accessed"]["date-parts"] == [[2026, 7, 14]]
    assert csl["id"] == "cdc_places_current_tract_2025"
    assert bibtex.startswith("@dataset{cdc_places_current_tract_2025,")
    assert "catalog_id = {yjkw-uj5s}" in bibtex


def test_citation_rejects_missing_required_fields_and_protected_paths() -> None:
    with pytest.raises(CitationError, match="organization"):
        _citation(organization=" ")
    with pytest.raises(CitationError, match="protected path"):
        _citation(url="/Users/investigator/restricted/export")
    with pytest.raises(CitationError, match="protected path"):
        _citation(title="Dataset at /Users/investigator/restricted/export")


def test_first_party_citation_describes_access_restriction_without_paths() -> None:
    citation = _citation(
        source_id="capricorn_chicagohealthmap_export",
        organization="CAPriCORN and CONSCIENCE Project",
        title="Chicago Health Map restricted research extract; access restricted",
        version="extract 2026-05-27",
        year="2026",
        url="https://chicagohealthmap.com/",
        catalog_id=None,
    )
    rendered = citation.to_bibtex()
    assert "access restricted" in rendered
    assert "/Users/" not in rendered


def test_citation_materialization_verifies_snapshot_provenance_first(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject_unverified(_paths: ProjectPaths) -> None:
        raise NormalizationError("unverified snapshot")

    monkeypatch.setattr(
        citations_module, "verify_public_provenance", reject_unverified, raising=False
    )
    with pytest.raises(NormalizationError, match="unverified snapshot"):
        citations_module.write_citations(ProjectPaths.from_root(tmp_path))


def test_places_citation_uses_2025_release_not_arbitrary_input_year() -> None:
    places = next(
        citation
        for citation in citations_for_project(ROOT)
        if citation.source_id == "cdc_places_current_tract"
    )
    assert places.year == "2025"
    assert places.version.startswith("2025 release")


def test_first_party_project_citation_uses_archived_approved_attribution_exactly() -> None:
    citation = next(
        item
        for item in citations_for_project(ROOT)
        if item.source_id == "capricorn_chicagohealthmap_export_2026_05_27"
    )
    assert citation.organization == "CONSCIENCE Project"
    assert citation.title == "CONSCIENCE: CONnecting SCIence, ENgaging Chicago for Equity"
    rendered = citation.to_bibtex()
    assert "Rush Health Equity Data Analytics Studio" in rendered
    assert "Rush University System for Health" in rendered
    assert "extract 2026-05-27" in rendered
    assert "access restricted" in rendered
