# JNTUH Question Paper Predictor: Dataset Design & Field Specifications

## 1. Objective

Build a machine-learning and rubric-based question paper prediction engine for JNTUH B.Tech examinations targeting the **R22 Regulation**. Given a subject and its R22 syllabus, the engine predicts a valid exam paper by analyzing historical question frequency, recency, and cognitive depth across regulations (R13, R15, R16, R18, R22).

---

## 2. Key Design Decisions

### One Row = One Unique Question
Each row in the dataset represents a **unique question statement**. If the exact same question appeared in 2018 and 2022, it is stored as **one single row** with calendar year arrays: `part_a_years: [2018, 2022]` or `part_b_years: [2018, 2022]`.

### Universal Topic Tags Aligned with R22 Syllabus
Syllabus units change across regulations (e.g. Applets moved from Unit 4 to Unit 5). We do **not** hardcode unit numbers into the CSV. Instead, every question is tagged with its official `topic_tag` (e.g., `ABSTRACT_CLASSES`, `LAYOUT_MANAGERS`, `CUSTOM_EXCEPTIONS`) mapped from the R22 syllabus JSON config.

### Simplified 7-Column Schema (No topic_category)
`topic_category` has been intentionally excluded from the active ingestion schema to keep the pipeline lightweight, modular, and strictly aligned with unit syllabus topics.

### Atomic Splitting vs. Cohesive Composites
- **Independent sub-questions (`[5+5]` marks):** Must be split into separate rows so each has its own topic tag and pure Bloom level.
- **Short-note composites (`Explain: a) ... b) ... c) ... [5+5+5]`):** Must be kept glued as a single composite row to prevent naked fragments from polluting the dataset.

---

## 3. Dataset Fields (7 Standard Columns)

| # | Field | Type | Example | Purpose |
|---|---|---|---|---|
| 1 | `subject_name` | String | `"Object Oriented Programming through Java"` | Identifies which subject this question belongs to. Primary filter. |
| 2 | `raw_question_text` | Text | `"Explain abstract class with a suitable example."` | The actual question statement as it appeared in the exam. |
| 3 | `topic_tag` | String | `"ABSTRACT_CLASSES"` | Exact concept being tested. Mapped strictly to R22 syllabus JSON. |
| 4 | `bloom_level` | Enum | `"Understand"` | Cognitive depth: `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`. |
| 5 | `original_marks` | Integer | `5` | Standard marks (1–3 for Part A; 5 or 10 for Part B). |
| 6 | `part_a_years` | List[Integer] | `[2018, 2021]` | Calendar years this question appeared in Part A (short answer). |
| 7 | `part_b_years` | List[Integer] | `[2022, 2024]` | Calendar years this question appeared in Part B (long answer). |

---

## 4. Bloom's Taxonomy Cognitive Hierarchy

Cognitive levels are assigned based on the primary cognitive demand required from the student:

1. **`Apply`**: ONLY assigned for active programming or computational problem-solving tasks (e.g. *"Write a Java program"*, *"Develop a code snippet"*, *"Implement with a program"*).
2. **`Analyze`**: Comparisons, distinctions, differences, and structural contrasts (e.g. *"What are the differences between Thread and Process?"*, *"Differentiate between checked and unchecked exceptions"*).
3. **`Evaluate`**: Critical justification, suitability trade-offs, and proofs (e.g. *"Is Java a robust language? Justify your answer"*).
4. **`Remember`**: Direct recall, naming, definitions, and simple listings (e.g. *"Define bytecode"*, *"List the primitive types"*).
5. **`Understand`**: Conceptual explanations, mechanisms, and descriptions (e.g. *"Explain the lifecycle of a thread"*, *"How is an Exception handled in Java?"*).

---

## 5. Derived Features (Computed at Query Time)

These are computed dynamically by the prediction engine:

| Feature | How it's computed |
|---|---|
| `part_a_count` | `len(part_a_years)` |
| `part_b_count` | `len(part_b_years)` |
| `total_appearances` | `len(part_a_years) + len(part_b_years)` |
| `last_appeared` | `max(part_a_years + part_b_years)` |
| `recency_gap_years` | `current_year - last_appeared` |
| `anti_collision_flag` | `true` if question appeared in the immediate prior examination year |

---

## 6. How the Prediction Engine Uses This Dataset

```
Input: Subject name + Target R22 syllabus config (Units 1 to 5)

Step 1: Filter dataset by subject_name
Step 2: Filter by topic_tags present in the target R22 syllabus
Step 3: Part A Slots (10 questions x 1M):
        Pick top candidate short-answer questions (part_a_years != [])
        allocating exactly 2 questions per unit across Units 1 to 5.
Step 4: Part B Slots (5 questions x 10M, internal choice: 2 per unit):
        Pick top-ranked long-answer questions (part_b_years != [], 5M or 10M)
        ensuring coverage of all 5 units without immediate repeat collision.

Output: Complete valid predicted R22 examination paper
```
