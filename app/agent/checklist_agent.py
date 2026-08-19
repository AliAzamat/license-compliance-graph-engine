"""The orchestration: gather ground-truth facts, prompt the model to draft a
checklist over ONLY those facts, and return structured JSON."""
from __future__ import annotations

from typing import Any

from app.agent.tools import gather_compliance_state
from app.agent.prompt import SYSTEM, user_prompt
from app.agent.llm import complete_json


def draft_checklist(entity_key: str, last_filed: dict[str, Any]) -> dict[str, Any]:
    state = gather_compliance_state(entity_key, last_filed)
    if not state["facts"]:
        return {"summary": "No tracked obligations for this entity.", "items": []}
    result = complete_json(SYSTEM, user_prompt(state))
    result["_facts"] = state["facts"]  # carried for the grounding check (next step)
    return result
