"""
tagger.py
---------
Assigns topic_tag and bloom_level to each question in questions_raw.csv
using sentence embeddings + unit position filtering.

Two outputs:
  data/questions_tagged.csv   — all questions with assigned tags
  data/review_queue.csv       — low-confidence rows needing human review

Usage:
    pip install sentence-transformers
    python src/tagger.py
"""

import csv
import numpy as np
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

QUESTIONS_RAW  = Path("data/questions_raw.csv")
VOCAB_FILE     = Path("data/topic_tag_vocabulary.csv")
TAGGED_OUT     = Path("data/questions_tagged.csv")
REVIEW_OUT     = Path("data/review_queue.csv")
EMBEDDINGS_OUT = Path("data/topic_embeddings.npy")

# Confidence below this → goes to review queue
AUTO_TAG_THRESHOLD = 0.35

# If top-2 scores are within this margin → flag as ambiguous
AMBIGUITY_MARGIN = 0.07

# ── BLOOM LEVEL ───────────────────────────────────────────────────────────────

BLOOM_VERBS = {
    "Remember":   ["define", "list", "state", "name", "identify", "what is",
                   "what are", "mention", "recall", "label"],
    "Understand": ["explain", "describe", "discuss", "differentiate", "distinguish",
                   "compare", "contrast", "summarize", "interpret", "classify",
                   "give an example", "illustrate"],
    "Apply":      ["write", "implement", "construct", "solve", "perform", "compute",
                   "calculate", "show", "demonstrate", "apply", "develop",
                   "design", "draw", "simulate", "trace", "convert"],
    "Analyze":    ["analyze", "derive", "examine", "investigate", "determine",
                   "justify", "find", "obtain", "how does", "what happens"],
    "Evaluate":   ["evaluate", "assess", "critique", "recommend",
                   "support or oppose", "compare and justify"],
}

def get_bloom_level(text: str) -> str:
    t = text.lower()
    for level in ["Evaluate", "Analyze", "Apply", "Understand", "Remember"]:
        for verb in BLOOM_VERBS[level]:
            if verb in t:
                return level
    return "Understand" if "?" in text else "Apply"

# ── VOCABULARY ────────────────────────────────────────────────────────────────

def load_vocabulary():
    vocab = []
    with open(VOCAB_FILE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["unit_number"] = int(row["unit_number"])
            vocab.append(row)

    unit_tags = {}
    for row in vocab:
        key = (row["subject_name"], row["unit_number"])
        unit_tags.setdefault(key, []).append(row["topic_tag"])

    return vocab, unit_tags

# ── EMBEDDINGS ────────────────────────────────────────────────────────────────

def load_or_build_embeddings(vocab):
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers")

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    if EMBEDDINGS_OUT.exists():
        print(f"Loading cached topic embeddings from {EMBEDDINGS_OUT}")
        embeddings = np.load(str(EMBEDDINGS_OUT))
    else:
        print(f"Computing topic embeddings for {len(vocab)} topics...")
        descriptions = [row["description"] for row in vocab]
        embeddings = model.encode(descriptions, show_progress_bar=True)
        np.save(str(EMBEDDINGS_OUT), embeddings)
        print(f"Saved to {EMBEDDINGS_OUT}")

    return model, embeddings

# ── TAGGING ───────────────────────────────────────────────────────────────────

def cosine_sim(vec, matrix):
    norm_a = np.linalg.norm(vec)
    norms  = np.linalg.norm(matrix, axis=1)
    if norm_a == 0:
        return np.zeros(len(matrix))
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = np.dot(matrix, vec) / (norms * norm_a)
        return np.nan_to_num(sims)

def tag_question(text, subject, unit_num, model, vocab, embeddings, unit_tags):
    # Get valid tags for this subject+unit
    valid_tags = unit_tags.get((subject, unit_num), [])
    if not valid_tags or unit_num == 0:
        valid_tags = [r["topic_tag"] for r in vocab if r["subject_name"] == subject]

    valid_indices = [i for i, r in enumerate(vocab) if r["topic_tag"] in valid_tags]

    if not valid_indices:
        return {"topic_tag": "", "confidence": 0.0, "needs_review": True}

    q_emb = model.encode([text])[0]
    filtered = embeddings[valid_indices]
    sims = cosine_sim(q_emb, filtered)

    best_local = int(np.argmax(sims))
    best_score = float(sims[best_local])
    best_idx   = valid_indices[best_local]

    sorted_sims = np.sort(sims)[::-1]
    second      = float(sorted_sims[1]) if len(sorted_sims) > 1 else 0.0
    ambiguous   = (best_score - second) < AMBIGUITY_MARGIN

    return {
        "topic_tag":    vocab[best_idx]["topic_tag"],
        "confidence":   round(best_score, 4),
        "needs_review": best_score < AUTO_TAG_THRESHOLD or ambiguous,
    }

# ── MAIN ──────────────────────────────────────────────────────────────────────

TAGGED_FIELDS = [
    "subject_name", "raw_question_text", "question_type",
    "original_marks", "unit_number", "regulation", "year", "session",
    "year_sem", "has_diagram", "data_quality",
    "topic_tag", "bloom_level", "tag_confidence", "needs_review",
]

def main():
    if not QUESTIONS_RAW.exists():
        print(f"ERROR: {QUESTIONS_RAW} not found. Run parser.py first.")
        return

    vocab, unit_tags = load_vocabulary()
    model, embeddings = load_or_build_embeddings(vocab)

    with open(QUESTIONS_RAW, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"\nTagging {len(rows)} questions...\n")

    tagged = []
    review = []

    for row in rows:
        subject  = row["subject_name"]
        unit_num = int(row["unit_number"]) if str(row["unit_number"]).isdigit() else 0
        text     = row["raw_question_text"]

        result = tag_question(text, subject, unit_num, model, vocab, embeddings, unit_tags)
        bloom  = get_bloom_level(text)

        out = {**row,
               "topic_tag":      result["topic_tag"],
               "bloom_level":    bloom,
               "tag_confidence": result["confidence"],
               "needs_review":   result["needs_review"]}

        tagged.append(out)
        if result["needs_review"]:
            review.append(out)

    with open(TAGGED_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TAGGED_FIELDS)
        writer.writeheader()
        writer.writerows(tagged)

    with open(REVIEW_OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=TAGGED_FIELDS)
        writer.writeheader()
        writer.writerows(review)

    n = len(rows)
    auto = n - len(review)
    print(f"\n{'='*55}")
    print(f"Total      : {n}")
    print(f"Auto-tagged: {auto}  ({100*auto//n}%)")
    print(f"Review     : {len(review)}  ({100*len(review)//n}%)")
    print(f"Tagged CSV : {TAGGED_OUT}")
    print(f"Review CSV : {REVIEW_OUT}")
    print(f"{'='*55}")
    print(f"\nNext: review data/review_queue.csv, then run deduplicator.py")

if __name__ == "__main__":
    main()
