"""
remediate_java_dataset.py
Implements the 4-point refinement plan:
1. Fixes all split-word OCR kerning and unstripped footers.
2. Normalizes COVID-era 15-mark questions to 10-marks.
3. Implements strict, multi-pass Bloom taxonomy classification (fixing Apply vs Understand/Remember/Analyze/Evaluate).
4. Refines topic_tag assignments (thread priorities, multithreading vs multitasking, applet parameters, try/catch).
5. Splits the dataset into:
   - java_master_final.csv (100% strictly aligned with R22 syllabus)
   - java_unmatched_archive.csv (legacy out-of-syllabus questions: JDBC, Collections, Servlets).
"""

import re
import csv
from pathlib import Path
from difflib import SequenceMatcher

INPUT_CSV = Path("data/processed_dataset/java_master_final.csv")
OUTPUT_R22_CSV = Path("data/processed_dataset/java_master_final.csv")
OUTPUT_ARCHIVE_CSV = Path("data/processed_dataset/java_unmatched_archive.csv")

# ---------------------------------------------------------------------------
# 1. OCR Kerning & Artifact Repair Dictionary
# ---------------------------------------------------------------------------
KERNING_REPLACEMENTS = [
    (r"\bp\s+olymorphism\b", "polymorphism"),
    (r"\bpr\s+int\b", "print"),
    (r"\bprog\s+ram\b", "program"),
    (r"\bprog\s+ramming\b", "programming"),
    (r"\bsw\s+ing\b", "swing"),
    (r"\btext\s+filed\b", "text field"),
    (r"\bbr\s+ief\b", "brief"),
    (r"\bill\s+ustrate\b", "illustrate"),
    (r"\bh\s+andling\b", "handling"),
    (r"\bdispat\s+ch\b", "dispatch"),
    (r"\bparam\s+eters\b", "parameters"),
    (r"\bmult\s+iprocessing\b", "multiprocessing"),
    (r"\bmult\s+ithreading\b", "multithreading"),
    (r"\bconst\s+ructor\b", "constructor"),
    (r"\binher\s+itance\b", "inheritance"),
    (r"\binter\s+face\b", "interface"),
    (r"\bstat\s+ement\b", "statement"),
    (r"\bdi\s+splay\b", "display"),
    (r"\bfo\s+r\b", "for"),
    (r"\bprobl\s+em\b", "problem"),
    (r"\bmaintai\s+nability\b", "maintainability"),
    (r"\bmaintainabi\s+lity\b", "maintainability"),
]

def clean_kerning_and_artifacts(text: str) -> str:
    # 1. Strip remaining trailing footers
    text = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", text, flags=re.IGNORECASE)
    # 2. Fix kerning splits
    for pat, rep in KERNING_REPLACEMENTS:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    # 3. Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

# ---------------------------------------------------------------------------
# 2. Strict Bloom's Taxonomy Classifier
# ---------------------------------------------------------------------------
def classify_bloom_strict(q_text: str) -> str:
    q = q_text.lower()

    # Rule 1: APPLY - Questions requiring active programming, writing code, implementation, or calculation
    # Takes precedence over introductory "Define" or "With"
    active_coding_patterns = [
        r"write a (?:java )?program",
        r"write a prog\s*ram",
        r"write an applet",
        r"develop an applet",
        r"develop a program",
        r"implement a (?:java )?program",
        r"write (?:java )?code",
        r"program to (?:illustrate|demonstrate|implement|create|display|show|count|check|accept|search|reverse)",
        r"illustrate .* with an? (?:example )?(?:java )?program",
        r"illustrate .* with a program",
        r"demonstrate .* with a program",
        r"with a program,? illustrate",
        r"create a (?:simple )?(?:user interface|frame window|applet|program)",
        r"\bconstruct\b",
        r"\bsolve\b",
        r"\bcompute\b",
        r"\bcalculate\b"
    ]
    if any(re.search(p, q) for p in active_coding_patterns):
        return "Apply"

    # Rule 2: EVALUATE - Justification, evaluation, critique, appraisal, trade-offs
    eval_patterns = [
        r"\bjustify\b",
        r"\bevaluate\b",
        r"\bassess\b",
        r"\bcritique\b",
        r"\bappraise\b",
        r"trade[ -]offs?",
        r"which paradigm is preferred"
    ]
    if any(re.search(p, q) for p in eval_patterns):
        return "Evaluate"

    # Rule 3: ANALYZE - Comparison, differentiation, contrast, breakdown of pros/cons
    analyze_patterns = [
        r"\bdifferentiate\b",
        r"\bdistinguish\b",
        r"differences? between",
        r"\bcompare\b",
        r"\bcontrast\b",
        r"\bdiffer from\b",
        r"advantages and disadvantages",
        r"pros and cons",
        r"how is .* different",
        r"comparison of"
    ]
    if any(re.search(p, q) for p in analyze_patterns):
        return "Analyze"

    # Rule 4: REMEMBER - Direct recall, naming, definitions (without explanatory requirement)
    remember_patterns = [
        r"^what is\b",
        r"^what are\b",
        r"^define\b",
        r"^list\b",
        r"^name\b",
        r"^state\b",
        r"give (?:any )?(?:two|four|the) (?:examples|limitations|properties|syntax)"
    ]
    has_remember = any(re.search(p, q) for p in remember_patterns)
    has_understand = any(k in q for k in ["explain", "describe", "discuss", "how to", "why", "illustrate", "how does"])

    if has_remember and not has_understand:
        return "Remember"

    # Rule 5: UNDERSTAND - Conceptual explanation, descriptions, reasoning
    return "Understand"

# ---------------------------------------------------------------------------
# 3. Topic Refinements (Fixing keyword priority & regex misses)
# ---------------------------------------------------------------------------
def refine_topic_tag(q_text: str, current_tag: str) -> str:
    q = q_text.lower()

    # Multithreading vs Multitasking (thread vs process)
    if any(k in q for k in ["thread and a process", "thread and process", "thread vs process", "multitasking"]):
        return "MULTITHREADING_VS_MULTITASKING"

    # Thread priorities
    if any(k in q for k in ["priorit", "setpriority"]):
        return "THREAD_PRIORITIES"

    # Passing parameters to applets
    if "parameter" in q and "applet" in q:
        return "CREATING_AND_PASSING_PARAMETERS_TO_APPLETS"

    # Try, Catch, Throw, Throws, Finally syntax
    if any(k in q for k in ["try statement", "nested try", "catch block", "multiple catch", "finally block", "throw vs throws", "throws clause"]):
        return "TRY_CATCH_THROW_THROWS_FINALLY"

    # Layout Managers
    if any(k in q for k in ["layout", "flowlayout", "borderlayout", "gridlayout", "cardlayout", "gridbaglayout"]):
        return "LAYOUT_MANAGERS"

    # Swing Components
    if any(k in q for k in ["jtoggle", "jbutton", "jcombobox", "jlist", "jcheckbox", "jradiobutton", "radio buttion", "radio button"]):
        return "SWING_COMPONENTS"

    # I/O Streams
    if any(k in q for k in ["stream", "fileinputstream", "fileoutputstream", "console class", "serialization", "file and director"]):
        return "JAVA_IO_BASICS"

    # Control Statements
    if any(k in q for k in ["'for' statement", "for loop", "selection statement", "switch statement", "control statement"]):
        return "CONTROL_STATEMENTS"

    # Inheritance
    if any(k in q for k in ["multiple inheritance", "class hierarchy", "multilevel class hierarchy"]):
        return "INHERITANCE_BASICS_AND_TYPES"

    # Access Control
    if any(k in q for k in ["access protection", "access specifier", "access modifier"]):
        return "ACCESS_CONTROL"

    return current_tag

# ---------------------------------------------------------------------------
# 4. Legacy Topic Identification
# ---------------------------------------------------------------------------
LEGACY_TOPICS = {
    "DATABASE_CONNECTIVITY_JDBC",
    "COLLECTIONS_FRAMEWORK",
    "SERVLETS_AND_ENTERPRISE_JAVA"
}

def run():
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} questions from {INPUT_CSV}")

    cleaned_rows = []
    for r in rows:
        # Step 1: Clean kerning and footers
        clean_text = clean_kerning_and_artifacts(r["raw_question_text"])
        r["raw_question_text"] = clean_text

        # Step 2: Normalize COVID-era 15-mark questions to 10 marks
        if int(r["original_marks"]) > 10:
            r["original_marks"] = 10

        # Step 3: Refine topic tag
        r["topic_tag"] = refine_topic_tag(clean_text, r["topic_tag"])

        # Step 4: Strict Bloom classification
        r["bloom_level"] = classify_bloom_strict(clean_text)

        cleaned_rows.append(r)

    # Step 5: Re-deduplicate across years after kerning fixes
    unique_r22 = []
    unique_legacy = []

    def merge_or_append(target_list, row):
        norm = re.sub(r"[^\w\s]", "", row["raw_question_text"].lower())
        norm = re.sub(r"\s+", " ", norm).strip()

        for existing in target_list:
            if existing["topic_tag"] == row["topic_tag"]:
                e_norm = re.sub(r"[^\w\s]", "", existing["raw_question_text"].lower())
                e_norm = re.sub(r"\s+", " ", e_norm).strip()
                if SequenceMatcher(None, norm, e_norm).ratio() >= 0.90:
                    # Merge years
                    e_a = set(eval(existing["part_a_years"]))
                    e_b = set(eval(existing["part_b_years"]))
                    r_a = set(eval(row["part_a_years"]))
                    r_b = set(eval(row["part_b_years"]))
                    existing["part_a_years"] = str(sorted(list(e_a | r_a)))
                    existing["part_b_years"] = str(sorted(list(e_b | r_b)))
                    return
        target_list.append(row)

    for r in cleaned_rows:
        if r["topic_tag"] in LEGACY_TOPICS:
            merge_or_append(unique_legacy, r)
        else:
            merge_or_append(unique_r22, r)

    print(f"\nFinal Separation Results:")
    print(f"  R22 Master In-Syllabus Questions: {len(unique_r22)}")
    print(f"  Legacy Archive Questions:         {len(unique_legacy)}")

    fieldnames = [
        "subject_name", "raw_question_text", "topic_tag",
        "bloom_level", "original_marks", "part_a_years", "part_b_years"
    ]

    # Write R22 Master Final CSV
    OUTPUT_R22_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_R22_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in unique_r22:
            writer.writerow(r)

    # Write Legacy Archive CSV
    with open(OUTPUT_ARCHIVE_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in unique_legacy:
            writer.writerow(r)

    print(f"\nSaved R22 clean dataset to: {OUTPUT_R22_CSV.resolve()}")
    print(f"Saved Legacy archive dataset to: {OUTPUT_ARCHIVE_CSV.resolve()}")

if __name__ == "__main__":
    run()
