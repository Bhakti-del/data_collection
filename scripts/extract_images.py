"""
extract_images.py
For each cleaned text file containing image-bearing questions,
finds the matching PDF, locates the question on the page,
crops the image region between question text and next question,
saves to data/images/ and prints a mapping of question -> image filename.

Usage:
    python extract_images.py
"""

import re
import pymupdf
from pathlib import Path

CLEANED_BASE = Path("data/cleaned_papers")
PDF_BASE = Path("Data/Text_data/All_Reg_QP_PDF_data")
IMG_OUT = Path("data/images")
IMG_OUT.mkdir(exist_ok=True)

IMAGE_TRIGGERS = re.compile(
    r"shown below|following graph|following figure|following circuit|following diagram|following table",
    re.IGNORECASE
)

# Regex to find question number at start of a text block
Q_NUM = re.compile(r"^\s*(\d+)\.")


def find_pdf(txt_path: Path) -> Path | None:
    """Find the PDF sitting alongside the text file in the PDF folder tree."""
    # txt: data/cleaned_papers/R18 text/2nd Year/.../SUBJECT/file.txt
    # pdf: Data/Text_data/All_Reg_QP_PDF_data/R18 copy/2nd Year/.../SUBJECT/file.pdf
    # Strategy: search by subject folder name + filename stem
    stem = txt_path.stem
    subject = txt_path.parent.name
    matches = list(PDF_BASE.rglob(f"{stem}.pdf"))
    # Filter to same subject folder name
    matches = [p for p in matches if p.parent.name == subject]
    return matches[0] if matches else None


def get_q_blocks(page) -> list[tuple[int, float, float]]:
    """Return list of (q_num, y_start, y_end) for numbered questions on page."""
    blocks = page.get_text("blocks")
    q_blocks = []
    for b in blocks:
        y0, y1, text = b[1], b[3], b[4]
        m = Q_NUM.match(text)
        if m:
            q_blocks.append((int(m.group(1)), y0, y1))
    q_blocks.sort(key=lambda x: x[1])
    return q_blocks


def crop_image_for_question(page, q_num: int, q_blocks) -> pymupdf.Pixmap | None:
    """Crop the region between q_num text end and next question start."""
    current = next((b for b in q_blocks if b[0] == q_num), None)
    if not current:
        return None
    y_start = current[2]  # bottom of this question's text block

    # Next question's y_start
    later = [b for b in q_blocks if b[1] > current[1]]
    y_end = later[0][1] if later else page.rect.y1

    gap = y_end - y_start
    if gap < 20:  # no meaningful space for an image
        return None

    clip = pymupdf.Rect(page.rect.x0, y_start, page.rect.x1, y_end)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=clip)
    return pix


def process():
    # Find all text files with image-bearing questions
    txt_files = [f for f in CLEANED_BASE.rglob("*.txt")
                 if IMAGE_TRIGGERS.search(f.read_text(encoding="utf-8", errors="ignore"))]

    print(f"Found {len(txt_files)} files with image-bearing questions\n")

    mapping = []  # (txt_path, q_num, img_filename)

    for txt_path in txt_files:
        pdf_path = find_pdf(txt_path)
        if not pdf_path:
            print(f"[NO PDF] {txt_path.name}")
            continue

        text = txt_path.read_text(encoding="utf-8", errors="ignore")
        # Find which question numbers have image triggers
        img_q_nums = set()
        for line in text.splitlines():
            if IMAGE_TRIGGERS.search(line):
                m = re.match(r"^\s*(\d+)\.", line)
                if m:
                    img_q_nums.add(int(m.group(1)))

        if not img_q_nums:
            continue

        try:
            doc = pymupdf.open(str(pdf_path))
        except Exception as e:
            print(f"[PDF ERR] {pdf_path.name}: {e}")
            continue

        subject_slug = re.sub(r"[^A-Z0-9]", "_", txt_path.parent.name.upper())[:20]
        year_m = re.search(r"\d{4}", txt_path.stem)
        year = year_m.group() if year_m else txt_path.stem

        for page in doc:
            page_text = page.get_text()
            q_blocks = get_q_blocks(page)
            page_q_nums = {b[0] for b in q_blocks}

            for q_num in img_q_nums & page_q_nums:
                # Verify this page actually has the trigger phrase near this question
                if not IMAGE_TRIGGERS.search(page_text):
                    continue
                pix = crop_image_for_question(page, q_num, q_blocks)
                if pix is None:
                    continue
                img_name = f"{subject_slug}_{year}_q{q_num}.png"
                pix.save(str(IMG_OUT / img_name))
                mapping.append((str(txt_path), q_num, img_name))
                print(f"  Saved: {img_name}")

        doc.close()

    print(f"\nTotal images extracted: {len(mapping)}")
    return mapping


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    process()
