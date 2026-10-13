"""
extract_images.py
-----------------
Automated diagram and figure extraction from JNTUH question paper PDFs.

Features:
  - Robust text-to-PDF matching resilient to whitespace, line breaks, and punctuation.
  - Automatically maps cleaned text questions to original source PDFs.
  - Crops diagram regions at 2x resolution (144 DPI) without cutting off labels.
  - Exports a structured CSV with `has_diagram`, `image_path`, and `figure_label` fields.

Usage:
    # Run on a single paper:
    python scripts/extract_images.py --paper "March-2021" --subject "BASIC ELECTRICAL ENGINEERING"

    # Run on a specific subject:
    python scripts/extract_images.py --subject "BASIC ELECTRICAL ENGINEERING"

    # Run across all papers in the dataset:
    python scripts/extract_images.py --all
"""

from __future__ import annotations

import os
import re
import csv
import argparse
from pathlib import Path

try:
    import pymupdf
except ImportError:
    raise ImportError("PyMuPDF is required. Install it using: pip install pymupdf")


# -- PATH RESOLUTION ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Check for primary or fallback text data directories
TEXT_DIRS = [
    PROJECT_ROOT / "Datafiles" / "Text_data" / "All_Reg_QP_Text_data",
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data",
    PROJECT_ROOT / "temp_data" / "cleaned_papers",
]
TEXT_BASE = next((d for d in TEXT_DIRS if d.exists()), None)

# Check for primary or fallback PDF directories
PDF_DIRS = [
    PROJECT_ROOT / "Datafiles" / "Text_data" / "All_Reg_QP_PDF_data",
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_PDF_data",
]
PDF_BASE = next((d for d in PDF_DIRS if d.exists()), None)

DEFAULT_IMG_OUT = PROJECT_ROOT / "data" / "images"
DEFAULT_CSV_OUT = PROJECT_ROOT / "data" / "questions_with_images.csv"


# -- PATTERNS ----------------------------------------------------------------

IMAGE_TRIGGERS = re.compile(
    r"(?:shown\s+in\s+(?:the\s+)?(?:fig(?:ure)?|circuit|graph|diagram|network)|"
    r"shown\s+below|"
    r"given\s+in\s+(?:the\s+)?(?:fig(?:ure)?|circuit|graph|diagram|network)|"
    r"given\s+circuit|given\s+graph|given\s+network|"
    r"refer\s+(?:to\s+)?(?:the\s+)?(?:fig(?:ure)?|diagram)|"
    r"see\s+fig(?:ure)?|"
    r"for\s+the\s+circuit\s+shown|"
    r"following\s+(?:circuit|graph|diagram|figure|network)|"
    r"\bfig(?:ure)?\.?\s*[:\s]?\s*\d+|"
    r"from\s+fig(?:ure)?\.?\s*\d+)",
    re.IGNORECASE
)

FIGURE_LABEL_PATTERN = re.compile(
    r"(Figure\s*[:\.]?\s*\d+)",
    re.IGNORECASE
)


# -- HELPERS -----------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Removes non-alphanumeric characters and standardizes spaces for robust matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def find_pdf_for_txt(txt_path: Path) -> Path | None:
    """Finds the corresponding PDF for a text file."""
    if not PDF_BASE or not PDF_BASE.exists():
        return None

    try:
        rel_path = txt_path.relative_to(TEXT_BASE)
        direct_match = PDF_BASE / rel_path.with_suffix(".pdf")
        if direct_match.exists():
            return direct_match
    except Exception:
        pass

    stem = txt_path.stem
    subject = txt_path.parent.name
    matches = list(PDF_BASE.rglob(f"{stem}.pdf"))
    if not matches:
        return None

    same_subj = [p for p in matches if p.parent.name.lower().replace("_", " ") == subject.lower().replace("_", " ")]
    return same_subj[0] if same_subj else matches[0]


def parse_questions_from_text(text: str) -> list[dict]:
    """Splits question paper text into individual questions with their metadata."""
    lines = text.splitlines()
    questions = []
    current_q_num = None
    current_text = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if any(h in stripped.lower() for h in [
            "hall ticket", "roll no", "jawaharlal nehru technological",
            "time: 3 hours", "max marks", "max. marks", "note:",
            "answer any five", "part-a", "part-b", "---oo"
        ]):
            continue

        m = re.match(r"^\s*(\d+)[\.\)]\s*(?:([a-z])\))?", stripped, re.IGNORECASE)
        m_sub = re.match(r"^\s*([a-z])\)\s+", stripped, re.IGNORECASE)

        if m:
            if current_text and current_q_num:
                questions.append({
                    "q_no": current_q_num,
                    "text": " ".join(current_text)
                })
            q_main = m.group(1)
            q_sub = f".{m.group(2)}" if m.group(2) else ""
            current_q_num = f"{q_main}{q_sub}"
            current_text = [stripped]
        elif m_sub and current_q_num:
            if current_text:
                questions.append({
                    "q_no": current_q_num,
                    "text": " ".join(current_text)
                })
            main_digit = current_q_num.split(".")[0]
            current_q_num = f"{main_digit}.{m_sub.group(1)}"
            current_text = [stripped]
        else:
            if current_text:
                current_text.append(stripped)

    if current_text and current_q_num:
        questions.append({
            "q_no": current_q_num,
            "text": " ".join(current_text)
        })

    return questions


def extract_marks(q_text: str) -> int | None:
    """Extracts marks from brackets at the end of a question, e.g. [15] or [7+8]."""
    m = re.search(r"\[(\d+)(?:\+(\d+))?\]\s*$", q_text)
    if m:
        if m.group(2):
            return int(m.group(1)) + int(m.group(2))
        return int(m.group(1))
    return None


def crop_diagram_for_question(page, q_text: str, zoom: float = 2.0) -> tuple[pymupdf.Pixmap | None, str]:
    """Crops the diagram region following a question block on a page."""
    # Exclude vertical watermarks and stamps (width < 40 or height > 300 with narrow width)
    raw_blocks = page.get_text("blocks")
    blocks = [b for b in raw_blocks if b[6] == 0 and (b[2] - b[0] > 45)]
    blocks.sort(key=lambda b: b[1])  # Sort by vertical top position

    # Normalize words from the question text for fuzzy matching
    q_words = [w for w in re.findall(r"[a-zA-Z0-9]+", q_text.lower()) if len(w) > 3]
    if not q_words:
        return None, ""

    match_idx = None
    for idx, b in enumerate(blocks):
        b_clean = re.sub(r"\s+", " ", b[4]).lower()
        # Count keyword overlap
        overlap = sum(1 for w in q_words[:6] if w in b_clean)
        if overlap >= 2:
            match_idx = idx
            break

    if match_idx is None:
        return None, ""

    matched_b = blocks[match_idx]
    y_start = matched_b[3] + 2  # Bottom of question block

    # Determine diagram bottom boundary
    fig_label = ""
    y_end = page.rect.y1 - 40

    if match_idx + 1 < len(blocks):
        next_b = blocks[match_idx + 1]
        next_text = next_b[4]

        # Check if next block has a Figure label
        m_fig = FIGURE_LABEL_PATTERN.search(next_text)
        if m_fig:
            fig_label = m_fig.group(1)
            # If the block starts with the Figure label, crop up to that label's bottom
            y_end = next_b[1] + 25
            if next_b[3] - next_b[1] < 40:  # Single-line figure label
                y_end = next_b[3] + 2
        else:
            y_end = next_b[1] - 2

    # Verify gap
    gap = y_end - y_start
    if gap < 25:
        return None, ""

    # Crop rectangle
    x0 = max(page.rect.x0 + 40, 40)
    x1 = min(page.rect.x1 - 40, page.rect.width - 40)
    clip_rect = pymupdf.Rect(x0, y_start, x1, y_end)

    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=clip_rect)
    return pix, fig_label


# -- MAIN EXTRACTION ---------------------------------------------------------

def process_paper(txt_path: Path, img_out_dir: Path) -> list[dict]:
    """Processes a single paper: crops all diagrams and returns structured question rows."""
    pdf_path = find_pdf_for_txt(txt_path)
    if not pdf_path or not pdf_path.exists():
        print(f"[!] No matching PDF found for: {txt_path.name}")
        return []

    content = txt_path.read_text(encoding="utf-8", errors="ignore")
    questions = parse_questions_from_text(content)
    subject = txt_path.parent.name
    subject_slug = re.sub(r"[^A-Za-z0-9]", "_", subject.upper())[:15]
    stem = txt_path.stem

    rows = []
    doc = pymupdf.open(str(pdf_path))

    for idx, q in enumerate(questions):
        q_no = q["q_no"]
        q_text = q["text"]
        has_diagram = bool(IMAGE_TRIGGERS.search(q_text))
        img_filename = ""
        fig_label = ""

        if has_diagram:
            q_norm = normalize_text(q_text)
            target_page = None

            for page in doc:
                page_norm = normalize_text(page.get_text())
                # Match against question text
                if q_norm[:30] in page_norm or any(w in page_norm for w in re.findall(r"[a-z0-9]+", q_text.lower())[:5] if len(w) > 4):
                    target_page = page
                    break

            if target_page:
                pix, fig_label = crop_diagram_for_question(target_page, q_text)
                if pix:
                    clean_q_tag = q_no.replace(".", "_")
                    img_filename = f"{subject_slug}_{stem}_Q{clean_q_tag}.png"
                    img_path = img_out_dir / img_filename
                    pix.save(str(img_path))
                    print(f"  [+] Cropped Diagram for Q{q_no}: {img_filename} {f'({fig_label})' if fig_label else ''}")

        marks = extract_marks(q_text)

        rows.append({
            "subject_name": subject,
            "question_no": q_no,
            "raw_question_text": q_text,
            "original_marks": marks if marks else "",
            "has_diagram": bool(img_filename),
            "image_path": str(Path("data/images") / img_filename) if img_filename else "",
            "figure_label": fig_label,
            "source_pdf": pdf_path.name
        })

    doc.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description="Extract diagrams and generate structured dataset with image paths.")
    parser.add_argument("--paper", type=str, help="Specific paper stem to process (e.g., 'March-2021')")
    parser.add_argument("--subject", type=str, help="Filter by subject folder name")
    parser.add_argument("--all", action="store_true", help="Process all available papers")
    parser.add_argument("--img_out", type=Path, default=DEFAULT_IMG_OUT, help="Directory to save cropped images")
    parser.add_argument("--csv_out", type=Path, default=DEFAULT_CSV_OUT, help="Path for output CSV")

    args = parser.parse_args()

    if not TEXT_BASE or not TEXT_BASE.exists():
        print(f"[ERROR] Text dataset base directory not found.")
        return

    args.img_out.mkdir(parents=True, exist_ok=True)
    args.csv_out.parent.mkdir(parents=True, exist_ok=True)

    # Collect target files
    txt_files = list(TEXT_BASE.rglob("*.txt"))
    if args.subject:
        txt_files = [f for f in txt_files if args.subject.lower() in f.parent.name.lower()]
    if args.paper:
        txt_files = [f for f in txt_files if args.paper.lower() in f.stem.lower()]

    if not txt_files:
        print("[!] No matching text files found with current criteria.")
        return

    print(f"\nProcessing {len(txt_files)} question paper(s)...")
    all_rows = []

    for f in txt_files:
        print(f"\nScanning: {f.parent.name} / {f.name}")
        rows = process_paper(f, args.img_out)
        all_rows.extend(rows)

    if all_rows:
        fieldnames = [
            "subject_name", "question_no", "raw_question_text", "original_marks",
            "has_diagram", "image_path", "figure_label", "source_pdf"
        ]
        with open(args.csv_out, "w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_rows)

        diagram_count = sum(1 for r in all_rows if r["has_diagram"])
        print(f"\n{'='*55}")
        print(f"Total Questions Processed : {len(all_rows)}")
        print(f"Diagrams Extracted        : {diagram_count}")
        print(f"Output Images Directory   : {args.img_out}")
        print(f"Output Dataset CSV        : {args.csv_out}")
        print(f"{'='*55}\n")


if __name__ == "__main__":
    main()
