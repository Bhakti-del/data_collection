"""
clean_mfcs_dataset.py
======================
Cleans MFCS_Dataset.csv:
  1. Removes rows with garbled/unreadable math equations
  2. Splits questions with a) and b) into separate rows
  3. Removes trailing exam dates from question text

Output: data/MFCS_Dataset.csv (overwritten)
"""

import csv
import re
from pathlib import Path

INPUT  = Path("data/MFCS_Dataset.csv")
OUTPUT = Path("data/MFCS_Dataset.csv")

# ── Detect garbled text ───────────────────────────────────────────────────────
def is_garbled(text: str) -> bool:
    # Private-use unicode (Windows Symbol font artifacts like \uf0XX)
    if re.search(r'[\uf000-\uf8ff]', text):
        return True
    # More than 3 non-ASCII math symbols
    math_symbols = re.findall(r'[→←↔∀∃∧∨¬≤≥≠∈∉⊆⊂∪∩∑∏√∞±×÷]', text)
    if len(math_symbols) > 3:
        return True
    # Garbled OCR: sequences like "  a a a  " (isolated single letters)
    if re.search(r'(?<!\w)([a-z] ){4,}', text):
        return True
    return False

# ── Remove date/stamp artifacts ────────────────────────────────────────────────
def remove_date_artifacts(text: str) -> str:
    text = re.sub(r'\s*---?oo[Oo]oo---?\s*$', '', text)
    text = re.sub(r'\s*used paper.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*JNTUH USED.*$', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*[0-9]{2}-[0-9]{2}-[0-9]{2,4}\s*(AM|PM)?\s*$', '', text)
    return text.strip()

# ── Split a)...b) into two rows ────────────────────────────────────────────────
def split_ab(row: dict) -> list:
    text = row["raw_question_text"]

    # Match " b) " anywhere in the text (with at least 10 chars before and after)
    split_match = re.search(r'^(.{10,}?)\s+b\)\s+(.{10,})$', text, re.DOTALL | re.IGNORECASE)

    if not split_match:
        return [row]

    part_a_text = split_match.group(1).strip()
    part_b_text = split_match.group(2).strip()

    # Clean leading "a)" from part_a if present
    part_a_text = re.sub(r'^a\)\s*', '', part_a_text, flags=re.IGNORECASE).strip()

    marks = int(row["original_marks"])
    part_marks = max(1, marks // 2)

    base = {
        "subject_name": row["subject_name"],
        "topic_tag": row["topic_tag"],
        "bloom_level": row["bloom_level"],
        "part_a_years": row["part_a_years"],
        "part_b_years": row["part_b_years"],
    }

    return [
        {**base, "raw_question_text": part_a_text, "original_marks": part_marks},
        {**base, "raw_question_text": part_b_text, "original_marks": part_marks},
    ]

# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    with open(INPUT, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Input rows: {len(rows)}")

    cleaned = []
    removed_garbled = 0
    split_count = 0

    for row in rows:
        text = row["raw_question_text"]

        # Step 1: Remove garbled
        if is_garbled(text):
            removed_garbled += 1
            continue

        # Step 2: Remove date artifacts
        row["raw_question_text"] = remove_date_artifacts(row["raw_question_text"])

        # Step 3: Split a)+b)
        split_rows = split_ab(row)
        if len(split_rows) == 2:
            split_count += 1
        cleaned.extend(split_rows)

    print(f"Removed (garbled math): {removed_garbled}")
    print(f"Split into 2 (a+b questions): {split_count}")
    print(f"Output rows: {len(cleaned)}")

    fieldnames = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
                  "original_marks", "part_a_years", "part_b_years"]

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)

    print(f"\nSaved to: {OUTPUT}")

if __name__ == "__main__":
    main()
