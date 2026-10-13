"""
build_r18_dataset.py
--------------------
Builds per-subject datasets for every R18 subject by combining:
  - Atomic question parsing + diagram cropping from scripts/extract_images.py
  - topic_tag + bloom_level inference (keyword based, syllabus config)
  - part_a_years / part_b_years aggregation across exam years

R18 text tree layout (one extra depth level vs R15):
    temp_data/Text_data/All_Reg_QP_Text_data/R18 text/
        <Year>/
            Semester <N>/
                <SUBJECT>/
                    <paper>.txt

For each subject two CSVs are written:
    data/datasets/<Subject>_R18_Dataset.csv            (all questions)
    data/datasets_with_images/<Subject>_R18_Dataset.csv (only image rows)

Schema:
    subject_name, raw_question_text, topic_tag, bloom_level,
    original_marks, part_a_years, part_b_years, image_path

Topic configs are read from data/syllabi/configs/R18/<SUBJECT>_syllabus.json.
Run scripts/generate_r18_syllabus_configs.py first to create missing ones.

Usage:
    python scripts/build_r18_dataset.py            # all subjects
    python scripts/build_r18_dataset.py --subject "DATA STRUCTURES"
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent
sys.path.insert(0, str(SCRIPTS_DIR))

from extract_images import process_paper  # noqa: E402

REGULATION = "R18"
# R18 text root: .../R18 text/<Year>/Semester <N>/<SUBJECT>/
TEXT_ROOT = (
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data" / "R18 text"
)
CONFIG_DIR = PROJECT_ROOT / "data" / "syllabi" / "configs" / REGULATION
IMG_OUT = PROJECT_ROOT / "data" / "images"
DATASETS_DIR = PROJECT_ROOT / "data" / "datasets"
DATASETS_IMG_DIR = PROJECT_ROOT / "data" / "datasets_with_images"

BLOOM_VERBS = {
    "Evaluate":   ["evaluate", "justify", "assess", "critique", "recommend", "support or oppose"],
    "Analyze":    ["analyze", "analyse", "compare", "differentiate", "distinguish", "derive",
                   "examine", "contrast", "determine", "trace"],
    "Apply":      ["write", "implement", "construct", "solve", "perform", "compute", "calculate",
                   "show", "demonstrate", "apply", "develop", "design", "draw", "find",
                   "obtain", "simulate", "convert", "estimate"],
    "Understand": ["explain", "describe", "discuss", "summarize", "interpret", "classify",
                   "illustrate", "give an example", "how does", "what happens"],
    "Remember":   ["define", "list", "state", "name", "identify", "what is", "what are",
                   "mention", "recall", "label"],
}


def infer_bloom(text: str) -> str:
    t = text.lower()
    for level in ("Evaluate", "Analyze", "Apply", "Understand", "Remember"):
        if any(verb in t for verb in BLOOM_VERBS[level]):
            return level
    return "Understand"


def slugify(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")


def title_slug(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", name.title()).strip("_")


def load_config(folder: str) -> tuple[dict[str, list[str]], dict[str, str], dict[str, list[str]]]:
    config_path = CONFIG_DIR / f"{slugify(folder)}_syllabus.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Missing syllabus config: {config_path}")
    config = json.loads(config_path.read_text(encoding="utf-8"))

    keywords = config.get("topic_keywords", {})
    tag_unit: dict[str, str] = {}
    for unit, meta in config.get("units", {}).items():
        for tag in meta.get("topics", []):
            tag_unit[tag] = unit
    domain_triggers = config.get("domain_triggers", {})
    return keywords, tag_unit, domain_triggers


def _score_tags(text: str, tags: list[str], keywords: dict[str, list[str]]) -> tuple[str, int]:
    best_tag, best_score = "UNTAGGED", 0
    for tag in tags:
        score = sum(1 for kw in keywords.get(tag, []) if kw in text)
        if score > best_score:
            best_score, best_tag = score, tag
    return best_tag, best_score


def infer_topic(text, keywords, tag_unit, domain_triggers) -> str:
    t = " " + re.sub(r"\s+", " ", text.lower()) + " "
    for unit, triggers in domain_triggers.items():
        if any(trigger in t for trigger in triggers):
            unit_tags = [tag for tag, u in tag_unit.items() if u == unit]
            tag, score = _score_tags(t, unit_tags, keywords)
            if score > 0:
                return tag
    tag, _ = _score_tags(t, list(keywords.keys()), keywords)
    return tag


def parse_year(filename: str) -> int | None:
    m = re.search(r"(\d{4})", filename)
    return int(m.group(1)) if m else None


def clean_question_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.split(r"\bPART\s*[-–]?\s*[AB]\b", text, flags=re.IGNORECASE)[0]
    text = re.split(r"\bJNTUH\b", text, flags=re.IGNORECASE)[0]
    text = re.sub(r"\bR1[0-9]\b", " ", text)
    text = re.sub(r"^\s*\d+\.\s*(?:[a-j]\))?\s*", "", text)
    text = re.sub(r"^\s*[a-j]\)\s*", "", text)
    text = re.sub(r"\s*Figure\s*[:.]?\s*\d+\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\[[\d\s\+]*\]", " ", text)
    text = re.sub(r"\s*\bOR\b\s*$", "", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def extract_marks_local(text: str) -> int | None:
    m = re.search(r"\[(\d+(?:\s*\+\s*\d+)*)\]\s*$", text)
    if not m:
        return None
    return sum(int(x) for x in re.split(r"\s*\+\s*", m.group(1)))


def question_marks(questions: list[dict]) -> dict[str, int]:
    marks: dict[str, int] = {}
    groups: dict[str, list[dict]] = {}
    for q in questions:
        groups.setdefault(q["question_no"].split(".")[0], []).append(q)

    bracket = re.compile(r"\[(\d+(?:\s*\+\s*\d+)*)\]")
    for group in groups.values():
        explicit = {q["question_no"]: extract_marks_local(q["raw_question_text"]) for q in group}
        if all(v is not None for v in explicit.values()):
            marks.update(explicit)
            continue
        components: list[int] = []
        for q in group:
            m = bracket.search(q["raw_question_text"])
            if m:
                components = [int(x) for x in re.split(r"\s*\+\s*", m.group(1))]
        if components and len(components) == len(group):
            for q, component in zip(group, components):
                marks[q["question_no"]] = component
        elif components:
            per = max(1, round(sum(components) / len(group)))
            for q in group:
                marks[q["question_no"]] = per
        else:
            for q_no, v in explicit.items():
                marks[q_no] = v if v is not None else ""
    return marks


def build_subject(folder: str, text_dir: Path) -> tuple[int, int]:
    keywords, tag_unit, domain_triggers = load_config(folder)
    subject_name = folder.title()

    dataset: dict[str, dict] = {}
    txt_files = sorted(text_dir.glob("*.txt"))
    for txt_path in txt_files:
        year = parse_year(txt_path.name)
        if not year:
            continue
        rows = process_paper(txt_path, IMG_OUT)
        if not rows:
            continue
        content = txt_path.read_text(encoding="utf-8", errors="ignore")
        has_part_a = bool(re.search(r"PART\s*[-–]?\s*A\b", content, re.IGNORECASE))
        marks = question_marks(rows)

        for row in rows:
            q_no = row["question_no"]
            raw = clean_question_text(row["raw_question_text"])
            if len(raw) < 10:
                continue
            main = q_no.split(".")[0]
            part = "A" if (has_part_a and main == "1") else "B"
            key = re.sub(r"[^a-z0-9]", "", raw.lower())

            rec = dataset.get(key)
            if rec is None:
                rec = {
                    "subject_name": subject_name,
                    "raw_question_text": raw,
                    "topic_tag": infer_topic(raw, keywords, tag_unit, domain_triggers),
                    "bloom_level": infer_bloom(raw),
                    "original_marks": marks.get(q_no, ""),
                    "part_a_years": set(),
                    "part_b_years": set(),
                    "image_paths": [],
                }
                dataset[key] = rec

            (rec["part_a_years"] if part == "A" else rec["part_b_years"]).add(year)
            if rec["original_marks"] in ("", None) and marks.get(q_no):
                rec["original_marks"] = marks[q_no]
            img = row.get("image_path", "")
            if img and img not in rec["image_paths"]:
                rec["image_paths"].append(img)

    fieldnames = [
        "subject_name", "raw_question_text", "topic_tag", "bloom_level",
        "original_marks", "part_a_years", "part_b_years", "image_path",
    ]

    def to_row(rec: dict) -> dict:
        return {
            "subject_name": rec["subject_name"],
            "raw_question_text": rec["raw_question_text"],
            "topic_tag": rec["topic_tag"],
            "bloom_level": rec["bloom_level"],
            "original_marks": rec["original_marks"],
            "part_a_years": sorted(rec["part_a_years"]),
            "part_b_years": sorted(rec["part_b_years"]),
            "image_path": "; ".join(rec["image_paths"]),
        }

    base = f"{title_slug(folder)}_R18_Dataset.csv"
    DATASETS_DIR.mkdir(parents=True, exist_ok=True)
    DATASETS_IMG_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATASETS_DIR / base, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in dataset.values():
            writer.writerow(to_row(rec))

    with_img = 0
    with open(DATASETS_IMG_DIR / base, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in dataset.values():
            if rec["image_paths"]:
                writer.writerow(to_row(rec))
                with_img += 1

    return len(dataset), with_img


def subject_folders() -> list[tuple[str, Path]]:
    """Walk <Year>/Semester <N>/<SUBJECT>/ and return (subject_name, path) pairs."""
    folders = []
    for year_dir in sorted(TEXT_ROOT.iterdir()):
        if not year_dir.is_dir() or year_dir.name == "Syllabus":
            continue
        for sem_dir in sorted(year_dir.iterdir()):
            if not sem_dir.is_dir() or sem_dir.name == "Syllabus":
                continue
            for subj_dir in sorted(sem_dir.iterdir()):
                if subj_dir.is_dir():
                    folders.append((subj_dir.name, subj_dir))
    return folders


def main() -> None:
    parser = argparse.ArgumentParser(description="Build R18 per-subject datasets.")
    parser.add_argument("--subject", type=str, help="Subject folder name (default: all)")
    args = parser.parse_args()

    folders = subject_folders()
    if args.subject:
        folders = [(n, p) for n, p in folders if n.lower() == args.subject.lower()]
        if not folders:
            raise SystemExit(f"No R18 subject folder matching '{args.subject}'")

    print(f"Building {len(folders)} subject(s)...\n")
    total_q = total_img = skipped = 0
    for folder, path in folders:
        try:
            n, img = build_subject(folder, path)
        except FileNotFoundError as exc:
            print(f"[SKIP] {folder}: {exc}")
            skipped += 1
            continue
        total_q += n
        total_img += img
        print(f"{folder:50} questions={n:4}  with_image={img}")

    print(f"\n{'='*65}")
    print(f"Subjects processed : {len(folders) - skipped}  (skipped {skipped})")
    print(f"Total questions    : {total_q}")
    print(f"Image questions    : {total_img}")
    print(f"Datasets dir       : {DATASETS_DIR}")
    print(f"Images-only dir    : {DATASETS_IMG_DIR}")


if __name__ == "__main__":
    main()
