"""Map validated RequirementRecords into graph nodes and typed edges. Every write
goes through GraphRepo upserts, so loading the same records twice is a no-op."""
from __future__ import annotations

import re

from app.graph.repository import GraphRepo
from app.extraction.schema import RequirementRecord

repo = GraphRepo()


def _slug(text: str) -> str:
    """Stable natural key from a human label: lower, non-alnum -> '-'."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def load_records(records: list[RequirementRecord]) -> dict[str, int]:
    """Create/refresh the nodes and edges for a batch of extracted requirements.
    Returns simple counts for the audit log. Two-pass so depends_on can resolve."""
    req_nodes: dict[tuple[str, str], str] = {}  # (state, requirement slug) -> node id
    counts = {"states": 0, "license_types": 0, "requirements": 0, "edges": 0}

    # Pass 1: nodes + structural edges (offers, requires, renews_every).
    for r in records:
        state = repo.upsert_node("state", r.state, r.state)
        lt_key = f"{r.state}:{_slug(r.license_type)}"
        lt = repo.upsert_node("license_type", lt_key, r.license_type)
        req_key = f"{lt_key}:{_slug(r.requirement)}"
        req = repo.upsert_node(
            "requirement", req_key, r.requirement,
            attrs={"cadence": r.cadence, "interval_months": r.interval_months,
                   "source_page": r.source_page},
        )
        req_nodes[(r.state, _slug(r.requirement))] = req.id

        repo.upsert_edge(state.id, lt.id, "offers")
        repo.upsert_edge(lt.id, req.id, "requires")
        if r.interval_months:
            # A self-edge carrying the cadence: the requirement renews every N months.
            repo.upsert_edge(req.id, req.id, "renews_every",
                             attrs={"interval_months": r.interval_months})
        counts["edges"] += 2

    counts["states"] = len({r.state for r in records})
    counts["license_types"] = len({(r.state, r.license_type) for r in records})
    counts["requirements"] = len(req_nodes)

    # Pass 2: depends_on edges, now that all requirement nodes exist.
    for r in records:
        if not r.depends_on:
            continue
        src = req_nodes.get((r.state, _slug(r.requirement)))
        dst = req_nodes.get((r.state, _slug(r.depends_on)))
        if src and dst:
            repo.upsert_edge(src, dst, "depends_on")
            counts["edges"] += 1
    return counts
