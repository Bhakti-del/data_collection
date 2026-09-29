"""
run_pipeline.py
---------------
Runs the full pipeline in one command:
  Step 1: parser.py       → data/questions_raw.csv
  Step 2: tagger.py       → data/questions_tagged.csv + data/review_queue.csv
  Step 3: deduplicator.py → output/output.csv

Usage:
    python run_pipeline.py

Requirements:
    pip install sentence-transformers
"""

import subprocess
import sys
import time
from pathlib import Path

PYTHON = sys.executable  # uses whichever python is running this script

STEPS = [
    ("Step 1 — Parser",       "src/parser.py"),
    ("Step 2 — Tagger",       "src/tagger.py"),
    ("Step 3 — Deduplicator", "src/deduplicator.py"),
]

def check_requirements():
    missing = []
    if not Path("data/topic_tag_vocabulary.csv").exists():
        missing.append("data/topic_tag_vocabulary.csv  (vocabulary file missing)")
    if not Path("Data/Text_data/All_Reg_QP_Text_data").exists():
        missing.append("Data/Text_data/All_Reg_QP_Text_data  (question paper text files missing)")
    if missing:
        print("ERROR: Required files not found:")
        for m in missing:
            print(f"  - {m}")
        sys.exit(1)

def run_step(label, script):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run([PYTHON, script], capture_output=False)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\nERROR: {label} failed. Pipeline stopped.")
        sys.exit(1)
    print(f"\n  Completed in {elapsed:.1f}s")

def main():
    print("JNTUH Question Paper Predictor — Full Pipeline")
    print("="*60)

    check_requirements()

    total_start = time.time()
    for label, script in STEPS:
        run_step(label, script)

    total = time.time() - total_start
    print(f"\n{'='*60}")
    print(f"  Pipeline complete in {total:.1f}s")
    print(f"  Final output: output/output.csv")
    print(f"  Review queue: data/review_queue.csv")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
