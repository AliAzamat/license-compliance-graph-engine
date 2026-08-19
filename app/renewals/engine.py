"""Given an entity's obligations and its filing history, compute each next-due
date from the cadence and classify it. Pure, deterministic date arithmetic —
the same inputs always produce the same schedule, which is what makes it auditable."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

from dateutil.relativedelta import relativedelta

from app.graph.traversal import Obligation

DUE_SOON_DAYS = 45  # a renewal within this window is flagged for action


@dataclass
class DueItem:
    requirement: str
    state: str
    license_type: str
    next_due: Optional[date]
    status: str  # lapsed | due_soon | upcoming | unknown
    days_until: Optional[int]


def _next_due(last_filed: Optional[date], interval_months: Optional[int]) -> Optional[date]:
    """Next due = last filed + interval. One-time (no interval) has no next due."""
    if interval_months is None:
        return None
    base = last_filed or date.today()
    return base + relativedelta(months=interval_months)


def classify(
    obligations: list[Obligation],
    last_filed: dict[str, date],
    today: Optional[date] = None,
) -> list[DueItem]:
    """last_filed maps requirement_id -> the date it was last filed (if ever)."""
    today = today or date.today()
    items: list[DueItem] = []
    for ob in obligations:
        filed = last_filed.get(ob.requirement_id)
        due = _next_due(filed, ob.interval_months)
        if due is None:
            status, days = ("unknown" if filed is None else "upcoming"), None
        else:
            days = (due - today).days
            if days < 0:
                status = "lapsed"
            elif days <= DUE_SOON_DAYS:
                status = "due_soon"
            else:
                status = "upcoming"
        items.append(DueItem(ob.requirement, ob.state, ob.license_type, due, status, days))
    # Surface the most urgent first: lapsed, then soonest due.
    order = {"lapsed": 0, "due_soon": 1, "upcoming": 2, "unknown": 3}
    items.sort(key=lambda i: (order[i.status], i.days_until if i.days_until is not None else 10**6))
    return items
