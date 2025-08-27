import re
import pandas as pd

def tokenize(text: str):
    """
    Tokenize text into lowercase words, including common tech symbols.
    """
    tokens = re.findall(r"[A-Za-z][A-Za-z+.#-]*", text.lower())
    return tokens

def keyword_score(resume_text: str, job_desc: str) -> float:
    """
    Compute raw keyword match score between resume and job description.
    Tech keywords are weighted slightly higher.
    """
    r = set(tokenize(resume_text))
    j = set(tokenize(job_desc))
    if not j:
        return 0.0
    
    overlap = r.intersection(j)
    
    # Slightly reduced weights for tech keywords
    tech_keywords = {
        "python","flask","sql","pandas","javascript",
        "react","docker","aws","gcp","azure","ml","nlp"
    }
    
    weights = {k: 1.5 if k in tech_keywords else 1.0 for k in overlap}
    
    raw_score = sum(weights.values()) / (len(j) + 1e-6)
    return float(raw_score)

def normalize_score(raw: float) -> int:
    """
    Convert raw score to 0-100 with reduced scaling.
    Non-linear compression reduces extreme high scores.
    """
    # scale raw score and compress high values
    scaled = min(1.0, raw * 1.2)  # reduced from 1.8 → 1.2
    pct = scaled ** 0.9  # non-linear compression
    return int(round(pct * 100))
