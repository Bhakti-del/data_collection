# Hard Constraints Specification

This document defines all **Hard Constraints** ($\mathcal{H}$) enforced by the Question Paper Predictor.
A Hard Constraint is a strict Boolean predicate $P: \text{Paper} \to \{0, 1\}$.
If any candidate paper violates even one hard constraint, it is **unconditionally rejected**.

---

## 1. Paper-Level Structural Constraints

### H1: Total Attempted Marks
* **Rule:** The total marks attempted by a student must equal **exactly 60 marks**.
* **Formula:**
  $$\text{AttemptedMarks}(\text{Paper}) = \text{Marks}(\text{Part A}) + \text{AttemptedMarks}(\text{Part B}) = 10 + 50 = 60$$
* **Printed Total:** 110 marks across all compulsory and optional alternatives.
* **Origin:** `rubrics4` (Person 2 R9, Person 5), `rubrics3`.

### H2: Part A Structure & Unit Allocation
* **Rule:** Part A must contain **exactly 10 compulsory questions**, each carrying **exactly 1 mark**.
* **Unit Distribution:** Exactly 2 questions from each of the 5 units ($\text{Unit } 1, 2, 3, 4, 5$).
* **Constraint:**
  $$\forall u \in \{1, 2, 3, 4, 5\}, \quad |\{q \in \text{Part A} \mid \text{unit}(q) = u\}| = 2$$
* **Origin:** `rubrics4` (Person 2 R1, R2, R3), `rubrics3`.

### H3: Part B 5-Unit OR-Choice Structure
* **Rule:** Part B must contain **exactly 5 choice pairs**, exactly one per unit ($\text{Unit } 1, 2, 3, 4, 5$).
* **Choices per Unit:** Every unit has exactly 2 alternatives: $\text{Choice I}$ and $\text{Choice II}$.
* **Marks per Choice:** Each alternative choice must sum to **exactly 10 marks**.
* **Constraint:**
  $$\forall u \in \{1, 2, 3, 4, 5\}, \quad \text{marks}(\text{Choice I}_u) = 10 \quad \land \quad \text{marks}(\text{Choice II}_u) = 10$$
* **Origin:** `rubrics4` (Person 2 R4, R5, R6, R7), `rubrics3`.

### H4: Part B Allowed Mark Distributions (Pruned to Dataset Feasibility)
* **Rule:** Every Part B alternative must follow an approved mark distribution.
* **Strict Allowed Splits:**
  1. `[10]` — A single 10-mark question.
  2. `[5, 5]` — Two 5-mark sub-questions (e.g., Q(a) and Q(b)).
  3. `[6, 4]` — A 6-mark and a 4-mark sub-question (where available in question bank).
* **Note on Active Dataset:** In `java_candidates.json`, sub-questions are normalized to 5M and 10M. Thus active choices evaluate to `[10]` or `[5, 5]`.
* **Origin:** Sourced from `rubrics3` / `rubrics3formalized.md` (which lists `[10], [5,5], [6,4], [7,3], [8,2]`), refined here to the practical splits `[10], [5, 5], [6, 4]`.

---

## 2. Topic & Content Integrity Constraints

### H5: Category Orthogonality (Choice Diversity)
* **Rule:** For any unit in Part B, Choice I and Choice II **must come from different topic categories**.
* **Constraint:**
  $$\forall u \in \{1, 2, 3, 4, 5\}, \quad \text{category}(\text{Choice I}_u) \neq \text{category}(\text{Choice II}_u)$$
* **Rationale:** A student choosing between Choice I and Choice II must be given a genuine choice across distinct conceptual areas within that unit, not two questions on the exact same topic.
* **Origin:** `rubrics4` (Person 2 R8), `origin/engine:Documents/rubrics_set.txt`.

### H6: Global Non-Duplication
* **Rule:** No duplicate question or identical core task can appear anywhere in the printed paper.
* **Scope:**
  * Across Part A and Part B.
  * Between Choice I and Choice II in the same unit.
  * Across different units.
* **Constraint:**
  $$\forall q_i, q_j \in \text{PrintedQuestions}(\text{Paper}), \quad i \neq j \implies \text{id}(q_i) \neq \text{id}(q_j)$$
* **Origin:** `rubrics3`, `rubrics4` (Person 6), `origin/engine:Scorer/Scorer_Spec.md`.

### H7: Syllabus Compliance Gate
* **Rule:** Every candidate question must map to an active, valid topic in the current regulation's syllabus (R22).
* **Constraint:** Any question with no topic tag, an out-of-syllabus tag, or a topic removed in R22 is excluded before assembly.
* **Origin:** `rubrics4` (Person 1 R1, R2, R5, R6), `origin/engine:Scorer/Scorer_Spec.md`.

---

## 3. Temporal & Pool Constraints

### H8: Anti-Repeat Gate (Immediate Previous Exam)
* **Rule:** Questions that appeared in Part B of the immediately preceding examination cycle ($\text{gap} = 0$) receive an absolute exclusion penalty ($-1000$) and cannot appear in Part B of the predicted paper.
* **Formulation:** Evaluated dynamically using relative $\text{gap} = 0$ (avoiding hardcoded calendar years).
* **Origin:** `rubrics4` (Person 4), implemented in `JAVA_sample-engine/src/Engine.lean`.

### H9: Temporal Data Leakage Prohibition
* **Rule:** When predicting for exam $n$, feature extraction and candidate metrics must strictly use data from exams $\le n - 1$.
* **Origin:** `rubrics4` (Additional Considerations).

### H10: Top-Frequency Topic Pool Presence
* **Rule:** For every unit, candidate questions covering the historically most-frequent topic in that unit must be present in the candidate pool.
* **Origin:** `rubrics4` (Person 3).
