"""
extract_images.py
-----------------
Automated diagram and figure extraction from JNTUH question paper PDFs.

Features:
  - Robust text-to-PDF matching resilient to whitespace, line breaks, and punctuation.
  - Automatically maps cleaned text questions to original source PDFs across regulations (R13, R15, R16, R18, R22).
  - Intelligent diagram crop with watermark/stamp filtering and cross-page figure handling.
  - Generates structured datasets matching data/datasets_with_images/ schema:
      subject_name, raw_question_text, topic_tag, bloom_level,
      original_marks, part_a_years, part_b_years, image_path
  - Validates cropped images to exclude whitespace or non-diagram noise.

Usage:
    # Run across all R13 regulation question papers and output to datasets_with_images:
    python scripts/extract_images.py --regulation R13

    # Run on a single paper:
    python scripts/extract_images.py --paper "July-2021" --subject "ENGINEERING DRAWING"

    # Run on a specific subject:
    python scripts/extract_images.py --subject "BASIC ELECTRICAL ENGINEERING" --regulation R13
"""

from __future__ import annotations

import os
import re
import csv
import json
import argparse
from pathlib import Path

try:
    import pymupdf
except ImportError:
    raise ImportError("PyMuPDF is required. Install it using: pip install pymupdf")


# -- PATH RESOLUTION ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

TEXT_DIRS = [
    PROJECT_ROOT / "temp_data" / "cleaned_papers",
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data",
    PROJECT_ROOT / "Datafiles" / "Text_data" / "All_Reg_QP_Text_data",
]
TEXT_BASE = next((d for d in TEXT_DIRS if d.exists()), None)

PDF_DIRS = [
    PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_PDF_data",
    PROJECT_ROOT / "Datafiles" / "Text_data" / "All_Reg_QP_PDF_data",
]


def get_pdf_base() -> Path | None:
    for d in PDF_DIRS:
        if d.exists() and any(d.rglob("*.pdf")):
            return d
    for d in PDF_DIRS:
        if d.exists():
            return d
    return None


PDF_BASE = get_pdf_base()

DEFAULT_IMG_OUT = PROJECT_ROOT / "data" / "images"
DEFAULT_CSV_OUT = PROJECT_ROOT / "data" / "datasets_with_images" / "R13_Dataset_with_images.csv"
DATASETS_IMG_DIR = PROJECT_ROOT / "data" / "datasets_with_images"


# -- PATTERNS ----------------------------------------------------------------

IMAGE_TRIGGERS = re.compile(
    r"(?:shown\s+in\s+(?:the\s+)?(?:fig(?:ure)?|circuit|graph|diagram|network)|"
    r"shown\s+below|"
    r"given\s+in\s+(?:the\s+)?(?:fig(?:ure)?|circuit|graph|diagram|network)|"
    r"given\s+circuit|given\s+graph|given\s+network|"
    r"(?:given|below)\s+(?:the\s+)?fig(?:ure)?|"
    r"fig(?:ure)?\s+below|"
    r"refer\s+(?:to\s+)?(?:the\s+)?(?:fig(?:ure)?|diagram)|"
    r"see\s+fig(?:ure)?|"
    r"for\s+the\s+circuit\s+shown|"
    r"following\s+(?:circuit|graph|diagram|figure|network)|"
    r"\bfig(?:ure)?\.?\s*[:\s]?\s*\d+|"
    r"from\s+fig(?:ure)?\.?\s*\d+)",
    re.IGNORECASE
)

FIGURE_LABEL_PATTERN = re.compile(
    r"(Figure\s*[:\.]?\s*\d+)",
    re.IGNORECASE
)

BLOOM_VERBS = {
    "Evaluate":   ["evaluate", "justify", "assess", "critique", "recommend", "support or oppose"],
    "Analyze":    ["analyze", "analyse", "compare", "differentiate", "distinguish", "derive",
                   "examine", "contrast", "determine", "trace"],
    "Apply":      ["write", "implement", "construct", "solve", "perform", "compute", "calculate",
                   "show", "demonstrate", "apply", "develop", "design", "draw", "find",
                   "obtain", "simulate", "convert", "estimate"],
    "Understand": ["explain", "describe", "discuss", "summarize", "interpret", "classify",
                   "illustrate", "give an example", "how does", "what happens"],
    "Remember":   ["define", "list", "state", "name", "identify", "what is", "what are",
                   "mention", "recall", "label"],
}


# -- HELPERS -----------------------------------------------------------------

def normalize_text(text: str) -> str:
    """Removes non-alphanumeric characters and standardizes spaces for robust matching."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def infer_bloom(text: str) -> str:
    t = text.lower()
    for level in ("Evaluate", "Analyze", "Apply", "Understand", "Remember"):
        if any(verb in t for verb in BLOOM_VERBS[level]):
            return level
    return "Understand"


def parse_year(filename: str) -> int | None:
    m = re.search(r"(\d{4})", filename)
    return int(m.group(1)) if m else None


def clean_question_text(text: str) -> str:
    """Cleans question text, stripping question prefixes, trailing figure captions, matrices, and fixing OCR errors."""
    # 1. Truncate at marks bracket if present in the text line (e.g. [10], [5+5], [15])
    m_marks = re.search(r"\[\s*\d+(?:\s*[\+]\s*\d+)*\s*\]", text)
    if m_marks:
        before = text[:m_marks.start()].strip()
        after = text[m_marks.end():].strip()
        # Keep valid question continuation text after marks (e.g. 'Find: i)...', 'All dimensions are in mm')
        # but discard figure captions (Figure 1, Graph 1) or matrix/data tables
        if after and not re.match(r"^(?:Figure|Fig|Graph)\s*[:.]?\s*\d+", after, re.I):
            words = after.split()
            num_count = sum(1 for w in words if re.match(r"^[\d\.,\(\)\[\]]+$", w))
            if num_count / max(1, len(words)) < 0.4:
                text = before + " " + after
            else:
                text = before
        else:
            text = before

    # 2. Strip leading headers, Part A/B, JNTUH, Question numbers
    text = re.split(r"\bPART\s*[-–]?\s*[AB]\b", text, flags=re.IGNORECASE)[0]
    text = re.split(r"\bJNTUH\b", text, flags=re.IGNORECASE)[0]
    text = re.sub(r"\bR1[0-9]\b", " ", text)
    text = re.sub(r"^\s*\d+[\.\)]\s*(?:[a-z][\.\)])?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[a-z][\.\)]\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\s*[\)\.\-]\s*", "", text)

    # 3. Strip trailing figure labels/captions
    text = re.sub(r"\s*(?:Figure|Fig|Graph)\s*[:.]?\s*\d+\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\((?:Figure|Fig|Graph)\s*[:.]?\s*\d+\)\.?\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*(?:Figure|Fig|Graph)\s*[:.]?\s*\d+\s*$", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*\bOR\b\s*$", "", text, flags=re.IGNORECASE)

    # 4. Remove unicode private-use characters & matrix symbols
    text = re.sub(r"[\uf000-\uf8ff]", "", text)

    # 5. Fix common OCR split-word and typo errors
    word_fixes = [
        (r"\bt he\b", "the"),
        (r"\bc urrent\b", "current"),
        (r"\bpow er\b", "power"),
        (r"\ba lgorithm\b", "algorithm"),
        (r"\bFig ure\b", "Figure"),
        (r"\bt o\b", "to"),
        (r"\btransforma tion\b", "transformation"),
        (r"\bSuper position\b", "Superposition"),
        (r"\bSuper\s+position\b", "Superposition"),
        (r"\bThevinin\b", "Thevenin"),
        (r"\bkrushkal\b", "Kruskal"),
        (r"\bPrime\'s algorithm\b", "Prim's algorithm"),
        (r"\bFinite Automate\b", "Finite Automata"),
        (r"\bFinite Automaton[’\']s\b", "Finite Automata"),
        (r"\bFinite Automaton\(FA\)\b", "Finite Automaton (FA)"),
    ]
    for pattern, repl in word_fixes:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)

    # 6. Specific cleanup for double FA label artifact
    text = re.sub(r"Figure:\s*3\s*", "", text)
    text = re.sub(
        r"Finite Automaton \(FA\) 1 \(figure 3\):\s*Finite Automaton \(FA\) 2\(figure 4\):?",
        "Finite Automaton 1 (figure 3) and Finite Automaton 2 (figure 4).",
        text,
        flags=re.IGNORECASE
    )

    # 7. Normalize whitespace and punctuation spacing
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,\.:;\?\)])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)

    # Convert trailing colon to period if it's not introducing an enumerated list
    if text.endswith(":") and not re.search(r"\b(?:find|calculate|determine)\s*:$", text, re.I):
        text = text[:-1] + "."

    # 8. Ensure trailing period if sentence ends without punctuation
    if text and text[-1] not in (".", "?", ":", ";", "!"):
        text += "."

    return text


def extract_marks(q_text: str) -> int | None:
    """Extracts marks from brackets anywhere in a question text, e.g. [15] or [7+8]."""
    m = re.search(r"\[\s*(\d+(?:\s*[\+]\s*\d+)*)\s*\]", q_text)
    if not m:
        return None
    return sum(int(x) for x in re.split(r"\s*[\+]\s*", m.group(1)))


def get_paper_marks(questions: list[dict]) -> dict[str, int]:
    """Calculates paper-wide marks mapping so subquestions inherit the split component marks."""
    marks: dict[str, int] = {}
    groups: dict[str, list[dict]] = {}
    for q in questions:
        groups.setdefault(q["q_no"].split(".")[0], []).append(q)

    bracket = re.compile(r"\[\s*(\d+(?:\s*[\+]\s*\d+)*)\s*\]")
    for main_no, group in groups.items():
        explicit = {q["q_no"]: extract_marks(q["text"]) for q in group}
        if all(v is not None for v in explicit.values()):
            marks.update(explicit)
            continue
        components: list[int] = []
        for q in group:
            m = bracket.search(q["text"])
            if m:
                components = [int(x) for x in re.split(r"\s*[\+]\s*", m.group(1))]
        if components and len(components) == len(group):
            for q, component in zip(group, components):
                marks[q["q_no"]] = component
        elif components:
            per = max(1, round(sum(components) / len(group)))
            for q in group:
                marks[q["q_no"]] = per
        else:
            for q_no, v in explicit.items():
                marks[q_no] = v if v is not None else 10
    return marks


def tag_question(subj: str, text: str) -> str:
    """Tags question strictly matching JNTUH syllabus units."""
    t = text.lower()
    if "electrical" in subj.lower():
        if "transformer" in t:
            return "IDEAL_AND_PRACTICAL_TRANSFORMER"
        if "thevenin" in t or "thevinin" in t:
            return "THEVENINS_THEOREM"
        if "super" in t and "position" in t:
            return "SUPERPOSITION_THEOREM"
        if "star" in t and "delta" in t:
            return "STAR_DELTA_TRANSFORMATION"
        if "rms" in t or "average value" in t or "periodic function" in t or "waveform" in t or "form factor" in t:
            return "RMS_AND_AVERAGE_VALUES"
        if "kirchhoff" in t:
            return "KIRCHHOFFS_LAWS"
        if "capacit" in t:
            return "CAPACITORS_AND_INDUCTORS"
        return "ELECTRICAL_QUANTITIES_AND_OHMS_LAW"

    if "drawing" in subj.lower():
        if "isometric view" in t or "isometric projection" in t:
            if "orthographic" in t or "projections are given" in t or "views of a solid" in t:
                return "ORTHOGRAPHIC_TO_ISOMETRIC_PROJECTION"
            return "ISOMETRIC_PROJECTIONS"
        if "orthographic" in t or "front view" in t or "top view" in t or "side view" in t or "first angle" in t:
            return "ORTHOGRAPHIC_PROJECTIONS"
        return "ENGINEERING_DRAWING_PROJECTIONS"

    if "formal languages" in subj.lower() or "flat" in subj.lower():
        if "minimiz" in t:
            return "MINIMIZATION_OF_FINITE_AUTOMATA"
        if "nfa" in t and "dfa" in t:
            return "NFA_TO_DFA_EQUIVALENCE"
        if "regular expression" in t or "arden" in t or "regular grammar" in t:
            return "FINITE_AUTOMATA_AND_REGULAR_EXPRESSIONS"
        if "equivalent" in t:
            return "EQUIVALENCE_OF_FINITE_AUTOMATA"
        return "FINITE_AUTOMATA"

    if "mathematical foundations" in subj.lower() or "mfcs" in subj.lower():
        if "chromatic" in t or "color" in t:
            return "CHROMATIC_NUMBER_AND_GRAPH_COLORING"
        if "hamilton" in t:
            return "HAMILTONIAN_CYCLES_AND_PATHS"
        if "euler" in t:
            return "EULER_CIRCUITS_AND_PATHS"
        if "isomorphic" in t or "isomorphism" in t:
            return "GRAPH_ISOMORPHISM"
        if "dual" in t:
            return "PLANAR_AND_DUAL_GRAPHS"
        if "kruskal" in t or "prime" in t or "spanning" in t:
            return "MINIMAL_SPANNING_TREES"
        if "shortest path" in t:
            return "SHORTEST_PATH_IN_GRAPHS"
        return "GRAPH_THEORY"

    if "algorithms" in subj.lower() or "daa" in subj.lower():
        if "kruskal" in t or "prim" in t or "mcst" in t or "spanning" in t:
            return "MINIMUM_COST_SPANNING_TREES"
        if "shortest path" in t or "all pairs" in t or "single source" in t:
            if "all pairs" in t:
                return "ALL_PAIRS_SHORTEST_PATH"
            return "SINGLE_SOURCE_SHORTEST_PATH"
        if "tour" in t or "tsp" in t or "travelling" in t:
            return "TRAVELLING_SALESPERSON_PROBLEM"
        if "traversal" in t or "bfs" in t or "dfs" in t:
            return "GRAPH_TRAVERSALS"
        return "GRAPH_ALGORITHMS"

    if "data structures" in subj.lower():
        if "bfs" in t or "dfs" in t or "traversal" in t:
            return "GRAPH_TRAVERSALS_BFS_DFS"
        return "GRAPHS_AND_REPRESENTATIONS"

    if "electronic devices" in subj.lower() or "edc" in subj.lower():
        if "circuit" in t or "vcc" in t or "rb" in t or "rc" in t or "β" in t:
            return "TRANSISTOR_BIASING_AND_STABILIZATION"
        return "BIPOLAR_JUNCTION_TRANSISTORS"

    return "GENERAL"


def is_valid_diagram_pix(pix: pymupdf.Pixmap) -> bool:
    """Validates that a cropped pixmap has genuine drawing pixels and is not whitespace/noise."""
    if not pix or pix.height < 70 or pix.width < 100:
        return False
    samples = pix.samples
    non_white = sum(1 for i in range(0, len(samples), pix.n) if any(samples[i + c] < 240 for c in range(3)))
    ratio = non_white / (pix.width * pix.height)
    return ratio >= 0.01


def find_pdf_for_txt(txt_path: Path) -> Path | None:
    """Finds the corresponding PDF for a text file across all regulation folders."""
    pdf_base = get_pdf_base()
    if not pdf_base or not pdf_base.exists():
        return None

    # Check relative path from 'question papers' subfolder
    parts = list(txt_path.parts)
    lower_parts = [p.lower() for p in parts]
    if "question papers" in lower_parts:
        idx = lower_parts.index("question papers")
        qp_subpath = Path(*parts[idx:]).with_suffix(".pdf")
        for reg_dir in pdf_base.iterdir():
            if reg_dir.is_dir():
                cand = reg_dir / qp_subpath
                if cand.exists():
                    return cand

    # Match by stem & subject
    stem = txt_path.stem
    subject = txt_path.parent.name
    matches = list(pdf_base.rglob(f"{stem}.pdf"))
    if not matches:
        return None

    same_subj = [
        p for p in matches
        if p.parent.name.lower().replace("_", " ") == subject.lower().replace("_", " ")
    ]
    return same_subj[0] if same_subj else matches[0]


def parse_questions_from_text(text: str) -> list[dict]:
    """Splits question paper text into individual questions with their metadata."""
    lines = text.splitlines()
    questions = []
    current_q_num = None
    current_text = []
    current_is_stem = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        low = stripped.lower()
        if any(h in low for h in [
            "hall ticket", "roll no", "jawaharlal nehru technological",
            "time: 3 hours", "time: 2 hours", "max marks", "max. marks", "note:",
            "answer any five", "part-a", "part-b", "---oo", "code no",
            "jntuh", "-ooooo-", "--ooo--"
        ]):
            continue
        if re.fullmatch(r"or", low) or re.fullmatch(r"\(\s*\d+\s*marks\s*\)", low):
            continue
        if re.fullmatch(r"part\s*[\-–]?\s*[ab]\b.*", low) or re.fullmatch(r"r1[0-9](\s*[/,]?\s*r1[0-9])*", low):
            continue
        if re.match(r"^\d{2}[\-/]\d{2}[\-/]\d{4}", low):
            continue

        m = re.match(r"^\s*(\d+)[\.\)]\s*(?:([a-h]|j)\))?", stripped, re.IGNORECASE)
        m_sub = re.match(r"^\s*([a-h]|j)\)\s+", stripped, re.IGNORECASE)
        is_roman = re.match(r"^\s*(?:i|ii|iii|iv|v|vi)\)\s+", stripped, re.IGNORECASE)

        if m and m.group(1):
            if current_text and current_q_num:
                questions.append({
                    "q_no": current_q_num,
                    "text": " ".join(current_text)
                })
            q_main = m.group(1)
            q_sub = f".{m.group(2)}" if m.group(2) else ""
            current_q_num = f"{q_main}{q_sub}"
            current_text = [stripped]
            current_is_stem = False
        elif m_sub and current_q_num:
            joined_so_far = " ".join(current_text).strip()
            if not current_is_stem:
                current_is_stem = (
                    "." not in current_q_num
                    and (joined_so_far.endswith(":") or joined_so_far.lower().endswith("find:"))
                    and not re.search(r"\[\s*\d+", joined_so_far)
                )
            if current_is_stem:
                current_text.append(stripped)
            else:
                if current_text:
                    questions.append({
                        "q_no": current_q_num,
                        "text": joined_so_far
                    })
                main_digit = current_q_num.split(".")[0]
                current_q_num = f"{main_digit}.{m_sub.group(1)}"
                current_text = [stripped]
        else:
            if current_text:
                current_text.append(stripped)

    if current_text and current_q_num:
        questions.append({
            "q_no": current_q_num,
            "text": " ".join(current_text)
        })

    return questions


def crop_diagram_for_question(
    doc_or_page: pymupdf.Document | pymupdf.Page,
    q_text: str,
    q_no: str = "",
    zoom: float = 2.0
) -> tuple[pymupdf.Pixmap | None, str]:
    """
    Crops the diagram region for a question.
    Accepts either a pymupdf.Page or pymupdf.Document.
    When passed a Document, intelligently scans for the best page and supports
    cross-page diagram overflow.
    """
    q_words = [w for w in re.findall(r"[a-zA-Z0-9]+", q_text.lower()) if len(w) > 3]
    if not q_words:
        return None, ""

    main_q = q_no.split(".")[0] if q_no else ""

    doc = None
    page = None
    best_page_idx = -1

    if isinstance(doc_or_page, pymupdf.Document):
        doc = doc_or_page
        best_score = 0
        for idx, p in enumerate(doc):
            p_text = p.get_text().lower()
            score = sum(1 for w in q_words if w in p_text)
            if main_q and re.search(rf"\b{main_q}[\.\)]", p_text):
                score += 3
            if score > best_score:
                best_score = score
                page = p
                best_page_idx = idx
        if not page or best_score < 2:
            return None, ""
    else:
        page = doc_or_page
        doc = page.parent
        best_page_idx = page.number

    raw_blocks = page.get_text("blocks")
    blocks = []
    for b in raw_blocks:
        if b[6] != 0 or (b[2] - b[0] <= 45):
            continue
        text_clean = b[4].strip().lower()
        if "jntuh used" in text_clean or (b[3] - b[1] > 300 and "jntuh" in text_clean):
            continue
        blocks.append(b)

    blocks.sort(key=lambda b: b[1])

    best_idx = None
    best_score = 0
    for idx, b in enumerate(blocks):
        b_clean = re.sub(r"\s+", " ", b[4]).lower()
        score = sum(1 for w in q_words if w in b_clean)
        if main_q and re.search(rf"\b{main_q}[\.\)]", b_clean):
            score += 3
        if score > best_score:
            best_score = score
            best_idx = idx

    if best_idx is None or best_score < 2:
        return None, ""

    # Advance while subsequent blocks are continuation of the question text
    curr_idx = best_idx
    while curr_idx + 1 < len(blocks):
        next_candidate = blocks[curr_idx + 1]
        gap_to_next = next_candidate[1] - blocks[curr_idx][3]
        if gap_to_next < 15 and not re.match(r"^\s*(?:[a-z]\)|\d+[\.\)]|figure|---)", next_candidate[4], re.I):
            curr_idx += 1
        else:
            break

    matched_b = blocks[curr_idx]
    y_start = matched_b[3] + 2

    fig_label = ""
    y_end = page.rect.y1 - 40

    if curr_idx + 1 < len(blocks):
        next_b = blocks[curr_idx + 1]
        next_text = next_b[4]
        m_fig = FIGURE_LABEL_PATTERN.search(next_text)
        if m_fig:
            fig_label = m_fig.group(1)
            y_end = next_b[1] + 25
            if next_b[3] - next_b[1] < 40:
                y_end = next_b[3] + 2
        else:
            y_end = next_b[1] - 2

    gap = y_end - y_start
    pix = None

    if gap >= 25:
        x0 = max(page.rect.x0 + 40, 40)
        x1 = min(page.rect.x1 - 40, page.rect.width - 40)
        clip_rect = pymupdf.Rect(x0, y_start, x1, y_end)
        candidate_pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip_rect)
        if is_valid_diagram_pix(candidate_pix):
            pix = candidate_pix

    # Cross-page fallback: check top of next page if diagram was placed there
    if not pix and doc and best_page_idx + 1 < len(doc):
        next_page = doc[best_page_idx + 1]
        next_raw_blocks = [
            b for b in next_page.get_text("blocks")
            if b[6] == 0 and "jntuh" not in b[4].lower() and (b[2] - b[0] > 45)
        ]
        next_raw_blocks.sort(key=lambda b: b[1])
        if next_raw_blocks:
            top_b = next_raw_blocks[0]
            m_fig = FIGURE_LABEL_PATTERN.search(top_b[4])
            if m_fig and top_b[1] < 250:
                fig_label = m_fig.group(1)
                y_end_next = top_b[3] + 2
                x0 = max(next_page.rect.x0 + 40, 40)
                x1 = min(next_page.rect.x1 - 40, next_page.rect.width - 40)
                clip_rect = pymupdf.Rect(x0, 40, x1, y_end_next)
                candidate_pix = next_page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), clip=clip_rect)
                if is_valid_diagram_pix(candidate_pix):
                    pix = candidate_pix

    return pix, fig_label


# -- MAIN EXTRACTION ---------------------------------------------------------

def process_paper(txt_path: Path, img_out_dir: Path) -> list[dict]:
    """Processes a single paper: crops all diagrams and returns structured question rows."""
    pdf_path = find_pdf_for_txt(txt_path)
    if not pdf_path or not pdf_path.exists():
        print(f"[!] No matching PDF found for: {txt_path.name}")
        return []

    content = txt_path.read_text(encoding="utf-8", errors="ignore")
    questions = parse_questions_from_text(content)
    paper_marks = get_paper_marks(questions)
    subject = txt_path.parent.name
    subject_slug = re.sub(r"[^A-Za-z0-9]", "_", subject.upper())[:15]
    stem = txt_path.stem

    rows = []
    doc = pymupdf.open(str(pdf_path))

    for idx, q in enumerate(questions):
        q_no = q["q_no"]
        q_text = q["text"]
        has_diagram = bool(IMAGE_TRIGGERS.search(q_text))
        img_filename = ""
        fig_label = ""

        if has_diagram:
            pix, fig_label = crop_diagram_for_question(doc, q_text, q_no)
            if pix:
                clean_q_tag = q_no.replace(".", "_")
                img_filename = f"{subject_slug}_{stem}_Q{clean_q_tag}.png"
                img_path = img_out_dir / img_filename
                pix.save(str(img_path))
                print(f"  [+] Cropped Diagram for Q{q_no}: {img_filename} {f'({fig_label})' if fig_label else ''}")

        marks = paper_marks.get(q_no) or extract_marks(q_text)
        raw_clean = clean_question_text(q_text)

        rows.append({
            "subject_name": subject,
            "question_no": q_no,
            "raw_question_text": raw_clean,
            "original_marks": marks if marks else "",
            "has_diagram": bool(img_filename),
            "image_path": str(Path("data/images") / img_filename) if img_filename else "",
            "figure_label": fig_label,
            "source_pdf": pdf_path.name,
        })

    doc.close()
    return rows


def build_regulation_dataset(
    regulation: str = "R13",
    subject_filter: str | None = None,
    paper_filter: str | None = None,
    img_out_dir: Path = DEFAULT_IMG_OUT,
    csv_out_path: Path = DEFAULT_CSV_OUT,
    write_per_subject: bool = False
) -> None:
    """
    Builds the dataset with images for all subjects and papers under the specified regulation.
    Schema matches data/datasets_with_images/Basic_Electrical_Engineering_R15_Dataset.csv:
        subject_name, raw_question_text, topic_tag, bloom_level,
        original_marks, part_a_years, part_b_years, image_path
    """
    img_out_dir.mkdir(parents=True, exist_ok=True)
    csv_out_path.parent.mkdir(parents=True, exist_ok=True)

    # Locate regulation text folders
    cand_dirs = [
        PROJECT_ROOT / "temp_data" / "cleaned_papers" / f"{regulation}_text" / "question papers",
        PROJECT_ROOT / "temp_data" / "Text_data" / "All_Reg_QP_Text_data" / f"{regulation}_text" / "question papers",
    ]
    reg_root = next((d for d in cand_dirs if d.exists()), None)
    if not reg_root:
        print(f"[ERROR] Could not find text root for regulation {regulation}.")
        return

    txt_files = sorted(list(reg_root.rglob("*.txt")))
    if subject_filter:
        txt_files = [f for f in txt_files if subject_filter.lower() in f.parent.name.lower()]
    if paper_filter:
        txt_files = [f for f in txt_files if paper_filter.lower() in f.stem.lower()]

    print(f"\nProcessing {len(txt_files)} papers for {regulation} regulation...")

    dataset_by_subject: dict[str, dict[str, dict]] = {}
    all_combined: dict[tuple[str, str], dict] = {}
    total_cropped = 0

    for txt_path in txt_files:
        pdf_path = find_pdf_for_txt(txt_path)
        if not pdf_path or not pdf_path.exists():
            continue

        content = txt_path.read_text(encoding="utf-8", errors="ignore")
        questions = parse_questions_from_text(content)

        if not any(IMAGE_TRIGGERS.search(q["text"]) for q in questions):
            continue

        subject = txt_path.parent.name
        if subject.upper() in [
            "MANAGERIAL ECONOMICS AND FINANCIAL ANALYSIS",
            "PROBABILITY AND STATISTICS",
            "MANAGEMENT SCIENCE",
        ]:
            continue
        paper_marks = get_paper_marks(questions)
        subject_slug = re.sub(r"[^A-Za-z0-9]", "_", subject.upper())[:15]
        stem = txt_path.stem
        year = parse_year(stem)
        has_part_a = bool(re.search(r"PART\s*[-–]?\s*A\b", content, re.IGNORECASE))

        doc = pymupdf.open(str(pdf_path))

        for q in questions:
            q_no = q["q_no"]
            q_text = q["text"]
            if not IMAGE_TRIGGERS.search(q_text):
                continue

            pix, fig_label = crop_diagram_for_question(doc, q_text, q_no)
            if not pix:
                continue

            clean_q_tag = q_no.replace(".", "_")
            img_filename = f"{subject_slug}_{stem}_Q{clean_q_tag}.png"
            img_path = img_out_dir / img_filename
            pix.save(str(img_path))
            total_cropped += 1
            print(f"  [+] Cropped Diagram ({subject} - {stem} Q{q_no}): {img_filename}")

            raw_clean = clean_question_text(q_text)
            if len(raw_clean) < 10:
                continue

            marks = paper_marks.get(q_no) or extract_marks(q_text)
            main_q = q_no.split(".")[0]
            part = "A" if (has_part_a and main_q == "1") or (marks and marks <= 3) else "B"

            key = re.sub(r"[^a-z0-9]", "", raw_clean.lower())
            topic = tag_question(subject, raw_clean)
            bloom = infer_bloom(raw_clean)

            subj_data = dataset_by_subject.setdefault(subject, {})
            if key not in subj_data:
                subj_data[key] = {
                    "subject_name": subject.title(),
                    "raw_question_text": raw_clean,
                    "topic_tag": topic,
                    "bloom_level": bloom,
                    "original_marks": marks if marks is not None else "",
                    "part_a_years": set(),
                    "part_b_years": set(),
                    "image_path": f"data/images/{img_filename}",
                }

            if year:
                (subj_data[key]["part_a_years"] if part == "A" else subj_data[key]["part_b_years"]).add(year)
            if subj_data[key]["original_marks"] in ("", None) and marks:
                subj_data[key]["original_marks"] = marks

            comb_key = (subject, key)
            if comb_key not in all_combined:
                all_combined[comb_key] = {
                    "subject_name": subject.title(),
                    "raw_question_text": raw_clean,
                    "topic_tag": topic,
                    "bloom_level": bloom,
                    "original_marks": marks if marks is not None else "",
                    "part_a_years": set(),
                    "part_b_years": set(),
                    "image_path": f"data/images/{img_filename}",
                }
            if year:
                (all_combined[comb_key]["part_a_years"] if part == "A" else all_combined[comb_key]["part_b_years"]).add(year)
            if all_combined[comb_key]["original_marks"] in ("", None) and marks:
                all_combined[comb_key]["original_marks"] = marks

        doc.close()

    fieldnames = [
        "subject_name", "raw_question_text", "topic_tag", "bloom_level",
        "original_marks", "part_a_years", "part_b_years", "image_path"
    ]

    def to_row(rec: dict) -> dict:
        return {
            "subject_name": rec["subject_name"],
            "raw_question_text": rec["raw_question_text"],
            "topic_tag": rec["topic_tag"],
            "bloom_level": rec["bloom_level"],
            "original_marks": rec["original_marks"],
            "part_a_years": sorted(rec["part_a_years"]),
            "part_b_years": sorted(rec["part_b_years"]),
            "image_path": rec["image_path"],
        }

    # 1. Write the combined dataset
    with open(csv_out_path, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        for rec in all_combined.values():
            writer.writerow(to_row(rec))

    # 2. Optionally write per-subject datasets into datasets_with_images/
    if write_per_subject:
        for subj, records in dataset_by_subject.items():
            slug = re.sub(r"[^A-Za-z0-9]+", "_", subj.title()).strip("_")
            subj_csv = DATASETS_IMG_DIR / f"{slug}_{regulation}_Dataset.csv"
            with open(subj_csv, "w", newline="", encoding="utf-8") as fp:
                writer = csv.DictWriter(fp, fieldnames=fieldnames)
                writer.writeheader()
                for rec in records.values():
                    writer.writerow(to_row(rec))
            print(f"  -> Wrote subject dataset: {subj_csv.name} ({len(records)} questions)")

    print(f"\n{'='*60}")
    print(f"Regulation               : {regulation}")
    print(f"Diagrams Extracted       : {total_cropped}")
    print(f"Unique Questions with Img: {len(all_combined)}")
    print(f"Main Combined CSV        : {csv_out_path}")
    print(f"Per-Subject Directory    : {DATASETS_IMG_DIR}")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Extract diagrams and generate structured dataset with image paths.")
    parser.add_argument("--paper", type=str, help="Specific paper stem to process (e.g., 'March-2021')")
    parser.add_argument("--subject", type=str, help="Filter by subject folder name")
    parser.add_argument("--regulation", type=str, default="R13", help="Regulation filter (e.g., 'R13', 'R15')")
    parser.add_argument("--all", action="store_true", help="Process all available papers")
    parser.add_argument("--img_out", type=Path, default=DEFAULT_IMG_OUT, help="Directory to save cropped images")
    parser.add_argument("--csv_out", type=Path, default=DEFAULT_CSV_OUT, help="Path for output dataset CSV")
    parser.add_argument("--per_subject", action="store_true", default=False, help="Write per-subject datasets as well")

    args = parser.parse_args()

    build_regulation_dataset(
        regulation=args.regulation,
        subject_filter=args.subject,
        paper_filter=args.paper,
        img_out_dir=args.img_out,
        csv_out_path=args.csv_out,
        write_per_subject=args.per_subject
    )


if __name__ == "__main__":
    main()
