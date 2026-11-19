from backend.graph.main_graph import app


def test_graph_compiles_with_expected_nodes():
    nodes = set(app.get_graph().nodes)
    assert {"router", "research", "orchestrator", "worker", "reducer"} <= nodes
