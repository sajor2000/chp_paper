from pathlib import Path


ROOT = Path(__file__).parents[3]
PROVENANCE = ROOT / "docs/analysis/master_notebook_research_provenance.md"


def test_master_notebook_research_provenance_is_claim_linked_and_fail_closed() -> None:
    text = PROVENANCE.read_text(encoding="utf-8")
    for required in (
        "PMC9364501#L49-L50",
        "PMC11262136#L22,L32",
        "PMID 38991533",
        "PMID 35945537",
        "PMID 38478904",
        "PMID 28727539",
        "PMID 26863550",
        "PMID 26262310",
        "monthly_cap_reached_bonus_eligible",
        "opened directly on July 15, 2026",
        "did not prevent direct official-page verification",
        "results_authorized=false",
        "Ref documentation trail",
    ):
        assert required in text
