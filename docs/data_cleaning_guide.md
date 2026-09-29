# Data Cleaning Guide & Teammate Manual

This guide outlines the standard operating procedure (SOP) for cleaning raw JNTUH question paper text files into machine-readable format for the question prediction pipeline.

---

## 1. Pipeline Overview

```
[Raw PDFs] (data/raw_pdfs/)
       │
       ▼  (Data/pdf_to_txt.py)
[Extracted Text] (Data/Text_data/All_Reg_QP_Text_data/ or data/extracted_text/)
       │
       ▼  (scripts/clean_papers.py)
[Cleaned Text] (data/cleaned_papers/)
       │
       ├──► (scripts/extract_images.py) ──► data/images/
       │
       ▼  (scripts/txt_to_csv.py)
[Master Dataset] (data/processed_dataset/questions_master.csv)
```

---

## 2. Directory & Naming Conventions

To keep all team members synchronized and avoid path conflicts across Windows, Mac, and Linux:

1. **Root casing:** Always use lowercase `data/` (avoid uppercase `Data/`).
2. **Regulation naming:** Use underscores rather than spaces (e.g., `R18_text` instead of `R18 text`).
3. **File naming convention:**
   ```
   [SubjectName]_[Year]_[Month]_[ExamType].txt
   ```
   * *Example:* `DataStructures_2022_Nov_Regular.txt`
   * *Allowed Exam Types:* `Regular`, `Supply`

---

## 3. How to Clean Question Paper Text

### 3.1 Quick Start
Run the cleaning script from the project root:
```bash
python3 scripts/clean_papers.py --input-dir Data/Text_data/All_Reg_QP_Text_data --output-dir data/cleaned_papers
```

### 3.2 Optional Flags
* `--input-dir <path>`: Source folder containing raw extracted `.txt` files.
* `--output-dir <path>`: Target folder for cleaned files (mirrors input folder structure).
* `--regulation <R13|R15|R16|R18|R22>`: Process only a specific regulation.
* `--dry-run`: View what files would be cleaned and inspect sample output without saving.
* `--verbose`: Print per-file stats (lines removed, questions detected).

---

## 4. What Gets Stripped vs. What Must Be Kept

### 4.1 Automatically Stripped (Boilerplate Noise)
| Category | Examples to Remove |
|---|---|
| **University Headers** | `JAWAHARLAL NEHRU TECHNOLOGICAL UNIVERSITY HYDERABAD` |
| **Exam Headers** | `B. Tech II Year I Semester Examinations, February - 2024` |
| **Codes & Registration** | `Code No: 183AK`, `Hall Ticket No: ...` |
| **Exam Logistics** | `Time: 3 Hours`, `Max. Marks: 75`, `(Common to CSE, IT, ...)` |
| **Standard Instructions** | `Note: This question paper contains two parts...`, `Part-A is a compulsory question...` |
| **Watermarks & Footers** | `---ooOoo---`, `jntufastupdates.com`, `Page 1 of 2` |

### 4.2 Must ALWAYS Be Preserved
* **Question numbers and letters:** `1.a)`, `2.`, `b)`, `OR`
* **Mark distribution brackets:** `[1]`, `[5+5]`, `[10]`, `[7+8]` (crucial for `txt_to_csv.py` to identify Part A vs Part B)
* **Tables and data blocks:** Die numbers, frequencies, coordinates, state transition tables
* **Figure & diagram references:** `shown below`, `following figure`, `circuit diagram` (needed by `extract_images.py`)
* **Paragraph breaks:** Blank lines between questions should be preserved to prevent sub-questions from running into each other.

---

## 5. Edge Cases & Manual Quality Checks

### Case 1: Scanned PDFs (Image-Only)
* If `pdf_to_txt.py` encountered a scanned document, the text contains:
  `[SCANNED IMAGE PDF - text extraction not available]`
* **Action:** Flag these files. Do not clean them. They must be processed via OCR (`tesseract` or OCR-space) or manually transcribed.

### Case 2: Multi-line Questions & Indented Sub-parts
* Long numerical or scenario questions often span 4-5 lines.
* Ensure question text lines are not prematurely truncated or split into separate items.

### Case 3: Math Symbols & Greek Letters
* UTF-8 characters like $\alpha, \beta, \sigma, \mu, \le, \ge, \pm$ must not be corrupted by `errors="ignore"`.
* Always open files using `encoding="utf-8"`.

### Case 4: Diagram / Circuit Questions
* When a question says *"Find the equivalent impedance of the circuit shown below"*, the text alone is incomplete.
* Run `python3 scripts/extract_images.py` after cleaning to crop and save the corresponding diagram to `data/images/`.

---

## 6. Verifying Cleaned Files

After running the cleaning script, verify sample output:
1. Check that the file starts directly with the first question (or subject name) without exam instructions.
2. Confirm mark brackets like `[1]` or `[5+5]` remain intact at the end of questions.
3. Check the question count: standard JNTUH papers have 10 sub-questions (Part A) + 10 questions (Part B) or 8 comprehensive questions.
