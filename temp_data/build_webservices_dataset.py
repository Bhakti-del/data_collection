"""
build_webservices_dataset.py
Parses JNTUH Web Services / Web Services and SOA question paper .txt files
(R13, R16) and produces Web_Services_SOA_Dataset.csv.

Topic tags from R13/R16 Web Services syllabus:
  Unit I  : WEB_SERVICES_FUNDAMENTALS
  Unit II : SOAP
  Unit III: WSDL
  Unit IV : UDDI
  Unit V  : INTEROPERABILITY_AND_SECURITY
"""

import os, re, csv
from collections import defaultdict

TOPIC_KEYWORDS = {
    "WEB_SERVICES_FUNDAMENTALS": [
        "web service", "web services", "distributed computing",
        "evolution of distributed", "core distributed computing",
        "corba", "java rmi", "rmi", "dcom", "mom",
        "j2ee", "xml in distributed", "role of j2ee",
        "service oriented architecture", "soa", "emergence of web services",
        "operational model", "building blocks", "web services architecture",
        "characteristics of web services", "benefits of web services",
        "challenges", "communication model", "web service life cycle",
        "basic steps", "implementing web service", "tools and technologies",
        "ebxml", "web services standards", "core web services",
        "benefits and challenges", "web application", "message based communication",
    ],
    "SOAP": [
        "soap", "simple object access protocol",
        "soap message", "soap envelope", "soap header", "soap body",
        "soap fault", "faultcode", "faultactor", "soap encoding",
        "soap communication", "soap messaging", "message exchange model",
        "soap binding", "soap rpc", "rpc concept in soap",
        "soap 1.1", "soap request", "soap response",
        "serialization", "deserialization", "marshalling",
        "structure type", "enumeration", "multiple references",
        "java and axis", "axis", "limitations of soap",
        "anatomy of soap", "soap message structure",
        "soap web service in java", "soap proxies",
    ],
    "WSDL": [
        "wsdl", "web service description language",
        "wsdl document", "wsdl definition", "wsdl binding",
        "wsdl tools", "wsdl life cycle", "web service life cycle",
        "structural elements", "anatomy of wsdl",
        "message element", "service element", "port type",
        "operation", "extensibility", "limitations of wsdl",
        "namespaces", "definitions element", "wsdl in the world",
        "types of operations", "wsdl tools functionalities",
        "java code from wsdl", "create wsdl", "request response operation",
    ],
    "UDDI": [
        "uddi", "universal description discovery integration",
        "uddi registry", "uddi data structure", "uddi specifications",
        "business entity", "business service", "binding template",
        "tmodel", "white pages", "yellow pages", "green pages",
        "public registry", "private registry", "service discovery",
        "publishing api", "inquiry api", "save_", "delete_",
        "find_", "get_", "publishing", "searching", "deleting",
        "categorization", "uddi error", "limitations of uddi",
        "programming with uddi", "uddi business registry",
        "role of service discovery",
    ],
    "INTEROPERABILITY_AND_SECURITY": [
        "interoperability", "web services interoperability",
        ".net", "dotnet", "net framework", "net client",
        "axis web service", "java client", "creating a client",
        "soap proxy", "soap proxies", "steps to create",
        "xml security", "xml encryption", "xml signature",
        "digital signature", "digital certificate",
        "cryptography", "symmetric cipher", "asymmetric cipher",
        "goals of cryptography", "rapid-fire cryptography",
        "non-repudiation", "integrity", "authentication",
        "certification authority", "dual signature",
        "xml security framework", "web services security",
        "challenges in security", "securing web services",
        "distributed management framework", "semantic interoperability",
    ],
}

def classify_topic(text):
    tl = text.lower()
    scores = {t: sum(1 for kw in kws if kw in tl) for t, kws in TOPIC_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "WEB_SERVICES_FUNDAMENTALS"

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
                             "illustrate", "write a program", "write code", "solve",
                             "write down", "develop a webservice", "write the code"]):
        return "Apply"
    if any(w in t for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                             "summarize", "briefly", "how does", "how is", "how are",
                             "how can", "how to", "what are the", "list and explain"]):
        return "Understand"
    return "Remember"

def extract_year(filename):
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else None

def parse_marks(text):
    m = re.search(r'\[(\d+)\+(\d+)\+(\d+)\]', text)
    if m: return max(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = re.search(r'\[(\d+)\+(\d+)\]', text)
    if m: return max(int(m.group(1)), int(m.group(2)))
    m = re.search(r'\[(\d+)\]', text)
    if m: return int(m.group(1))
    return None

def clean_q(text):
    text = re.sub(r'\[\d+\+\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'used paper.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'--oo.*', '', text, flags=re.IGNORECASE)
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
        r'^--oo', r'^part\s*[ab]', r'^or$', r'^r\d{2}$',
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
    text = re.sub(r'^.*?(WEB SERVICES.*?)\n', '', text, flags=re.DOTALL | re.IGNORECASE, count=1)
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
    (os.path.join(BASE, "R13_text/question papers/4-2/WEB SERVICES"), "Web Services"),
    (os.path.join(BASE, "R16_text/Question Papers/4-2/WEB SERVICES AND SERVICE ORIENTED ARCHITECTURE"), "Web Services and Service Oriented Architecture"),
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

OUT = os.path.join(os.path.dirname(__file__), "Web_Services_SOA_Dataset.csv")
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)
print(f"\nDone. {len(final_rows)} unique questions → {OUT}")
