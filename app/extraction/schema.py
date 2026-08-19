"""The typed shape we force the LLM to produce. Extraction is only trustworthy if
its output is validated against a strict schema before anything downstream sees it."""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

Cadence = Literal["one_time", "annual", "biennial", "quarterly", "monthly"]


class RequirementRecord(BaseModel):
    """One extracted obligation. Maps 1:1 to a requirement node + its edges."""
    state: str = Field(..., description="two-letter state code, e.g. CA")
    license_type: str = Field(..., description="the license this requirement attaches to")
    requirement: str = Field(..., description="the obligation, e.g. 'Annual Report'")
    cadence: Cadence
    interval_months: Optional[int] = Field(
        None, description="months between filings; null for one_time"
    )
    depends_on: Optional[str] = Field(
        None, description="a requirement that must be filed first, if any"
    )
    source_page: Optional[int] = Field(None, description="page in the source doc")

    @field_validator("state")
    @classmethod
    def _upper_two(cls, v: str) -> str:
        v = v.strip().upper()
        if len(v) != 2:
            raise ValueError("state must be a two-letter code")
        return v


class ExtractionResult(BaseModel):
    requirements: list[RequirementRecord]
