import re
from typing import List, Dict, Any

def chunk_text(text: str, target_words: int = 850, overlap_words: int = 80) -> List[str]:
    """
    Word-based chunking (legacy, no metadata).
    """
    text = re.sub(r"\s+", " ", text)
    words = text.split()
    chunks = []
    i = 0
    step = max(1, target_words - overlap_words)
    while i < len(words):
        chunk = words[i:i + target_words]
        if not chunk:
            break
        chunks.append(" ".join(chunk))
        i += step
    return chunks

def chunk_pages(pages: List[str], target_words: int = 850, overlap_words: int = 80) -> List[Dict[str, Any]]:
    """
    Page-aware chunking. Returns list of dicts:
    [{ 'text': str, 'page': int, 'chunk_idx': int }, ...]
    """
    out: List[Dict[str, Any]] = []
    chunk_idx = 0
    for pnum, page_text in enumerate(pages, start=1):
        norm = re.sub(r"\s+", " ", page_text or "")
        words = norm.split()
        if not words:
            continue
        i = 0
        step = max(1, target_words - overlap_words)
        while i < len(words):
            w = words[i:i + target_words]
            if not w:
                break
            out.append({
                "text": " ".join(w),
                "page": pnum,
                "chunk_idx": chunk_idx
            })
            chunk_idx += 1
            i += step
    return out
