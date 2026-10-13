# Question Paper Dataset Normalization & Validation Specification

## 1. Executive Summary

This document specifies the official normalization protocol and validation suite for the JNTUH Question Paper Predictor targeting the **R22 Regulation**. It standardizes:
- Multi-slot marks mapping (`8+7` historical patterns to R22 `5M` and `10M`).
- Handling questions that appeared in both 5M and 10M contexts across years.
- Multimodal semantic deduplication (Sentence Transformers + Perceptual Image Hashing).
- Subject name standardization.
- Automated pre- and post-normalization validation gates.

---

## 2. Marks Normalization & Slot Mapping Rules

Historical JNTUH regulations (R13, R15, R16) employed irregular marks schemes (`8+7=15`, `7+7=14`, `12M`, `16M`). Under R22, exam blueprints are strictly:
- **Part A**: 10 questions $\times$ 1 Mark or 2 Marks (mandatory short answer).
- **Part B**: 5 questions $\times$ 10 Marks (either single 10M or `5M + 5M` split sub-parts `a)` and `b)`).

### Rule 1: Sub-Questions (7M, 8M) $\rightarrow$ `PART_B_5M`
When historical questions appear as sub-parts `a)` or `b)` carrying 6M, 7M, or 8M:
- Set `normalized_marks = 5`.
- Set `slot_type = "PART_B_5M"`.
- *Rationale*: In R22, Part B sub-questions are strictly 5 Marks each.

### Rule 2: Standalone Full Questions (10M, 12M, 15M) $\rightarrow$ `PART_B_10M`
When historical questions appear as full, unsplit questions carrying 10M, 12M, or 15M:
- Set `normalized_marks = 10`.
- Set `slot_type = "PART_B_10M"`.

### Rule 3: Short Answers (1M, 2M, 3M) $\rightarrow$ `PART_A_1M` / `PART_A_2M`
When historical questions appear in Part A carrying 1M, 2M, or 3M:
- Set `normalized_marks = 1` (or 2).
- Set `slot_type = "PART_A_1M"`.

### Rule 4: The Dual-Slot Overlap Resolution (Appeared in BOTH 5M and 10M)
*Problem*: A fundamental question (e.g., *"Explain abstract classes with an example"*) appeared as a 10M standalone question in 2018, and as a 5M sub-question in 2021.
*Policy*:
1. Do **not** duplicate the question into two separate rows.
2. Maintain distinct calendar year arrays:
   - `part_a_years`: `[2017]` (years as short answer)
   - `part_b_years`: `[2018, 2021]` (years in Part B)
3. Set `normalized_marks = 5` and `slot_type = "PART_B_5M"` as primary default.
   - *Rationale*: Any 5M question can be paired into a `5M + 5M = 10M` Part B question in R22, ensuring complete flexibility for the blueprint assembler without overestimating question scope.

---

## 3. Multimodal Semantic Deduplication Protocol

A question candidate is deduplicated across years using a combined text-semantic and visual analysis:

```
[Candidate Question Pair (Q1, Q2) within same (Subject, Topic_Tag)]
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
        [Text-Only Questions]         [Image-Bearing Questions]
                 │                             │
    Cosine Similarity >= 0.88?                 ├─ Image pHash Distance <= 4?
                 │                             └─ Cosine Similarity >= 0.85?
        ┌────────┴────────┐                            │
        ▼                 ▼                    ┌───────┴───────┐
      [YES]              [NO]                  ▼               ▼
      Merge           Keep Both              [YES]            [NO]
     (Select           Distinct              Merge         Keep Both
    Canonical)                              (Combine        Distinct
                                             Years)
```

### Text Paraphrase Canonical Selection Rule:
When merging two semantically equivalent questions (e.g. *"What is an abstract class?"* vs. *"Explain abstract class with a suitable example."*):
1. Select the **more descriptive, grammatically complete statement** as the canonical `raw_question_text`.
2. Union the year arrays: `part_a_years = sorted(list(set(q1.part_a_years + q2.part_a_years)))`.

### Image Disambiguation Rule:
- If both questions share identical text prompts (*"Find node voltage V1 for the circuit shown below:"*):
  - If $\text{pHash}(img_1) - \text{pHash}(img_2) \le 4$: **SAME question** $\rightarrow$ Merge years.
  - If $\text{pHash}(img_1) - \text{pHash}(img_2) > 4$: **DIFFERENT questions** $\rightarrow$ Retain as two distinct candidate rows.

---

## 4. Subject Name Canonicalization Map

All subject names across datasets must normalize to official R22 titles:

| Historical / Variant Name | Canonical R22 Subject Name |
|---|---|
| `Java Programming` / `JAVA` / `OOP through Java` | `Object Oriented Programming through Java` |
| `Digital Logic Design` / `DLD` | `Digital Electronics` |
| `Computer Organization` / `CO` | `Computer Organization and Architecture` |
| `Design and Analysis Algorithms` / `DAA` | `Design and Analysis of Algorithms` |
| `English` / `English for Skill Enhancement` | `Professional Communication in English` |
| `Computer Oriented Statistical Methods` | `Probability and Statistics` |
| `Formal Languages and Automata Theory` / `FLAT` | `Formal Languages and Automata Theory` |
| `Web Services` / `SOA` | `Web Services and Service Oriented Architecture` |

---

## 5. Standardized 10-Column Master Schema

Normalized subject datasets must follow this exact schema:

```csv
subject_name,raw_question_text,image_path,topic_tag,bloom_level,original_marks,normalized_marks,slot_type,part_a_years,part_b_years
```

| Field | Type | Description |
|---|---|---|
| `subject_name` | String | Canonical R22 subject title. |
| `raw_question_text` | Text | Cleaned canonical statement without marks/headers. |
| `image_path` | String | Relative path to image (`"data/images/...png"`) or empty `""`. |
| `topic_tag` | String | Strict R22 syllabus enum tag. |
| `bloom_level` | Enum | `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`. |
| `original_marks` | Integer | Raw marks from source paper (e.g., 7, 8, 15). |
| `normalized_marks` | Integer | Target R22 slot marks (1, 2, 5, 10). |
| `slot_type` | Enum | `PART_A_1M`, `PART_A_2M`, `PART_B_5M`, `PART_B_10M`. |
| `part_a_years` | List[Int] | Calendar years question appeared in Part A. |
| `part_b_years` | List[Int] | Calendar years question appeared in Part B. |

---

## 6. Post-Normalization Validation Test Suite

Before certifying a normalized dataset, the following automated assertions must pass:

1. **Schema Completeness**: All 10 columns present and non-null (except `image_path` which may be empty).
2. **Year Set Integrity**: Every row must have at least one recorded year in `part_a_years` or `part_b_years`.
3. **No Duplicate Rows**: Zero exact string matches in `raw_question_text` within the same subject.
4. **Normalized Marks Validity**: `normalized_marks` must strictly be an element of `[1, 2, 5, 10]`.
5. **Image Path Verification**: If `image_path != ""`, `Path(image_path).is_file()` must be `True`.
6. **Syllabus Coverage**: 100% of `topic_tag` values must exist in the subject's R22 syllabus config.
