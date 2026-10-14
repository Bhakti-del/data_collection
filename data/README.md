# Question Paper Predictor — Data Architecture & Dataset Catalog

Welcome to the data engineering hub for the **Question Paper Predictor** project. This directory serves as the **Single Source of Truth** for all examination question datasets, syllabi specifications, diagram assets, and raw papers across JNTU Hyderabad regulations (**R13, R15, R16, R18, and R22**).

---

## 1. Directory Structure

```text
data/
├── README.md                # This file (catalog, schema contract, and progress tracker)
├── subjects/                # Production-ready canonical 8-column CSV datasets (35 subjects)
├── normalized/              # Normalized datasets partitioned into question slots for prediction engines
├── images/                  # High-resolution diagram assets referenced in questions
├── syllabi/
│   ├── configs/             # Regulation JSON topic & keyword mappings (R13, R15, R16, R18, R22)
│   └── references/          # Official curriculum Markdown syllabus specifications
├── raw/
│   ├── text_papers/         # 1,805 raw text exam papers parsed from PDFs
│   └── pdf_papers/          # Original university examination PDFs (git-ignored)
└── cleaned/
    └── text_papers/         # 1,726 boilerplate-stripped exam papers
```

---

## 2. Canonical 8-Column Schema Contract

All finalized subject CSVs in [`data/subjects/`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/) strictly comply with the canonical **8-Column Standard Schema**. Every subject has exactly **one comprehensive dataset** merging pure text questions, mathematical formulas, and diagram-based questions.

| Column | Type | Description | Valid Values / Format | Example |
| :--- | :--- | :--- | :--- | :--- |
| `subject_name` | string | Normalized title-case subject name | String | `Advanced Algorithms` |
| `raw_question_text` | string | Complete question text (Unicode math preserved) | Clean text / Unicode math | `Find the max flow of the following graph.` |
| `topic_tag` | string | Uppercase syllabus topic identifier | Aligned to syllabus JSON | `MAXIMUM_FLOW_AND_NETWORK_FLOWS` |
| `bloom_level` | string | Bloom's taxonomy category | `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate` | `Apply` |
| `original_marks` | int | Marks weightage in source paper | Positive integer ($1 \le m \le 25$) | `15` |
| `part_a_years` | list[int] | Sorted years question appeared in Part A (short answers) | JSON integer list format | `[]` or `[2021, 2023]` |
| `part_b_years` | list[int] | Sorted years question appeared in Part B (long answers) | JSON integer list format | `[2020]` |
| `image_path` | string | Relative path to diagram asset on disk | Empty string `""` if pure text | `data/images/Advanced Algorithms/Q4.png` |

---

## 3. Data Quality & Integrity Standards

1. **Unified Datasets (No Split CSVs)**: Pure text questions and diagram questions live in the exact same subject CSV. Questions without diagrams have `image_path = ""`.
2. **Unicode Math Preservation**: Equations and mathematical symbols (`→`, `∧`, `∨`, `¬`, `∏`, `∑`, `∈`, `∫`, `≤`, `≥`, `'`) are preserved as valid Unicode text. Word Private Use Area (PUA) font glyphs (`\uf000`–`\uf8ff` and `\ue000`–`\ue0ff`) are automatically decoded into standard Unicode.
3. **Verified Image References**: Every non-empty `image_path` is verified to exist on disk.
4. **Deterministic Auditing**: All datasets must pass automated verification with 0 defects before being deployed:
   ```bash
   python3 scripts/audit_datasets.py
   ```

---

## 4. Current Dataset Catalog (35 Canonical Subjects)

All 35 canonical subjects below have been verified with **0 defects** against the 8-column schema, Bloom calibration, and image disk existence checks:

| # | Subject Dataset | Total Rows | Diagrams | Audit Status |
| :-: | :--- | :-: | :-: | :-: |
| 1 | [`Advanced_Algorithms_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Advanced_Algorithms_Dataset.csv) | 146 | 4 | **PASSED (0 defects)** |
| 2 | [`Artificial_Intelligence_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Artificial_Intelligence_Dataset.csv) | 326 | 0 | **PASSED (0 defects)** |
| 3 | [`Artificial_Neural_Networks_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Artificial_Neural_Networks_Dataset.csv) | 217 | 0 | **PASSED (0 defects)** |
| 4 | [`Big_Data_Analytics_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Big_Data_Analytics_Dataset.csv) | 149 | 0 | **PASSED (0 defects)** |
| 5 | [`Cloud_Computing_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Cloud_Computing_Dataset.csv) | 290 | 0 | **PASSED (0 defects)** |
| 6 | [`Compiler_Design_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Compiler_Design_Dataset.csv) | 266 | 0 | **PASSED (0 defects)** |
| 7 | [`Computer_Forensics_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Computer_Forensics_Dataset.csv) | 217 | 0 | **PASSED (0 defects)** |
| 8 | [`Computer_Oriented_Statistical_Methods_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Computer_Oriented_Statistical_Methods_Dataset.csv) | 223 | 0 | **PASSED (0 defects)** |
| 9 | [`Cryptography_and_Network_Security_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Cryptography_and_Network_Security_Dataset.csv) | 118 | 0 | **PASSED (0 defects)** |
| 10 | [`Data_Analytics_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Data_Analytics_Dataset.csv) | 424 | 0 | **PASSED (0 defects)** |
| 11 | [`Data_Mining_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Data_Mining_Dataset.csv) | 223 | 0 | **PASSED (0 defects)** |
| 12 | [`Database_Security_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Database_Security_Dataset.csv) | 178 | 0 | **PASSED (0 defects)** |
| 13 | [`Design_and_Analysis_of_Algorithms_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Design_and_Analysis_of_Algorithms_Dataset.csv) | 348 | 10 | **PASSED (0 defects)** |
| 14 | [`Design_Patterns_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Design_Patterns_Dataset.csv) | 360 | 0 | **PASSED (0 defects)** |
| 15 | [`Discrete_Mathematics_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Discrete_Mathematics_Dataset.csv) | 227 | 0 | **PASSED (0 defects)** |
| 16 | [`Distributed_Systems_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Distributed_Systems_Dataset.csv) | 213 | 0 | **PASSED (0 defects)** |
| 17 | [`Formal_Languages_and_Automata_Theory_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Formal_Languages_and_Automata_Theory_Dataset.csv) | 288 | 28 | **PASSED (0 defects)** |
| 18 | [`Fundamentals_of_IoT_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Fundamentals_of_IoT_Dataset.csv) | 102 | 0 | **PASSED (0 defects)** |
| 19 | [`HCI_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/HCI_Dataset.csv) | 191 | 0 | **PASSED (0 defects)** |
| 20 | [`Internet_of_Things_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Internet_of_Things_Dataset.csv) | 102 | 0 | **PASSED (0 defects)** |
| 21 | [`Java_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Java_Dataset.csv) | 453 | 0 | **PASSED (0 defects)** |
| 22 | [`Machine_Learning_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Machine_Learning_Dataset.csv) | 181 | 0 | **PASSED (0 defects)** |
| 23 | [`Mathematical_Foundations_of_Computer_Science_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Mathematical_Foundations_of_Computer_Science_Dataset.csv) | 248 | 17 | **PASSED (0 defects)** |
| 24 | [`Matrices_and_Calculus_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Matrices_and_Calculus_Dataset.csv) | 272 | 0 | **PASSED (0 defects)** |
| 25 | [`Middleware_Technologies_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Middleware_Technologies_Dataset.csv) | 25 | 0 | **PASSED (0 defects)** |
| 26 | [`Natural_Language_Processing_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Natural_Language_Processing_Dataset.csv) | 81 | 0 | **PASSED (0 defects)** |
| 27 | [`Ordinary_Differential_Equations_and_Vector_Calculus_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Ordinary_Differential_Equations_and_Vector_Calculus_Dataset.csv) | 181 | 0 | **PASSED (0 defects)** |
| 28 | [`Principles_of_Programming_Languages_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Principles_of_Programming_Languages_Dataset.csv) | 328 | 0 | **PASSED (0 defects)** |
| 29 | [`Scripting_Languages_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Scripting_Languages_Dataset.csv) | 417 | 0 | **PASSED (0 defects)** |
| 30 | [`Semantic_Web_and_Social_Networks_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Semantic_Web_and_Social_Networks_Dataset.csv) | 181 | 0 | **PASSED (0 defects)** |
| 31 | [`Soft_Computing_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Soft_Computing_Dataset.csv) | 162 | 0 | **PASSED (0 defects)** |
| 32 | [`Software_Project_Management_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Software_Project_Management_Dataset.csv) | 294 | 0 | **PASSED (0 defects)** |
| 33 | [`Software_Testing_Methodologies_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Software_Testing_Methodologies_Dataset.csv) | 170 | 0 | **PASSED (0 defects)** |
| 34 | [`Web_Services_SOA_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Web_Services_SOA_Dataset.csv) | 267 | 0 | **PASSED (0 defects)** |
| 35 | [`Web_Technologies_Dataset.csv`](file:///home/slesha/wings-AI/question-paper-predictor/data/subjects/Web_Technologies_Dataset.csv) | 309 | 0 | **PASSED (0 defects)** |
| **Total** | **35 Subject Datasets** | **8,177** | **59** | **0 Defects** |

---

## 5. Next Phase: Data Normalization (`data/normalized/`)

Once subject data collection and verification is finalized, datasets proceed to normalization into [`data/normalized/`](file:///home/slesha/wings-AI/question-paper-predictor/data/normalized/):
- **Marks Calibration**: Sub-questions mapped to standard JNTUH examination slots (`PART_A_1M`, `PART_A_2M`, `PART_B_5M`, `PART_B_7M`, `PART_B_10M`).
- **Blueprint Alignment**: Formatted directly for prediction engines and constraint solvers.
