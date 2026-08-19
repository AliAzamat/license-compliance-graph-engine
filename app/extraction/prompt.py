"""The extraction prompt. It pins the model to the schema, forbids invention, and
demands an empty list rather than a guess when the document is silent."""

SYSTEM = """You extract regulated-licensing requirements from U.S. state
regulator documents into structured records.

Rules:
- Extract ONLY obligations the document actually states. Never infer or invent.
- If the document does not state a requirement, do not produce a record for it.
- cadence must be one of: one_time, annual, biennial, quarterly, monthly.
- interval_months: 12 for annual, 24 for biennial, 3 for quarterly, 1 for
  monthly, null for one_time.
- depends_on: only if the text explicitly orders one filing before another.
- Record source_page when the document is paginated.

Return ONLY valid JSON matching:
{"requirements": [
  {"state": str, "license_type": str, "requirement": str,
   "cadence": str, "interval_months": int|null,
   "depends_on": str|null, "source_page": int|null}
]}"""


def user_prompt(state_hint: str, document_text: str) -> str:
    return (
        f"State (hint, verify against the text): {state_hint}\n\n"
        f"Document:\n{document_text}"
    )
