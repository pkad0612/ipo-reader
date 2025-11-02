import json
import re
import numpy as np
import pandas as pd
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from scipy.special import softmax

CORPUS_DIR = Path("data/corpus")

# Load FinBERT
MODEL_NAME = "yiyanghkust/finbert-tone"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
labels = ["Positive", "Negative", "Neutral"]

# Optional: Loughran-McDonald Uncertainty Lexicon (tiny version)
UNCERTAINTY_WORDS = {
    "may", "could", "might", "uncertain", "fluctuate", "volatile",
    "risk", "depend", "contingent", "exposure", "litigation"
}

def load_risk_text(file_id: str) -> str:
    """Return text of the 'Risk Factors' section from corpus JSONL."""
    path = CORPUS_DIR / f"{file_id}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"No parsed corpus found for {file_id}")
    text = ""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line.strip().replace("'", '"'))
            if d["section"].lower().startswith("risk"):
                text += "\n" + d["text"]
    return text.strip() if text else None


def finbert_sentiment(text: str, batch_size: int = 8):
    """Split text into sentences and compute FinBERT sentiment."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    results = []
    for i in range(0, len(sentences), batch_size):
        batch = sentences[i:i+batch_size]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=128)
        outputs = model(**inputs)
        scores = softmax(outputs.logits.detach().numpy(), axis=1)
        for s, p in zip(batch, scores):
            results.append({
                "sentence": s.strip(),
                "positive": float(p[0]),
                "negative": float(p[1]),
                "neutral": float(p[2]),
                "dominant": labels[int(np.argmax(p))]
            })
    return pd.DataFrame(results)


def compute_risk_score(df: pd.DataFrame) -> float:
    """Weighted risk score: higher if many negatives + uncertainty words."""
    neg_ratio = (df["dominant"] == "Negative").mean()
    unc_density = df["sentence"].str.lower().apply(
        lambda x: sum(w in x for w in UNCERTAINTY_WORDS)
    ).sum() / max(len(df), 1)
    score = (0.7 * neg_ratio + 0.3 * unc_density) * 100
    return round(min(score, 100), 2)


def analyze_risk(file_id: str):
    """End-to-end risk analysis for a given file."""
    text = load_risk_text(file_id)
    if not text:
        raise ValueError("No 'Risk Factors' section found.")

    df = finbert_sentiment(text)
    score = compute_risk_score(df)

    # top negative sentences
    negatives = df[df["dominant"] == "Negative"].nlargest(5, "negative")[["sentence", "negative"]].to_dict("records")

    return {
        "file_id": file_id,
        "risk_score": score,
        "avg_positive": round(df["positive"].mean(), 3),
        "avg_negative": round(df["negative"].mean(), 3),
        "avg_neutral": round(df["neutral"].mean(), 3),
        "top_negatives": negatives
    }
