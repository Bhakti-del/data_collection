import os
import re
import csv

# ── topic taxonomy ────────────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "WATER_HARDNESS_AND_TREATMENT": [
        "hardness", "hard water", "soft water", "temporary hardness", "permanent hardness",
        "edta", "calgon", "lime soda", "zeolite", "ion exchange", "softening",
        "scale", "sludge", "boiler", "caustic embrittlement", "priming", "foaming",
        "potable water", "portable water", "domestic water", "disinfection", "chlorination",
        "ozonation", "reverse osmosis", "defluoridation", "nalgonda", "caco3",
        "ion-selective electrode", "fluoride", "treatment of water", "water quality",
        "water system", "freeze drying", "estimate fluorine", "fluorine in water",
    ],
    "ELECTROCHEMISTRY_AND_BATTERIES": [
        "electrode potential", "nernst", "electrochemical cell", "emf", "galvanic",
        "calomel electrode", "standard electrode", "salt bridge", "electrochemical series",
        "battery", "batteries", "lead acid", "lithium ion", "li-ion", "ni-cd", "nickel",
        "zn-air", "zinc air", "fuel cell", "hydrogen fuel",
        "charging", "discharging", "primary battery", "secondary battery",
        "quinhydrone", "glass electrode", "molar conductance", "molar conductivity",
        "conductivity", "conductance", "standard hydrogen electrode", "ph",
        "pilling-bedworth",
    ],
    "CORROSION": [
        "corrosion", "rusting", "rust", "pitting", "galvanic corrosion",
        "cathodic protection", "anodic", "sacrificial anode", "impressed current",
        "galvanizing", "tinning", "electroplating", "electroless plating",
        "anodic coating", "cathodic coating", "rate of corrosion", "factors affecting corrosion",
        "chemical corrosion", "electrochemical corrosion", "surface coating", "paint",
        "paints", "constituents of paint",
    ],
    "POLYMERS_AND_PLASTICS": [
        "polymer", "polymerization", "monomer", "thermoplastic", "thermosetting",
        "bakelite", "teflon", "pvc", "polyvinyl", "dacron", "terylene", "nylon",
        "polylactic acid", "pla", "biodegradable polymer", "conducting polymer",
        "frp", "fibre reinforced", "tacticity", "isotactic", "syndiotactic", "atactic",
        "free radical", "step growth", "addition polymerization", "condensation",
        "functionality", "molecular weight", "degree of polymerization",
        "polyacrylamide", "polyacryl", "poly acetylene", "polylactic", "poly l-lactic",
        "conduction in poly", "conducting polymer", "doping", "effect of doping",
        "terelene",
    ],
    "RUBBER": [
        "rubber", "vulcanization", "natural rubber", "synthetic rubber",
        "butyl rubber", "thiokol", "styrene rubber", "buna", "neoprene",
        "elastomer",
    ],
    "FUELS_AND_COMBUSTION": [
        "fuel", "coal", "calorific value", "hcv", "lcv", "gross calorific", "net calorific",
        "dulong", "proximate analysis", "ultimate analysis", "fixed carbon",
        "volatile matter", "moisture", "ash", "coke", "petroleum", "crude oil",
        "fractional distillation", "cracking", "catalytic cracking", "moving bed",
        "fixed bed", "fischer-tropsch", "synthetic petrol", "gasoline",
        "lpg", "cng", "natural gas", "biodiesel", "transesterification",
        "octane number", "cetane", "knocking", "refining", "flue gas", "orsat",
        "ignition temperature", "bergius", "methanol fuel",
    ],
    "LUBRICANTS": [
        "lubricant", "lubrication", "viscosity", "viscosity index",
        "flash point", "fire point", "cloud point", "pour point",
        "thick film", "thin film", "boundary lubrication", "extreme pressure",
        "additives", "grease", "mechanism of lubrication",
    ],
    "CEMENT_AND_REFRACTORIES": [
        "cement", "portland cement", "setting of cement", "hardening of cement",
        "gypsum", "refractory", "refractories", "classification of refractories",
        "shape memory", "smart material", "refractoriness", "rul test",
        "annealing", "hardening", "normalization", "heat treatment",
        "composites", "composite material", "classification of composites",
    ],
    "PHASE_RULE_AND_COLLOIDS": [
        "phase rule", "phase diagram", "gibbs", "triple point", "condensed phase",
        "iron carbon", "lead silver", "one component", "two component",
        "colloid", "colloidal", "adsorption", "langmuir", "freundlich",
        "tyndall", "tyndal", "coagulation", "emulsion", "micelle", "miscelle",
        "electrophoresis", "electrophoreses", "degree of freedom", "eutectic",
        "physisorption", "chemisorption", "isotherm", "component", "phase",
    ],
    "NANOMATERIALS": [
        "nanomaterial", "nano material", "nanoparticle", "nanotube",
        "carbon nanotube", "cnt", "chemical vapour deposition", "cvd",
        "sol-gel", "sol gel", "nanoscale", "nano",
        "magnetic resonance imaging", "mri",
    ],
    "MOLECULAR_ORBITAL_THEORY": [
        "molecular orbital", "lcao", "bonding orbital", "antibonding orbital",
        "bond order", "crystal field", "crystal field splitting", "d-orbital",
        "octahedral", "tetrahedral", "band structure", "energy level diagram",
        "n2 molecule", "o2 molecule", "ligand",
    ],
    "ORGANIC_REACTIONS_AND_STEREOCHEMISTRY": [
        "sn1", "sn2", "nucleophilic substitution", "elimination", "dehydrohalogenation",
        "markownikoff", "grignard", "carbonyl", "oxidation", "reduction", "lialth4",
        "kmno4", "isomerism", "optical isomer", "enantiomer", "diastereomer",
        "stereochemistry", "conformation", "butane conformation", "tartaric acid",
        "chirality", "racemic", "optical activity", "specific rotation", "lactic acid",
        "aspirin", "hydroboration", "olefin", "hbr", "propene", "alkyl halide",
        "fundamental vibration", "hcn", "ch4",
    ],
    "SPECTROSCOPY": [
        "spectroscopy", "ir spectroscopy", "uv spectroscopy", "nmr", "nuclear magnetic resonance",
        "infrared", "ultraviolet", "lambert-beer", "beer lambert", "electronic transition",
        "molecular vibration", "shielding", "deshielding", "chemical shift",
        "selection rule", "absorption", "chromophore", "ir radiation", "ir energy",
        "methane does not absorb",
    ],
}

def classify_topic(text):
    text_lower = text.lower()
    scores = {topic: 0 for topic in TOPIC_KEYWORDS}
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[topic] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "GENERAL_CHEMISTRY"

def classify_bloom(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["design", "propose", "synthesize", "formulate", "create", "develop"]):
        return "Create"
    if any(w in text_lower for w in ["evaluate", "justify", "assess", "critique", "recommend"]):
        return "Evaluate"
    if any(w in text_lower for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                                      "contrast", "examine", "investigate"]):
        return "Analyze"
    if any(w in text_lower for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                                      "illustrate", "write a program", "write a java", "write a code",
                                      "write a python", "solve", "determine"]):
        return "Apply"
    if any(w in text_lower for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                                      "summarize", "outline", "give an account", "briefly"]):
        return "Understand"
    return "Remember"

def extract_year_from_filename(filename):
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else None

def parse_marks(text):
    m = re.search(r'\[(\d+)\]', text)
    if m:
        return int(m.group(1))
    if re.search(r'\[5\+5\]', text):
        return 5
    if re.search(r'\[10\]', text):
        return 10
    return None

def clean_question(text):
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def split_subquestions(block):
    """Split a Part-B block like '2.a) ... b) ...' into individual sub-questions."""
    parts = re.split(r'\n(?=[a-c]\))', block)
    return [p.strip() for p in parts if p.strip()]

def extract_part_a(text, year):
    rows = []
    part_a_match = re.search(r'PART[\s\-–]*A(.*?)PART[\s\-–]*B', text, re.DOTALL | re.IGNORECASE)
    if not part_a_match:
        return rows
    part_a = part_a_match.group(1)
    # Each sub-question: letter) text [marks]
    questions = re.findall(r'[a-j]\)\s*(.*?)(?=\n[a-j]\)|\Z)', part_a, re.DOTALL)
    for q in questions:
        q = q.strip()
        if not q or len(q) < 8:
            continue
        marks = parse_marks(q) or 2
        q_clean = clean_question(q)
        if not q_clean:
            continue
        rows.append({
            "subject_name": "Engineering Chemistry",
            "raw_question_text": q_clean,
            "topic_tag": classify_topic(q_clean),
            "bloom_level": classify_bloom(q_clean),
            "original_marks": marks,
            "part_a_years": f"[{year}]",
            "part_b_years": "[]",
        })
    return rows

def extract_part_b(text, year):
    rows = []
    part_b_match = re.search(r'PART[\s\-–]*B(.*)', text, re.DOTALL | re.IGNORECASE)
    if not part_b_match:
        return rows
    part_b = part_b_match.group(1)
    # Split on question numbers like "2." "3." etc.
    blocks = re.split(r'\n(?=\d{1,2}\.)', part_b)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        # Determine marks from [5+5] or [10] pattern
        if re.search(r'\[5\+5\]', block):
            marks = 5
        elif re.search(r'\[10\]', block):
            marks = 10
        elif re.search(r'\[4\+3\+3\]|\[3\+4\+3\]|\[4\+4\+2\]|\[3\+3\+4\]', block):
            marks = 5
        else:
            marks = 5  # default for Part-B

        # Split into sub-questions a), b), c)
        sub_parts = re.split(r'\n(?=[a-c]\))', block)
        for part in sub_parts:
            part = part.strip()
            # Remove leading question number like "2." or "2.a)"
            part = re.sub(r'^\d{1,2}\.\s*', '', part)
            part = re.sub(r'^[a-c]\)\s*', '', part)
            part = part.strip()
            if not part or len(part) < 10:
                continue
            q_clean = clean_question(part)
            if not q_clean:
                continue
            rows.append({
                "subject_name": "Engineering Chemistry",
                "raw_question_text": q_clean,
                "topic_tag": classify_topic(q_clean),
                "bloom_level": classify_bloom(q_clean),
                "original_marks": marks,
                "part_a_years": "[]",
                "part_b_years": f"[{year}]",
            })
    return rows

def process_file(filepath):
    year = extract_year_from_filename(os.path.basename(filepath))
    if not year:
        return []
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    rows = extract_part_a(text, year) + extract_part_b(text, year)
    return rows

def collect_all_files(base_dirs):
    files = []
    for base in base_dirs:
        for root, _, fnames in os.walk(base):
            for fname in fnames:
                if fname.endswith(".txt"):
                    files.append(os.path.join(root, fname))
    return files

BASE = "/home/admin1/WingsAI/group_2/DATA/Question_Paper_Generator/question-paper-predictor/data/cleaned_papers"
CHEM_DIRS = [
    os.path.join(BASE, "R13_text/question papers/1-1/ENGINEERING CHEMISTRY"),
    os.path.join(BASE, "R15_text/Question Papers/1-1/ENGINEERING CHEMISTRY"),
    os.path.join(BASE, "R16_text/Question Papers/1-1/ENGINEERING CHEMISTRY"),
    os.path.join(BASE, "R18 text/1st Year/Semester 1/CHEMISTRY"),
    os.path.join(BASE, "R18 text/1st Year/Semester 2/CHEMISTRY"),
    os.path.join(BASE, "R22_text/Question paper/1-1/Engineering Chemistry"),
]

all_rows = []
for f in collect_all_files(CHEM_DIRS):
    all_rows.extend(process_file(f))

# Merge duplicate questions: same text → combine years
from collections import defaultdict
merged = defaultdict(lambda: {"part_a_years": set(), "part_b_years": set(), "meta": None})
for row in all_rows:
    key = row["raw_question_text"].strip().lower()
    if merged[key]["meta"] is None:
        merged[key]["meta"] = row
    if row["part_a_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_a_years"])
        if yr:
            merged[key]["part_a_years"].add(int(yr.group()))
    if row["part_b_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_b_years"])
        if yr:
            merged[key]["part_b_years"].add(int(yr.group()))

final_rows = []
for key, val in merged.items():
    row = val["meta"].copy()
    pa = sorted(val["part_a_years"])
    pb = sorted(val["part_b_years"])
    row["part_a_years"] = str(pa) if pa else "[]"
    row["part_b_years"] = str(pb) if pb else "[]"
    final_rows.append(row)

# ── filter out garbage / fragment rows ───────────────────────────────────────
GARBAGE_PATTERNS = [
    r'^\(\s*\d+\s*marks\s*\)$',
    r'^define the following',
    r'^explain the following',
    r'^write short notes? on:?$',
    r'^\w+\s+b\)\s+\w+\s+c\)',
    r'^--',
    r'^ or$',
    r'^\d+\s+marks',
]

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 12:
        return True
    for pat in GARBAGE_PATTERNS:
        if re.search(pat, t):
            return True
    return False

final_rows = [r for r in final_rows if not is_garbage(r["raw_question_text"])]

# Manual overrides for residual misclassifications
OVERRIDES = {
    "give brief note on trans esterification.": "FUELS_AND_COMBUSTION",
    "give the molecular energy diagrams of o2.": "MOLECULAR_ORBITAL_THEORY",
}
for r in final_rows:
    key = r["raw_question_text"].strip().lower()
    if key in OVERRIDES:
        r["topic_tag"] = OVERRIDES[key]

# Sort by topic then bloom level
final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

OUT = "/home/admin1/WingsAI/group_2/DATA/Question_Paper_Generator/question-paper-predictor/data/Engineering_Chemistry_Dataset.csv"
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level", "original_marks", "part_a_years", "part_b_years"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)

print(f"Done. {len(final_rows)} unique questions written to {OUT}")
