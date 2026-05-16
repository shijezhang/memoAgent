from memo_agent.models import Guideline


def test_guideline_creation():
    g = Guideline(
        rule="MAGCN cross-network attention must align features first",
        source_entities=["MAGCN", "cross-network attention"],
        timestamp="2026-05-16T10:00:00",
    )
    assert g.rule == "MAGCN cross-network attention must align features first"
    assert len(g.source_entities) == 2
    assert g.timestamp == "2026-05-16T10:00:00"


def test_guideline_is_dataclass():
    from dataclasses import is_dataclass
    assert is_dataclass(Guideline)
