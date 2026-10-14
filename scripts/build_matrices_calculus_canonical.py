#!/usr/bin/env python3
"""
build_matrices_calculus_canonical.py
====================================
Builds the canonical 8-column dataset for Matrices and Calculus / Mathematics-I
across R13, R16, R18, and R22 regulations:
  1. Handles MS Word Symbol and R22 Math PUA characters (mapping \\ue005 -> +, \\ue006 -> -,
     \\ue008 -> =, \\uf0b6 -> ∂, \\uf0d6 -> √, \\ue016 -> ∫, etc.).
  2. Preserves matrix equations, systems of linear equations, Taylor/Maclaurin series,
     and double/triple integrals as Unicode text.
  3. Maps every question to the 5 official syllabus units:
     - Unit I: MATRICES_AND_SYSTEM_OF_EQUATIONS
     - Unit II: EIGENVALUES_AND_EIGENVECTORS
     - Unit III: CALCULUS_AND_MEAN_VALUE_THEOREMS
     - Unit IV: MULTIVARIABLE_CALCULUS_DIFFERENTIATION
     - Unit V: MULTIVARIABLE_CALCULUS_INTEGRATION
  4. 8-column schema:
     subject_name, raw_question_text, topic_tag, bloom_level,
     original_marks, part_a_years, part_b_years, image_path

Output:
  data/processed/subjects/Matrices_and_Calculus_Dataset.csv
"""

import csv
import glob
import re
from pathlib import Path

PUA_REPAIR = {
    # Legacy Word Symbol font (\uf000 - \uf0ff)
    "\uf0ae": "→", "\uf0ac": "¬", "\uf0da": "∧", "\uf0d9": "∨",
    "\uf0db": "↔", "\uf0ab": "↔", "\uf0d8": "¬", "\uf0ce": "∈",
    "\uf0cf": "∉", "\uf0c7": "∩", "\uf0c8": "∪", "\uf0a9": "⊆",
    "\uf0cc": "⊂", "\uf0b9": "≠", "\uf0a3": "≤", "\uf0b3": "≥",
    "\uf0b1": "±", "\uf0b4": "×", "\uf0b8": "÷", "\uf0a5": "∞",
    "\uf0d6": "√", "\uf0e5": "∑", "\uf0d5": "∏", "\uf03d": "=",
    "\uf07e": "~", "\uf028": "(", "\uf029": ")", "\uf05b": "[",
    "\uf05d": "]", "\uf0b6": "∂", "\uf071": "θ", "\uf06c": "λ",
    "": "∧", "": "∨", "": "¬", "": "→", "": "↔", "": "⇔",
    "": "∈", "": "∉", "": "∩", "": "∪", "": "⊆", "": "⊂",
    "": "≠", "": "≤", "": "≥", "": "±", "": "×", "": "÷",
    "": "∞", "": "√", "": "∑", "": "∏", "": "=", "": "{",
    "": "}", "": "(", "": ")", "": "[", "": "]", "": "∃",
    "": "∀", "": "[", "": "]", "": "-", "": "∂", "": "(",
    "": ")", "": "(", "": ")", "": "(", "": ")", "": "Γ",
    # R22 Equation PUA (\ue000 - \ue0ff)
    "\ue005": "+", "\ue006": "-", "\ue008": "=", "\ue007": "±",
    "\ue00b": "λ", "\ue00c": "θ", "\ue00d": "θ", "\ue00e": "≤",
    "\ue012": "(", "\ue013": ")", "\ue014": "[", "\ue015": "]",
    "\ue016": "∫", "\ue017": "∫", "\ue01a": "[", "\ue01b": "]",
    "\ue01c": "[", "\ue01d": "]", "\ue00f": "≥"
}

def clean_question_text(text: str) -> str:
    for k, v in PUA_REPAIR.items():
        text = text.replace(k, v)
    text = re.sub(r"---?[oO0]+---?.*", "", text, flags=re.DOTALL)
    text = re.sub(r"JNTUH USED.*", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"\s*used paper.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*[0-9]{2}-[0-9]{2}-[0-9]{2,4}\s*(AM|PM)?\s*$", "", text)
    text = re.sub(r"\[\d+(?:\+\d+)?\]", "", text)
    text = re.sub(r"^([a-j]|[1-9]|1[0-5])[\.\)]\s*", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def infer_topic(text: str, q_num: int = 0) -> str:
    t = text.lower()
    if any(k in t for k in ["echelon", "normal form", "rank of", "homogeneous", "non-homogeneous", "gauss elimination", "gauss seidel", "gauss-jordan", "system of linear", "consistency", "ax=b", "row elementary"]):
        return "MATRICES_AND_SYSTEM_OF_EQUATIONS"
    if any(k in t for k in ["eigenvalue", "eigen value", "eigenvector", "eigen vector", "cayley-hamilton", "diagonaliz", "quadratic form", "canonical form", "index of", "signature", "orthogonal transformation", "hermitian", "unitary"]):
        return "EIGENVALUES_AND_EIGENVECTORS"
    if any(k in t for k in ["rolle", "lagrange", "mean value theorem", "mvt", "cauchy", "taylor", "maclaurin", "beta and gamma", "beta function", "gamma function", "radius of curvature", "evolute"]):
        return "CALCULUS_AND_MEAN_VALUE_THEOREMS"
    if any(k in t for k in ["partial differential", "partial derivative", "euler’s theorem", "euler theorem", "total derivative", "jacobian", "maxima and minima", "stationary point", "saddle point", "lagrange multiplier"]):
        return "MULTIVARIABLE_CALCULUS_DIFFERENTIATION"
    if any(k in t for k in ["double integral", "triple integral", "change of order", "order of integration", "polar coordinate", "volume of", "area of", "surface area", "multiple integral", "dirichlet integral"]):
        return "MULTIVARIABLE_CALCULUS_INTEGRATION"
    if q_num in [2, 3]:
        return "MATRICES_AND_SYSTEM_OF_EQUATIONS"
    elif q_num in [4, 5]:
        return "EIGENVALUES_AND_EIGENVECTORS"
    elif q_num in [6, 7]:
        return "CALCULUS_AND_MEAN_VALUE_THEOREMS"
    elif q_num in [8, 9]:
        return "MULTIVARIABLE_CALCULUS_DIFFERENTIATION"
    elif q_num in [10, 11]:
        return "MULTIVARIABLE_CALCULUS_INTEGRATION"
    return "MATRICES_AND_SYSTEM_OF_EQUATIONS"

def infer_bloom(text: str) -> str:
    t = text.lower()
    if any(k in t for k in ["verify", "justify", "test for", "examine", "determine", "evaluate whether"]):
        return "Evaluate"
    if any(k in t for k in ["distinguish", "differentiate", "compare", "classify"]):
        return "Analyze"
    if any(k in t for k in ["find", "solve", "calculate", "compute", "reduce", "show that", "prove that", "expand", "change the order", "apply"]):
        return "Apply"
    if any(k in t for k in ["define", "state", "list", "what is", "write"]):
        return "Remember"
    return "Understand"

def normalize_key(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[\s_]+", " ", s).strip(" ?.:,;")
    return s

def build_matrices_calculus_dataset():
    out_dir = Path("data/processed/subjects")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "Matrices_and_Calculus_Dataset.csv"

    papers = glob.glob("temp_data/Text_data/All_Reg_QP_Text_data/**/MATHEMATICS-I/*.txt", recursive=True) + \
             glob.glob("temp_data/Text_data/All_Reg_QP_Text_data/**/Matrices and Calculus/*.txt", recursive=True)
    papers = sorted(list(set(papers)))

    merged = {}

    for p in papers:
        content = Path(p).read_text(encoding="utf-8", errors="replace")
        for k, v in PUA_REPAIR.items():
            content = content.replace(k, v)
            
        year_m = re.search(r"(20\d{2})", Path(p).name)
        year = int(year_m.group(1)) if year_m else 2020

        # Part A
        pa_match = re.search(r"PART\s*[-–]\s*A.*?\n(.*?)PART\s*[-–]\s*B", content, re.DOTALL | re.IGNORECASE)
        if pa_match:
            for m in re.finditer(r"(?:^|\n)\s*(?:1\.)?\s*([a-j])\)\s*(.*?)(?=\n\s*(?:[a-j]\)|\Z|\[\d+\]))", pa_match.group(1), re.DOTALL | re.IGNORECASE):
                qtext = clean_question_text(m.group(2))
                if len(qtext) >= 12 and not qtext.startswith("Code No"):
                    topic = infer_topic(qtext)
                    bloom = infer_bloom(qtext)
                    k = (topic, normalize_key(qtext), "")
                    if k in merged:
                        merged[k]["part_a_years"] = sorted(list(set(merged[k]["part_a_years"] + [year])))
                    else:
                        merged[k] = {
                            "subject_name": "Matrices and Calculus",
                            "raw_question_text": qtext,
                            "topic_tag": topic,
                            "bloom_level": bloom,
                            "original_marks": 2,
                            "part_a_years": [year],
                            "part_b_years": [],
                            "image_path": ""
                        }

        # Part B
        pb_match = re.search(r"PART\s*[-–]\s*B.*?\n(.*)", content, re.DOTALL | re.IGNORECASE)
        if pb_match:
            pb_text = pb_match.group(1)
            q_matches = list(re.finditer(r"(?:^|\n)\s*([2-9]|1[0-1])\.?\s*([ab])?\)\s*(.*?)(?=\n\s*(?:(?:OR\s*)?(?:[2-9]|1[0-1])\.?\s*[ab]?\)|\bOR\b|\Z))", pb_text, re.DOTALL | re.IGNORECASE))
            for m in q_matches:
                q_num = int(m.group(1))
                qtext = clean_question_text(m.group(3))
                if len(qtext) >= 15 and not qtext.startswith("Code No"):
                    topic = infer_topic(qtext, q_num)
                    bloom = infer_bloom(qtext)
                    k = (topic, normalize_key(qtext), "")
                    if k in merged:
                        merged[k]["part_b_years"] = sorted(list(set(merged[k]["part_b_years"] + [year])))
                    else:
                        merged[k] = {
                            "subject_name": "Matrices and Calculus",
                            "raw_question_text": qtext,
                            "topic_tag": topic,
                            "bloom_level": bloom,
                            "original_marks": 5,
                            "part_a_years": [],
                            "part_b_years": [year],
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

    print(f"Generated {out_file.name} with {len(final_rows)} rows.")

if __name__ == "__main__":
    build_matrices_calculus_dataset()
