"""The graph repository: the single place that reads and writes nodes and edges.
Everything above (loader, traversal, agent) speaks in nodes and edges, never SQL."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from app.db.postgres import cursor


@dataclass
class Node:
    id: str
    type: str
    key: str
    label: str
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass
class Edge:
    src_id: str
    dst_id: str
    type: str
    attrs: dict[str, Any] = field(default_factory=dict)


class GraphRepo:
    def upsert_node(self, type: str, key: str, label: str, attrs: dict | None = None) -> Node:
        """Idempotent on (type, key): the same state/requirement resolves to one node."""
        node_id = str(uuid.uuid4())
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO nodes (id, type, key, label, attrs)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (type, key)
                DO UPDATE SET label = EXCLUDED.label, attrs = EXCLUDED.attrs
                RETURNING id, type, key, label, attrs
                """,
                (node_id, type, key, label, json.dumps(attrs or {})),
            )
            row = cur.fetchone()
        return Node(row["id"], row["type"], row["key"], row["label"], row["attrs"])

    def upsert_edge(self, src_id: str, dst_id: str, type: str, attrs: dict | None = None) -> None:
        """Idempotent on (src, dst, type): re-loading a rule updates its payload in place."""
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO edges (id, src_id, dst_id, type, attrs)
                VALUES (%s, %s, %s, %s, %s::jsonb)
                ON CONFLICT (src_id, dst_id, type)
                DO UPDATE SET attrs = EXCLUDED.attrs
                """,
                (str(uuid.uuid4()), src_id, dst_id, type, json.dumps(attrs or {})),
            )

    def get_node(self, type: str, key: str) -> Optional[Node]:
        with cursor() as cur:
            cur.execute("SELECT * FROM nodes WHERE type=%s AND key=%s", (type, key))
            row = cur.fetchone()
        return Node(row["id"], row["type"], row["key"], row["label"], row["attrs"]) if row else None

    def neighbors(self, src_id: str, edge_type: str) -> list[tuple[Edge, Node]]:
        """One hop: all (edge, destination node) out of src_id along edge_type."""
        with cursor() as cur:
            cur.execute(
                """
                SELECT e.src_id, e.dst_id, e.type AS etype, e.attrs AS eattrs,
                       n.id, n.type, n.key, n.label, n.attrs AS nattrs
                FROM edges e JOIN nodes n ON n.id = e.dst_id
                WHERE e.src_id = %s AND e.type = %s
                """,
                (src_id, edge_type),
            )
            rows = cur.fetchall()
        out = []
        for r in rows:
            edge = Edge(r["src_id"], r["dst_id"], r["etype"], r["eattrs"])
            node = Node(r["id"], r["type"], r["key"], r["label"], r["nattrs"])
            out.append((edge, node))
        return out
