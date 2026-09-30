"""
build_middleware_dataset.py
Parses JNTUH Middleware Technologies question paper .txt files (R18)
and produces Middleware_Technologies_Dataset.csv.

Topic tags from R18 Middleware Technologies syllabus:
  Unit I  : CLIENT_SERVER_MODELS
  Unit II : CORBA_ARCHITECTURE
  Unit III: DOTNET_PLATFORM
  Unit IV : CORBA_JAVABEANS
  Unit V  : EJB_AND_TRANSACTIONS
"""

import os, re, csv
from collections import defaultdict

TOPIC_KEYWORDS = {
    "CLIENT_SERVER_MODELS": [
        "client-server", "client server", "client/server",
        "three-tier", "three tier", "two-tier", "distributed computing",
        "pitfalls of client", "client server programming",
        "corporate computing", "centralized computing",
        "evolution of corporate", "distributed system",
        "middleware", "middleware architecture", "middleware types",
        "message oriented middleware", "mom", "rpc", "remote procedure call",
        "rmi", "java rmi", "dcom", "microsoft dcom",
    ],
    "CORBA_ARCHITECTURE": [
        "corba", "orb", "object request broker", "iiop",
        "idl", "interface definition language", "ior",
        "interoperable object reference", "naming service",
        "corba services", "omg", "poa", "portable object adapter",
        "skeleton", "stub", "servant", "corba object",
        "corba client", "corba server", "corba/java",
        "corba interoperability", "trader", "corba trader",
        "local/remote transparency", "location transparency",
        "corba architecture", "object services",
    ],
    "DOTNET_PLATFORM": [
        ".net", "dotnet", "dot net", "c#", "csharp", "c sharp",
        "reflection", "system.io", "namespace", "assembly",
        "clr", "common language runtime", "il", "intermediate language",
        "interoperability", ".net interoperability", "autolot",
        "ado.net", "serializable", "servicecontract", "dllimport",
        "obsolete", "predefined attributes", ".net attributes",
        "events in c#", "delegate", "windows forms",
        "asp.net", "web form", ".net framework",
    ],
    "CORBA_JAVABEANS": [
        "javabeans", "java beans", "javabean", "bean",
        "corba components", "corba beans", "compile time",
        "run time java beans", "runtime java beans",
        "jar file", "bdk", "introspection",
        "properties", "events", "methods in beans",
        "bean development kit", "corba augment",
        "java to java beans", "services to java beans",
    ],
    "EJB_AND_TRANSACTIONS": [
        "ejb", "enterprise java beans", "enterprise javabean",
        "session bean", "entity bean", "message driven bean",
        "mdb", "container", "ejb container", "deployment descriptor",
        "cmp", "container managed persistence", "bmp",
        "j2ee", "application server", "ejb client",
        "object transaction monitor", "otm", "transaction monitor",
        "transaction", "acid", "two-phase commit", "xa protocol",
        "distributed transaction", "jta", "jndi",
        "ejb lifecycle", "stateful", "stateless",
    ],
}

def classify_topic(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "CLIENT_SERVER_MODELS"

def classify_bloom(text):
    t = text.lower()
    if any(w in t for w in ["design", "propose", "formulate", "create a", "develop a"]):
        return "Create"
    if any(w in t for w in ["evaluate", "justify", "assess", "critique", "recommend"]):
        return "Evaluate"
    if any(w in t for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                             "contrast", "examine", "trace", "derive"]):
        return "Analyze"
    if any(w in t for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                             "illustrate", "write a program", "solve", "construct",
                             "write a code", "write code", "show"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "briefly", "how does", "how is", "how are",
                             "how can", "how to", "what are the"]):
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
    text = re.sub(r'R\d{2}\s+RA\s*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+OR\s*$', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', text).strip()

IMAGE_PATS = [r'neat (sketch|diagram|figure)', r'shown in (the )?figure',
              r'draw (a neat|and explain)', r'given below', r'figure \d+']

def is_image(text):
    return any(re.search(p, text.lower()) for p in IMAGE_PATS)

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 12: return True
    return any(re.search(p, t) for p in [
        r'^\(\s*\d+\s*marks\s*\)$', r'^used paper', r'^---', r'^ or$',
        r'^--oo', r'^r\d{2}\s+ra', r'^part\s*[ab]', r'^or$',
    ])

def extract_no_parta(text, year, subject_name):
    rows = []
    text = re.sub(r'^.*?MIDDLEWARE TECHNOLOGIES\n', '', text, flags=re.DOTALL | re.IGNORECASE)
    blocks = re.split(r'\n(?=\d{1,2}[\.\)])', text)
    for block in blocks:
        block = block.strip()
        if not block: continue
        marks = (8 if re.search(r'\[7\+8\]|\[8\+7\]', block) else
                 9 if re.search(r'\[6\+9\]|\[9\+6\]', block) else
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

BASE = os.path.join(os.path.dirname(__file__), "cleaned_papers")
DIRS = [
    (os.path.join(BASE, "R18 text/3rd Year/Semester 1/MIDDLEWARE TECHNOLOGIES"), "Middleware Technologies"),
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
    for field in ["part_a_years", "part_b_years"]:
        if row[field] != "[]":
            yr = re.search(r'\d{4}', row[field])
            if yr: merged[key][field[:-6] + "_years"].add(int(yr.group()))

# rebuild merged properly
merged2 = defaultdict(lambda: {"part_a_years": set(), "part_b_years": set(), "meta": None})
for row in all_rows:
    key = row["raw_question_text"].strip().lower()
    if merged2[key]["meta"] is None: merged2[key]["meta"] = row
    if row["part_a_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_a_years"])
        if yr: merged2[key]["part_a_years"].add(int(yr.group()))
    if row["part_b_years"] != "[]":
        yr = re.search(r'\d{4}', row["part_b_years"])
        if yr: merged2[key]["part_b_years"].add(int(yr.group()))

final_rows = []
for key, val in merged2.items():
    row = val["meta"].copy()
    pa, pb = sorted(val["part_a_years"]), sorted(val["part_b_years"])
    row["part_a_years"] = str(pa) if pa else "[]"
    row["part_b_years"] = str(pb) if pb else "[]"
    final_rows.append(row)

final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

OUT = os.path.join(os.path.dirname(__file__), "Middleware_Technologies_Dataset.csv")
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)
print(f"\nDone. {len(final_rows)} unique questions → {OUT}")
