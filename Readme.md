# WeCare — Ask Your Medical Records, Safely

**Multi-document patient Q&A with strict citations, cross-document conflict detection, and clinician escalation. Built for the AMD Developer Hackathon ACT III — Track 2 (Health & Wellbeing).**

> Other healthcare projects in this hackathon translate **one** document into a static sheet.
> WeCare starts where they stop: it lets the patient **ask the next question** across **every**
> record, cites every claim, flags contradictions **between** documents before they become a
> dose error, and escalates uncertainty to a clinician with an AI-drafted reply.

---

## Why WeCare is different

| | Static translators (ClearCare, Clearsheet, DischargeDost) | BridgeCare (nurse tool) | **WeCare** |
|---|---|---|---|
| Input | Single document | Single discharge summary | **Multiple documents across visits** |
| Output | Static plain-language sheet | Static nurse draft | **Interactive Q&A** |
| Citations | Sometimes | Yes (within doc) | **Yes, line-level, every answer** |
| Conflict detection | Within one document | Within one document | **Across documents (dose, buried allergy)** |
| Uncertainty | Static apology | Blocked contradictions | **Confidence gating + escalation queue** |
| Audience | Patient | Nurse | **Patient + clinician loop** |

---

## Architecture

Built solo. AI coding assistants were used for scaffolding and code review; all product decisions, safety architecture, and the design are the author's.