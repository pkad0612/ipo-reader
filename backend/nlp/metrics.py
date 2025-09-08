import re
from typing import Dict

SPACE = r"[ \t]*"
NUM   = r"[\d,\.]+"
INR   = r"(?:₹|Rs\.?|INR)\s*"
CRORE = r"(?:crore(?:s)?|Cr\.?)"

_PATTERNS = {
    "Issue Size": re.compile(
        rf"(?:issue size|offer size|aggregate size)\s*[:\-–]\s*({INR}?{NUM}(?:\s*{CRORE})?)",
        re.IGNORECASE),
    "Promoters": re.compile(
        r"(?:promoter(?:s)?|promoted by)\s*[:\-–]\s*([A-Za-z0-9 ,&\.]+)",
        re.IGNORECASE),
    "Objects of the Issue": re.compile(
        r"(?:objects? of the issue|use of proceeds?)\s*[:\-–]\s*(.+?)(?:\n\n|\Z)",
        re.IGNORECASE | re.DOTALL),
    "Top Risks": re.compile(
        r"(?:key risks?|risk factors?)\s*[:\-–]\s*(.+?)(?:\n\n|\Z)",
        re.IGNORECASE | re.DOTALL),
}

def extract_metrics_from_text(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key, pat in _PATTERNS.items():
        m = pat.search(text)
        if not m:
            out[key] = "Not found"
            continue
        val = m.group(1).strip()
        # light cleanup
        val = re.sub(r"\s+", " ", val)
        out[key] = val[:800]
    return out
