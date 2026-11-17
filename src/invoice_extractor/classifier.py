import re

from .rules import CATEGORIES, DEFAULT_CATEGORY, GST_CATEGORY

def classify(text: str) -> str:
    body = text.lower()
    non_empty = [line for line in body.splitlines() if line.strip()]
    header = " ".join(non_empty[:5])

    scores = {}
    for name, cfg in CATEGORIES.items():
        if cfg.get("generic"):
            continue
        score = 0
        for kw in cfg["keywords"]:
            pattern = rf"\b{re.escape(kw)}(?:s|es)?\b"
            score += len(re.findall(pattern, body)) + 3 * len(re.findall(pattern, header))
        scores[name] = score

    if scores:
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            return best

    gst_words = CATEGORIES[GST_CATEGORY]["keywords"]
    if any(re.search(rf"\b{re.escape(word)}\b", body) for word in gst_words):
        return GST_CATEGORY
    return DEFAULT_CATEGORY
