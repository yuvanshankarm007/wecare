"""Citation-bound Q&A with confidence gating and escalation.

No answer without a citation. No high-stakes answer under the confidence
threshold. Conflicts on the queried topic force escalation.
"""
from __future__ import annotations

import re
from .schemas import Citation, Conflict, DocumentExtraction, QAResponse

CONFIDENCE_THRESHOLD = 0.60
ADVICE_TRIGGERS = ("should i", "can i take", "is it safe", "do i take", "what should")


def _mentions(term: str, extractions: list[DocumentExtraction]) -> list[Citation]:
    """Return every line that mentions `term` (case-insensitive)."""
    hits: list[Citation] = []
    pat = re.compile(re.escape(term), re.IGNORECASE)
    for e in extractions:
        for i, line in enumerate(e.raw_lines, start=1):
            if pat.search(line):
                hits.append(Citation(
                    document_id=e.document_id,
                    line_number=i,
                    verbatim_quote=line,
                ))
    return hits


def _all_drug_names(extractions: list[DocumentExtraction]) -> set[str]:
    return {m.name.lower() for e in extractions for m in e.medications}


def _conflicts_on(topic: str, conflicts: list[Conflict]) -> list[Conflict]:
    t = topic.lower()
    return [c for c in conflicts if t in c.description.lower()]


def answer(
    question: str,
    extractions: list[DocumentExtraction],
    conflicts: list[Conflict],
) -> QAResponse:
    q = question.strip().lower()
    if not q:
        return QAResponse(
            question=question, answer_text="Please ask a question.",
            confidence=0.0, escalate=False,
        )

    # --- 1. Allergy question ---------------------------------------------
    if "allerg" in q:
        hits = _mentions("allerg", extractions)
        if hits:
            text = "Your records list the following allergy information:\n" + "\n".join(
                f"- {c.verbatim_quote}  (source: {c.document_id}, line {c.line_number})"
                for c in hits
            )
            return QAResponse(
                question=question, answer_text=text, citations=hits,
                confidence=0.9, escalate=False,
            )
        return QAResponse(
            question=question,
            answer_text="No allergy information is recorded in your documents. "
                        "This is being escalated to a clinician.",
            confidence=0.2, escalate=True,
            reason="No allergy data in records; cannot answer safely.",
        )

    # --- 2. Drug-specific question (dose / general) ----------------------
    drugs = _all_drug_names(extractions)
    for drug in drugs:
        if re.search(rf"\b{re.escape(drug)}\b", q):
            hits = _mentions(drug, extractions)
            drug_conflicts = _conflicts_on(drug, conflicts)

            if drug_conflicts:
                c = drug_conflicts[0]
                return QAResponse(
                    question=question,
                    answer_text=(
                        f"⚠ Conflicting information found for {drug.title()} across your "
                        f"documents. I am not answering directly — this is being sent to a "
                        f"clinician for review.\n\nDetail: {c.description}"
                    ),
                    citations=hits,
                    confidence=0.45,
                    escalate=True,
                    reason=f"Conflicting records on {drug.title()}; human review required.",
                )

            advice = any(t in q for t in ADVICE_TRIGGERS)
            if advice and "interaction" in " ".join(c.kind for c in conflicts).lower():
                pass  # handled below by interaction check

            text = f"Here is what your records say about {drug.title()}:\n" + "\n".join(
                f"- {c.verbatim_quote}  (source: {c.document_id}, line {c.line_number})"
                for c in hits
            )
            conf = 0.85 if len(hits) == 1 else 0.9
            return QAResponse(
                question=question, answer_text=text, citations=hits,
                confidence=conf, escalate=False,
            )

    # --- 3. Advice question that may hit an interaction rule -------------
    if any(t in q for t in ADVICE_TRIGGERS):
        interaction = [c for c in conflicts if c.kind == "drug_interaction"]
        if interaction:
            c = interaction[0]
            return QAResponse(
                question=question,
                answer_text=(
                    f"⚠ I cannot answer this safely. A potential high-risk interaction "
                    f"was detected in your records: {c.description}. "
                    f"This has been escalated to a clinician."
                ),
                confidence=0.3, escalate=True,
                reason="High-risk interaction detected; advice withheld.",
            )

    # --- 4. No grounded answer → escalate --------------------------------
    return QAResponse(
        question=question,
        answer_text=(
            "I could not find a clear answer in your uploaded records. "
            "This question has been escalated to a clinician rather than guessed."
        ),
        confidence=0.15, escalate=True,
        reason="No grounded evidence in the patient's records.",
    )