"""
build_ann_dataset.py
Parses JNTUH Artificial Neural Networks / Neural Networks and Deep Learning
question paper .txt files (R16, R18) and produces
Artificial_Neural_Networks_Dataset.csv.

Topic tags from R16 ANN syllabus:
  Unit I  : NEURON_MODELS_AND_LEARNING
  Unit II : SUPERVISED_LEARNING_AND_PERCEPTRON
  Unit III: BACKPROPAGATION_AND_MLFF
  Unit IV : SELF_ORGANIZING_MAPS
  Unit V  : NEURODYNAMICS_AND_HOPFIELD
"""

import os, re, csv
from collections import defaultdict

TOPIC_KEYWORDS = {
    "NEURON_MODELS_AND_LEARNING": [
        "model of a neuron", "models of neuron", "neuron model",
        "building blocks of neural", "active building blocks",
        "current mirror", "inverter based neuron",
        "neural network architecture", "network architecture",
        "directed graph", "neural networks viewed as",
        "knowledge representation", "credit assignment",
        "memory based learning", "hebbian learning",
        "boltzmann learning", "competitive learning",
        "statistical nature of learning", "learning process",
        "error correction learning", "boltzmann",
        "neural network with human brain", "compare neural",
        "artificial intelligence and neural", "learning rules",
        "stochastic learning", "unsupervised learning",
    ],
    "SUPERVISED_LEARNING_AND_PERCEPTRON": [
        "perceptron", "perceptron convergence theorem",
        "single layer perceptron", "adaptive filtering",
        "least mean square", "lms algorithm", "widrow-hoff",
        "linear least square", "unconstrained optimization",
        "learning curves", "bayes classifier",
        "perceptron and bayes", "gaussian environment",
        "delta rule", "decision surface", "linear separability",
        "feature detection", "supervised learning",
        "xor problem", "multilayer perceptron",
        "multi-layer perceptron", "multilayer feedforward",
    ],
    "BACKPROPAGATION_AND_MLFF": [
        "back propagation", "backpropagation", "bp algorithm",
        "back propagation algorithm", "weight update",
        "heuristics in bp", "heuristics for back",
        "learning rate", "momentum", "accelerated convergence",
        "cross validation", "generalization",
        "hessian matrix", "second order method",
        "gauss-newton", "network pruning", "pruning techniques",
        "optimal brain surgeon", "optimal brain damage",
        "virtues of back propagation", "limitations of back propagation",
        "back propagation and differentiation",
        "radial basis function", "rbf network",
    ],
    "SELF_ORGANIZING_MAPS": [
        "self organizing map", "self-organizing map", "som",
        "kohonen", "unsupervised learning",
        "feature mapping", "basic feature mapping",
        "learning vector quantization", "lvq",
        "adaptive pattern classification",
        "competitive learning",
        "winner takes all", "neighborhood function",
        "topology preserving", "som algorithm",
        "properties of feature map", "computer simulation",
        "formation of self-organizing", "three essential processes",
        "kohonen network",
    ],
    "NEURODYNAMICS_AND_HOPFIELD": [
        "hopfield", "hopfield network", "hopfield model",
        "recurrent network", "attractor", "attractors",
        "attractor neural network", "equilibrium state",
        "stability of equilibrium", "dynamical system",
        "dynamic system", "neuro-dynamical", "neurodynamics",
        "lyapunov", "energy function", "basin of attraction",
        "manipulation of attractors", "recurrent network paradigm",
        "additive model", "cohen-grossberg", "boltzmann machine",
        "associative memory", "storage algorithm", "retrieval algorithm",
        "modes of operation of hopfield", "information in hopfield",
        "neuro dynamic models",
    ],
}

def classify_topic(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "NEURON_MODELS_AND_LEARNING"

def classify_bloom(text):
    t = text.lower()
    if any(w in t for w in ["design", "propose", "formulate", "create a", "develop a"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                             "contrast", "examine", "derive"]):
        return "Analyze"
    if any(w in t for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                             "illustrate", "write a program", "solve", "construct",
                             "prove", "state and prove"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "briefly", "how does", "how is", "how are",
                             "how can", "how to", "what are the", "list and explain",
                             "write about", "write in detail", "write brief"]):
        return "Understand"
    return "Remember"

def extract_year(filename):
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else None

def parse_marks(text):
    m = re.search(r'\[(\d+)\+(\d+)\]', text)
    if m: return max(int(m.group(1)), int(m.group(2)))
    m = re.search(r'\[(\d+)\]', text)
    if m: return int(m.group(1))
    return None

def clean_q(text):
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'used paper.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'r\d{2} used paper.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+OR\s*$', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

IMAGE_PATS = [r'neat (sketch|diagram|figure)', r'shown in (the )?figure',
              r'draw (a neat|and explain)', r'given below']

def is_image(text):
    return any(re.search(p, text.lower()) for p in IMAGE_PATS)

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 12: return True
    return any(re.search(p, t) for p in [
        r'^\(\s*\d+\s*marks\s*\)$', r'^used paper', r'^---', r'^ or$',
        r'^--oo', r'^part\s*[ab]', r'^or$',
    ])

def extract_part_a(text, year, subject_name):
    rows = []
    m = re.search(r'PART[\s\-–]*A(.*?)PART[\s\-–]*B', text, re.DOTALL | re.IGNORECASE)
    if not m: return rows
    for q in re.findall(r'[a-j]\)\s*(.*?)(?=\n[a-j]\)|\Z)', m.group(1), re.DOTALL):
        q = q.strip()
        if not q or len(q) < 8: continue
        marks = parse_marks(q) or 2
        q = clean_q(q)
        if not q or is_garbage(q) or is_image(q): continue
        rows.append({"subject_name": subject_name, "raw_question_text": q,
                     "topic_tag": classify_topic(q), "bloom_level": classify_bloom(q),
                     "original_marks": marks, "part_a_years": f"[{year}]", "part_b_years": "[]"})
    return rows

def extract_part_b(text, year, subject_name):
    rows = []
    m = re.search(r'PART[\s\-–]*B(.*)', text, re.DOTALL | re.IGNORECASE)
    if not m: return rows
    for block in re.split(r'\n(?=\d{1,2}[\.\)])', m.group(1)):
        block = block.strip()
        if not block: continue
        marks = (5 if re.search(r'\[5\+5\]', block) else
                 8 if re.search(r'\[7\+8\]|\[8\+7\]', block) else
                 10 if re.search(r'\[10\]', block) else
                 15 if re.search(r'\[15\]', block) else 5)
        for part in re.split(r'\n(?=[a-c]\))', block):
            part = re.sub(r'^\d{1,2}[\.\)]\s*', '', part.strip())
            part = re.sub(r'^[a-c]\)\s*', '', part).strip()
            if not part or len(part) < 10: continue
            q = clean_q(part)
            if not q or is_garbage(q) or is_image(q): continue
            rows.append({"subject_name": subject_name, "raw_question_text": q,
                         "topic_tag": classify_topic(q), "bloom_level": classify_bloom(q),
                         "original_marks": marks, "part_a_years": "[]", "part_b_years": f"[{year}]"})
    return rows

def extract_no_parta(text, year, subject_name):
    rows = []
    text = re.sub(r'^.*?(NEURAL NETWORKS.*?|ARTIFICIAL NEURAL.*?)\n', '',
                  text, flags=re.DOTALL | re.IGNORECASE, count=1)
    for block in re.split(r'\n(?=\d{1,2}[\.\)])', text):
        block = block.strip()
        if not block: continue
        marks = (8 if re.search(r'\[7\+8\]|\[8\+7\]', block) else
                 15 if re.search(r'\[15\]', block) else
                 5 if re.search(r'\[5\+5\]', block) else
                 10 if re.search(r'\[10\]', block) else 15)
        for part in re.split(r'\n(?=[a-c]\))', block):
            part = re.sub(r'^\d{1,2}[\.\)]\s*', '', part.strip())
            part = re.sub(r'^[a-c]\)\s*', '', part).strip()
            if not part or len(part) < 10: continue
            q = clean_q(part)
            if not q or is_garbage(q) or is_image(q): continue
            rows.append({"subject_name": subject_name, "raw_question_text": q,
                         "topic_tag": classify_topic(q), "bloom_level": classify_bloom(q),
                         "original_marks": marks, "part_a_years": "[]", "part_b_years": f"[{year}]"})
    return rows

def process_file(filepath, subject_name):
    year = extract_year(os.path.basename(filepath))
    if not year: return []
    text = open(filepath, encoding="utf-8", errors="ignore").read()
    has_parta = bool(re.search(r'PART[\s\-–]*A', text, re.IGNORECASE))
    if has_parta:
        return extract_part_a(text, year, subject_name) + extract_part_b(text, year, subject_name)
    return extract_no_parta(text, year, subject_name)

BASE = os.path.join(os.path.dirname(__file__), "cleaned_papers")
DIRS = [
    (os.path.join(BASE, "R16_text/Question Papers/3-2/ARTIFICIAL NEURAL NETWORKS"), "Artificial Neural Networks"),
    (os.path.join(BASE, "R16_text/Question Papers/4-2/NEURAL NETWORKS AND DEEP LEARNING"), "Artificial Neural Networks"),
    (os.path.join(BASE, "R18 text/4th Year/Semester 2/NEURAL NETWORKS AND DEEP LEARNING"), "Artificial Neural Networks"),
]

all_rows = []
for d, sname in DIRS:
    if not os.path.isdir(d):
        print(f"[SKIP] {d}"); continue
    for fname in sorted(os.listdir(d)):
        if fname.endswith(".txt"):
            rows = process_file(os.path.join(d, fname), sname)
            print(f"  {fname}: {len(rows)} questions")
            all_rows.extend(rows)

merged = defaultdict(lambda: {"part_a_years": set(), "part_b_years": set(), "meta": None})
for row in all_rows:
    key = row["raw_question_text"].strip().lower()
    if merged[key]["meta"] is None: merged[key]["meta"] = row
    if row["part_a_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_a_years"])
        if yr: merged[key]["part_a_years"].add(int(yr.group()))
    if row["part_b_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_b_years"])
        if yr: merged[key]["part_b_years"].add(int(yr.group()))

final_rows = []
for key, val in merged.items():
    row = val["meta"].copy()
    pa, pb = sorted(val["part_a_years"]), sorted(val["part_b_years"])
    row["part_a_years"] = str(pa) if pa else "[]"
    row["part_b_years"] = str(pb) if pb else "[]"
    final_rows.append(row)

final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

OUT = os.path.join(os.path.dirname(__file__), "Artificial_Neural_Networks_Dataset.csv")
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)
print(f"\nDone. {len(final_rows)} unique questions → {OUT}")
