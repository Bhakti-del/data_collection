# JNTUH R22 Marks Normalization Specification

## 1. Why Normalization Is Required

Across historical JNTUH regulations (R13, R15, R16, R18), marks schemes varied significantly:
- **R13 / R15:** Comprehensive 15-mark and 8-mark questions, with 2-mark and 3-mark Part A questions.
- **R16 / R18:** 7-mark and 8-mark questions (`[7+8] = 15M` or `[5+5] = 10M`).
- **R22 Regulation:** The official structure strictly standardizes to:
  - **Part A:** 10 questions $\times$ **1 Mark** = 10 Marks total.
  - **Part B:** 5 questions $\times$ **10 Marks** = 50 Marks total. Each 10M slot is composed of either:
    - **Single Comprehensive Question:** 10 Marks.
    - **Two Sub-Questions ($a + b$):** 5 Marks + 5 Marks.

---

## 2. Deterministic Mapping Rules

Every row in `temp_data/Java_Dataset.csv` is mapped deterministically into R22 slots:

| Historical Condition | Assigned `normalized_marks` | Assigned `slot_type` | Rationale |
|---|---|---|---|
| Question appeared in `part_a_years` (or original marks $\le 3$) | **1** | `PART_A_1M` | Standard short definition or conceptual recall for Part A slots. |
| Question appeared in `part_b_years` and original marks $\in [4, 5, 6, 7, 8]$ | **5** | `PART_B_5M` | Atomic sub-question. Two of these pair to fill one 10M choice slot. |
| Question appeared in `part_b_years` and original marks $\ge 10$ | **10** | `PART_B_10M` | Comprehensive standalone question. Fills an entire 10M choice slot directly. |

---

## 3. Results for `Java_Dataset.csv`

Running the normalization pipeline on the 454 Java questions yields:

```text
Total Questions: 454
├── PART_A_1M   : 118 questions (1 Mark each)
├── PART_B_5M   : 292 questions (5 Marks each)
└── PART_B_10M  :  44 questions (10 Marks each)
```

### Slot Assembly Combinations for Part B:
For any unit's Choice slot (10 Marks):
- **Option 1 (Direct 10M):** 1 question of type `PART_B_10M`.
- **Option 2 (Sub-parts 5M + 5M):** 2 questions of type `PART_B_5M` from compatible sub-topics.
