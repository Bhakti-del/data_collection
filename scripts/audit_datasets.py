#!/usr/bin/env python3
"""
audit_datasets.py
=================
Automated verification suite to validate all canonical datasets in data/datasets/
against data consistency, Bloom's taxonomy calibration, schema compliance,
and syllabus rules.
"""

import os
import sys
import csv
import re
from pathlib import Path
from collections import defaultdict

VALID_BLOOMS = {'Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate'}
EXPECTED_COLUMNS = [
    "subject_name", "raw_question_text", "topic_tag",
    "bloom_level", "original_marks", "part_a_years", "part_b_years"
]

def parse_years(ystr):
    if isinstance(ystr, list):
        return sorted(list(set(int(y) for y in ystr)))
    years = re.findall(r'\b\d{4}\b', str(ystr))
    return sorted(list(set(int(y) for y in years)))

def normalize_text_for_dedup(qtext):
    s = qtext.lower().strip()
    s = re.sub(r'[\s_]+', ' ', s)
    s = s.strip(' ?.:,;')
    return s

def audit_directory(dir_path: Path):
    if not dir_path.exists():
        print(f"Error: Directory {dir_path} does not exist.")
        return 1

    csv_files = sorted(list(dir_path.glob("*.csv")))
    if not csv_files:
        print(f"Error: No CSV files found in {dir_path}.")
        return 1

    print("=" * 80)
    print(f"CANONICAL DATASET INTEGRITY & QUALITY AUDIT: {dir_path}")
    print("=" * 80)

    total_records = 0
    total_violations = 0
    results = []

    for fpath in csv_files:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            reader = list(csv.reader(f))
        
        if not reader:
            print(f"  [FAIL] {fpath.name:45s} : Empty file!")
            total_violations += 1
            continue

        header = reader[0]
        rows = reader[1:]
        total_records += len(rows)

        # 1. Header check
        header_err = header != EXPECTED_COLUMNS
        
        # Row audits
        schema_errs = 0
        bloom_errs = 0
        mark_errs = 0
        stem_errs = 0
        year_errs = 0
        dupes = defaultdict(list)

        for idx, r in enumerate(rows):
            if len(r) != 7:
                schema_errs += 1
                continue
            
            subj, qtext, topic, bloom, marks_str, pa_str, pb_str = r

            # Bloom check
            if bloom not in VALID_BLOOMS:
                bloom_errs += 1

            # Marks check
            try:
                m = int(marks_str)
            except ValueError:
                m = 0
                mark_errs += 1

            # Year parse
            pa = parse_years(pa_str)
            pb = parse_years(pb_str)
            if not pa and not pb:
                year_errs += 1

            # Part inversion check (Part A <= 3M, Part B >= 5M)
            if m <= 3 and pb and not pa:
                mark_errs += 1
            elif m >= 8 and pa and not pb:
                mark_errs += 1

            # Severed stem check
            if re.search(r'^(?:explain|define|discuss|write|describe|trace|give|consider|state)\s+(?:the following|any|each of the following|the following terms)[\s:]*$', qtext.strip(), re.I):
                stem_errs += 1

            norm = normalize_text_for_dedup(qtext)
            dupes[(topic, norm)].append(idx)

        dupe_errs = sum(1 for v in dupes.values() if len(v) > 1)
        sub_violations = (1 if header_err else 0) + schema_errs + bloom_errs + mark_errs + stem_errs + year_errs + dupe_errs
        total_violations += sub_violations

        status = "PASSED (0 defects)" if sub_violations == 0 else f"ISSUES: schema={schema_errs}, bloom={bloom_errs}, marks={mark_errs}, stems={stem_errs}, dupes={dupe_errs}"
        print(f"  {fpath.name:45s} | {len(rows):3d} rows | {status}")
        results.append((fpath.name, len(rows), sub_violations))

    print("=" * 80)
    print(f"AUDIT SUMMARY: {len(csv_files)} datasets checked | {total_records} total rows | {total_violations} defects found.")
    print("=" * 80)

    return total_violations

if __name__ == "__main__":
    target_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/datasets")
    exit_code = audit_directory(target_dir)
    sys.exit(0 if exit_code == 0 else 1)
