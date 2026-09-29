"""
apply_llm_verified_classification.py
Applies semantic verification to fix:
1. The OOP_PARADIGM_AND_CONCEPTS fallback dump (reclassifies misclassified questions to their true topics).
2. Bloom Taxonomy misclassifications (distinguishes active programming verbs for Apply vs conceptual Analyze/Understand).
"""

import csv
import re
from pathlib import Path

DATASET_CSV = Path("data/processed_dataset/java_master_final.csv")

# Semantic Topic Reclassification Map for the 82 questions that were trapped in OOP_PARADIGM_AND_CONCEPTS
TOPIC_REMAP = {
    # Collections / Legacy
    "What are the advantages of Collections Framework?": "COLLECTIONS_FRAMEWORK",
    "What is tree set class?": "COLLECTIONS_FRAMEWORK",
    "What is the significance of Legacy class? Give example.": "COLLECTIONS_FRAMEWORK",
    "What is a Java Priority queue?": "COLLECTIONS_FRAMEWORK",
    "Explain the Collection algorithms.": "COLLECTIONS_FRAMEWORK",
    "What is Priority Queue in Java? Explain": "COLLECTIONS_FRAMEWORK",
    "Explain different java collections in brief.": "COLLECTIONS_FRAMEWORK",
    "Explain the implementation of priority queue in java.": "COLLECTIONS_FRAMEWORK",
    "What is Java Collections Framework? List out some benefits of Collections framework and explain.": "COLLECTIONS_FRAMEWORK",
    "What are the common algorithms implemented in Collections Framework? Discuss.": "COLLECTIONS_FRAMEWORK",
    "What are the best practices related to Java Collections Framework? Discuss.": "COLLECTIONS_FRAMEWORK",
    "Give overview of collections framework.": "COLLECTIONS_FRAMEWORK",

    # Database / JDBC
    "Discuss the steps need to be followed in establishing connectivity to a database.": "DATABASE_CONNECTIVITY_JDBC",
    "Write Java J DBC program that update the records in a Student table in Database containing the fields Roll Number (Integer), Name (String), Branch (String), Percentage (Float) based on Roll Number (Integer).": "DATABASE_CONNECTIVITY_JDBC",

    # Java I/O Basics & Streams
    "What is Console class? What is its use in java?": "JAVA_IO_BASICS",
    "List the different ways to read input from console in java.": "JAVA_IO_BASICS",
    "Define stream. List types of streams.": "JAVA_IO_BASICS",
    "Contrast text streams and binary streams.": "JAVA_IO_BASICS",
    "List out the benefits of Stream oriented I/O.": "JAVA_IO_BASICS",
    "What is serialization? Give one example.": "JAVA_IO_BASICS",
    "What is the need of IO Streams?": "JAVA_IO_BASICS",
    "Write a program to list all the files and directories contained in a directory given as the command line argument.": "JAVA_IO_BASICS",
    "Discuss about input and output streams in Java with examples.": "JAVA_IO_BASICS",

    # Layout Managers
    "Write about Border Layout.": "LAYOUT_MANAGERS",
    "Illustrate the use of Grid Bag layout.": "LAYOUT_MANAGERS",

    # Swing Components
    "What are the differences between JToggle buttion and Radio buttion?": "SWING_COMPONENTS",
    "Write a program to display the month names by JList and di splay the Days by JComboBox.": "SWING_COMPONENTS",

    # Mouse & Keyboard Events
    "Write a program to create a frame window that responds to key strokes.": "MOUSE_AND_KEYBOARD_EVENTS",
    "Write a program to create a frame window that responds to mouse clicks.": "MOUSE_AND_KEYBOARD_EVENTS",

    # Multithreading / Concurrency
    "What is a Multi Threading? Explain.": "CREATING_THREADS",
    "Write a simple Timer that can periodically print a timeout message.": "CREATING_THREADS",
    "What are the different ways that are possible to create multiple threaded programs in java? Discuss the differences between them.": "CREATING_THREADS",
    "How many ways are possible in ja va to create multiple threaded programs? Discuss the differences between them.": "CREATING_THREADS",

    # Inheritance & Access Control
    "Does java supports multiple inheritances? Justify your answer.": "INHERITANCE_BASICS_AND_TYPES",
    "Can you create a multilevel class hierarchy in Java to model a system with different levels of abstraction?": "INHERITANCE_BASICS_AND_TYPES",
    "Discuss the different levels of access protection available in Java.": "ACCESS_CONTROL",

    # Classes & Objects
    "What is an Object? How to allocate memory for objects?": "CLASSES_AND_OBJECTS",

    # Data Types, Variables & Types
    "How to cast types in expression evaluation?": "TYPE_CONVERSION_AND_CASTING",
    "What are symbolic constants? Explain with examples.": "DATA_TYPES_VARIABLES_ARRAYS",
    "Discuss the lexical issues of Java.": "DATA_TYPES_VARIABLES_ARRAYS",

    # Control Statements
    "Explain the use of ‘for’ statement in Java with an example.": "CONTROL_STATEMENTS",
    "Does Java support multi way selection statement? Justify your answer.": "CONTROL_STATEMENTS",

    # Generics, Annotations, Autoboxing
    "What is the use of auto boxing in java? Explain.": "ENUMERATIONS_AUTOBOXING_ANNOTATIONS_GENERICS",
    "What is auto boxing? Explain.": "ENUMERATIONS_AUTOBOXING_ANNOTATIONS_GENERICS",
    "What is type wrapper? What is the role of auto boxing?": "ENUMERATIONS_AUTOBOXING_ANNOTATIONS_GENERICS",

    # String & Java Util
    "Write about Random Utility Class?": "STRING_HANDLING_AND_JAVA_UTIL",
    "Write a program to count number of words in a given sentence.": "STRING_HANDLING_AND_JAVA_UTIL",
    "Write a Java program to check whether a given string is palindrome.": "STRING_HANDLING_AND_JAVA_UTIL",
    "What is the purpose of BitSet class? What is the functionality of the following functions of BitSet class: cardinality( ) , flip( ) and intersects( )": "STRING_HANDLING_AND_JAVA_UTIL",
    "Explain the Bit Set and Calander classes in detail.": "STRING_HANDLING_AND_JAVA_UTIL",
    "Explain string and string buffer class in Java.": "STRING_HANDLING_AND_JAVA_UTIL",
    "Write a Java program to accept a String and to reverse it?": "STRING_HANDLING_AND_JAVA_UTIL",
    "Analyze the use of utility classes in complex data processing scenarios. How can these classes contribute to code readability and maintainability, and are there any trade -offs associated with their usage?": "STRING_HANDLING_AND_JAVA_UTIL"
}

# Strict Semantic Bloom Classifier
def classify_bloom_accurately(q_text: str) -> str:
    q = q_text.lower()

    # 1. EVALUATE: Justify, evaluate, assess, critique, verify, test claim
    if any(k in q for k in ["justify", "evaluate", "assess", "critique", "verify your answer", "is java a robust language? justify"]):
        return "Evaluate"

    # 2. ANALYZE: Comparison, differentiation, contrast, deep examination, pros/cons, trade-offs
    if any(k in q for k in [
        "differentiate", "distinguish", "difference between", "differences between",
        "compare", "contrast", "differ from", "trade-offs", "impact of", "advantages and disadvantages",
        "how is abstraction different", "which paradigm is preferred"
    ]):
        return "Analyze"

    # 3. APPLY: Explicit coding/problem-solving tasks (writing a program, constructing, developing)
    # Must have an active action verb, NOT passive "in a program" or "application program"
    has_active_coding = any(k in q for k in [
        "write a program", "write a java program", "write an applet", "develop an applet",
        "develop a program", "implement a program", "implement a java program", "write a code",
        "write code", "solve the", "compute the", "calculate the", "program to illustrate",
        "program to demonstrate", "program to create", "program to display", "program to count",
        "program to check", "program to accept", "program to search", "program to design"
    ])
    if has_active_coding:
        return "Apply"

    # 4. REMEMBER: Direct recall, definitions, list, name, state
    if any(k in q for k in [
        "what is", "what are", "define", "list out", "list the", "list any", "name any", "state the",
        "which swing class", "give the syntax", "give example", "what features", "what feature"
    ]) and not any(k in q for k in ["explain", "describe", "discuss", "how to", "why"]):
        return "Remember"

    # 5. UNDERSTAND: Conceptual explanations, descriptions, summaries, reasoning
    return "Understand"

def run():
    with open(DATASET_CSV) as f:
        rows = list(csv.DictReader(f))

    print(f"Loaded {len(rows)} questions from {DATASET_CSV}")

    topics_remapped = 0
    bloom_corrected = 0

    for r in rows:
        q_text = r["raw_question_text"]

        # 1. Topic Remapping
        if q_text in TOPIC_REMAP:
            new_tag = TOPIC_REMAP[q_text]
            if new_tag != r["topic_tag"]:
                r["topic_tag"] = new_tag
                topics_remapped += 1

        # 2. Bloom Correction
        correct_bloom = classify_bloom_accurately(q_text)
        if correct_bloom != r["bloom_level"]:
            r["bloom_level"] = correct_bloom
            bloom_corrected += 1

    # Write updated CSV
    with open(DATASET_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"Updated {DATASET_CSV} successfully!")
    print(f"  Topics remapped away from generic OOP_PARADIGM: {topics_remapped}")
    print(f"  Bloom cognitive levels corrected: {bloom_corrected}")

if __name__ == "__main__":
    run()
