"""
build_ai_dataset.py
-------------------
Builds Artificial_Intelligence_Dataset.csv from all AI question paper .txt files
across R13, R16, R18 regulations.

Topic tags are derived from the official syllabus units.
Output: Data/Artificial_Intelligence_Dataset.csv
"""

import re
import csv
from pathlib import Path
from collections import defaultdict

# ── OUTPUT ────────────────────────────────────────────────────────────────────
OUTPUT         = Path("Data/Artificial_Intelligence_Dataset.csv")
OUTPUT_FIGURES = Path("Data/Artificial_Intelligence_Dataset_figures.csv")
SUBJECT_NAME   = "Artificial Intelligence"

# ── DIAGRAM / FIGURE DETECTION ────────────────────────────────────────────────
# Questions that reference diagrams, figures, tables or embedded data
# that were lost during PDF→text conversion are split out to a separate file.

DIAGRAM_PATTERNS = [
    r"\bneat sketch\b",
    r"\bneat diagram\b",
    r"\bdraw a\b",
    r"\bdraw the\b",
    r"\bshown below\b",
    r"\bshown in\b",
    r"\bgiven diagram\b",
    r"\bgiven figure\b",
    r"\babove figure\b",
    r"\brefer to.*fig\b",
    r"\bas shown\b",
    r"\bfollowing circuit\b",
    r"\bfollowing diagram\b",
    r"\bfollowing figure\b",
    r"\bdendrogram\b",
    r"following data:\s",
    r"following.*distance.*matrix",
    r"following.*table",
    r"generate decision tree for the following data",
    r"show the final result of hierarchical clustering.*draw",
]
DIAGRAM_RE = re.compile("|".join(DIAGRAM_PATTERNS), re.IGNORECASE)

# Inline tabular data patterns (data rows embedded in question text)
TABULAR_DATA_RE = re.compile(
    r"(rainy|overcast|sunny|hot|mild|cool|high|normal|false|true|yes|no)\s+"
    r"(rainy|overcast|sunny|hot|mild|cool|high|normal|false|true|yes|no)",
    re.IGNORECASE
)

def has_figure(text: str) -> bool:
    return bool(DIAGRAM_RE.search(text) or TABULAR_DATA_RE.search(text))

# ── TOPIC TAG MAPPING ─────────────────────────────────────────────────────────
# Maps keyword patterns → canonical topic_tag from syllabus units
# R13/R16 and R18 syllabi verified — tags cover all 5 units

TOPIC_RULES = [
    # Unit I — Introduction & Search
    (["intelligent system", "intelligent agent", "agent program", "agent system",
      "sub.area of ai", "subarea", "foundation of ai", "history of ai",
      "application of ai", "application of artificial intelligence",
      "what is artificial intelligence", "define artificial intelligence",
      "problems underlying with ai", "ai technique", "ai problem",
      "thinking rationally", "acting humanly", "well defined problem",
      "simple problem solving agent"],
     "INTRODUCTION_AND_AI_OVERVIEW"),

    (["state space", "state-space", "problem space", "problem solving",
      "problem formulation", "characteristics of problem", "characteristics of a problem",
      "exhaustive search", "brute force", "depth.first", "breadth.first",
      "uniform cost", "iterative deepening", "bidirectional search",
      "search tree", "search algorithm", "uninformed search",
      "hill.climbing", "simulated annealing", "local search",
      "online search", "8 puzzle", "eight puzzle", "blocks.world",
      "towers of hanoi", "8.queen", "eight.queen"],
     "STATE_SPACE_SEARCH"),

    (["heuristic search", "a\\* ", "a\\*algorithm", "a-star", "best.first search",
      "greedy best", "admissib", "heuristic function", "informed search",
      "iterative deepening a\\*", "ida\\*", "branch and bound",
      "nearest neighbor heuristic"],
     "HEURISTIC_SEARCH"),

    (["alpha.beta", "alpha beta", "game playing", "game tree", "minimax",
      "mini.max", "bounded look.ahead", "evaluation function",
      "tic.tac.toe", "bounded lookahead", "imperfect real.time"],
     "GAME_PLAYING_AND_ALPHA_BETA"),

    (["constraint satisfaction", "csp", "cryptarithmetic", "backtracking search",
      "constraint propagation", "local search for csp", "job scheduling",
      "arc consistency"],
     "CONSTRAINT_SATISFACTION"),

    # Unit II — Logic & Knowledge Representation
    (["propositional logic", "propositional calculus", "semantic tableau",
      "resolution refutation", "resolution in propositional",
      "truth table", "well.formed formula", "tautology",
      "logical connect", "satisfiable", "contradictory", "valid",
      "forward chaining", "backward chaining", "horn clause",
      "wumpus world", "knowledge.based agent", "proof by resolution",
      "natural deduction", "axiomatic system", "refutation"],
     "PROPOSITIONAL_LOGIC"),

    (["predicate logic", "predicate calculus", "first.order logic", "first order logic",
      "quantifier", "universal quantif", "existential quantif",
      "unification", "lifting", "resolution in predicate",
      "inference in first.order", "represent.*sentence.*predicate",
      "predicate form", "clause form", "syntax and semantics of first",
      "circumscription", "default logic"],
     "PREDICATE_LOGIC"),

    (["semantic net", "semantic network", "extended semantic net",
      "knowledge representation.*semantic", "frame.*knowledge",
      "conceptual depend", "scripts", "inheritance.*frame",
      "approaches.*knowledge representation", "approaches to knowledge representation",
      "knowledge representation.*approach",
      "categories and objects", "ontological engineering",
      "reasoning systems for categories", "default information",
      "mental events"],
     "KNOWLEDGE_REPRESENTATION_SEMANTIC_NETS"),

    (["frame based", "frame.based", "knowledge representation using frame",
      "components.*frame", "what.*frame", "define.*frame",
      "frame with example", "knowledge.*frame"],
     "KNOWLEDGE_REPRESENTATION_FRAMES"),

    # Unit III — Expert Systems & Uncertainty
    (["expert system", "rule.based system", "rule based system",
      "knowledge base.*inference", "inference engine",
      "expert system architecture", "building expert system",
      "phases.*expert system", "expert system shell",
      "expert system.*traditional", "capabilities.*expert system",
      "knowledge acquisition", "knowledge engineering process",
      "logic.*based.*truth maintenance", "justification.*based.*truth"],
     "EXPERT_SYSTEMS"),

    (["truth maintenance", "tms", "jtms", "atms", "ltms",
      "assumption.based", "justification.based"],
     "TRUTH_MAINTENANCE_SYSTEMS"),

    (["bayesian", "bayes", "baye's rule", "bayesian belief network",
      "bayesian network", "conditional probability", "probability theory",
      "uncertainty.*probability", "acting under uncertainty",
      "joint distribution", "independence.*probability",
      "probabilistic reasoning", "relational.*probability"],
     "UNCERTAINTY_AND_BAYESIAN_NETWORKS"),

    (["certainty factor", "dempster.shafer", "dempster shafer",
      "certainty factor theory", "explicit representation",
      "uncertainty.*dempster", "reasoning under uncertainty"],
     "CERTAINTY_AND_DEMPSTER_SHAFER"),

    # Unit IV — Machine Learning & ANN (R13/R16) / Planning (R18)
    (["planning", "classical planning", "graphplan", "graph plan",
      "state.space search.*planning", "planning graph",
      "hierarchical planning", "multi.agent planning", "multiagent planning",
      "job.shop scheduling", "scheduling.*resource",
      "planning.*nondeterministic", "regressive.*state space",
      "temporal constraint"],
     "PLANNING"),

    (["machine learning", "supervised learning", "unsupervised learning",
      "reinforcement learning", "inductive learning", "deductive learning",
      "learning paradigm", "forms of learning", "machine learning system",
      "inductive logic programming", "explanation.based learning",
      "learning by.*advice", "learning.*parameter", "learning.*chunking",
      "knowledge in learning"],
     "MACHINE_LEARNING_PARADIGMS"),

    (["decision tree", "id3", "information gain", "entropy.*decision",
      "decision tree learning", "issues in decision tree",
      "decision tree.*boolean", "classify.*decision tree",
      "construct.*decision tree"],
     "DECISION_TREES"),

    (["clustering", "k.means", "k means", "hierarchical clustering",
      "dendrogram", "conceptual clustering"],
     "CLUSTERING"),

    (["support vector machine", "svm", "maximum margin hyperplane",
      "linear separab", "radial.basis function", "rbf network",
      "mathematical formulation.*svm"],
     "SUPPORT_VECTOR_MACHINES"),

    (["artificial neural network", "ann", "single.layer feed.forward",
      "multi.layer feed.forward", "multilayer perceptron",
      "recurrent network", "design issues.*neural",
      "perceptron.*training", "perceptron.*algorithm",
      "biological nn", "biological.*neural",
      "feed.forward network", "single layer.*network",
      "neural network.*design"],
     "ARTIFICIAL_NEURAL_NETWORKS"),

    # Unit V — NLP & Semantic Web
    (["natural language processing", "nlp", "sentence analysis",
      "phases.*natural language", "natural language understanding",
      "components.*natural language", "tasks.*natural language",
      "importance.*natural language", "applications.*natural language",
      "syntactic analysis", "semantic analysis", "parse tree",
      "parsing", "parser", "n.gram", "grammar.*nlp",
      "syntax.*semantics.*nlp", "process.*natural language"],
     "NATURAL_LANGUAGE_PROCESSING"),

    (["semantic web", "knowledge.*semantic web", "universal networking",
      "unk", "ontology", "rdf", "owl"],
     "SEMANTIC_WEB"),

    (["case grammar", "augmented transition network", "transition network parser",
      "grammar.*parser", "types of parser", "grammars and parser",
      "sentence analysis phase"],
     "CASE_GRAMMARS_AND_PARSERS"),
]

# ── BLOOM LEVEL ───────────────────────────────────────────────────────────────
BLOOM_RULES = [
    (["write a program", "implement", "develop a program", "construct", "compute",
      "calculate", "simulate", "trace the", "generate decision tree",
      "create a.*program", "build a.*model"],
     "Apply"),
    (["differentiate", "distinguish", "compare", "difference between",
      "contrast", "analyze the result", "analyze a", "how does.*differ"],
     "Analyze"),
    (["evaluate", "justify", "critique", "assess", "prove that", "support or oppose"],
     "Evaluate"),
    (["define", "what is", "what are", "list", "state", "name", "mention",
      "give an overview", "write short note", "brief note"],
     "Remember"),
    (["explain", "describe", "discuss", "illustrate", "elaborate", "demonstrate",
      "show", "summarize", "give an example", "with example", "with suitable example"],
     "Understand"),
]

# ── HELPERS ───────────────────────────────────────────────────────────────────

def assign_topic(text: str) -> str:
    t = text.lower()
    for keywords, tag in TOPIC_RULES:
        for kw in keywords:
            if re.search(kw, t):
                return tag
    return "INTRODUCTION_AND_AI_OVERVIEW"  # fallback

def assign_bloom(text: str) -> str:
    t = text.lower()
    for keywords, level in BLOOM_RULES:
        for kw in keywords:
            if kw in t:
                return level
    return "Understand"

def get_year(filename: str):
    m = re.search(r"(20\d{2})", Path(filename).stem)
    return int(m.group(1)) if m else None

def get_regulation(path: Path) -> str:
    for part in path.parts:
        m = re.match(r"(R\d{2})", part, re.IGNORECASE)
        if m:
            return m.group(1).upper()
    return "UNKNOWN"

# ── NOISE & SECTION PATTERNS ──────────────────────────────────────────────────
NOISE_RE = re.compile(
    r"jawaharlal nehru|b\.?\s*tech|time\s*:|max\.?\s*marks|"
    r"note\s*:|answer any|all questions carry|part [ab] is compulsory|"
    r"part [ab] consists|each question carries|^-{2,}|^---+oo|"
    r"jntuh\s+used|used\s+paper|r1[3568]\s*$|r22\s*$|\d{2}-\d{2}-\d{4}|"
    r"^\s*set\s*\d|code no\s*:|^oo[o0]oo",
    re.IGNORECASE | re.MULTILINE
)

PART_A_RE = re.compile(r"PART\s*[-–]\s*A", re.IGNORECASE)
PART_B_RE = re.compile(r"PART\s*[-–]\s*B", re.IGNORECASE)
MARKS_END_RE = re.compile(r"\[(\d+(?:[+\d]*)?)\]\s*$")
OR_RE = re.compile(r"^\s*OR\s*$", re.IGNORECASE)

# Sub-question patterns
PARTA_SUB_RE = re.compile(r"^\s*1\s*[.)]\s*([a-j])\s*[.)]\s*(.*)", re.DOTALL)
PARTB_NUM_RE = re.compile(r"^\s*(\d+)\s*[.)a-e]\s*[.)]\s*(.*)")
STANDALONE_NUM_RE = re.compile(r"^\s*(\d+)\s*[.)]\s*(.*)")

def strip_marks(text):
    m = MARKS_END_RE.search(text)
    if m:
        raw = m.group(1)
        marks = sum(int(x) for x in re.findall(r"\d+", raw))
        return text[:m.start()].strip(), marks
    return text.strip(), 0

def is_noise(line):
    return bool(NOISE_RE.search(line))

def clean_text(text):
    return re.sub(r"\s{2,}", " ", text).strip()

# ── EXTRACT QUESTIONS FROM ONE FILE ───────────────────────────────────────────

def extract_questions(filepath: Path, year: int, regulation: str) -> list:
    raw = filepath.read_text(encoding="utf-8", errors="ignore")

    if "[SCANNED IMAGE PDF" in raw:
        return []

    lines = raw.splitlines()
    questions = []

    in_part_a = False
    in_part_b = False
    current_text = []
    current_type = None

    def flush():
        if not current_text or current_type is None:
            return
        text = clean_text(" ".join(current_text))
        text, marks = strip_marks(text)
        if len(text) < 20:
            return
        if marks == 0:
            marks = 2 if current_type == "PART_A" else 10
        questions.append({
            "raw_question_text": text,
            "question_type": current_type,
            "original_marks": marks,
            "year": year,
            "regulation": regulation,
        })
        current_text.clear()

    # Check paper format
    has_part_a = any(PART_A_RE.search(l) for l in lines)

    # Flat format (Feb 2022 style — "Answer any five questions")
    if not has_part_a:
        # All questions are Part B style
        for line in lines:
            s = line.strip()
            if not s or is_noise(s):
                continue
            if OR_RE.match(s):
                flush()
                continue
            m = STANDALONE_NUM_RE.match(s)
            if m:
                flush()
                qnum = int(m.group(1))
                rest = m.group(2).strip()
                current_type = "PART_B"
                if rest:
                    # strip sub letter if present: "a) ..."
                    rest = re.sub(r"^[a-e]\s*[.)]\s*", "", rest)
                    current_text.append(rest)
            else:
                # sub-question continuation
                sub = re.match(r"^\s*[a-e]\s*[.)]\s*(.*)", s)
                if sub and current_text:
                    current_text.append(sub.group(1).strip())
                elif current_text:
                    current_text.append(s)
        flush()
        return questions

    # Part A / Part B format
    section = None
    for line in lines:
        s = line.strip()
        if not s:
            continue
        if is_noise(s):
            continue
        if PART_A_RE.search(s):
            flush()
            section = "A"
            continue
        if PART_B_RE.search(s):
            flush()
            section = "B"
            continue
        if OR_RE.match(s):
            flush()
            continue

        if section == "A":
            # Part A: "1.a) ..." or standalone "a) ..."
            sub = re.match(r"^\s*(?:1\s*[.)]\s*)?([a-j])\s*[.)]\s*(.*)", s)
            if sub:
                flush()
                rest = sub.group(2).strip()
                current_type = "PART_A"
                if rest:
                    current_text.append(rest)
            elif current_text:
                current_text.append(s)

        elif section == "B":
            # Part B: numbered questions
            m = re.match(r"^\s*(\d+)\s*[.)]\s*(.*)", s)
            if m:
                qnum = int(m.group(1))
                if qnum == 1:
                    continue  # skip question 1 in Part B (it's Part A)
                flush()
                rest = m.group(2).strip()
                current_type = "PART_B"
                rest = re.sub(r"^[a-e]\s*[.)]\s*", "", rest)
                if rest:
                    current_text.append(rest)
            else:
                sub = re.match(r"^\s*[a-e]\s*[.)]\s*(.*)", s)
                if sub and current_text:
                    current_text.append(sub.group(1).strip())
                elif current_text:
                    current_text.append(s)

    flush()
    return questions

# ── DEDUPLICATE ───────────────────────────────────────────────────────────────

def normalize_text(text: str) -> str:
    """Normalize for dedup comparison."""
    t = text.lower()
    t = re.sub(r"[^a-z0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def merge_duplicates(raw_questions: list) -> list:
    """
    Group questions with same normalized text.
    Merge part_a_years and part_b_years.
    Keep the longest version of the text.
    """
    groups = defaultdict(list)
    for q in raw_questions:
        key = normalize_text(q["raw_question_text"])
        groups[key].append(q)

    merged = []
    for key, group in groups.items():
        canonical = max(group, key=lambda x: len(x["raw_question_text"]))
        part_a_years = sorted(set(
            q["year"] for q in group
            if q["question_type"] == "PART_A" and q["year"]
        ))
        part_b_years = sorted(set(
            q["year"] for q in group
            if q["question_type"] == "PART_B" and q["year"]
        ))
        marks_list = [q["original_marks"] for q in group if q["original_marks"]]
        merged.append({
            "subject_name": SUBJECT_NAME,
            "raw_question_text": canonical["raw_question_text"],
            "topic_tag": assign_topic(canonical["raw_question_text"]),
            "bloom_level": assign_bloom(canonical["raw_question_text"]),
            "original_marks": max(marks_list) if marks_list else 0,
            "part_a_years": str(part_a_years),
            "part_b_years": str(part_b_years),
        })

    return merged

# ── MAIN ──────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "subject_name", "raw_question_text", "topic_tag", "bloom_level",
    "original_marks", "part_a_years", "part_b_years",
]

AI_DIRS = [
    Path("Data/Text_data/All_Reg_QP_Text_data/R13_text/question papers/4-1/ARTIFICIAL INTELLIGENCE"),
    Path("Data/Text_data/All_Reg_QP_Text_data/R16_text/Question Papers/3-2/ARTIFICIAL INTELLIGENCE"),
    Path("Data/Text_data/All_Reg_QP_Text_data/R18 text/4th Year/Semester 1/ARTIFICIAL INTELLIGENCE"),
]

def main():
    all_questions = []

    for ai_dir in AI_DIRS:
        if not ai_dir.exists():
            print(f"[SKIP] Not found: {ai_dir}")
            continue
        for txt_file in sorted(ai_dir.glob("*.txt")):
            year = get_year(txt_file.name)
            regulation = get_regulation(txt_file)
            qs = extract_questions(txt_file, year, regulation)
            print(f"  {regulation} | {txt_file.name:40s} | {len(qs)} questions")
            all_questions.extend(qs)

    print(f"\nTotal extracted : {len(all_questions)}")

    merged = merge_duplicates(all_questions)
    print(f"After dedup     : {len(merged)}")

    # Sort by topic_tag for readability
    merged.sort(key=lambda x: (x["topic_tag"], x["raw_question_text"]))

    # Split into clean and figure-dependent
    clean_rows   = [r for r in merged if not has_figure(r["raw_question_text"])]
    figure_rows  = [r for r in merged if has_figure(r["raw_question_text"])]

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(clean_rows)

    with open(OUTPUT_FIGURES, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(figure_rows)

    # Stats
    tag_counts = defaultdict(int)
    for r in clean_rows:
        tag_counts[r["topic_tag"]] += 1

    print(f"\nClean output    : {OUTPUT}  ({len(clean_rows)} questions)")
    print(f"Figures archive : {OUTPUT_FIGURES}  ({len(figure_rows)} questions)")
    print(f"\nQuestions per topic (clean):")
    for tag, cnt in sorted(tag_counts.items()):
        print(f"  {tag:45s}: {cnt}")
    print(f"\nFigure-dependent questions (moved to figures file):")
    for r in figure_rows:
        print(f"  [{r['topic_tag']}] {r['raw_question_text'][:100]}")

if __name__ == "__main__":
    main()
