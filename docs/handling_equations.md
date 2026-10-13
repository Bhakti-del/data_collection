# Handling Mathematical Equations & Formulas in Examination Datasets

## 1. Context & Scope

Question papers in engineering programs (such as **MFCS / Discrete Mathematics**, **Mathematics I–IV**, **Probability & Statistics**, **Digital Logic Design**, and **Design & Analysis of Algorithms**) are rich in mathematical notation. 

Unlike theoretical subjects, mathematical questions pose unique ingestion challenges:
- Standard PDF text extractors (`pdftotext`, PyMuPDF) frequently mangle mathematical glyphs into private-use Unicode characters.
- Traditional OCR (Tesseract) fails on multi-level fractions, matrices, integrals, and logic symbols.
- Regex question cleaners risk corrupting formulas by misinterpreting mathematical punctuation (decimals, asterisks, brackets) as exam delimiters.

This document establishes the architecture, sanitization rules, and fallback mechanisms for ingesting, preserving, and auditing mathematical equations **before normalization**.

---

## 2. Critical Findings & Analysis of Existing Pitfalls

> [!CAUTION]
> **Severe Data Loss Bug Discovered in Legacy Cleanup Scripts**:
> In earlier scripts (e.g., [`temp_data/clean_mfcs_dataset.py`](file:///home/slesha/wings-AI/question-paper-predictor/temp_data/clean_mfcs_dataset.py#L20-L31)), text was flagged as "garbled" and **discarded entirely** if it contained more than 3 math symbols:
> ```python
> # BUG in legacy script: Discarded perfectly valid mathematical questions!
> math_symbols = re.findall(r'[→←↔∀∃∧∨¬≤≥≠∈∉⊆⊂∪∩∑∏√∞±×÷]', text)
> if len(math_symbols) > 3:
>     return True  # Marked as garbled and DELETED!
> ```
> This led to the silent deletion of valid questions testing truth tables, logical equivalence, De Morgan's laws, set theory relations, and recurrence relations.
> 
> **Resolution**: Valid Unicode math symbols must **never** be used as a heuristic for noise or garbled text. Only random unprintable characters or disconnected single-letter OCR noise should be flagged.

---

## 3. Typology of Mathematical Questions in JNTUH Papers

Mathematical questions fall into two primary formats across examination papers:

```
                  ┌──────────────────────────────────────────────┐
                  │          MATHEMATICS / EQUATION QUESTION     │
                  └───────────────────────┬──────────────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼                                                 ▼
   [Tier 1: Linear / Inline Formulas]             [Tier 2: Multi-Dimensional Math]
   • Propositional logic: (P → ~Q) ∧ (Q ∨ R)      • Matrices & Determinants: [3x3 arrays]
   • Recurrence relations: an = 5an-1 - 6an-2     • Complex integrals with multi-tier limits
   • Set operations: (A ∩ B) - (B ∩ C)            • Step-by-step mathematical proofs
   • Exponents & Polynomials: (1 + X + X^2)^10    • Truth tables with formatted grids
                 │                                                 │
                 ▼                                                 ▼
    Preserved as Standardized Text /               Preserved via Bounding-Box Image Crop
         Normalized Unicode / LaTeX                (image_path: "images/math/2021_q3.png")
```

---

## 4. Ingestion & Preservation Strategy

### Strategy 1: Standardized Unicode / Inline LaTeX (Tier 1)
For inline mathematical statements from clean digital PDFs:
- **Canonical Glyphs**: Standardize equivalent notations to canonical Unicode or LaTeX tokens:
  - Logic negation: `~`, `¬`, `!` $\rightarrow$ Standardize to `¬` or `~`
  - Logic conjunction / disjunction: `^`, `Λ`, `&` $\rightarrow$ Standardize to `∧`, `v` $\rightarrow$ `∨`
  - Logic implication: `->`, `→`, `implies` $\rightarrow$ Standardize to `→`
  - Bi-conditional: `<->`, `↔`, `iff` $\rightarrow$ Standardize to `↔`
  - Exponentiation: Use caret syntax `X^14`, `a^-1` or proper Unicode superscripts.
  - Set notation: `A U B` $\rightarrow$ `A ∪ B`, `A intersection B` $\rightarrow$ `A ∩ B`.

### Strategy 2: Bounding-Box Image Snippet Fallback (Tier 2)
For large matrices, complex double/triple integrals, equations on scanned photocopies, or truth tables:
- **Do not force-OCR complex layout math**: Tesseract OCR will corrupt fractions, sub/superscripts, and alignment.
- **Crop the formula region as an image**:
  - The `raw_question_text` retains the instruction prompt:
    `"Solve the following system of equations using Gauss-Jordan elimination:"` or `"Evaluate the integral:"`
  - The equation or matrix itself is cropped into `images/<subject>/<year>_<paper>_q<num>.png`.
  - Store the relative path in `image_path`.
  - The question is now 100% complete, visually intact, and solvable by humans and multimodal models.

---

## 5. Handling Font Glitches & Private-Use Unicode (`\uf000`–`\uf8ff`)

### The Problem
Older JNTUH question papers formatted in MS Word used legacy fonts such as **Symbol**, **Wingdings**, or **MT Extra**. When converted to PDF, these symbols are placed in Unicode's **Private Use Area (PUA)** (`\uf000` to `\uf8ff`). For instance, `\uf0ae` appears instead of `→`, and `\uf0d9` appears instead of `∨`.

### The PUA Glyph Repair Map
Before running cleaning or tagging, pass the raw text through a glyph substitution table:

```python
PUA_MATH_REPAIR_MAP = {
    '\uf0ae': '→',   # Right arrow (implication)
    '\uf0ac': '¬',   # Logical NOT
    '\uf0da': '∧',   # Logical AND
    '\uf0d9': '∨',   # Logical OR
    '\uf0db': '↔',   # Bi-conditional
    '\uf0ab': '↔',   # Double arrow
    '\uf0a9': '⊆',   # Subset or equal
    '\uf0cc': '⊂',   # Proper subset
    '\uf0c7': '∩',   # Intersection
    '\uf0c8': '∪',   # Union
    '\uf0ce': '∈',   # Belongs to
    '\uf0cf': '∉',   # Does not belong to
    '\uf0b9': '≠',   # Not equal
    '\uf0a3': '≤',   # Less than or equal
    '\uf0b3': '≥',   # Greater than or equal
    '\uf0b1': '±',   # Plus-minus
    '\uf0b4': '×',   # Multiplication
    '\uf0b8': '÷',   # Division
    '\uf0a5': '∞',   # Infinity
    '\uf0d6': '√',   # Square root
    '\uf0e5': '∑',   # Summation
    '\uf0d5': '∏',   # Product
    '\uf06c': 'λ',   # Lambda
    '\uf06d': 'μ',   # Mu
    '\uf073': 'σ',   # Sigma
}

def repair_pua_math_symbols(text: str) -> str:
    """Translates legacy Symbol font PUA codes to canonical Unicode math characters."""
    for pua_char, canonical in PUA_MATH_REPAIR_MAP.items():
        text = text.replace(pua_char, canonical)
    return text
```

---

## 6. Pre-Normalization Protection Rules for Math Questions

To prevent noise strippers and tokenizers from ruining equations before normalization:

1. **Decimal & Constant Numbering Guard**:
   - Ensure question splitting regexes never split on numbers like `2.5`, `0.05 ohm`, `1.5625`:
   - Use negative lookahead: `r'(?<!\d)([1-9]|1[0-5])\.(?!\d)\s*'`
2. **Operator Preservation**:
   - Regex cleaning rules in `scripts/clean_papers.py` must never strip characters like `^`, `_`, `=`, `+`, `-`, `\`, `*`, `~`, `|`, `{`, `}` from question text.
3. **Multi-condition Parenthesis Protection**:
   - Predicate formulas often have nested parentheses (e.g. `((P ∧ Q) → R) ↔ (P → (Q → R))`). Do not strip or balance-trim parentheses inside the question statement.

---

## 7. Mathematical Deduplication Principles (For Normalization)

When mathematical questions enter the normalization step:

1. **Exact Symbolic Invariance**:
   - In math, a change in sign, power, or index represents an entirely **different problem**:
     - Question 1: *"Evaluate $\int_0^1 x^2 e^x dx$"*
     - Question 2: *"Evaluate $\int_0^1 x^3 e^x dx$"*
   - Sentence embedding models (`all-MiniLM-L6-v2`) will give these questions a similarity score $> 0.95$!
   - **Rule**: If two questions differ in numerical coefficients, powers, or variable bindings, they are **distinct candidate questions** and must not be merged.
2. **Text + Image Hybrid Match**:
   - For Tier 2 math questions (instruction text + equation image snippet), apply the same visual hashing rule:
     $$\text{Is\_Duplicate} = (\text{Text Match}) \land (\text{Image\_pHash Distance} \le 4)$$

---

## 8. Summary Checklist for Math Question Extraction

- [ ] Private Use Area glyphs mapped to canonical Unicode (`→`, `∧`, `∨`, `¬`, etc.).
- [ ] No arbitrary removal of rows containing multiple math symbols.
- [ ] Large matrices, truth tables, and complex scanned equations cropped to `images/` and linked via `image_path`.
- [ ] Question splitters guarded against decimal constants (`3.14`, `0.5`).
- [ ] Operators and exponents (`^`, `_`, `*`, `~`) fully preserved in `raw_question_text`.
