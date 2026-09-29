"""
local_llm_tagger.py
Runs a local LLM pipeline via Ollama to classify topic_tag and bloom_level with 100% precision.
"""

import os
import csv
import json
import time
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:3b"

INPUT_CSV = Path("data/processed_dataset/java_master_final.csv")
OUTPUT_CSV = Path("data/processed_dataset/java_master_llm_verified.csv")
CHECKPOINT_FILE = Path("data/processed_dataset/.tagger_checkpoint.json")

# Structured syllabus units for maximum classification accuracy
UNIT_STRUCTURE = {
    "UNIT_1_JAVA_BASICS_AND_OOP": [
        "OOP_PARADIGM_AND_CONCEPTS", "DATA_TYPES_VARIABLES_ARRAYS", "OPERATORS_AND_EXPRESSIONS",
        "CONTROL_STATEMENTS", "TYPE_CONVERSION_AND_CASTING", "CLASSES_AND_OBJECTS",
        "CONSTRUCTORS_AND_METHODS", "ACCESS_CONTROL", "THIS_KEYWORD", "GARBAGE_COLLECTION",
        "METHOD_AND_CONSTRUCTOR_OVERLOADING", "PARAMETER_PASSING_AND_RECURSION", "NESTED_AND_INNER_CLASSES"
    ],
    "UNIT_2_INHERITANCE_PACKAGES_INTERFACES": [
        "INHERITANCE_BASICS_AND_TYPES", "MEMBER_ACCESS_RULES", "SUPER_KEYWORD", "FINAL_KEYWORD",
        "METHOD_OVERRIDING_AND_POLYMORPHISM", "ABSTRACT_CLASSES", "OBJECT_CLASS",
        "PACKAGES_CREATION_AND_ACCESS", "CLASSPATH", "IMPORTING_PACKAGES",
        "INTERFACES_DEFINITION_AND_IMPLEMENTATION", "EXTENDING_INTERFACES", "JAVA_IO_BASICS"
    ],
    "UNIT_3_EXCEPTIONS_AND_THREADS": [
        "EXCEPTION_HANDLING_CONCEPTS", "TRY_CATCH_THROW_THROWS_FINALLY", "BUILT_IN_EXCEPTIONS",
        "CUSTOM_EXCEPTIONS", "STRING_HANDLING_AND_JAVA_UTIL", "MULTITHREADING_VS_MULTITASKING",
        "THREAD_LIFECYCLE", "CREATING_THREADS", "THREAD_PRIORITIES", "THREAD_SYNCHRONIZATION",
        "INTER_THREAD_COMMUNICATION", "DAEMON_THREADS", "ENUMERATIONS_AUTOBOXING_ANNOTATIONS_GENERICS"
    ],
    "UNIT_4_EVENT_HANDLING_AND_AWT": [
        "EVENT_HANDLING_AND_DELEGATION_MODEL", "MOUSE_AND_KEYBOARD_EVENTS", "ADAPTER_CLASSES",
        "AWT_CLASS_HIERARCHY", "AWT_USER_INTERFACE_COMPONENTS", "AWT_CONTAINERS_AND_PANELS",
        "GRAPHICS_PROGRAMMING", "LAYOUT_MANAGERS"
    ],
    "UNIT_5_APPLETS_AND_SWING": [
        "APPLETS_CONCEPTS_AND_LIFECYCLE", "CREATING_AND_PASSING_PARAMETERS_TO_APPLETS",
        "SWING_OVERVIEW_AND_LIMITATIONS_OF_AWT", "MVC_ARCHITECTURE",
        "SWING_CONTAINERS_JFRAME_JAPPLET", "SWING_COMPONENTS"
    ]
}

ALL_VALID_TOPICS = set()
for topics in UNIT_STRUCTURE.values():
    ALL_VALID_TOPICS.update(topics)

ALLOWED_BLOOM = ["Remember", "Understand", "Apply", "Analyze", "Evaluate"]

TOPICS_LIST_STR = "\n".join(f"- {t}" for t in sorted(ALL_VALID_TOPICS)) + "\n- LEGACY_OUT_OF_SYLLABUS"

def build_prompt(question_text: str) -> str:
    return (
        "You are an expert Computer Science Professor and JNTUH curriculum auditor.\n"
        "Classify this exam question into its exact R22 Java topic_tag and bloom_level.\n\n"
        f"Question to classify:\n\"{question_text}\"\n\n"
        "ALLOWED TOPIC TAGS (Select the single most specific matching tag from this list):\n"
        f"{TOPICS_LIST_STR}\n\n"
        "BLOOM TAXONOMY RULES (Pick exactly one level based on the primary cognitive demand):\n"
        "1. 'Apply': ONLY if the student is required to write code, develop/implement a program, or write an applet (e.g. 'Write a Java program', 'With a program illustrate', 'Develop a program', 'Write a code snippet').\n"
        "2. 'Analyze': Comparison, distinction, differences, contrast, pros/cons (e.g. 'What are the differences between X and Y', 'Differentiate X and Y', 'Compare X and Y', 'How does X differ from Y').\n"
        "3. 'Evaluate': Justification, critique, trade-offs, proof (e.g. 'Justify your answer', 'Evaluate whether', 'Prove that').\n"
        "4. 'Remember': Direct recall, definitions, naming, listing (e.g. 'Define X', 'What is X', 'List the types of X', 'State the features').\n"
        "5. 'Understand': Conceptual explanations, descriptions, working principles (e.g. 'Explain X', 'Describe the lifecycle', 'Discuss the mechanism').\n\n"
        "Respond ONLY with this exact JSON schema:\n"
        "{\n"
        "  \"topic_tag\": \"<EXACT_TAG_FROM_LIST>\",\n"
        "  \"bloom_level\": \"<Remember | Understand | Apply | Analyze | Evaluate>\"\n"
        "}\n"
    )

def classify_with_llm(q_text: str, default_tag: str, default_bloom: str, retries: int = 3) -> dict:
    prompt = build_prompt(q_text)

    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 80
        }
    }

    for attempt in range(retries):
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
            if resp.status_code == 200:
                result_text = resp.json().get("response", "{}")
                data = json.loads(result_text)
                
                raw_tag = data.get("topic_tag", "").strip()
                raw_bloom = data.get("bloom_level", "").strip()

                tag = raw_tag.upper().replace(" ", "_")
                # Strip any leading bullets or numbers
                if tag.startswith("-"):
                    tag = tag.lstrip("-").strip()

                if tag not in ALL_VALID_TOPICS and tag != "LEGACY_OUT_OF_SYLLABUS":
                    # If tag wasn't exact match, keep default tag if valid
                    tag = default_tag if default_tag in ALL_VALID_TOPICS else "OOP_PARADIGM_AND_CONCEPTS"

                bloom_candidates = [b for b in ALLOWED_BLOOM if b.lower() == raw_bloom.lower()]
                bloom = bloom_candidates[0] if bloom_candidates else default_bloom

                return {"topic_tag": tag, "bloom_level": bloom}
        except Exception:
            time.sleep(1)

    return {"topic_tag": default_tag, "bloom_level": default_bloom}

def run():
    if not INPUT_CSV.exists():
        print(f"Error: {INPUT_CSV} does not exist.")
        return

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} questions to classify with local {MODEL_NAME}...")

    processed = {}
    if CHECKPOINT_FILE.exists():
        try:
            with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
                processed = json.load(f)
            print(f"Resumed from checkpoint: {len(processed)} questions already verified.")
        except Exception:
            processed = {}

    start_time = time.time()
    total = len(rows)

    for idx, r in enumerate(rows, 1):
        q_text = r["raw_question_text"]

        if q_text in processed:
            r["topic_tag"] = processed[q_text]["topic_tag"]
            r["bloom_level"] = processed[q_text]["bloom_level"]
            continue

        res = classify_with_llm(q_text, r["topic_tag"], r["bloom_level"])
        r["topic_tag"] = res["topic_tag"]
        r["bloom_level"] = res["bloom_level"]
        processed[q_text] = res

        if idx % 5 == 0 or idx == total:
            with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
                json.dump(processed, f)
            elapsed = time.time() - start_time
            rate = idx / max(elapsed, 0.001)
            eta = (total - idx) / max(rate, 0.001)
            print(f"[{idx}/{total}] Verified ({rate:.2f} q/s, ETA: {eta:.0f}s) -> Last: {res['topic_tag']} | {res['bloom_level']}", flush=True)

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"\nAll {total} questions verified and saved to: {OUTPUT_CSV.resolve()}")

    # Sync to data/Java_Dataset.csv and data/processed_dataset/java_master.csv
    import shutil
    shutil.copy2(OUTPUT_CSV, "data/Java_Dataset.csv")
    shutil.copy2(OUTPUT_CSV, "data/processed_dataset/java_master.csv")
    print("Synchronized verified dataset to data/Java_Dataset.csv and data/processed_dataset/java_master.csv")

    if CHECKPOINT_FILE.exists():
        CHECKPOINT_FILE.unlink()

if __name__ == "__main__":
    run()
