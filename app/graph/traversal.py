"""The core query: from an entity, compute every requirement it owes across the
states it operates in, ordered so dependencies come before their dependents."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.db.postgres import cursor


@dataclass
class Obligation:
    requirement_id: str
    state: str
    license_type: str
    requirement: str
    cadence: str
    interval_months: int | None
    depth: int  # position in the dependency order (0 = no prerequisites)


def obligations_for_entity(entity_key: str) -> list[Obligation]:
    """Walk entity -[operates_in]-> state -[offers]-> license_type,
    intersect with entity -[holds]-> license_type, then -[requires]-> requirement.
    A recursive CTE orders requirements by depends_on depth."""
    with cursor() as cur:
        cur.execute(
            """
            WITH ent AS (
                SELECT id FROM nodes WHERE type='entity' AND key=%s
            ),
            -- license types the entity HOLDS that its states actually OFFER
            held AS (
                SELECT h.dst_id AS lt_id
                FROM ent
                JOIN edges h  ON h.src_id = ent.id AND h.type='holds'
                JOIN edges op ON op.src_id = ent.id AND op.type='operates_in'
                JOIN edges of2 ON of2.src_id = op.dst_id
                              AND of2.type='offers'
                              AND of2.dst_id = h.dst_id
            ),
            -- requirements those license types impose
            reqs AS (
                SELECT r.dst_id AS req_id
                FROM held
                JOIN edges r ON r.src_id = held.lt_id AND r.type='requires'
            ),
            -- order requirements by depends_on depth (roots first)
            ordered AS (
                SELECT req_id, 0 AS depth
                FROM reqs
                WHERE req_id NOT IN (
                    SELECT src_id FROM edges WHERE type='depends_on'
                )
                UNION ALL
                SELECT e.src_id, o.depth + 1
                FROM ordered o
                JOIN edges e ON e.dst_id = o.req_id AND e.type='depends_on'
            )
            SELECT DISTINCT ON (n.id)
                   n.id AS requirement_id, n.label AS requirement,
                   n.attrs->>'cadence' AS cadence,
                   (n.attrs->>'interval_months')::int AS interval_months,
                   lt.label AS license_type, st.key AS state,
                   o.depth AS depth
            FROM ordered o
            JOIN nodes n   ON n.id = o.req_id
            JOIN edges rq  ON rq.dst_id = n.id AND rq.type='requires'
            JOIN nodes lt  ON lt.id = rq.src_id
            JOIN edges of3 ON of3.dst_id = lt.id AND of3.type='offers'
            JOIN nodes st  ON st.id = of3.src_id
            ORDER BY n.id, o.depth DESC
            """,
            (entity_key,),
        )
        rows = cur.fetchall()
    return [
        Obligation(
            requirement_id=r["requirement_id"], state=r["state"],
            license_type=r["license_type"], requirement=r["requirement"],
            cadence=r["cadence"], interval_months=r["interval_months"],
            depth=r["depth"],
        )
        for r in rows
    ]
