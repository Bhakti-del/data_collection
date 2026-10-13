"""
generate_r15_syllabus_configs.py
--------------------------------
Auto-generates topic-tag configs for R15 subjects from the official JNTUH R15
syllabus text file. Existing hand-written configs (e.g. Basic Electrical
Engineering, Java) are never overwritten.

For every subject folder under the R15 question-paper tree, the script:
  1. Finds the matching syllabus section in R15_CSE_I_to_IV_Syllabus.txt.
  2. Splits it into UNIT blocks and extracts UPPER_SNAKE topic tags.
  3. Writes data/syllabi/configs/R15/<Subject>_syllabus.json with a
     `topic_keywords` map usable by build_r15_dataset.py.

Usage:
    python scripts/generate_r15_syllabus_configs.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SYLLABUS_TXT = (
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data"
    / "R15_text" / "Syllabus" / "R15_CSE_I_to_IV_Syllabus.txt"
)
QP_ROOT = (
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data"
    / "R15_text" / "Question Papers"
)
CONFIG_DIR = PROJECT_ROOT / "data" / "syllabi" / "configs" / "R15"

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


def parse_syllabus_sections(text: str) -> dict[str, str]:
    """(A#####) NAME → body text, covering every detailed syllabus section."""
    pattern = re.compile(r"^\((A\d{5})\)\s+([A-Z0-9][^\n]*)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    sections: dict[str, str] = {}
    for i, m in enumerate(matches):
        name = re.sub(r"\s+", " ", m.group(2)).strip()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():body_end]
        # Trim trailing lab/misc sections.
        body = re.split(r"\n\s*REFERENCE BOOKS|\n\s*Outcomes", body)[0]
        sections[name] = body
    return sections


def normalize_name(name: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "", name.upper())


def tokenize(name: str) -> set[str]:
    return {w for w in re.findall(r"[A-Z0-9]+", name.upper()) if w}


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


def split_units(body: str) -> list[tuple[str, str]]:
    """Returns (unit_label, unit_text) pairs; falls back to one pseudo-unit."""
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
    if not units:
        units = [("UNIT_1", body)]
    return units


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
        core = core[:4]
        tag = "_".join(w.upper() for w in core)
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
    units = split_units(body)
    for idx, (label, unit_text) in enumerate(units, start=1):
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
        "regulation": "R15",
        "units": units_out,
        "topic_keywords": keywords,
    }


def subject_folders() -> list[tuple[str, Path]]:
    folders = []
    for semester in sorted(QP_ROOT.iterdir()):
        if not semester.is_dir():
            continue
        for subject in sorted(semester.iterdir()):
            if subject.is_dir():
                folders.append((subject.name, subject))
    return folders


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def main() -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    text = SYLLABUS_TXT.read_text(encoding="utf-8", errors="ignore")
    sections = parse_syllabus_sections(text)

    created, skipped, unmatched = [], [], []
    for folder, _path in subject_folders():
        config_path = CONFIG_DIR / f"{slugify(folder)}_syllabus.json"
        if config_path.exists():
            skipped.append(folder)
            continue
        syllabus_name = match_subject(folder, sections)
        if not syllabus_name:
            unmatched.append(folder)
            continue
        config = build_config(folder.title(), sections[syllabus_name])
        config["syllabus_section"] = syllabus_name
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
        created.append(f"{folder}  <-  {syllabus_name}  ({len(config['topic_keywords'])} tags)")

    print(f"Created {len(created)} config(s):")
    for c in created:
        print("  +", c)
    if skipped:
        print(f"Skipped {len(skipped)} (existing config): {', '.join(skipped)}")
    if unmatched:
        print(f"Unmatched {len(unmatched)}: {', '.join(unmatched)}")


if __name__ == "__main__":
    main()
