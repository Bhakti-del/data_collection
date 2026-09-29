"""
parser.py
---------
Reads all question paper .txt files for Operating Systems, Database Management Systems,
and Software Engineering across all regulations, cleans noise, extracts individual
questions, and outputs questions_raw.csv.

Fixes applied:
  1. Noise fragments (header tails, instruction leftovers) are caught and dropped
  2. Part A sub-questions (1.a, 1.b ... 1.j) are split into individual rows
  3. Marks on a separate line (e.g. [5+5] alone on next line) are attached correctly

Usage:
    python src/parser.py

Output:
    data/questions_raw.csv
"""

import re
import csv
from pathlib import Path

# ── CONFIG ────────────────────────────────────────────────────────────────────

ROOT   = Path("Data/Text_data/All_Reg_QP_Text_data")
OUTPUT = Path("data/questions_raw.csv")

TARGET_SUBJECTS = {
    "OPERATING SYSTEMS":           "Operating Systems",
    "DATABASE MANAGEMENT SYSTEMS": "Database Management Systems",
    "SOFTWARE ENGINEERING":        "Software Engineering",
}

# ── METADATA FROM PATH ────────────────────────────────────────────────────────

def get_regulation(path: Path) -> str:
    for part in path.parts:
        m = re.match(r"(R\d{2})", part, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return "UNKNOWN"

def get_year_sem(path: Path) -> str:
    parts = [p.name for p in path.parents] + [path.name]
    for part in parts:
        if re.match(r"^\d-\d$", part):
            return part
    year_map = {"1st": "1", "2nd": "2", "3rd": "3", "4th": "4"}
    sem_map  = {"semester 1": "1", "semester 2": "2"}
    year = sem = None
    for part in parts:
        pl = part.lower().strip()
        for k, v in year_map.items():
            if pl.startswith(k) and "year" in pl:
                year = v
        if pl in sem_map:
            sem = sem_map[pl]
    return f"{year}-{sem}" if year and sem else "UNKNOWN"

def get_session_year(filename: str):
    name = Path(filename).stem.upper()
    year_m = re.search(r"(20\d{2})", name)
    year = int(year_m.group(1)) if year_m else None
    if any(x in name for x in ["NOV", "DEC"]):   session = "Nov-Dec"
    elif any(x in name for x in ["APR", "MAY"]): session = "Apr-May"
    elif any(x in name for x in ["AUG", "SEP"]): session = "Aug-Sep"
    elif any(x in name for x in ["JAN", "FEB"]): session = "Jan-Feb"
    elif "MAR" in name:                           session = "Mar"
    elif "OCT" in name:                           session = "Oct"
    elif "JUN" in name:                           session = "Jun"
    elif "JUL" in name:                           session = "Jul"
    else:                                         session = "Unknown"
    return session, year

# ── NOISE PATTERNS ────────────────────────────────────────────────────────────

NOISE_PATTERNS = [
    r"^code\s+no[\s:]+",
    r"jawaharlal nehru",
    r"b\.?\s*tech",
    r"^\s*time\s*:",
    r"max\.?\s*marks",
    r"^\s*note\s*:",
    r"^\s*i{1,3}[).]\s+",
    r"answer any (five|all|one)",
    r"all questions carry",
    r"each question carries",
    r"^-\s*-\s*-\s*$",
    r"^---+",
    r"jntuh\s+used",
    r"jntuh\s+paper",
    r"\bused\s+paper\b",
    r"\bra\s+used\b",
    r"^\s*r1[3568]\s*$",
    r"^\s*r22\s*$",
    r"\d{2}-\d{2}-\d{4}",
    r"^\s*\(common to",
    r"part [ab] is compulsory",
    r"consists of part",
    r"oo[0o]oo|oo[oO]oo",
    r"text books?:",
    r"reference books?:",
    r"^\s*\d+\.\s*(silberschatz|pressman|sommerville|tanenbaum|korth|galvin)",
    r"prerequisites?:",
    r"course objectives?:",
    r"course outcomes?:",
    # Subject name lines that appear as standalone lines mid-file
    r"^\s*(operating systems|database management systems|software engineering)"
    r"\s*(\(.*?\))?\s*$",
    # Instruction tail fragments that survive multi-line header removal
    r"and may have\s+a,?\s*b",
    r"\bsub\s+questions?\b",
    r"^\s*\(computer science(\s+and\s+engineering)?\)?\s*$",
    r"^\s*\(r\d{2}[\s\-]",          # regulation tags like (R16-Common to CSE...)
]
NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)

SECTION_RE = re.compile(
    r"^\s*PART\s*[-–]\s*[AB]\b.*$"
    r"|^\s*\(\s*\d+\s*[Mm]arks?\s*\)\s*$",
    re.IGNORECASE
)

# A line that is ONLY a marks pattern e.g. "   [5+5]   " or "   [10]   "
MARKS_ONLY_RE = re.compile(r"^\s*\[(\d+(?:\+\d+)?)\]\s*$")

# Marks at end of text
MARKS_END_RE = re.compile(r"\[(\d+(?:\+\d+)?)\]\s*$")

# Noise fragments that can appear inside extracted question text
INVALID_TEXT_FRAGMENTS = [
    "sub questions",
    "common to cse",
    "common to r1",
    "used paper",
    " ra used",
    "and may have a",
]

def is_invalid_question(text: str) -> bool:
    t = text.lower()
    if len(text.strip()) < 15:
        return True
    if any(f in t for f in INVALID_TEXT_FRAGMENTS):
        return True
    return False

# ── CLEANING ──────────────────────────────────────────────────────────────────

def clean_lines(raw: str):
    """
    Returns (cleaned_lines, paper_format)
    Each element of cleaned_lines is either a string or the special
    token ('MARKS_ONLY', N) for a line that contains only marks.
    """
    lines = raw.splitlines()
    cleaned = []
    has_part_a = False

    for line in lines:
        s = line.strip()
        if not s:
            continue
        if NOISE_RE.search(s):
            continue
        if SECTION_RE.match(s):
            if re.search(r"PART\s*[-–]\s*A", s, re.IGNORECASE):
                has_part_a = True
            continue
        # Check if line is ONLY a marks tag — tag it specially
        m = MARKS_ONLY_RE.match(s)
        if m:
            marks_val = sum(int(x) for x in m.group(1).split("+"))
            cleaned.append(("MARKS_ONLY", marks_val))
            continue
        cleaned.append(s)

    fmt = "PART_AB" if has_part_a else "FLAT"
    return cleaned, fmt

# ── MARKS HELPERS ─────────────────────────────────────────────────────────────

def strip_marks(text: str):
    """Strip trailing [N] or [N+N] from text. Returns (clean_text, marks)."""
    m = MARKS_END_RE.search(text)
    if m:
        marks = sum(int(x) for x in m.group(1).split("+"))
        return text[:m.start()].strip(), marks
    return text.strip(), 0

def infer_marks(question_type: str) -> int:
    """Fallback marks when none found in text."""
    return 2 if question_type == "PART_A" else 10

# ── QUESTION EXTRACTION ───────────────────────────────────────────────────────

QNUM_RE = re.compile(r"^\s*(\d+)\s*[.)]")
# Part A sub-question: standalone a) b) c) ... j)
PARTA_SUBQ_RE = re.compile(r"^\s*([a-j])\s*[.)]\s*(.*)", re.DOTALL)
# Part B sub-question: a) b) within a Part B question
PARTB_SUBQ_RE = re.compile(r"^\s*([a-e])\s*[.)]\s*(.*)", re.DOTALL)
OR_RE = re.compile(r"^\s*OR\s*$", re.IGNORECASE)

def unit_from_qnum(n: int) -> int:
    if n <= 1:
        return 0
    return ((n - 2) // 2) + 1

def extract_questions(lines: list, fmt: str) -> list:
    """
    Returns list of dicts: {raw_question_text, question_type, original_marks, unit_number}

    Key behaviours:
    - Part A (question 1): each sub-question a)..j) becomes its OWN row
    - Part B (questions 2-11): sub-questions a) b) are appended to the same row
    - Marks-only lines are attached to the preceding question
    - Orphan lines before any question number are discarded
    """
    questions = []
    current_parts = []
    current_type  = "PART_A"
    current_unit  = 0
    in_part_a     = False
    has_question  = False   # True once we've seen a question number

    def flush(qtype=None, unit=None):
        nonlocal current_type, current_unit
        t = qtype or current_type
        u = unit  if unit is not None else current_unit
        if not current_parts:
            return
        text = " ".join(str(p) for p in current_parts).strip()
        text = re.sub(r"\s{2,}", " ", text)
        text, marks = strip_marks(text)
        if marks == 0:
            marks = infer_marks(t)
        if not is_invalid_question(text):
            questions.append({
                "raw_question_text": text,
                "question_type":     t,
                "original_marks":    marks,
                "unit_number":       u,
            })
        current_parts.clear()

    for item in lines:
        # Handle marks-only token — attach to current question
        if isinstance(item, tuple) and item[0] == "MARKS_ONLY":
            if current_parts:
                current_parts.append(f"[{item[1]}]")
            continue

        line = item  # plain string from here

        # OR separator
        if OR_RE.match(line):
            flush()
            continue

        # Question number line
        qnum_m = QNUM_RE.match(line)
        if qnum_m:
            qnum = int(qnum_m.group(1))
            rest = line[qnum_m.end():].strip()

            if fmt == "PART_AB":
                if qnum == 1:
                    # Entering Part A — flush any prior, set state
                    flush()
                    in_part_a = True
                    current_type = "PART_A"
                    current_unit = 0
                    has_question = True
                    # rest might be "a) What is..." — handle inline sub-question
                    sub_m = PARTA_SUBQ_RE.match(rest)
                    if sub_m:
                        flush()
                        current_parts.append(sub_m.group(2))
                    elif rest:
                        current_parts.append(rest)
                else:
                    # Entering Part B
                    flush()
                    in_part_a = False
                    current_type = "PART_B"
                    current_unit = unit_from_qnum(qnum)
                    has_question = True
                    # strip sub-question letter if immediately following: "2.a) ..."
                    rest = re.sub(r"^[a-e]\s*[.)]\s*", "", rest)
                    if rest:
                        current_parts.append(rest)
            else:
                # FLAT format
                flush()
                in_part_a = False
                current_type = "PART_B"
                current_unit = qnum
                has_question = True
                rest = re.sub(r"^[a-e]\s*[.)]\s*", "", rest)
                if rest:
                    current_parts.append(rest)
            continue

        # Sub-question line
        if has_question:
            if in_part_a:
                # In Part A: each a)..j) is a NEW question
                sub_m = PARTA_SUBQ_RE.match(line)
                if sub_m:
                    flush()   # flush previous sub-question
                    content = sub_m.group(2).strip()
                    if content:
                        current_parts.append(content)
                    continue
            else:
                # In Part B: a) b) are continuation of same question
                sub_m = PARTB_SUBQ_RE.match(line)
                if sub_m:
                    content = sub_m.group(2).strip()
                    if content:
                        current_parts.append(content)
                    continue

        # Plain continuation line — only append if we have an active question
        if has_question:
            current_parts.append(line)

    flush()
    return questions

# ── DIAGRAM DETECTION ─────────────────────────────────────────────────────────

DIAGRAM_KEYWORDS = [
    "figure", "shown below", "following circuit", "given diagram",
    "above circuit", "shown in fig", "draw the circuit",
    "refer to the figure", "as shown", "given figure",
]

def has_diagram(text: str) -> bool:
    t = text.lower()
    return any(kw in t for kw in DIAGRAM_KEYWORDS)

# ── FILE DISCOVERY ────────────────────────────────────────────────────────────

def find_subject_files():
    for txt_path in sorted(ROOT.rglob("*.txt")):
        folder_name = txt_path.parent.name.upper()
        if folder_name in TARGET_SUBJECTS:
            yield txt_path, TARGET_SUBJECTS[folder_name]

# ── MAIN ──────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "subject_name", "raw_question_text", "question_type",
    "original_marks", "unit_number", "regulation", "year",
    "session", "year_sem", "has_diagram", "data_quality",
]

def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    file_count = 0
    subject_counts = {}

    for txt_path, subject_name in find_subject_files():
        regulation        = get_regulation(txt_path)
        year_sem          = get_year_sem(txt_path)
        session, year     = get_session_year(txt_path.name)

        try:
            raw = txt_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            print(f"  [ERROR] {txt_path}: {e}")
            continue

        if "[SCANNED IMAGE PDF" in raw:
            continue

        cleaned, fmt   = clean_lines(raw)
        questions      = extract_questions(cleaned, fmt)
        file_count    += 1
        subject_counts[subject_name] = subject_counts.get(subject_name, 0) + len(questions)

        print(f"  {regulation:4s} | {year_sem:5s} | {session:8s} {year} | "
              f"{subject_name:35s} | {len(questions):3d} Qs [{fmt}]")

        for q in questions:
            diag = has_diagram(q["raw_question_text"])
            rows.append({
                "subject_name":      subject_name,
                "raw_question_text": q["raw_question_text"],
                "question_type":     q["question_type"],
                "original_marks":    q["original_marks"],
                "unit_number":       q["unit_number"],
                "regulation":        regulation,
                "year":              year if year else "",
                "session":           session,
                "year_sem":          year_sem,
                "has_diagram":       diag,
                "data_quality":      "DIAGRAM_MISSING" if diag else "COMPLETE",
            })

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n{'='*65}")
    print(f"Files processed : {file_count}")
    print(f"Total rows      : {len(rows)}")
    for subj, cnt in subject_counts.items():
        print(f"  {subj:35s} : {cnt} questions")
    print(f"Output          : {OUTPUT}")
    print(f"{'='*65}")

if __name__ == "__main__":
    main()
