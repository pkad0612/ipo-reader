import os
import json
from typing import List, Dict, Any, Union
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

class EmbeddingStore:
    def __init__(self, doc_dir: str):
        self.doc_dir = doc_dir
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self.model = SentenceTransformer(self.model_name)
        self.index = None
        self.texts: List[str] = []
        self.metas: List[Dict[str, Any]] = []

    @property
    def index_path(self):
        return os.path.join(self.doc_dir, "index.faiss")

    @property
    def meta_path(self):
        return os.path.join(self.doc_dir, "index_meta.json")

    @classmethod
    def load_or_create(cls, doc_dir: str):
        store = cls(doc_dir)
        if os.path.exists(store.index_path) and os.path.exists(store.meta_path):
            store._load()
        return store

    def index_chunks(self, chunks: List[Union[str, Dict[str, Any]]]):
        """
        Accepts either list[str] or list[{'text', ...meta}]
        """
        if not chunks:
            self.texts, self.metas = [], []
            dim = 384
            self.index = faiss.IndexFlatIP(dim)
            return

        if isinstance(chunks[0], dict):
            self.texts = [c["text"] for c in chunks]
            # Keep only JSON-serializable meta
            self.metas = [{k: v for k, v in c.items() if k != "text"} for c in chunks]
        else:
            self.texts = list(chunks)
            self.metas = [{"page": None, "chunk_idx": i} for i in range(len(self.texts))]

        embs = self.model.encode(self.texts, batch_size=64, convert_to_numpy=True, show_progress_bar=False)
        faiss.normalize_L2(embs)
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs)

    def save(self):
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.meta_path, "w", encoding="utf-8") as f:
                json.dump({"texts": self.texts, "metas": self.metas}, f)

    def _load(self):
        self.index = faiss.read_index(self.index_path)
        with open(self.meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        self.texts = meta.get("texts", [])
        self.metas = meta.get("metas", [{"page": None, "chunk_idx": i} for i in range(len(self.texts))])

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        q = self.model.encode([query], convert_to_numpy=True)
        faiss.normalize_L2(q)
        D, I = self.index.search(q, top_k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx == -1:
                continue
            results.append({
                "id": int(idx),
                "text": self.texts[idx],
                "score": float(score),
                "meta": self.metas[idx] if idx < len(self.metas) else {}
            })
        return results
