# Java Sample Engine: Formally Verified R22 Question Paper Predictor

This directory contains the reference decision engine for predicting JNTUH examination question papers targeting the **R22 Regulation** for **Object Oriented Programming through Java**.

Once proven and verified here, this architecture will be scaled systematically across all 29 other engineering subjects.

---

## 1. Directory Structure

```text
JAVA_sample-engine/
├── README.md                                # This document
├── docs/                                    # Formal Architecture & Guides
│   ├── CSP_Architecture.md                  # Mathematical formulation of the Max-CSP
│   ├── Marks_Normalization_Guide.md         # R22 1M, 5M, 10M normalization rules
│   └── Rubric_Synthesis.md                  # Synthesis of Rubric Teams 1, 2, 3, 4
├── data/                                    # Ground Truth Datasets
│   ├── Java_Dataset_normalized.csv          # 454 Java questions with R22 normalized marks
│   └── Java_syllabus.json                   # Official R22 5-unit syllabus with categories
└── src/                                     # Lean 4 & Pipeline Implementation
```

---

## 2. The Core Problem: A Constrained Optimization Problem (Max-CSP)

The decision engine solves a **Weighted Constraint Satisfaction Problem**:

$$\text{Maximize } \mathcal{J}(P) \quad \text{subject to} \quad \mathcal{H}_1 \wedge \mathcal{H}_2 \wedge \mathcal{H}_3 \wedge \mathcal{H}_4 \wedge \mathcal{H}_5$$

### Hard Constraints $\mathcal{H}$ (Enforced & Proved in Lean 4)
- **$\mathcal{H}_1$ (Total Marks):** Exactly 60 marks attempted.
- **$\mathcal{H}_2$ (Unit Coverage):** Exactly 2 Part A questions per unit across Units 1–5; exactly 1 Part B internal choice pair per unit.
- **$\mathcal{H}_3$ (Category Orthogonality):** Choice I and Choice II in Part B test disjoint syllabus categories (e.g. *Exceptions* vs *Threads* in Unit 3).
- **$\mathcal{H}_4$ (Non-Duplication):** No duplicate questions across the paper.
- **$\mathcal{H}_5$ (Anti-2024 Repeat):** No question from the 2024 paper is repeated identically.

### Soft Constraints $\mathcal{J}$ (Score Optimization)
- Historical appearance frequency over 8 years ($T = 8$).
- Cycle boost ($gap = 2$, last seen in 2022 $\to +35\%$ boost).
- Java coding requirement ($\ge 30\%$ `Apply` in Part B).
- Part A verbatim repeat affinity ($P1$ flag).
