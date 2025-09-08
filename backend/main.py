from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, uuid, json, re
from typing import List, Dict, Any

from nlp.extract_text import extract_text_from_pdf
from nlp.chunking import chunk_pages
from nlp.embeddings import EmbeddingStore
from nlp.summarize import HierarchicalSummarizer
from nlp.rag import RAGAnswerer
from nlp.utils import ensure_dir
from nlp.metrics import extract_metrics_from_text  # regex-based extraction

# ----- paths & app -----
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.environ.get("DATA_DIR", "/data")  # writable on HF Spaces
ensure_dir(DATA_DIR)

ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000"
).split(",")

app = FastAPI(title="IPO Prospectus Reader API", version="1.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in ALLOWED_ORIGINS if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ----- singletons -----
_summarizer = None

# ----- models -----
class UploadResponse(BaseModel):
    doc_id: str
    pages: int
    chunks: int

class SummarizeRequest(BaseModel):
    doc_id: str
    max_words: int = 300

class AskRequest(BaseModel):
    doc_id: str
    question: str
    top_k: int = 5
    max_words: int = 200

class ExtractRequest(BaseModel):
    doc_id: str

class CompareRequest(BaseModel):
    doc_id_a: str
    doc_id_b: str

# ----- health -----
@app.get("/health")
def health():
    return {"status": "ok"}

# ----- helpers -----
def _find_page_for_snippet(pages_text: List[str], snippet: str) -> int | None:
    """Naively map a snippet back to the first page containing its first ~120 chars."""
    needle = re.sub(r"\s+", " ", snippet[:120]).strip()
    for i, page in enumerate(pages_text, start=1):
        hay = re.sub(r"\s+", " ", page)
        if needle and needle in hay:
            return i
    return None

def _extract_metrics_from_doc_dir(doc_dir: str) -> Dict[str, str]:
    """Extract metrics by reading the persisted text for a given doc_dir."""
    if not os.path.isdir(doc_dir):
        return {"error": "doc not found"}  # type: ignore
    chunks_path = os.path.join(doc_dir, "chunks.json")
    pages_path = os.path.join(doc_dir, "pages.json")
    text = ""

    if os.path.exists(pages_path):
        with open(pages_path, "r", encoding="utf-8") as f:
            text = "\n\n".join(json.load(f))
    elif os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            texts = [c["text"] if isinstance(c, dict) else str(c) for c in chunks]
            text = "\n\n".join(texts)

    return extract_metrics_from_text(text)

# ----- routes -----
@app.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    doc_id = str(uuid.uuid4())
    doc_dir = os.path.join(DATA_DIR, doc_id)
    ensure_dir(doc_dir)

    # save PDF
    pdf_path = os.path.join(doc_dir, file.filename)
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # per-page text (OCR fallback inside)
    pages_text: List[str] = extract_text_from_pdf(pdf_path)

    # persist raw text
    with open(os.path.join(doc_dir, "pages.json"), "w", encoding="utf-8") as f:
        json.dump(pages_text, f, ensure_ascii=False)

    # page-aware chunking WITH metadata (e.g., {"text": ..., "page": ...})
    chunks_with_meta: List[Dict[str, Any]] = chunk_pages(pages_text)
    with open(os.path.join(doc_dir, "chunks.json"), "w", encoding="utf-8") as f:
        json.dump(chunks_with_meta, f, ensure_ascii=False)

    # embeddings + FAISS
    store = EmbeddingStore.load_or_create(doc_dir)
    store.index_chunks(chunks_with_meta)
    store.save()

    return UploadResponse(doc_id=doc_id, pages=len(pages_text), chunks=len(chunks_with_meta))

@app.post("/summarize")
def summarize(req: SummarizeRequest):
    global _summarizer
    doc_dir = os.path.join(DATA_DIR, req.doc_id)
    if not os.path.isdir(doc_dir):
        return {"error": "doc_id not found"}

    with open(os.path.join(doc_dir, "chunks.json"), "r", encoding="utf-8") as f:
        chunks = json.load(f)  # list[dict]

    if _summarizer is None:
        _summarizer = HierarchicalSummarizer()

    texts = [c["text"] for c in chunks]
    summary = _summarizer.hierarchical_summarize(texts, target_words=req.max_words)

    with open(os.path.join(doc_dir, "summary.txt"), "w", encoding="utf-8") as f:
        f.write(summary)

    return {"doc_id": req.doc_id, "summary": summary}

@app.post("/ask")
def ask(req: AskRequest):
    doc_dir = os.path.join(DATA_DIR, req.doc_id)
    if not os.path.isdir(doc_dir):
        return {"error": "doc_id not found"}

    # search relevant chunks
    store = EmbeddingStore.load_or_create(doc_dir)
    results = store.search(req.question, top_k=req.top_k)

    passages = [r["text"] for r in results]
    scores   = [float(r["score"]) for r in results]

    # compute page numbers by scanning pages.json
    pages_text: List[str] = []
    pages_path = os.path.join(doc_dir, "pages.json")
    if os.path.exists(pages_path):
        with open(pages_path, "r", encoding="utf-8") as f:
            pages_text = json.load(f)

    sources = []
    for txt, s in zip(passages, scores):
        page_no = _find_page_for_snippet(pages_text, txt) if pages_text else None
        snippet = re.sub(r"\s+", " ", txt).strip()
        snippet = snippet[:260] + ("…" if len(snippet) > 260 else "")
        sources.append({"page": page_no, "score": s, "text": snippet})

    # generate answer
    answerer = RAGAnswerer()
    answer = answerer.answer(
        question=req.question,
        contexts=passages,
        max_words=req.max_words
    )

    return {
        "doc_id": req.doc_id,
        "question": req.question,
        "answer": answer,
        "sources": sources,  # page numbers + snippet + score
    }

@app.post("/extract")
def extract(req: ExtractRequest):
    doc_dir = os.path.join(DATA_DIR, req.doc_id)
    if not os.path.isdir(doc_dir):
        return {"error": "doc_id not found"}

    pages_path = os.path.join(doc_dir, "pages.json")
    chunks_path = os.path.join(doc_dir, "chunks.json")

    text = ""
    if os.path.exists(pages_path):
        with open(pages_path, "r", encoding="utf-8") as f:
            pages = json.load(f)
            text = "\n\n".join(pages)
    elif os.path.exists(chunks_path):
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            texts = [c["text"] if isinstance(c, dict) else str(c) for c in chunks]
            text = "\n\n".join(texts)

    metrics = extract_metrics_from_text(text)
    return {"doc_id": req.doc_id, "metrics": metrics}

@app.post("/compare")
def compare(req: CompareRequest):
    def load_text(doc_id: str) -> str:
        dd = os.path.join(DATA_DIR, doc_id)
        p = os.path.join(dd, "pages.json")
        c = os.path.join(dd, "chunks.json")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return "\n\n".join(json.load(f))
        if os.path.exists(c):
            with open(c, "r", encoding="utf-8") as f:
                chunks = json.load(f)
                texts = [x["text"] if isinstance(x, dict) else str(x) for x in chunks]
                return "\n\n".join(texts)
        return ""

    text_a = load_text(req.doc_id_a)
    text_b = load_text(req.doc_id_b)

    A = extract_metrics_from_text(text_a)
    B = extract_metrics_from_text(text_b)

    comp = {}
    for k in set(A) | set(B):
        va, vb = A.get(k, ""), B.get(k, "")
        comp[k] = "Same" if va == vb else "Different"

    return {
        "doc_id_a": req.doc_id_a,
        "doc_id_b": req.doc_id_b,
        "a": A,
        "b": B,
        "comparison": comp
    }
