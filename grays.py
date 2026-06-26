import time
import re
import os
from datetime import datetime, timedelta, timezone
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import openai
import json
import undetected_chromedriver as uc


# Helper: GPT Functions
def get_year_make_model_variant_from_gpt(title):
    prompt = f"""
You are an expert vehicle parsing AI. Your task is to extract key structured fields from vehicle auction titles.

From the given title, extract:
- Year
- Make
- Model
- Variant (everything after the model; if none, leave it empty)

Title: "{title}"

Respond ONLY in this **exact JSON format**:
{{
  "year": "YYYY",
  "make": "MAKE",
  "model": "MODEL",
  "variant": "VARIANT"
}}
"""
    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        raw = response.choices[0].message.content.strip()
        parsed = json.loads(raw)
        return {
            "year": parsed.get("year", "").strip(),
            "make": parsed.get("make", "").strip(),
            "model": parsed.get("model", "").strip(),
            "variant": parsed.get("variant", "").strip()
        }
    except Exception as e:
        print(f"⚠️ GPT failed to parse vehicle fields: {e}")
        return {"year": "", "make": "", "model": "", "variant": ""}


def get_category_from_gpt(title):
    prompt = f"""
    You are an AI that classifies equipment or vehicles into **broad asset categories** for auction listings. The possible categories are:
    - CAR
    - LIGHT COMMERCIAL
    - HEAVY COMMERCIAL
    - MACHINERY
    - MINING EQUIPMENT
    - AGRICULTURE EQUIPMENT
    - OTHER

    **DO NOT** classify small accessories (like terminals, sockets, clamps, cable accessories, parts, etc.) as vehicles. These should be marked as "OTHER".

    Now classify the following item strictly into one of the above categories:

    Title: "{title}"
    Asset Type:"""


    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"⚠️ GPT failed to get category: {e}")
        return ""

    
def get_mods_and_attachments(title, description):

    prompt = f"""
Given the following vehicle listing title and description, identify:

1. Any **aftermarket modifications** (i.e., changes made by the owner after purchase like lift kits, bull bars, upgraded exhaust, performance chips, etc).
2. Any **additional attachments** (i.e., equipment or accessories like roof racks, tow bars, canopy, toolboxes, etc).

If none are found, return "None" for that field.

Respond in this format:
Modifications: ...
Attachments: ...

Title: "{title}"
Description: "{description}"
"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()

        mods = ""
        attachments = ""

        for line in content.splitlines():
            if "modification" in line.lower():
                mods = line.split(":", 1)[-1].strip()
            elif "attachment" in line.lower():
                attachments = line.split(":", 1)[-1].strip()

        return mods or "None", attachments or "None"
    except Exception as e:
        print(f"⚠️ GPT failed to get mods & attachments: {e}")
        return "None", "None"


def get_variant_from_gpt(title, description):

    prompt = f"""
Extract the transmission or variant from the following vehicle description.
Example outputs: "Automatic", "Manual", "CVT", "6-Speed Automatic", etc.
If it's unknown, return "Unknown".

Title: "{title}"

Description: "{description}"

Variant:"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        result = response.choices[0].message.content.strip()
        return result
    except Exception as e:
        print(f"⚠️ GPT failed to get variant: {e}")
        return "Unknown"

def get_condition_from_gpt(title, description):
    prompt = f"""
You are an expert vehicle analyst trained to assess the **overall physical and mechanical condition** of vehicles or equipment from auction listings.

You must classify the condition into **one** of the following categories:

- Excellent: As-new or showroom condition. No noticeable defects.
- Good: Minor wear, clean, well-maintained.
- Fair: Visible wear and tear, aged but usable.
- Bad: Poor condition, needs repairs, significant damage.
- Unknown: Only use this if there is absolutely NO detail in the title or description.

Your job is to make a reasonable judgment **even from subtle clues**. Avoid choosing "Unknown" unless the description is completely empty or meaningless.

Use the vehicle title and description below:

Title: "{title}"
Description: "{description}"

Respond with just the condition category: Excellent, Good, Fair, Bad, or Unknown.

Condition:"""

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        result = response.choices[0].message.content.strip()
        allowed = ["Excellent", "Good", "Fair", "Bad", "Unknown"]
        # Fix common mistakes like extra punctuation or multiple words
        result_cleaned = result.split()[0].capitalize()
        return result_cleaned if result_cleaned in allowed else "Unknown"
    except Exception as e:
        print(f"⚠️ GPT failed to get condition: {e}")
        return "Unknown"

# def extract_title_parts(title):
#     try:
#         parts = title.split()
#         year = parts[0]
#         make = parts[1]
#         model = parts[2]
#         variant = " ".join(parts[3:])
#         return year, make, model, variant
#     except:
#         return "", "", "", ""

# def get_category_from_body_type(body_type):
#     bt = body_type.lower()
#     if any(x in bt for x in ["sedan", "hatch", "wagon", "suv", "passenger"]):
#         return "CAR"
#     elif any(x in bt for x in ["van", "ute", "pickup", "4x4", "commercial"]) or "light" in bt:
#         return "LIGHT COMMERCIAL"
#     elif any(x in bt for x in ["truck", "semi", "bus", "heavy"]):
#         return "HEAVY COMMERCIAL"
#     elif any(x in bt for x in ["excavator", "loader", "crane", "earth", "digger"]):
#         return "MACHINERY"
#     elif any(x in bt for x in ["mine", "mining"]):
#         return "MINING EQUIPMENT"
#     elif any(x in bt for x in ["tractor", "harvest", "agri"]):
#         return "AGRICULTURE EQUIPMENT"
#     else:
#         return ""

def get_versioned_filename(base_path):
    """Return a versioned file path if the base already exists."""
    if not os.path.exists(base_path):
        return base_path

    base, ext = os.path.splitext(base_path)
    counter = 1
    new_path = f"{base} ({counter}){ext}"
    while os.path.exists(new_path):
        counter += 1
        new_path = f"{base} ({counter}){ext}"
    return new_path

def write_to_excel(product, columns, output_file):
    df = pd.DataFrame([product], columns=columns)
    if os.path.exists(output_file):
        with pd.ExcelWriter(output_file, engine="openpyxl", mode="a", if_sheet_exists="overlay") as writer:
            df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)
    else:
        df.to_excel(output_file, index=False)

def load_existing_links(filepath):
    if os.path.exists(filepath):
        try:
            df = pd.read_excel(filepath)
            return set(df['product_link'].dropna().unique())
        except:
            return set()
    return set()

def scrape_product_detail(driver, link):
    wait = WebDriverWait(driver, 10)
    driver.execute_script("window.open('');")
    driver.switch_to.window(driver.window_handles[-1])
    driver.get(link)
    time.sleep(2)

    details = {
        "auction_end_date": "", "location": "", "description": "","description2": "", "body_type": "",
        "vin": "", "odometer": "", "price": "", "lot_no": "", "category": "","build_date":""
    }

    # tbodies = ['//tbody', '//*[@id="lotContainer"]/div/div[1]/div[5]/div[2]/table/tbody']
    # for tbody_xpath in tbodies:
    #     try:
    #         tbody = driver.find_element(By.XPATH, tbody_xpath)
    #         driver.execute_script("arguments[0].scrollIntoView();", tbody)
    #         rows = tbody.find_elements(By.TAG_NAME, 'tr')
    #         for row in rows:
    #             tds = row.find_elements(By.TAG_NAME, 'td')
    #             if len(tds) == 2:
    #                 label = tds[0].text.lower()
    #                 value = tds[1].text.strip()
    #                 if 'location' in label and not details["location"]:
    #                     details["location"] = value
    #                 elif 'lot id' in label and not details["lot_no"]:
    #                     details["lot_no"] = value
    #                 elif 'category' in label and not details["category"]:
    #                     details["category"] = value
    #     except:
    #         continue

    ul_paths = [
    '//*[@id="tabpage_Description"]/div[1]/div/ul[1]',
    '//*[@id="tabpage_Description"]/div[1]/div/ul[2]',
    '//*[@id="tabpage_Description"]/div[1]/div/ul[3]',
    '//*[@id="tabpage_Description"]/div[1]/div/ul[4]',
    '//*[@id="tabpage_Description"]/div[1]/div/ul[5]',
    '//*[@id="tabpage_Description"]/div[1]/div/ul[6]',
    ]

    li_texts = []

    for ul_xpath in ul_paths:
        try:
            desc_ul = driver.find_element(By.XPATH, ul_xpath)
            driver.execute_script("arguments[0].scrollIntoView();", desc_ul)
            li_items = desc_ul.find_elements(By.TAG_NAME, 'li')
            for li in li_items:
                text = li.text.strip()
                if text:
                    li_texts.append(text)
        except Exception:
            continue

    # Save full description
    details["description"] = " | ".join(li_texts)

    # Optional: Extract structured values like VIN and odometer
    for item in li_texts:
        low_item = item.lower()
        if low_item.startswith("body type:"):
            details["body_type"] = item.split(":", 1)[1].strip()
        elif low_item.startswith("vin"):
            details["vin"] = item.split(":", 1)[1].strip()
        elif "odometer" in low_item:
            match = re.search(r"\d+", item.replace(",", ""))
            if match:
                details["odometer"] = match.group()
        elif low_item.startswith("indicated odometer reading"):
            odo = item.split(":", 1)[1].strip()
            match = re.search(r"\d+", odo.replace(",", ""))
            if match:
                details["odometer"] = match.group()
        elif low_item.startswith("build date"):
            details["build_date"] = item.split(":", 1)[1].strip()



    try:
        price_elem = driver.find_element(By.XPATH, '//*[@id="biddableLot"]/form/div/div[1]/div[1]/div[2]/div/span/span')
        driver.execute_script("arguments[0].scrollIntoView();", price_elem)
        raw_price = price_elem.text.strip()
        details["price"] = re.sub(r"[^\d]", "", raw_price)
        # print("sale price : ",details["price"])
        # print("raw price : ",raw_price)
    except:
        print("cannot find the sale price")
        pass
    
    # if not details["category"]:
    #     details["category"] = get_category_from_body_type(details["body_type"])

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return details

def scrape_grays_category(url, filename,driver):
    now = datetime.now()
    wait = WebDriverWait(driver, 10)

    driver.get(url)
    time.sleep(4)

    while True:
        try:
            load_more_btn = wait.until(EC.element_to_be_clickable((By.XPATH,
                '//*[@id="__next"]/div/div[6]/div/div[2]/div/div/div/div[2]/div[2]/div/div[2]/div/button')))
            driver.execute_script("arguments[0].scrollIntoView();", load_more_btn)
            time.sleep(1)
            load_more_btn.click()
            print("🔁 Clicked 'Load More'")
            time.sleep(3)
        except:
            print("✅ No more 'Load More' button or not clickable.")
            break

    columns = [
    "Auction House", "Sale Date", "State", "Image URL", "Asset Type", "Asset Description", "Year",
    "Make", "Model", "Variant", "VIN", "KM or Hours", "Condition", "Additional Attachments",
    "Modifications", "Status", "Sale Price", "Product URL"
    ]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "Grays_data")
    os.makedirs(output_dir, exist_ok=True)

    base_output_file = os.path.join(output_dir, filename)
    output_file = get_versioned_filename(base_output_file)

    container = driver.find_element(By.XPATH, '//*[@id="__next"]/div/div[6]/div/div[2]/div/div/div/div[2]/div[1]')
    cards = container.find_elements(By.XPATH, './div')
    print(f"\n🔍 Found {len(cards)} product cards for {filename}\n")

    for index, card in enumerate(cards, 1):
        try:
            product = dict.fromkeys(columns, "")
            product["Sale Date"] = now.strftime("%d/%m/%Y")
            product["Auction House"] = "Grays"
            product["Status"] = "Sold"

            try:
                product["Asset Description"] = card.find_element(By.TAG_NAME, "h2").text.strip()
            except: pass
            # try:
            #     product["condition"] = card.find_element(By.XPATH, './/div[2]/div[3]/p[1]').text.strip()
            # except: pass
            try:
                product["State"] = card.find_element(By.XPATH, './/div[2]/div[3]/p[2]').text.strip()
            except: pass
            # try:
            #     product["countdown"] = card.find_element(By.XPATH, './/div[2]/div[1]/div[2]/p').text.strip()
            # except: pass
            try:
                link = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                product["Product URL"] = link
            except: pass
            try:
                product["Image URL"] = card.find_element(By.TAG_NAME, "img").get_attribute("src")
            except: pass

            parsed = get_year_make_model_variant_from_gpt(product["Asset Description"])
            product["Year"] = parsed['year']
            product["Make"] = parsed['make']
            product["Model"] = parsed['model']
            product["Variant"] = parsed['variant']


            detail = scrape_product_detail(driver, link)
            category = get_category_from_gpt(product["Asset Description"])
            product.update({
                "VIN": detail["vin"],
                "KM or Hours": detail["odometer"],
                "Sale Price": detail["price"],
                "Asset Type": category
            })
            if not product["Year"]:
                product["Year"] = detail["build_date"]

            modifications, attachments = get_mods_and_attachments(product["Asset Description"], detail["description"])
            condition = get_condition_from_gpt(product["Asset Description"], detail["description"])
            product["Additional Attachments"] = attachments
            product["Modifications"] = modifications 
            product["Condition"] = condition
            
            print(f"\n✅ Finished Product #{index}")
            for k in columns:
                print(f"{k:<18}: {product[k]}")

            write_to_excel(product, columns, output_file)
        except:
            print("error scraping the product :",index)
            continue

    driver.quit()


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
    options.add_argument("--start-maximized")
    options.add_argument("--headless=new")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    for category in categories:
        try:
            print(f"\n🚀 Starting scraping: {category['filename']}")
            scrape_grays_category(category["url"], category["filename"],driver)
            print(f"✅ Finished scraping: {category['filename']}")
        except:
            print(f"eror scraping: {category['url']}")
            pass


if __name__ == "__main__":
    while True:
        print("\n🔁 Starting new scraping cycle...\n")
        try:
            main()
        except Exception as e:
            print(f"⚠️ Scraping failed this cycle: {e}")
        # print("⏳ Sleeping for 1 hour before next run...\n")
        # time.sleep(3600)  # wait 1 hour (3600 seconds)
