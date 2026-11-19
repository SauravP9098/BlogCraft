from __future__ import annotations

from datetime import date, timedelta
from typing import List

from langchain_core.messages import HumanMessage, SystemMessage

from backend.config import MAX_QUERIES, MAX_RESULTS_PER_QUERY
from backend.llm import llm
from backend.prompts.research import RESEARCH_SYSTEM
from backend.schemas import EvidencePack, State
from backend.tools.tavily_search import _tavily_search
from backend.utils.dates import _iso_to_date


def research_node(state: State) -> dict:
    queries = (state.get("queries") or [])[:MAX_QUERIES]
    raw: List[dict] = []
    for q in queries:
        raw.extend(_tavily_search(q, max_results=MAX_RESULTS_PER_QUERY))

    if not raw:
        return {"evidence": []}

    extractor = llm.with_structured_output(EvidencePack)
    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_SYSTEM),
            HumanMessage(
                content=(
                    f"As-of date: {state['as_of']}\n"
                    f"Recency days: {state['recency_days']}\n\n"
                    f"Raw results:\n{raw}"
                )
            ),
        ]
    )

    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e

    evidence = list(dedup.values())

    if state.get("mode") == "open_book":
        as_of = date.fromisoformat(state["as_of"])
        cutoff = as_of - timedelta(days=int(state["recency_days"]))
        evidence = [e for e in evidence if (d := _iso_to_date(e.published_at)) and d >= cutoff]

    return {"evidence": evidence}
