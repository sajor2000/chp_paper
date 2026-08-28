#!/usr/bin/env python3
"""Build local JAMA Health Forum style-audit artifacts from exemplar PDFs."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import statistics
from typing import Any

try:
    import yaml  # type: ignore[import-untyped]
except ModuleNotFoundError:  # pragma: no cover - exercised by bundled PDF runtime.
    yaml = None


SECTION_NAMES = ("Introduction", "Methods", "Results", "Discussion", "Limitations", "Conclusions")
END_MARKERS = (
    "ARTICLE INFORMATION",
    "Author Affiliations",
    "Corresponding Author",
    "Accepted for Publication",
    "Published Online",
    "Conflict of Interest Disclosures",
    "Funding/Support",
    "Role of the Funder/Sponsor",
    "Data Sharing Statement",
    "References",
    "SUPPLEMENT",
)
ABSTRACT_HEADINGS = (
    "IMPORTANCE",
    "OBJECTIVE",
    "DESIGN, SETTING, AND PARTICIPANTS",
    "EXPOSURE",
    "EXPOSURES",
    "MAIN OUTCOMES AND MEASURES",
    "RESULTS",
    "CONCLUSIONS AND RELEVANCE",
)
KEY_POINT_HEADINGS = ("Question", "Findings", "Meaning")
HEDGE_TERMS = (
    "associated",
    "association",
    "suggest",
    "suggests",
    "may",
    "might",
    "could",
    "potential",
    "plausibly",
    "consistent",
    "unclear",
    "limited",
)
TRANSITION_TERMS = (
    "however",
    "although",
    "while",
    "despite",
    "therefore",
    "consequently",
    "in contrast",
    "in addition",
)


def _require_pdfplumber() -> Any:
    try:
        import pdfplumber  # type: ignore[import-not-found]
    except ModuleNotFoundError as error:
        raise SystemExit(
            "pdfplumber is required. Run this script with the Codex bundled Python runtime "
            "or install pdfplumber in the active environment."
        ) from error
    return pdfplumber


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def read_manifest(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if yaml is not None:
        loaded = yaml.safe_load(text)
        if not isinstance(loaded, dict):
            raise SystemExit("Manifest must contain a mapping")
        return loaded

    # Tiny fallback for this repository-owned manifest shape. The project venv
    # has PyYAML; the bundled PDF runtime may not.
    manifest: dict[str, Any] = {"articles": []}
    current_article: dict[str, Any] | None = None
    pending_key: str | None = None
    pending_lines: list[str] = []

    def flush_pending() -> None:
        nonlocal pending_key, pending_lines
        if pending_key is None:
            return
        value = " ".join(line.strip() for line in pending_lines).strip()
        target = current_article if current_article is not None else manifest
        target[pending_key] = value
        pending_key = None
        pending_lines = []

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if pending_key is not None and raw_line.startswith("  "):
            pending_lines.append(raw_line)
            continue
        flush_pending()
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped == "articles:":
            continue
        if stripped.startswith("- "):
            current_article = {}
            manifest["articles"].append(current_article)
            stripped = stripped[2:]
        if ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if raw_value == ">-":
            pending_key = key
            pending_lines = []
            continue
        value: Any = raw_value.strip('"')
        if value.isdigit():
            value = int(value)
        target = current_article if current_article is not None else manifest
        target[key] = value
    flush_pending()
    return manifest


def _outside_table_bboxes(table_bboxes: list[tuple[float, float, float, float]]) -> Any:
    """Return a pdfplumber filter that retains characters outside detected tables."""

    def keep(obj: dict[str, Any]) -> bool:
        if not {"x0", "x1", "top", "bottom"}.issubset(obj):
            return True
        return not any(
            obj["x1"] > x0 and obj["x0"] < x1 and obj["bottom"] > top and obj["top"] < bottom
            for x0, top, x1, bottom in table_bboxes
        )

    return keep


def extract_pdf_text(path: Path, *, exclude_tables: bool = True) -> str:
    pdfplumber = _require_pdfplumber()
    with pdfplumber.open(path) as pdf:
        pages: list[str] = []
        for page in pdf.pages:
            table_bboxes = [tuple(table.bbox) for table in page.find_tables()]
            prose_page = (
                page.filter(_outside_table_bboxes(table_bboxes))
                if exclude_tables and table_bboxes
                else page
            )
            pages.append(prose_page.extract_text(x_tolerance=1, y_tolerance=3) or "")
    return "\n".join(pages)


def clean_text(text: str) -> str:
    lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            lines.append("")
            continue
        if line.startswith("Downloaded from jamanetwork.com"):
            continue
        if line.startswith("JAMA Health Forum. 2026;") and "(Reprinted)" in line:
            continue
        if line.startswith("Open Access. This is an open access article"):
            continue
        if line == "(continued)":
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned


def _line_positions(text: str) -> list[tuple[int, str]]:
    positions: list[tuple[int, str]] = []
    offset = 0
    for line in text.splitlines(keepends=True):
        positions.append((offset, line.strip()))
        offset += len(line)
    return positions


def _heading_positions(text: str) -> list[tuple[int, str]]:
    headings: list[tuple[int, str]] = []
    for offset, line in _line_positions(text):
        if line in SECTION_NAMES:
            headings.append((offset, line))
    return headings


def _end_position(text: str, start: int) -> int:
    candidates = [
        match.start()
        for marker in END_MARKERS
        for match in re.finditer(rf"(?m)^{re.escape(marker)}\b", text[start:])
    ]
    if not candidates:
        return len(text)
    return start + min(candidates)


def extract_sections(text: str) -> dict[str, str]:
    headings = _heading_positions(text)
    if not headings:
        return {}
    sections: dict[str, str] = {}
    for index, (start, name) in enumerate(headings):
        next_start = (
            headings[index + 1][0] if index + 1 < len(headings) else _end_position(text, start)
        )
        block = text[start:next_start].strip()
        sections[name] = block
    if "Conclusions" in sections:
        start = text.find(sections["Conclusions"])
        if start >= 0:
            sections["Conclusions"] = text[start : _end_position(text, start)].strip()
    return sections


def extract_front_matter(text: str) -> dict[str, Any]:
    intro_start = text.find("\nIntroduction\n")
    front = text[:intro_start] if intro_start >= 0 else text[:3000]
    return {
        "abstract_headings_present": [
            heading
            for heading in ABSTRACT_HEADINGS
            if re.search(rf"\b{re.escape(heading)}\b", front)
        ],
        "key_points_headings_present": [
            heading
            for heading in KEY_POINT_HEADINGS
            if re.search(rf"\b{re.escape(heading)}\b", front)
        ],
        "abstract_word_count_estimate": len(
            re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+(?:\.\d+)?%?", front)
        ),
    }


def words(text: str) -> list[str]:
    return re.findall(r"[A-Za-z]+(?:[-'][A-Za-z]+)?|\d+(?:\.\d+)?%?", text)


def sentences(text: str) -> list[str]:
    compact = re.sub(r"\s+", " ", text)
    citation = r"\d+(?:[-–]\d+)?(?:,\d+(?:[-–]\d+)?)*"
    compact = re.sub(
        rf"([.!?])({citation})\s+(?=[A-Z(])",
        r"\1\2<SENTENCE_BREAK>",
        compact,
    )
    compact = re.sub(r"([.!?])\s+(?=[A-Z(])", r"\1<SENTENCE_BREAK>", compact)
    parts = compact.split("<SENTENCE_BREAK>")
    cleaned = [re.sub(rf"([.!?]){citation}$", r"\1", part.strip()) for part in parts]
    return [part for part in cleaned if len(words(part)) >= 4]


def paragraphs(text: str) -> list[str]:
    chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    return [chunk for chunk in chunks if len(words(chunk)) >= 8]


def syllables(word: str) -> int:
    normalized = re.sub(r"[^a-z]", "", word.lower())
    if not normalized:
        return 0
    groups = re.findall(r"[aeiouy]+", normalized)
    count = len(groups)
    if normalized.endswith("e") and count > 1:
        count -= 1
    return max(count, 1)


def percentile(values: list[int], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = (len(ordered) - 1) * pct
    low = int(index)
    high = min(low + 1, len(ordered) - 1)
    weight = index - low
    return ordered[low] * (1 - weight) + ordered[high] * weight


def section_metrics(article_id: str, section: str, text: str) -> dict[str, Any]:
    section_words = words(text)
    section_sentences = sentences(text)
    sentence_lengths = [len(words(sentence)) for sentence in section_sentences]
    paragraph_lengths = [len(words(paragraph)) for paragraph in paragraphs(text)]
    syllable_count = sum(syllables(word) for word in section_words)
    sentence_count = max(len(section_sentences), 1)
    word_count = max(len(section_words), 1)
    fk_grade = 0.39 * (word_count / sentence_count) + 11.8 * (syllable_count / word_count) - 15.59
    lower = text.lower()
    numeric_tokens = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    passive_flags = re.findall(
        r"\b(?:is|are|was|were|be|been|being)\s+(?:\w+ly\s+)?\w+(?:ed|en)\b",
        lower,
    )
    nominalizations = re.findall(
        r"\b\w+(?:tion|sion|ment|ance|ence|ity|ness|ability|ization|isation)\b",
        lower,
    )
    return {
        "article_id": article_id,
        "section": section,
        "word_count": len(section_words),
        "sentence_count": len(section_sentences),
        "mean_sentence_words": round(statistics.mean(sentence_lengths), 2)
        if sentence_lengths
        else 0,
        "median_sentence_words": round(statistics.median(sentence_lengths), 2)
        if sentence_lengths
        else 0,
        "p25_sentence_words": round(percentile(sentence_lengths, 0.25), 2),
        "p75_sentence_words": round(percentile(sentence_lengths, 0.75), 2),
        "flesch_kincaid_grade": round(fk_grade, 2),
        "paragraph_count": len(paragraph_lengths),
        "mean_paragraph_words": round(statistics.mean(paragraph_lengths), 2)
        if paragraph_lengths
        else 0,
        "passive_flag_count": len(passive_flags),
        "nominalization_flag_count": len(nominalizations),
        "hedge_term_count": sum(lower.count(term) for term in HEDGE_TERMS),
        "transition_term_count": sum(lower.count(term) for term in TRANSITION_TERMS),
        "numeric_token_count": len(numeric_tokens),
        "numeric_tokens_per_100_words": round(len(numeric_tokens) * 100 / word_count, 2),
    }


def heading_inventory(text: str) -> list[str]:
    headings: list[str] = []
    for _, line in _line_positions(text):
        if not 3 <= len(line) <= 90:
            continue
        if line == "Data Sharing Statement" or line.startswith("Meaning "):
            continue
        if line in SECTION_NAMES:
            headings.append(line)
            continue
        if re.match(r"^[A-Z][A-Za-z0-9 ,()/$%–-]+$", line) and any(
            token in line
            for token in (
                "Data",
                "Study",
                "Population",
                "Outcome",
                "Statistical",
                "Sensitivity",
                "Cost Sharing",
                "Results",
                "Discussion",
                "Limitations",
                "Conclusions",
                "Sources",
                "Covariates",
            )
        ):
            headings.append(line)
    return list(dict.fromkeys(headings))


def display_inventory(text: str) -> list[dict[str, Any]]:
    displays: list[dict[str, Any]] = []
    observed: set[tuple[str, str]] = set()
    pattern = re.compile(r"(?m)^(Table \d+|Figure|Figure \d+|eTable \d+|eFigure)\.?\s+(.+)")
    for match in pattern.finditer(text):
        label = match.group(1)
        title = match.group(2).strip()
        display_key = (label, title)
        if display_key in observed:
            continue
        observed.add(display_key)
        start = match.end()
        snippet = re.sub(r"\s+", " ", text[start : start + 1200])
        displays.append(
            {
                "label": label,
                "title": title,
                "display_type": (
                    "supplement"
                    if label.startswith("e")
                    else "figure"
                    if label.startswith("Figure")
                    else "table"
                ),
                "mentions_ci": bool(re.search(r"\bCI\b|confidence interval", snippet, re.I)),
                "mentions_no_percent": "No. (%)" in snippet,
                "has_abbreviation_note": "Abbreviations:" in snippet,
                "has_footnote_markers": bool(re.search(r"\b[a-z]\s", snippet[:300])),
            }
        )
    return displays


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def build_audit(root: Path) -> None:
    manifest_path = (
        root / "sources/literature/jama_health_forum_examples/snapshots/2026-07-14/manifest.yml"
    )
    manifest = read_manifest(manifest_path)
    snapshot_root = manifest_path.parent
    output_root = root / "outputs/manuscript/jama_style_audit"
    output_root.mkdir(parents=True, exist_ok=True)

    all_metrics: list[dict[str, Any]] = []
    section_payload: dict[str, dict[str, str]] = {}
    article_summaries: list[dict[str, Any]] = []
    display_payload: dict[str, list[dict[str, Any]]] = {}

    for article in manifest["articles"]:
        article_id = article["id"]
        pdf_path = snapshot_root / article["copied_filename"]
        observed_hash = sha256_file(pdf_path)
        if observed_hash != article["sha256"]:
            raise SystemExit(f"Checksum mismatch for {article_id}: {observed_hash}")

        text = clean_text(extract_pdf_text(pdf_path))
        display_text = clean_text(extract_pdf_text(pdf_path, exclude_tables=False))
        sections = extract_sections(text)
        missing = [name for name in SECTION_NAMES if name not in sections]
        if missing:
            raise SystemExit(f"{article_id} missing sections: {', '.join(missing)}")
        section_payload[article_id] = sections
        for section_name in SECTION_NAMES:
            all_metrics.append(section_metrics(article_id, section_name, sections[section_name]))

        displays = display_inventory(display_text)
        display_payload[article_id] = displays
        article_summaries.append(
            {
                "article_id": article_id,
                "title": article["title"],
                "doi": article["doi"],
                "front_matter": extract_front_matter(text),
                "headings": heading_inventory(text),
                "display_count": len(
                    [display for display in displays if display["display_type"] != "supplement"]
                ),
                "supplement_display_count": len(
                    [display for display in displays if display["display_type"] == "supplement"]
                ),
            }
        )

    (output_root / "sections.json").write_text(
        json.dumps(section_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_csv(output_root / "section_metrics.csv", all_metrics)
    (output_root / "display_inventory.json").write_text(
        json.dumps(display_payload, indent=2, sort_keys=True), encoding="utf-8"
    )
    (output_root / "article_summary.json").write_text(
        json.dumps(article_summaries, indent=2, sort_keys=True), encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    build_audit(args.root.resolve())


if __name__ == "__main__":
    main()
