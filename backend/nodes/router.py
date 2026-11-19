from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import RECENCY_DAYS
from backend.llm import llm
from backend.prompts.router import ROUTER_SYSTEM
from backend.schemas import RouterDecision, State


def router_node(state: State) -> dict:
    decider = llm.with_structured_output(RouterDecision)
    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {state['topic']}\nAs-of date: {state['as_of']}"),
        ]
    )

    recency_days = RECENCY_DAYS.get(decision.mode, RECENCY_DAYS["closed_book"])

    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
        "recency_days": recency_days,
    }


def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"
