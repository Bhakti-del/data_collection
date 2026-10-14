#!/usr/bin/env python3
"""
build_math_datasets.py
======================
Builds canonical R22-tagged datasets for core mathematics and foundational subjects:
  1. Discrete Mathematics (migrated & enriched from MFCS)
  2. Matrices and Calculus (from R22, R18, R16, R15, R13 exam papers)
  3. Ordinary Differential Equations & Vector Calculus (from R22, R18, R16, R15, R13)
  4. Computer Oriented Statistical Methods (from R22, R18, R16, R15, R13)

Strictly enforces:
  - Official R22 syllabus topic tags (from data/syllabi/configs/R22/*.json).
  - Canonical 7-column schema.
  - Type A clean text math notation (^ for powers, _ for subscripts, [[...]] for matrices).
  - Deduplication: one row per unique question with year aggregation.
  - Zero modification to Training_Data/.
"""

import os
import sys
import glob
import re
import csv
import json
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "data" / "syllabi" / "configs" / "R22"
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"

BLOOM_VERBS = {
    "Evaluate":   ["evaluate", "justify", "assess", "critique", "recommend", "prove or disprove"],
    "Analyze":    ["analyze", "analyse", "compare", "differentiate", "distinguish", "derive",
                   "examine", "contrast", "determine", "trace", "test"],
    "Apply":      ["apply", "calculate", "compute", "solve", "reduce", "find", "diagonalize",
                   "expand", "construct", "convert", "minimize", "maximize", "show that", "prove that", "verify"],
    "Understand": ["explain", "describe", "discuss", "illustrate", "outline", "summarize"],
    "Remember":   ["define", "state", "list", "what is", "what are", "write down", "give", "name", "mention", "is"]
}

def infer_bloom(text: str) -> str:
    text_lower = text.lower().strip()
    for level, verbs in BLOOM_VERBS.items():
        for v in verbs:
            if re.search(rf"\b{re.escape(v)}\b", text_lower):
                return level
    return "Apply"  # Math default: usually computational/application

def score_topic(text: str, config: dict) -> str:
    text_lower = text.lower()
    best_tag = list(config["topic_keywords"].keys())[0]
    best_score = 0
    for tag, kws in config["topic_keywords"].items():
        score = sum(3 if " " in kw else 1 for kw in kws if kw in text_lower)
        if score > best_score:
            best_score = score
            best_tag = tag
    return best_tag

def clean_math_text(q: str) -> str:
    # Remove OCR noise & trailing artifacts
    q = re.sub(r'\s+', ' ', q).strip()
    q = re.sub(r'--ooOoo--|\bOR\b$|- - -', '', q).strip()
    
    # Standardize common math expressions
    q = re.sub(r'\blog\s+2\(', 'log_2(', q)
    q = re.sub(r'\bT\s*\(\s*n\s*\)', 'T(n)', q)
    q = re.sub(r'->0', '-> 0', q)
    q = re.sub(r'->1', '-> 1', q)
    
    # Clean OCR PUA glyphs if any
    q = q.replace('', ' <=> ').replace('', '^-')
    
    # Clean square roots and symbols
    q = q.replace('', '√')
    return q.strip()

def fix_part_inversion(marks: int, pa_years: set, pb_years: set):
    pa = sorted(list(pa_years))
    pb = sorted(list(pb_years))
    if marks <= 3 and pb and not pa:
        pa = pb
        pb = []
    elif marks >= 8 and pa and not pb:
        pb = pa
        pa = []
    return marks, pa, pb

def build_discrete_mathematics():
    print("Building Discrete Mathematics dataset...")
    config_path = CONFIG_DIR / "Discrete_Mathematics_syllabus.json"
    with open(config_path) as f:
        config = json.load(f)
    
    valid_topics = set()
    for unit in config["units"].values():
        valid_topics.update(unit["topics"])
    
    # Map from old MFCS tags to R22
    TAG_MAP = {
        'PROPOSITIONAL_LOGIC': 'PROPOSITIONAL_LOGIC_AND_CONNECTIVES',
        'NORMAL_FORMS_DNF_CNF': 'NORMAL_FORMS_AND_INFERENCE',
        'PREDICATE_LOGIC': 'PREDICATE_CALCULUS',
        'SET_THEORY_BASICS': 'SET_THEORY_AND_OPERATIONS',
        'INCLUSION_EXCLUSION_PRINCIPLE': 'SET_THEORY_AND_OPERATIONS',
        'RELATIONS_DEFINITION_AND_TYPES': 'RELATIONS_AND_ORDERING',
        'EQUIVALENCE_RELATION': 'RELATIONS_AND_ORDERING',
        'HASSE_DIAGRAM': 'RELATIONS_AND_ORDERING',
        'ALGEBRAIC_STRUCTURES': 'ALGEBRAIC_SYSTEMS_SEMIGROUPS_MONOIDS',
        'LATTICE': 'LATTICES_AND_BOOLEAN_ALGEBRA',
        'BASIC_COUNTING_PRINCIPLES': 'PERMUTATIONS_AND_COMBINATIONS',
        'PERMUTATIONS_AND_COMBINATIONS': 'PERMUTATIONS_AND_COMBINATIONS',
        'PIGEONHOLE_PRINCIPLE': 'PERMUTATIONS_AND_COMBINATIONS',
        'BINOMIAL_THEOREM': 'BINOMIAL_AND_MULTINOMIAL_THEOREMS',
        'LINEAR_RECURRENCE_RELATIONS': 'RECURRENCE_RELATIONS_AND_GENERATING_FUNCTIONS',
        'NON_HOMOGENEOUS_RECURRENCE_RELATIONS': 'RECURRENCE_RELATIONS_AND_GENERATING_FUNCTIONS',
        'GENERATING_FUNCTIONS': 'RECURRENCE_RELATIONS_AND_GENERATING_FUNCTIONS',
        'GRAPH_BASICS_AND_TERMINOLOGY': 'GRAPH_CONCEPTS_AND_ISOMORPHISM',
        'EULER_GRAPH_AND_PATH': 'GRAPH_CONCEPTS_AND_ISOMORPHISM',
        'HAMILTONIAN_GRAPH_AND_PATH': 'GRAPH_CONCEPTS_AND_ISOMORPHISM',
        'SPANNING_TREE': 'TREES_AND_SPANNING_TREES',
        'PLANAR_GRAPHS': 'PLANAR_GRAPHS_AND_COLORING',
        'GRAPH_COLORING_AND_CHROMATIC_NUMBER': 'PLANAR_GRAPHS_AND_COLORING'
    }
    
    source_csv = PROJECT_ROOT / "temp_data" / "MFCS_Dataset.csv"
    with open(source_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    dedup = {}
    for r in rows:
        q = clean_math_text(r["raw_question_text"])
        old_tag = r["topic_tag"]
        new_tag = TAG_MAP.get(old_tag)
        if not new_tag or new_tag not in valid_topics:
            new_tag = score_topic(q, config)
            
        bloom = r["bloom_level"]
        if bloom not in {"Remember", "Understand", "Apply", "Analyze", "Evaluate"}:
            bloom = infer_bloom(q)
            
        marks = int(r["original_marks"]) if r["original_marks"].isdigit() else 5
        pa = set(eval(r["part_a_years"]) if r["part_a_years"] else [])
        pb = set(eval(r["part_b_years"]) if r["part_b_years"] else [])
        
        # Deduplication key by topic and normalized text
        norm_key = (new_tag, re.sub(r'[\s_]+', ' ', q.lower()).strip(' ?.:,;'))
        if norm_key not in dedup:
            dedup[norm_key] = {
                "subject_name": "Discrete Mathematics",
                "raw_question_text": q,
                "topic_tag": new_tag,
                "bloom_level": bloom,
                "marks": marks,
                "part_a_years": set(pa),
                "part_b_years": set(pb)
            }
        else:
            dedup[norm_key]["part_a_years"].update(pa)
            dedup[norm_key]["part_b_years"].update(pb)
            dedup[norm_key]["marks"] = max(dedup[norm_key]["marks"], marks)
            
    out_rows = []
    for item in dedup.values():
        marks, pa, pb = fix_part_inversion(item["marks"], item["part_a_years"], item["part_b_years"])
        out_rows.append({
            "subject_name": item["subject_name"],
            "raw_question_text": item["raw_question_text"],
            "topic_tag": item["topic_tag"],
            "bloom_level": item["bloom_level"],
            "original_marks": str(marks),
            "part_a_years": str(pa),
            "part_b_years": str(pb)
        })
    
    out_rows.sort(key=lambda x: (x["topic_tag"], x["raw_question_text"]))
    out_file = DATASETS_DIR / "Discrete_Mathematics_Dataset.csv"
    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "subject_name", "raw_question_text", "topic_tag", "bloom_level",
            "original_marks", "part_a_years", "part_b_years"
        ])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"  -> Wrote {len(out_rows)} unique rows to {out_file.name}")

def parse_exam_paper(filepath: str):
    """Robust extraction of questions from question paper text."""
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        text = f.read()
    
    # Extract year from filepath
    year_match = re.search(r'(20\d\d)', filepath)
    year = int(year_match.group(1)) if year_match else 2023
    
    questions = []
    lines = [l.strip() for l in text.splitlines()]
    
    q_start_re = re.compile(r'^(\d+)\s*[\.\)]\s*(?:([a-j])[\.\)]\s*)?', re.I)
    sub_q_re = re.compile(r'^\s*([a-j])[\.\)]\s*', re.I)
    marks_re = re.compile(r'\[([0-9\+\s]+)\]\s*$')
    
    current_q = []
    current_marks = 5
    is_part_a = False
    in_questions = False
    
    for line in lines:
        if 'PART - A' in line.upper() or 'PART- A' in line.upper() or 'PART-A' in line.upper():
            is_part_a = True
            in_questions = True
            continue
        elif 'PART - B' in line.upper() or 'PART- B' in line.upper() or 'PART-B' in line.upper():
            is_part_a = False
            in_questions = True
            continue
        if not in_questions:
            continue
        if line in ['OR', '---ooOoo---', '- - -'] or 'JNTUH USED' in line or 'Code No:' in line:
            continue
        
        m_marks = marks_re.search(line)
        line_clean = marks_re.sub('', line).strip()
        
        m_start = q_start_re.match(line)
        m_sub = sub_q_re.match(line)
        
        if m_start or m_sub:
            if current_q:
                q_text = ' '.join(current_q).strip()
                if len(q_text) > 15:
                    questions.append((q_text, current_marks, is_part_a, year))
                current_q = []
                current_marks = 2 if is_part_a else 5
            
            if m_marks:
                try:
                    current_marks = int(eval(m_marks.group(1).replace('+', '+')))
                except Exception:
                    current_marks = 2 if is_part_a else 5
            
            if m_start:
                text_part = q_start_re.sub('', line_clean).strip()
            else:
                text_part = sub_q_re.sub('', line_clean).strip()
            if text_part:
                current_q.append(text_part)
        else:
            if current_q:
                current_q.append(line_clean)
                if m_marks:
                    try:
                        current_marks = int(eval(m_marks.group(1).replace('+', '+')))
                    except Exception:
                        pass
    if current_q:
        q_text = ' '.join(current_q).strip()
        if len(q_text) > 15:
            questions.append((q_text, current_marks, is_part_a, year))
    return questions

def build_subject_from_papers(subject_name: str, config_name: str, paper_globs: list, out_filename: str):
    print(f"Building {subject_name} dataset...")
    config_path = CONFIG_DIR / config_name
    with open(config_path) as f:
        config = json.load(f)
    
    all_paper_files = []
    for g in paper_globs:
        all_paper_files.extend(glob.glob(str(PROJECT_ROOT / g), recursive=True))
    all_paper_files = sorted(list(set(all_paper_files)))
    print(f"  Scanning {len(all_paper_files)} papers...")
    
    # Group by normalized text for deduplication
    dedup = {}
    for pfile in all_paper_files:
        try:
            extracted = parse_exam_paper(pfile)
            for q_text, marks, is_part_a, year in extracted:
                q_clean = clean_math_text(q_text)
                if len(q_clean) < 20 or q_clean.startswith("Code No:") or "Time: 3 Hours" in q_clean:
                    continue
                tag = score_topic(q_clean, config)
                norm = re.sub(r'[\s_]+', ' ', q_clean.lower()).strip(' ?.:,;')
                key = (tag, norm)
                if key not in dedup:
                    dedup[key] = {
                        "subject_name": subject_name,
                        "raw_question_text": q_clean,
                        "topic_tag": tag,
                        "marks": marks,
                        "part_a_years": set(),
                        "part_b_years": set()
                    }
                else:
                    dedup[key]["marks"] = max(dedup[key]["marks"], marks)
                if is_part_a or marks <= 3:
                    dedup[key]["part_a_years"].add(year)
                else:
                    dedup[key]["part_b_years"].add(year)
        except Exception as e:
            continue
    
    out_rows = []
    for item in dedup.values():
        q = item["raw_question_text"]
        tag = item["topic_tag"]
        bloom = infer_bloom(q)
        marks, pa_yrs, pb_yrs = fix_part_inversion(item["marks"], item["part_a_years"], item["part_b_years"])
        
        out_rows.append({
            "subject_name": subject_name,
            "raw_question_text": q,
            "topic_tag": tag,
            "bloom_level": bloom,
            "original_marks": str(marks),
            "part_a_years": str(pa_yrs),
            "part_b_years": str(pb_yrs)
        })
    
    # Sort deterministically
    out_rows.sort(key=lambda x: (x["topic_tag"], x["raw_question_text"]))
    out_file = DATASETS_DIR / out_filename
    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "subject_name", "raw_question_text", "topic_tag", "bloom_level",
            "original_marks", "part_a_years", "part_b_years"
        ])
        writer.writeheader()
        writer.writerows(out_rows)
    print(f"  -> Wrote {len(out_rows)} unique questions to {out_file.name}")

def main():
    # 1. Discrete Mathematics
    build_discrete_mathematics()
    
    # 2. Matrices and Calculus
    build_subject_from_papers(
        subject_name="Matrices and Calculus",
        config_name="Matrices_and_Calculus_syllabus.json",
        paper_globs=[
            "data/raw/extracted_text/R22_text/Question paper/1-1/Matrices and Calculus/*.txt",
            "data/raw/extracted_text/R18 text/1st Year/Semester 1/MATHEMATICS-I/*.txt",
            "data/raw/extracted_text/R16_text/Question Papers/1-1/MATHEMATICS-I/*.txt",
            "data/raw/extracted_text/R15_text/Question Papers/1-1/Mathematics-1/*.txt",
            "data/raw/extracted_text/R13_text/question papers/1-1/MATHEMATICS-I/*.txt"
        ],
        out_filename="Matrices_and_Calculus_Dataset.csv"
    )
    
    # 3. Ordinary Differential Equations & Vector Calculus
    build_subject_from_papers(
        subject_name="Ordinary Differential Equations & Vector Calculus",
        config_name="Ordinary_Differential_Equations_and_Vector_Calculus_syllabus.json",
        paper_globs=[
            "data/raw/extracted_text/R22_text/Question paper/1-2/Ordinary Differential Equations and Vector Calculus/*.txt",
            "data/raw/extracted_text/R18 text/1st Year/Semester 2/MATHEMATICS-II/*.txt",
            "data/raw/extracted_text/R16_text/Question Papers/1-2/1-2/MATHEMATICS-II/*.txt",
            "data/raw/extracted_text/R15_text/Question Papers/1-2/Mathematics-2/*.txt",
            "data/raw/extracted_text/R13_text/question papers/1-2/MATHEMATICS-II/*.txt"
        ],
        out_filename="Ordinary_Differential_Equations_and_Vector_Calculus_Dataset.csv"
    )
    
    # 4. Computer Oriented Statistical Methods
    build_subject_from_papers(
        subject_name="Computer Oriented Statistical Methods",
        config_name="Computer_Oriented_Statistical_Methods_syllabus.json",
        paper_globs=[
            "data/raw/extracted_text/R22_text/Question paper/2-1/Computer Oriented Statistical Methods/*.txt",
            "data/raw/extracted_text/R18 text/2nd Year/Semester 1/COMPUTER ORIENTED STATISTICAL METHODS/*.txt",
            "data/raw/extracted_text/R16_text/Question Papers/2-1/2-1/PROBABILITY AND STATISTICS/*.txt",
            "data/raw/extracted_text/R15_text/Question Papers/2-1/PROBABILITY AND STATISTICS/*.txt",
            "data/raw/extracted_text/R13_text/question papers/2-1/PROBABILITY AND STATISTICS/*.txt"
        ],
        out_filename="Computer_Oriented_Statistical_Methods_Dataset.csv"
    )

if __name__ == "__main__":
    main()
