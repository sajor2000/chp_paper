import csv
import hashlib
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GUIDE = ROOT / "docs/manuscript/jama_health_forum_style_guide.md"
SCRIPT = ROOT / "scripts/manuscript/build_jama_style_audit.py"
REQUIRED_SECTIONS = {
    "Introduction",
    "Methods",
    "Results",
    "Discussion",
    "Limitations",
    "Conclusions",
}
END_MATTER_MARKERS = {
    "References",
    "Data Sharing Statement",
    "ARTICLE INFORMATION",
    "Author Affiliations",
    "SUPPLEMENT",
}


def _load_audit_module():
    spec = importlib.util.spec_from_file_location("build_jama_style_audit", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_style_audit_manifest_reader_supports_portable_yaml(tmp_path: Path) -> None:
    audit = _load_audit_module()
    pdf = tmp_path / "example.pdf"
    pdf.write_bytes(b"portable fixture")
    digest = _sha256(pdf)
    manifest = tmp_path / "manifest.yml"
    manifest.write_text(
        "copyright_caution: true\n"
        "articles:\n"
        "  - article_id: fixture_article\n"
        "    copied_filename: example.pdf\n"
        f"    sha256: {digest}\n"
        "    doi: 10.1001/jamahealthforum.2026.0001\n"
        "    title: Example Article\n"
        "    journal: JAMA Health Forum\n"
        "    article_type: Original Investigation\n"
        "    page_count: 12\n"
        "    role: style exemplar\n"
        "    license_note: open access license recorded\n"
        "    source_path: local-fixture\n",
        encoding="utf-8",
    )

    loaded = audit.read_manifest(manifest)

    assert loaded["copyright_caution"] is True
    assert loaded["articles"][0]["sha256"] == digest


def test_extract_sections_are_bounded_to_manuscript_body() -> None:
    audit = _load_audit_module()
    text = "\n\n".join(
        (
            "Introduction\nThis is the introduction body with enough words to parse.",
            "Methods\nThis is the methods body with enough words to parse.",
            "Results\nThis is the results body with enough words to parse.",
            "Discussion\nThis is the discussion body with enough words to parse.",
            "Limitations\nThis is the limitations body with enough words to parse.",
            "Conclusions\nThis is the conclusions body with enough words to parse.",
            "References\n1. End matter should not appear.",
        )
    )

    sections = audit.extract_sections(text)

    assert set(sections) == REQUIRED_SECTIONS
    for section_name, section_text in sections.items():
        assert section_text.startswith(section_name)
        for marker in END_MATTER_MARKERS:
            assert marker not in section_text


def test_metrics_output_shape_is_portable(tmp_path: Path) -> None:
    metrics = tmp_path / "section_metrics.csv"
    fields = (
        "article_id",
        "section",
        "word_count",
        "sentence_count",
        "mean_sentence_words",
        "flesch_kincaid_grade",
        "paragraph_count",
        "passive_flag_count",
        "nominalization_flag_count",
        "hedge_term_count",
        "numeric_tokens_per_100_words",
    )
    with metrics.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for article_id in ("article_a", "article_b"):
            for section in REQUIRED_SECTIONS:
                writer.writerow(
                    {
                        "article_id": article_id,
                        "section": section,
                        "word_count": "25",
                        "sentence_count": "2",
                        "mean_sentence_words": "12.5",
                        "flesch_kincaid_grade": "14.0",
                        "paragraph_count": "1",
                        "passive_flag_count": "0",
                        "nominalization_flag_count": "0",
                        "hedge_term_count": "1",
                        "numeric_tokens_per_100_words": "0.0",
                    }
                )

    with metrics.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == 12
    by_article: dict[str, set[str]] = {}
    for row in rows:
        by_article.setdefault(row["article_id"], set()).add(row["section"])
        for field in (
            "word_count",
            "sentence_count",
            "mean_sentence_words",
            "flesch_kincaid_grade",
            "paragraph_count",
            "passive_flag_count",
            "nominalization_flag_count",
            "hedge_term_count",
            "numeric_tokens_per_100_words",
        ):
            assert row[field] != ""

    assert all(sections == REQUIRED_SECTIONS for sections in by_article.values())


def test_sentence_segmentation_handles_jama_numeric_citations() -> None:
    audit = _load_audit_module()
    text = (
        "The first claim ends here.1-3 The next sentence reports a result.4,5 "
        "The final sentence has no citation."
    )

    assert len(audit.sentences(text)) == 3


def test_sentence_segmentation_does_not_split_decimal_table_values() -> None:
    audit = _load_audit_module()
    text = "Model values were 0.04 0.82 0.72. The next prose sentence starts here."

    assert len(audit.sentences(text)) == 2


def test_style_guide_includes_requested_audit_domains() -> None:
    text = GUIDE.read_text(encoding="utf-8")
    required_phrases = (
        "sentence length",
        "Flesch-Kincaid",
        "syntax",
        "Introduction",
        "Methods",
        "Results",
        "Discussion",
        "Abstract and Key Points",
        "Tables and Figures",
        "EHR-diagnosed proportion among observed CAPriCORN adults",
    )
    for phrase in required_phrases:
        assert phrase in text


def test_style_guide_distinguishes_corpus_patterns_from_requirements() -> None:
    text = GUIDE.read_text(encoding="utf-8")

    required_phrases = (
        "Observed in the 2-paper corpus",
        "ChicagoHealthMap drafting rule",
        "Journal requirement",
        "screening description",
        "not a target",
        "PDF-extracted paragraph boundaries are not used",
        "This is not population prevalence.",
        "Recheck the journal instructions within 30 days of submission.",
    )
    for phrase in required_phrases:
        assert phrase in text


def test_style_guide_includes_human_and_current_jama_controls() -> None:
    text = GUIDE.read_text(encoding="utf-8")

    required_phrases = (
        "Real Sentences to Model",
        "Human Scientific Voice",
        "Human Accountability and AI Use",
        "Human Revision Pass",
        "Keep Design, Setting, and Participants separate at submission",
        "primary comparison reads horizontally",
        "Do not use pie charts or 3-dimensional graphs",
        "do not estimate population prevalence or establish service need",
    )
    for phrase in required_phrases:
        assert phrase in text
