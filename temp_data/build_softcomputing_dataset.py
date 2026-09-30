"""
build_softcomputing_dataset.py
Parses JNTUH Soft Computing question paper .txt files (R13, R18)
and produces Soft_Computing_Dataset.csv.

Topic tags from R13/R18 Soft Computing syllabus:
  Unit I  : SEARCH_AND_OPTIMIZATION
  Unit II : NEURAL_NETWORKS_SC
  Unit III: ASSOCIATIVE_MEMORY_AND_SOM
  Unit IV : FUZZY_SETS_AND_LOGIC
  Unit V  : GENETIC_ALGORITHMS
"""

import os, re, csv
from collections import defaultdict

TOPIC_KEYWORDS = {
    "SEARCH_AND_OPTIMIZATION": [
        "state space", "search", "heuristic search", "hill climbing",
        "best first search", "generate and test", "means end analysis",
        "constraint satisfaction", "cryptarithmetic", "8 queens",
        "depth first", "breadth first", "a* algorithm", "a star",
        "simulated annealing", "problem solving", "problem characteristics",
        "soft computing", "hard computing", "soft vs hard",
        "hybrid model", "soft computing methods", "recent trends",
        "particle swarm", "pso", "swarm optimization",
        "evolutionary computing", "information retrieval",
    ],
    "NEURAL_NETWORKS_SC": [
        "artificial neural network", "ann", "neural network",
        "perceptron", "back propagation", "backpropagation",
        "delta rule", "learning rate", "weight", "bias",
        "multilayer perceptron", "convergence", "training algorithm",
        "biological neural", "basic models of ann",
        "connection topology", "feedforward", "feedback",
        "boltzmann machine", "cauchy machine", "hamming network",
        "hopfield", "bam", "bidirectional associative",
        "adaptive resonance", "art", "counter propagation",
    ],
    "ASSOCIATIVE_MEMORY_AND_SOM": [
        "associative memory", "kohonen", "self organizing",
        "self-organizing map", "som", "learning vector quantization",
        "lvq", "fixed weight competitive", "competitive learning",
        "counter propagation", "full counter propagation",
        "maxnet", "feature map", "unsupervised learning",
        "clustering", "winner takes all",
    ],
    "FUZZY_SETS_AND_LOGIC": [
        "fuzzy", "fuzzy set", "fuzzy logic", "membership function",
        "fuzzification", "defuzzification", "fuzzy relation",
        "fuzzy composition", "max-min composition",
        "max-product composition", "fuzzy rule", "fuzzy inference",
        "mamdani", "sugeno", "fuzzy proposition",
        "linguistic variable", "crisp set", "classical set",
        "characteristic function", "lambda cut", "alpha cut",
        "tolerance relation", "equivalence relation fuzzy",
        "belief measure", "plausibility measure", "approximate reasoning",
        "fuzzy decision making", "fuzzy membership",
        "extension principle", "intuitionistic fuzzy",
        "fuzzy c-means", "rough fuzzy", "rough set",
        "rough approximation", "multi criteria decision",
        "multi-person decision", "relational join",
    ],
    "GENETIC_ALGORITHMS": [
        "genetic algorithm", "ga", "chromosome", "crossover",
        "mutation", "fitness function", "selection",
        "roulette wheel", "tournament selection",
        "travelling salesman", "tsp", "genetic operator",
        "population", "generation", "offspring",
        "single point crossover", "multipoint crossover",
        "stopping condition", "evolutionary", "neuro fuzzy",
        "neuro-fuzzy", "jaccard", "indexing",
    ],
}

def classify_topic(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "FUZZY_SETS_AND_LOGIC"

def classify_bloom(text):
    t = text.lower()
    if any(w in t for w in ["design", "propose", "formulate", "create a", "develop a"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                             "contrast", "examine", "prove", "compare and contrast"]):
        return "Analyze"
    if any(w in t for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                             "illustrate", "construct", "obtain", "find", "solve",
                             "write the training", "write a program"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "briefly", "how does", "how is", "list and explain",
                             "outline", "elucidate", "elaborate"]):
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
    text = re.sub(r'--oo.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+OR\s*$', '', text, flags=re.IGNORECASE)
    # Remove matrix/table data artifacts (lines of numbers/symbols)
    text = re.sub(r'\n[\d\s\.\*\^]+$', '', text, flags=re.MULTILINE)
    return re.sub(r'\s+', ' ', text).strip()

IMAGE_PATS = [r'neat (sketch|diagram|figure)', r'shown in (the )?figure',
              r'draw (a neat|and explain)', r'given below', r'with neat architecture']

def is_image(text):
    return any(re.search(p, text.lower()) for p in IMAGE_PATS)

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 15: return True
    # Contains matrix rows (lines of just numbers/symbols - artifact from numerical problems)
    if re.search(r'^[\d\s\.\*\^\+\-x]+$', t):
        return True
    return any(re.search(p, t) for p in [
        r'^\(\s*\d+\s*marks\s*\)$', r'^used paper', r'^---', r'^ or$',
        r'^--oo', r'^part\s*[ab]', r'^or$',
        r'^r\s*y\d', r'^x\d\s+\d',  # matrix data rows
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
                 15 if re.search(r'\[15\]', block) else 10)
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
    text = re.sub(r'^.*?SOFT COMPUTING\n', '', text, flags=re.DOTALL | re.IGNORECASE, count=1)
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
    (os.path.join(BASE, "R13_text/question papers/4-1/SOFT COMPUTING"), "Soft Computing"),
    (os.path.join(BASE, "R18 text/4th Year/Semester 1/SOFT COMPUTING"), "Soft Computing"),
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

# dedup
def normalize(text):
    t = re.sub(r'[^\w\s]', ' ', text.lower())
    stop = {'a','an','the','in','on','of','to','for','with','and','or','is','are','was','by',
            'from','it','be','as','that','this','how','what','give','write','explain','describe',
            'discuss','define','list','any','various','different','detail','brief','example'}
    return set(w for w in t.split() if w not in stop and len(w) > 2)

to_remove = set()
by_topic = defaultdict(list)
for r in final_rows:
    by_topic[r['topic_tag']].append(r)
for topic, tr in by_topic.items():
    for i in range(len(tr)):
        for j in range(i+1, len(tr)):
            if id(tr[i]) in to_remove or id(tr[j]) in to_remove: continue
            wi, wj = normalize(tr[i]['raw_question_text']), normalize(tr[j]['raw_question_text'])
            if len(wi) < 4 or len(wj) < 4: continue
            if len(wi & wj) / max(len(wi | wj), 1) >= 0.60:
                yi = len(re.findall(r'\d{4}', tr[i]['part_a_years']+tr[i]['part_b_years']))
                yj = len(re.findall(r'\d{4}', tr[j]['part_a_years']+tr[j]['part_b_years']))
                to_remove.add(id(tr[j]) if yi >= yj else id(tr[i]))

removed = [r for r in final_rows if id(r) in to_remove]
final_rows = [r for r in final_rows if id(r) not in to_remove]
final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]
BASE_DIR = os.path.dirname(__file__)

OUT = os.path.join(BASE_DIR, "Soft_Computing_Dataset.csv")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)

DUP_OUT = os.path.join(BASE_DIR, "Soft_Computing_Dataset_duplicates_removed.csv")
with open(DUP_OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(removed)

print(f"\nDone. {len(final_rows)} unique questions → {OUT}")
print(f"Removed {len(removed)} duplicates → {DUP_OUT}")
