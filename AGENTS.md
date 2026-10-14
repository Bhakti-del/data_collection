# AGENTS.md — Question Paper Predictor

Welcome, Agent. This document defines the operational directives, architectural standards, permission policies, and data contracts for the `question-paper-predictor` project.

---

## 1. Project Overview & Mission

`question-paper-predictor` is an automated data engineering and machine learning pipeline designed to scrape, extract, clean, categorize, and assemble question papers for university examinations (JNTUH R13, R15, R16, R18, and R22 regulations).

### Core Pipeline Objectives
1. **Raw Paper Ingestion & OCR**: Ingest PDF and scanned examination papers into raw text format.
2. **Boilerplate Stripping & Cleaning**: Eliminate recurring headers, invigilator instructions, and kerning noise.
3. **Atomic Question Extraction**: Parse papers into individual atomic questions and sub-questions with marks.
4. **Syllabus & Bloom Tagging**: Map questions to syllabus units and Bloom's taxonomy levels using sentence embeddings and local LLMs.
5. **Semantic Deduplication**: Cluster recurring questions across examination sessions and years using Union-Find cosine similarity.
6. **Blueprint & Constraint Assembly**: Feed normalized datasets to constraint solvers and prediction engines.

---

## 2. Command Permissions & Autonomy Policy

To ensure high velocity without compromising system safety, agents are granted explicit permission to execute **non-disruptive commands autonomously** without seeking interactive user approval.

### Allowed Non-Disruptive Commands (Auto-Approved)
* **Python Execution**:
  * Running any script in `scripts/`, `src/`, `tools/`, or `run_pipeline.py`.
  * Running audits: `python scripts/audit_datasets.py`, `python scripts/clean_all_datasets.py`.
  * Running one-off diagnostic snippets: `python -c "..."`.
* **Testing & Quality Assurance**:
  * Test execution: `pytest`, `python -m pytest`, `python -m unittest`.
  * Linting and format checks: `flake8`, `black --check`, `isort --check`, `mypy`.
* **Repository & Environment Inspection**:
  * Git queries: `git status`, `git diff`, `git log`, `git branch`, `git ls-files`, `git ls-tree`, `git show`.
  * File and filesystem exploration: `ls`, `cat`, `head`, `tail`, `grep`, `find`, `wc`, `tree`, `awk`, `sed`.
  * Package inspection: `pip list`, `pip show`, `pip check`.

### Guarded & Disruptive Actions (Require Explicit Confirmation / Denied)
* **Destructive Git Commands**: `git reset --hard`, `git push --force`, `git clean -fd`.
* **Dangerous Deletions**: `rm -rf` on root, home, parent directories, or unverified wildcards.
* **External Environment Modifications**: Installing global packages or modifying system binaries without user notice.

*(Fine-grained machine permissions are configured in [`.agents/permissions.json`](file:///.agents/permissions.json)).*

---

## 3. Directory Layout & Storage Hierarchy

All project data must reside strictly within the unified `data/` directory. **Do not create ad-hoc scratch folders** (such as `temp_data` or personal folders) in the repository root.

```text
question-paper-predictor/
├── README.md                                    # Project documentation
├── AGENTS.md                                    # Agent operating instructions & rules
├── run_pipeline.py                              # End-to-end pipeline runner
├── conftest.py                                  # Pytest global fixtures
│
├── .agents/                                     # Agent configuration & permission rules
│   └── permissions.json                         # Command permission grant specification
│
├── data/                                        # Single Source of Truth for Data
│   ├── README.md                                # Dataset catalog & architecture guide
│   │
│   ├── subjects/                                # Canonical 8-column subject datasets (35 subjects)
│   │
│   ├── normalized/                              # Normalized slot-mapped datasets for prediction engines
│   │
│   ├── images/                                  # Extracted and verified exam diagrams
│   │
│   ├── syllabi/                                 # Syllabi definitions and configs
│   │   ├── configs/                             # Regulation-wise JSON configs (R13, R15, R16, R18, R22)
│   │   └── references/                          # Markdown syllabi references
│   │
│   ├── raw/                                     # Raw crawled inputs & unedited OCR txt
│   │   ├── text_papers/                         # Raw text papers across regulations
│   │   └── pdf_papers/                          # Original exam PDFs (git-ignored)
│   │
│   └── cleaned/                                 # Regularized paper text files
│       └── text_papers/                         # Boilerplate-stripped exam text
│
├── docs/                                        # Architecture specifications and guides
│
├── scripts/                                     # Automated data processing & QA tools
│   ├── audit_datasets.py                        # Dataset verification test suite
│   ├── clean_all_datasets.py                    # Dataset regularizer and normalizer
│   ├── clean_papers.py                          # Boilerplate stripper
│   ├── extract_images.py                        # Diagram extractor
│   ├── local_llm_tagger.py                      # Ollama-based LLM classifier
│   ├── txt_to_csv.py                            # Regex question parser
│   └── build_*_canonical.py                     # Subject canonical builders
│
├── src/                                         # Core modular pipeline
│   ├── parser.py                                # Paper parser and question segmenter
│   ├── tagger.py                                # SentenceTransformer semantic tagger
│   └── deduplicator.py                          # Union-Find question deduplicator
│
└── tools/                                       # Scraping and batch extraction tools
    ├── pdf_to_txt.py                            # PDF to text converter
    └── qpaper_scraper.py                        # Selenium-based crawler
```

---

## 4. Dataset Standards & Schema Contract

All finalized subject CSVs inside `data/subjects/` must strictly comply with the **8-Column Standard Schema** (merging text and image-based questions):

| Column Name | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `subject_name` | string | Normalized title-case subject name | `Database Management Systems` |
| `raw_question_text` | string | Cleaned question text (preserves Unicode math & equations) | `Explain Domain Integrity constraints in SQL.` |
| `topic_tag` | string | Uppercase snake_case syllabus topic identifier | `RELATIONAL_MODEL_ALGEBRA` |
| `bloom_level` | string | Bloom's taxonomy category | `Remember`, `Understand`, `Apply`, `Analyze`, `Evaluate`, `Create` |
| `original_marks` | int / float | Question mark weightage | `10` |
| `part_a_years` | list[int] | Sorted calendar years appearing in Part A (short questions) | `[2021, 2023]` |
| `part_b_years` | list[int] | Sorted calendar years appearing in Part B (long questions) | `[2018, 2022]` |
| `image_path` | string | Relative path to question diagram (empty string `""` if pure text) | `data/images/DAA/q5.png` or `""` |

### Data Quality Rules
1. **Equations are Text**: Standard mathematical symbols (`→`, `∧`, `∨`, `¬`, `∈`, `⊆`, `∑`, `√`, `∫`) are valid Unicode text. Never discard questions containing mathematical symbols. Map legacy Private Use Area (PUA) font glyphs (`\uf000`–`\uf8ff`) to canonical Unicode characters.
2. **Unified Image Handling**: Do not maintain separate `_with_images` CSV files. Every subject has exactly one canonical dataset where questions without diagrams simply have an empty `image_path`.
3. **2D Structural Math Fallback**: Only complex 2D layouts (matrices, multi-line integral systems) where linear text extraction collapses the structure should utilize an image crop in `image_path`.
4. **No Phantom Artifacts**: Remove PDF line break artifacts, double spaces, and broken ligatures (`fi`, `fl`, `ff`).
5. **Deterministic Validation**: Always run `python scripts/audit_datasets.py` after modifying any dataset.

---

## 5. Development & Pairing Guidelines

1. **Path Handling**: Always use `pathlib.Path` over raw string manipulation for cross-platform robustness.
2. **Documentation Integrity**: Preserve existing comments and docstrings unless explicitly asked to modify them.
3. **Clickable Links**: In chat responses, always provide clickable markdown links to referenced files using `file:///absolute/path`.
4. **Verification First**: Validate scripts by running tests or audits prior to completing tasks.
