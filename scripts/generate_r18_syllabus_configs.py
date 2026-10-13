"""
generate_r18_syllabus_configs.py
---------------------------------
Auto-generates topic-tag configs for R18 subjects from the official JNTUH R18
syllabus text files (one per year). Existing configs are never overwritten.

Usage:
    python scripts/generate_r18_syllabus_configs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

R18_TEXT_ROOT = (
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data" / "R18 text"
)
SYLLABUS_FILES = [
    R18_TEXT_ROOT / "1st Year" / "Syllabus" / "R18 B.Tech I Year Syllabus (Circuit Branches incl. CSE).txt",
    R18_TEXT_ROOT / "2nd Year" / "Syllabus" / "R18 B.Tech CSE II Year Syllabus.txt",
    R18_TEXT_ROOT / "3rd Year" / "Syllabus" / "R18 B.Tech CSE III Year Syllabus.txt",
    R18_TEXT_ROOT / "4th Year" / "Syllabus" / "R18 B.Tech CSE IV Year Syllabus.txt",
]
CONFIG_DIR = PROJECT_ROOT / "data" / "syllabi" / "configs" / "R18"

STOPWORDS = {
    "to", "of", "and", "the", "a", "an", "in", "on", "for", "with", "using",
    "their", "its", "they", "is", "are", "be", "by", "as", "at", "or", "etc",
    "introduction", "definition", "definitions", "concepts", "concept", "basic",
    "operations", "operation", "various", "different", "example", "examples",
    "only", "from", "into", "over", "this", "that", "these", "those", "such",
    "about", "between", "other", "given", "following", "need", "uses", "used",
    "study", "simple", "general", "unit", "objectives", "outcomes", "text",
    "books", "reference",
}

GENERIC_TAGS = {
    "DEFINITION", "DEFINITIONS", "OPERATIONS", "OPERATION", "TERMINOLOGY",
    "INTRODUCTION", "OVERVIEW", "CONCEPTS", "PROPERTIES", "PROPERTY", "TYPES",
    "TYPE", "CLASSIFICATION", "ADVANTAGES", "DISADVANTAGES", "APPLICATIONS",
    "APPLICATION", "EXAMPLES", "EXAMPLE", "COMPARISON", "BASIC", "GENERAL",
    "STRUCTURE", "STRUCTURES", "FEATURES", "METHODS", "METHOD", "TECHNIQUES",
    "TECHNIQUE", "ALGORITHM", "ALGORITHMS", "PROBLEMS", "PROBLEM", "SYSTEMS",
    "SYSTEM", "STUDY", "NOTATION", "NOTATIONS",
}


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def tokenize(name: str) -> set[str]:
    return {w for w in re.findall(r"[A-Z0-9]+", name.upper()) if w}


def split_units(body: str) -> list[tuple[str, str]]:
    body = re.split(r"TEXT\s+BOOKS|REFERENCE\s+BOOKS|Outcomes:", body, flags=re.IGNORECASE)[0]
    parts = re.split(
        r"\bUNIT\s*[-–:]?\s*(I{1,3}|IV|V\b|[1-5])\b",
        body, flags=re.IGNORECASE,
    )
    units: list[tuple[str, str]] = []
    i = 1
    while i + 1 < len(parts):
        units.append((parts[i].upper(), parts[i + 1]))
        i += 2
    return units or [("UNIT_1", body)]


def extract_tags(unit_text: str, top_n: int = 8) -> list[str]:
    text = re.sub(r"[•·]", " ", unit_text)
    text = re.sub(r"\s+", " ", text)
    phrases = re.split(r"[,;.:]|\s[-–]\s|/|\)|\(", text)
    tags: list[str] = []
    seen: set[str] = set()
    for phrase in phrases:
        words = re.findall(r"[A-Za-z][A-Za-z0-9]*", phrase.lower())
        core = [w for w in words if w not in STOPWORDS]
        if not core:
            continue
        tag = "_".join(w.upper() for w in core[:4])
        if len(tag) < 4 or tag in seen or tag in GENERIC_TAGS:
            continue
        seen.add(tag)
        tags.append(tag)
        if len(tags) >= top_n:
            break
    return tags


def build_config(subject_name: str, body: str) -> dict:
    units_out: dict[str, dict] = {}
    keywords: dict[str, list[str]] = {}
    for idx, (label, unit_text) in enumerate(split_units(body), start=1):
        tags = extract_tags(unit_text)
        if not tags:
            continue
        unit_key = f"UNIT_{idx}"
        units_out[unit_key] = {"name": label, "topics": tags}
        for tag in tags:
            phrase = tag.replace("_", " ").lower()
            words = [w for w in tag.lower().split("_") if len(w) > 3]
            keywords[tag] = [phrase] + words
    return {
        "subject_name": subject_name,
        "regulation": "R18",
        "units": units_out,
        "topic_keywords": keywords,
    }


def parse_subjects_from_syllabus(text: str) -> dict[str, str]:
    """Extract subject name → body from R18 syllabus text.

    R18 syllabus uses course-code headers of the form:
        CS501PC: FORMAL LANGUAGES AND AUTOMATA THEORY
        CS511PE: INFORMATION THEORY & CODING (Professional Elective - I)
        SM402MS/SM305MS: BUSINESS ECONOMICS AND FINANCIAL ANALYSIS
    We split on those lines and map the normalised subject name to its body.
    Lab sections (ending in LAB) are skipped.
    """
    # Pattern: one or more course codes (e.g. CS501PC or CS501PC/IT502PC) followed
    # by a colon and the subject name (which may include parenthesised elective info).
    header_re = re.compile(
        r'^[A-Z]{2}\d{3}[A-Z]{2}(?:/[A-Z]{2}\d{3}[A-Z]{2})*:\s*(.+)$'
    )

    lines = text.splitlines()
    subjects: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        m = header_re.match(stripped)
        if m:
            # Save previous section
            if current_name and current_lines:
                subjects[current_name] = "\n".join(current_lines)
            # Normalise: strip elective label in parens, uppercase
            raw_name = m.group(1).strip()
            raw_name = re.sub(r'\s*\(.*?\)\s*$', '', raw_name).strip()
            name = raw_name.upper()
            # Skip lab entries
            if re.search(r'\bLAB\b', name):
                current_name = None
                current_lines = []
            else:
                current_name = name
                current_lines = []
        elif current_name:
            current_lines.append(line)

    if current_name and current_lines:
        subjects[current_name] = "\n".join(current_lines)

    return subjects


def get_all_subject_folders() -> list[tuple[str, Path]]:
    folders = []
    for year_dir in sorted(R18_TEXT_ROOT.iterdir()):
        if not year_dir.is_dir() or year_dir.name == "Syllabus":
            continue
        for sem_dir in sorted(year_dir.iterdir()):
            if not sem_dir.is_dir() or sem_dir.name == "Syllabus":
                continue
            for subj_dir in sorted(sem_dir.iterdir()):
                if subj_dir.is_dir():
                    folders.append((subj_dir.name, subj_dir))
    return folders


def match_subject(folder: str, sections: dict[str, str]) -> str | None:
    folder_tokens = tokenize(folder) - {"AND", "OF", "THE", "FOR"}
    best_name, best_score = None, 0.0
    for name in sections:
        name_tokens = tokenize(name) - {"AND", "OF", "THE", "FOR"}
        if not folder_tokens:
            continue
        score = len(folder_tokens & name_tokens) / len(folder_tokens)
        if score > best_score:
            best_score, best_name = score, name
    return best_name if best_score >= 0.5 else None


def main() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Merge all syllabus texts and parse subjects
    all_sections: dict[str, str] = {}
    for syllabus_file in SYLLABUS_FILES:
        if syllabus_file.exists():
            text = syllabus_file.read_text(encoding="utf-8", errors="ignore")
            all_sections.update(parse_subjects_from_syllabus(text))

    print(f"Found {len(all_sections)} syllabus sections across R18 files.")

    created, skipped, unmatched = [], [], []
    for folder, _ in get_all_subject_folders():
        config_path = CONFIG_DIR / f"{slugify(folder)}_syllabus.json"
        if config_path.exists():
            skipped.append(folder)
            continue
        syllabus_name = match_subject(folder, all_sections)
        if not syllabus_name:
            # Generate a minimal config with folder name as single tag
            config = {
                "subject_name": folder.title(),
                "regulation": "R18",
                "units": {"UNIT_1": {"name": "GENERAL", "topics": [slugify(folder).upper()]}},
                "topic_keywords": {slugify(folder).upper(): [folder.lower()]},
            }
            unmatched.append(folder)
        else:
            config = build_config(folder.title(), all_sections[syllabus_name])
            config["syllabus_section"] = syllabus_name
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        created.append(folder)

    print(f"Created {len(created)} config(s), skipped {len(skipped)} existing.")
    if unmatched:
        print(f"Unmatched (minimal config generated): {', '.join(unmatched)}")


if __name__ == "__main__":
    main()
