"""
build_mfcs_dataset.py
======================
Builds the MFCS (Mathematical Foundations of Computer Science) dataset CSV
from cleaned question paper .txt files across R13, R15, R16 regulations.

Output: data/MFCS_Dataset.csv
"""

import os
import re
import csv
from pathlib import Path

# ── Topic keyword taxonomy ─────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "PROPOSITIONAL_LOGIC": [
        "propositional logic", "proposition", "well formed formula", "wff",
        "connectives", "logical connective", "tautology", "contradiction",
        "contingency", "minimal set of connectives",
    ],
    "NORMAL_FORMS_DNF_CNF": [
        "dnf", "cnf", "pcnf", "pdnf", "principal conjunctive normal form",
        "principal disjunctive normal form", "normal form", "canonical form",
    ],
    "LOGICAL_EQUIVALENCES_AND_IDENTITIES": [
        "logical equivalence", "logical identities", "equivalence", "simplify",
        "logical expression", "tautology", "contradiction",
    ],
    "THEORY_OF_INFERENCE": [
        "inference", "rules of inference", "indirect proof", "deduction",
        "valid argument", "inconsistent", "derive", "theory of inference",
    ],
    "PREDICATE_LOGIC": [
        "predicate logic", "predicate calculus", "quantifier", "universal quantifier",
        "existential quantifier", "predicate", "prenex normal form",
    ],
    "RELATIONS_DEFINITION_AND_TYPES": [
        "relation", "binary relation", "properties of relation", "reflexive",
        "symmetric", "transitive", "antisymmetric", "irreflexive",
        "equivalence relation", "partial order", "total order",
    ],
    "EQUIVALENCE_RELATION": [
        "equivalence relation", "equivalence class", "partition",
        "equal on set of integers", "divisible by",
    ],
    "HASSE_DIAGRAM": [
        "hasse diagram", "poset", "partial ordering", "power set", "divisibility",
    ],
    "LATTICE": [
        "lattice", "lub", "glb", "least upper bound", "greatest lower bound",
        "bounded lattice", "distributive lattice",
    ],
    "ALGEBRAIC_STRUCTURES": [
        "algebraic structure", "semigroup", "monoid", "group", "abelian group",
        "homomorphism", "isomorphism", "subgroup", "cyclic group",
        "verify which of the following are semi group",
    ],
    "SET_THEORY_BASICS": [
        "set theory", "set operations", "union", "intersection", "complement",
        "cartesian product", "power set", "venn diagram", "a x b",
    ],
    "BASIC_COUNTING_PRINCIPLES": [
        "counting", "permutation", "combination", "rule of sum", "rule of product",
        "multiplication principle", "addition principle",
    ],
    "PERMUTATIONS_AND_COMBINATIONS": [
        "permutations", "combinations", "r-permutation", "r-combination",
        "arrangement", "selection", "committee", "ways can",
    ],
    "PIGEONHOLE_PRINCIPLE": [
        "pigeonhole", "pigeon hole", "dirichlet", "given any",
    ],
    "INCLUSION_EXCLUSION_PRINCIPLE": [
        "inclusion exclusion", "principle of inclusion", "derangement",
    ],
    "BINOMIAL_THEOREM": [
        "binomial theorem", "binomial coefficient", "binomial identity",
        "expand", "binomial", "multinomial", "pascal",
    ],
    "GENERATING_FUNCTIONS": [
        "generating function", "ordinary generating function", "exponential generating function",
        "sequence", "enumerator", "generating functions",
    ],
    "LINEAR_RECURRENCE_RELATIONS": [
        "recurrence relation", "recurrence", "linear recurrence", "homogeneous",
        "characteristic equation", "characteristic root", "fibonacci",
        "fibonacci series", "an =", "solve the recurrence",
    ],
    "NON_HOMOGENEOUS_RECURRENCE_RELATIONS": [
        "non homogeneous", "nonhomogeneous", "particular solution",
        "solve an", "difference equation",
    ],
    "GRAPH_BASICS_AND_TERMINOLOGY": [
        "graph", "vertex", "vertices", "edge", "degree", "in degree", "out degree",
        "simple graph", "directed graph", "undirected graph", "multigraph",
        "complete graph", "bipartite", "path", "walk", "trail",
    ],
    "EULER_GRAPH_AND_PATH": [
        "euler", "eulerian", "euler path", "euler circuit", "euler graph",
        "konigsberg",
    ],
    "HAMILTONIAN_GRAPH_AND_PATH": [
        "hamiltonian", "hamilton", "hamiltonian path", "hamiltonian circuit",
        "hamiltonian graph",
    ],
    "PLANAR_GRAPHS": [
        "planar", "planar graph", "non planar", "kuratowski", "k3,3", "k5",
        "euler formula", "region", "degree of region",
    ],
    "GRAPH_COLORING_AND_CHROMATIC_NUMBER": [
        "chromatic number", "graph coloring", "coloring", "k-colorable",
        "cycle graph", "cn",
    ],
    "SPANNING_TREE": [
        "spanning tree", "minimum spanning tree", "prim", "kruskal",
        "depth first", "breadth first", "tree",
    ],
    "ISOMORPHIC_GRAPHS": [
        "isomorphic", "isomorphism", "complement", "self-complementary", "c5",
    ],
}

BLOOM_APPLY_KEYWORDS = [
    "draw", "construct", "solve", "calculate", "compute", "find", "expand",
    "apply", "evaluate the sum", "prove", "show that"
]
BLOOM_ANALYZE_KEYWORDS = [
    "differentiate", "distinguish", "compare", "contrast", "analyze", "analyse",
    "differences between", "difference between", "classify"
]
BLOOM_EVALUATE_KEYWORDS = [
    "justify", "critique", "assess", "verify", "validate", "is it",
]
BLOOM_REMEMBER_KEYWORDS = [
    "define", "list", "state", "name", "what is", "mention", "write the",
    "give", "write short note", "briefly"
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
    best_topic = "PROPOSITIONAL_LOGIC"
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
            marks = int(m.group(2))
            rows.append({
                "subject_name": "Mathematical Foundations of Computer Science",
                "raw_question_text": q,
                "topic_tag": assign_topic(q),
                "bloom_level": infer_bloom(q),
                "original_marks": marks,
                "part_a_years": [year],
                "part_b_years": [],
            })

    part_b_match = re.search(
        r'PART\s*[-–]\s*B.*?\n(.*)',
        content, re.DOTALL | re.IGNORECASE
    )
    if part_b_match:
        part_b = part_b_match.group(1)
        for m in re.finditer(
            r'(?:^|\n)\s*\d+\.?\s*[ab]?\)\s*(.*?)(?=\n\s*(?:OR|\d+\.|\Z))',
            part_b, re.DOTALL | re.IGNORECASE
        ):
            q = clean_text(m.group(1))
            if len(q) < 10:
                continue
            rows.append({
                "subject_name": "Mathematical Foundations of Computer Science",
                "raw_question_text": q,
                "topic_tag": assign_topic(q),
                "bloom_level": infer_bloom(q),
                "original_marks": 5,
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
        base / "R13_text" / "question papers" / "2-1" / "MATHEMATICAL FOUNDATIONS OF COMPUTER SCIENCE",
        base / "R15_text" / "Question Papers" / "2-1" / "MATHEMATICAL FOUNDATIONS OF COMPUTER SCIENCE",
        base / "R16_text" / "Question Papers" / "2-1" / "2-1" / "MATHEMATICAL FOUNDATIONS OF COMPUTER SCIENCE",
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

    output = Path("data/MFCS_Dataset.csv")
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
