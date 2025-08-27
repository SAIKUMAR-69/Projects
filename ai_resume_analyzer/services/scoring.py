import re
import pandas as pd

def tokenize(text: str):
    tokens = re.findall(r"[A-Za-z][A-Za-z+.#-]*", text.lower())
    return tokens

def keyword_score(resume_text: str, job_desc: str) -> float:
    r = set(tokenize(resume_text))
    j = set(tokenize(job_desc))
    if not j:
        return 0.0
    overlap = r.intersection(j)
    # weight common tech keywords slightly higher
    weights = {k: 2.0 if k in {"python","flask","sql","pandas","javascript","react","docker","aws","gcp","azure","ml","nlp"} else 1.0 for k in overlap}
    score = sum(weights.values()) / (len(j) + 1e-6)
    return float(score)

def normalize_score(raw: float) -> int:
    # Map heuristic raw score to 0-100
    pct = max(0.0, min(1.0, raw * 1.8))  # dampening
    return int(round(pct * 100))
