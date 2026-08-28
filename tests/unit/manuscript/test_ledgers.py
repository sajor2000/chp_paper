from pathlib import Path

import pandas as pd
import pytest

from chicagohealthmap.manuscript.ledgers import LedgerError, verify_ledgers


def _write_record(control_dir: Path, filename: str, record: dict[str, str]) -> None:
    pd.DataFrame([record]).to_csv(control_dir / filename, index=False)


def _valid_claim(**changes: str) -> dict[str, str]:
    claim = {
        "claim_id": "R-001",
        "section": "Results",
        "draft_claim": "The observed proportion was 12%.",
        "claim_class": "result",
        "source_or_artifact_id": "artifact-001",
        "exact_support_location": "estimate.value",
        "population_geography_measure_period_match": "exact",
        "support_strength": "frozen",
        "conflict_or_gap": "",
        "allowed_wording": "was",
        "prohibited_inference": "caused",
        "result_status": "prespecified",
        "owner": "results agent",
        "verified_by": "",
        "verified_date": "",
        "final_text_location": "Results paragraph 1",
    }
    claim.update(changes)
    return claim


def _valid_number(**changes: str) -> dict[str, str]:
    number = {
        "number_id": "N-001",
        "artifact_id": "artifact-001",
        "checksum": "sha256:" + "0" * 64,
        "artifact_field": "estimate.value",
        "code_version": "abc1234",
        "population": "observed CAPriCORN adults",
        "exclusions": "none",
        "geography": "Chicago community area",
        "time_period": "2022",
        "measure": "EHR-diagnosed proportion",
        "unit": "percent",
        "denominator": "1000",
        "raw_value": "0.12",
        "display_value": "12%",
        "uncertainty": "95% CI, 10%-14%",
        "result_status": "prespecified",
        "manuscript_locations": "Results paragraph 1",
    }
    number.update(changes)
    return number


def _valid_ai_use(**changes: str) -> dict[str, str]:
    ai_use = {
        "ai_use_id": "AI-001",
        "platform": "OpenAI Codex",
        "model": "unavailable",
        "manufacturer": "OpenAI",
        "start_date": "2026-07-14",
        "end_date": "2026-07-14",
        "use": "outline design",
        "affected_artifact": "blueprint",
        "human_verifier": "J Doe",
        "verified_date": "2026-07-14",
    }
    ai_use.update(changes)
    return ai_use


def _valid_issue(**changes: str) -> dict[str, str]:
    issue = {
        "issue_id": "I-001",
        "severity": "critical",
        "gate": "M5",
        "description": "Numerical discrepancy",
        "evidence": "review report",
        "owner": "statistical QA human",
        "status": "open",
        "resolution": "",
    }
    issue.update(changes)
    return issue


def test_empty_header_only_ledgers_are_valid(control_dir: Path, contracts) -> None:
    report = verify_ledgers(control_dir, contracts)

    assert report.claims == 0
    assert report.numbers == 0
    assert report.ai_uses == 0
    assert report.open_critical_issues == 0


def test_valid_ledgers_report_counts(control_dir: Path, contracts) -> None:
    _write_record(control_dir, "claim_ledger.csv", _valid_claim())
    _write_record(control_dir, "number_ledger.csv", _valid_number())
    _write_record(control_dir, "ai_use_ledger.csv", _valid_ai_use())
    _write_record(control_dir, "issue_ledger.csv", _valid_issue())

    report = verify_ledgers(control_dir, contracts)

    assert report.claims == 1
    assert report.numbers == 1
    assert report.ai_uses == 1
    assert report.open_critical_issues == 1


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"source_or_artifact_id": ""}, "result claim R-001 requires a frozen artifact"),
        ({"exact_support_location": ""}, "result claim R-001 requires a frozen artifact"),
        ({"support_strength": "draft"}, "result claim R-001 requires a frozen artifact"),
    ],
)
def test_result_claim_requires_frozen_artifact(
    control_dir: Path,
    contracts,
    changes: dict[str, str],
    message: str,
) -> None:
    _write_record(control_dir, "claim_ledger.csv", _valid_claim(**changes))

    with pytest.raises(LedgerError, match=message):
        verify_ledgers(control_dir, contracts)


def test_result_claim_requires_matching_number_artifact(control_dir: Path, contracts) -> None:
    _write_record(control_dir, "claim_ledger.csv", _valid_claim())
    _write_record(
        control_dir,
        "number_ledger.csv",
        _valid_number(artifact_id="different-artifact"),
    )

    with pytest.raises(LedgerError, match="result claim R-001 has no matching number artifact"):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize("field", ["artifact_id", "artifact_field", "code_version"])
@pytest.mark.parametrize("blank", ["", "   "])
def test_number_artifact_lineage_fields_are_required(
    control_dir: Path, contracts, field: str, blank: str
) -> None:
    _write_record(control_dir, "number_ledger.csv", _valid_number(**{field: blank}))

    with pytest.raises(LedgerError, match=rf"number N-001 requires nonblank {field}"):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    "checksum",
    [
        "0" * 64,
        "sha256:" + "A" * 64,
        "sha256:abc",
        "md5:" + "0" * 64,
        " sha256:" + "0" * 64,
        "sha256:" + "0" * 64 + " ",
    ],
)
def test_number_checksum_requires_canonical_sha256(
    control_dir: Path, contracts, checksum: str
) -> None:
    _write_record(control_dir, "number_ledger.csv", _valid_number(checksum=checksum))

    with pytest.raises(LedgerError, match="number_ledger.csv row 1 is invalid"):
        verify_ledgers(control_dir, contracts)


def test_ledger_report_exposes_immutable_number_checksum_links(
    control_dir: Path, contracts
) -> None:
    _write_record(control_dir, "number_ledger.csv", _valid_number())

    report = verify_ledgers(control_dir, contracts)

    assert report.number_artifacts == (("artifact-001", "sha256:" + "0" * 64),)
    with pytest.raises(TypeError):
        report.number_artifacts[0] = ("other", "sha256:" + "1" * 64)


def test_verified_non_result_claim_requires_independent_verifier(
    control_dir: Path, contracts
) -> None:
    _write_record(
        control_dir,
        "claim_ledger.csv",
        _valid_claim(
            claim_id="M-001",
            claim_class="method",
            support_strength="verified",
            result_status="not_applicable",
            verified_by="",
        ),
    )

    with pytest.raises(LedgerError, match="verified claim M-001 lacks an independent verifier"):
        verify_ledgers(control_dir, contracts)


def test_verified_non_result_claim_requires_verification_date(control_dir: Path, contracts) -> None:
    _write_record(
        control_dir,
        "claim_ledger.csv",
        _valid_claim(
            claim_id="M-001",
            claim_class="method",
            support_strength="verified",
            result_status="not_applicable",
            owner="J Doe",
            verified_by="A Smith",
            verified_date="",
        ),
    )

    with pytest.raises(LedgerError, match="verified claim M-001 lacks a verification date"):
        verify_ledgers(control_dir, contracts)


def test_verified_non_result_claim_rejects_self_verification(control_dir: Path, contracts) -> None:
    _write_record(
        control_dir,
        "claim_ledger.csv",
        _valid_claim(
            claim_id="M-001",
            claim_class="method",
            support_strength="verified",
            result_status="not_applicable",
            owner=" J DOE ",
            verified_by="j doe",
            verified_date="2026-07-14",
        ),
    )

    with pytest.raises(LedgerError, match="verified claim M-001 cannot be self-verified"):
        verify_ledgers(control_dir, contracts)


def test_verified_non_result_claim_requires_owner(control_dir: Path, contracts) -> None:
    _write_record(
        control_dir,
        "claim_ledger.csv",
        _valid_claim(
            claim_id="M-001",
            claim_class="method",
            support_strength="verified",
            result_status="not_applicable",
            owner="   ",
            verified_by="A Smith",
            verified_date="2026-07-14",
        ),
    )

    with pytest.raises(LedgerError, match="verified claim M-001 requires an owner"):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        (
            {"result_status": "not_applicable"},
            "result claim R-001 cannot use not_applicable result status",
        ),
        (
            {
                "claim_id": "M-001",
                "claim_class": "method",
                "support_strength": "draft",
                "result_status": "prespecified",
            },
            "non-result claim M-001 must use not_applicable result status",
        ),
    ],
)
def test_claim_class_and_result_status_must_agree(
    control_dir: Path,
    contracts,
    changes: dict[str, str],
    message: str,
) -> None:
    _write_record(control_dir, "claim_ledger.csv", _valid_claim(**changes))

    with pytest.raises(LedgerError, match=message):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    "changes",
    [
        {"human_verifier": ""},
        {"verified_date": ""},
    ],
)
def test_ai_use_requires_human_verification(
    control_dir: Path, contracts, changes: dict[str, str]
) -> None:
    _write_record(control_dir, "ai_use_ledger.csv", _valid_ai_use(**changes))

    with pytest.raises(LedgerError, match="AI-001 lacks human verification"):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    ("filename", "record", "identifier"),
    [
        ("claim_ledger.csv", _valid_claim(), "claim IDs must be unique"),
        ("number_ledger.csv", _valid_number(), "number IDs must be unique"),
        ("ai_use_ledger.csv", _valid_ai_use(), "AI-use IDs must be unique"),
        ("issue_ledger.csv", _valid_issue(), "issue IDs must be unique"),
    ],
)
def test_ledger_ids_must_be_unique(
    control_dir: Path,
    contracts,
    filename: str,
    record: dict[str, str],
    identifier: str,
) -> None:
    pd.DataFrame([record, record]).to_csv(control_dir / filename, index=False)

    with pytest.raises(LedgerError, match=identifier):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    ("filename", "first", "second", "message"),
    [
        (
            "claim_ledger.csv",
            _valid_claim(claim_id="R-001"),
            _valid_claim(claim_id=" R-001 "),
            "claim IDs must be unique",
        ),
        (
            "number_ledger.csv",
            _valid_number(number_id="N-001"),
            _valid_number(number_id=" N-001 "),
            "number IDs must be unique",
        ),
        (
            "ai_use_ledger.csv",
            _valid_ai_use(ai_use_id="AI-001"),
            _valid_ai_use(ai_use_id=" AI-001 "),
            "AI-use IDs must be unique",
        ),
        (
            "issue_ledger.csv",
            _valid_issue(issue_id="I-001"),
            _valid_issue(issue_id=" I-001 "),
            "issue IDs must be unique",
        ),
    ],
)
def test_ledger_ids_are_unique_after_trimming(
    control_dir: Path,
    contracts,
    filename: str,
    first: dict[str, str],
    second: dict[str, str],
    message: str,
) -> None:
    pd.DataFrame([first, second]).to_csv(control_dir / filename, index=False)

    with pytest.raises(LedgerError, match=message):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    ("filename", "record", "label"),
    [
        ("claim_ledger.csv", _valid_claim(claim_id="   "), "claim ID is required"),
        ("number_ledger.csv", _valid_number(number_id=""), "number ID is required"),
        ("ai_use_ledger.csv", _valid_ai_use(ai_use_id="   "), "AI-use ID is required"),
        ("issue_ledger.csv", _valid_issue(issue_id=""), "issue ID is required"),
    ],
)
def test_ledger_ids_must_not_be_blank(
    control_dir: Path,
    contracts,
    filename: str,
    record: dict[str, str],
    label: str,
) -> None:
    _write_record(control_dir, filename, record)

    with pytest.raises(LedgerError, match=label):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize("mutation", ["missing", "extra", "reordered"])
def test_headers_must_match_exact_schema(control_dir: Path, contracts, mutation: str) -> None:
    path = control_dir / "claim_ledger.csv"
    frame = pd.read_csv(path)
    if mutation == "missing":
        frame = frame.drop(columns=["owner"])
    elif mutation == "extra":
        frame["unexpected"] = pd.Series(dtype="object")
    else:
        frame = frame[list(reversed(frame.columns))]
    frame.to_csv(path, index=False)

    with pytest.raises(LedgerError, match="claim_ledger.csv headers must exactly match"):
        verify_ledgers(control_dir, contracts)


def test_missing_ledger_is_a_ledger_error(control_dir: Path, contracts) -> None:
    (control_dir / "issue_ledger.csv").unlink()

    with pytest.raises(LedgerError, match="issue_ledger.csv is required"):
        verify_ledgers(control_dir, contracts)


def test_invalid_record_schema_is_a_ledger_error(control_dir: Path, contracts) -> None:
    _write_record(control_dir, "issue_ledger.csv", _valid_issue(severity="urgent"))

    with pytest.raises(LedgerError, match="issue_ledger.csv row 1 is invalid"):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize("status", ["resolved", "accepted_by_human"])
@pytest.mark.parametrize("field", ["evidence", "owner", "resolution"])
def test_closed_critical_issue_requires_accountable_disposition(
    control_dir: Path, contracts, status: str, field: str
) -> None:
    changes = {
        "status": status,
        "evidence": "review report",
        "owner": "J Doe",
        "resolution": "corrected and independently checked",
    }
    changes[field] = "   "
    _write_record(
        control_dir,
        "issue_ledger.csv",
        _valid_issue(**changes),
    )

    with pytest.raises(
        LedgerError, match=rf"issue I-001 with status {status} requires nonblank {field}"
    ):
        verify_ledgers(control_dir, contracts)


@pytest.mark.parametrize(
    ("filename", "record"),
    [
        (
            "claim_ledger.csv",
            _valid_claim(
                claim_class="method",
                support_strength="draft",
                verified_date="2026-07-14T00:00:00",
            ),
        ),
        ("ai_use_ledger.csv", _valid_ai_use(start_date="07/14/2026")),
        ("ai_use_ledger.csv", _valid_ai_use(end_date="2026-7-14")),
        ("ai_use_ledger.csv", _valid_ai_use(verified_date="2026-07-14 00:00:00")),
    ],
)
def test_dates_require_exact_iso_calendar_lexical_form(
    control_dir: Path, contracts, filename: str, record: dict[str, str]
) -> None:
    _write_record(control_dir, filename, record)

    with pytest.raises(LedgerError, match=rf"{filename} row 1 is invalid"):
        verify_ledgers(control_dir, contracts)


def test_ai_use_date_range_must_be_ordered(control_dir: Path, contracts) -> None:
    _write_record(
        control_dir,
        "ai_use_ledger.csv",
        _valid_ai_use(start_date="2026-07-15", end_date="2026-07-14"),
    )

    with pytest.raises(LedgerError, match="ai_use_ledger.csv row 1 is invalid"):
        verify_ledgers(control_dir, contracts)


def test_unicode_decode_error_is_normalized(control_dir: Path, contracts) -> None:
    (control_dir / "issue_ledger.csv").write_bytes(b"issue_id,description\n\xff\n")

    with pytest.raises(LedgerError, match="issue_ledger.csv is not a readable ledger"):
        verify_ledgers(control_dir, contracts)


def test_only_open_critical_issues_are_counted(control_dir: Path, contracts) -> None:
    records = [
        _valid_issue(issue_id="I-001", severity="critical", status="open"),
        _valid_issue(
            issue_id="I-002",
            severity="critical",
            status="resolved",
            resolution="corrected",
        ),
        _valid_issue(issue_id="I-003", severity="important", status="open"),
        _valid_issue(
            issue_id="I-004",
            severity="critical",
            status="accepted_by_human",
            resolution="accepted by named gate approver",
        ),
    ]
    pd.DataFrame(records).to_csv(control_dir / "issue_ledger.csv", index=False)

    report = verify_ledgers(control_dir, contracts)

    assert report.open_critical_issues == 1
    assert report.open_important_issues == 1
