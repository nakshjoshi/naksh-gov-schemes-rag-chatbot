import json
import re
from pathlib import Path


import nltk
nltk.data.path.append('C:/Users/gungu/AppData/Roaming/nltk_data')
from nltk.tokenize import sent_tokenize


# === CONFIGURATION ===
INPUT_FILE = '../../data/4.clean_pre-process_data/cleaned_schemes_final.json'
OUTPUT_FILE = '../../data/5.chunking/chunked_schemes.json'

# Fields to chunk directly
FIELDS_TO_CHUNK = [
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

# Fields treated as metadata only
METADATA_FIELDS = ["Unique-ID"]

# Max tokens per chunk (approx using words count)
MAX_WORDS = 100  # Adjust based on your embedding model capacity

# === LOAD DATA ===
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    schemes = json.load(f)

chunks = []

# === PROCESS EACH SCHEME ===
for scheme in schemes:
    scheme_name = scheme.get("Scheme Name", "Unknown Scheme")
    unique_id = scheme.get("Unique-ID", "")

    for field in FIELDS_TO_CHUNK:
        content = scheme.get(field, "")
        if not content or content == "Not Available":
            continue

        # Clean content
        content = re.sub(r'\n+', '\n', content).strip()

        # If short, keep as is
        if len(content.split()) <= MAX_WORDS or field in ["Scheme Name", "Ministry/Department", "Target Beneficiaries", "Tags"]:
            chunks.append({
                "text": f"{field}: {content}",
                "scheme_name": scheme_name,
                "unique_id": unique_id,
                "field": field
            })
        else:
            # For long fields, split by sentences
            sentences = sent_tokenize(content)
            temp_chunk = ""
            for sentence in sentences:
                if len((temp_chunk + " " + sentence).split()) <= MAX_WORDS:
                    temp_chunk += " " + sentence
                else:
                    chunks.append({
                        "text": f"{field}: {temp_chunk.strip()}",
                        "scheme_name": scheme_name,
                        "unique_id": unique_id,
                        "field": field
                    })
                    temp_chunk = sentence
            if temp_chunk:
                chunks.append({
                    "text": f"{field}: {temp_chunk.strip()}",
                    "scheme_name": scheme_name,
                    "unique_id": unique_id,
                    "field": field
                })

# === SAVE CHUNKS ===
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Chunking complete! Total chunks created: {len(chunks)}")
print(f"Chunks saved to: {OUTPUT_FILE}")
