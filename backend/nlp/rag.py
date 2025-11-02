from transformers import pipeline
from typing import List

class RAGAnswerer:
    def __init__(self, model_name: str = "google/flan-t5-base"):
        self.generator = pipeline("text2text-generation", model=model_name)

    def answer(self, question: str, contexts: List[str], max_words: int = 200) -> str:
        context_block = "\n\n".join(contexts[:5])
        prompt = (
            "Answer the question based only on the context.\n"
            "Be concise and cite key facts. If unknown, say you don't know.\n\n"
            f"Context:\n{context_block}\n\nQuestion: {question}\nAnswer:"
        )
        max_len = min(256, max(64, int(max_words * 1.3)))
        out = self.generator(prompt, max_length=max_len, do_sample=False)
        return out[0]["generated_text"].strip()
