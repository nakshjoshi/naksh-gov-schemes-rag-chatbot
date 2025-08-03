import json
import os
import requests
import sys
# Change stdout to use UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')
headers = {
  'accept': 'application/json',
  'origin': 'https://www.myscheme.gov.in',
  'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
  'x-api-key': 'tYTy5eEhlu9rFjyxuCr7ra7ACp4dv1RH8gWuHTDc'
}
for i in range(0, 3400, 100):
    url = f"https://api.myscheme.gov.in/search/v4/schemes?lang=en&q=%5B%5D&keyword=&sort=&from={i}&size=100"
    response = requests.get(url, headers=headers)
    print(response.text)
    # save response as json file
    with open(f"../../data/1.raw/response{(i//100)+1}.json", "w", encoding="utf-8") as file:
        file.write(response.text)

# Set to store unique slugs
setofslags = set()
# Iterate through each file (assuming files are named "response1.json", "response2.json", ..., "response34.json")
for i in range(1, 35):
    try:
        # Construct the file path dynamically
        file_path = f"../../data/1.raw/response{i}.json"
        
        # Check if file exists
        if not os.path.exists(file_path):
            print(f"[!] File not found: {file_path}")
            continue
        
        # Read and parse the JSON file
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Access the 'total' value
        total = data.get("data", {}).get("hits", {}).get("items", [])
        for item in total:
            # Extract the 'slug' value from each item and add to the set
            item_total = item.get("fields", {}).get("slug", "")
            if item_total:
                setofslags.add(item_total)

        print(f"✅ Processed file: {file_path}")
    
    except json.JSONDecodeError as e:
        print(f"[!] JSON Decode Error in file {file_path}: {e}")
    except Exception as e:
        print(f"[!] Error processing file {file_path}: {e}")

# Print the total unique slugs and the set
print(f"Total unique slugs: {len(setofslags)}")
print(setofslags)

# Function to fetch data for multiple schemes
all_data = {}

# def fetch_multiple_schemes(scheme_names, output_file="schemes_data.json"):
#     base_url = "https://www.myscheme.gov.in/_next/data/Pgr1-v_XYCcKuy3LqoxeR/en/schemes/{}.json?slug={}"
#
#     headers = {
#         "User-Agent": "Mozilla/5.0",
#         "Accept": "application/json"
#     }
#
#     for name in scheme_names:
#         url = base_url.format(name, name)  # Format the URL for each scheme name
#         try:
#             response = requests.get(url, headers=headers)
#             response.raise_for_status()  # Raise an exception for non-2xx responses
#             data = response.json()
#
#             # Store data using scheme name as key
#             all_data[name] = data
#
#             print(f"Fetched data for: {name}")  # Removed the Unicode checkmark here
#         except requests.exceptions.RequestException as e:
#             print(f"❌ Error fetching '{name}': {e}")
#
#     # Save combined data
#     with open(output_file, "w", encoding="utf-8") as f:
#         json.dump(all_data, f, indent=4, ensure_ascii=False)
#     print(f"\n💾 Data saved to: {output_file}")

def fetch_and_append_scheme_data(scheme_names, output_file="../../data/1.raw/schemes_data.json"):
    base_url = "https://www.myscheme.gov.in/_next/data/izZ63Jp_8jzqnemoxFmi0/en/schemes/{}.json?slug={}"
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }

    # Load existing data if file already exists
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            try:
                all_data = json.load(f)
            except json.JSONDecodeError:
                all_data = {}
    else:
        all_data = {}

    for name in scheme_names:
        if name in all_data:
            print(f"⏭️ Skipping already fetched: {name}")
            continue

        url = base_url.format(name, name)
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Add the scheme data
            all_data[name] = data

            # Save after every successful fetch
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_data, f, indent=4, ensure_ascii=False)

            print(f"✅ Fetched and saved: {name}")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching '{name}': {e}")

# Example usage: read one file of slugs, then call the function
with open("../../data/1.raw/response1.json", "r", encoding="utf-8") as file:
    data = json.load(file)

slugs = set()
for item in data.get("data", {}).get("hits", {}).get("items", []):
    slug = item.get("fields", {}).get("slug", "")
    if slug:
        slugs.add(slug)

fetch_and_append_scheme_data(setofslags, output_file="../../data/1.raw/schemes_data.json")
