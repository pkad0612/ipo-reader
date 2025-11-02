import json
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from transformers import pipeline

FAISS_DIR = Path("data/faiss")

# Embedding & Reader models
EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
READER = pipeline("question-answering", model="deepset/roberta-base-squad2", tokenizer="deepset/roberta-base-squad2")

def retrieve_top_chunks(file_id: str, query: str, k: int = 5):
    """Return top-k most relevant text chunks from FAISS index."""
    index_path = FAISS_DIR / f"{file_id}.index"
    meta_path = FAISS_DIR / f"{file_id}_meta.json"

    if not index_path.exists() or not meta_path.exists():
        raise FileNotFoundError("No FAISS index or metadata found for this file.")

    # Load index & metadata
    index = faiss.read_index(str(index_path))
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)

    # Embed query and search
    q_vec = EMBED_MODEL.encode([query], normalize_embeddings=True)
    D, I = index.search(q_vec, k)
    results = []
    for rank, idx in enumerate(I[0]):
        chunk = meta[idx]
        results.append({
            "rank": rank + 1,
            "score": float(D[0][rank]),
            "section": chunk["section"],
            "text": chunk["text"]
        })
    return results


def answer_question(file_id: str, query: str):
    """Run retriever-reader pipeline."""
    top_chunks = retrieve_top_chunks(file_id, query, k=5)
    context = "\n\n".join([c["text"] for c in top_chunks])
    result = READER(question=query, context=context)

    return {
        "answer": result.get("answer"),
        "confidence": float(result.get("score", 0)),
        "context": top_chunks[:3]  # include top 3 supporting snippets
    }
