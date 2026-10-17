from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field


class Medication(BaseModel):
    name: str
    dose: Optional[str] = None
    frequency: Optional[str] = None
    source_line: int


class Allergy(BaseModel):
    substance: str
    reaction: Optional[str] = None
    source_line: int


class DocumentExtraction(BaseModel):
    document_id: str
    document_type: str
    visit_date: Optional[str] = None
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[Allergy] = Field(default_factory=list)
    instructions: list[str] = Field(default_factory=list)
    unclear_lines: list[int] = Field(default_factory=list)
    raw_lines: list[str] = Field(default_factory=list)


class Conflict(BaseModel):
    kind: Literal[
        "dose_mismatch",
        "buried_allergy",
        "missing_in_summary",
        "unclear_line",
        "drug_interaction",
    ]
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    description: str
    source_doc_a: Optional[str] = None
    source_doc_b: Optional[str] = None
    source_lines: list[int] = Field(default_factory=list)


class Citation(BaseModel):
    document_id: str
    line_number: int
    verbatim_quote: str


class QAResponse(BaseModel):
    question: str
    answer_text: str
    citations: list[Citation] = Field(default_factory=list)
    confidence: float
    escalate: bool
    reason: Optional[str] = None