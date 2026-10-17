"""Extraction: mock mode (no network) or live OpenAI-compatible endpoint.

Usage:
    python -m backend.extract --all
"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .schemas import DocumentExtraction, Medication, Allergy
from .synthetic_docs import ALL_DOCS


# ---------------------------------------------------------------------------
# Mock extraction (ground truth for the demo; deterministic, always works)
# ---------------------------------------------------------------------------
MOCK_EXTRACTION: dict[str, dict[str, Any]] = {
    "doc1_discharge_2024_10_01": {
        "medications": [
            {"name": "Metformin", "dose": "500 mg", "frequency": "twice daily", "source_line": 5},
            {"name": "Ibuprofen", "dose": "400 mg", "frequency": "as needed", "source_line": 6},
        ],
        "allergies": [],
        "instructions": ["Follow-up in 2 weeks."],
        "unclear_lines": [],
    },
    "doc2_consult_2024_10_05": {
        "medications": [
            {"name": "Metformin", "dose": "1 g", "frequency": "twice daily", "source_line": 5},
        ],
        "allergies": [
            {"substance": "Penicillin", "reaction": "rash", "source_line": 3},
        ],
        "instructions": [],
        "unclear_lines": [],
    },
    "doc3_discharge_2024_10_10": {
        "medications": [
            {"name": "Warfarin", "dose": "5 mg", "frequency": "once daily", "source_line": 5},
            {"name": "Metformin", "dose": "1000 mg", "frequency": "twice daily", "source_line": 6},
        ],
        "allergies": [],
        "instructions": ["INR monitoring weekly."],
        "unclear_lines": [7],
    },
}


def _from_mock(doc: dict) -> DocumentExtraction:
    payload = MOCK_EXTRACTION[doc["document_id"]]
    return DocumentExtraction(
        document_id=doc["document_id"],
        document_type=doc["document_type"],
        visit_date=doc["visit_date"],
        medications=[Medication(**m) for m in payload["medications"]],
        allergies=[Allergy(**a) for a in payload["allergies"]],
        instructions=payload["instructions"],
        unclear_lines=payload["unclear_lines"],
        raw_lines=doc["lines"],
    )


# ---------------------------------------------------------------------------
# Live extraction via any OpenAI-compatible endpoint
# ---------------------------------------------------------------------------
EXTRACTION_PROMPT = """You extract structured clinical data from a single document.

Return ONLY valid JSON matching this schema:
{
  "medications": [{"name": str, "dose": str|null, "frequency": str|null, "source_line": int}],
  "allergies":   [{"substance": str, "reaction": str|null, "source_line": int}],
  "instructions": [str],
  "unclear_lines": [int]
}

Rules:
- source_line is the 1-indexed line number in the input.
- If a line is illegible or ambiguous, add its line number to unclear_lines.
- Never invent medications or allergies not present in the text.
- If nothing is found, return empty arrays.

Document (line numbers in brackets):
{document}
"""


def _from_llm(doc: dict) -> DocumentExtraction:
    from openai import OpenAI  # imported lazily so mock mode never needs it

    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ.get("OPENAI_BASE_URL") or None,
    )
    numbered = "\n".join(f"[{i+1}] {ln}" for i, ln in enumerate(doc["lines"]))
    resp = client.chat.completions.create(
        model=os.environ["OPENAI_MODEL"],
        messages=[
            {"role": "system", "content": "You are a precise clinical information extractor."},
            {"role": "user", "content": EXTRACTION_PROMPT.format(document=numbered)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    data = json.loads(resp.choices[0].message.content)
    return DocumentExtraction(
        document_id=doc["document_id"],
        document_type=doc["document_type"],
        visit_date=doc["visit_date"],
        medications=[Medication(**m) for m in data.get("medications", [])],
        allergies=[Allergy(**a) for a in data.get("allergies", [])],
        instructions=data.get("instructions", []),
        unclear_lines=data.get("unclear_lines", []),
        raw_lines=doc["lines"],
    )


def extract_document(doc: dict) -> DocumentExtraction:
    if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_MODEL"):
        return _from_llm(doc)
    return _from_mock(doc)


def extract_all() -> list[DocumentExtraction]:
    return [extract_document(d) for d in ALL_DOCS]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true", help="extract all documents")
    args = parser.parse_args()
    if not args.all:
        parser.print_help()
        return
    extractions = extract_all()
    for e in extractions:
        print(f"\n=== {e.document_id} ({e.document_type}, {e.visit_date}) ===")
        print(json.dumps(e.model_dump(exclude={"raw_lines"}), indent=2))


if __name__ == "__main__":
    main()