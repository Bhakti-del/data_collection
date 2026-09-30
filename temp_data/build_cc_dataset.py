"""
build_cc_dataset.py
====================
Builds the Computational Complexity dataset CSV
from cleaned question paper .txt files across R18 regulation.

Output: data/CC_Dataset.csv
"""

import re
import csv
from pathlib import Path

# ── Topic keyword taxonomy ─────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "CLASS_P": [
        "class p", "polynomial time", "polynomial-time", "p class",
        "polynomial run time", "polynomial algorithm", "nontrivial examples",
        "polynomial time algorithm",
    ],
    "CLASS_NP": [
        "class np", "np problem", "np class", "nondeterministic", "np-complete",
        "npcomplete", "np completeness", "polynomial time verification",
        "p versus np", "p vs np", "p and np",
    ],
    "NP_COMPLETENESS": [
        "np-complete", "np complete", "np hard", "np-hard", "reducibility",
        "reduce", "reduction", "cook", "satisfiability", "sat problem",
    ],
    "REDUCIBILITY": [
        "reducibility", "polynomial reduction", "turing reducibility",
        "many-one reducible", "reduce to",
    ],
    "DYNAMIC_PROGRAMMING_OVERVIEW": [
        "dynamic programming", "dp", "optimal substructure", "overlapping subproblems",
        "memoization", "bottom up",
    ],
    "MATRIX_CHAIN_MULTIPLICATION": [
        "matrix chain", "matrix chain multiplication", "matrix multiplication",
        "chain multiplication",
    ],
    "KNAPSACK_PROBLEM": [
        "knapsack", "0/1 knapsack", "fractional knapsack",
        "knapsack problem", "solved using dynamic programming",
    ],
    "HUFFMAN_CODING": [
        "huffman", "huffman coding", "huffman tree", "huffman algorithm",
        "prefix code", "greedy",
    ],
    "QUICKSORT_AND_COMPLEXITY_ANALYSIS": [
        "quick sort", "quicksort", "quick sort algorithm", "worst case",
        "time complexity", "analyze", "analysis",
    ],
    "BRANCH_AND_BOUND_TECHNIQUE": [
        "branch and bound", "branch-and-bound", "bounding function",
        "state space tree", "live node", "dead node",
    ],
    "TRAVELLING_SALESPERSON_PROBLEM": [
        "travelling salesperson", "travelling sales person", "tsp",
        "salesman", "cities", "tour",
    ],
    "BACKTRACKING_STRATEGY": [
        "backtracking", "backtrack", "n-queens", "graph coloring",
        "subset sum", "hamiltonian",
    ],
    "GRAPH_PROBLEMS": [
        "graph problem", "graph problems", "graph algorithms",
        "shortest path", "minimum spanning tree",
    ],
    "RANDOMIZED_ALGORITHMS_OVERVIEW": [
        "randomized algorithm", "randomized algorithms", "randomness",
        "probabilistic", "random", "what are randomized",
    ],
    "FINGERPRINTING": [
        "fingerprinting", "fingerprint", "digital fingerprinting",
        "string matching", "pattern matching",
    ],
    "DERANDOMIZATION": [
        "derandomization", "de-randomization", "deterministic",
        "advanced randomized",
    ],
    "APPROXIMATION_ALGORITHMS": [
        "approximation algorithm", "approximation algorithms",
        "approximation ratio", "approximation scheme",
    ],
    "POLYNOMIAL_TIME_APPROXIMATION_SCHEMES": [
        "polynomial time approximation", "ptas", "fptas",
        "approximation scheme",
    ],
    "DECISION_TREES_AND_CIRCUITS": [
        "decision tree", "decision trees", "circuit", "circuits",
        "boolean circuit", "circuit complexity",
    ],
    "DISJOINT_SETS": [
        "disjoint set", "disjoint sets", "union find", "union-find",
        "set union", "find operation",
    ],
    "B_TREES_INSERTION_AND_DELETION": [
        "b-tree", "b tree", "btree", "b+ tree", "insert", "delete",
        "b-tree operations",
    ],
    "AVL_TREES": [
        "avl tree", "avl", "height balanced", "rotation", "rebalance",
        "avl tree with", "construct an avl",
    ],
}

BLOOM_APPLY_KEYWORDS = [
    "write", "implement", "construct", "solve", "apply", "illustrate",
    "show", "find", "compute", "calculate", "insert", "delete", "build"
]
BLOOM_ANALYZE_KEYWORDS = [
    "differentiate", "compare", "contrast", "analyze", "analyse",
    "differences between", "distinguish", "examine"
]
BLOOM_EVALUATE_KEYWORDS = [
    "evaluate", "justify", "assess", "discuss the advantages", "critique"
]
BLOOM_REMEMBER_KEYWORDS = [
    "define", "list", "state", "what is", "what are", "mention",
    "write a brief note", "write short note", "briefly"
]

def infer_bloom(text: str) -> str:
    t = text.lower()
    if any(k in t for k in BLOOM_EVALUATE_KEYWORDS):
        return "Evaluate"
    if any(k in t for k in BLOOM_ANALYZE_KEYWORDS):
        return "Analyze"
    if any(k in t for k in BLOOM_APPLY_KEYWORDS):
        return "Apply"
    if any(k in t for k in BLOOM_REMEMBER_KEYWORDS):
        return "Remember"
    return "Understand"

def assign_topic(text: str) -> str:
    t = text.lower()
    best_topic = "CLASS_P"
    best_count = 0
    for topic, keywords in TOPIC_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in t)
        if count > best_count:
            best_count = count
            best_topic = topic
    return best_topic

def extract_year(filename: str) -> int:
    m = re.search(r'(20\d{2})', filename)
    return int(m.group(1)) if m else 0

def clean_text(text: str) -> str:
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def parse_questions(content: str, year: int) -> list:
    rows = []

    # CC papers use numbered questions (no Part A/B split in some)
    # Try Part A/B first
    part_a_match = re.search(
        r'PART\s*[-–]\s*A.*?\n(.*?)PART\s*[-–]\s*B',
        content, re.DOTALL | re.IGNORECASE
    )
    if part_a_match:
        part_a = part_a_match.group(1)
        for m in re.finditer(r'[a-j]\)\s*(.*?)\[(\d+)\]', part_a, re.DOTALL | re.IGNORECASE):
            q = clean_text(m.group(1))
            if len(q) < 8:
                continue
            rows.append({
                "subject_name": "Computational Complexity",
                "raw_question_text": q,
                "topic_tag": assign_topic(q),
                "bloom_level": infer_bloom(q),
                "original_marks": int(m.group(2)),
                "part_a_years": [year],
                "part_b_years": [],
            })

    # Parse numbered questions (CC papers use 1., 2., etc.)
    for m in re.finditer(
        r'(?:^|\n)\s*(\d+)\.?\s*[ab]?\)\s*(.*?)(?=\n\s*(?:\d+\.|\Z))',
        content, re.DOTALL | re.IGNORECASE
    ):
        q_num = int(m.group(1))
        if q_num < 1:
            continue
        q = clean_text(m.group(2))
        if len(q) < 10:
            continue
        rows.append({
            "subject_name": "Computational Complexity",
            "raw_question_text": q,
            "topic_tag": assign_topic(q),
            "bloom_level": infer_bloom(q),
            "original_marks": 15,
            "part_a_years": [],
            "part_b_years": [year],
        })

    return rows

def deduplicate(rows: list) -> list:
    merged = {}
    for row in rows:
        key = row["raw_question_text"].lower().strip()[:80]
        if key in merged:
            existing = merged[key]
            if row["part_a_years"]:
                existing["part_a_years"] = sorted(set(existing["part_a_years"] + row["part_a_years"]))
            if row["part_b_years"]:
                existing["part_b_years"] = sorted(set(existing["part_b_years"] + row["part_b_years"]))
        else:
            merged[key] = {
                "subject_name": row["subject_name"],
                "raw_question_text": row["raw_question_text"],
                "topic_tag": row["topic_tag"],
                "bloom_level": row["bloom_level"],
                "original_marks": row["original_marks"],
                "part_a_years": list(row["part_a_years"]),
                "part_b_years": list(row["part_b_years"]),
            }
    return list(merged.values())

def main():
    base = Path("data/cleaned_papers")
    subject_dirs = [
        base / "R18 text" / "4th Year" / "Semester 2" / "COMPUTATIONAL COMPLEXITY",
    ]

    all_rows = []
    total_files = 0

    for subject_dir in subject_dirs:
        if not subject_dir.exists():
            print(f"  WARNING: {subject_dir} not found, skipping.")
            continue
        for txt_file in sorted(subject_dir.glob("*.txt")):
            year = extract_year(txt_file.stem)
            content = txt_file.read_text(encoding="utf-8", errors="replace")
            rows = parse_questions(content, year)
            all_rows.extend(rows)
            total_files += 1
            print(f"  Parsed: {txt_file.name} → {len(rows)} questions (year {year})")

    print(f"\nTotal files parsed: {total_files}")
    print(f"Total raw questions: {len(all_rows)}")

    deduped = deduplicate(all_rows)
    print(f"After deduplication: {len(deduped)} unique questions")

    output = Path("data/CC_Dataset.csv")
    fieldnames = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
                  "original_marks", "part_a_years", "part_b_years"]

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in deduped:
            writer.writerow({
                **row,
                "part_a_years": str(row["part_a_years"]),
                "part_b_years": str(row["part_b_years"]),
            })

    print(f"\nSaved to: {output}  ({len(deduped)} rows)")

if __name__ == "__main__":
    main()
