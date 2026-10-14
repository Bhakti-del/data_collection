#!/usr/bin/env python3
"""
build_mfcs_canonical.py
=======================
Builds the canonical, consolidated 8-column dataset for Mathematical Foundations of
Computer Science (MFCS), fully resolving all historical defects:
  1. Full Unicode preservation for logic and mathematical formulas (no garbled deletion).
  2. Integration of all 5 Units (I: Mathematical Logic, II: Relations & Lattices,
     III: Combinatorics, IV: Recurrence Relations, V: Graph Theory).
  3. Resolution of image collision on MayJune - 2019 Q11.a (distinct images for R13 dual
     and R16 graph isomorphism).
  4. Fix typo on disk and CSV for AugustSeptember-2022_Q8_b.
  5. Alignment of topic tags strictly to MATHEMATICAL_FOUNDATIONS_OF_COMPUTER_SCIENCE_syllabus.json.
  6. Calibration of Bloom taxonomy (shortest path -> Apply, Euler circuit -> Apply).
  7. Proper marks calibration (eliminating marks inversion defects).

Output:
  data/processed/subjects/Mathematical_Foundations_of_Computer_Science_Dataset.csv
"""

import csv
import re
from pathlib import Path

# Legacy Word PUA font map to standard Unicode characters
PUA_REPAIR = {
    "\uf0ae": "→", "\uf0ac": "¬", "\uf0da": "∧", "\uf0d9": "∨",
    "\uf0db": "↔", "\uf0ab": "↔", "\uf0d8": "¬", "\uf0ce": "∈",
    "\uf0cf": "∉", "\uf0c7": "∩", "\uf0c8": "∪", "\uf0a9": "⊆",
    "\uf0cc": "⊂", "\uf0b9": "≠", "\uf0a3": "≤", "\uf0b3": "≥",
    "\uf0b1": "±", "\uf0b4": "×", "\uf0b8": "÷", "\uf0a5": "∞",
    "\uf0d6": "√", "\uf0e5": "∑", "\uf0d5": "∏", "\uf03d": "=",
    "\uf07e": "~", "\uf028": "(", "\uf029": ")", "\uf05b": "[",
    "\uf05d": "]", "": "∧", "": "∨", "": "¬", "": "→",
    "": "↔", "": "⇔", "": "∈", "": "∉", "": "∩", "": "∪",
    "": "⊆", "": "⊂", "": "≠", "": "≤", "": "≥", "": "±",
    "": "×", "": "÷", "": "∞", "": "√", "": "∑", "": "∏",
    "": "=", "": "{", "": "}", "": "(", "": ")", "": "[",
    "": "]", "": "∃", "": "∀", "": "[", "": "]", "": "-"
}

# Strict alignment to MATHEMATICAL_FOUNDATIONS_OF_COMPUTER_SCIENCE_syllabus.json
TOPIC_STANDARDIZATION = {
    # Unit 1: Mathematical Logic
    "PROPOSITIONAL_LOGIC": "MATHEMATICAL_LOGIC",
    "NORMAL_FORMS_DNF_CNF": "NORMAL_FORMS",
    "LOGICAL_EQUIVALENCES_AND_IDENTITIES": "EQUIVALENCE_IMPLICATION",
    "THEORY_OF_INFERENCE": "MATHEMATICAL_LOGIC",
    "PREDICATE_LOGIC": "MATHEMATICAL_LOGIC",
    "SET_THEORY_BASICS": "STATEMENTS_NOTATIONS",
    # Unit 2: Relations & Lattices
    "RELATIONS_DEFINITION_AND_TYPES": "PROPERTIES_BINARY_RELATIONS",
    "EQUIVALENCE_RELATION": "EQUIVALENCE",
    "HASSE_DIAGRAM": "HASSE_DIAGRAM",
    "LATTICE": "LATTICES",
    "ALGEBRAIC_STRUCTURES": "COMPATIBILITY_PARTIAL_ORDERING_RELATIONS",
    # Unit 3: Combinatorics
    "BASIC_COUNTING_PRINCIPLES": "BASIS_COUNTING",
    "PERMUTATIONS_AND_COMBINATIONS": "COMBINATIONS_PERMUTATIONS",
    "PIGEONHOLE_PRINCIPLE": "BASIS_COUNTING",
    "INCLUSION_EXCLUSION_PRINCIPLE": "PRINCIPLES_INCLUSION",
    "BINOMIAL_THEOREM": "BINOMIAL_MULTINOMIAL_THEOREMS",
    # Unit 4: Recurrence Relations
    "GENERATING_FUNCTIONS": "GENERATING_FUNCTIONS",
    "LINEAR_RECURRENCE_RELATIONS": "RECURRENCE_RELATIONS",
    "NON_HOMOGENEOUS_RECURRENCE_RELATIONS": "SOLVING_RECURRENCE_RELATION_SUBSTITUTION",
    # Unit 5: Graph Theory
    "CHROMATIC_NUMBER_AND_GRAPH_COLORING": "GRAPH_THEORY_APPLICATIONS",
    "GRAPH_COLORING_AND_CHROMATIC_NUMBER": "GRAPH_THEORY_APPLICATIONS",
    "EULER_CIRCUITS_AND_PATHS": "MULTI_GRAPHS_EULER_CIRCUITS",
    "EULER_GRAPH_AND_PATH": "MULTI_GRAPHS_EULER_CIRCUITS",
    "HAMILTONIAN_CYCLES_AND_PATHS": "HAMILTONIAN_GRAPHS",
    "HAMILTONIAN_GRAPH_AND_PATH": "HAMILTONIAN_GRAPHS",
    "PLANAR_AND_DUAL_GRAPHS": "PLANAR_GRAPHS",
    "PLANAR_GRAPHS": "PLANAR_GRAPHS",
    "MINIMAL_SPANNING_TREES": "SPANNING_TREES",
    "SPANNING_TREE": "SPANNING_TREES",
    "SHORTEST_PATH_IN_GRAPHS": "GRAPH_THEORY_APPLICATIONS",
    "GRAPH_ISOMORPHISM": "ISOMORPHISM_SUB_GRAPHS",
    "ISOMORPHIC_GRAPHS": "ISOMORPHISM_SUB_GRAPHS",
    "GRAPH_BASICS_AND_TERMINOLOGY": "GRAPH_THEORY",
}

def clean_question_text(text: str) -> str:
    for k, v in PUA_REPAIR.items():
        text = text.replace(k, v)
    text = re.sub(r"\s*---?oo[Oo0]+---?\s*$", "", text)
    text = re.sub(r"\s*used paper.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*JNTUH USED.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*[0-9]{2}-[0-9]{2}-[0-9]{2,4}\s*(AM|PM)?\s*$", "", text)
    text = re.sub(r"\[\d+(?:\+\d+)?\]", "", text)
    text = re.sub(r"^([a-j]|[1-9]|1[0-5])[\.\)]\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def parse_years(ystr) -> list:
    if isinstance(ystr, list):
        return sorted(list(set(int(y) for y in ystr)))
    years = re.findall(r"\b\d{4}\b", str(ystr))
    return sorted(list(set(int(y) for y in years)))

def normalize_key(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[\s_]+", " ", s).strip(" ?.:,;")
    return s

def build_mfcs_dataset():
    src_text = Path("temp_data/MFCS_Dataset.csv")
    src_img = Path("data/datasets_with_images/Mathematical_Foundations_Of_Computer_Science_Dataset_with_images.csv")
    out_dir = Path("data/processed/subjects")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "Mathematical_Foundations_of_Computer_Science_Dataset.csv"

    merged = {}

    # 1. Process base text questions (covers Units I - IV and text Unit V)
    if src_text.exists():
        with open(src_text, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        for r in reader:
            q = clean_question_text(r["raw_question_text"])
            if len(q) < 10:
                continue
            raw_topic = r["topic_tag"].strip()
            topic = TOPIC_STANDARDIZATION.get(raw_topic, raw_topic)
            bloom = r["bloom_level"].strip()
            marks = int(r["original_marks"])
            pa = parse_years(r["part_a_years"])
            pb = parse_years(r["part_b_years"])

            # Calibrate marks with part categorization
            if marks <= 3 and pb and not pa:
                marks = 5
            elif marks >= 8 and pa and not pb:
                marks = 3

            # Calibrate Bloom taxonomy
            if "shortest path" in q.lower():
                bloom = "Apply"
            elif "euler" in q.lower() and ("find" in q.lower() or "determine" in q.lower()):
                bloom = "Apply"

            k = (topic, normalize_key(q), "")
            if k in merged:
                merged[k]["part_a_years"] = sorted(list(set(merged[k]["part_a_years"] + pa)))
                merged[k]["part_b_years"] = sorted(list(set(merged[k]["part_b_years"] + pb)))
            else:
                merged[k] = {
                    "subject_name": "Mathematical Foundations of Computer Science",
                    "raw_question_text": q,
                    "topic_tag": topic,
                    "bloom_level": bloom,
                    "original_marks": marks,
                    "part_a_years": pa,
                    "part_b_years": pb,
                    "image_path": ""
                }

    # 2. Process image questions (Unit V Graph Theory diagrams)
    if src_img.exists():
        with open(src_img, "r", encoding="utf-8") as f:
            reader = list(csv.DictReader(f))
        for r in reader:
            q = clean_question_text(r["raw_question_text"])
            img = r["image_path"].strip()

            # Fix typo in AugustSeptember image name
            if "AugustSpetember-2022_Q8_b.png" in img:
                img = "data/images/Mathematical Foundations Of Computer Science/MATHEMATICAL_FO_AugustSeptember-2022_Q8_b_r16.png"

            # Resolve image collision on MayJune - 2019 Q11.a
            if "MayJune - 2019_Q11_a.png" in img:
                if "dual" in q.lower():
                    img = "data/images/Mathematical Foundations Of Computer Science/MATHEMATICAL_FO_R13_MayJune - 2019_Q11_a_dual.png"
                elif "isomorphic" in q.lower():
                    img = "data/images/Mathematical Foundations Of Computer Science/MATHEMATICAL_FO_R16_MayJune - 2019_Q11_a_isomorphism.png"

            raw_topic = r["topic_tag"].strip()
            topic = TOPIC_STANDARDIZATION.get(raw_topic, raw_topic)
            bloom = r["bloom_level"].strip()
            marks = int(r["original_marks"])
            pa = parse_years(r["part_a_years"])
            pb = parse_years(r["part_b_years"])
            if marks <= 3 and pb and not pa:
                marks = 5

            # Calibrate Bloom taxonomy
            if "shortest path" in q.lower():
                bloom = "Apply"
            elif "euler" in q.lower() and ("find" in q.lower() or "determine" in q.lower()):
                bloom = "Apply"

            # Search for existing text entry by text key regardless of initial topic
            matched_text_k = None
            norm_q = normalize_key(q)
            for k in list(merged.keys()):
                if k[1] == norm_q and k[2] == "":
                    matched_text_k = k
                    break

            img_k = (topic, norm_q, img)

            if matched_text_k:
                entry = merged.pop(matched_text_k)
                entry["topic_tag"] = topic  # Use more specific topic tag from image dataset
                entry["image_path"] = img
                entry["part_a_years"] = sorted(list(set(entry["part_a_years"] + pa)))
                entry["part_b_years"] = sorted(list(set(entry["part_b_years"] + pb)))
                entry["original_marks"] = marks
                merged[img_k] = entry
            elif img_k in merged:
                merged[img_k]["part_a_years"] = sorted(list(set(merged[img_k]["part_a_years"] + pa)))
                merged[img_k]["part_b_years"] = sorted(list(set(merged[img_k]["part_b_years"] + pb)))
            else:
                merged[img_k] = {
                    "subject_name": "Mathematical Foundations of Computer Science",
                    "raw_question_text": q,
                    "topic_tag": topic,
                    "bloom_level": bloom,
                    "original_marks": marks,
                    "part_a_years": pa,
                    "part_b_years": pb,
                    "image_path": img
                }

    # 3. Add previously dropped high-value mathematical questions
    recovered = [
        ("Obtain principal conjunctive normal form (PCNF) for the formula (~p → r) ∧ (q ↔ p).", "NORMAL_FORMS", "Apply", 5, [], [2021]),
        ("Show that ((P ∨ Q) ∧ ¬(¬P ∧ (¬Q ∨ ¬R))) ∨ (¬P ∧ ¬Q) ∨ (¬Q ∧ ¬R) is a tautology.", "MATHEMATICAL_LOGIC", "Apply", 10, [], [2018]),
        ("In a lattice (L, ≤, ∧, ∨), state and prove the laws idempotent, commutative, associative and absorption.", "LATTICES", "Understand", 5, [], [2018]),
        ("Solve the recurrence relation an - 5 an-1 + 8 an-2 - 4 an-3 = 0 for n ≥ 3, given a0 = 1 and a1 = 0.", "RECURRENCE_RELATIONS", "Apply", 10, [], [2021]),
        ("Construct a truth table to show that (p ∧ q) → p is a tautology.", "MATHEMATICAL_LOGIC", "Understand", 3, [2018], [])
    ]
    for q, topic, bloom, marks, pa, pb in recovered:
        k = (topic, normalize_key(q), "")
        if k not in merged:
            merged[k] = {
                "subject_name": "Mathematical Foundations of Computer Science",
                "raw_question_text": q,
                "topic_tag": topic,
                "bloom_level": bloom,
                "original_marks": marks,
                "part_a_years": pa,
                "part_b_years": pb,
                "image_path": ""
            }

    final_rows = sorted(list(merged.values()), key=lambda x: (x["topic_tag"], x["raw_question_text"]))

    fieldnames = [
        "subject_name", "raw_question_text", "topic_tag", "bloom_level",
        "original_marks", "part_a_years", "part_b_years", "image_path"
    ]

    with open(out_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in final_rows:
            writer.writerow({
                **r,
                "part_a_years": str(r["part_a_years"]),
                "part_b_years": str(r["part_b_years"]),
            })

    print(f"Generated {out_file.name} with {len(final_rows)} rows ({sum(1 for r in final_rows if r['image_path'])} with images).")

if __name__ == "__main__":
    build_mfcs_dataset()
