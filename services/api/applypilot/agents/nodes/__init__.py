"""Application-graph nodes.

Each node is a plain synchronous function over
:class:`~applypilot.agents.state.ApplicationGraphState` that returns a *partial*
state dict. Nodes that need external dependencies (an LLM provider, a DB session)
take them as leading parameters; the graph factory binds those via
``functools.partial`` so LangGraph only ever calls ``node(state)``.

Execution order: ``validate_input`` → ``extract_job_details`` →
``extract_requirements`` → ``retrieve_evidence`` → ``rank_evidence`` →
``generate_fit_analysis`` → ``generate_draft_bundle`` → ``persist_outputs`` →
``finalize``.
"""

from applypilot.agents.nodes.extract_job_details import extract_job_details
from applypilot.agents.nodes.extract_requirements import extract_requirements
from applypilot.agents.nodes.finalize import finalize
from applypilot.agents.nodes.generate_draft_bundle import generate_draft_bundle
from applypilot.agents.nodes.generate_fit_analysis import generate_fit_analysis
from applypilot.agents.nodes.persist_outputs import persist_outputs
from applypilot.agents.nodes.rank_evidence import rank_evidence
from applypilot.agents.nodes.retrieve_evidence import retrieve_evidence
from applypilot.agents.nodes.validate_input import validate_input

__all__ = [
    "extract_job_details",
    "extract_requirements",
    "finalize",
    "generate_draft_bundle",
    "generate_fit_analysis",
    "persist_outputs",
    "rank_evidence",
    "retrieve_evidence",
    "validate_input",
]
