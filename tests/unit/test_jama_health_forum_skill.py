import json
from pathlib import Path
import types

import yaml  # type: ignore[import-untyped]


ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/write-jama-health-forum-manuscript"


def _load_auditor():
    path = SKILL / "scripts/audit_manuscript.py"
    module = types.ModuleType("audit_jama_manuscript")
    module.__file__ = str(path)
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), module.__dict__)
    return module


def test_skill_package_has_required_resources() -> None:
    required = {
        "SKILL.md",
        "agents/openai.yaml",
        "evals/evals.json",
        "scripts/audit_manuscript.py",
        "references/audit-rubric.md",
        "references/jama-requirements.md",
        "references/writing-style.md",
        "references/chicagohealthmap-profile.md",
    }

    assert required <= {str(path.relative_to(SKILL)) for path in SKILL.rglob("*") if path.is_file()}


def test_skill_package_excludes_generated_python_artifacts() -> None:
    packaged_paths = {str(path.relative_to(SKILL)) for path in SKILL.rglob("*")}

    assert not any("__pycache__" in path for path in packaged_paths)
    assert not any(path.endswith(".pyc") for path in packaged_paths)


def test_skill_metadata_is_trigger_rich_and_project_neutral() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(text.split("---", 2)[1])

    assert set(frontmatter) == {"name", "description"}
    assert frontmatter["name"] == "write-jama-health-forum-manuscript"
    assert frontmatter["description"].startswith("Use when")
    for trigger in (
        "audit",
        "draft",
        "revise",
        "JAMA paper writing",
        "JAMA manuscript",
        "JAMA Health Forum",
        "Original Investigation",
    ):
        assert trigger in frontmatter["description"]
    assert "TODO" not in text
    assert "ChicagoHealthMap" not in frontmatter["description"]


def test_skill_allows_implicit_global_invocation() -> None:
    config = yaml.safe_load((SKILL / "agents/openai.yaml").read_text(encoding="utf-8"))

    assert config["policy"]["allow_implicit_invocation"] is True


def test_skill_gates_journal_scope_before_applying_requirements() -> None:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")

    assert "Confirm the target journal" in text
    assert "Do not apply JAMA Health Forum-specific requirements" in text


def test_skill_has_realistic_behavioral_evals() -> None:
    payload = json.loads((SKILL / "evals/evals.json").read_text(encoding="utf-8"))
    evals = payload["evals"]

    assert payload["skill_name"] == "write-jama-health-forum-manuscript"
    assert len(evals) >= 4
    assert len({item["id"] for item in evals}) == len(evals)
    for item in evals:
        assert isinstance(item["id"], int)
        assert item["prompt"].strip()
        assert item["expected_output"].strip()
        assert isinstance(item["files"], list)
        assert len(item["expectations"]) >= 2
        assert all(expectation.strip() for expectation in item["expectations"])


def test_generic_auditor_reports_structure_and_limits(tmp_path: Path) -> None:
    auditor = _load_auditor()
    manuscript = tmp_path / "manuscript.md"
    manuscript.write_text(
        "# A Question About Health Policy?\n\n"
        "## Key Points\nQuestion: What was studied?\n"
        "Findings: In this cross-sectional study, the measures were associated.\n"
        "Meaning: The results may inform policy.\n\n"
        "## Abstract\n### Importance\nThis question matters.\n"
        "### Objective\nTo examine an association.\n"
        "### Design\nCross-sectional study.\n"
        "### Setting\nChicago.\n### Participants\nAdults.\n"
        "### Exposure\nObserved measure.\n"
        "### Main Outcomes and Measures\nPrimary outcome.\n"
        "### Results\nThe estimate was 1.2 (95% CI, 1.0-1.4).\n"
        "### Conclusions and Relevance\nThe measures were associated.\n\n"
        "## Introduction\nBackground and objective.\n\n"
        "## Methods\nDesign and analysis.\n\n"
        "## Results\nPrimary findings.\n\n"
        "## Discussion\nInterpretation.\n\n"
        "## Limitations\nLimitations.\n\n"
        "## Conclusions\nConclusion.\n",
        encoding="utf-8",
    )

    report = auditor.audit_manuscript(manuscript)

    assert report["title"]["characters"] > 0
    assert "Introduction" in report["section_words"]
    assert "Abstract" in report["section_words"]
    assert any("question" in warning.casefold() for warning in report["warnings"])
    assert set(report["abstract_headings_present"]) >= {
        "Importance",
        "Objective",
        "Design",
        "Setting",
        "Participants",
        "Exposures",
        "Main Outcomes and Measures",
        "Results",
        "Conclusions and Relevance",
    }

    encoded = json.dumps(report)
    assert "manuscript.md" in encoded


def test_auditor_does_not_double_count_nested_discussion_sections(
    tmp_path: Path,
) -> None:
    auditor = _load_auditor()
    manuscript = tmp_path / "nested.md"
    unique_paragraphs = [
        "The policy problem affects many adults.",
        "We analyzed records using prespecified methods.",
        "The primary estimate was precisely measured.",
        "The findings showed a bounded association.",
        "Selection may limit the estimated association.",
        "The findings may inform further evaluation.",
    ]
    manuscript.write_text(
        "# Policy Measures and Health Outcomes\n\n"
        f"## Introduction\n{unique_paragraphs[0]}\n\n"
        f"## Methods\n{unique_paragraphs[1]}\n\n"
        f"## Results\n{unique_paragraphs[2]}\n\n"
        f"## Discussion\n{unique_paragraphs[3]}\n\n"
        f"### Limitations\n{unique_paragraphs[4]}\n\n"
        f"### Conclusions\n{unique_paragraphs[5]}\n",
        encoding="utf-8",
    )

    report = auditor.audit_manuscript(manuscript)
    expected = sum(len(auditor.words(paragraph)) for paragraph in unique_paragraphs)

    assert report["main_text_words"] == expected


def test_auditor_accepts_concise_key_points_and_standard_ci_notation(
    tmp_path: Path,
) -> None:
    auditor = _load_auditor()
    manuscript = tmp_path / "concise.md"
    manuscript.write_text(
        "# Policy Measures and Health Outcomes\n\n"
        "## Key Points\n"
        "Question: Were the measures associated?\n"
        "Findings: In this cross-sectional study, the measures differed across areas.\n"
        "Meaning: The findings may support further evaluation.\n\n"
        "## Abstract\n"
        "### Importance\nPolicy evidence is limited.\n"
        "### Objective\nTo examine an association.\n"
        "### Design\nCross-sectional study.\n"
        "### Setting\nCommunity settings.\n"
        "### Participants\nObserved adults.\n"
        "### Exposure\nArea measure.\n"
        "### Main Outcomes and Measures\nPrimary outcome.\n"
        "### Results\nThe estimate was 1.2 (95% CI, 1.0-1.4).\n"
        "### Conclusions and Relevance\nThe measures were associated.\n\n"
        "## Introduction\nBackground and objective.\n\n"
        "## Methods\nDesign and analysis.\n\n"
        "## Results\nPrimary findings.\n\n"
        "## Discussion\nInterpretation.\n\n"
        "### Limitations\nSelection limits interpretation.\n\n"
        "### Conclusions\nFurther evaluation is warranted.\n",
        encoding="utf-8",
    )

    warnings = auditor.audit_manuscript(manuscript)["warnings"]

    assert not any("Key Points should" in warning for warning in warnings)
    assert not any("abbreviations in abstract: CI" in warning for warning in warnings)
