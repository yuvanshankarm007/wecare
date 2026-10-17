"""Deterministic cross-document conflict detection.

This is WeCare's wedge: it works even when the LLM does not, and it is the
feature no other healthcare submission in the gallery has.
"""
from __future__ import annotations

import re
from .schemas import Conflict, DocumentExtraction

NSAIDS = {"ibuprofen", "aspirin", "naproxen", "diclofenac", "ketorolac"}
ANTICOAGULANTS = {"warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban"}

INTERACTION_RULES = [
    (ANTICOAGULANTS, NSAIDS, "HIGH", "Bleeding risk: anticoagulant + NSAID"),
]


def parse_dose_mg(dose: str | None) -> float | None:
    if not dose:
        return None
    s = dose.lower().replace(",", ".")
    m = re.search(r"([\d.]+)\s*(mg|mcg|g)\b", s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2)
    if unit == "g":
        return val * 1000
    if unit == "mcg":
        return val / 1000
    return val


def _fmt_mg(v: float) -> str:
    return f"{v:g} mg"


def detect_conflicts(extractions: list[DocumentExtraction]) -> list[Conflict]:
    conflicts: list[Conflict] = []

    # ---- 1. Dose mismatches across documents ------------------------------
    by_drug: dict[str, list[tuple[str, str, int]]] = {}
    for e in extractions:
        for m in e.medications:
            key = m.name.lower().strip()
            by_drug.setdefault(key, []).append((e.document_id, m.dose or "", m.source_line))

    for drug, mentions in by_drug.items():
        per_doc: dict[str, tuple[float | None, int]] = {}
        for doc_id, dose, line in mentions:
            per_doc[doc_id] = (parse_dose_mg(dose), line)
        mg_values = {v for v, _ in per_doc.values() if v is not None}
        if len(mg_values) > 1:
            doc_a, doc_b = list(per_doc.keys())[:2]
            parts = []
            for doc_id, (mg, _) in per_doc.items():
                if mg is not None:
                    parts.append(f"{_fmt_mg(mg)} in {doc_id}")
            conflicts.append(Conflict(
                kind="dose_mismatch",
                severity="HIGH",
                description=f"{drug.title()} dose differs: " + " vs ".join(parts),
                source_doc_a=doc_a,
                source_doc_b=doc_b,
                source_lines=[ln for _, ln in per_doc.values()],
            ))

    # ---- 2. Buried allergies (present in one doc, missing in another) -----
    allergy_docs: dict[str, list[tuple[str, int, str]]] = {}
    for e in extractions:
        for a in e.allergies:
            allergy_docs.setdefault(a.substance.lower(), []).append(
                (e.document_id, a.source_line, a.substance)
            )
    for substance, items in allergy_docs.items():
        present_in = {d for d, _, _ in items}
        missing_in = [e.document_id for e in extractions if e.document_id not in present_in]
        if missing_in:
            conflicts.append(Conflict(
                kind="buried_allergy",
                severity="HIGH",
                description=(
                    f"Allergy to {substance.title()} appears in "
                    f"{', '.join(sorted(present_in))} but is missing from "
                    f"{', '.join(missing_in)}"
                ),
                source_doc_a=sorted(present_in)[0],
                source_doc_b=missing_in[0],
                source_lines=[ln for _, ln, _ in items],
            ))

    # ---- 3. Drug interaction rules ----------------------------------------
    present = {m.name.lower() for e in extractions for m in e.medications}
    for group_a, group_b, severity, msg in INTERACTION_RULES:
        hit_a = group_a & present
        hit_b = group_b & present
        if hit_a and hit_b:
            conflicts.append(Conflict(
                kind="drug_interaction",
                severity=severity,
                description=f"{msg}: {', '.join(sorted(hit_a))} + {', '.join(sorted(hit_b))}",
            ))

    # ---- 4. Unclear / illegible lines -------------------------------------
    for e in extractions:
        for ln in e.unclear_lines:
            text = e.raw_lines[ln - 1] if 0 < ln <= len(e.raw_lines) else ""
            conflicts.append(Conflict(
                kind="unclear_line",
                severity="MEDIUM",
                description=f'Unclear instruction in {e.document_id}: "{text}"',
                source_doc_a=e.document_id,
                source_lines=[ln],
            ))

    return conflicts


# ---------------------------------------------------------------------------
# "What changed?" diff between two visits
# ---------------------------------------------------------------------------
def diff_visits(extractions: list[DocumentExtraction]) -> list[dict]:
    ordered = sorted(
        [e for e in extractions if e.visit_date],
        key=lambda e: e.visit_date,  # type: ignore[arg-type]
    )
    if len(ordered) < 2:
        return []
    first, last = ordered[0], ordered[-1]

    def med_map(e: DocumentExtraction) -> dict[str, str]:
        return {m.name.lower(): (m.dose or "?") for m in e.medications}

    a, b = med_map(first), med_map(last)
    rows = []
    for name in sorted(set(a) | set(b)):
        before, after = a.get(name, "—"), b.get(name, "—")
        if before != after:
            rows.append({"drug": name.title(), "before": before, "after": after})
    return rows