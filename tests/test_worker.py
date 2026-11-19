from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.nodes import orchestrator as orch_mod
from backend.nodes import worker as worker_mod
from backend.schemas import Plan, Task


def _plan():
    tasks = [
        Task(id=i, title=f"S{i}", goal="g", bullets=["a", "b", "c"], target_words=200)
        for i in (1, 2, 3)
    ]
    return Plan(blog_title="My Blog", audience="devs", tone="clear", tasks=tasks)


def test_worker_returns_tagged_section(monkeypatch):
    m = MagicMock()
    m.invoke.return_value = SimpleNamespace(content="  ## S2\ntext  ")
    monkeypatch.setattr(worker_mod, "llm", m)

    plan = _plan()
    payload = {
        "task": plan.tasks[1].model_dump(),
        "plan": plan.model_dump(),
        "topic": "t",
        "mode": "closed_book",
        "as_of": "2026-11-18",
        "recency_days": 3650,
        "evidence": [],
    }
    out = worker_mod.worker_node(payload)
    assert out == {"sections": [(2, "## S2\ntext")]}


def test_fanout_sends_one_worker_per_task():
    plan = _plan()
    state = {
        "plan": plan,
        "topic": "t",
        "mode": "closed_book",
        "as_of": "2026-11-18",
        "recency_days": 3650,
        "evidence": [],
    }
    sends = orch_mod.fanout(state)
    assert len(sends) == 3
    assert all(s.node == "worker" for s in sends)
    assert [s.arg["task"]["id"] for s in sends] == [1, 2, 3]
