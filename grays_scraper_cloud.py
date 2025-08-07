# grays_scraper_cloud.py

import os
import time
import json
import re
import base64
import requests
import pandas as pd
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import openai
import traceback
from functools import wraps

openai.api_key = "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"

# ---------- Retry Decorator ----------
def retry(exceptions, tries=3, delay=2):
    def decorator_retry(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(tries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    print(f"[!] Retry {func.__name__} due to {e} (Attempt {attempt+1}/{tries})")
                    time.sleep(delay)
            raise
        return wrapper
    return decorator_retry

# ---------- GitHub API Upload ----------
def upload_to_git():
    print("\n⬆️ Uploading scraped files to GitHub via API...")

    GITHUB_USER = "Haseeb536"
    GITHUB_REPO = "Grays_data"
    GITHUB_BRANCH = "main"
    GITHUB_TOKEN = "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" 
    GITHUB_API_URL = "https://api.github.com"

    if not GITHUB_TOKEN:
        print("❌ Missing GITHUB_TOKEN environment variable.")
        return

    base_dir = "Grays_data"
    commit_message = f"Upload data {datetime.now().isoformat()}"

    for filename in os.listdir(base_dir):
        if not filename.endswith(".xlsx"):
            continue

        local_path = os.path.join(base_dir, filename)
        repo_path = f"{base_dir}/{filename}"  # Upload into same dir in GitHub

        with open(local_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        url = f"{GITHUB_API_URL}/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{repo_path}"

        headers = {
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # Check if file exists to get SHA (needed for updating)
        response = requests.get(url, headers=headers, params={"ref": GITHUB_BRANCH})
        if response.status_code == 200:
            sha = response.json().get("sha")
        else:
            sha = None

        data = {
            "message": commit_message,
            "branch": GITHUB_BRANCH,
            "content": content
        }

        if sha:
            data["sha"] = sha

        upload_response = requests.put(url, headers=headers, json=data)

        if upload_response.status_code in [200, 201]:
            print(f"[✅] Uploaded: {repo_path}")
        else:
            print(f"[❌] Failed to upload {repo_path}: {upload_response.status_code} - {upload_response.text}")

# ---------- Place all scraping logic here ----------
from grays import scrape_grays_category

@retry(Exception, tries=3, delay=5)
def safe_scrape(category, driver):
    scrape_grays_category(category["url"], category["filename"], driver)

# ---------- Main ----------
def main():
    categories = [
        {
            "url": "https://www.grays.com/search/automotive-trucks-and-marine/motor-vehiclesmotor-cycles?tab=items",
            "filename": "motor-vehiclesmotor-cycles.xlsx"
        },
        {
            "url": "https://www.grays.com/search/mining-construction-and-agriculture?tab=items",
            "filename": "mining-construction-and-agriculture.xlsx"
        },
        {
            "url": "https://www.grays.com/search/automotive-trucks-and-marine/transport-trucks-and-trailers?tab=items",
            "filename": "transport-trucks-and-trailers.xlsx"
        }
    ]

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    for category in categories:
        try:
            print(f"\n🚀 Scraping: {category['filename']}")
            safe_scrape(category, driver)
        except Exception as e:
            print(f"❌ Error scraping {category['filename']}: {e}")
            traceback.print_exc()
            continue

    driver.quit()
    upload_to_git()

# ---------- Infinite Loop with Wait ----------
if __name__ == "__main__":
    while True:
        print("\n🔁 Starting new scraping cycle...")
        try:
            main()
        except Exception as e:
            print(f"⚠️ Critical failure in main loop: {e}")
            traceback.print_exc()
        print("⏳ Sleeping 1 minute before next run...\n")
        time.sleep(603600)
