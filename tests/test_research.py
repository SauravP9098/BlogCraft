from unittest.mock import MagicMock

from backend.nodes import research as research_mod
from backend.schemas import EvidenceItem, EvidencePack
from backend.utils.dates import _iso_to_date


def _state(mode):
    return {
        "queries": ["q1"],
        "as_of": "2026-11-18",
        "recency_days": 7,
        "mode": mode,
    }


def _patch(monkeypatch, items):
    monkeypatch.setattr(research_mod, "_tavily_search", lambda q, max_results=5: [{"url": "x"}])
    m = MagicMock()
    m.with_structured_output.return_value.invoke.return_value = EvidencePack(evidence=items)
    monkeypatch.setattr(research_mod, "llm", m)


ITEMS = [
    EvidenceItem(title="new", url="https://a.com", published_at="2026-11-16"),
    EvidenceItem(title="old", url="https://b.com", published_at="2026-01-01"),
    EvidenceItem(title="undated", url="https://c.com", published_at=None),
    EvidenceItem(title="dup", url="https://a.com", published_at="2026-11-16"),
]


def test_open_book_filters_old_and_undated_and_dedupes(monkeypatch):
    _patch(monkeypatch, ITEMS)
    out = research_mod.research_node(_state("open_book"))
    assert [e.url for e in out["evidence"]] == ["https://a.com"]


def test_hybrid_does_not_filter_by_date(monkeypatch):
    _patch(monkeypatch, ITEMS)
    out = research_mod.research_node(_state("hybrid"))
    assert {e.url for e in out["evidence"]} == {"https://a.com", "https://b.com", "https://c.com"}


def test_no_results_returns_empty(monkeypatch):
    monkeypatch.setattr(research_mod, "_tavily_search", lambda q, max_results=5: [])
    assert research_mod.research_node(_state("open_book")) == {"evidence": []}


def test_iso_to_date():
    assert str(_iso_to_date("2026-11-16T10:00:00Z")) == "2026-11-16"
    assert _iso_to_date("garbage") is None
    assert _iso_to_date(None) is None
