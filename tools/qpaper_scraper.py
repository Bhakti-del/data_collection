"""
JNTUH Previous Question Papers Downloader
Navigates: B.Tech -> R15 -> 1-1 -> CSE -> MATHEMATICS-I -> downloads all PDFs

Requirements:
    pip install selenium webdriver-manager requests
"""

import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Force UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WDM = True
except ImportError:
    USE_WDM = False

# ── CONFIG ──────────────────────────────────────────────────────────────────
# Navigation path to follow (change these to download different subjects)
NAV_PATH = [
    "B.Tech",       # course
    "R15",          # regulation
    "2-2",          # year-sem
    "CSE",          # branch
    "ENVIRONMENTAL STUDIES" # subject
]

BASE_URL = "https://studentservices.jntuh.ac.in/oss/syllabus.html?type=previousQPapers"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "JNTUH_QP", "_".join(NAV_PATH[-2:]))
os.makedirs(SAVE_DIR, exist_ok=True)
# ────────────────────────────────────────────────────────────────────────────

def make_driver():
    opts = Options()
    # Comment out headless to see the browser in action (for debugging)
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1280,900")
    if USE_WDM:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts
        )
    else:
        driver = webdriver.Chrome(options=opts)
    return driver


def wait_and_click(driver, wait, link_text):
    """Wait for a link with given text and click it."""
    print(f"  -> Clicking: '{link_text}'")
    try:
        el = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, f"//a[normalize-space(text())='{link_text}']")
            )
        )
        el.click()
        time.sleep(2)
        return True
    except Exception as e:
        print(f"     Could not find link '{link_text}': {e}")
        # Print available links for debugging
        links = driver.find_elements(By.TAG_NAME, "a")
        texts = [l.text.strip() for l in links if l.text.strip() and not l.text.strip().startswith("http")]
        print(f"     Available links: {texts}")
        return False


def download_pdf(url, filename, session_cookies):
    """Download a PDF file."""
    save_path = os.path.join(SAVE_DIR, filename)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "https://studentservices.jntuh.ac.in/oss/",
    }
    cookies = {c["name"]: c["value"] for c in session_cookies}
    try:
        r = requests.get(url, headers=headers, cookies=cookies, timeout=30)
        if r.status_code == 200 and b"%PDF" in r.content[:10]:
            with open(save_path, "wb") as f:
                f.write(r.content)
            print(f"  [OK] {filename} ({len(r.content)//1024} KB)")
            return True
        else:
            print(f"  [FAIL] {filename} -- HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"  [ERROR] {filename} -- {e}")
        return False


def main():
    print("Starting browser...")
    driver = make_driver()
    wait = WebDriverWait(driver, 15)

    try:
        print(f"Loading: {BASE_URL}")
        driver.get(BASE_URL)
        time.sleep(2)

        # Navigate through the path
        for step in NAV_PATH:
            if not wait_and_click(driver, wait, step):
                print(f"\nFailed at step: '{step}'. Stopping.")
                return

        # Now we should be on the subject page with PDF links
        time.sleep(2)
        print(f"\nCurrent URL: {driver.current_url}")
        print("Looking for PDF links...")

        links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

        # Filter out Terms & Conditions
        pdf_links = [
            (a.text.strip() or a.get_attribute("href").split("/")[-1], a.get_attribute("href"))
            for a in links
            if "TermsandConditions" not in a.get_attribute("href")
        ]

        if not pdf_links:
            print("No PDF links found.")
            print("\nPage source (first 3000 chars):")
            print(driver.page_source[:3000])
            return

        print(f"\nFound {len(pdf_links)} PDF(s):")
        cookies = driver.get_cookies()

        for name, url in pdf_links:
            filename = name if name.endswith(".pdf") else url.split("/")[-1]
            filename = filename.replace("/", "_").replace("\\", "_").strip()
            download_pdf(url, filename, cookies)

        print(f"\nDone! Files saved to:\n  {SAVE_DIR}")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()
