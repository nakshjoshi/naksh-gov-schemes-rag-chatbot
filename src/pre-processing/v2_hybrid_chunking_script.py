
import json
import re
import uuid
from nltk.tokenize import sent_tokenize
from transformers import AutoTokenizer

# Load tokenizer for token-based chunking
tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

# Configuration
INPUT_FILE = '../../data/4.clean_pre-process_data/cleaned_schemes_final.json'
OUTPUT_FILE = '../../data/5.chunking/hybrid_chunked_schemes.json'

SMALL_FIELDS = ["Scheme Name", "Ministry/Department", "Target Beneficiaries", "Tags", "Description"]
MEDIUM_FIELDS = ["Benefits", "Eligibility Criteria", "Documents Required"]
LARGE_FIELD = "Application Process"

MAX_WORDS = 300
MAX_TOKENS = 450

# Load data
with open(INPUT_FILE, "r", encoding="utf-8") as f:
    schemes = json.load(f)

chunks = []

def clean_text(text):
    return re.sub(r'\n+', '\n', text).strip()

def word_based_chunking(content, field, scheme_name, unique_id):
    sentences = sent_tokenize(content)
    temp_chunk = ""
    for sentence in sentences:
        if len((temp_chunk + " " + sentence).split()) <= MAX_WORDS:
            temp_chunk += " " + sentence
        else:
            chunks.append(create_chunk(temp_chunk.strip(), field, scheme_name, unique_id))
            temp_chunk = sentence
    if temp_chunk:
        chunks.append(create_chunk(temp_chunk.strip(), field, scheme_name, unique_id))

def token_based_chunking(content, field, scheme_name, unique_id):
    sentences = sent_tokenize(content)
    temp_chunk = ""
    for sentence in sentences:
        token_count = len(tokenizer.encode(temp_chunk + " " + sentence, add_special_tokens=False))
        if token_count <= MAX_TOKENS:
            temp_chunk += " " + sentence
        else:
            chunks.append(create_chunk(temp_chunk.strip(), field, scheme_name, unique_id))
            temp_chunk = sentence  # Overlap handled naturally
    if temp_chunk:
        chunks.append(create_chunk(temp_chunk.strip(), field, scheme_name, unique_id))

def create_chunk(content, field, scheme_name, unique_id):
    return {
        "chunk_id": str(uuid.uuid4()),
        "parent_doc_id": unique_id,
        "text": f"{field}: {content}",
        "scheme_name": scheme_name,
        "field": field
    }

# Process each scheme
for scheme in schemes:
    scheme_name = scheme.get("Scheme Name", "Unknown Scheme").strip()
    unique_id = scheme.get("Unique-ID", str(uuid.uuid4()))

    for field in SMALL_FIELDS + MEDIUM_FIELDS + [LARGE_FIELD]:
        content = scheme.get(field, "")
        if not content or content.strip().lower() in ["not available", "n/a"]:
            continue

        content = clean_text(content)

        if field in SMALL_FIELDS:
            chunks.append(create_chunk(content, field, scheme_name, unique_id))
        elif field in MEDIUM_FIELDS:
            if len(content.split()) <= MAX_WORDS:
                chunks.append(create_chunk(content, field, scheme_name, unique_id))
            else:
                word_based_chunking(content, field, scheme_name, unique_id)
        elif field == LARGE_FIELD:
            if len(tokenizer.encode(content, add_special_tokens=False)) <= MAX_TOKENS:
                chunks.append(create_chunk(content, field, scheme_name, unique_id))
            else:
                token_based_chunking(content, field, scheme_name, unique_id)

# Save the chunks
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(chunks, f, ensure_ascii=False, indent=2)

print(f"✅ Chunking complete! Total chunks created: {len(chunks)}")
print(f"Chunks saved to: {OUTPUT_FILE}")
