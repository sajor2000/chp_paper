"""CSL JSON and BibTeX rendering for immutable dataset snapshots."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit

from chicagohealthmap.config import ProjectPaths
from chicagohealthmap.external.normalize import verify_public_provenance
from chicagohealthmap.sources.registry import load_registry


class CitationError(ValueError):
    """Citation metadata is incomplete or disclosure-unsafe."""


_PROTECTED_PATH = re.compile(r"(?:^|[\s\"'])/(?:Users|home|private|Volumes)/|[A-Za-z]:\\")


def _bibtex_escape(value: str) -> str:
    return value.replace("\\", "\\textbackslash{}").replace("{", "\\{").replace("}", "\\}")


@dataclass(frozen=True)
class DataCitation:
    source_id: str
    organization: str
    title: str
    version: str
    year: str
    url: str
    accessed: date
    catalog_id: str | None

    def __post_init__(self) -> None:
        for field in ("source_id", "organization", "title", "version", "year", "url"):
            value = str(getattr(self, field))
            if not value.strip():
                raise CitationError(f"{field} is required")
            if _PROTECTED_PATH.search(value):
                raise CitationError("citation metadata must not expose a protected path")
        parsed = urlsplit(self.url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise CitationError("citation URL must not expose a protected path")
        if not re.fullmatch(r"[a-z0-9_]+", self.source_id):
            raise CitationError("source_id must be a lowercase identifier")

    @property
    def citation_id(self) -> str:
        normalized_year = re.sub(r"[^0-9A-Za-z]+", "_", self.year).strip("_")
        return f"{self.source_id}_{normalized_year}"

    def as_csl(self) -> dict[str, object]:
        item: dict[str, object] = {
            "id": self.citation_id,
            "type": "dataset",
            "author": [{"literal": self.organization}],
            "title": self.title,
            "version": self.version,
            "issued": {"date-parts": [[int(self.year)]]},
            "URL": self.url,
            "accessed": {
                "date-parts": [[self.accessed.year, self.accessed.month, self.accessed.day]]
            },
        }
        if self.catalog_id is not None:
            item["number"] = self.catalog_id
        return item

    def to_csl_json(self) -> str:
        return json.dumps(self.as_csl(), indent=2, sort_keys=True) + "\n"

    def to_bibtex(self) -> str:
        fields = [
            ("author", _bibtex_escape(self.organization)),
            ("title", _bibtex_escape(self.title)),
            ("year", self.year),
            ("version", _bibtex_escape(self.version)),
            ("url", _bibtex_escape(self.url)),
            ("urldate", self.accessed.isoformat()),
        ]
        if self.catalog_id is not None:
            fields.append(("catalog_id", _bibtex_escape(self.catalog_id)))
        body = "\n".join(f"  {name} = {{{value}}}," for name, value in fields)
        return f"@dataset{{{self.citation_id},\n{body}\n}}\n"


def citations_for_project(paths: ProjectPaths) -> tuple[DataCitation, ...]:
    """Build one disclosure-safe citation per registered and first-party snapshot."""

    registry = load_registry(paths.root / "config" / "source_registry.yml")
    citations = [
        DataCitation(
            source_id=source.source_id,
            organization=source.organization,
            title=source.dataset_title,
            version=source.release,
            year=(re.findall(r"\d{4}", source.release) or [str(source.access_date.year)])[0],
            url=str(source.citation_url),
            accessed=source.access_date,
            catalog_id=source.catalog_id,
        )
        for source in registry.sources
    ]
    citations.extend(
        [
            DataCitation(
                source_id="capricorn_chicagohealthmap_export_2026_05_27",
                organization="CONSCIENCE Project",
                title="CONSCIENCE: CONnecting SCIence, ENgaging Chicago for Equity",
                version=(
                    "Chicago, IL: Rush Health Equity Data Analytics Studio, Rush University "
                    "System for Health; CAPriCORN/ChicagoHealthMap extract 2026-05-27; "
                    "access restricted"
                ),
                year="2026",
                url="https://chicagohealthmap.com/",
                accessed=date(2026, 7, 13),
                catalog_id=None,
            ),
            DataCitation(
                source_id="chicagohealthmap_website_methods",
                organization="CONSCIENCE Project",
                title="CONSCIENCE: CONnecting SCIence, ENgaging Chicago for Equity",
                version="website methods archive 2026-07-13",
                year="2026",
                url="https://chicagohealthmap.com/",
                accessed=date(2026, 7, 13),
                catalog_id=None,
            ),
        ]
    )
    return tuple(sorted(citations, key=lambda item: item.source_id))


def write_citations(paths: ProjectPaths) -> tuple[Path, Path]:
    verify_public_provenance(paths)
    citations = citations_for_project(paths)
    if len({citation.citation_id for citation in citations}) != len(citations):
        raise CitationError("citation identifiers must be unique")
    paths.provenance.mkdir(parents=True, exist_ok=True)
    csl_path = paths.provenance / "data_sources.csl.json"
    bib_path = paths.provenance / "data_sources.bib"
    csl_path.write_text(
        json.dumps([citation.as_csl() for citation in citations], indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    bib_path.write_text(
        "\n".join(item.to_bibtex().rstrip() for item in citations) + "\n", encoding="utf-8"
    )
    return csl_path, bib_path
