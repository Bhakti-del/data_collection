#!/usr/bin/env python3
"""
clean_all_datasets.py
=====================
Master script to critique, clean, standardize, and deduplicate all question paper
datasets across subjects in data/datasets/.

Enforces:
  1. Standard 7-column schema.
  2. "One Row = One Unique Question" deduplication with calendar year union.
  3. Resolution of Part A (<= 3 marks) and Part B (>= 5 marks) inversions.
  4. Removal of invalid Bloom taxonomy level 'Create' remapped by cognitive demand.
  5. Cognitive verb alignment (Differentiate -> Analyze, Define -> Remember, etc.).
  6. Stitching severed question stems and expanding naked fragments.
  7. Stripping OCR spacing noise, boilerplate university headers, and trailing artifacts.
  8. Unification of IoT / Fundamentals of IoT question banks.
"""

import os
import sys
import csv
import re
from collections import defaultdict, Counter

VALID_BLOOMS = {'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate'}

# Common OCR spacing fixes
OCR_REPLACEMENTS = [
    (r'\bstri\s+ng\b', 'string'),
    (r'\bstri\s+ng-matching\b', 'string-matching'),
    (r'\bautomat\s+ion\b', 'automaton'),
    (r'\bcontr\s+ol\b', 'control'),
    (r'\bdr\s+aw\b', 'draw'),
    (r'\bh\s+ow\b', 'how'),
    (r'\bprogra\s+m\b', 'program'),
    (r'\balgori\s+thm\b', 'algorithm'),
    (r'\bfunct\s+ion\b', 'function'),
    (r'\bfi\s+les\b', 'files'),
    (r'\bcrated\b', 'created'),
    (r'\bd\s+atabase\b', 'database'),
    (r'\bt\s+ransaction\b', 'transaction'),
    (r'\bcl\s+oud\b', 'cloud'),
    (r'\bcl\s+ouds\b', 'clouds'),
    (r'\bnetwo\s+rk\b', 'network'),
    (r'\bdistribut\s+ed\b', 'distributed'),
    (r'\bsyst\s+em\b', 'system'),
    (r'\bmemor\s+y\b', 'memory'),
    (r'\binfor\s+mation\b', 'information'),
    (r'\boperat\s+ion\b', 'operation'),
    (r'\bprocess\s+or\b', 'processor'),
    (r'\bsoftw\s+are\b', 'software'),
    (r'\barchi\s+tecture\b', 'architecture'),
    (r'\binter\s+face\b', 'interface'),
    (r'\bexecut\s+ion\b', 'execution'),
    (r'\bcompil\s+er\b', 'compiler'),
    (r'\bveri\s+fication\b', 'verification'),
    (r'\bspecifi\s+cation\b', 'specification'),
    (r'\bartifi\s+cial\b', 'artificial'),
    (r'\bintelli\s+gence\b', 'intelligence'),
    (r'\bconcurr\s+ency\b', 'concurrency'),
    (r'\bvertex\s+-cover\b', 'vertex-cover'),
    (r'\bMap\s*-\s*reduce\b', 'MapReduce'),
    (r'\bPerceptron\s+-Convergence\b', 'Perceptron Convergence'),
    (r'\bAdaptive\s+Patter\b', 'Adaptive Pattern'),
    (r'\bback\s*-propagation\b', 'back-propagation'),
    (r'\binter\s+process\b', 'interprocess'),
    (r'\bfo\s+r\b', 'for'),
    (r'\bc\s+ontrols\b', 'controls'),
    (r'\bregula\s+r\b', 'regular'),
    (r'\bdo\s+es\b', 'does'),
    (r'\bproces\s+s\b', 'process'),
    (r'\bconstru\s+ct\b', 'construct'),
    (r'\ble\s+arning\b', 'learning'),
    (r'\bst\s+atement\b', 'statement'),
    (r'\bequal\s*-\s*span\b', 'equal-span')
]

def clean_ocr(text):
    t = text.strip()
    for pattern, repl in OCR_REPLACEMENTS:
        t = re.sub(pattern, repl, t, flags=re.I)
    t = re.sub(r'\s+', ' ', t).strip()
    return t

def parse_years(ystr):
    if isinstance(ystr, list):
        return sorted(list(set(int(y) for y in ystr)))
    years = re.findall(r'\b\d{4}\b', str(ystr))
    return sorted(list(set(int(y) for y in years)))

def format_years(ylist):
    return str(sorted(list(set(ylist))))

def normalize_text_for_dedup(qtext):
    s = qtext.lower().strip()
    s = s.replace("write a short notes on", "write short notes on")
    s = s.replace("write short notes on", "")
    s = s.replace("write a short note on", "")
    s = s.replace("explain about ", "")
    s = s.replace("explain in brief about ", "")
    s = s.replace("explain in brief ", "")
    s = s.replace("explain in detail about ", "")
    s = s.replace("explain in detail ", "")
    s = s.replace("discuss about ", "")
    s = s.replace("discuss in brief about ", "")
    s = s.replace("discuss in detail about ", "")
    s = s.replace("differentiate between ", "differentiate ")
    s = s.replace("distinguish between ", "distinguish ")
    s = s.replace("difference between ", "differentiate ")
    s = s.replace("what is ", "")
    s = s.replace("what are ", "")
    s = s.replace("define ", "")
    s = re.sub(r'[^a-z0-9]', '', s)
    return s

def remap_create_bloom(qtext):
    qt_low = qtext.lower()
    if re.search(r'\b(program|script|code|develop a|implement|construct|design a php|write tk|create a form|write a query|write an sql|calculate|compute|solve)\b', qt_low):
        return 'Apply'
    elif re.search(r'\b(test plan|walkthrough|usability|heuristic does not have|ratio bound|evaluate|assess|validate)\b', qt_low):
        return 'Evaluate'
    elif re.search(r'\b(differentiate|distinguish|compare|contrast|differ)\b', qt_low):
        return 'Analyze'
    elif re.search(r'\b(define|list|state|name|what is|what are)\b', qt_low):
        return 'Remember'
    else:
        # Conceptual design, architecture, steps to create
        if re.search(r'\b(how to create|steps to create|design considerations|design concepts|design patterns?|approach to|design requirements)\b', qt_low):
            return 'Understand'
        return 'Apply'

def align_bloom(qtext, current_bloom):
    qt = qtext.strip()
    # 1. Remap Create
    if current_bloom == 'Create':
        current_bloom = remap_create_bloom(qt)

    # 2. Compare / Differentiate -> Analyze
    if re.match(r'^(?:differentiate|distinguish|compare|contrast)\b', qt, re.I):
        return 'Analyze'
    elif re.search(r'\b(?:difference between|differ from)\b', qt, re.I) and not re.search(r'\b(program|code|algorithm)\b', qt, re.I):
        return 'Analyze'

    # 3. Programming / Implementation -> Apply
    if re.match(r'^(?:write a (?:java|c|c\+\+|python|perl|php|tk) (?:program|script|code)|develop a (?:program|servlet|jsp|script)|construct (?:a|an) (?:dfa|nfa|turing machine|string-matching automaton))\b', qt, re.I):
        return 'Apply'

    # 4. Pure Recall -> Remember
    if re.match(r'^(?:define|list|state|name)\b', qt, re.I) and not re.search(r'\b(compare|differentiate|distinguish|analyze|program|code|algorithm to solve|calculate|compute)\b', qt, re.I):
        if current_bloom not in ['Remember', 'Understand']:
            return 'Remember'

    return current_bloom if current_bloom in VALID_BLOOMS else 'Understand'

def fix_part_inversion(marks, pa_years, pb_years):
    m = int(marks) if str(marks).isdigit() else 5
    pa = list(pa_years)
    pb = list(pb_years)
    # Marks <= 3 in Part B -> Move to Part A
    if m <= 3 and pb and not pa:
        pa = pb
        pb = []
    # Marks >= 8 in Part A -> Move to Part B
    elif m >= 8 and pa and not pb:
        pb = pa
        pa = []
    return str(m), pa, pb

BDA_GENERAL_MAPPING = {
    0: "WORKPLACE_SAFETY_BDA", 1: "DATA_SOURCES", 2: "OUTLIER_NOISE",
    3: "DATA_SOURCES", 4: "DATA_VISUALIZATION_BDA", 5: "BIG_DATA_INTRODUCTION",
    6: "DATA_SOURCES", 7: "BIG_DATA_INTRODUCTION", 8: "DATA_SOURCES",
    9: "BIG_DATA_INTRODUCTION", 10: "KNOWLEDGE_MANAGEMENT", 11: "APACHE_SPARK",
    12: "OUTLIER_NOISE", 13: "MACHINE_LEARNING_BDA", 14: "DATA_VISUALIZATION_BDA",
    15: "OUTLIER_NOISE", 16: "OUTLIER_NOISE", 17: "DATA_GOVERNANCE",
    18: "DATA_SOURCES", 19: "DATA_SOURCES", 20: "BIG_DATA_INTRODUCTION",
    21: "DATA_SOURCES", 22: "MACHINE_LEARNING_BDA", 23: "DATA_VISUALIZATION_BDA",
    24: "BIG_DATA_INTRODUCTION", 25: "WORKPLACE_SAFETY_BDA", 26: "OUTLIER_NOISE",
    27: "BIG_DATA_INTRODUCTION", 28: "KNOWLEDGE_MANAGEMENT", 29: "DATA_GOVERNANCE",
    30: "DATA_GOVERNANCE", 31: "KNOWLEDGE_MANAGEMENT", 32: "DESCRIPTIVE_ANALYTICS",
    33: "DESCRIPTIVE_ANALYTICS", 34: "DATA_VISUALIZATION_BDA", 35: "WORKPLACE_SAFETY_BDA",
    36: "DATA_SOURCES", 37: "MAPREDUCE", 38: "BIG_DATA_INTRODUCTION",
    39: "BIG_DATA_INTRODUCTION", 40: "MACHINE_LEARNING_BDA", 41: "DATA_VISUALIZATION_BDA",
    42: "BIG_DATA_INTRODUCTION", 43: "APACHE_SPARK", 44: "BIG_DATA_INTRODUCTION",
    45: "DESCRIPTIVE_ANALYTICS", 46: "WORKPLACE_SAFETY_BDA"
}

def clean_subject_rows(subj_name, rows):
    cleaned = []
    skip_indices = set()
    bda_gen_counter = 0

    # Pass 1: Handle stitches and deletions
    for idx in range(len(rows)):
        if idx in skip_indices:
            continue
        r = list(rows[idx])
        sub, qtext, topic, bloom, marks, pa_str, pb_str = r[:7]
        qtext = clean_ocr(qtext)

        # Boilerplate check
        if qtext.lower() in ["(computer science and engineering)", "computer science and engineering"]:
            continue
        if re.search(r'^\(computer science', qtext, re.I):
            continue

        # AI Stitches
        if "Artificial_Intelligence" in subj_name:
            if qtext == "Define the following terms:" and idx + 1 < len(rows):
                next_r = rows[idx + 1]
                if "Problem space" in next_r[1]:
                    qtext = f"Define the following terms: i) {clean_ocr(next_r[1])}"
                    topic = "STATE_SPACE_SEARCH_AND_HEURISTICS"
                    bloom = "Remember"
                    marks = "3"
                    pa = sorted(list(set(parse_years(pa_str) + parse_years(next_r[5]) + [2018])))
                    pb = []
                    skip_indices.add(idx + 1)
                    cleaned.append([sub, qtext, topic, bloom, str(marks), format_years(pa), format_years(pb)])
                    continue
            if "Everyone who loves someone who loves them back is happy" in qtext and idx + 2 < len(rows):
                r2 = rows[idx + 1]
                r3 = rows[idx + 2]
                if "Mary loves everyone" in r2[1] and "There is someone who loves Mary" in r3[1]:
                    qtext = "Consider the following statements: (i) Everyone who loves someone who loves them back is happy. (ii) Mary loves everyone. (iii) There is someone who loves Mary. From the above statements conclude that: Mary is happy."
                    topic = "LOGIC_AND_LOGIC_PROGRAMMING"
                    bloom = "Apply"
                    marks = "15"
                    pa = []
                    pb = sorted(list(set(parse_years(pb_str) + parse_years(r2[6]) + parse_years(r3[6]) + [2022])))
                    skip_indices.add(idx + 1)
                    skip_indices.add(idx + 2)
                    cleaned.append([sub, qtext, topic, bloom, str(marks), format_years(pa), format_years(pb)])
                    continue
            if qtext.rstrip() == "Describe the following:":
                continue # merged with subquestion below
            if qtext.startswith("Dempster-Shafer Theory b) Certainty Factor Theory"):
                qtext = "Describe the following: a) Dempster-Shafer Theory b) Certainty Factor Theory."
                topic = "UNCERTAINTY_AND_PROBABILITY"
                bloom = "Understand"
                marks = "10"
                pb = [2018]
                pa = []
            # AI Fragments
            if qtext == "Bayesian Belief Networks":
                qtext = "Write short notes on Bayesian Belief Networks."
            elif qtext == "Dempster-Shafer Theory.":
                qtext = "Write short notes on Dempster-Shafer Theory."
            elif qtext == "Support Vector Machines":
                qtext = "Write short notes on Support Vector Machines."
            elif qtext == "Radial-Basis Function Networks.":
                qtext = "Write short notes on Radial-Basis Function Networks."
            elif qtext == "Bounded Look-ahead Strategy":
                qtext = "Explain Bounded Look-ahead Strategy."
            elif qtext == "Alpha-Beta Pruning.":
                qtext = "Explain Alpha-Beta Pruning."
            elif qtext == "Conceptual Dependency":
                qtext = "Explain Conceptual Dependency."

        # Distributed Systems Stitches
        if "Distributed_Systems" in subj_name:
            if qtext == "Describe briefly about the following." and idx + 1 < len(rows):
                next_r = rows[idx + 1]
                if "WWW" in next_r[1]:
                    qtext = f"Describe briefly about the following: i) {clean_ocr(next_r[1])}"
                    m_max = max(int(marks) if marks.isdigit() else 5, int(next_r[4]) if next_r[4].isdigit() else 5)
                    pa = sorted(list(set(parse_years(pa_str) + parse_years(next_r[5]))))
                    pb = sorted(list(set(parse_years(pb_str) + parse_years(next_r[6]))))
                    m_str, pa, pb = fix_part_inversion(m_max, pa, pb)
                    skip_indices.add(idx + 1)
                    cleaned.append([sub, qtext, topic, bloom, m_str, format_years(pa), format_years(pb)])
                    continue
            if qtext in ["Give brief notes on:", "Give brief notes on"] and idx + 1 < len(rows):
                next_r = rows[idx + 1]
                if "Deadlock" in next_r[1]:
                    qtext = f"Give brief notes on: i) {clean_ocr(next_r[1])}"
                    m_max = max(int(marks) if marks.isdigit() else 5, int(next_r[4]) if next_r[4].isdigit() else 5)
                    pa = sorted(list(set(parse_years(pa_str) + parse_years(next_r[5]))))
                    pb = sorted(list(set(parse_years(pb_str) + parse_years(next_r[6]))))
                    m_str, pa, pb = fix_part_inversion(m_max, pa, pb)
                    skip_indices.add(idx + 1)
                    cleaned.append([sub, qtext, topic, bloom, m_str, format_years(pa), format_years(pb)])
                    continue
            # DS Fragments
            if qtext == "Directory services.":
                qtext = "Write a short note on Directory services."
            elif qtext == "Mobile Computing":
                qtext = "Write a short note on Mobile Computing."
            elif qtext == "Secure Channels.":
                qtext = "Write a short note on Secure Channels."
            elif qtext == "Release consistency in distributed shared memory.":
                qtext = "Explain release consistency in distributed shared memory."

        # Middleware Technologies Stitches
        if "Middleware_Technologies" in subj_name:
            if qtext == "Serializable" and idx + 2 < len(rows):
                r_sc = rows[idx + 1]
                r_need = rows[idx + 2]
                if "SeriveContract" in r_sc[1] and "predefined attributes" in r_need[1]:
                    qtext = "Discuss the need of the following .NET predefined attributes: a) Serializable b) ServiceContract c) DllImport."
                    topic = "DOTNET_PLATFORM"
                    bloom = "Understand"
                    marks = "15"
                    pa = []
                    pb = [2021]
                    skip_indices.add(idx + 1)
                    skip_indices.add(idx + 2)
                    cleaned.append([sub, qtext, topic, bloom, str(marks), format_years(pa), format_years(pb)])
                    continue
            if qtext.endswith("diagram. RA"):
                qtext = qtext[:-3].strip()

        # NLP Stitches / Deletions
        if "Natural_Language_Processing" in subj_name:
            if qtext.rstrip() == "Explain the following:":
                continue # dangling stem already split into subquestions
            if qtext == "Language Model Adaptation":
                qtext = "Explain Language Model Adaptation."
            elif qtext == "Semantic Parsing with Execution":
                qtext = "Explain Semantic Parsing with Execution."
            elif qtext == "Dictionary lookup":
                qtext = "Explain Dictionary lookup in NLP."
            elif qtext == "Unification based morphology.":
                qtext = "Explain Unification-based morphology."

        # ANN Fragments
        if "Artificial_Neural_Networks" in subj_name:
            if qtext == "Retrieval algorithm":
                qtext = "Explain the Hopfield network retrieval algorithm."
            elif qtext == "Storage algorithm.":
                qtext = "Explain the Hopfield network storage algorithm."

        # Scripting Languages Stitches
        if "Scripting_Languages" in subj_name:
            if qtext == "Explain briefly about the following commands:" and idx + 1 < len(rows):
                next_r = rows[idx + 1]
                qtext = f"Explain briefly about the following commands: i) {clean_ocr(next_r[1])}"
                topic = next_r[2]
                marks = "15"
                pa = sorted(list(set(parse_years(pa_str) + parse_years(next_r[5]))))
                pb = sorted(list(set(parse_years(pb_str) + parse_years(next_r[6]))))
                skip_indices.add(idx + 1)
                cleaned.append([sub, qtext, topic, bloom, str(marks), format_years(pa), format_years(pb)])
                continue
            if qtext == "Explain the functionality and usage with various options of the following commands:":
                qtext = "Explain the functionality and usage with various options of essential Linux file and directory management commands (e.g. tar, gzip, find, chmod, chown)."

        # Formal Languages Fragments
        if "Formal_Languages" in subj_name:
            if qtext == "Linear-Bounded Automata":
                qtext = "Write short notes on Linear-Bounded Automata."
            elif qtext == "Recursively enumerable language":
                qtext = "Write short notes on Recursively enumerable language."
            elif qtext == "Context Free Grammar":
                qtext = "Write short notes on Context Free Grammar."
            elif qtext == "Left Most Derivation":
                qtext = "Write short notes on Left Most Derivation."
            elif qtext == "Right Most Derivation.":
                qtext = "Write short notes on Right Most Derivation."
            elif qtext == "Universal Turing Machine":
                qtext = "Write short notes on Universal Turing Machine."
            elif qtext.startswith("Define DFA") and "CONTEXT_FREE" in topic:
                topic = "FINITE_AUTOMATA_AND_DFA_NFA"
            elif "Universal TM" in qtext and "TURING_MACHINE" not in topic:
                topic = "TURING_MACHINE"

        # Web Services Fragments
        if "Web_Services" in subj_name:
            if qtext == "Asymmetric ciphers.":
                qtext = "Explain Asymmetric ciphers."
            elif qtext == "Symmetric ciphers.":
                qtext = "Explain Symmetric ciphers."
            elif qtext == "Enumeration.":
                qtext = "Explain Enumeration in SOAP."
            elif qtext == "Structure types":
                qtext = "Explain Structure types in SOAP."

        # Software Testing Fragments
        if "Software_Testing" in subj_name:
            if qtext == "Design guideline for building finite state machine":
                qtext = "Explain design guidelines for building finite state machines."
            elif qtext == "Inessential finite state behavior.":
                qtext = "Explain inessential finite state behavior."

        # PPL Fragments
        if "Principles_of_Programming" in subj_name:
            if qtext == "Conditional statements":
                qtext = "Write short notes on conditional statements."
            elif qtext.startswith("Pass-by-value-result"):
                qtext = "Explain the following parameter passing methods: i) Pass-by-value-result ii) Pass-by-Reference."

        # DAA Fragments
        if "Design_and_Analysis_of_Algorithms" in subj_name:
            if qtext == "Breadth First Search.":
                qtext = "Explain Breadth First Search."
            elif qtext == "Kruskal’s algorithm.":
                qtext = "Explain Kruskal’s algorithm."

        # Compiler Design tag fixes for 2024 short questions
        if "Compiler_Design" in subj_name:
            if "primary goal of the lexical analysis" in qtext.lower():
                topic = "LEXICAL_ANALYSIS"
                bloom = "Understand"
            elif "type checker" in qtext.lower():
                topic = "SYNTAX_DIRECTED_TRANSLATION"
                bloom = "Understand"
            elif "code optimizations" in qtext.lower() or "copy propagation" in qtext.lower():
                topic = "CODE_OPTIMIZATION"
                bloom = "Understand"
            elif "object code" in qtext.lower() or "register allocation" in qtext.lower():
                topic = "CODE_GENERATION"
                bloom = "Understand"
            elif qtext.startswith("000111 ii) 00S11"):
                qtext = "Derive the following strings using context free grammar: i) 000111 ii) 00S11."

        # BDA Re-tagging
        if "Big_Data_Analytics" in subj_name and topic == "BIG_DATA_GENERAL":
            if bda_gen_counter in BDA_GENERAL_MAPPING:
                topic = BDA_GENERAL_MAPPING[bda_gen_counter]
            bda_gen_counter += 1

        # Cloud Computing Re-tagging
        if "Cloud_Computing" in subj_name and topic == "GENERAL_CLOUD_COMPUTING":
            t_low = qtext.lower()
            if "elasticity" in t_low or "multitenancy" in t_low:
                topic = "CLOUD_FUNDAMENTALS"
            elif "service bus" in t_low:
                topic = "CLOUD_PLATFORM_FRAMEWORKS"
            elif "lease scheduling" in t_low:
                topic = "VIRTUALIZATION_AND_RESOURCE_MANAGEMENT"
            elif "service design" in t_low:
                topic = "SERVICE_ORIENTED_ARCHITECTURE"
            elif "information card" in t_low or "availability" in t_low or "recovery" in t_low:
                topic = "CLOUD_SECURITY_AND_DISASTER_RECOVERY"

        # Bloom & Inversions
        bloom = align_bloom(qtext, bloom)
        pa_list = parse_years(pa_str)
        pb_list = parse_years(pb_str)
        m_str, pa_list, pb_list = fix_part_inversion(marks, pa_list, pb_list)

        cleaned.append([sub, qtext, topic, bloom, m_str, format_years(pa_list), format_years(pb_list)])

    # Pass 2: Deduplicate
    merged_map = {}
    for r in cleaned:
        sub, qtext, topic, bloom, marks, pa_str, pb_str = r
        norm_key = (topic, normalize_text_for_dedup(qtext))

        if norm_key in merged_map:
            ex = merged_map[norm_key]
            # Union of years
            pa_union = sorted(list(set(parse_years(ex[5]) + parse_years(pa_str))))
            pb_union = sorted(list(set(parse_years(ex[6]) + parse_years(pb_str))))
            # Represent marks
            m_max = max(int(ex[4]), int(marks))
            ex[4] = str(m_max)
            ex[5] = format_years(pa_union)
            ex[6] = format_years(pb_union)
            # Prefer cleaner/longer question statement
            if len(qtext) > len(ex[1]):
                ex[1] = qtext
        else:
            merged_map[norm_key] = r

    final_rows = list(merged_map.values())
    final_rows.sort(key=lambda r: (r[2], r[1]))
    return final_rows

def process_iot_datasets(ds_dir, df_dir):
    """Unifies Fundamentals_of_IoT and Internet_of_Things into consistent datasets."""
    f1_ds = os.path.join(ds_dir, "Fundamentals_of_IoT_Dataset.csv")
    f2_ds = os.path.join(ds_dir, "Internet_of_Things_Dataset.csv")

    rows1, rows2 = [], []
    header = ["subject_name", "raw_question_text", "topic_tag", "bloom_level", "original_marks", "part_a_years", "part_b_years"]
    if os.path.exists(f1_ds):
        with open(f1_ds, 'r', encoding='utf-8', errors='replace') as f:
            r = list(csv.reader(f))
            if r:
                header = r[0]
                rows1 = r[1:]
    if os.path.exists(f2_ds):
        with open(f2_ds, 'r', encoding='utf-8', errors='replace') as f:
            r = list(csv.reader(f))
            if r:
                rows2 = r[1:]

    combined = rows1 + rows2
    for r in combined:
        r[0] = "Internet of Things"
        qt = clean_ocr(r[1])
        r[1] = qt
        if "network function virtualization" in qt.lower() or "sdn" in qt.lower():
            r[2] = "SDN_NFV_FOR_IOT"
        elif r[2] == "GENERAL_IOT":
            r[2] = "WIRELESS_COMMUNICATIONS_IOT"
        elif r[2] == "M2M_ARCHITECTURE_SERVICES":
            r[2] = "M2M_VS_IOT"

    cleaned = clean_subject_rows("Internet_of_Things", combined)

    # Write to Data_sets
    for fname, subj_label in [("Fundamentals_of_IoT_Dataset.csv", "Fundamentals of IoT"),
                              ("Internet_of_Things_Dataset.csv", "Internet of Things")]:
        p = os.path.join(ds_dir, fname)
        rows_to_write = []
        for row in cleaned:
            r_copy = list(row)
            r_copy[0] = subj_label
            rows_to_write.append(r_copy)
        rows_to_write.sort(key=lambda r: (r[2], r[1]))
        with open(p, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows_to_write)

        # Sync to Datafiles if dir exists
        if df_dir and os.path.exists(df_dir):
            p_df = os.path.join(df_dir, fname)
            with open(p_df, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(rows_to_write)

    return len(cleaned)

def process_root_ai(root_path):
    """Cleans root Artificial_Intelligence_Dataset.csv."""
    if not os.path.exists(root_path):
        return 0
    with open(root_path, 'r', encoding='utf-8', errors='replace') as f:
        rows = list(csv.reader(f))
    if not rows:
        return 0
    header = rows[0]
    data = rows[1:]

    cleaned = clean_subject_rows("Artificial_Intelligence", data)
    with open(root_path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(cleaned)
    return len(cleaned)

def main():
    target_dir = sys.argv[1] if len(sys.argv) > 1 else "data/datasets"
    ds_arranged = target_dir
    df_arranged = None
    root_ai = None

    if not os.path.exists(ds_arranged):
        print(f"Error: {ds_arranged} does not exist.")
        sys.exit(1)

    print("=" * 80)
    print("MASTER DATASET CLEANING & SUBJECT-WISE REPAIR PIPELINE")
    print("=" * 80)

    # Process all regular subjects in Data_sets/Arranged_csv_qp
    files = sorted([f for f in os.listdir(ds_arranged) if f.endswith(".csv")])
    stats = {}

    for fname in files:
        if fname in ["Fundamentals_of_IoT_Dataset.csv", "Internet_of_Things_Dataset.csv"]:
            continue # handled specially

        p_ds = os.path.join(ds_arranged, fname)
        with open(p_ds, 'r', encoding='utf-8', errors='replace') as f:
            rows = list(csv.reader(f))
        if not rows:
            continue
        header = rows[0]
        data = rows[1:]
        before_count = len(data)

        subj_name = fname.replace("_Dataset.csv", "")
        cleaned = clean_subject_rows(subj_name, data)
        after_count = len(cleaned)

        # Write cleaned to Data_sets
        with open(p_ds, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(cleaned)

        # Sync to Datafiles if present
        if df_arranged and os.path.exists(df_arranged):
            p_df = os.path.join(df_arranged, fname)
            with open(p_df, 'w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(header)
                w.writerows(cleaned)

        stats[subj_name] = (before_count, after_count)
        print(f"  Processed {subj_name:40s} | Before: {before_count:3d} -> After: {after_count:3d}")

    # Process IoT datasets
    iot_count = process_iot_datasets(ds_arranged, None)
    stats["Internet_of_Things"] = ("50+52 (unmerged)", iot_count)
    stats["Fundamentals_of_IoT"] = ("50+52 (unmerged)", iot_count)
    print(f"  Processed {'IoT & Fundamentals of IoT (Unified)':40s} | -> Consolidated: {iot_count:3d}")

    # Process root AI dataset
    if root_ai and os.path.exists(root_ai):
        root_ai_count = process_root_ai(root_ai)
        print(f"  Processed {'Root Artificial_Intelligence_Dataset.csv':40s} | -> Cleaned: {root_ai_count:3d}")

    print("\n" + "=" * 80)
    print("RUNNING FINAL POST-CLEANING QUALITY VERIFICATION AUDIT")
    print("=" * 80)

    total_issues = 0
    for fname in sorted(os.listdir(ds_arranged)):
        if not fname.endswith(".csv"):
            continue
        p = os.path.join(ds_arranged, fname)
        with open(p, 'r', encoding='utf-8') as f:
            rows = list(csv.reader(f))[1:]

        dupes = defaultdict(list)
        creates = 0
        part_invs = 0
        severed = 0

        for idx, r in enumerate(rows):
            if len(r) < 7: continue
            q = r[1]
            if r[3] not in VALID_BLOOMS:
                creates += 1
            m = int(r[4]) if r[4].isdigit() else 0
            pa = parse_years(r[5])
            pb = parse_years(r[6])
            if m <= 3 and pb and not pa:
                part_invs += 1
            elif m >= 8 and pa and not pb:
                part_invs += 1
            if re.search(r'^(?:explain|define|discuss|write|describe|trace|give|consider|state)\s+(?:the following|any|each of the following|the following terms)[\s:]*$', q.strip(), re.I):
                severed += 1
            norm = normalize_text_for_dedup(q)
            dupes[(r[2], norm)].append(idx)

        dupe_count = sum(1 for v in dupes.values() if len(v) > 1)
        issues = creates + part_invs + severed + dupe_count
        total_issues += issues

        status = "PASSED (0 issues)" if issues == 0 else f"ISSUES: dup={dupe_count}, bloom={creates}, inv={part_invs}, sev={severed}"
        print(f"  {fname:45s} | {len(rows):3d} rows | {status}")

    print("=" * 80)
    print(f"TOTAL REMAINING QUALITY ISSUES ACROSS ALL SUBJECTS: {total_issues}")
    print("=" * 80)

if __name__ == "__main__":
    main()
