"""Chat wrapper. Temperature 0 + JSON-only keeps the checklist deterministic and
parseable; a parse failure fails soft to an empty checklist, never a 500."""
from __future__ import annotations

import json
import os
from typing import Any

from openai import OpenAI

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"


def complete_json(system: str, user: str) -> dict[str, Any]:
    resp = _client.chat.completions.create(
        model=MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    try:
        return json.loads(resp.choices[0].message.content or "{}")
    except json.JSONDecodeError:
        return {"summary": "Could not draft the checklist.", "items": []}
