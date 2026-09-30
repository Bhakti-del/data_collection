"""
build_nlp_dataset.py
Parses JNTUH Natural Language Processing question paper .txt files (R18)
and produces Natural_Language_Processing_Dataset.csv.

Topic tags from R18 NLP syllabus:
  Unit I  : MORPHOLOGY_AND_NLP_INTRO
  Unit II : SYNTAX_AND_PARSING
  Unit III: SEMANTICS_AND_WSD
  Unit IV : DISCOURSE_AND_PRAGMATICS
  Unit V  : LANGUAGE_MODELING
"""

import os, re, csv
from collections import defaultdict

TOPIC_KEYWORDS = {
    "MORPHOLOGY_AND_NLP_INTRO": [
        "morpholog", "morpheme", "allomorph", "lexeme", "lemma",
        "stemming", "lemmatization", "inflection", "derivation",
        "morphological model", "morphological analysis",
        "dictionary lookup", "unification based morphology",
        "challenges of morphological", "structure of words",
        "components of words", "early nlp", "nlp system",
        "applications of nlp", "challenges in nlp", "goals of nlp",
        "history of nlp", "importance of nlp", "introduction to nlp",
        "natural language processing", "nlp",
        "complexity of approaches", "performance of approaches",
        "surface structure", "deep structure",
    ],
    "SYNTAX_AND_PARSING": [
        "parsing", "parser", "parse tree", "phrase structure",
        "context free grammar", "cfg", "treebank", "tree bank",
        "top down parsing", "bottom up parsing", "shift reduce",
        "chart parsing", "cky", "earley", "probabilistic context free",
        "pcfg", "ambiguity resolution", "syntactic", "syntax",
        "tokenization", "multilingual syntactic", "syntactic representation",
        "data driven approach to syntax", "parsing algorithm",
        "types of parsers", "transition network", "atn",
        "multilingual issues", "cross lingual", "bilingual",
    ],
    "SEMANTICS_AND_WSD": [
        "word sense disambiguation", "wsd", "homonymy", "polysemy",
        "semantic parsing", "semantic", "semantics", "meaning representation",
        "predicate argument structure", "predicator", "predicate",
        "propbank", "framenet", "verbnet", "wordnet",
        "event identification", "entity resolution",
        "ontology", "semantic role", "selectional restriction",
        "lexical resource", "semantic analysis",
        "meaning representation system", "knowledge representation",
    ],
    "DISCOURSE_AND_PRAGMATICS": [
        "discourse", "cohesion", "coherence", "anaphora",
        "anaphora resolution", "coreference", "reference resolution",
        "demonstrative reference", "pronoun resolution",
        "discourse analysis", "pragmatics",
        "cohesion structure", "discourse structure",
        "definite reference", "indefinite reference",
        "types of references", "reference in discourse",
    ],
    "LANGUAGE_MODELING": [
        "language model", "language modeling", "n-gram", "bigram",
        "unigram", "trigram", "probability", "perplexity",
        "parameter estimation", "smoothing", "backoff",
        "factored language model", "syntax based language model",
        "multilingual language model", "cross lingual language model",
        "sequence classification", "generative", "discriminative",
        "structure of documents", "document structure",
        "information extraction", "named entity", "ner",
    ],
}

def classify_topic(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "MORPHOLOGY_AND_NLP_INTRO"

def classify_bloom(text):
    t = text.lower()
    if any(w in t for w in ["design", "propose", "formulate", "create a", "develop a"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                             "contrast", "examine", "make a comparison"]):
        return "Analyze"
    if any(w in t for w in ["apply", "implement", "demonstrate", "illustrate",
                             "write procedure", "calculate", "compute", "apply"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "briefly", "how does", "how is", "list and explain",
                             "elaborate", "elucidate", "give an overview"]):
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
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+OR\s*$', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

IMAGE_PATS = [r'neat (sketch|diagram|figure)', r'shown in (the )?figure',
              r'draw (a neat|and explain)', r'given below']

def is_image(text):
    return any(re.search(p, text.lower()) for p in IMAGE_PATS)

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 15: return True
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
    text = re.sub(r'^.*?NATURAL LANGUAGE PROCESSING.*?\n', '', text, flags=re.DOTALL | re.IGNORECASE, count=1)
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
    (os.path.join(BASE, "R18 text/3rd Year/Semester 1/NATURAL LANGUAGE PROCESSING"), "Natural Language Processing"),
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

OUT = os.path.join(BASE_DIR, "Natural_Language_Processing_Dataset.csv")
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)

DUP_OUT = os.path.join(BASE_DIR, "Natural_Language_Processing_Dataset_duplicates_removed.csv")
with open(DUP_OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(removed)

print(f"\nDone. {len(final_rows)} unique questions → {OUT}")
print(f"Removed {len(removed)} duplicates → {DUP_OUT}")
