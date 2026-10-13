# Normalization Pre-Steps Specification & Data Readiness Audit

## 1. Overview & Objective

Before questions can undergo **normalization** (candidate deduplication, calendar year aggregation, marks scaling to R22 schema, and cross-regulation merging), all raw data extracted from question paper PDFs must pass strict **pre-normalization verification gates**.

This document outlines the mandatory validation criteria, automated integrity checks, and edge-case handling rules across **theoretical**, **image-bearing**, and **mathematical** questions to guarantee 0% data corruption before running deduplication.

---

## 2. The Ingestion-to-Normalization Lifecycle

```
[Raw PDFs (Digital & Scans)]
            │
            ▼
[Text Extraction & Image Cropping]
  • Digital: PyMuPDF high-fidelity text
  • Scans: Preprocessed Tesseract OCR
  • Diagrams & Equations: Cropped to images/
            │
            ▼
[Cleaning & Atomic Segmentation]
  • Noise & watermark stripping
  • Atomic sub-question splitting ([5+5])
  • Cohesive composite preservation ([5+5+5])
            │
            ▼
[Topic Tagging & Bloom Audit]
  • Canonical R22 syllabus enum tagging
  • Bloom taxonomy classification
  • Legacy/Out-of-syllabus isolation
            │
            ▼
   ┌────────────────────────────────────────────────────────┐
   │         >>> NORMALIZATION PRE-STEPS AUDIT <<<          │
   │  (Checkpoints 1–5: Verify Integrity & Readiness)       │
   └────────────────────────────────────────────────────────┘
            │
            ▼ (Passed all gates)
[Normalization & Candidate Deduplication Pipeline]
```

---

## 3. Mandatory Pre-Normalization Audit Checkpoints

Every subject dataset (e.g. `temp_data/<Subject>_Dataset.csv`) must satisfy all five gates before entering the normalization phase.

### Gate 1: No Headless or Truncated Questions
* **The Defect**: Questions that end abruptly with introductory phrases because the actual problem statement, equation, or table was lost during extraction.
  * *Examples*:
    * `"Solve the following:"`
    * `"Find the equivalent resistance across terminals AB for the network:"`
    * `"Evaluate the following integral:"`
    * `"Determine the truth table for:"`
* **Automated Audit Rule**:
  Flag any question that matches the regex:
  ```regex
  r"(?i)\b(following|below|given|evaluate|calculate|find|prove\s+that|solve)\s*[:\-\s]*$"
  ```
* **Resolution**:
  - If an image exists, verify that `image_path` is populated.
  - If the question was text-based, re-extract the missing trailing block from the cleaned paper before proceeding.
  - If unrecoverable, quarantine the row in `quarantine_unresolved.csv`.

---

### Gate 2: Image Referential Integrity & Visual Validity
* **The Defect**: CSV rows containing dead image paths, 0-byte corrupted image crops, or blank white crops.
* **Automated Audit Rule**:
  For every row where `image_path` is non-empty:
  1. **Path Existence**: File must exist at `Path(image_path)`.
  2. **File Size**: Size must be $> 2.0\text{ KB}$ (crops $< 2\text{ KB}$ are usually blank margins or noise borders).
  3. **Visual Variance**: Standard deviation of pixel intensities must be $> 10$ (detects all-white or all-black blank crops).
* **Resolution**:
  Re-crop the bounding box using PyMuPDF between question coordinate $y_{start}$ and next question coordinate $y_{end}$.

---

### Gate 3: Sub-Question Splitting Sanity (Atomic vs. Composite)
* **The Defect**:
  - *Over-splitting*: Splitting cohesive short-note questions into naked fragments (e.g., splitting *"Write short notes on: a) Encapsulation b) Abstraction"* into *"b) Abstraction"*, which loses question context and marks).
  - *Under-splitting*: Keeping independent questions glued together (e.g., keeping *"a) What is dynamic binding? [5M] b) Explain packages [5M]"* as one 10M row), making topic tagging ambiguous.
* **Automated Audit Rule**:
  - Independent sub-questions (`a)` and `b)` testing distinct concepts) must each have a separate row and independent `topic_tag`.
  - Composite short notes starting with `"Write short notes on:"`, `"Explain the following:"`, or `"Discuss any three of the following:"` must remain **glued as a single composite row**.
  - No row text may begin with naked bullet markers like `^b\)\s+` or `^ii\)\s+` unless accompanied by its parent prompt.

---

### Gate 4: R22 Syllabus Topic Tag Compliance
* **The Defect**: Questions tagged with invalid enum values, unit mismatches, or obsolete curriculum concepts.
* **Automated Audit Rule**:
  - Cross-check `topic_tag` against the canonical R22 syllabus JSON config for that subject.
  - Every valid row must belong to Units 1 through 5 of the R22 curriculum.
* **Legacy Decoupling Rule**:
  - Historical questions testing obsolete topics removed in R22 (e.g., Servlets/Applets in Java, 8086 Assembly in COA, Phase Rule in Chemistry) must **not** be forced into R22 tags.
  - Route them directly to `data/<subject>_unmatched_archive.csv` before normalization runs.

---

### Gate 5: Text Cleanliness & Noise Elimination
* **The Defect**: Header leaks, hall-ticket grids, regulation codes, or download portal watermarks remaining inside `raw_question_text`.
* **Automated Audit Rule**:
  Ensure 0 rows contain:
  - University headers: `JAWAHARLAL NEHRU`, `B.Tech`, `Code No:`
  - Watermarks: `jntufastupdates`, `smartzworld`, `manaresults`, `firstranker`, `JNTUH USED`
  - Exam metadata: `Max Marks`, `Time: 3 Hours`, `PART - A`, `PART - B`
  - Trailing marks tags: `[5M]`, `[5+5]`, `(10 Marks)`, `[15 Marks]`

---

## 4. Subject Modality Audit Rules (Pre-Normalization)

Before running subject-wide normalization, classify each question row into its respective modality handling stream:

| Question Modality | Indicators / Features | Pre-Normalization Action |
|---|---|---|
| **Theoretical** | Pure text, explanation verbs (*"Explain"*, *"Define"*, *"Describe"*, *"Compare"*) | Clean text, verify Bloom level, confirm topic tag. |
| **Image / Circuit / Graph** | References visual artifacts (*"shown below"*, *"circuit"*, *"graph"*, *"waveform"*); non-empty `image_path` | Validate image crop file, compute visual pHash for upcoming deduplication. |
| **Mathematical / Equations** | Contains symbols ($\int, \sum, \land, \lor, \rightarrow$), matrices, fractions, recurrences | Preserve Unicode/LaTeX; if complex/scan, ensure snippet is preserved or cropped (see [handling_equations.md](file:///home/slesha/wings-AI/question-paper-predictor/docs/handling_equations.md)). |
| **Code / Programming** | Java, C, Python syntax, keywords (`class`, `public static void`, `struct`) | Protect indentation and syntax from noise strippers; ensure not mangled into single unbroken lines. |

---

## 5. Automated Pre-Steps Audit Script

A lightweight validation runner should be executed before any normalization script:

```bash
python scripts/audit_pre_normalization.py --subject "Object Oriented Programming through Java" --input temp_data/Java_Dataset.csv
```

### Success Criteria:
```text
[CHECK 1] Headless Questions Check: 0 found (PASSED)
[CHECK 2] Image Integrity Check: 18/18 valid on disk (PASSED)
[CHECK 3] Atomic Segmentation Check: No orphan fragments (PASSED)
[CHECK 4] R22 Syllabus Tag Alignment: 100% compliant with R22_Java_Syllabus.json (PASSED)
[CHECK 5] Noise & Watermark Leakage: 0 noise patterns detected (PASSED)
============================================================
STATUS: DATASET IS CERTIFIED FOR NORMALIZATION & DEDUPLICATION
============================================================
```
