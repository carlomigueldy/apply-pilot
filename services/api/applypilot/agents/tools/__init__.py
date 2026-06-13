"""Agent tool functions — thin sync wrappers reusing existing services and repositories.

Each tool is a plain synchronous function that accepts a SQLAlchemy
:class:`~sqlalchemy.orm.Session` (when DB access is required) and returns
standard Python / Pydantic objects.  Tools never perform embedding or LLM
calls directly; they delegate to the service layer.
"""

from applypilot.agents.tools.evidence_search import evidence_search
from applypilot.agents.tools.profile_lookup import list_profile_by_type, profile_lookup
from applypilot.agents.tools.salary_strategy import salary_strategy

__all__ = [
    "evidence_search",
    "list_profile_by_type",
    "profile_lookup",
    "salary_strategy",
]
