# JNTUH Question Paper Predictor: Dataset Design & Field Specifications

## 1. Objective

Build a question paper prediction engine for JNTUH exams using 15 years of past papers (R09, R13, R15, R16, R18, R22). Given a subject and its syllabus, the engine predicts a valid exam paper by analyzing historical question frequency and recency.

---

## 2. Key Design Decisions

### One row = one unique question
Each row in the dataset represents a **unique question**. If the same question appeared in 2018 and 2022, it is stored as **one row** with `part_a_years: [2018, 2022]` or `part_b_years: [2018, 2022]` — not two separate rows.

### Universal concept tags, not unit numbers
Syllabus units change across regulations (R16, R18, R22). A topic like *AVL Trees* was in Unit 2 under R16 but Unit 3 under R22. We do **not** store unit numbers. Instead, every question is tagged with a `topic_tag` (e.g., `AVL_TREES`). The prediction engine maps the new syllabus's units to topic tags at query time.

### Two-tier topic hierarchy
Topics are organized in two levels:
- `topic_category` — higher-level group (e.g., `SEARCH_TREES`)
- `topic_tag` — exact concept (e.g., `AVL_TREES`)

This is required to enforce paper quality: the two OR-choices in a Part B question must belong to **different** `topic_category` values, preventing a paper where both choices test the same broad area.

---

## 3. Dataset Fields

| # | Field | Type | Example | Purpose |
|---|---|---|---|---|
| 1 | `subject_name` | String | `"Data Structures"` | Identifies which subject this question belongs to. Primary filter. |
| 2 | `raw_question_text` | Text | `"Explain AVL tree rotations (LL, RR, LR, RL) with an example."` | The actual question text as it appeared in the exam. |
| 3 | `topic_tag` | String | `"AVL_TREES"` | Exact concept being tested. Used for frequency-based prediction. |
| 4 | `topic_category` | String | `"SEARCH_TREES"` | Higher-level group of the topic. Used to enforce variety in OR-choice pairs. |
| 5 | `bloom_level` | Enum | `"Apply"` | Cognitive depth: `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`. Used to balance paper difficulty. |
| 6 | `original_marks` | Integer | `7` | Standard marks for this question. Used to slot into Part A (≤3M) or Part B (≥5M). |
| 7 | `part_a_years` | List[Integer] | `[2018, 2021]` | Years this question appeared as a Part A (short answer) question. |
| 8 | `part_b_years` | List[Integer] | `[2019, 2022, 2023]` | Years this question appeared as a Part B (long answer) question. |

---

## 4. topic_category → topic_tag Hierarchy (Example: Data Structures)

```
SEARCH_TREES
  ├── AVL_TREES
  ├── B_TREES
  └── SPLAY_TREES

SORTING
  ├── QUICK_SORT
  ├── HEAP_SORT
  └── MERGE_SORT

GRAPHS
  ├── DIJKSTRA
  ├── KRUSKAL_MST
  └── BFS_DFS
```

Each `topic_tag` belongs to exactly one `topic_category`.

---

## 5. Derived Features (Computed at Query Time)

These are **not stored** in the dataset. The engine computes them on the fly:

| Feature | How it's computed |
|---|---|
| `part_a_count` | `len(part_a_years)` |
| `part_b_count` | `len(part_b_years)` |
| `last_appeared` | `max(part_a_years + part_b_years)` |
| `recency_gap_years` | `current_year - last_appeared` |
| `anti_collision_flag` | `true` if appeared in the immediately preceding exam year |

---

## 6. How the Engine Uses This Data

```
Input:  Subject name + Target syllabus (unit → topic_tags mapping)

Step 1: Filter dataset by subject_name
Step 2: Filter by topic_tags present in the target syllabus
Step 3: For Part A slots — pick high-frequency questions with original_marks ≤ 3
Step 4: For Part B slots — pick high-frequency questions with original_marks ≥ 5,
        ensuring each OR-pair has two questions from different topic_category values
Step 5: Apply recency penalty (deprioritize questions asked in the last 1–2 years)

Output: Complete predicted exam paper
```
