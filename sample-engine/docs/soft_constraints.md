# Soft Constraints Specification

This document defines all **Soft Constraints** ($\mathcal{S}$) enforced by the Question Paper Predictor.
Soft constraints do not invalidate or reject a paper. Instead, they produce real-valued scoring multipliers or preference rankings:
$$S: \text{Candidate} \to \mathbb{R}^+$$
These scores guide the combinatorial solver in choosing the top candidates and ranking candidate paper blueprints.

---

## 1. Candidate Scoring Multipliers & Signals

### S1: Historical Topic Frequency
* **Definition:** The proportion of eligible historical exam papers in which a question or topic has appeared.
* **Range:** $\text{freq} \in [0.0, 1.0]$.
* **Role:** Serves as the primary baseline confidence term:
  $$\text{base\_score}(q) = \text{freq}(q)$$
* **Origin:** `origin/engine:Scorer/Scorer_Spec.md`, `rubrics3`, `rubrics4` (Person 3).

### S2: Recency Gap Multipliers
* **Definition:** Modifies candidate score based on the number of examination sessions since its last observed appearance ($\text{gap}$).
* **Values:**
  * **Gap = 2 (Cycle-Due Boost):** Topic skipped one exam cycle and is overdue for reappearance $\implies \times 1.45$.
  * **Gap = 1 (Cooling-off Penalty):** Topic appeared in the very recent cycle $\implies \times 0.60$.
  * **Gap = 0 (Part A Repeat):** Recent questions in Part A allowed with slight dampening $\implies \times 0.80$.
  * **Gap $\ge 3$ or Unseen:** Baseline long-gap multiplier $\implies \times 1.10$.
* **Origin:** `JAVA_sample-engine/src/Engine.lean`, `origin/engine:Scorer/Scorer_Spec.md`, `rubrics4` (Person 4).

### S3: Bloom's Taxonomy Cognitive Multiplier
* **Definition:** Adjusts priority according to cognitive depth and subject requirements:
  * **Part B Slots (Technical / Java Coding Focus):**
    * `Apply` $\implies \times 1.35$ (Writing code, implementing OOP principles).
    * `Analyze` $\implies \times 1.15$ (Debugging, complexity, class design).
    * `Understand` $\implies \times 1.00$ (Theoretical explanations).
    * Other $\implies \times 0.80$.
  * **Part A Slots (Short Definitions / Recall):**
    * `Remember` (with $\text{freq} \ge 0.25$) $\implies \times 1.30$.
    * Other $\implies \times 1.00$.
* **Origin:** `JAVA_sample-engine/src/Engine.lean`, `rubrics3`.

### S4: Semantic Syllabus Closeness
* **Definition:** Candidates whose wording or topic matches syllabus headings with high semantic similarity receive higher baseline priority.
* **Origin:** `rubrics4` (Person 1 R3).

---

## 2. Structural & Placement Preferences

### S5: Form B (Sub-questions) Over Form A Preference
* **Definition:** When a unit's pool contains two strong candidates covering distinct topic categories, prefer splitting the 10 marks into sub-questions (e.g., `[5, 5]` or `[6, 4]`) over a single 10-mark question (`[10]`).
* **Origin:** `rubrics4` (Person 2 R10).

### S6: Choice Slot Ordering
* **Definition:** Within each Part B unit choice pair, place the candidate with the higher composite score in **Choice I** and the secondary candidate in **Choice II**.
* **Origin:** `rubrics4` (Person 2 R11).

### S7: Marks-Weighted Unit History
* **Definition:** Units that historically carried higher aggregate marks across papers receive higher selection priority when allocating strong candidates.
* **Origin:** `rubrics4` (Person 5).

---

## 3. Deduplication & Conflict Resolution

### S8: Semantic Deduplication Preference
* **Definition:** If two candidate questions within the candidate pool have semantic similarity (cosine similarity) exceeding threshold $T$:
  1. Keep the candidate with higher historical frequency.
  2. If tied on frequency, keep the candidate with higher model score.
  3. Drop the other from the pool.
* **Origin:** `origin/engine:Scorer/Scorer_Spec.md` (SD-R2), `rubrics4` (Person 6).

### S9: 5-Level Tie-Breaking Hierarchy
* **Definition:** When two candidate questions have composite scores within $\pm 0.05$, resolve the tie using this sequential hierarchy:
  1. **Section History:** Prefer the candidate with past appearance in that specific section (Part A vs Part B).
  2. **Marks History:** Prefer the candidate consistently asked for higher marks.
  3. **Last Appearance Gap:** Prefer the candidate with the larger gap (absent longer).
  4. **Sub-topic Breadth:** Prefer the candidate addressing broader syllabus scope.
  5. **Verbatim Repeat History:** Prefer the candidate with verified repeated past appearances.
* **Origin:** `rubrics2:002.md` (Case 13).

### S10: Paper Composite Score Calibration
* **Definition:** The score of a complete verified paper blueprint is the normalized sum of scores of all selected questions:
  $$\text{PaperScore}(P) = \frac{1}{|P|} \sum_{q \in P} \text{score}(q)$$
  This composite score allows ranking all structurally valid papers to select the **Top 3 Predicted Papers**.
* **Origin:** Sourced from `rubrics3` (Section 5, Rule 6), formalized in `JAVA_sample-engine/src/Engine.lean`.
