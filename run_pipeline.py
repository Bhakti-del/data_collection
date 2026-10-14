#!/usr/bin/env python3
"""
run_pipeline.py
---------------
Master runner for the Question Paper Predictor data pipeline:
  - Audits all canonical 8-column datasets in data/subjects/
  - Runs modular extraction and normalization pipeline steps
  - Reports dataset coverage and integrity metrics

Usage:
    python3 run_pipeline.py           # Runs dataset audit & integrity check
    python3 run_pipeline.py --audit   # Explicit audit check
    python3 run_pipeline.py --help    # Show pipeline options
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
SUBJECTS_DIR = PROJECT_ROOT / "data" / "subjects"


def run_audit(target_dir: Path | None = None) -> int:
    """Runs the canonical audit test suite across all subject datasets."""
    dir_to_check = target_dir or SUBJECTS_DIR
    audit_script = SCRIPTS_DIR / "audit_datasets.py"
    
    if not audit_script.exists():
        print(f"Error: Audit script not found at {audit_script}")
        return 1

    print(f"\n>> Running dataset integrity audit on: {dir_to_check.relative_to(PROJECT_ROOT)}...")
    result = subprocess.run([sys.executable, str(audit_script), str(dir_to_check)])
    return result.returncode


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Question Paper Predictor — Data Engineering & Dataset Runner"
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        default=True,
        help="Run integrity & quality audit on data/subjects/ (default: True)",
    )
    parser.add_argument(
        "--target-dir",
        type=Path,
        default=SUBJECTS_DIR,
        help="Target directory to audit (default: data/subjects)",
    )

    args = parser.parse_args()

    print("=" * 80)
    print("  Question Paper Predictor — Data Collection & Quality Pipeline")
    print("=" * 80)

    code = run_audit(args.target_dir)
    sys.exit(code)


if __name__ == "__main__":
    main()
