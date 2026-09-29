# JNTUH Data Crawling & Acquisition Pipeline

## 1. Overview & Data Sources

To predict future JNTUH examination papers with high fidelity, the system requires a complete 15-year historical corpus spanning multiple academic regulations (**R09, R13, R15, R16, R18, R22**).

Data is acquired from two primary sources:
1. **JNTUH Online Student Services (OSS) Portal:** The official repository maintained by JNTUH (`https://studentservices.jntuh.ac.in/oss/`).
2. **Curated Secondary Mirrors / Google Drive Archive:** Backups containing scanned papers for older regulations (R09, R13, R15) and subjects with missing portal links.

---

## 2. JNTUH OSS Portal Architecture & Crawling Mechanism

### 2.1 The Multi-Level Hierarchy
The JNTUH OSS portal operates on an Apache Tomcat server using a multi-step session wizard where query parameters control drilldown depth:

| Level (`l123`) | Scope | Example Parameter / UI Link |
|---|---|---|
| `l123=0` | Course Selection | `level=1.B.Tech&l123=0&type=previousQPapers` |
| `l123=1` | Academic Year & Regulation | `level=2.II Year&l123=1` |
| `l123=2` | Semester | `level=1.I Sem&l123=2` |
| `l123=3` | Subject Name | `level=3.DATA STRUCTURES&l123=3` |
| `l123=4` | Downloadable PDF Files | List of exam PDFs for that subject |

### 2.2 The Tomcat Session Bug & Solution
* **The Bug:** Jumping directly to a deep URL like:
  ```text
  https://studentservices.jntuh.ac.in/oss/syllabus_action.html?type=previousQPapers&level=3.DATA%20STRUCTURES&l123=4
  ```
  causes the server to throw an error:
  `null/var/lib/tomcat9/webapps/oss/resources/files/previousQPapers/3.DATA STRUCTURES : is Not found`
  This happens because the Tomcat servlet concatenates directory paths in the user's `HttpSession`. If intermediate levels are skipped, the path prefix evaluates to `null`.
* **The Solution:** The crawler must instantiate a persistent HTTP Session (`requests.Session` in Python) with a cookie jar and traverse the hierarchy **sequentially** from `l123=0` down to `l123=4`.

---

## 3. Automated Crawler Script Implementation

The automated recursive crawler operates with session persistence, error retries, and rate limiting:

```python
import os
import re
import time
import urllib.parse
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://studentservices.jntuh.ac.in/oss/"
START_URL = BASE_URL + "syllabus.html?type=previousQPapers"
LOCAL_DOWNLOAD_ROOT = "./data/raw_pdf_repository"

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
})

def crawl_and_download(current_url, path_crumbs=[]):
    """
    Recursively traverses JNTUH OSS portal drilldown levels
    and downloads all discovered PDF papers into nested directories.
    """
    try:
        response = session.get(current_url, timeout=25, verify=False)
        response.raise_for_status()
    except Exception as e:
        print(f"[ERROR] Failed to fetch {current_url}: {e}")
        return

    soup = BeautifulSoup(response.text, "html.parser")

    # 1. Download any PDF links found at this level
    pdf_tags = soup.find_all("a", href=re.compile(r"\.pdf$", re.IGNORECASE))
    for tag in pdf_tags:
        href = tag.get("href")
        pdf_url = urllib.parse.urljoin(BASE_URL, href)
        filename = tag.text.strip() or os.path.basename(href)
        if not filename.lower().endswith(".pdf"):
            filename += ".pdf"

        # Sanitize filename
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        target_dir = os.path.join(LOCAL_DOWNLOAD_ROOT, *path_crumbs)
        os.makedirs(target_dir, exist_ok=True)
        file_path = os.path.join(target_dir, filename)

        if not os.path.exists(file_path):
            print(f"[DOWNLOAD] {' / '.join(path_crumbs)} -> {filename}")
            try:
                content = session.get(pdf_url, timeout=30, verify=False).content
                if len(content) > 1024:  # Ignore empty/corrupted 0KB downloads
                    with open(file_path, "wb") as f:
                        f.write(content)
                time.sleep(0.5)  # Rate limiting to prevent 429 errors
            except Exception as ex:
                print(f"[DOWNLOAD FAILED] {pdf_url}: {ex}")

    # 2. Recurse into child navigation links
    nav_links = soup.find_all("a", href=re.compile(r"syllabus_action\.html\?"))
    for nav in nav_links:
        label = nav.text.strip()
        if not label or label.lower() in ["home", "back", "terms & conditions"]:
            continue
        href = nav.get("href")
        next_url = urllib.parse.urljoin(BASE_URL, href)
        if next_url != current_url:
            clean_label = re.sub(r'[\\/*?:"<>|]', "_", label)
            crawl_and_download(next_url, path_crumbs + [clean_label])

if __name__ == "__main__":
    os.makedirs(LOCAL_DOWNLOAD_ROOT, exist_ok=True)
    crawl_and_download(START_URL)
```

---

## 4. Google Drive Synchronization Strategy

Because older papers (R09, R13) often suffer from broken links on the official portal, supplementary archives are mirrored on Google Drive under **`Paper Prediction Dataset`**:

- Drive Folder Structure:
  - `R13/`
  - `R15/`
  - `R16/`
  - `R18/` (1st, 2nd, 3rd, 4th Year)
  - `R22/` (`Question paper/` and `Syllabus/`)

Synchronization to local workspaces is performed via `gdown` or API export:
```bash
# Sync specific regulation folder locally
gdown --folder "https://drive.google.com/drive/folders/1TVNS9AmNXTK_mgkl3g_o74J3MHXlhIu6" -O ./data/google_drive_mirror/
```

---

## 5. Crawling Quality Assurance Checklist

Before sending downloaded PDFs to Phase 2 (Text Extraction), the crawler must pass:
- [x] **File Size Verification:** Flag any PDF smaller than 10 KB (indicates empty files or error pages).
- [x] **Duplicate Elimination:** Deduplicate files matching identical MD5 checksums.
- [x] **Regulation Verification:** Cross-check the header regulation string printed inside the PDF against the folder path it was placed in.
