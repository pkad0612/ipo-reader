import json
from pathlib import Path
from transformers import pipeline

CORPUS_DIR = Path("data/corpus")

# Load summarization model
SUMMARIZER = pipeline("summarization", model="facebook/bart-large-cnn")

# Select sections you want to summarize
TARGET_SECTIONS = ["Risk Factors", "Promoters", "Financial Statements", "Business", "MD&A"]

def load_sections(file_id: str):
    """Load section-wise text from the parsed corpus."""
    path = CORPUS_DIR / f"{file_id}.jsonl"
    if not path.exists():
        raise FileNotFoundError(f"No parsed corpus found for {file_id}")
    
    sections = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line.strip().replace("'", '"'))
            section_name = d["section"]
            if section_name in TARGET_SECTIONS:
                text = d["text"].replace("\n", " ")
                sections[section_name] = text[:12000]  # Limit for model input
    return sections


def summarize_text(text: str, max_len=200):
    """Summarize long text using transformer pipeline."""
    try:
        summary = SUMMARIZER(
            text, max_length=max_len, min_length=60, do_sample=False
        )[0]["summary_text"]
        return summary.strip()
    except Exception as e:
        return f"⚠️ Summarization failed: {e}"


def generate_summaries(file_id: str):
    """Generate summaries for key sections."""
    sections = load_sections(file_id)
    results = {}

    for section, text in sections.items():
        print(f"📝 Summarizing {section}...")
        results[section] = summarize_text(text)
    
    return {
        "file_id": file_id,
        "summaries": results
    }
