"""Doctor queue: every escalated question becomes a pending review item."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from .schemas import QAResponse

QUEUE_PATH = Path(__file__).resolve().parent.parent / "data" / "doctor_queue.json"


def enqueue(resp: QAResponse, draft_reply: str | None = None) -> dict:
    QUEUE_PATH.parent.mkdir(exist_ok=True)
    queue = []
    if QUEUE_PATH.exists():
        queue = json.loads(QUEUE_PATH.read_text())
    item = {
        "id": f"esc_{len(queue) + 1:03d}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "patient_question": resp.question,
        "ai_draft_reply": draft_reply or resp.answer_text,
        "confidence": resp.confidence,
        "reason": resp.reason,
        "citations": [c.model_dump() for c in resp.citations],
        "status": "pending_review",
    }
    queue.append(item)
    QUEUE_PATH.write_text(json.dumps(queue, indent=2))
    return item


def load_queue() -> list[dict]:
    if not QUEUE_PATH.exists():
        return []
    return json.loads(QUEUE_PATH.read_text())