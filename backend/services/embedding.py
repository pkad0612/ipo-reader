from pathlib import Path
import json
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter

CORPUS_DIR = Path("data/corpus")
FAISS_DIR = Path("data/faiss")
FAISS_DIR.mkdir(parents=True, exist_ok=True)

EMBED_MODEL = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def load_sections(file_id: str):
    """Load the parsed text sections saved earlier in data/corpus."""
    path = CORPUS_DIR / f"{file_id}.jsonl"
    docs = []
    if not path.exists():
        raise FileNotFoundError(f"No corpus file for {file_id}")
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            # each line is a dict string e.g. {"section": "...", "text": "..."}
            d = eval(line.strip())
            docs.append(d)
    return docs


def chunk_text(docs: list[dict], chunk_size=1200, chunk_overlap=150):
    """Split text into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    chunks = []
    for d in docs:
        splits = splitter.split_text(d["text"])
        for i, chunk in enumerate(splits):
            chunks.append({
                "section": d["section"],
                "chunk_id": f"{d['section']}_{i}",
                "text": chunk
            })
    return chunks


def build_faiss_index(file_id: str):
    """Generate embeddings and save FAISS index."""
    docs = load_sections(file_id)
    chunks = chunk_text(docs)
    texts = [c["text"] for c in chunks]

    # Compute embeddings
    embeddings = EMBED_MODEL.encode(texts, batch_size=32, show_progress_bar=True, convert_to_numpy=True, normalize_embeddings=True)

    # Save metadata
    meta_path = FAISS_DIR / f"{file_id}_meta.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f)

    # Build FAISS index
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)  # cosine similarity since we normalized
    index.add(embeddings)

    faiss.write_index(index, str(FAISS_DIR / f"{file_id}.index"))
    return len(chunks)
