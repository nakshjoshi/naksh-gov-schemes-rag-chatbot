import json
import re
from bs4 import BeautifulSoup
from pathlib import Path

# Load the enhanced schemes JSON
input_path = Path("../../data/3.enhancing_blank_data/enhanced_schemes.json")
with open(input_path, "r", encoding="utf-8") as f:
    schemes = json.load(f)

# Define a function to clean HTML tags and entities
def clean_html(text):
    if not isinstance(text, str):
        return text
    # Use BeautifulSoup to remove HTML tags and unescape entities
    return BeautifulSoup(text, "html.parser").get_text().strip()

# Normalize and clean data
for scheme in schemes:
    # Clean all string fields from HTML
    for key in scheme:
        scheme[key] = clean_html(scheme[key])

    # Handle Ministry/Department inconsistencies
    ministry = scheme.get("Ministry/Department")
    if isinstance(ministry, dict):
        scheme["Ministry/Department"] = ministry.get("label", "Not Available")

    # Fill missing or empty fields with a placeholder
    required_fields = [
        "Scheme Name", "Ministry/Department", "Target Beneficiaries",
        "Description", "Benefits", "Eligibility Criteria", "Application Process",
        "Tags", "Documents Required"
    ]
    for field in required_fields:
        if field not in scheme or not scheme[field]:
            scheme[field] = "Not Available"

# Save the cleaned data
output_path = Path("../../data/4.clean_pre-process_data/cleaned_schemes_final.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(schemes, f, ensure_ascii=False, indent=2)

output_path.name
