"""
generate_java_master_v2.py
Extracts, deduplicates, and tags Java examination questions across R13, R15, R16, and R22.
Preserves ALL questions (in-syllabus and legacy out-of-syllabus), splits atomic sub-questions,
and performs fuzzy deduplication across years.
"""

import os
import re
import csv
from pathlib import Path
from difflib import SequenceMatcher

CLEANED_DIR = Path("data/cleaned_papers")
OUTPUT_CSV = Path("data/processed_dataset/java_master_v2.csv")

IMAGE_TRIGGERS = re.compile(
    r"shown below|following figure|following circuit|following diagram|following graph|following table",
    re.IGNORECASE
)

# ---------------------------------------------------------------------------
# Bloom Taxonomy Patterns
# ---------------------------------------------------------------------------
BLOOM_PATTERNS = [
    ("Evaluate",   [r"\bevaluate\b", r"\bjustify\b", r"\bassess\b", r"\bcritique\b", r"\bverify\b"]),
    ("Analyze",    [r"\banalyze\b", r"\bdifferentiate\b", r"\bdistinguish\b", r"\bcompare\b", r"\bexamine\b", r"\btrace\b"]),
    ("Apply",      [r"\bwrite a (?:java )?program\b", r"\bprogram\b", r"\bdemonstrate\b", r"\billustrate\b", r"\bconstruct\b", r"\bimplement\b", r"\bdevelop\b", r"\bsolve\b", r"\bcompute\b"]),
    ("Remember",   [r"\bdefine\b", r"\blist\b", r"\bname\b", r"\bstate\b", r"\bwhat is\b", r"\bwhat are\b", r"\bwhich\b"]),
    ("Understand", [r"\bexplain\b", r"\bdescribe\b", r"\bdiscuss\b", r"\bsummarize\b", r"\binterpret\b", r"\bhow\b", r"\bwhy\b"])
]

def infer_bloom(text: str) -> str:
    text_lower = text.lower()
    for level, patterns in BLOOM_PATTERNS:
        if any(re.search(p, text_lower) for p in patterns):
            return level
    return "Understand"

# ---------------------------------------------------------------------------
# Topic Matching Rules (Preserving both R22 and Legacy topics)
# ---------------------------------------------------------------------------
TOPIC_RULES = [
    # Legacy Topics (Kept and tagged rather than dropped)
    ("DATABASE_CONNECTIVITY_JDBC", [
        r"jdbc\b", r"driver ?manager", r"database connectivity", r"resultset", r"preparedstatement"
    ]),
    ("COLLECTIONS_FRAMEWORK", [
        r"\bvector\b", r"hash ?table", r"stack class", r"iterator", r"listiterator",
        r"collection framework", r"collections? in java", r"dictionary class", r"collections? class"
    ]),
    ("SERVLETS_AND_ENTERPRISE_JAVA", [
        r"servlet", r"jsp\b", r"rmi\b", r"corba\b", r"java beans?", r"remote method invocation"
    ]),

    # Unit 5: Swing & Applets
    ("CREATING_AND_PASSING_PARAMETERS_TO_APPLETS", [
        r"parameters? to applet", r"pass(?:ing)? parameters? to (?:an )?applet", r"param tag", r"getparameter"
    ]),
    ("APPLETS_CONCEPTS_AND_LIFECYCLE", [
        r"applet life ?cycle", r"lifecycle of (?:an )?applet", r"life cycle of an applet", r"applet display methods", r"init\(\)", r"applets? vs application", r"\bapplets?\b"
    ]),
    ("MVC_ARCHITECTURE", [
        r"\bmvc\b", r"model[ -]view[ -]controller"
    ]),
    ("SWING_OVERVIEW_AND_LIMITATIONS_OF_AWT", [
        r"limitations? of awt", r"swing vs\.? awt", r"why swing", r"preferred over awt", r"differences? between awt and swing"
    ]),
    ("SWING_CONTAINERS_JFRAME_JAPPLET", [
        r"swing container", r"jframe", r"japplet", r"jcomponent", r"jdialog", r"jpanel"
    ]),
    ("SWING_COMPONENTS", [
        r"swing components?", r"swing class.*button", r"jbutton", r"combo box", r"radio button", r"check box.*swing", r"tabbed pane", r"scroll pane", r"trees? and tables?", r"\bswing\b"
    ]),

    # Unit 4: Event Handling & AWT
    ("ADAPTER_CLASSES", [
        r"adapter class"
    ]),
    ("MOUSE_AND_KEYBOARD_EVENTS", [
        r"mouse event", r"mouse listener", r"mouse motion", r"keyboard event", r"key listener", r"actionevent", r"itemevent", r"item event"
    ]),
    ("EVENT_HANDLING_AND_DELEGATION_MODEL", [
        r"delegation event model", r"event handling", r"event listener", r"event source", r"action listener", r"\bevents?\b"
    ]),
    ("LAYOUT_MANAGERS", [
        r"layout manager", r"flowlayout", r"borderlayout", r"gridlayout", r"cardlayout", r"gridbaglayout"
    ]),
    ("GRAPHICS_PROGRAMMING", [
        r"graphics class", r"drawing and rendering", r"paint\(\)", r"drawline", r"drawrect", r"\bcanvas\b", r"\bgraphics\b"
    ]),
    ("AWT_CONTAINERS_AND_PANELS", [
        r"menubar", r"dialog class", r"panel class", r"scrollpane"
    ]),
    ("AWT_CLASS_HIERARCHY", [
        r"awt (?:class )?hierarchy"
    ]),
    ("AWT_USER_INTERFACE_COMPONENTS", [
        r"awt component", r"scrollbar", r"checkboxgroup", r"choice class", r"button class", r"\bawt\b"
    ]),

    # Unit 3: Exception Handling & Multithreading
    ("MULTITHREADING_VS_MULTITASKING", [
        r"multitasking", r"multiprocessing", r"thread vs process", r"thread based preemptive", r"multithreading vs"
    ]),
    ("DAEMON_THREADS", [
        r"daemon thread"
    ]),
    ("INTER_THREAD_COMMUNICATION", [
        r"inter[ -]thread communication", r"wait\(\).*notify", r"producer[ -]consumer"
    ]),
    ("THREAD_PRIORITIES", [
        r"thread priorit(?:y|ies)", r"setpriority"
    ]),
    ("THREAD_SYNCHRONIZATION", [
        r"synchroniz(?:e|ation|ing) thread", r"synchronized block", r"synchronized method", r"thread lock"
    ]),
    ("THREAD_LIFECYCLE", [
        r"thread life ?cycle", r"life cycle of (?:a )?thread", r"thread state", r"deadlock"
    ]),
    ("CREATING_THREADS", [
        r"creating threads?", r"runnable interface", r"thread class", r"ways of implementing thread", r"multithreading", r"implement(?:ing)? thread", r"\bthreads?\b"
    ]),
    ("TRY_CATCH_THROW_THROWS_FINALLY", [
        r"try.*catch", r"finally block", r"throw vs throws", r"throws clause", r"multiple catch", r"\bfinally\b", r"\bthrow\b", r"\bthrows\b"
    ]),
    ("CUSTOM_EXCEPTIONS", [
        r"custom exception", r"own exception subclass", r"user[ -]defined exception"
    ]),
    ("BUILT_IN_EXCEPTIONS", [
        r"built[ -]in exception", r"checked vs\.? unchecked", r"checked and unchecked", r"checked exceptions?", r"exception hierarchy"
    ]),
    ("EXCEPTION_HANDLING_CONCEPTS", [
        r"exception handling", r"error vs exception", r"error and exception", r"throwable", r"\bexceptions?\b"
    ]),
    ("ENUMERATIONS_AUTOBOXING_ANNOTATIONS_GENERICS", [
        r"enumeration", r"autoboxing", r"annotation", r"generics"
    ]),
    ("STRING_HANDLING_AND_JAVA_UTIL", [
        r"stringtokenizer", r"string ?tokenizer", r"stringbuffer", r"stringbuilder", r"string class", r"string handling", r"scanner class", r"\bscanner\b"
    ]),

    # Unit 2: Inheritance, Packages, Interfaces
    ("EXTENDING_INTERFACES", [
        r"extend(?:ing)? (?:multiple )?interface", r"class extend multiple interface"
    ]),
    ("INTERFACES_DEFINITION_AND_IMPLEMENTATION", [
        r"defining an interface", r"implement(?:ing)? interface", r"multiple inheritance using interface", r"interface vs abstract class", r"\binterfaces?\b"
    ]),
    ("ABSTRACT_CLASSES", [
        r"abstract class", r"abstract method", r"\babstract\b"
    ]),
    ("SUPER_KEYWORD", [
        r"super keyword", r"uses of super", r"super\(\)", r"\bsuper\b"
    ]),
    ("FINAL_KEYWORD", [
        r"final keyword", r"final class", r"final method", r"final variable", r"preventing inheritance", r"\bfinal\b"
    ]),
    ("METHOD_OVERRIDING_AND_POLYMORPHISM", [
        r"method overriding", r"dynamic method dispatch", r"dynamic binding", r"runtime polymorphism", r"polymorphism"
    ]),
    ("CLASSPATH", [
        r"classpath"
    ]),
    ("IMPORTING_PACKAGES", [
        r"importing package", r"import statement", r"import state ?ment", r"importing"
    ]),
    ("PACKAGES_CREATION_AND_ACCESS", [
        r"creating.*package", r"defining.*package", r"accessing.*package", r"\bpackages?\b"
    ]),
    ("ACCESS_CONTROL", [
        r"access specifier", r"access modifier", r"private.*protected.*public", r"access control"
    ]),
    ("INHERITANCE_BASICS_AND_TYPES", [
        r"types of inheritance", r"forms of inheritance", r"subclass", r"superclass", r"\binheritance\b"
    ]),
    ("MEMBER_ACCESS_RULES", [
        r"member access"
    ]),
    ("OBJECT_CLASS", [
        r"object class", r"methods of object class"
    ]),
    ("JAVA_IO_BASICS", [
        r"java\.io", r"file input/output", r"byte streams?", r"character streams?", r"fileinputstream", r"fileoutputstream", r"\bfile\b"
    ]),

    # Unit 1: Java Basics and OOP
    ("NESTED_AND_INNER_CLASSES", [
        r"inner class", r"nested class", r"anonymous inner class", r"nested interface"
    ]),
    ("GARBAGE_COLLECTION", [
        r"garbage collection", r"gc\(\)", r"finalize\(\)"
    ]),
    ("THIS_KEYWORD", [
        r"this keyword", r"this reference", r"this\(\)", r"\bthis\b"
    ]),
    ("METHOD_AND_CONSTRUCTOR_OVERLOADING", [
        r"constructor overloading", r"method overloading", r"\boverloading\b"
    ]),
    ("CONSTRUCTORS_AND_METHODS", [
        r"\bconstructors?\b", r"static method", r"static variable", r"static block", r"\bmethods?\b"
    ]),
    ("CLASSES_AND_OBJECTS", [
        r"class and object", r"classes and objects", r"instantiation", r"difference between a class and an object", r"classes and instances"
    ]),
    ("TYPE_CONVERSION_AND_CASTING", [
        r"type conversion", r"type casting", r"narrowing", r"widening"
    ]),
    ("CONTROL_STATEMENTS", [
        r"control statement", r"conditional statement", r"loops?", r"switch statement"
    ]),
    ("OPERATORS_AND_EXPRESSIONS", [
        r"operators? in java", r"operator precedence", r"bitwise operator", r"ternary operator", r"\boperators?\b"
    ]),
    ("DATA_TYPES_VARIABLES_ARRAYS", [
        r"data types?", r"variables?", r"arrays? in java", r"\barrays?\b", r"scope and lifetime", r"size of char"
    ]),
    ("PARAMETER_PASSING_AND_RECURSION", [
        r"parameter passing", r"pass by value", r"recursion"
    ]),
    ("OOP_PARADIGM_AND_CONCEPTS", [
        r"oop paradigm", r"oop concept", r"data abstraction", r"encapsulation", r"features of java", r"java buzzwords", r"platform independent", r"byte code", r"jvm", r"java virtual machine"
    ])
]

def assign_topic(q_text: str) -> str:
    cleaned = q_text.lower()
    for tag, patterns in TOPIC_RULES:
        for p in patterns:
            if re.search(p, cleaned):
                return tag
    return "OOP_PARADIGM_AND_CONCEPTS"

def parse_year(filename: str) -> int | None:
    m = re.search(r"(\d{4})", filename)
    return int(m.group(1)) if m else None

def clean_text_basic(text: str) -> str:
    text = re.sub(r"^\s*(?:\d{1,2}\.\s*)?(?:\(?[a-j]\)?[.\s]*)?", "", text)
    text = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\[[\d\+\s]+\]\s*$", "", text)
    text = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\[[\d\+\s]+\]\s*$", "", text)
    text = re.sub(r"\s*Used Papers.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def normalize_for_fuzzy(text: str) -> str:
    norm = re.sub(r"[^\w\s]", "", text.lower())
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm

def extract_questions_from_paper(raw_text: str) -> list[dict]:
    questions = []

    part_split = re.split(r"(?:^|\n)\s*PART\s*[\-\u2013\u2014]?\s*B\b.*", raw_text, flags=re.IGNORECASE)
    part_a_raw = part_split[0] if len(part_split) >= 2 else ""
    part_b_raw = part_split[1] if len(part_split) >= 2 else raw_text

    # ----------------- PART A EXTRACTION -----------------
    if part_a_raw:
        a_pattern = re.compile(
            r"(?:^|\n)\s*(?:1\.\s*)?([a-j])\)\s*(.+?)(?=(?:\n\s*(?:1\.\s*)?[a-j]\)|\Z))",
            re.DOTALL | re.IGNORECASE
        )
        for m in a_pattern.finditer(part_a_raw):
            content = m.group(2).strip()
            # Accurately extract mark [1], [2], or [3]
            m_m = re.search(r"\[([1-3])\]", content)
            marks = int(m_m.group(1)) if m_m else 1

            q_clean = clean_text_basic(content)
            if len(q_clean) > 15 and not q_clean.startswith(("Code No", "Note:", "Max", "Time")):
                questions.append({"text": q_clean, "marks": marks, "part": "A"})

    # ----------------- PART B EXTRACTION -----------------
    q_split_pattern = re.compile(r"(?:^|\n)\s*([1-9]|1[0-5])\.(?!\d)\s*", re.IGNORECASE)
    b_splits = q_split_pattern.split(part_b_raw)

    for i in range(1, len(b_splits), 2):
        q_num = int(b_splits[i])
        block = b_splits[i+1].strip()

        block = re.sub(r"(?:^|\n)\s*OR\s*(?:\n|\Z)", "\n", block, flags=re.IGNORECASE).strip()

        marks_match = re.search(r"\[([\d\+]+)\]", block)
        marks_raw = marks_match.group(1) if marks_match else "10"
        mark_parts = [int(x) for x in marks_raw.split("+") if x.isdigit()]
        if not mark_parts:
            mark_parts = [10]

        clean_block = re.sub(r"\[[\d\+\s]+\]", "", block).strip()

        sub_pattern = re.compile(r"(?:^|\n)\s*(?:\(([a-d])\)|([a-d])\))\s*", re.IGNORECASE)
        sub_matches = list(sub_pattern.finditer(clean_block))

        if len(sub_matches) >= 2:
            premise = clean_block[:sub_matches[0].start()].strip()
            premise = re.sub(r"^Code No:.*$", "", premise, flags=re.M).strip()
            for idx, sm in enumerate(sub_matches):
                start = sm.end()
                end = sub_matches[idx+1].start() if idx + 1 < len(sub_matches) else len(clean_block)
                sub_txt = clean_block[start:end].strip()
                sub_letter = (sm.group(1) or sm.group(2)).lower()
                m_val = mark_parts[idx] if idx < len(mark_parts) else (sum(mark_parts) // len(sub_matches))

                if premise and len(premise) > 15:
                    full_text = f"{premise} ({sub_letter}) {sub_txt}"
                else:
                    full_text = sub_txt

                full_text = clean_text_basic(full_text)
                if len(full_text) > 15:
                    questions.append({"text": full_text, "marks": m_val, "part": "B"})
        else:
            total_m = sum(mark_parts)
            full_text = clean_text_basic(clean_block)
            if len(full_text) > 15 and not full_text.startswith(("Code No", "Note:", "Max", "Time")):
                questions.append({"text": full_text, "marks": total_m, "part": "B"})

    return questions

def run():
    java_files = sorted(list(CLEANED_DIR.rglob("*JAVA*/**/*.txt")) + list(CLEANED_DIR.rglob("*Java*/**/*.txt")))
    print(f"Processing {len(java_files)} Java question paper files...")

    unique_questions: list[dict] = []

    def find_match(norm_text: str, tag: str) -> dict | None:
        for entry in unique_questions:
            if entry["topic_tag"] == tag:
                len_ratio = len(norm_text) / max(len(entry["norm"]), 1)
                if 0.75 <= len_ratio <= 1.33:
                    ratio = SequenceMatcher(None, norm_text, entry["norm"]).ratio()
                    if ratio >= 0.90:
                        return entry
        return None

    total_extracted = 0
    merged_count = 0

    for f in java_files:
        year = parse_year(f.name)
        if not year:
            continue

        raw = f.read_text(encoding="utf-8", errors="ignore")
        extracted = extract_questions_from_paper(raw)
        total_extracted += len(extracted)

        for q in extracted:
            q_text = q["text"]
            if IMAGE_TRIGGERS.search(q_text):
                continue
            if len(q_text.split()) < 3:
                continue

            tag = assign_topic(q_text)
            norm = normalize_for_fuzzy(q_text)
            matched_entry = find_match(norm, tag)

            if matched_entry:
                merged_count += 1
                if q["part"] == "A":
                    matched_entry["part_a_years"].add(year)
                else:
                    matched_entry["part_b_years"].add(year)
                if len(q_text) > len(matched_entry["text"]):
                    matched_entry["text"] = q_text
                    matched_entry["norm"] = norm
            else:
                entry = {
                    "text": q_text,
                    "norm": norm,
                    "marks": q["marks"],
                    "part_a_years": {year} if q["part"] == "A" else set(),
                    "part_b_years": {year} if q["part"] == "B" else set(),
                    "topic_tag": tag
                }
                unique_questions.append(entry)

    print(f"Total atomic questions extracted: {total_extracted}")
    print(f"Fuzzy merges: {merged_count}")
    print(f"Total unique questions preserved: {len(unique_questions)}")

    rows = []
    for q in unique_questions:
        bloom = infer_bloom(q["text"])
        rows.append({
            "subject_name": "Object Oriented Programming through Java",
            "raw_question_text": q["text"],
            "topic_tag": q["topic_tag"],
            "bloom_level": bloom,
            "original_marks": q["marks"],
            "part_a_years": sorted(list(q["part_a_years"])),
            "part_b_years": sorted(list(q["part_b_years"]))
        })

    rows.sort(key=lambda r: (r["topic_tag"], r["original_marks"]))

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "subject_name", "raw_question_text", "topic_tag",
            "bloom_level", "original_marks", "part_a_years", "part_b_years"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Saved dataset with {len(rows)} rows to {OUTPUT_CSV}")

if __name__ == "__main__":
    run()
