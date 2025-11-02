import time
import json
from pathlib import Path
import fitz  # PyMuPDF

from store.db import set_status
from services.embedding import build_faiss_index  # new import

# Directory setup
RAW_DIR = Path("data/raw")
CORPUS_DIR = Path("data/corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


# ----------- 1️⃣ PDF Text Extraction ----------- #
def extract_text_pymupdf(pdf_path: Path):
    """Extract page-wise text using PyMuPDF."""
    doc = fitz.open(pdf_path)
    pages = []
    for i, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            pages.append({"page_num": i + 1, "text": text})
    doc.close()
    return pages


# ----------- 2️⃣ Section Detection ----------- #
def detect_sections(text: str) -> str:
    """Heuristic rule-based section tagger based on keywords."""
    t = text.lower()
    if "risk" in t and "factor" in t:
        return "Risk Factors"
    elif "management discussion" in t or "analysis" in t:
        return "MD&A"
    elif "business overview" in t or "our business" in t:
        return "Business"
    elif "financial statements" in t:
        return "Financial Statements"
    elif "legal" in t and "proceeding" in t:
        return "Legal"
    elif "object" in t and "issue" in t:
        return "Objects of the Issue"
    elif "promoter" in t:
        return "Promoters"
    else:
        return "General"


# ----------- 3️⃣ Sectionize Pages ----------- #
def sectionize(pages: list[dict]) -> list[dict]:
    """Assign each page to a section and aggregate text."""
    sections = {}
    current_section = "General"
    for p in pages:
        section_guess = detect_sections(p["text"])
        if section_guess != current_section:
            current_section = section_guess
        sections.setdefault(current_section, "")
        sections[current_section] += "\n" + p["text"]

    result = []
    for name, text in sections.items():
        result.append({"section": name, "text": text.strip()})
    return result


# ----------- 4️⃣ Full Pipeline ----------- #
def process_pipeline(file_id: str):
    """
    Background task:
    PDF → Extract text → Sectionize → Chunk + Embed → FAISS
    """
    pdf_path = RAW_DIR / f"{file_id}.pdf"
    set_status(file_id, "parsing")

    try:
        # 1. Extract text
        pages = extract_text_pymupdf(pdf_path)

        # 2. Detect and merge sections
        sections = sectionize(pages)

        # 3. Save to corpus as JSONL
        out_path = CORPUS_DIR / f"{file_id}.jsonl"
        with open(out_path, "w", encoding="utf-8") as f:
            for s in sections:
                f.write(json.dumps(s) + "\n")

        # 4. Build FAISS index
        set_status(file_id, "embedding")
        total_chunks = build_faiss_index(file_id)
        print(f"✅ Built FAISS index with {total_chunks} chunks for {file_id}")

        # 5. Done
        set_status(file_id, "done")

    except Exception as e:
        print("❌ Error in pipeline:", e)
        set_status(file_id, "error")
