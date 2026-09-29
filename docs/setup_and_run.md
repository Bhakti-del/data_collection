# Setup & Run Instructions

## Prerequisites

- Python 3.8 or above
- Internet connection (first run only — to download the embedding model)

---

## First Time Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd question-paper-predictor
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependency

```bash
pip install sentence-transformers
```

---

## Run the Pipeline

```bash
python run_pipeline.py
```

This runs all 3 steps automatically:

| Step | Script | Output |
|---|---|---|
| 1 | `src/parser.py` | `data/questions_raw.csv` |
| 2 | `src/tagger.py` | `data/questions_tagged.csv`, `data/review_queue.csv` |
| 3 | `src/deduplicator.py` | `output/output.csv` |

---

## Output Files

| File | Description |
|---|---|
| `output/output.csv` | Final dataset — one row per unique question with topic tags, bloom level, marks, and years |
| `data/review_queue.csv` | Questions where auto-tagging confidence was low — review and correct `topic_tag` manually if needed |

---

## Adding a New Subject

1. Open `data/topic_tag_vocabulary.csv`
2. Add rows for your subject following the existing format:

```
subject_name, unit_number, topic_tag, description
Data Structures, 1, LINKED_LIST, "singly linked list doubly linked circular insertion deletion traversal"
Data Structures, 1, STACK, "stack push pop LIFO infix postfix prefix"
...
```

3. Add question paper `.txt` files under:
```
Data/Text_data/All_Reg_QP_Text_data/<regulation>/question papers/<year-sem>/<SUBJECT NAME>/
```

4. Add the subject name mapping in `src/parser.py` under `TARGET_SUBJECTS`:
```python
TARGET_SUBJECTS = {
    "OPERATING SYSTEMS":           "Operating Systems",
    "DATABASE MANAGEMENT SYSTEMS": "Database Management Systems",
    "SOFTWARE ENGINEERING":        "Software Engineering",
    "YOUR SUBJECT NAME":           "Your Subject Name",   # ← add here
}
```

5. Run the pipeline again:
```bash
python run_pipeline.py
```

---

## Notes

- The embedding model (`all-MiniLM-L6-v2`) is downloaded automatically on first run (~80MB)
- Topic embeddings are cached in `data/topic_embeddings.npy` — delete this file if you update `topic_tag_vocabulary.csv`
- `output/output.csv` and all `data/*.csv` generated files are not pushed to the repo — each person generates them locally by running the pipeline
