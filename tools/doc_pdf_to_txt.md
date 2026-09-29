# `pdf_to_txt.py` — PDF to Text Converter

**Purpose:** Recursively converts all PDF question papers in a directory tree to `.txt` files, saving each text file alongside its source PDF.

## Dependency

```bash
pip install pypdf
```

## Usage

```bash
# Uses the default root path
python3 pdf_to_txt.py

# Specify a custom root directory
python3 pdf_to_txt.py --root /path/to/your/pdf/folder
```

## What it does

- Walks all subdirectories under the root folder and finds every `.pdf` file.
- Extracts text from each PDF using `pypdf`.
- Saves a `.txt` file with the same name in the same directory as the PDF.
- **Skips** files where a non-empty `.txt` already exists (safe to re-run).
- For scanned/image-only PDFs where no text can be extracted, writes a placeholder: `[SCANNED IMAGE PDF - text extraction not available]`.

## Output Summary

| Status | Meaning |
|---|---|
| ✓ Converted | PDF successfully extracted to `.txt` |
| → Skipped | `.txt` already existed, no action taken |
| ⚠ Scanned | Image-only PDF, placeholder written |
| ✗ Failed | Error during processing |

## Main Function

`convert_pdf_to_txt(root: Path)` — takes a `pathlib.Path` as input and processes all PDFs under it.
