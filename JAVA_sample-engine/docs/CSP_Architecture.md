# Formal CSP Architecture & Decision Engine Specification

## 1. Mathematical Framing: Constrained Optimization (Max-CSP)

The Question Paper Predictor is mathematically framed as a **Constrained Optimization Problem** (or **Weighted Max-CSP**):

$$\text{Maximize } \mathcal{J}(P) = \sum_{q \in P} \text{Score}(q) \quad \text{subject to} \quad \mathcal{H}_i(P) = \text{True} \quad \forall i$$

Where:
- $P$ is the synthesized Examination Paper (a selection of slots).
- $\mathcal{H}_i$ are the **Hard Constraints** (must be 100% satisfied; failure = invalid paper).
- $\mathcal{J}(P)$ is the **Soft Optimization Objective** (the composite score derived from rubric rules).

---

## 2. Variables & Domains (The R22 JNTUH Slot Layout)

An R22 question paper consists of **15 slots** (total 60 attempted marks):

### A. Part A Slots ($A_1 \dots A_{10}$ — 10 Marks Total)
- Exactly 10 compulsory questions carrying **1 Mark each**.
- Variables:
  - Unit 1: $A_1, A_2$
  - Unit 2: $A_3, A_4$
  - Unit 3: $A_5, A_6$
  - Unit 4: $A_7, A_8$
  - Unit 5: $A_9, A_{10}$
- Domain for $A_i$: All normalized Java questions where `slot_type == "PART_A_1M"` and `unit == u(i)`.

### B. Part B Slots ($B_1 \dots B_5$ with Internal Choice — 50 Marks Total)
- Exactly 5 choice pairs, one for each unit $u \in \{1..5\}$.
- Each pair consists of **Choice I (Questions $2u$)** OR **Choice II (Questions $2u + 1$)**.
- Each Choice carries **10 Marks** (either a single 10M question, or two 5M sub-questions $a + b$).
- Domain for $B_u$: All normalized Java questions where `slot_type ∈ {"PART_B_10M", "PART_B_5M"}` and `unit == u`.

---

## 3. Hard Constraints $\mathcal{H}$ (Invariants Enforced in Lean 4)

A generated paper $P$ is valid if and only if **all five hard constraints hold**:

1. **$\mathcal{H}_1$ (Total Marks Conservation):**
   $$\sum_{q \in \text{Attempted}(P)} \text{marks}(q) = 60$$

2. **$\mathcal{H}_2$ (Strict Unit Equipartition):**
   $$\forall u \in \{1..5\}: \quad |\text{PartA}(u)| = 2 \quad \wedge \quad |\text{PartBChoicePairs}(u)| = 1$$

3. **$\mathcal{H}_3$ (Category Orthogonality):**
   Within every unit $u$, Choice I and Choice II must be drawn from **distinct syllabus categories**:
   $$\text{Category}(\text{Choice } I_u) \cap \text{Category}(\text{Choice } II_u) = \emptyset$$
   *(e.g., in Unit 3, Choice I tests "Exception Handling" while Choice II tests "Multithreading".)*

4. **$\mathcal{H}_4$ (Global Non-Duplication):**
   No question statement may appear more than once across the entire paper:
   $$\forall q_i, q_j \in P: \quad i \neq j \implies q_i \neq q_j$$

5. **$\mathcal{H}_5$ (Immediate Prior Year Non-Repeat / Cooling-Off Gate):**
   No selected question may have appeared in the immediate prior examination year ($2024$):
   $$\forall q \in P: \quad 2024 \notin (\text{part\_a\_years}(q) \cup \text{part\_b\_years}(q))$$

---

## 4. Soft Constraints & Scoring Function $\mathcal{J}(q)$

Candidate questions that pass all hard gates are scored using the synthesized multi-team rubric:

$$\text{Score}(q) = w_1 \cdot \text{Freq}(q) + w_2 \cdot \text{CycleBoost}(q) + w_3 \cdot \text{BloomWeight}(q) + w_4 \cdot \text{Affinity}(q)$$

1. **Historical Frequency Signal $\text{Freq}(q)$:**
   $$\text{Freq}(q) = \frac{|\text{part\_a\_years}(q) \cup \text{part\_b\_years}(q)|}{T}$$
   Where $T = 8$ (years 2017 to 2024).

2. **Cycle / Overdue Boost:**
   If a question appeared in 2022 ($gap = 2$) or 2021 ($gap = 3$) and has a multi-year history, it receives a $+0.25$ cycle boost (cooling-off period completed; overdue to reappear).

3. **Bloom Taxonomy / Java Coding Quota:**
   - For Part B questions, code-writing tasks (`Apply`) receive a $+0.20$ multiplier.
   - For Part A questions, direct definitions (`Remember`) receive $+0.15$ if they have a confirmed verbatim repeat history ($P1$ flag).

---

## 5. Execution Strategy

```
[Normalized Java Dataset (454 rows)] + [R22 Java Syllabus JSON (5 Units, 53 Topics)]
                                  │
                                  ▼
                    [Hard Gate: Syllabus & Anti-2024 Repeat]
                                  │
                                  ▼
                       [Soft Scorer & Ranker]
                                  │
                                  ▼
                [Lean 4 Backtracking / Greedy CSP Solver]
                                  │
                                  ▼
         [Formal Proof: All Hard Invariants Validated at Compile-Time]
                                  │
                                  ▼
                       [PaperBlueprint JSON Output]
```
