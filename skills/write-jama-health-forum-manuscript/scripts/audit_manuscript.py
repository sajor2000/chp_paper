#!/usr/bin/env python3
"""Audit Markdown or plain-text manuscripts against stable JAMA Health Forum checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
from typing import Any


MAIN_SECTIONS = ("Introduction", "Methods", "Results", "Discussion", "Limitations", "Conclusions")
ABSTRACT_HEADINGS = (
    "Importance",
    "Objective",
    "Design",
    "Setting",
    "Participants",
    "Exposures",
    "Main Outcomes and Measures",
    "Results",
    "Conclusions and Relevance",
)
ABSTRACT_HEADING_ALIASES = {
    "Exposures": ("Exposure", "Exposures", "Intervention", "Interventions"),
    "Main Outcomes and Measures": ("Main Outcome and Measure", "Main Outcomes and Measures"),
}
KEY_POINT_HEADINGS = ("Question", "Findings", "Meaning")
ABSTRACT_STATISTICAL_NOTATION = {"CI", "IQR", "SD"}
LIMITS = {
    "title_characters": 100,
    "abstract_words": 350,
    "main_text_words": 3000,
    "key_points_max_words": 100,
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


def parse_blocks(text: str) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for line in text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if match:
            current = {"heading": match.group(2).strip(), "level": len(match.group(1)), "lines": []}
            blocks.append(current)
        elif current is not None:
            current["lines"].append(line)
    return blocks


def block_content(blocks: list[dict[str, Any]], index: int) -> str:
    block = blocks[index]
    content = list(block["lines"])
    for following in blocks[index + 1 :]:
        if following["level"] <= block["level"]:
            break
        content.extend(following["lines"])
    return "\n".join(content).strip()


def block_end(blocks: list[dict[str, Any]], index: int) -> int:
    level = blocks[index]["level"]
    for following_index in range(index + 1, len(blocks)):
        if blocks[following_index]["level"] <= level:
            return following_index
    return len(blocks)


def find_block(blocks: list[dict[str, Any]], heading: str) -> tuple[int, dict[str, Any]] | None:
    target = heading.casefold()
    for index, block in enumerate(blocks):
        if block["heading"].casefold() == target:
            return index, block
    return None


def child_headings(blocks: list[dict[str, Any]], parent_heading: str) -> list[str]:
    found = find_block(blocks, parent_heading)
    if found is None:
        return []
    index, parent = found
    headings: list[str] = []
    for following in blocks[index + 1 :]:
        if following["level"] <= parent["level"]:
            break
        headings.append(following["heading"])
    return headings


def audit_manuscript(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    blocks = parse_blocks(text)
    warnings: list[str] = []

    title_block = next((block for block in blocks if block["level"] == 1), None)
    title = title_block["heading"] if title_block else path.stem
    title_characters = len(title)
    if title_characters > LIMITS["title_characters"]:
        warnings.append(f"Title exceeds {LIMITS['title_characters']} characters.")
    if "?" in title:
        warnings.append("Title is phrased as a question; research titles should not be questions.")
    if re.search(r"\b(study|analysis|cohort|cross-sectional|case-control)\b", title, re.I):
        warnings.append(
            "Review study-design wording in the title; observational reports omit design."
        )
    if re.search(r"\b[A-Z]{2,}\b", title):
        warnings.append("Review abbreviation in title; JAMA titles should not use abbreviations.")

    section_words: dict[str, int] = {}
    section_text: dict[str, str] = {}
    for heading in (*MAIN_SECTIONS, "Abstract", "Key Points"):
        found = find_block(blocks, heading)
        content = block_content(blocks, found[0]) if found else ""
        section_text[heading] = content
        section_words[heading] = len(words(content))

    missing_main = [heading for heading in MAIN_SECTIONS if not section_text[heading]]
    if missing_main:
        warnings.append(f"Missing or empty main sections: {', '.join(missing_main)}.")

    main_blocks = sorted(
        found[0] for heading in MAIN_SECTIONS if (found := find_block(blocks, heading)) is not None
    )
    main_text_parts: list[str] = []
    covered_until = -1
    for index in main_blocks:
        if index < covered_until:
            continue
        main_text_parts.append(block_content(blocks, index))
        covered_until = block_end(blocks, index)
    main_text_words = len(words(" ".join(main_text_parts)))
    if main_text_words > LIMITS["main_text_words"]:
        warnings.append(f"Main text exceeds {LIMITS['main_text_words']} words.")
    if section_words["Abstract"] > LIMITS["abstract_words"]:
        warnings.append(f"Abstract exceeds {LIMITS['abstract_words']} words.")
    key_points_words = section_words["Key Points"]
    if key_points_words:
        key_points_body = re.sub(
            rf"(?im)^\s*(?:{'|'.join(KEY_POINT_HEADINGS)})\s*:\s*",
            "",
            section_text["Key Points"],
        )
        key_points_words = len(words(key_points_body))
        section_words["Key Points"] = key_points_words
    if key_points_words > LIMITS["key_points_max_words"]:
        warnings.append(f"Key Points exceeds {LIMITS['key_points_max_words']} words.")

    abstract_children = child_headings(blocks, "Abstract")
    observed_abstract_headings = {item.casefold() for item in abstract_children}
    abstract_present = [
        heading
        for heading in ABSTRACT_HEADINGS
        if any(
            alias.casefold() in observed_abstract_headings
            for alias in ABSTRACT_HEADING_ALIASES.get(heading, (heading,))
        )
    ]
    missing_abstract = [heading for heading in ABSTRACT_HEADINGS if heading not in abstract_present]
    if missing_abstract:
        warnings.append(f"Missing abstract headings: {', '.join(missing_abstract)}.")

    key_text = section_text["Key Points"]
    key_present = [
        heading for heading in KEY_POINT_HEADINGS if re.search(rf"(?im)^\s*{heading}\s*:", key_text)
    ]
    missing_key = [heading for heading in KEY_POINT_HEADINGS if heading not in key_present]
    if missing_key:
        warnings.append(f"Missing Key Points labels: {', '.join(missing_key)}.")

    abstract_acronyms = sorted(
        set(re.findall(r"\b[A-Z]{2,}\b", section_text["Abstract"])) - ABSTRACT_STATISTICAL_NOTATION
    )
    if abstract_acronyms:
        warnings.append(f"Review abbreviations in abstract: {', '.join(abstract_acronyms)}.")

    causal_terms = sorted(
        set(
            re.findall(
                r"\b(?:caused?|effects?|efficacy|impacts?|improved?|led to|reduced?)\b",
                f"{section_text['Methods']} {section_text['Results']}",
                re.I,
            )
        )
    )
    if causal_terms:
        warnings.append(
            f"Review potentially causal Methods/Results terms: {', '.join(causal_terms)}."
        )

    stock_phrases = [
        phrase
        for phrase in (
            "taken together",
            "these findings underscore",
            "it is important to note",
            "it should be noted",
            "valuable lens",
            "may help inform",
        )
        if phrase in text.casefold()
    ]
    if stock_phrases:
        warnings.append(f"Review stock prose phrases: {', '.join(stock_phrases)}.")

    main_sentences = sentences(" ".join(section_text[heading] for heading in MAIN_SECTIONS))
    sentence_lengths = [len(words(sentence)) for sentence in main_sentences]

    return {
        "file": str(path),
        "title": {"text": title, "characters": title_characters},
        "section_words": section_words,
        "main_text_words": main_text_words,
        "abstract_headings_present": abstract_present,
        "key_point_headings_present": key_present,
        "sentence_metrics": {
            "count": len(sentence_lengths),
            "mean_words": round(statistics.mean(sentence_lengths), 2) if sentence_lengths else 0,
            "median_words": round(statistics.median(sentence_lengths), 2)
            if sentence_lengths
            else 0,
            "over_40_words": sum(length > 40 for length in sentence_lengths),
        },
        "warnings": warnings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manuscript", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit_manuscript(args.manuscript.resolve())
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload}\n", encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
