# How Embeddings Work in This Project

## The Big Picture

The pipeline has 3 steps:

```
Step 1 — parser.py       →  extracts raw questions from .txt files
Step 2 — tagger.py       →  assigns topic tags using embeddings
Step 3 — deduplicator.py →  merges similar questions using embeddings
```

Embeddings are used in **Step 2 and Step 3**. They are not used to generate any content.

---

## What is an Embedding?

An embedding is a list of numbers (a vector) that represents the **meaning** of a sentence.

Example:
```
"What is deadlock?"          → [0.12, -0.45, 0.78, 0.33, ...]  (384 numbers)
"Define deadlock condition."  → [0.11, -0.43, 0.80, 0.31, ...]  (384 numbers)
"What is process scheduling?" → [0.55,  0.22, -0.10, 0.60, ...]  (384 numbers)
```

Sentences that mean **similar things** produce vectors that point in nearly the same direction.
Sentences about **different things** produce vectors that point in different directions.

The model used here is **`all-MiniLM-L6-v2`** from HuggingFace — a small, fast, and accurate sentence transformer model.

---

## Step 2 — Tagging (tagger.py)

**Goal:** Given a question like `"Explain the dining philosophers problem"`, automatically assign the correct topic tag (e.g., `DEADLOCK`).

### How it works

**1. Build topic descriptions**

The vocabulary file (`data/topic_tag_vocabulary.csv`) has one row per topic with a plain-English description:

| topic_tag | description |
|---|---|
| DEADLOCK | Deadlock conditions, detection, prevention, avoidance, banker's algorithm |
| CPU_SCHEDULING | CPU scheduling algorithms: FCFS, SJF, Round Robin, Priority |
| ER_MODEL | Entity-relationship model, ER diagrams, entities, attributes, relationships |
| ... | ... |

**2. Pre-compute topic embeddings**

Each description is converted to a vector and saved to `data/topic_embeddings.npy`.
This is done once and reused on future runs.

```
"Deadlock conditions, detection, prevention..." → [0.21, -0.60, 0.44, ...]
"CPU scheduling algorithms: FCFS, SJF..."       → [0.55,  0.30, -0.12, ...]
```

**3. Embed the incoming question**

```
"Explain the dining philosophers problem" → [0.19, -0.58, 0.47, ...]
```

**4. Measure similarity (Cosine Similarity)**

Cosine similarity measures the angle between two vectors.
- Score = **1.0** → identical meaning
- Score = **0.8+** → very similar
- Score = **0.3-** → unrelated

The question vector is compared against all topic vectors. The topic with the **highest score** wins.

```
Question vs DEADLOCK        → 0.81  ✓  ← WINNER
Question vs CPU_SCHEDULING  → 0.34
Question vs ER_MODEL        → 0.12
...
```

**5. Confidence check**

- If the best score is **below 0.35** → low confidence, sent to `review_queue.csv` for human review.
- If the **top-2 scores are very close** (within 0.07 margin) → ambiguous, also sent for review.
- Otherwise → auto-tagged and written to `questions_tagged.csv`.

**6. Unit filtering**

Before comparing, the topic list is filtered to only include topics from the same subject and unit number as the question. This prevents a DBMS question from accidentally matching an OS topic.

---

## Step 3 — Deduplication (deduplicator.py)

**Goal:** The same question appears across multiple years with slight wording differences. Merge them into one row that tracks all the years it appeared.

Example:
```
2018: "What is deadlock? State the four necessary conditions."
2020: "Define deadlock. What are the necessary conditions for deadlock?"
2022: "State and explain the four conditions required for deadlock."
```
These are the same question. They should become one row.

### How it works

**1. Embed all questions for a subject**

All question texts are passed through the same `all-MiniLM-L6-v2` model to get their vectors.

**2. Build a similarity matrix**

Every question is compared against every other question. The result is a grid of similarity scores.

```
         Q1    Q2    Q3
Q1      1.00  0.88  0.21
Q2      0.88  1.00  0.18
Q3      0.21  0.18  1.00
```

Here Q1 and Q2 score 0.88, which is above the **threshold of 0.82** → they are duplicates.

**3. Group duplicates (Union-Find)**

A Union-Find data structure groups all questions connected by similarity into clusters.

```
Group 1: [Q1 (2018), Q2 (2020), Q3 (2022)]  ← all versions of same question
Group 2: [Q4 (2019)]
Group 3: [Q5 (2018), Q6 (2023)]
...
```

**4. Merge each group into one row**

| Field | How it's picked |
|---|---|
| `raw_question_text` | Longest version (most complete wording) |
| `topic_tag` | Most common tag across duplicates |
| `bloom_level` | Most common level across duplicates |
| `original_marks` | Maximum marks seen (Part B preferred) |
| `part_a_years` | All years it appeared as a Part A question |
| `part_b_years` | All years it appeared as a Part B question |

---

## Final Output (dbms_os_se_Dataset.csv)

Each row in the final file is one **unique question concept** with its full history:

| Column | Meaning |
|---|---|
| `subject_name` | DBMS / Operating Systems / Software Engineering |
| `raw_question_text` | The most complete version of the question text |
| `topic_tag` | Topic it belongs to (e.g., DEADLOCK, ER_MODEL) |
| `bloom_level` | Cognitive level (Remember / Understand / Apply / Analyze / Evaluate) |
| `original_marks` | Marks it carries (2 = Part A short, 10 = Part B long) |
| `part_a_years` | Years it appeared as a short question |
| `part_b_years` | Years it appeared as a long question |

A question appearing in `part_b_years: [2018, 2020, 2022, 2023]` is a **high-frequency, high-weightage** question — exactly the kind the predictor targets.

---

## Quick Visual Summary

```
.txt question paper files
        │
        ▼
   [ parser.py ]
   Extract raw questions
        │
        ▼
   [ tagger.py ]
   For each question:
     embed question ──────────────────────┐
     embed topic descriptions (once)      │
     cosine similarity →  best topic tag  │
     bloom level from verb matching       │
        │                                 │
        ▼                                 │
  questions_tagged.csv           review_queue.csv
        │                        (low confidence)
        ▼
  [ deduplicator.py ]
   embed all questions
   pairwise cosine similarity
   group duplicates (threshold 0.82)
   merge → track years
        │
        ▼
  dbms_os_se_Dataset.csv
  (one row per unique question)
```

---

## Key Numbers

| Setting | Value | Meaning |
|---|---|---|
| Embedding model | all-MiniLM-L6-v2 | 384-dimensional sentence vectors |
| Auto-tag threshold | 0.35 | Below this → human review |
| Ambiguity margin | 0.07 | Top-2 too close → human review |
| Dedup threshold | 0.82 | Above this → treated as same question |
