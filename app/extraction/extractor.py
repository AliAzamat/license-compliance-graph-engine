"""Call the model, then VALIDATE. An extraction that doesn't parse against the
schema is dropped, not loaded — bad data must never reach the graph."""
from __future__ import annotations

import json
import os

from openai import OpenAI
from pydantic import ValidationError

from app.extraction.schema import ExtractionResult
from app.extraction.prompt import SYSTEM, user_prompt

_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
MODEL = "gpt-4o"


def extract(state_hint: str, document_text: str) -> ExtractionResult:
    """Returns validated records. On any parse/validation failure, returns an
    empty result rather than propagating unvalidated data downstream."""
    resp = _client.chat.completions.create(
        model=MODEL,
        temperature=0,  # deterministic extraction: same doc -> same records
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user_prompt(state_hint, document_text)},
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
        return ExtractionResult.model_validate(data)
    except (json.JSONDecodeError, ValidationError):
        # Fail closed: never let malformed extraction become graph edges.
        return ExtractionResult(requirements=[])
