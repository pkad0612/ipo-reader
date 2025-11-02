from transformers import pipeline
from typing import List

class HierarchicalSummarizer:
    def __init__(self, model_name: str = "sshleifer/distilbart-cnn-12-6"):
        self.summarizer = pipeline("summarization", model=model_name)

    def summarize_chunk(self, text: str, max_words: int = 120) -> str:
        max_len = min(256, max(128, int(max_words * 1.3)))
        out = self.summarizer(text[:4000], max_length=max_len, min_length=int(max_len * 0.4), do_sample=False)
        return out[0]["summary_text"]

    def hierarchical_summarize(self, chunks: List[str], target_words: int = 300) -> str:
        micros = [self.summarize_chunk(c, max_words=120) for c in chunks[:20]]
        joined = " \n".join(micros)
        master = self.summarize_chunk(joined, max_words=target_words)
        return master
