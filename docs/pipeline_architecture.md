# Pipeline Architecture & Data Processing Specification

This document details the end-to-end ingestion, segmentation, normalization, and tagging pipeline for JNTUH examination question papers targeting the **R22 Regulation**.

---

## 1. High-Level Architecture

```
[Raw PDFs / Portal Dumps]
           │
           ▼ (tools/pdf_to_txt.py / poppler pdftotext)
[Raw Text Corpus]
           │
           ▼ (scripts/clean_papers.py)
[Cleaned & Regularized Text]
  • Strips headers, footers, hall-ticket grids
  • Repairs kerning glitches ("prog ram" -> "program")
  • Resolves Unicode en-dashes in sections ("PART – A")
           │
           ▼ (scripts/txt_to_csv.py)
[Atomic Segmentation & Extraction]
  • Splits independent sub-questions ("a) ... b) ...")
  • Keeps cohesive short-notes glued ("Explain: a) ... b) ... [5+5+5]")
  • Normalizes marks (R22 max Part B = 10M)
           │
           ▼ (Deduplication & Year Aggregation)
[Aggregated Questions]
  • Deduplicates identical questions across years
  • Builds calendar year arrays: part_a_years, part_b_years
           │
           ▼ (scripts/local_llm_tagger.py via Ollama qwen2.5:3b)
[LLM Semantic Classification & Audit]
  • Maps strictly to official R22 unit syllabus topics
  • Classifies Bloom cognitive level (Apply, Analyze, Evaluate, Remember, Understand)
           │
     ┌─────┴─────────────────────────────────┐
     ▼                                       ▼
[In-Syllabus Master Dataset]       [Legacy Archive Dataset]
(data/Java_Dataset.csv)            (data/java_unmatched_archive.csv)
 • 100% R22 topics only             • Out-of-syllabus legacy topics
 • Used for R22 Prediction models   • JDBC, Servlets, Collections Framework
```

---

## 2. Dataset Schema (7 Standard Columns)

Every subject dataset is exported as a clean CSV with the following 7 columns:

| # | Column Name | Type | Description | Example |
|---|---|---|---|---|
| 1 | `subject_name` | String | Full name of the subject matching R22 syllabus | `"Object Oriented Programming through Java"` |
| 2 | `raw_question_text` | Text | Exact cleaned question statement without marks bracket | `"Explain abstract class with a suitable example."` |
| 3 | `topic_tag` | String | Canonical syllabus topic enum from R22 syllabus JSON | `"ABSTRACT_CLASSES"` |
| 4 | `bloom_level` | Enum | Cognitive complexity tier: `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate` | `"Understand"` |
| 5 | `original_marks` | Integer | Normalized marks slot (1–3 for Part A; 5 or 10 for Part B) | `5` |
| 6 | `part_a_years` | List[Int] | Calendar years question appeared as a short-answer (Part A) | `[2018, 2021]` |
| 7 | `part_b_years` | List[Int] | Calendar years question appeared as a long-answer (Part B) | `[2022, 2024]` |

> [!NOTE]
> `topic_category` is intentionally excluded at this ingestion stage to keep the schema compact and strictly aligned with syllabus units. Regular vs. supplementary distinctions are normalized into calendar year arrays.

---

## 3. Cognitive Level (Bloom's Taxonomy) Rules

To eliminate subjective labeling and heuristic errors:

- **`Apply`**: ONLY assigned when the student is explicitly required to write code, develop an application, construct a program, or solve a computational problem.
  - *Keywords:* `"Write a Java program"`, `"Develop a code snippet"`, `"Implement with a program"`, `"Write an applet"`.
  - *Heuristic Guard:* Conceptual questions containing the word "program" (e.g. *"Describe the structure of a typical Java program"*) are NOT `Apply`; they are `Understand`.
- **`Analyze`**: Comparison, contrast, structural differentiation, or breakdown of pros and cons.
  - *Keywords:* `"What are the differences between X and Y"`, `"Differentiate X and Y"`, `"Compare and contrast"`.
- **`Evaluate`**: Critical defense, trade-off assessment, or justification.
  - *Keywords:* `"Is Java robust? Justify your answer"`, `"Evaluate the suitability of"`, `"Critique"`.
- **`Remember`**: Pure recall, definitions, naming, or stating items without explanation.
  - *Keywords:* `"Define X"`, `"What is X"`, `"List the types of X"`, `"State the properties"`.
- **`Understand`**: Explanations, mechanisms, lifecycle descriptions, or architectural concepts.
  - *Keywords:* `"Explain X"`, `"Describe the lifecycle of X"`, `"Discuss the architecture"`.

---

## 4. Question Segmentation & Splitting Rules

1. **Independent Sub-Questions:**
   - When an exam paper lists:
     ```
     2.a) What is dynamic method dispatch? [5M]
       b) Explain package creation with an example. [5M]
     ```
     These are **independent concepts** and MUST be split into **two distinct rows** (5M each) with individual topic tags.
2. **Cohesive Short-Note Composites:**
   - When an exam paper lists:
     ```
     8. Explain the following with examples:
        a) this keyword
        b) garbage collection
        c) constructors                   [5+5+5]
     ```
     These sub-items MUST be **kept glued together as a single composite row** (10M / 15M). Splitting them produces naked fragments like `"this keyword."` that lack full question context.
3. **Decimal Numbering Guard:**
   - Regex splitters must use negative lookahead `([1-9]|1[0-5])\.(?!\d)\s*` to prevent splitting on decimal values (e.g., `1.5625` or `0.050 ohm`).
4. **Unicode En-Dash Guard:**
   - JNTUH question papers frequently use Unicode en-dashes (`PART – A`, `\u2013`), not standard ASCII hyphens. Regexes must match `[\-\u2013\u2014]`.

---

## 5. R22 Syllabus Filtering & Legacy Archiving

- Any historical question testing content removed from the R22 curriculum (e.g. JDBC, Servlets, or legacy Collections like Vector/HashTable in Java) is decoupled from the master dataset.
- These questions are safely stored in `<subject>_unmatched_archive.csv` to ensure 0 out-of-syllabus data pollutes R22 exam paper predictors.
