from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).parents[2]
EVIDENCE = ROOT / "docs/analysis/chm_complementarity_evidence_ledger.md"
DISPLAY = ROOT / "docs/analysis/chm_complementarity_display_ledger.csv"


def test_complementarity_evidence_ledger_has_traceable_claim_contract() -> None:
    text = EVIDENCE.read_text(encoding="utf-8")

    for field in ("claim", "source artifact", "denominator", "unit", "period", "uncertainty", "analysis status"):
        assert field in text.casefold()
    assert "EHR-diagnosed proportion among observed CAPriCORN adults" in text
    assert "population prevalence" not in text.casefold()
    assert "caused" not in text.casefold()


def test_complementarity_display_ledger_covers_three_main_displays() -> None:
    text = DISPLAY.read_text(encoding="utf-8")

    for display in ("Table 1", "Figure 1", "Table 2"):
        assert display in text
    assert "Reserve Figure S1,Supplement reserve" in text
    assert "Reserve Figure S2,Supplement reserve" in text
    assert "Main Figure 2" not in text
    assert "Main Figure 3" not in text
    assert "results_authorized=false" in text
