from unittest.mock import MagicMock

from backend.nodes import router as router_mod
from backend.schemas import RouterDecision


def _mock_llm(decision: RouterDecision) -> MagicMock:
    m = MagicMock()
    m.with_structured_output.return_value.invoke.return_value = decision
    return m


def test_router_open_book_sets_7_day_window(monkeypatch):
    decision = RouterDecision(needs_research=True, mode="open_book", reason="weekly news", queries=["ai news"])
    monkeypatch.setattr(router_mod, "llm", _mock_llm(decision))

    out = router_mod.router_node({"topic": "AI news this week", "as_of": "2026-11-18"})

    assert out["mode"] == "open_book"
    assert out["recency_days"] == 7
    assert out["needs_research"] is True
    assert out["queries"] == ["ai news"]


def test_router_hybrid_and_closed_book_windows(monkeypatch):
    for mode, days in (("hybrid", 45), ("closed_book", 3650)):
        decision = RouterDecision(needs_research=(mode == "hybrid"), mode=mode, reason="x")
        monkeypatch.setattr(router_mod, "llm", _mock_llm(decision))
        out = router_mod.router_node({"topic": "t", "as_of": "2026-11-18"})
        assert out["recency_days"] == days


def test_route_next():
    assert router_mod.route_next({"needs_research": True}) == "research"
    assert router_mod.route_next({"needs_research": False}) == "orchestrator"
