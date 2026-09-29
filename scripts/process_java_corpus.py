"""
process_java_corpus.py
Extracts, deduplicates, and tags Java examination questions across R13, R15, R16, and R22.
Exports data/processed_dataset/java_master.csv with 7 canonical fields.
"""

import os
import re
import csv
import json
from pathlib import Path

CLEANED_DIR = Path("data/cleaned_papers")
OUTPUT_CSV = Path("data/processed_dataset/java_master.csv")
OUTPUT_JSON = Path("data/processed_dataset/java_all_extracted.json")

IMAGE_TRIGGERS = re.compile(
    r"shown below|following figure|following circuit|following diagram|following graph|following table",
    re.IGNORECASE
)

# Bloom Taxonomy Keywords
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

# High-precision concept matcher for R22 Java Topics
# Evaluated in strict priority order.
TOPIC_RULES = [
    # 0. Out of syllabus (R13/R15 topics dropped in R22 Java)
    ("OUT_OF_SYLLABUS", [
        r"jdbc\b", r"driver ?manager", r"database connectivity", r"resultset", r"preparedstatement",
        r"\bvector\b", r"hash ?table", r"stack class", r"iterator", r"listiterator",
        r"collection framework", r"collections? in java", r"dictionary class",
        r"servlet", r"jsp\b", r"rmi\b", r"corba\b", r"java beans?", r"remote method invocation"
    ]),

    # Unit 5: Swing & Applets
    ("CREATING_AND_PASSING_PARAMETERS_TO_APPLETS", [
        r"parameters? to applet", r"pass(?:ing)? parameters? to (?:an )?applet", r"param tag", r"getparameter"
    ]),
    ("APPLETS_CONCEPTS_AND_LIFECYCLE", [
        r"applet life cycle", r"lifecycle of (?:an )?applet", r"life cycle of an applet", r"applet display methods", r"init\(\)", r"applets? vs application", r"\bapplets?\b"
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
    ("AWT_USER_INTERFACE_COMPONENTS", [
        r"awt component", r"awt class hierarchy", r"scrollbar", r"checkboxgroup", r"choice class", r"button class", r"\bawt\b"
    ]),

    # Unit 3: Exception Handling & Multithreading
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
        r"thread life cycle", r"life cycle of (?:a )?thread", r"thread state", r"deadlock"
    ]),
    ("CREATING_THREADS", [
        r"creating threads?", r"runnable interface", r"thread class", r"thread vs process", r"multithreading", r"\bthreads?\b"
    ]),
    ("TRY_CATCH_THROW_THROWS_FINALLY", [
        r"try.*catch", r"finally block", r"throw vs throws", r"throws clause", r"multiple catch", r"\bfinally\b", r"\bthrow\b", r"\bthrows\b"
    ]),
    ("CUSTOM_EXCEPTIONS", [
        r"custom exception", r"own exception subclass", r"user[ -]defined exception"
    ]),
    ("BUILT_IN_EXCEPTIONS", [
        r"built[ -]in exception", r"checked vs\.? unchecked", r"checked and unchecked", r"exception hierarchy"
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
        r"extend(?:ing)? (?:multiple )?interface"
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
    ("INHERITANCE_BASICS_AND_TYPES", [
        r"types of inheritance", r"forms of inheritance", r"subclass", r"superclass", r"\binheritance\b"
    ]),
    ("MEMBER_ACCESS_RULES", [
        r"member access", r"access specifier", r"access modifier", r"private.*protected.*public"
    ]),
    ("OBJECT_CLASS", [
        r"object class", r"methods of object class"
    ]),
    ("JAVA_IO_BASICS", [
        r"java\.io", r"file input/output", r"byte streams?", r"character streams?", r"fileinputstream", r"fileoutputstream", r"\bfile\b"
    ]),

    # Unit 1: Java Basics and OOP
    ("NESTED_AND_INNER_CLASSES", [
        r"inner class", r"nested class", r"anonymous inner class"
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
        r"class and object", r"classes and objects", r"instantiation", r"difference between a class and an object"
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
    return "OOP_PARADIGM_AND_CONCEPTS" # Default fallback for general Java OOP questions

def parse_year(filename: str) -> int | None:
    m = re.search(r"(\d{4})", filename)
    return int(m.group(1)) if m else None

def normalize(text: str) -> str:
    # 1. Remove leading question numbers e.g. "1.a) ", "2. ", "b) "
    text = re.sub(r"^\s*(?:\d+\.\s*)?(?:[a-j]\)\s*)?", "", text)
    # 2. Strip any trailing exam footers (---oo0oo---, ---ooOoo---, etc.) and anything after them
    text = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", text, flags=re.IGNORECASE)
    # 3. Strip trailing mark brackets e.g. [5+5], [10], [5+5+5], [1], [2+3+2+3]
    text = re.sub(r"\s*\[[\d\+\s]+\]\s*$", "", text)
    # 4. Repeat in case mark was before footer or vice versa
    text = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\[[\d\+\s]+\]\s*$", "", text)
    # 5. Clean trailing notes like "Used Papers SEP 2021"
    text = re.sub(r"\s*Used Papers.*$", "", text, flags=re.IGNORECASE)
    # 6. Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def run():
    java_files = sorted(list(CLEANED_DIR.rglob("*JAVA*/**/*.txt")) + list(CLEANED_DIR.rglob("*Java*/**/*.txt")))
    print(f"Processing {len(java_files)} Java question paper files...")

    # norm_text -> metadata
    corpus = {}

    for f in java_files:
        year = parse_year(f.name)
        if not year:
            continue
        text = f.read_text(encoding="utf-8", errors="ignore")
        lines = [l.strip() for l in text.splitlines() if l.strip()]

        current_part = "B"
        curr_q = None

        def flush():
            nonlocal curr_q
            if curr_q:
                norm = normalize(curr_q["text"])
                if len(norm) > 15 and not IMAGE_TRIGGERS.search(norm):
                    if norm not in corpus:
                        corpus[norm] = {
                            "text": norm,
                            "marks": curr_q["marks"],
                            "part_a_years": set(),
                            "part_b_years": set(),
                            "files": set()
                        }
                    target_set = corpus[norm]["part_a_years"] if curr_q["part"] == "A" else corpus[norm]["part_b_years"]
                    target_set.add(year)
                    corpus[norm]["files"].add(f.name)
                curr_q = None

        for line in lines:
            if re.search(r"PART[\s\-]*A\b", line, re.I):
                flush()
                current_part = "A"
                continue
            if re.search(r"PART[\s\-]*B\b", line, re.I):
                flush()
                current_part = "B"
                continue
            if line == "OR":
                flush()
                continue
            if line.startswith(("Code No", "JAWAHARLAL", "B.Tech", "Time:", "Max Marks", "Note:")):
                continue

            m_a = re.match(r"^(?:1\.\s*)?([a-j]\))\s*(.*)", line)
            if current_part == "A" and m_a:
                flush()
                q_text = m_a.group(2).strip()
                marks = 2
                m_m = re.search(r"\[([1-3])\]", q_text)
                if m_m:
                    marks = int(m_m.group(1))
                curr_q = {"text": q_text, "part": "A", "marks": marks}
                continue

            m_b_sub = re.match(r"^(?:(\d+)\.\s*)?([a-d]\))\s*(.*)", line)
            if current_part == "B" and m_b_sub:
                flush()
                q_text = m_b_sub.group(3).strip()
                marks = 5
                m_m = re.search(r"\[([\d\+]+)\]", q_text)
                if m_m:
                    parts = [int(p) for p in m_m.group(1).split("+") if p.isdigit()]
                    if parts:
                        marks = parts[0]
                curr_q = {"text": q_text, "part": "B", "marks": marks}
                continue

            m_b_num = re.match(r"^(\d+)\.\s*(.*)", line)
            if current_part == "B" and m_b_num:
                flush()
                q_text = m_b_num.group(2).strip()
                marks = 10
                m_m = re.search(r"\[([\d\+]+)\]", q_text)
                if m_m:
                    parts = [int(p) for p in m_m.group(1).split("+") if p.isdigit()]
                    if parts:
                        marks = sum(parts)
                curr_q = {"text": q_text, "part": "B", "marks": marks}
                continue

            if curr_q:
                curr_q["text"] += " " + line

        flush()

    print(f"Total deduplicated text questions: {len(corpus)}")

    in_syllabus_rows = []
    oos_count = 0

    for norm_text, data in corpus.items():
        tag = assign_topic(norm_text)
        if tag == "OUT_OF_SYLLABUS":
            oos_count += 1
            continue

        bloom = infer_bloom(norm_text)
        in_syllabus_rows.append({
            "subject_name": "Object Oriented Programming through Java",
            "raw_question_text": norm_text,
            "topic_tag": tag,
            "bloom_level": bloom,
            "original_marks": data["marks"],
            "part_a_years": sorted(list(data["part_a_years"])),
            "part_b_years": sorted(list(data["part_b_years"]))
        })

    # Sort rows by topic_tag then original_marks
    in_syllabus_rows.sort(key=lambda r: (r["topic_tag"], r["original_marks"]))

    # Write Master CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "subject_name", "raw_question_text", "topic_tag",
            "bloom_level", "original_marks", "part_a_years", "part_b_years"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in in_syllabus_rows:
            writer.writerow(row)

    print(f"Done! {len(in_syllabus_rows)} in-syllabus questions written to {OUTPUT_CSV}")
    print(f"Filtered out {oos_count} out-of-syllabus questions (e.g. JDBC, Vector, Servlets from older regulations).")

if __name__ == "__main__":
    run()
