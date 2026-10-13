# Multi-Team Rubric Synthesis & Calibration for Java

This document establishes the unified mathematical rubric synthesized from all four rubric team proposals (`rubric_team1`, `rubrics2`, `rubrics3`, `rubrics4`) calibrated specifically for Object Oriented Programming through Java.

---

## 1. Synthesis Table of the 4 Rubric Teams

| Team / Source | Core Mechanism Integrated into Engine | Formal Implementation |
|---|---|---|
| **Team 1 (`rubric_team1`)** | Strict JNTUH R22 structure: 10 Part A (1M) + 5 Part B (10M pairs). Orthogonal internal choice partitions. | Hard Constraint: $H_1, H_2, H_3$ |
| **Team 2 (`rubrics2`)** | Priority Score formula with inverted recency ($w_{N-1} = 0.2$ cooling-off). High boost ($P1$) for Part A definitions that repeat verbatim. | Soft Scoring Signal: $S_{\text{recency}}, S_{\text{verbatim}}$ |
| **Team 3 (`rubrics3`)** | Formal Lean 4 types (`QuestionRow`, `UnitId := Fin 5`), exact rational arithmetic (`Rat`), and non-duplication invariants. | Lean 4 Invariant: `ValidPaper` |
| **Team 4 (`rubrics4`)** | Alternating cycle pattern detection (topics that alternate on odd/even years). | Soft Scoring Signal: $S_{\text{cycle}}$ |
| **Java Base Profile** | The **Coding Imperative**: At least 30% of Part B questions must require writing Java code (`bloom_level == "Apply"`). | Subject Domain Constraint: $H_{\text{Java\_Code}}$ |

---

## 2. Mathematical Definition of the Scoring Function

For each candidate question $q$ passing the Hard Gates ($q \in \text{R22 Syllabus}$ and $2024 \notin \text{years}(q)$):

$$\text{FinalScore}(q) = \text{BaseFrequency}(q) \times \text{CycleMultiplier}(q) \times \text{BloomMultiplier}(q)$$

### Component 1: Base Frequency ($T = 8$ years: 2017 to 2024)
$$\text{BaseFrequency}(q) = \frac{|\text{years}(q)|}{8}$$

### Component 2: Cycle & Cooling-Off Multiplier
- **$gap = 0$ (Asked in 2024):** Excluded by Hard Gate $H_5$.
- **$gap = 1$ (Last asked in 2023):** $\text{CycleMultiplier} = 0.60$ (Cooling off).
- **$gap = 2$ (Last asked in 2022):** $\text{CycleMultiplier} = 1.35$ (Cycle Due Boost: high probability of alternating return).
- **$gap \ge 3$ (Last asked in 2021 or earlier):** $\text{CycleMultiplier} = 1.10$.

### Component 3: Bloom / Task Multiplier for Java
- **For Part B Slots:**
  - `Apply` (Writing code, constructing programs): $\times 1.25$
  - `Analyze` (Differentiating, comparisons): $\times 1.10$
  - `Understand` (Explaining mechanisms): $\times 1.00$
  - `Remember` (Pure recall in Part B): $\times 0.85$
- **For Part A Slots:**
  - `Remember` with multi-year repeat history ($P1$): $\times 1.30$
  - `Understand` / `Apply`: $\times 1.00$

---

## 3. Category Breakdown for Java Syllabus Units

Extracted directly from `Java_syllabus.json`:

- **Unit 1:**
  - `Cat_1A`: *Java Basics & Control Flow* (`OOP_PARADIGMS`, `DATA_TYPES`, `OPERATORS`, `CONTROL_STATEMENTS`)
  - `Cat_1B`: *Classes, Objects & Methods* (`CLASSES_AND_OBJECTS`, `CONSTRUCTORS`, `METHOD_OVERLOADING`, `THIS_KEYWORD`)
- **Unit 2:**
  - `Cat_2A`: *Inheritance & Polymorphism* (`INHERITANCE_BASICS`, `SUPER_KEYWORD`, `METHOD_OVERRIDING`, `ABSTRACT_CLASSES`)
  - `Cat_2B`: *Packages & Interfaces* (`PACKAGES_CREATION`, `INTERFACES_DEFINITION`, `EXTENDING_INTERFACES`)
- **Unit 3:**
  - `Cat_3A`: *Exception Handling* (`TRY_CATCH_FINALLY`, `CUSTOM_EXCEPTIONS`, `BUILT_IN_EXCEPTIONS`)
  - `Cat_3B`: *Multithreading* (`THREAD_LIFECYCLE`, `CREATING_THREADS`, `THREAD_SYNCHRONIZATION`, `INTER_THREAD_COMMUNICATION`)
- **Unit 4:**
  - `Cat_4A`: *Event Handling & Listeners* (`EVENT_HANDLING`, `DELEGATION_MODEL`, `ADAPTER_CLASSES`)
  - `Cat_4B`: *AWT Components & Layouts* (`AWT_COMPONENTS`, `LAYOUT_MANAGERS`, `GRAPHICS_PROGRAMMING`)
- **Unit 5:**
  - `Cat_5A`: *Applets* (`APPLETS_CONCEPTS`, `APPLET_LIFECYCLE`, `PASSING_PARAMETERS`)
  - `Cat_5B`: *Swing Architecture* (`SWING_OVERVIEW`, `MVC_ARCHITECTURE`, `SWING_COMPONENTS`)

**Guaranteed Orthogonality in Part B:**
- For Unit 3: Choice I is drawn strictly from `Cat_3A` (Exceptions), Choice II from `Cat_3B` (Multithreading).
- For Unit 5: Choice I from `Cat_5A` (Applets), Choice II from `Cat_5B` (Swing).
