"""
deduplicator.py
---------------
Reads questions_tagged.csv, merges semantically similar questions
(same concept across different years/wordings), and produces output.csv
with one row per unique question.

Final output fields:
  subject_name, raw_question_text, topic_tag, bloom_level,
  original_marks, part_a_years, part_b_years

Usage:
    python src/deduplicator.py
"""

import csv
import numpy as np
from pathlib import Path
from collections import defaultdict

# ── CONFIG ────────────────────────────────────────────────────────────────────

TAGGED_FILE = Path("data/intermediate/questions_tagged.csv") if Path("data/intermediate/questions_tagged.csv").exists() else Path("data/questions_tagged.csv")
OUTPUT_FILE = Path("output/output.csv")

# Questions with cosine similarity >= this are merged
SIMILARITY_THRESHOLD = 0.82

# ── UNION-FIND ────────────────────────────────────────────────────────────────

class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, x, y):
        self.parent[self.find(x)] = self.find(y)

    def groups(self):
        g = defaultdict(list)
        for i in range(len(self.parent)):
            g[self.find(i)].append(i)
        return list(g.values())

# ── COSINE SIMILARITY ─────────────────────────────────────────────────────────

def cosine_sim_matrix(embeddings: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-9, norms)
    normed = embeddings / norms
    return np.dot(normed, normed.T)

# ── MERGE GROUP ───────────────────────────────────────────────────────────────

def merge_group(group_rows: list) -> dict:
    """
    Merge duplicate rows into one canonical row.
    - raw_question_text : longest version (most complete)
    - topic_tag         : most common assigned value
    - bloom_level       : most common value
    - original_marks    : maximum (Part B marks preferred)
    - part_a_years      : all years where question_type == PART_A
    - part_b_years      : all years where question_type == PART_B
    """
    canonical = max(group_rows, key=lambda r: len(r.get("raw_question_text", "")))

    part_a_years = sorted(set(
        int(r["year"]) for r in group_rows
        if r.get("question_type") == "PART_A" and str(r.get("year", "")).isdigit()
    ))
    part_b_years = sorted(set(
        int(r["year"]) for r in group_rows
        if r.get("question_type") == "PART_B" and str(r.get("year", "")).isdigit()
    ))

    def most_common(values):
        values = [v for v in values if v]
        return max(set(values), key=values.count) if values else ""

    marks_list = [
        int(r["original_marks"]) for r in group_rows
        if str(r.get("original_marks", "")).isdigit()
    ]

    return {
        "subject_name":      canonical["subject_name"],
        "raw_question_text": canonical["raw_question_text"],
        "topic_tag":         most_common([r.get("topic_tag", "") for r in group_rows]),
        "bloom_level":       most_common([r.get("bloom_level", "") for r in group_rows]),
        "original_marks":    max(marks_list) if marks_list else 0,
        "part_a_years":      str(part_a_years),
        "part_b_years":      str(part_b_years),
    }

# ── MAIN ──────────────────────────────────────────────────────────────────────

OUTPUT_FIELDS = [
    "subject_name",
    "raw_question_text",
    "topic_tag",
    "bloom_level",
    "original_marks",
    "part_a_years",
    "part_b_years",
]

def main():
    if not TAGGED_FILE.exists():
        print(f"ERROR: {TAGGED_FILE} not found. Run tagger.py first.")
        return

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        raise ImportError("Run: pip install sentence-transformers")

    with open(TAGGED_FILE, encoding="utf-8") as f:
        all_rows = list(csv.DictReader(f))

    print(f"Loaded {len(all_rows)} question appearances")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer("all-MiniLM-L6-v2")

    subjects   = sorted(set(r["subject_name"] for r in all_rows))
    final_rows = []

    for subject in subjects:
        print(f"\nProcessing: {subject}")
        rows = [r for r in all_rows if r["subject_name"] == subject]
        print(f"  {len(rows)} appearances")

        texts      = [r["raw_question_text"] for r in rows]
        print(f"  Computing embeddings...")
        embeddings = model.encode(texts, show_progress_bar=False, batch_size=64)

        print(f"  Computing similarity matrix...")
        sim = cosine_sim_matrix(embeddings)

        uf = UnionFind(len(rows))
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                if sim[i][j] >= SIMILARITY_THRESHOLD:
                    uf.union(i, j)

        groups = uf.groups()
        print(f"  {len(rows)} appearances → {len(groups)} unique questions")

        for g in groups:
            final_rows.append(merge_group([rows[i] for i in g]))

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_FIELDS)
        writer.writeheader()
        writer.writerows(final_rows)

    subject_counts = defaultdict(int)
    for r in final_rows:
        subject_counts[r["subject_name"]] += 1

    print(f"\n{'='*55}")
    print(f"Total unique questions : {len(final_rows)}")
    for subj, cnt in subject_counts.items():
        print(f"  {subj:35s}: {cnt}")
    print(f"Output                : {OUTPUT_FILE}")
    print(f"{'='*55}")

if __name__ == "__main__":
    main()
