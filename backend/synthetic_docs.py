"""Three synthetic documents for SYNTHETIC PATIENT A. Not a real person."""

ALL_DOCS = [
    {
        "document_id": "doc1_discharge_2024_10_01",
        "document_type": "Discharge Summary",
        "visit_date": "2024-10-01",
        "lines": [
            "DISCHARGE SUMMARY — visit 2024-10-01",
            "SYNTHETIC PATIENT A — not a real person",
            "Diagnosis: Type 2 diabetes mellitus",
            "Medications:",
            "1. Metformin 500 mg twice daily after meals",
            "2. Ibuprofen 400 mg as needed for pain",
            "Follow-up in 2 weeks.",
        ],
    },
    {
        "document_id": "doc2_consult_2024_10_05",
        "document_type": "Consultation Note",
        "visit_date": "2024-10-05",
        "lines": [
            "CONSULTATION NOTE — 2024-10-05",
            "SYNTHETIC PATIENT A — not a real person",
            "Allergies: Penicillin — rash",
            "Current medications:",
            "Metformin 1 g twice daily",
            "Patient reports good adherence.",
        ],
    },
    {
        "document_id": "doc3_discharge_2024_10_10",
        "document_type": "Discharge Summary",
        "visit_date": "2024-10-10",
        "lines": [
            "DISCHARGE SUMMARY — visit 2024-10-10",
            "SYNTHETIC PATIENT A — not a real person",
            "Diagnosis: Atrial fibrillation, Type 2 diabetes",
            "Medications:",
            "1. Warfarin 5 mg once daily",
            "2. Metformin 1000 mg twice daily",
            "3. Continue [illegible] 5 mg daily",
            "INR monitoring weekly.",
        ],
    },
]