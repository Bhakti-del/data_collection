"""
clean_papers.py
Strips boilerplate from JNTUH question paper text files.
Writes cleaned files to data/cleaned_papers/ (or custom directory) mirroring the original structure.

Usage:
    python3 scripts/clean_papers.py
    python3 scripts/clean_papers.py --input_dir Data/Text_data/All_Reg_QP_Text_data --output_dir data/cleaned_papers
    python3 scripts/clean_papers.py --regulation R18 --dry-run
"""

import os
import re
import argparse
from pathlib import Path

# ---------------------------------------------------------------------------
# Noise Patterns to Strip
# ---------------------------------------------------------------------------
NOISE_PATTERNS = [
    # University & Exam header boilerplate
    r"^Code No[:\s].*",
    r"^JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY.*",
    r"^B\.?\s*Tech\b.*Examinations.*",
    r"^B\.?\s*Tech\b.*Semester.*",
    r"^Time\s*:\s*\d+.*",
    r"^Max\.?\s*Marks\s*:\s*\d+.*",
    r"^Hall Ticket(?:\s*No)?[:\s].*",
    r"^\s*\(Common to\b.*?\)",
    r"^\s*\((?:Computer Science|Information Technology|Electronics|Mechanical|Civil|Electrical)[^)]*\)\s*$",

    # General instructions / Note blocks
    r"^Note\s*:.*",
    r"^i+\)\s*Part[\s\-]*[AB].*",
    r"^Part[\s\-]*[AB]\s+is\s+.*",
    r"^Part[\s\-]*[AB]\s+consists.*",
    r"^Each question carries.*",
    r"^Answer any\s+\w+\s+questions.*",
    r"^All questions carry.*",
    r"^carrying equal marks.*",
    r"^from each unit.*",
    r"^student should answer.*",

    # Watermarks and third-party portal tags
    r".*jntufastupdates\.com.*",
    r".*smartzworld\.com.*",
    r".*firstranker\.com.*",
    r".*manaresults\.co\.in.*",
    r".*jntuworld\.com.*",
    r"JNTUH USED",

    # Delimiters and isolated regulation/page stamps
    r"^-{3,}.*",
    r"^---+ooOoo---+.*",
    r"^---ooOoo---.*",
    r"^\s*R\d{2}\s*$",
    r"^\d{2}-\d{2}-\d{4}$",
    r"^Page\s+\d+\s+of\s+\d+",
    r"^\d+\s+of\s+\d+$",
]

NOISE_RE = re.compile("|".join(NOISE_PATTERNS), re.IGNORECASE)
MARKS_HEADER_RE = re.compile(r"^\(\d+\s*Marks\)$", re.IGNORECASE)
SCANNED_PLACEHOLDER = "[SCANNED IMAGE PDF - text extraction not available]"


def clean_file(txt: str) -> tuple[str, bool]:
    """
    Cleans raw question paper text.
    Returns (cleaned_text, is_scanned).
    """
    if SCANNED_PLACEHOLDER in txt:
        return "", True

    lines = txt.splitlines()
    cleaned_lines = []
    consecutive_empty = 0

    for line in lines:
        stripped = line.strip()

        # Handle empty lines: preserve at most 1 empty line between blocks
        if not stripped:
            if consecutive_empty == 0 and cleaned_lines:
                cleaned_lines.append("")
                consecutive_empty += 1
            continue

        # Strip inline trailing exam footers (e.g. ---oo0oo---, ---ooOoo---)
        stripped = re.sub(r"-{2,}\s*oo[o0]oo\s*-{2,}.*$", "", stripped, flags=re.IGNORECASE).strip()
        if not stripped:
            continue

        # Skip noise lines
        if NOISE_RE.search(stripped):
            continue

        # Skip standalone header marks like "(10 Marks)" or "(50 Marks)"
        if MARKS_HEADER_RE.match(stripped):
            continue

        cleaned_lines.append(stripped)
        consecutive_empty = 0

    # Strip leading/trailing empty lines
    cleaned_text = "\n".join(cleaned_lines).strip()
    return cleaned_text, False


def process_all(input_dir: str, output_dir: str, regulation_filter: str | None = None, dry_run: bool = False):
    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"[ERROR] Input directory does not exist: {input_path}")
        return

    # Find all question paper txt files (excluding syllabi)
    all_files = sorted(input_path.rglob("*.txt"))
    qp_files = [
        f for f in all_files
        if "syllabus" not in str(f).lower() and "Syllabus" not in str(f)
    ]

    if regulation_filter:
        qp_files = [f for f in qp_files if regulation_filter.lower() in str(f).lower()]

    print(f"Found {len(qp_files)} question paper files in {input_path}")

    stats = {
        "processed": 0,
        "scanned": 0,
        "empty": 0,
        "skipped": 0,
    }

    for src in qp_files:
        try:
            rel = src.relative_to(input_path)
            dest = output_path / rel

            raw = src.read_text(encoding="utf-8", errors="ignore")
            cleaned, is_scanned = clean_file(raw)

            if is_scanned:
                stats["scanned"] += 1
                if not dry_run:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(f"[SCANNED PDF - NEEDS OCR]\n{src.name}\n", encoding="utf-8")
                continue

            if not cleaned:
                stats["empty"] += 1
                continue

            stats["processed"] += 1

            if not dry_run:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(cleaned, encoding="utf-8")

        except Exception as e:
            print(f"[ERROR] Failed {src}: {e}")
            stats["skipped"] += 1

    print("\n" + "=" * 50)
    print(f"  Processed successfully : {stats['processed']}")
    print(f"  Scanned (image PDFs)    : {stats['scanned']}")
    print(f"  Empty output            : {stats['empty']}")
    print(f"  Skipped / Errors        : {stats['skipped']}")
    print("=" * 50)
    if not dry_run:
        print(f"Cleaned files written to: {output_path.resolve()}/")
    else:
        print("[DRY-RUN] No files written to disk.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean JNTUH question paper text files.")
    parser.add_argument("--input_dir", default="Data/Text_data/All_Reg_QP_Text_data", help="Input directory")
    parser.add_argument("--output_dir", default="data/cleaned_papers", help="Output directory")
    parser.add_argument("--regulation", default=None, help="Filter by regulation (e.g. R18, R22)")
    parser.add_argument("--dry_run", action="store_true", help="Perform a dry run without writing files")
    args = parser.parse_args()

    process_all(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        regulation_filter=args.regulation,
        dry_run=args.dry_run
    )
