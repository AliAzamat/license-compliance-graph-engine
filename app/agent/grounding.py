"""Post-generation verification. The agent may only assert obligations that exist
in the facts. Any item that doesn't match a real fact is dropped and reported —
the last gate that makes a hallucinated compliance rule impossible to ship."""
from __future__ import annotations

from typing import Any


def _fact_key(requirement: str, state: str, due: str | None) -> tuple[str, str, str]:
    return (requirement.strip().lower(), state.strip().upper(), (due or "").strip())


def verify_grounded(result: dict[str, Any]) -> dict[str, Any]:
    """Keep only checklist items whose (requirement, state, due) matches a fact.
    Returns the filtered result plus a list of dropped, ungrounded items."""
    facts = result.get("_facts", [])
    allowed = {
        _fact_key(f["requirement"], f["state"], f.get("next_due"))
        for f in facts
    }

    grounded: list[dict[str, Any]] = []
    dropped: list[dict[str, Any]] = []
    for item in result.get("items", []):
        key = _fact_key(item.get("requirement", ""), item.get("state", ""), item.get("due"))
        if key in allowed:
            # Attach provenance: the exact fact this item is grounded in.
            item["grounded"] = True
            grounded.append(item)
        else:
            dropped.append(item)

    out = {
        "summary": result.get("summary", ""),
        "items": grounded,
        "dropped_ungrounded": dropped,
        "grounded_ratio": round(len(grounded) / max(1, len(grounded) + len(dropped)), 3),
    }
    return out
