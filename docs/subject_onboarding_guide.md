# Subject Onboarding Guide: Running the Pipeline in Parallel

This guide is an actionable Standard Operating Procedure (SOP) for team members to extract, clean, tag, and verify exam question papers for any subject in parallel.

---

## 1. Prerequisites & Setup

Ensure the following tools are installed on your machine:

```bash
# 1. Install Python dependencies
pip install requests pypdf

# 2. Install and launch Ollama (for local LLM classification)
# Download from https://ollama.com or via terminal on Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 3. Pull the classification model
ollama pull qwen2.5:3b

# 4. Verify Ollama is active
curl http://localhost:11434
# Expected output: "Ollama is running"
```

---

## 2. Directory Layout for a New Subject

When starting a subject (e.g., `Data Structures` or `Operating Systems`):

```
data/
├── raw_pdfs/<Subject>/              # Place raw downloaded PDFs here (if starting from PDF)
├── cleaned_papers/<Reg>/<Subject>/  # Destination for cleaned, boilerplate-free text files
└── syllabi_configs/R22/             # Place R22 syllabus JSON configuration here
```

---

## 3. Step-by-Step Execution Workflow

### Step 1: Create the R22 Syllabus Config

1. Open [`syllabus/R22_CSE_Syllabus.md`](file:///home/slesha/wings-AI/question-paper-predictor/syllabus/R22_CSE_Syllabus.md) and locate your subject.
2. Create `data/syllabi_configs/R22/<Subject>_syllabus.json` with canonical topic names for all 5 units:

```json
{
  "subject_name": "Data Structures",
  "canonical_id": "SUBJECT_DS",
  "regulation": "R22",
  "year": "II",
  "sem": "I",
  "units": {
    "UNIT_1": {
      "name": "Introduction to Data Structures & Arrays",
      "topics": [
        "TIME_AND_SPACE_COMPLEXITY",
        "ARRAY_REPRESENTATION_AND_OPERATIONS",
        "SPARSE_MATRICES",
        "RECURSION_ANALYSIS"
      ]
    },
    "UNIT_2": {
      "name": "Stacks and Queues",
      "topics": [ ... ]
    }
  }
}
```

---

### Step 2: Clean Raw Text Files

Run [`scripts/clean_papers.py`](file:///home/slesha/wings-AI/question-paper-predictor/scripts/clean_papers.py) to strip headers, footers, hall-ticket grids, and fix kerning artifacts:

```bash
python scripts/clean_papers.py \
  --input_dir "Data/Text_data/All_Reg_QP_Text_data" \
  --output_dir "data/cleaned_papers" \
  --regulation "R18"
```

**What this step does:**
- Detects and flags scanned image PDFs (`[SCANNED_IMAGE_DETECTED]`).
- Normalizes Unicode en-dashes (`PART – A` $\to$ `PART - A`).
- Fixes PDF extraction kerning glitches (`p olymorphism` $\to$ `polymorphism`).

---

### Step 3: Segment and Extract Questions into CSV

Run [`scripts/txt_to_csv.py`](file:///home/slesha/wings-AI/question-paper-predictor/scripts/txt_to_csv.py) targeting your subject's cleaned papers:

```bash
python scripts/txt_to_csv.py \
  --subject "Data Structures" \
  --syllabus "data/syllabi_configs/R22/Data_Structures_syllabus.json" \
  --output "data/processed_dataset/ds_master_raw.csv"
```

**What this step does:**
- Atomically splits sub-questions (`2.a` and `2.b` with `[5+5]` marks into separate rows).
- Preserves glued cohesive short notes (`Explain the following: a)... b)... [5+5+5]` into one 10M row).
- Deduplicates repeated questions across years and produces `part_a_years` and `part_b_years`.

---

### Step 4: Run Local LLM Tagging & Verification

Run [`scripts/local_llm_tagger.py`](file:///home/slesha/wings-AI/question-paper-predictor/scripts/local_llm_tagger.py) to verify topic tags and Bloom levels:

```bash
python scripts/local_llm_tagger.py \
  --input_csv "data/processed_dataset/ds_master_raw.csv" \
  --output_csv "data/processed_dataset/ds_master_llm_verified.csv" \
  --syllabus "data/syllabi_configs/R22/Data_Structures_syllabus.json"
```

**Key Features:**
- Automatically resumes from `.tagger_checkpoint.json` if interrupted.
- Enforces strict Bloom cognitive levels (`Apply` for code/algorithms; `Analyze` for comparisons; `Evaluate` for proofs/justifications).
- Routes out-of-syllabus legacy questions to `data/processed_dataset/ds_unmatched_archive.csv`.

---

## 4. Expected Processing Times per Subject

| Step | Operation | CPU (16 threads) | GPU (NVIDIA RTX / CUDA) |
|---|---|---|---|
| Step 1 | Syllabus JSON Creation | ~5 mins (manual) | ~5 mins (manual) |
| Step 2 | Boilerplate Stripping & Cleaning | ~15–30 seconds | ~15–30 seconds |
| Step 3 | Segmentation & Deduplication | ~5–10 seconds | ~5–10 seconds |
| Step 4 | Local LLM Tagging (Ollama 3B) | ~20–30 minutes | ~1–2 minutes |
| **Total** | **End-to-End Pipeline** | **~25–35 minutes** | **~6–8 minutes** |

> [!TIP]
> If running on CPU, the tagger saves checkpoints every 5 questions. Multiple team members can work on different subjects concurrently without CPU contention.

---

## 5. Post-Processing Quality Checklist

Before committing your subject dataset to git:

- [ ] Schema has exactly 7 columns: `subject_name`, `raw_question_text`, `topic_tag`, `bloom_level`, `original_marks`, `part_a_years`, `part_b_years`.
- [ ] No `PART - A` or boilerplate header fragments remain in `raw_question_text`.
- [ ] All `topic_tag` values strictly match the R22 syllabus JSON config.
- [ ] Coding / implementation questions are tagged as `Apply`.
- [ ] Comparison / differentiation questions are tagged as `Analyze`.
- [ ] Any legacy out-of-syllabus questions are isolated in `<subject>_unmatched_archive.csv`.
