# Q Discussion 1 — Project Understanding & Ambiguities

**Date:** 2026-09-29  
**Author:** Amazon Q  
**Sources:** `README.md`, `problem_descrption_v1.md`, `project_overview.md`, `docs/`, `qpaper_scraper.py`, `pdf_to_txt.py`, `sample.txt`

---

## My Understanding

### What the project does
Build a system that ingests ~13 years of JNTUH B.Tech question papers (R09–R22), extracts and structures every question into a dataset, then uses a rule/rubric engine to generate a realistic predicted question paper for an upcoming exam.

### Teams & Responsibilities
| Team | Responsibility |
|---|---|
| Data (T1–T3) | Crawl, extract, segment, deduplicate question papers into `questions_master.csv` |
| Rubrics (T4–T5) | Define all constraints/criteria the generated paper must satisfy (e.g., no repeat of last year's paper) |
| Backend / Lean (T6–T7) | **Constraint solver** — reads CSV + rubrics, generates a valid predicted paper |
| Frontend / Phoenix (T8–T9) | UI for subject selection, regulation selection, paper generation trigger, LaTeX/PDF export |
| ML Engine | Prediction logic (frequency analysis, recency weighting, topic scoring) |

> `project_overview.md` clarifies: **Backend (Lean) is NOT the ML engine.** ML engine is a separate team. Backend's job is the **constraint solver** — given a scored/ranked list of candidate questions from the ML engine, enforce the structural rubrics and output a valid paper.

### Dataset schema (confirmed 8 fields)
| # | Field | Type | Purpose |
|---|---|---|---|
| 1 | `subject_name` | String | Primary filter |
| 2 | `raw_question_text` | Text | Actual question text |
| 3 | `topic_tag` | String | Exact concept — drives frequency prediction |
| 4 | `topic_category` | String | Higher-level group — enforces variety in OR-choice pairs |
| 5 | `bloom_level` | Enum | Balances paper difficulty |
| 6 | `original_marks` | Integer | Slots into Part A (≤3M) or Part B (≥5M) |
| 7 | `part_a_years` | List[Int] | Years appeared as short answer |
| 8 | `part_b_years` | List[Int] | Years appeared as long answer |

> The CSV contains **only questions relevant to the current (latest) regulation's syllabus**. Cross-regulation filtering is handled at data ingestion time, not at query time.

### Pipeline (as designed)
```
Raw PDFs (portal + Drive)
  → Script 01: crawl & download
  → Script 02: PDF → TXT (pypdf / pdftotext)
  → Script 03: syllabus PDF → syllabi_configs JSON
  → Script 04: TXT → atomic questions (regex splitter)
  → Script 05: topic tagger + export → questions_master.csv
  → ML Engine: scores/ranks candidate questions
  → Lean 4 Backend: constraint solver applies rubrics → valid paper structure
  → Phoenix LiveView UI: subject/regulation selection, display, LaTeX/PDF export
```

### What exists right now
| File | Status |
|---|---|
| `qpaper_scraper.py` | Working Selenium scraper, hardcoded to one NAV_PATH at a time |
| `pdf_to_txt.py` | Working pypdf batch converter, hardcoded default root path |
| `sample.txt` | One extracted paper (COSM, R22, Feb 2024) — confirms extraction works |
| `docs/` | 4 design docs covering fields, crawling, directory layout, tagging guide |
| `scripts/`, `engine/`, `ui/`, `data/` | Directories do not exist yet — only documented |

---

## Ambiguities & Open Questions

### RESOLVED by `project_overview.md`

| # | Ambiguity | Resolution |
|---|---|---|
| A1 | "10 fields" claimed, 8 listed | **8 is correct.** `project_overview.md` lists exactly 8 with full descriptions. The "10 fields" mention in README/docs is stale. |
| A2 | `regulation` field missing from schema | **Intentional.** The CSV only contains questions for the current regulation's syllabus. Regulation is a pre-filter at ingestion, not a column. |

---

### STILL OPEN

**A3 — `unit_number` decision undocumented** *(Blocking — Backend)*  
The dataset design doc mentions "Universal concept keys vs hardcoded unit numbers" as a core architectural decision but never states the conclusion. Is `unit_number` stored or dropped? The Lean engine needs to know which unit a question belongs to in order to enforce the JNTUH rule that each unit must contribute exactly one Part B question.

**A4 — Two scrapers doing the same job differently** *(Medium)*  
`qpaper_scraper.py` (Selenium, in root) and the crawler in `data_crawling_and_sources.md` (requests + BeautifulSoup, recursive) are two different implementations of the same crawl. The doc crawler is the intended `scripts/01_crawler.py`. Which one is canonical?

**A5 — `pypdf` vs `pdfplumber`/`pdftotext`** *(Medium)*  
The working script uses `pypdf`. README and docs specify `pdfplumber` + `poppler pdftotext`. These produce different output quality. Which extractor is the pipeline standard?

**A6 — No OCR strategy for scanned papers** *(Blocking — Data)*  
Older regulations (R09, R13) are likely scanned image PDFs. `pdf_to_txt.py` writes a placeholder and moves on. No OCR tool (Tesseract, AWS Textract, etc.) is specified. Without this, a significant portion of the corpus will be empty rows.

**A7 — `bloom_level` assignment process unspecified** *(Medium)*  
The field exists and its purpose is clear (balance paper difficulty). But there is no script, rule, or guide describing how it is assigned — manually by reviewers, by an LLM, or by keyword heuristics.

**A8 — Deduplication criterion for "same question" undefined** *(Blocking — Data)*  
The storage model says "one row = one unique question." But question wording varies slightly across years. What is the deduplication criterion — exact text match, embedding similarity above a threshold, or manual review? This directly affects all frequency counts the ML engine relies on.

**A9 — `scripts/` directory doesn't exist yet** *(Blocking — All teams)*  
README tells contributors to run `python scripts/03_parse_syllabus.py` and `python scripts/04_segment_questions.py`. These scripts don't exist. Only `qpaper_scraper.py` and `pdf_to_txt.py` exist in root (not in `scripts/`).

**A10 — `sample.txt` misplaced** *(Low)*  
Per the naming spec, this should be at `data/extracted_text/R22/COSM/2024_Feb_Regular.txt`. Currently sits in root.

**A11 — Hardcoded Mac path in `pdf_to_txt.py`** *(Medium — breaks on other machines)*  
```python
default="/Users/dareddytanusree/Desktop/WingsAI/questions_P"
```
Should default to `./data/raw_pdfs` per the directory spec.

**A12 — Google Drive folder access** *(Medium)*  
`data_crawling_and_sources.md` embeds a specific Drive folder URL. It's unclear if this is accessible to all 45 contributors or only the team lead.

**A13 — Lean ↔ ML Engine interface undefined** *(Blocking — Backend)*  
`project_overview.md` clarifies that the ML engine scores questions and the Lean backend enforces constraints. But the interface between them is not specified:
- Does Lean read the CSV directly and do its own scoring?
- Or does the ML engine produce a ranked candidate list that Lean receives via IPC?
- If IPC: what protocol — JSON-RPC, stdin/stdout, HTTP?

**A14 — `question_tier` field used in validation but not in schema** *(Medium)*  
`syllabus_parsing_and_tagging_guide.md` Step 4 validation checks `question_tier == 'Short'` and `question_tier == 'Long'`. This field does not appear in the 8-field schema. Is it a 9th field omitted from the table, or is it derived from `part_a_years`/`part_b_years` at query time?

**A15 — Rubrics are not documented anywhere** *(Blocking — Backend)*  
`project_overview.md` gives one example rubric: "should not produce same paper as last year." But the full rubric set (the actual constraints the Lean solver must enforce) is not written down anywhere. The Lean engine cannot be built without a complete, formal rubric specification. Questions that need answers:
- How many Part A questions? How many Part B questions? (sample.txt shows 10+10 structure, 60 marks total — is this universal?)
- Must every unit appear exactly once in Part B?
- What is the anti-collision window — just last year, or last N years?
- Are there marks distribution constraints beyond Part A = 10M, Part B = 50M?
- What does "OR pair" mean structurally — always 2 questions per unit, student picks 1?

**A16 — "13 years" vs "15 years" inconsistency** *(Low)*  
`project_overview.md` says "past few (let us say 13 years)." README says "15-year historical corpus." Which is the actual target corpus size?

---

## Summary Table

| # | Ambiguity | Blocking? | Affects |
|---|---|---|---|
| ~~A1~~ | ~~10 fields vs 8~~ | ~~Resolved~~ | — |
| ~~A2~~ | ~~`regulation` field missing~~ | ~~Resolved~~ | — |
| A3 | `unit_number` decision undocumented | Yes | Backend/Lean |
| A4 | Two scrapers, unclear canonical | Medium | Data |
| A5 | `pypdf` vs `pdfplumber`/`pdftotext` | Medium | Data |
| A6 | No OCR for scanned PDFs | Yes | Data |
| A7 | Bloom level assignment unspecified | Medium | Data/Rubrics |
| A8 | Deduplication criterion undefined | Yes | Data/ML |
| A9 | `scripts/` doesn't exist | Yes | All teams |
| A10 | `sample.txt` misplaced | Low | Data |
| A11 | Hardcoded Mac path in script | Medium | Data |
| A12 | Drive folder access unclear | Medium | Data |
| A13 | Lean ↔ ML Engine interface undefined | Yes | Backend |
| A14 | `question_tier` field status unclear | Medium | Data/Backend |
| A15 | Rubrics not formally documented | Yes | Backend/Rubrics |
| A16 | 13 years vs 15 years corpus size | Low | Data |
