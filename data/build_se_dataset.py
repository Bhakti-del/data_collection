import os
import re
import csv
from collections import defaultdict

# ── topic taxonomy ─────────────────────────────────────────────────────────────
TOPIC_KEYWORDS = {
    "SOFTWARE_PROCESS_AND_LIFECYCLE": [
        "software development life cycle", "sdlc", "software process", "process model",
        "process framework", "process patterns", "process assessment", "layered technology",
        "software engineering", "legacy software", "software crisis", "software myths",
        "evolving role", "software products", "software services", "computer based system",
        "system engineering hierarchy", "software development process", "methodology",
        "evaluation of software engineering", "characteristics of software",
        "define the term software", "elements of a software process",
        "various myths", "managers myths", "practitioners performance",
        "psp", "tsp", "personal software process", "team software process",
        "in-house", "outsourced", "custom development",
    ],
    "PROCESS_MODELS": [
        "waterfall model", "waterfall", "spiral model", "incremental model",
        "evolutionary process model", "unified process", "rup", "agile", "scrum",
        "extreme programming", "xp", "cmmi", "cmm", "iso 9000", "six sigma",
        "personal process", "team process", "specialized process model",
        "prototype", "rapid application", "rad", "concurrent model",
    ],
    "REQUIREMENTS_ENGINEERING": [
        "requirement", "requirements engineering", "requirements elicitation",
        "requirements analysis", "requirements specification", "srs",
        "functional requirement", "non-functional requirement", "feasibility study",
        "feasibility studies", "use case", "requirements document", "requirements review",
        "requirements validation", "traceability", "requirement management",
        "context model", "behavioral model", "system model", "structured method",
        "data flow diagram", "dfd", "state transition", "cardinality", "modality",
    ],
    "SYSTEM_MODELING_AND_UML": [
        "uml", "class diagram", "sequence diagram", "collaboration diagram",
        "use case diagram", "activity diagram", "object model", "data model",
        "system modeling", "system modelling", "state machine", "context diagram",
        "object constraint language", "ocl", "structural model", "behavioral system model",
        "data flow model", "context level model", "tagged values", "constraints",
        "e-mail system", "food ordering", "washing machine", "dvd player",
        "ubiquitous language", "domain model",
    ],
    "SOFTWARE_DESIGN": [
        "software design", "design principle", "design concept", "design element",
        "architectural design", "architecture", "architectural style", "architectural pattern",
        "component design", "component level design", "component based",
        "cbse", "interface design", "interface analysis", "user interface design",
        "golden rules", "cohesion", "coupling", "modular design", "modularity",
        "function oriented design", "object oriented design", "data design",
        "program design language", "pdl", "architectural description language",
        "pattern based design", "design pattern", "architecture trade-off",
        "atam", "design evaluation",
    ],
    "SOFTWARE_TESTING": [
        "testing", "test", "black box testing", "white box testing", "grey box",
        "unit testing", "integration testing", "system testing", "regression testing",
        "acceptance testing", "validation testing", "verification",
        "cyclomatic complexity", "path testing", "basis path",
        "equivalence partitioning", "boundary value", "test strategy",
        "test case", "test plan", "debugging", "error", "failure", "fault",
        "defect", "defect removal", "exhaustive test", "strategic approach to testing",
    ],
    "SOFTWARE_METRICS_AND_MEASUREMENT": [
        "metric", "metrics", "software measurement", "software quality metric",
        "metrics for design", "metrics for analysis", "metrics for source code",
        "metrics for process", "metrics for product", "metrics for maintenance",
        "function point", "lines of code", "loc", "cyclomatic", "halstead",
        "size estimation", "effort estimation", "cost estimation", "cocomo",
        "software quality", "quality parameter", "quality attribute",
    ],
    "SOFTWARE_QUALITY_AND_REVIEWS": [
        "software quality assurance", "sqa", "quality assurance", "quality standard",
        "formal technical review", "ftr", "software review", "peer review",
        "inspection", "walkthrough", "iso 9000", "six sigma", "cmmi",
        "quality management", "quality plan", "defect prevention",
        "mccall", "quality factor", "sample-driven review", "review process",
        "software reliability", "reliability",
    ],
    "RISK_MANAGEMENT": [
        "risk", "risk management", "risk identification", "risk projection",
        "risk refinement", "risk mitigation", "risk monitoring", "rmmm",
        "risk strategies", "proactive risk", "reactive risk", "software risk",
        "risk driven", "risk reduction", "risk assessment",
    ],
    "SOFTWARE_MAINTENANCE_AND_EVOLUTION": [
        "software maintenance", "maintenance", "software evolution", "change management",
        "configuration management", "version control", "software change",
        "maintenance cost", "corrective maintenance", "adaptive maintenance",
        "perfective maintenance", "legacy system",
    ],
    "AGILE_AND_XP": [
        "agile", "extreme programming", "xp", "scrum", "kanban",
        "iteration", "sprint", "user story", "story", "velocity",
        "continuous integration", "collective ownership", "pair programming",
        "test driven development", "tdd", "refactoring", "onsite customer",
        "stand-up meeting", "daily standup", "retrospective", "release planning",
        "spike solution", "osmotic communication", "root cause analysis",
        "coding standard", "informative workspace", "adaptive planning",
        "iteration planning", "release commitment", "performance optimization",
        "version control system",
    ],
    "PROJECT_MANAGEMENT_AND_ESTIMATION": [
        "project management", "project planning", "project scheduling",
        "effort estimation", "cost estimation", "cocomo", "function point",
        "project monitoring", "project control", "team structure",
        "software configuration", "scm", "change control",
    ],
    "SOFTWARE_DESIGN": [
        "software design", "design principle", "design concept", "design element",
        "architectural design", "architecture", "architectural style", "architectural pattern",
        "component design", "component level design", "component based",
        "cbse", "interface design", "interface analysis", "user interface design",
        "golden rules", "cohesion", "coupling", "modular design", "modularity",
        "function oriented design", "object oriented design", "data design",
        "program design language", "pdl", "architectural description language",
        "pattern based design", "design pattern", "architecture trade-off",
        "atam", "design evaluation", "design quality", "design process",
        "transaction mapping", "transform mapping", "conventional component",
        "procedural interface", "component diagram", "maintainability",
        "memory load", "user memory", "design steps", "good design",
        "design quality guidelines",
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
    return best if scores[best] > 0 else "GENERAL_SE"

def classify_bloom(text):
    text_lower = text.lower()
    if any(w in text_lower for w in ["design a", "propose", "formulate", "create a", "develop a", "construct"]):
        return "Create"
    if any(w in text_lower for w in ["evaluate", "justify", "assess", "critique", "recommend", "judge"]):
        return "Evaluate"
    if any(w in text_lower for w in ["analyze", "analyse", "compare", "differentiate", "distinguish",
                                      "contrast", "examine", "why is it", "why does"]):
        return "Analyze"
    if any(w in text_lower for w in ["apply", "calculate", "compute", "implement", "demonstrate",
                                      "illustrate", "draw", "show", "write a program", "solve"]):
        return "Apply"
    if any(w in text_lower for w in ["explain", "describe", "discuss", "elaborate", "interpret",
                                      "summarize", "outline", "give an account", "briefly", "how does",
                                      "how is", "how are", "how can", "how to"]):
        return "Understand"
    return "Remember"

def extract_year_from_filename(filename):
    m = re.search(r'(\d{4})', filename)
    return int(m.group(1)) if m else None

def parse_marks(text):
    # [7+8] or [8+7] → 8 (larger portion)
    m = re.search(r'\[(\d+)\+(\d+)\]', text)
    if m:
        return max(int(m.group(1)), int(m.group(2)))
    m = re.search(r'\[(\d+)\]', text)
    if m:
        return int(m.group(1))
    return None

def clean_question(text):
    text = re.sub(r'\[\d+\+\d+\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    text = re.sub(r'used paper.*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'---.*?---', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_garbage(text):
    t = text.strip().lower()
    if len(t) < 12:
        return True
    garbage_patterns = [
        r'^\(?\s*\d+\s*marks\s*\)?$',
        r'^used paper',
        r'^---',
        r'^ or$',
        r'^--oo',
        r'^explain the following:?$',
        r'^write short notes? on:?$',
        r'^define the following:?$',
        r'^discuss the following:?$',
        r'^\d+\s+marks',
        r'^used papers',
    ]
    for pat in garbage_patterns:
        if re.search(pat, t):
            return True
    return False

# ── R13/R16 Part-A/Part-B format ───────────────────────────────────────────────
def extract_part_a(text, year):
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
        if not q_clean or is_garbage(q_clean):
            continue
        rows.append({
            "subject_name": "Software Engineering",
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
    blocks = re.split(r'\n(?=\d{1,2}[\.\)])', part_b)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.search(r'\[5\+5\]', block):
            marks = 5
        elif re.search(r'\[10\]', block):
            marks = 10
        elif re.search(r'\[7\+8\]|\[8\+7\]', block):
            marks = 8
        elif re.search(r'\[4\+3\+3\]|\[3\+4\+3\]', block):
            marks = 5
        else:
            marks = 5

        sub_parts = re.split(r'\n(?=[a-c]\))', block)
        for part in sub_parts:
            part = part.strip()
            part = re.sub(r'^\d{1,2}[\.\)]\s*', '', part)
            part = re.sub(r'^[a-c]\)\s*', '', part)
            part = part.strip()
            if not part or len(part) < 10:
                continue
            q_clean = clean_question(part)
            if not q_clean or is_garbage(q_clean):
                continue
            rows.append({
                "subject_name": "Software Engineering",
                "raw_question_text": q_clean,
                "topic_tag": classify_topic(q_clean),
                "bloom_level": classify_bloom(q_clean),
                "original_marks": marks,
                "part_a_years": "[]",
                "part_b_years": f"[{year}]",
            })
    return rows

# ── R18 / Modern SE format (no Part-A, numbered questions only) ────────────────
def extract_no_parta(text, year):
    rows = []
    # Strip header lines
    text = re.sub(r'^.*?(SOFTWARE ENGINEERING|MODERN SOFTWARE ENGINEERING)\n', '', text,
                  flags=re.DOTALL | re.IGNORECASE)
    blocks = re.split(r'\n(?=\d{1,2}[\.\)])', text)
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        if re.search(r'\[7\+8\]|\[8\+7\]', block):
            marks = 8
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
            if not q_clean or is_garbage(q_clean):
                continue
            rows.append({
                "subject_name": "Software Engineering",
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
    has_part_a = bool(re.search(r'PART[\s\-–]*A', text, re.IGNORECASE))
    if has_part_a:
        return extract_part_a(text, year) + extract_part_b(text, year)
    else:
        return extract_no_parta(text, year)

BASE = "/home/admin1/WingsAI/group_2/DATA/Question_Paper_Generator/question-paper-predictor/data/cleaned_papers"
SE_DIRS = [
    os.path.join(BASE, "R13_text/question papers/3-1/SOFTWARE ENGINEERING"),
    os.path.join(BASE, "R16_text/Question Papers/3-1/SOFTWARE ENGINEERING"),
    os.path.join(BASE, "R16_text/Question Papers/4-2/MODERN SOFTWARE ENGINEERING"),
    os.path.join(BASE, "R18 text/3rd Year/Semester 1/SOFTWARE ENGINEERING"),
]

all_rows = []
for d in SE_DIRS:
    for fname in os.listdir(d):
        if fname.endswith(".txt"):
            all_rows.extend(process_file(os.path.join(d, fname)))

# ── merge duplicates: same question text → combine years ──────────────────────
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

final_rows.sort(key=lambda r: (r["topic_tag"], r["bloom_level"], r["raw_question_text"]))

# ── manual overrides for residual misclassifications ──────────────────────────
OVERRIDES = {
    "what is a change? how it can be incorporated in the software.": "SOFTWARE_MAINTENANCE_AND_EVOLUTION",
    "what is the purpose of work in progress documentation?": "AGILE_AND_XP",
    "code goes through four levels of completion. discuss these levels.": "AGILE_AND_XP",
    "real customer involvement is necessary in software development-discuss.": "AGILE_AND_XP",
    "elaborate the strategies for generating trust.": "AGILE_AND_XP",
    "how to find the root-cause? when should we conduct root-cause analysis?": "AGILE_AND_XP",
    "discuss how hard data can be used to drive optimization efforts.": "AGILE_AND_XP",
    "what is meant by documentation? discuss the various types of it.": "AGILE_AND_XP",
    "what is meant by documentation? discuss the various types of it. or": "AGILE_AND_XP",
    "what does feasibility analysis imply when it is discussed within the context of the inception function?": "REQUIREMENTS_ENGINEERING",
    "describe various prototyping techniques and discuss on object oriented analysis and modeling.": "PROCESS_MODELS",
    "what is the role of maintainability in design quality?": "SOFTWARE_DESIGN",
    "how design process is useful in development process? what are different design quality guidelines that lead to a good design?": "SOFTWARE_DESIGN",
    "describe about the design of conventional components.": "SOFTWARE_DESIGN",
    "discuss, how to reduce the user's memory load.": "SOFTWARE_DESIGN",
    "discuss on key things to create a vision statement.": "AGILE_AND_XP",
    "appraise the importance of organizational success.": "AGILE_AND_XP",
    "give the importance of collective code ownership.": "AGILE_AND_XP",
    "is asynchronous integration more efficient than synchronous integration? substantiate your answer.": "AGILE_AND_XP",
    "list the important characteristics of stories.": "AGILE_AND_XP",
    "model the data processing that might take place in e -mail system. you should model the mail-sending and mail-receiving processing separately.": "SYSTEM_MODELING_AND_UML",
    "how to understand the goals and frustrations of customers and end-users? or": "AGILE_AND_XP",
}

GARBAGE_EXACT = {
    "(r16-common to cse, it; r15-common to cse, it; r13-common to cse, it; r09-common to cse, it)",
    "composable d) deployable e) documented. or",
}
for r in final_rows:
    key = r["raw_question_text"].strip().lower()
    if key in OVERRIDES:
        r["topic_tag"] = OVERRIDES[key]

# drop exact garbage strings and remaining short GENERAL_SE fragments
final_rows = [r for r in final_rows if
    r["raw_question_text"].strip().lower() not in GARBAGE_EXACT
    and not (r["topic_tag"] == "GENERAL_SE" and len(r["raw_question_text"]) < 40)
]

OUT = "/home/admin1/WingsAI/group_2/DATA/Question_Paper_Generator/question-paper-predictor/data/Software_Engineering_Dataset.csv"
FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level", "original_marks", "part_a_years", "part_b_years"]
with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(final_rows)

print(f"Done. {len(final_rows)} unique questions written to {OUT}")
