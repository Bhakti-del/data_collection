"""
build_ai_dataset.py
Parses all JNTUH Artificial Intelligence question paper .txt files and
produces Artificial_Intelligence_Dataset.csv following the same schema
as the other subject datasets.

Topic tags are derived directly from the R13 AI syllabus units:
  Unit I  : PROBLEM_SOLVING_AND_SEARCH, GAME_PLAYING
  Unit II : LOGIC_AND_PROPOSITIONAL_CALCULUS, KNOWLEDGE_REPRESENTATION
  Unit III: EXPERT_SYSTEMS, UNCERTAINTY_AND_PROBABILITY
  Unit IV : MACHINE_LEARNING, ARTIFICIAL_NEURAL_NETWORKS
  Unit V  : NLP_AND_SEMANTIC_WEB

Image-dependent questions (those asking to "draw a neat sketch/diagram"
where the diagram was lost in PDF-to-text conversion) are filtered out.
"""

import os
import re
import csv
from collections import defaultdict

# ── Topic taxonomy from AI syllabus ──────────────────────────────────────────
TOPIC_KEYWORDS = {
    "PROBLEM_SOLVING_AND_SEARCH": [
        "state space", "state-space", "problem solving", "problem space",
        "search", "heuristic search", "exhaustive search", "brute force",
        "breadth first", "depth first", "bfs", "dfs", "hill climbing",
        "best first search", "a* algorithm", "a star", "iterative deepening",
        "dfid", "depth first iterative", "constraint satisfaction",
        "cryptarithmetic", "blocks world", "8 puzzle", "eight puzzle",
        "n queens", "n-queens", "8 queens", "eight queens", "tic tac toe",
        "problem characteristics", "control strategy", "uninformed search",
        "informed search", "admissibility", "generate and test",
        "means-ends analysis", "problem reduction", "and-or graph",
        "bounded look-ahead", "plateau", "ridge", "restart",
    ],
    "GAME_PLAYING": [
        "game playing", "game tree", "minimax", "alpha-beta", "alpha beta pruning",
        "bounded look ahead", "evaluation function", "tic-tac-toe",
        "game search", "two player game",
    ],
    "LOGIC_AND_PROPOSITIONAL_CALCULUS": [
        "propositional logic", "propositional calculus", "predicate logic",
        "predicate calculus", "resolution", "resolution refutation",
        "clause form", "conjunctive normal form", "cnf", "horn clause",
        "unification", "modus ponens", "natural deduction",
        "axiomatic system", "semantic tableau", "tableaux",
        "forward chaining", "backward chaining", "inference rule",
        "inference mechanism", "theorem proving", "proof by refutation",
        "logic programming", "prolog", "first order logic", "fol",
        "abductive inference", "logical connectivity", "logical connective",
        "deductive", "validity", "satisfiability", "tautology",
        "sentence in predicate", "predicate form", "convert to clause",
    ],
    "KNOWLEDGE_REPRESENTATION": [
        "knowledge representation", "knowledge base", "knowledge engineering",
        "semantic network", "semantic net", "frame", "frames",
        "conceptual dependency", "script", "ontology",
        "procedural knowledge", "declarative knowledge",
        "inheritance", "slot", "facet", "isa link",
        "extended semantic net", "knowledge acquisition",
        "knowledge validation", "knowledge engineer",
        "case grammar", "case grammars",
    ],
    "EXPERT_SYSTEMS": [
        "expert system", "expert systems", "production rule", "rule based system",
        "rule based", "knowledge base system", "inference engine",
        "working memory", "expert system architecture", "expert system shell",
        "shell", "building expert system", "phases in building",
        "traditional system", "expert vs traditional",
        "truth maintenance", "jtms", "atms", "ltms", "tms",
        "explanation facility", "backward reasoning", "forward reasoning",
        "mycin", "dendral", "xcon", "applications of expert system",
    ],
    "UNCERTAINTY_AND_PROBABILITY": [
        "uncertainty", "probability", "bayesian", "bayes", "bayesian belief network",
        "belief network", "conditional probability", "prior probability",
        "posterior probability", "certainty factor", "dempster-shafer",
        "dempster shafer", "fuzzy logic", "possibility theory",
        "probabilistic reasoning", "uncertain reasoning",
        "measure of uncertainty", "evidence theory",
    ],
    "MACHINE_LEARNING": [
        "machine learning", "supervised learning", "unsupervised learning",
        "inductive learning", "deductive learning", "decision tree",
        "id3 algorithm", "id3", "information gain", "entropy",
        "classification", "clustering", "k-means", "k means",
        "support vector machine", "svm", "maximum margin", "hyperplane",
        "linear separability", "learning algorithm", "training data",
        "overfitting", "underfitting", "cross validation",
        "conceptual clustering", "reinforcement learning",
        "learning by analogy", "learning by taking advice",
        "parameter adjustment", "chunking",
    ],
    "ARTIFICIAL_NEURAL_NETWORKS": [
        "artificial neural network", "neural network", "perceptron",
        "single layer", "multi layer", "multilayer", "backpropagation",
        "back propagation", "feed forward", "recurrent network",
        "radial basis", "rbf", "activation function", "sigmoid",
        "weight", "neuron", "biological neural", "ann",
        "design issues", "training", "learning rate", "hidden layer",
    ],
    "NLP_AND_SEMANTIC_WEB": [
        "natural language processing", "nlp", "natural language understanding",
        "sentence analysis", "parsing", "parser", "parse tree",
        "grammar", "context free grammar", "syntax", "semantics",
        "semantic analysis", "pragmatics", "morphological analysis",
        "transition network", "augmented transition network", "atn",
        "lexical analysis", "universal networking language", "unl",
        "case grammar", "semantic web", "knowledge on web",
        "world wide web", "rdf", "owl", "ontology web",
        "applications of nlp", "machine translation", "information extraction",
    ],
}


def classify_topic(text: str) -> str:
    text_lower = text.lower()
    scores = {t: 0 for t in TOPIC_KEYWORDS}
    for topic, keywords in TOPIC_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[topic] += 1
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "PROBLEM_SOLVING_AND_SEARCH"


def classify_bloom(text: str) -> str:
    t = text.lower()
    if any(w in t for w in ["design", "propose", "formulate", "create a", "develop a", "construct"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend", "judge"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                             "contrast", "examine", "trace", "derive", "why is it", "why does"]):
        return "Analyze"
    if any(w in t for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                             "illustrate", "show", "write a program", "solve", "represent",
                             "convert", "prove", "construct", "formulate"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "outline", "briefly", "how does", "how is",
                             "how are", "how can", "how to", "what are the"]):
        return "Understand"
    return "Remember"


def extract_year_from_filename(filename: str):
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else None


def parse_marks(text: str):
    # [7+8] or [8+7] → larger part
    m = re.search(r'\[(\d+)\+(\d+)\]', text)
    if m:
        return max(int(m.group(1)), int(m.group(2)))
    m = re.search(r'\[(\d+)\]', text)
    if m:
        return int(m.group(1))
    return None


def clean_question(text: str) -> str:
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'used paper.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove trailing OR (JNTUH "or" separator between question alternatives)
    text = re.sub(r'\s+OR\s*$', '', text, flags=re.IGNORECASE).strip()
    return text


# ── Image-dependent question detection ───────────────────────────────────────
# These questions require a diagram/figure that was lost in PDF→text conversion.
IMAGE_PATTERNS = [
    r'\bfigure\s+\d+',
    r'\bfig\.\s*\d+',
    r'draw a neat (sketch|diagram|figure)',
    r'neat (sketch|diagram|figure)',
    r'shown in (the )?figure',
    r'shown below',
    r'given (below|above|in figure)',
    r'refer (to )?figure',
    r'the following (figure|diagram|graph|tree)',
    r'illustrate with (neat )?(a )?(sketch|diagram)',
    r'draw (and )?explain',
]

def is_image_dependent(text: str) -> bool:
    t = text.lower()
    for pat in IMAGE_PATTERNS:
        if re.search(pat, t):
            return True
    return False


def is_garbage(text: str) -> bool:
    t = text.strip().lower()
    if len(t) < 12:
        return True
    garbage_patterns = [
        r'^\(\s*\d+\s*marks\s*\)$',
        r'^used paper',
        r'^---',
        r'^ or$',
        r'^--oo',
        r'^explain the following:?$',
        r'^write short notes? on:?$',
        r'^define the following:?$',
        r'^discuss the following:?$',
        r'^\d+\s+marks',
        r'^or$',
        r'^part\s*[ab]',
    ]
    for pat in garbage_patterns:
        if re.search(pat, t):
            return True
    return False


def extract_part_a(text: str, year: int) -> list:
    rows = []
    part_a_match = re.search(r'PART[\s\-–]*A(.*?)PART[\s\-–]*B', text, re.DOTALL | re.IGNORECASE)
    if not part_a_match:
        return rows
    part_a = part_a_match.group(1)
    questions = re.findall(r'[a-j]\)\s*(.*?)(?=\n[a-j]\)|\Z)', part_a, re.DOTALL)
    for q in questions:
        q = q.strip()
        if not q or len(q) < 8:
            continue
        marks = parse_marks(q) or 2
        q_clean = clean_question(q)
        if not q_clean or is_garbage(q_clean) or is_image_dependent(q_clean):
            continue
        rows.append({
            "subject_name": "Artificial Intelligence",
            "raw_question_text": q_clean,
            "topic_tag": classify_topic(q_clean),
            "bloom_level": classify_bloom(q_clean),
            "original_marks": marks,
            "part_a_years": f"[{year}]",
            "part_b_years": "[]",
        })
    return rows


def extract_part_b(text: str, year: int) -> list:
    rows = []
    part_b_match = re.search(r'PART[\s\-–]*B(.*)', text, re.DOTALL | re.IGNORECASE)
    if not part_b_match:
        return rows
    part_b = part_b_match.group(1)
    blocks = re.split(r'\n(?=\d{1,2}[\.\)])', part_b)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.search(r'\[5\+5\]', block):
            marks = 5
        elif re.search(r'\[7\+8\]|\[8\+7\]', block):
            marks = 8
        elif re.search(r'\[6\+9\]|\[9\+6\]', block):
            marks = 9
        elif re.search(r'\[10\]', block):
            marks = 10
        elif re.search(r'\[15\]', block):
            marks = 15
        else:
            marks = 10

        sub_parts = re.split(r'\n(?=[a-c]\))', block)
        for part in sub_parts:
            part = part.strip()
            part = re.sub(r'^\d{1,2}[\.\)]\s*', '', part)
            part = re.sub(r'^[a-c]\)\s*', '', part)
            part = part.strip()
            if not part or len(part) < 10:
                continue
            q_clean = clean_question(part)
            if not q_clean or is_garbage(q_clean) or is_image_dependent(q_clean):
                continue
            rows.append({
                "subject_name": "Artificial Intelligence",
                "raw_question_text": q_clean,
                "topic_tag": classify_topic(q_clean),
                "bloom_level": classify_bloom(q_clean),
                "original_marks": marks,
                "part_a_years": "[]",
                "part_b_years": f"[{year}]",
            })
    return rows


def extract_no_parta(text: str, year: int) -> list:
    """For papers without Part-A/Part-B split (older format)."""
    rows = []
    # Strip subject header
    text = re.sub(r'^.*?ARTIFICIAL INTELLIGENCE\n', '', text, flags=re.DOTALL | re.IGNORECASE)
    blocks = re.split(r'\n(?=\d{1,2}[\.\)])', text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.search(r'\[7\+8\]|\[8\+7\]', block):
            marks = 8
        elif re.search(r'\[6\+9\]|\[9\+6\]', block):
            marks = 9
        elif re.search(r'\[15\]', block):
            marks = 15
        elif re.search(r'\[5\+5\]', block):
            marks = 5
        elif re.search(r'\[10\]', block):
            marks = 10
        else:
            marks = 15

        sub_parts = re.split(r'\n(?=[a-c]\))', block)
        for part in sub_parts:
            part = part.strip()
            part = re.sub(r'^\d{1,2}[\.\)]\s*', '', part)
            part = re.sub(r'^[a-c]\)\s*', '', part)
            part = part.strip()
            if not part or len(part) < 10:
                continue
            q_clean = clean_question(part)
            if not q_clean or is_garbage(q_clean) or is_image_dependent(q_clean):
                continue
            rows.append({
                "subject_name": "Artificial Intelligence",
                "raw_question_text": q_clean,
                "topic_tag": classify_topic(q_clean),
                "bloom_level": classify_bloom(q_clean),
                "original_marks": marks,
                "part_a_years": "[]",
                "part_b_years": f"[{year}]",
            })
    return rows


def process_file(filepath: str) -> list:
    year = extract_year_from_filename(os.path.basename(filepath))
    if not year:
        return []
    with open(filepath, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    has_part_a = bool(re.search(r'PART[\s\-–]*A', text, re.IGNORECASE))
    if has_part_a:
        return extract_part_a(text, year) + extract_part_b(text, year)
    else:
        return extract_no_parta(text, year)


# ── Directories ───────────────────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(__file__), "cleaned_papers")
AI_DIRS = [
    os.path.join(BASE, "R13_text/question papers/4-1/ARTIFICIAL INTELLIGENCE"),
    os.path.join(BASE, "R16_text/Question Papers/3-2/ARTIFICIAL INTELLIGENCE"),
    os.path.join(BASE, "R18 text/4th Year/Semester 1/ARTIFICIAL INTELLIGENCE"),
]

all_rows = []
for d in AI_DIRS:
    if not os.path.isdir(d):
        print(f"[SKIP] Directory not found: {d}")
        continue
    for fname in sorted(os.listdir(d)):
        if fname.endswith(".txt"):
            fpath = os.path.join(d, fname)
            extracted = process_file(fpath)
            print(f"  {fname}: {len(extracted)} questions")
            all_rows.extend(extracted)

# ── Merge duplicates: same question text → combine years ─────────────────────
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

# ── Manual overrides for residual misclassifications ─────────────────────────
OVERRIDES = {
    "give an example to explain the various approaches used for knowledge representation.": "KNOWLEDGE_REPRESENTATION",
    "give an example to explain the concept of bayesian belief network for measuring the uncertainity.": "UNCERTAINTY_AND_PROBABILITY",
    "describe in detail about the concept of single layer feed forward networks.": "ARTIFICIAL_NEURAL_NETWORKS",
    "with an example explain the steps used for processing a natural language sentence.": "NLP_AND_SEMANTIC_WEB",
    "explain how entropy and information gain are used in the construction of decision tree.": "MACHINE_LEARNING",
    "explain the challenges and applications of artificial intelligence.": "PROBLEM_SOLVING_AND_SEARCH",
    "represent 8 puzzle problem in state space. and apply best first search to solve.": "PROBLEM_SOLVING_AND_SEARCH",
    "define unsupervised learning and discuss in detail about conceptual clustering.": "MACHINE_LEARNING",
    "give an overview of multi-layer perceptron algorithm in detail.": "ARTIFICIAL_NEURAL_NETWORKS",
    "what do you mean by linear separability? give an overview of perceptron and perceptron training algorithm.": "ARTIFICIAL_NEURAL_NETWORKS",
    "explain maximum margin hyperplane and linear support vector machine.": "MACHINE_LEARNING",
}

for r in final_rows:
    key = r["raw_question_text"].strip().lower()
    if key in OVERRIDES:
        r["topic_tag"] = OVERRIDES[key]

# ── Sort by topic then bloom level ───────────────────────────────────────────
final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

# ── Write output CSV ──────────────────────────────────────────────────────────
OUT = os.path.join(os.path.dirname(__file__), "Artificial_Intelligence_Dataset.csv")
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)

print(f"\nDone. {len(final_rows)} unique questions written to {OUT}")
