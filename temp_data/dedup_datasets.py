"""
dedup_datasets.py
Removes semantic duplicate questions from each subject CSV.

Strategy:
  - Within each topic_tag group, find pairs with >60% normalised word overlap
  - Keep the one with more total years (part_a + part_b combined)
  - If tied, keep the longer/more detailed question text
  - Remove the other — write it to <subject>_duplicates_removed.csv

Run:
    python3 dedup_datasets.py
"""

import csv, re, os
from collections import defaultdict

TARGET_FILES = [
    "Artificial_Intelligence_Dataset.csv",
    "Web_Services_SOA_Dataset.csv",
    "Artificial_Neural_Networks_Dataset.csv",
    "Middleware_Technologies_Dataset.csv",
]

FIELDS = ["subject_name", "raw_question_text", "topic_tag", "bloom_level",
          "original_marks", "part_a_years", "part_b_years"]


def normalize(text):
    t = text.lower()
    t = re.sub(r'[^\w\s]', ' ', t)
    stopwords = {
        'a','an','the','in','on','of','to','for','with','and','or','is','are',
        'was','were','by','at','from','its','it','be','as','that','this','which',
        'about','into','how','what','when','where','why','who','suitable','neat',
        'brief','detail','any','one','two','three','each','give','write','state',
        'list','using','explain','describe','discuss','define','short','note',
        'notes','following','example','examples','also','various','different',
        'following','suitable','necessary','following','illustrate'
    }
    words = [w for w in t.split() if w not in stopwords and len(w) > 2]
    return set(words)


def count_years(row):
    """Total number of years a question appeared (part A + part B)."""
    total = 0
    for field in ['part_a_years', 'part_b_years']:
        total += len(re.findall(r'\d{4}', row[field]))
    return total


def pick_winner(r1, r2):
    """Return (keeper, duplicate) based on frequency then length."""
    y1, y2 = count_years(r1), count_years(r2)
    if y1 != y2:
        return (r1, r2) if y1 > y2 else (r2, r1)
    # same frequency → keep longer/more detailed text
    return (r1, r2) if len(r1['raw_question_text']) >= len(r2['raw_question_text']) else (r2, r1)


def merge_years(keeper, dup):
    """Merge years from dup into keeper so no year data is lost."""
    for field in ['part_a_years', 'part_b_years']:
        years_k = set(re.findall(r'\d{4}', keeper[field]))
        years_d = set(re.findall(r'\d{4}', dup[field]))
        merged = sorted(years_k | years_d, key=int)
        keeper[field] = str([int(y) for y in merged]) if merged else '[]'
    return keeper


def deduplicate(rows, threshold=0.60):
    """
    Within each topic_tag, find semantic duplicate pairs and remove the weaker one.
    Returns (clean_rows, removed_rows).
    """
    by_topic = defaultdict(list)
    for r in rows:
        by_topic[r['topic_tag']].append(r)

    to_remove = set()   # indices into original rows list
    row_index = {id(r): i for i, r in enumerate(rows)}

    for topic, topic_rows in by_topic.items():
        for i in range(len(topic_rows)):
            for j in range(i + 1, len(topic_rows)):
                ri, rj = topic_rows[i], topic_rows[j]
                if id(ri) in to_remove or id(rj) in to_remove:
                    continue
                words_i = normalize(ri['raw_question_text'])
                words_j = normalize(rj['raw_question_text'])
                if len(words_i) < 4 or len(words_j) < 4:
                    continue
                overlap = len(words_i & words_j) / max(len(words_i | words_j), 1)
                if overlap >= threshold:
                    keeper, dup = pick_winner(ri, rj)
                    # merge years into keeper before removing dup
                    merge_years(keeper, dup)
                    to_remove.add(id(dup))

    clean_rows  = [r for r in rows if id(r) not in to_remove]
    removed_rows = [r for r in rows if id(r) in to_remove]
    return clean_rows, removed_rows


BASE = os.path.dirname(__file__)

for fname in TARGET_FILES:
    fpath = os.path.join(BASE, fname)
    if not os.path.exists(fpath):
        print(f"[SKIP] {fname} not found")
        continue

    with open(fpath, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))

    original_count = len(rows)
    clean_rows, removed_rows = deduplicate(rows)

    # Overwrite original with deduped version
    with open(fpath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(clean_rows)

    # Write removed duplicates to separate file
    stem = fname.replace('.csv', '')
    dup_path = os.path.join(BASE, f"{stem}_duplicates_removed.csv")
    with open(dup_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(removed_rows)

    print(f"{fname}")
    print(f"  Before: {original_count}  |  After: {len(clean_rows)}  |  Removed: {len(removed_rows)}")
    print(f"  Duplicates saved → {stem}_duplicates_removed.csv")
    print()
