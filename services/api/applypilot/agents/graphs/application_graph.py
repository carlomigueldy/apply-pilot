"""The application-analysis LangGraph: raw job post → persisted analysis + drafts.

``build_application_graph`` wires the nodes from :mod:`applypilot.agents.nodes`
into a compiled, synchronous :class:`~langgraph.graph.StateGraph`. External
dependencies are injected once, at build time, via ``functools.partial`` so that
LangGraph only ever invokes ``node(state)`` — the nodes themselves stay
dependency-free and trivially testable.

Topology::

    START
      → validate_input
          ├─(invalid)→ END
          └─(valid)─→ extract_job_details
                       → extract_requirements
                       → retrieve_evidence
                       → rank_evidence
                       → generate_fit_analysis
                       → generate_draft_bundle
                       → persist_outputs
                       → finalize
                       → END

Human review is handled by the approval API, not a LangGraph interrupt, so the
graph is deterministic and requires no checkpointer to run end-to-end.
"""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING, cast

from langgraph.graph import END, START, StateGraph

from applypilot.agents.nodes import (
    extract_job_details,
    extract_requirements,
    finalize,
    generate_draft_bundle,
    generate_fit_analysis,
    persist_outputs,
    rank_evidence,
    retrieve_evidence,
    validate_input,
)
from applypilot.agents.state import ApplicationGraphState

if TYPE_CHECKING:
    from langgraph.graph.state import CompiledStateGraph
    from sqlalchemy.orm import Session

    from applypilot.agents.llm.base import LLMProvider

#: Canonical graph name persisted on ``GraphRun.graph_name``.
GRAPH_NAME: str = "application_graph"

#: Linear execution order of the main pipeline (post-validation), exposed for
#: timing/observability by the driving service. ``validate_input`` is the entry
#: node; the rest run in this sequence when validation passes.
NODE_ORDER: list[str] = [
    "validate_input",
    "extract_job_details",
    "extract_requirements",
    "retrieve_evidence",
    "rank_evidence",
    "generate_fit_analysis",
    "generate_draft_bundle",
    "persist_outputs",
    "finalize",
]


def _route_after_validate(state: ApplicationGraphState) -> str:
    """Branch key after ``validate_input``: ``"invalid"`` if any error was raised."""
    return "invalid" if state.get("errors") else "valid"


def build_application_graph(
    session: Session | None, provider: LLMProvider
) -> CompiledStateGraph:
    """Build and compile the application-analysis graph.

    Args:
        session: SQLAlchemy session injected into the DB-touching nodes
            (``retrieve_evidence``, ``generate_fit_analysis``, ``persist_outputs``).
            ``None`` is accepted for compile-only checks; never invoke the graph
            with a ``None`` session.
        provider: LLM provider injected into the generative nodes.

    Returns:
        A compiled ``StateGraph`` ready for ``.invoke(initial_state)``.
    """
    graph: StateGraph = StateGraph(ApplicationGraphState)

    # The DB-touching nodes require a live Session at runtime. ``None`` is only
    # tolerated for compile-only checks, where no node is ever invoked, so the
    # cast documents the runtime contract without forcing None-guards into nodes.
    db_session = cast("Session", session)

    # Entry guard (no injected dependencies).
    graph.add_node("validate_input", validate_input)

    # Generative nodes — provider injected.
    graph.add_node(
        "extract_job_details", functools.partial(extract_job_details, provider)
    )
    graph.add_node(
        "extract_requirements", functools.partial(extract_requirements, provider)
    )
    graph.add_node(
        "generate_draft_bundle", functools.partial(generate_draft_bundle, provider)
    )

    # DB-touching nodes — session (and provider) injected.
    graph.add_node(
        "retrieve_evidence", functools.partial(retrieve_evidence, db_session)
    )
    graph.add_node(
        "generate_fit_analysis",
        functools.partial(generate_fit_analysis, db_session, provider),
    )
    graph.add_node("persist_outputs", functools.partial(persist_outputs, db_session))

    # Pure nodes.
    graph.add_node("rank_evidence", rank_evidence)
    graph.add_node("finalize", finalize)

    # Edges.
    graph.add_edge(START, "validate_input")
    graph.add_conditional_edges(
        "validate_input",
        _route_after_validate,
        {"valid": "extract_job_details", "invalid": END},
    )
    graph.add_edge("extract_job_details", "extract_requirements")
    graph.add_edge("extract_requirements", "retrieve_evidence")
    graph.add_edge("retrieve_evidence", "rank_evidence")
    graph.add_edge("rank_evidence", "generate_fit_analysis")
    graph.add_edge("generate_fit_analysis", "generate_draft_bundle")
    graph.add_edge("generate_draft_bundle", "persist_outputs")
    graph.add_edge("persist_outputs", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile()
