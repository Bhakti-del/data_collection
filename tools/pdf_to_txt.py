"""
PDF to TXT Converter
====================
Converts all PDF question papers to .txt files in-place
(saves each .txt alongside its .pdf in the same folder).

Requirements:
    pip install pypdf

Usage:
    python3 pdf_to_txt.py
    python3 pdf_to_txt.py --root /path/to/questions_P

What it does:
    - Recursively finds every .pdf under the root folder
    - Extracts text using pypdf
    - Saves a .txt file with the same name next to the .pdf
    - Skips files already converted (non-empty .txt already exists)
    - For scanned/image-only PDFs (no extractable text), writes a
      placeholder: [SCANNED IMAGE PDF - text extraction not available]
"""

import argparse
import pypdf
from pathlib import Path


def convert_pdf_to_txt(root: Path) -> None:
    pdf_files = sorted(root.rglob("*.pdf"))
    total = len(pdf_files)

    if total == 0:
        print(f"No PDF files found under: {root}")
        return

    print(f"Found {total} PDFs under: {root}\n")

    ok = skipped = empty = failed = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        txt_path = pdf_path.with_suffix(".txt")

        # Skip already converted
        if txt_path.exists() and txt_path.stat().st_size > 0:
            print(f"  [{i}/{total}] SKIP (exists): {pdf_path.parent.name}/{pdf_path.name}")
            skipped += 1
            continue

        try:
            reader = pypdf.PdfReader(str(pdf_path))
            text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"

            if text.strip():
                txt_path.write_text(text, encoding="utf-8")
                size = txt_path.stat().st_size
                print(f"  [{i}/{total}] ✓ {pdf_path.parent.name}/{pdf_path.name}  ({size:,} bytes)")
                ok += 1
            else:
                # Scanned image PDF — no selectable text
                txt_path.write_text(
                    f"[SCANNED IMAGE PDF - text extraction not available]\nFile: {pdf_path.name}\n",
                    encoding="utf-8"
                )
                print(f"  [{i}/{total}] ⚠  SCANNED: {pdf_path.parent.name}/{pdf_path.name}")
                empty += 1

        except Exception as e:
            print(f"  [{i}/{total}] ✗  FAILED: {pdf_path.parent.name}/{pdf_path.name} — {e}")
            failed += 1

    print(f"\n{'='*55}")
    print(f"  ✓ Converted : {ok}")
    print(f"  → Skipped   : {skipped}  (already done)")
    print(f"  ⚠ Scanned   : {empty}   (image-only PDFs)")
    print(f"  ✗ Failed    : {failed}")
    print(f"  Total .txt  : {ok + skipped + empty}")
    print(f"{'='*55}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert all PDFs in a folder tree to .txt files.")
    parser.add_argument(
        "--root",
        type=str,
        default="/Users/dareddytanusree/Desktop/WingsAI/questions_P",
        help="Root directory to search for PDFs (default: questions_P folder)"
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        print(f"Error: path does not exist: {root}")
        exit(1)

    convert_pdf_to_txt(root)
