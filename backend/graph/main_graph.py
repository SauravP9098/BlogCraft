from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from backend.graph.reducer_graph import reducer_subgraph
from backend.nodes.orchestrator import fanout, orchestrator_node
from backend.nodes.research import research_node
from backend.nodes.router import route_next, router_node
from backend.nodes.worker import worker_node
from backend.schemas import State

# Router -> (Research?) -> Orchestrator -> Workers -> ReducerWithImages
g = StateGraph(State)
g.add_node("router", router_node)
g.add_node("research", research_node)
g.add_node("orchestrator", orchestrator_node)
g.add_node("worker", worker_node)
g.add_node("reducer", reducer_subgraph)

g.add_edge(START, "router")
g.add_conditional_edges("router", route_next, {"research": "research", "orchestrator": "orchestrator"})
g.add_edge("research", "orchestrator")
g.add_conditional_edges("orchestrator", fanout, ["worker"])
g.add_edge("worker", "reducer")
g.add_edge("reducer", END)

app = g.compile()
