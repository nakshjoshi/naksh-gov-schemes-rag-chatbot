import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# === CONFIGURATION ===
INPUT_FILE = '../../data/2.useful_extracted/useful_data.json'
OUTPUT_FILE = '../../data/3.enhancing_blank_data/enhanced_schemes.json'
BASE_URL = "https://www.myscheme.gov.in/schemes/{}"

fields_to_check = [
    "Scheme Name",
    "Ministry/Department",
    "Target Beneficiaries",
    "Description",
    "Benefits",
    "Eligibility Criteria",
    "Application Process",
    "Tags",
    "Documents Required"
]

# === Selenium Setup ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 15)

# === Scraper Function ===
def scrape_missing_fields(slug):
    url = BASE_URL.format(slug)
    print(f"🌐 Accessing: {url}")
    try:
        driver.get(url)
        wait.until(EC.presence_of_element_located((By.ID, "eligibility")))
    except:
        print(f"⚠️ Failed to load page for slug: {slug}")
        return {}

    soup = BeautifulSoup(driver.page_source, "html.parser")

    def get_div_text(div_id):
        div = soup.find('div', id=div_id)
        return div.text.strip() if div and div.text.strip() else "N/A"

    scraped_data = {
        "Scheme Name": soup.find("h1").text.strip() if soup.find("h1") else "N/A",
        "Ministry/Department": get_div_text("details"),
        "Description": get_div_text("benefits"),
        "Benefits": get_div_text("benefits"),
        "Eligibility Criteria": get_div_text("eligibility"),
        "Application Process": get_div_text("application-process"),
        "Documents Required": get_div_text("documents-required"),
    }

    tags_section = soup.find_all("a", class_="tag-item")
    scraped_data["Tags"] = ', '.join([tag.text.strip() for tag in tags_section]) if tags_section else "N/A"

    return scraped_data

# === Load Cleaned Data ===
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    schemes = json.load(f)

# === Main Loop: Patch Missing Fields ===
for scheme in schemes:
    slug = scheme.get("Slug") or scheme.get("Unique-ID")
    if not slug:
        continue  # Skip if no slug available

    missing_fields = []
    for field in fields_to_check:
        value = scheme.get(field, "")
        # Convert value to string safely before checking
        if value is None or str(value).strip() in ["", "''", "N/A", "[]", "{}"]:
            missing_fields.append(field)

    if missing_fields:
        print(f"\n🔎 Missing fields in {slug}: {missing_fields}")
        scraped_data = scrape_missing_fields(slug)

        for field in missing_fields:
            fetched_value = scraped_data.get(field)
            if fetched_value and fetched_value != "N/A":
                scheme[field] = fetched_value

# === Save Enhanced Data ===
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    json.dump(schemes, f, indent=2, ensure_ascii=False)

driver.quit()

print(f"\n✅ Enhancement complete! Saved as '{OUTPUT_FILE}'")
