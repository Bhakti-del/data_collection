# `qpaper_scraper.py` — JNTUH Question Papers Downloader

**Purpose:** Automates downloading of previous question paper PDFs from the [JNTUH Student Services portal](https://studentservices.jntuh.ac.in/oss/syllabus.html?type=previousQPapers) by navigating the site using Selenium and downloading matched PDFs via `requests`.

## Dependencies

```bash
pip install selenium webdriver-manager requests
```

> `webdriver-manager` is optional but recommended — it auto-installs the correct ChromeDriver. Without it, ChromeDriver must be available in the system PATH.

## Usage

```bash
python3 qpaper_scraper.py
```

Configure the target subject by editing the `NAV_PATH` and `SAVE_DIR` variables in the script before running.

## Configuration

Edit these variables at the top of the script:

| Variable | Description | Default |
|---|---|---|
| `NAV_PATH` | Navigation steps to reach the subject page | `["B.Tech", "R15", "2-2", "CSE", "ENVIRONMENTAL STUDIES"]` |
| `BASE_URL` | JNTUH portal URL | Student Services previous QP page |
| `SAVE_DIR` | Directory where PDFs are saved | `~/Downloads/JNTUH_QP/<year-sem>_<branch>/` |

### `NAV_PATH` format

```python
NAV_PATH = [
    "B.Tech",           # Course
    "R15",              # Regulation (R13, R15, R16, R18, R22, ...)
    "2-2",              # Year-Semester (1-1, 1-2, 2-1, 2-2, ...)
    "CSE",              # Branch
    "SUBJECT NAME"      # Subject (exact name as shown on the portal)
]
```

## How it Works

1. Launches a headless Chrome browser.
2. Opens the JNTUH portal URL.
3. Sequentially clicks each link in `NAV_PATH` to navigate to the target subject page.
4. Collects all `.pdf` links on the page (excluding Terms & Conditions).
5. Downloads each PDF using `requests` with the browser's session cookies.
6. Saves files to `SAVE_DIR`.

## Key Functions

| Function | Description |
|---|---|
| `make_driver()` | Initializes a headless Chrome WebDriver |
| `wait_and_click(driver, wait, link_text)` | Waits for a link by exact text and clicks it; prints available links on failure |
| `download_pdf(url, filename, session_cookies)` | Downloads a single PDF and saves it to `SAVE_DIR` |
| `main()` | Orchestrates the full navigation and download flow |

## Output

Downloaded PDFs are saved to:
```
~/Downloads/JNTUH_QP/<year-sem>_<subject>/
```

Console output example:
```
Starting browser...
Loading: https://studentservices.jntuh.ac.in/...
  -> Clicking: 'B.Tech'
  -> Clicking: 'R15'
  ...
Found 3 PDF(s):
  [OK] 2022_Nov_QP.pdf (210 KB)
  [OK] 2023_May_QP.pdf (198 KB)

Done! Files saved to:
  /home/user/Downloads/JNTUH_QP/2-2_ENVIRONMENTAL STUDIES
```

## Notes

- To debug navigation issues, comment out `--headless=new` in `make_driver()` to watch the browser in action.
- If a navigation step fails, the script prints all available links on the page to help identify the correct link text.
- Scanned PDFs are downloaded as-is; use `pdf_to_txt.py` afterwards to attempt text extraction.
