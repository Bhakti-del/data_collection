"""
build_ooad_dataset.py
======================
Builds the OOAD (Object Oriented Analysis and Design) dataset CSV
from cleaned question paper .txt files across R13 regulation.

Output: data/OOAD_Dataset.csv
"""

import os
import re
import csv
from collections import defaultdict
from pathlib import Path

# ── Topic keyword taxonomy ─────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "OOP_PARADIGM_AND_CONCEPTS": [
        "object oriented", "oop", "object oriented modeling", "object oriented paradigm",
        "why do we model", "model", "modeling", "principles of modeling",
        "four aims of modeling", "object oriented analysis", "object oriented design",
    ],
    "UML_OVERVIEW_AND_IMPORTANCE": [
        "uml", "unified modeling language", "importance of uml", "uml diagrams",
        "building blocks", "uml addresses", "significance of uml",
    ],
    "STRUCTURAL_THINGS": [
        "structural things", "class", "interface", "collaboration", "use case",
        "active class", "component", "node", "behavioral things", "annotational things",
        "relationships in uml", "grouping things",
    ],
    "STEREOTYPES_AND_CONSTRAINTS": [
        "stereotype", "stereotypes", "constraints", "tagged values", "extensibility",
    ],
    "CLASS_DIAGRAM": [
        "class diagram", "class diagrams", "structural diagram", "vocabulary of a system",
        "simple collaboration", "modeling a database schema",
    ],
    "CLASS_RELATIONSHIPS": [
        "relationship", "relationships", "dependency", "association", "aggregation",
        "composition", "is-a relationship", "has-a relationship", "advanced relationships",
    ],
    "OBJECT_DIAGRAM": [
        "object diagram", "object diagrams", "modeling techniques for object",
        "contrast is-a", "differentiate between classes and object",
    ],
    "USECASE_DIAGRAM": [
        "use case", "usecase", "use-case", "actor", "actors", "scenario",
        "usecase diagram", "use case diagram", "modeling the context",
        "use case relationships", "extend", "include",
    ],
    "SEQUENCE_DIAGRAM": [
        "sequence diagram", "interaction diagram", "interaction diagrams",
        "phone call", "flow of control", "message", "lifeline",
    ],
    "COLLABORATION_DIAGRAM": [
        "collaboration diagram", "common modeling techniques of collaboration",
    ],
    "ACTIVITY_DIAGRAM": [
        "activity diagram", "swimlane", "swimlanes", "fork", "join", "object flow",
        "activity", "logging into", "email system",
    ],
    "STATECHART_DIAGRAM": [
        "statechart", "state diagram", "state machine", "events and signals",
        "behavioral modeling",
    ],
    "COMPONENT_DIAGRAM": [
        "component diagram", "components", "component and interface",
        "components vs classes", "differences between components and classes",
        "common uses of component diagram",
    ],
    "DEPLOYMENT_DIAGRAM": [
        "deployment diagram", "forward engineer", "reverse engineer",
        "modeling tables", "modeling files", "modeling documents",
        "deployment", "node",
    ],
    "PATTERNS_AND_FRAMEWORKS": [
        "pattern", "framework", "architectural pattern", "patterns and framework",
        "differenti between patterns and framework",
    ],
    "LIBRARY_MANAGEMENT_SYSTEM_CASE_STUDY": [
        "library", "library management", "library system", "library application",
        "check out", "search facility", "wild card", "borrower",
    ],
    "OBJECT_ORIENTED_DESIGN_PRINCIPLES": [
        "design principles", "ood", "object oriented design", "iterative",
        "rational unified process", "rup", "unified process",
    ],
}

BLOOM_APPLY_KEYWORDS = [
    "write", "draw", "construct", "develop", "implement", "design", "build",
    "create", "compose", "prepare", "formulate"
]
BLOOM_ANALYZE_KEYWORDS = [
    "differentiate", "distinguish", "compare", "contrast", "analyze", "analyse",
    "examine", "classify", "differences between", "difference between"
]
BLOOM_EVALUATE_KEYWORDS = [
    "evaluate", "justify", "critique", "assess", "defend", "argue", "is it necessary",
    "are uml diagrams necessary"
]
BLOOM_REMEMBER_KEYWORDS = [
    "define", "list", "state", "name", "what is", "mention", "outline",
    "write short note", "briefly"
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
    best_topic = "UML_OVERVIEW_AND_IMPORTANCE"
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

def parse_questions(content: str, year: int, filepath: str) -> list:
    rows = []

    # Part A
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
                "subject_name": "Object Oriented Analysis and Design",
                "raw_question_text": q,
                "topic_tag": assign_topic(q),
                "bloom_level": infer_bloom(q),
                "original_marks": marks,
                "part_a_years": [year],
                "part_b_years": [],
            })

    # Part B
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
                "subject_name": "Object Oriented Analysis and Design",
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
        base / "R13_text" / "question papers" / "3-2" / "OBJECT ORIENTED ANALYSIS AND DESIGN",
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
            rows = parse_questions(content, year, str(txt_file))
            all_rows.extend(rows)
            total_files += 1
            print(f"  Parsed: {txt_file.name} → {len(rows)} questions (year {year})")

    print(f"\nTotal files parsed: {total_files}")
    print(f"Total raw questions: {len(all_rows)}")

    deduped = deduplicate(all_rows)
    print(f"After deduplication: {len(deduped)} unique questions")

    output = Path("data/OOAD_Dataset.csv")
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
