# Grays Auction Scraper – Vehicle & Equipment Lead Generator

A robust automation tool that scrapes vehicle and equipment auction listings from **Grays.com**, extracts detailed product information, and enriches the data using **GPT-4** to generate structured, market-ready datasets for sales, marketing, and inventory analysis.

---

## Overview

This script is designed for automotive dealers, equipment brokers, auction analysts, and logistics companies who need up‑to‑date intelligence on auction results. It automatically:

- Scrapes multiple categories: motor vehicles, mining/construction, transport/trucks
- Extracts detailed attributes (VIN, odometer, build date, location, sale price, etc.)
- Uses **GPT-4** to parse natural‑language titles and descriptions into structured fields (year, make, model, variant, asset category, condition, modifications, attachments)
- Saves enriched data to versioned Excel files for easy import into CRM or analytics tools
- Runs continuously in a loop, ensuring you never miss a new listing

**The result:** a clean, comprehensive database of sold assets with detailed specifications—ideal for market research, competitor analysis, and lead generation for after‑sales services.

---

## Features

- **Multi‑category scraping** – Covers motor vehicles, transport trucks, mining equipment, construction machinery, and agriculture equipment.
- **GPT‑4 enrichment** – Transforms messy auction titles into structured year/make/model/variant, identifies modifications, attachments, asset category, and condition.
- **Deep page extraction** – Opens each product page to capture VIN, odometer, build date, full description, and sale price.
- **Versioned output** – Automatically creates a new Excel file if the current one exists, preventing overwrites.
- **Headless mode** – Runs silently in the background without opening a visible browser window.
- **Resilient loading** – Clicks "Load More" buttons until all products are loaded, handling dynamic content.
- **Continuous operation** – Intended to run on a schedule (currently looped with 1‑hour sleep) for perpetual data collection.

---

## How It Works

### 1. Browser Setup
- Launches a headless Chrome instance using Selenium and `webdriver‑manager`.
- Disables logging to reduce noise.

### 2. Category Scraping
- Loops through pre‑defined categories (URL + output filename).
- Loads the category page and repeatedly clicks "Load More" until all items are visible.

### 3. Product Card Extraction
- For each product card, extracts:
  - Asset description (title)
  - State/location
  - Product URL
  - Image URL

### 4. GPT‑4 Field Enrichment
- The title is sent to GPT‑4 to extract:
  - Year, Make, Model, Variant
  - Asset Category (CAR, LIGHT COMMERCIAL, HEAVY COMMERCIAL, MACHINERY, MINING EQUIPMENT, AGRICULTURE EQUIPMENT, OTHER)
- The title and full description are used to determine:
  - Condition (Excellent, Good, Fair, Bad, Unknown)
  - Modifications and Additional Attachments

### 5. Detail Page Scraping
- Opens the product link in a new tab.
- Scrapes structured `<ul>` lists to extract:
  - VIN, odometer (KM or Hours), build date, body type
  - Sale price (from the bidding element)
- Closes the tab and returns to the main page.

### 6. Data Assembly & Export
- Combines card data, GPT results, and detail page data.
- Appends the final product row to an Excel file (with versioning if the file exists).
- Repeats for all products in the category.

### 7. Continuous Loop
- After finishing all categories, the script sleeps for 1 hour and then restarts, ensuring fresh data.

---

## Impact – Why This Matters

### 🚀 Market Intelligence at Scale
- No need to manually visit hundreds of auction pages. The script automatically collects and structures data for every listed item.
- Enables **trend analysis** (pricing, popular models, condition spreads) and **competitive benchmarking**.

### 💰 Lead Generation for After‑Sales Services
- Knowing which vehicles and equipment have recently been sold allows targeting of buyers with warranties, parts, servicing, or financing offers.
- The detailed condition and attachments data help tailor offers to specific assets.

### 📊 Data‑Driven Decision Making
- Structured data (year, make, model, price, VIN, etc.) can be fed into CRM, inventory systems, or pricing tools.
- The Excel output is ready for pivot tables, dashboards, and further analysis.

### ⏱️ Time Savings
- What used to take hours per category now runs automatically, 24/7, with minimal oversight.
- The headless mode allows it to run on servers or VMs without graphical interface.

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/grays-scraper.git
cd grays-scraper
