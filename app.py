"""WeCare — Streamlit demo.

Run: streamlit run app.py
"""
from __future__ import annotations

import json
import streamlit as st

from backend.pipeline import run_all, ask
from backend.escalation import load_queue

st.set_page_config(page_title="WeCare", page_icon="🩺", layout="wide")

st.markdown(
    """
    <div style="background:#fff3cd;padding:8px 14px;border-radius:6px;
                border-left:5px solid #b8860b;margin-bottom:16px;">
    <b>SYNTHETIC DATA — NOT A REAL PATIENT.</b> Decision support only, not diagnosis.
    Every answer is citation-bound; uncertain questions are escalated to a clinician.
    </div>
    """,
    unsafe_allow_html=True,
)

st.title("🩺 WeCare")
st.caption("Ask your medical records, safely — across every document, with citations.")

# ---- Run pipeline once per session ----
if "state" not in st.session_state:
    st.session_state.state = run_all()
state = st.session_state.state

tab_docs, tab_conf, tab_ask, tab_queue, tab_diff = st.tabs(
    ["📄 Documents", "⚠️ Conflicts & Red Flags", "💬 Ask", "🧑‍⚕️ Doctor Queue", "🔀 What Changed?"]
)

with tab_docs:
    st.subheader("Source documents")
    for e in state["extractions"]:
        with st.expander(f"{e.document_id} — {e.document_type} ({e.visit_date})"):
            for i, line in enumerate(e.raw_lines, start=1):
                flag = " ⚠️" if i in e.unclear_lines else ""
                st.markdown(f"`{i:02d}` {line}{flag}")
            st.markdown("**Extracted**")
            st.json(e.model_dump(exclude={"raw_lines"}), expanded=False)

with tab_conf:
    st.subheader("Cross-document conflicts")
    if not state["conflicts"]:
        st.success("No conflicts detected.")
    for c in state["conflicts"]:
        color = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟡"}[c.severity]
        with st.container(border=True):
            st.markdown(f"{color} **{c.severity} — {c.kind}**")
            st.write(c.description)
            if c.source_doc_a:
                st.caption(f"Sources: {c.source_doc_a} / {c.source_doc_b or '—'}; lines {c.source_lines}")

with tab_ask:
    st.subheader("Ask a question about your records")
    preset = st.selectbox(
        "Try a question",
        [
            "What dose of metformin am I on?",
            "Am I allergic to anything?",
            "Can I take ibuprofen?",
            "What is my INR target?",
        ],
    )
    q = st.text_input("Or type your own:", value=preset)
    if st.button("Ask WeCare", type="primary") and q:
        resp = ask(q)
        st.markdown(f"### Answer\n{resp['answer_text']}")
        col1, col2 = st.columns(2)
        col1.metric("Confidence", f"{resp['confidence']:.2f}")
        col2.metric("Escalated", "YES" if resp["escalate"] else "No")
        if resp["citations"]:
            st.markdown("**Citations**")
            for c in resp["citations"]:
                st.markdown(
                    f"- `{c['document_id']}` line {c['line_number']}: "
                    f"> {c['verbatim_quote']}"
                )
        if resp["escalate"]:
            st.warning(f"Escalated to clinician — {resp['reason']}")

with tab_queue:
    st.subheader("Clinician review queue")
    queue = load_queue()
    if not queue:
        st.info("No escalations yet. Ask an unanswerable question in the Ask tab.")
    for item in queue:
        with st.container(border=True):
            st.markdown(f"**{item['id']}** — `{item['status']}`")
            st.markdown(f"**Patient asked:** {item['patient_question']}")
            st.markdown(f"**AI draft:** {item['ai_draft_reply']}")
            st.caption(f"Confidence {item['confidence']:.2f} — {item['reason']}")

with tab_diff:
    st.subheader("What changed between visits?")
    if not state["diff"]:
        st.info("Not enough visits to diff.")
    else:
        st.table(state["diff"])

st.divider()
st.caption(
    "WeCare · AMD Developer Hackathon ACT III · Track 2 (Health & Wellbeing) · "
    "Pipeline runs on any OpenAI-compatible endpoint; target deployment is vLLM on AMD Instinct / Fireworks on AMD GPUs."
)