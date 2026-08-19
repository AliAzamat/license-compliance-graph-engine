from __future__ import annotations

from datetime import date

from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.checklist_agent import draft_checklist
from app.agent.grounding import verify_grounded
from app.repositories.audit import AuditRepo

router = APIRouter(prefix="/compliance", tags=["compliance"])
audit = AuditRepo()


class ChecklistRequest(BaseModel):
    entity_key: str
    last_filed: dict[str, str] = {}  # requirement_id -> ISO date


@router.post("/checklist")
def checklist(body: ChecklistRequest):
    # Parse ISO dates into date objects for the renewal engine.
    last_filed = {k: date.fromisoformat(v) for k, v in body.last_filed.items()}

    drafted = draft_checklist(body.entity_key, last_filed)
    verified = verify_grounded(drafted)

    audit_id = audit.record(
        entity_key=body.entity_key,
        request={"entity_key": body.entity_key, "last_filed": body.last_filed},
        facts=drafted.get("_facts", []),
        response=verified,
        grounded_ratio=verified["grounded_ratio"],
    )
    return {"audit_id": audit_id, **verified}
