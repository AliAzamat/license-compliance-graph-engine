"""Thin tools over the graph + renewal engine. The agent orchestrates; it never
recomputes obligations itself, so its facts are exactly what the graph produced."""
from __future__ import annotations

from typing import Any

from app.graph.traversal import obligations_for_entity
from app.renewals.engine import classify


def gather_compliance_state(entity_key: str, last_filed: dict[str, Any]) -> dict[str, Any]:
    """Compute the entity's obligations and their due status. This dict is the
    ONLY ground truth the agent is allowed to reason from."""
    obligations = obligations_for_entity(entity_key)
    due_items = classify(obligations, last_filed)
    return {
        "entity": entity_key,
        "facts": [
            {
                "requirement": d.requirement,
                "state": d.state,
                "license_type": d.license_type,
                "next_due": d.next_due.isoformat() if d.next_due else None,
                "status": d.status,
                "days_until": d.days_until,
            }
            for d in due_items
        ],
    }
