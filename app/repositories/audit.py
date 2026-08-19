from __future__ import annotations

import json
import uuid
from typing import Any

from app.db.postgres import cursor


class AuditRepo:
    def record(
        self, *, entity_key: str, request: dict[str, Any],
        facts: list[dict[str, Any]], response: dict[str, Any], grounded_ratio: float,
    ) -> str:
        """Append-only: insert a row, never update. The audit trail is immutable."""
        audit_id = str(uuid.uuid4())
        with cursor() as cur:
            cur.execute(
                """
                INSERT INTO audit_log (id, entity_key, request, facts, response, grounded_ratio)
                VALUES (%s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s)
                """,
                (audit_id, entity_key, json.dumps(request),
                 json.dumps(facts), json.dumps(response), grounded_ratio),
            )
        return audit_id
