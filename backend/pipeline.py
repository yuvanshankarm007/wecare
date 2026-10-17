"""End-to-end pipeline: extract → detect conflicts → Q&A → escalate.

Usage:
    python -m backend.pipeline --all
    python -m backend.pipeline --question "What dose of metformin am I on?"
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .extract import extract_all
from .conflict_engine import detect_conflicts, diff_visits
from .qa import answer
from .escalation import enqueue

DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def run_all() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    extractions = extract_all()
    conflicts = detect_conflicts(extractions)
    diff = diff_visits(extractions)

    (DATA_DIR / "extractions.json").write_text(
        json.dumps([e.model_dump() for e in extractions], indent=2)
    )
    (DATA_DIR / "conflicts.json").write_text(
        json.dumps([c.model_dump() for c in conflicts], indent=2)
    )
    (DATA_DIR / "diff.json").write_text(json.dumps(diff, indent=2))

    return {"extractions": extractions, "conflicts": conflicts, "diff": diff}


def ask(question: str) -> dict:
    state = run_all()
    resp = answer(question, state["extractions"], state["conflicts"])
    if resp.escalate:
        enqueue(resp)
    return resp.model_dump()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--question", type=str, default=None)
    args = parser.parse_args()

    if args.question:
        print(json.dumps(ask(args.question), indent=2))
        return

    state = run_all()
    print(f"Documents: {len(state['extractions'])}")
    print(f"Conflicts: {len(state['conflicts'])}")
    for c in state["conflicts"]:
        print(f"  [{c.severity}] {c.kind}: {c.description}")
    print(f"Diff rows: {len(state['diff'])}")


if __name__ == "__main__":
    main()