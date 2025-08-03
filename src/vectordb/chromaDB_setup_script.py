import json
import os
import uuid
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
import time

# Paths
INPUT_JSON = '../../data/5.chunking/hybrid_chunked_schemes.json'
INDEX_NAME = 'government-schemes-chunks'

# Pinecone Configuration
PINECONE_API_KEY = "pcsk_7BBQFT_EBYYTvYSxwJdQyeEUb2ztjKJTJUzJEvP8rTEhxkAhPUU1WEsUSRkYZEG2xmaEcS"
DIMENSION = 384  # Dimension for all-MiniLM-L6-v2 model

# Load chunked data
with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    chunks = json.load(f)

# Initialize Pinecone
pc = Pinecone(api_key=PINECONE_API_KEY)

# Create index if it doesn't exist
if INDEX_NAME not in pc.list_indexes().names():
    pc.create_index(
        name=INDEX_NAME,
        dimension=DIMENSION,
        metric='cosine',
        spec=ServerlessSpec(
            cloud='aws',
            region='us-east-1'
        )
    )
    # Wait for index to be ready
    print("Creating index... This may take a moment.")
    time.sleep(30)  # Give it time to initialize
else:
    # Check if the existing index has the right dimension
    index_stats = pc.describe_index(INDEX_NAME)
    if index_stats.dimension != DIMENSION:
        print(f"⚠️ Index exists but has wrong dimension ({index_stats.dimension} vs {DIMENSION})")
        print("Deleting existing index and creating a new one...")
        pc.delete_index(INDEX_NAME)
        time.sleep(10)  # Wait for deletion
        pc.create_index(
            name=INDEX_NAME,
            dimension=DIMENSION,
            metric='cosine',
            spec=ServerlessSpec(
                cloud='aws',
                region='us-east-1'
            )
        )
        print("Creating new index... This may take a moment.")
        time.sleep(30)  # Give it time to initialize

# Connect to the index
index = pc.Index(INDEX_NAME)

# Initialize embedding model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Prepare data for indexing
vectors_to_upsert = []

for chunk in tqdm(chunks, desc="Processing chunks"):
    text = chunk['text']
    chunk_id = chunk['chunk_id']
    metadata = {
        'parent_doc_id': chunk['parent_doc_id'],
        'field': chunk['field'],
        'scheme_name': chunk['scheme_name'],
        'text': text  # Store the text in metadata for retrieval
    }
    
    # Generate embedding for this chunk
    embedding = model.encode(text).tolist()
    
    # Prepare vector for upsert
    vectors_to_upsert.append({
        'id': chunk_id,
        'values': embedding,
        'metadata': metadata
    })

# Upsert vectors to Pinecone in batches
BATCH_SIZE = 100  # Pinecone recommends smaller batch sizes

for i in tqdm(range(0, len(vectors_to_upsert), BATCH_SIZE), desc="Storing in Pinecone"):
    batch = vectors_to_upsert[i:i+BATCH_SIZE]
    index.upsert(vectors=batch)

# Wait for upserts to be processed
time.sleep(2)

# Get index stats
stats = index.describe_index_stats()
print(f"✅ Indexed {stats['total_vector_count']} chunks into Pinecone index '{INDEX_NAME}'.")
print(f"📊 Index Stats: {stats}")
