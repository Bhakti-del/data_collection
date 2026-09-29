"""
txt_to_csv.py
Converts cleaned JNTUH question paper text files into the master dataset CSV.

Usage:
    python txt_to_csv.py --input_dir data/extracted_text --output data/processed_dataset/questions_master.csv

Directory structure expected:
    data/extracted_text/[Regulation]/[SubjectName]/[Year]_[Month]_[ExamType].txt

Output CSV fields (8 fields):
    subject_name, raw_question_text, topic_tag, topic_category, bloom_level, original_marks, part_a_years, part_b_years
"""

import os
import re
import csv
import json
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Noise patterns to strip from text files
# ---------------------------------------------------------------------------
NOISE_PATTERNS = [
    r"Code No[:\s]+\S+",
    r"JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY.*",
    r"B\.?\s*Tech.*Examinations.*",
    r"Time\s*:\s*\d+\s*Hours.*",
    r"Max\.?\s*Marks\s*:\s*\d+",
    r"Note\s*:.*",
    r"PART[\s\-]*[AB].*",
    r"\(\d+\s*Marks\)",
    r"Answer any.*",
    r"---+ooOoo---+",
    r"^\s*R\d{2}\s*$",
    r"\(Common to.*?\)",
    r"Hall Ticket.*",
]

BLOOM_KEYWORDS = {
    "Remember":   ["define", "state", "list", "name", "identify", "recall", "what is"],
    "Understand": ["explain", "describe", "discuss", "summarize", "interpret", "classify"],
    "Apply":      ["solve", "compute", "calculate", "construct", "implement", "demonstrate", "find"],
    "Analyze":    ["analyze", "compare", "differentiate", "examine", "trace", "derive"],
    "Evaluate":   ["evaluate", "justify", "assess", "critique", "test", "verify"],
}


def infer_bloom(text: str) -> str:
    text_lower = text.lower()
    for level, keywords in BLOOM_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return level
    return "Understand"


def strip_noise(text: str) -> str:
    for pattern in NOISE_PATTERNS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.MULTILINE)
    return text


def extract_questions(text: str) -> list[dict]:
    """
    Splits cleaned text into atomic questions with marks and part (A/B).
    Returns list of {text, marks, part}
    """
    questions = []

    # Part A: each sub-question has its own mark bracket <= 3
    # e.g. "1.a) Define a linked list? [1]" or "b) Explain big-oh. [3]"
    part_a_pattern = re.compile(
        r"(?:^\s*\d+\.\s*)?[a-j]\)\s*(.+?)\s*\[([1-3])\]",
        re.MULTILINE | re.DOTALL
    )
    has_part_a = False
    for m in part_a_pattern.finditer(text):
        q_text = re.sub(r"\s+", " ", m.group(1)).strip()
        if len(q_text) > 15:
            questions.append({"text": q_text, "marks": int(m.group(2)), "part": "A"})
            has_part_a = True

    # Part B: numbered blocks "2.a) ...\nb) ... [5+5]" or "6. ... [10]"
    # The mark bracket is at the END of the whole block, shared by all sub-questions.
    # We split each a)/b) sub-question into a separate row.
    part_b_block = re.compile(
        r"^\s*(\d+)\.\s*(.+?)\s*\[([\d\+]+)\](?=\s*(?:OR\s*)?(?:\n\s*\d+\.|\Z))",
        re.MULTILINE | re.DOTALL
    )
    # Each sub-question inside a block: "a) ..." or "b) ..."
    sub_q = re.compile(r"(?:^|\n)\s*[a-z]\)\s*(.+?)(?=(?:\n\s*[a-z]\)|\Z))", re.DOTALL)

    for m in part_b_block.finditer(text):
        q_num = int(m.group(1))
        if q_num == 1 and has_part_a:
            continue
        marks_raw = m.group(3)
        total_marks = sum(int(x) for x in marks_raw.split("+"))
        if total_marks < 5:
            continue
        block = m.group(2)
        subs = [s.group(1).strip() for s in sub_q.finditer(block) if len(s.group(1).strip()) > 15]
        if subs:
            per_mark = total_marks // len(subs)
            for sub in subs:
                questions.append({"text": re.sub(r"\s+", " ", sub).strip(), "marks": per_mark, "part": "B"})
        else:
            q_text = re.sub(r"\s+", " ", block).strip()
            if len(q_text) > 15:
                questions.append({"text": q_text, "marks": total_marks, "part": "B"})

    return questions


def load_topic_taxonomy(syllabi_dir: str) -> dict[str, dict]:
    """
    Loads topic tags and their parent categories from syllabus JSON files.
    Returns dict:
        {
            topic_tag: {
                "category": topic_category,
                "keywords": [keyword, ...]
            }
        }
    """
    taxonomy = {}
    syllabi_path = Path(syllabi_dir)
    if not syllabi_path.exists():
        return taxonomy

    for json_file in syllabi_path.rglob("*.json"):
        try:
            with open(json_file) as f:
                syllabus = json.load(f)
            for unit in syllabus.get("units", {}).values():
                for category, tags in unit.get("categories", {}).items():
                    for tag in tags:
                        keywords = tag.lower().replace("_", " ").split()
                        taxonomy[tag] = {
                            "category": category,
                            "keywords": keywords,
                        }
        except Exception:
            continue

    return taxonomy


def infer_topic(q_text: str, taxonomy: dict) -> tuple[str, str]:
    """
    Infers (topic_tag, topic_category) for a given question text based on taxonomy keywords.
    """
    text_lower = q_text.lower()
    best_tag = "UNTAGGED"
    best_category = "UNCATEGORIZED"
    best_score = 0
    for tag, meta in taxonomy.items():
        keywords = meta.get("keywords", [])
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_tag = tag
            best_category = meta.get("category", "UNCATEGORIZED")
    return best_tag, best_category


def parse_filename(filename: str) -> int | None:
    """Extract year from filename like 2021_Nov_Regular.txt"""
    m = re.search(r"(\d{4})", filename)
    return int(m.group(1)) if m else None


def process_files(input_dir: str, syllabi_dir: str, output_csv: str):
    taxonomy = load_topic_taxonomy(syllabi_dir)

    # subject_name -> question_text -> {marks, part_a_years, part_b_years, bloom, topic_tag, topic_category}
    dataset: dict[str, dict[str, dict]] = {}

    input_path = Path(input_dir)
    txt_files = list(input_path.rglob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return

    for txt_file in txt_files:
        # Derive subject_name from directory structure
        parts = txt_file.parts
        # Expected: .../extracted_text/[Regulation]/[SubjectName]/file.txt
        subject_name = parts[-2] if len(parts) >= 2 else "Unknown"
        subject_name = subject_name.replace("_", " ").title()

        year = parse_filename(txt_file.name)
        if not year:
            print(f"[SKIP] Cannot parse year from {txt_file.name}")
            continue

        raw_text = txt_file.read_text(encoding="utf-8", errors="ignore")
        clean_text = strip_noise(raw_text)
        questions = extract_questions(clean_text)

        if subject_name not in dataset:
            dataset[subject_name] = {}

        for q in questions:
            q_text = q["text"]
            part = q["part"]
            marks = q["marks"]

            if q_text not in dataset[subject_name]:
                topic_tag, topic_category = infer_topic(q_text, taxonomy)
                dataset[subject_name][q_text] = {
                    "marks": marks,
                    "bloom_level": infer_bloom(q_text),
                    "topic_tag": topic_tag,
                    "topic_category": topic_category,
                    "part_a_years": [],
                    "part_b_years": [],
                }

            entry = dataset[subject_name][q_text]
            if part == "A" and year not in entry["part_a_years"]:
                entry["part_a_years"].append(year)
            elif part == "B" and year not in entry["part_b_years"]:
                entry["part_b_years"].append(year)

    # Write CSV
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "subject_name", "raw_question_text", "topic_tag", "topic_category",
            "bloom_level", "original_marks", "part_a_years", "part_b_years"
        ])
        writer.writeheader()
        for subject, questions in dataset.items():
            for q_text, meta in questions.items():
                writer.writerow({
                    "subject_name": subject,
                    "raw_question_text": q_text,
                    "topic_tag": meta["topic_tag"],
                    "topic_category": meta["topic_category"],
                    "bloom_level": meta["bloom_level"],
                    "original_marks": meta["marks"],
                    "part_a_years": sorted(meta["part_a_years"]),
                    "part_b_years": sorted(meta["part_b_years"]),
                })

    total = sum(len(qs) for qs in dataset.values())
    print(f"Done. {total} unique questions written to {output_csv}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir",   default="data/extracted_text")
    parser.add_argument("--syllabi_dir", default="data/syllabi_configs")
    parser.add_argument("--output",      default="data/processed_dataset/questions_master.csv")
    args = parser.parse_args()

    process_files(args.input_dir, args.syllabi_dir, args.output)
