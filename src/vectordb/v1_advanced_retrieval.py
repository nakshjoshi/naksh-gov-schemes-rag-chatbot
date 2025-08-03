import chromadb
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
CHROMA_DB_DIR = '../../chroma_db'
COLLECTION_NAME = 'government_schemes_chunks'
TOP_K = 12

# Fields Setup
CORE_FIELDS = {"Ministry/Department", "Description", "Benefits"}
LONG_FIELDS = {"Application Process", "Eligibility Criteria", "Documents Required", "Benefits"}

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_collection(COLLECTION_NAME)

# Initialize embedding model
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# === FUNCTION: Retrieve Answer Context ===
def retrieve_context(user_query):
    # Step 1: Embed the query
    query_embedding = embed_model.encode([user_query])

    # Step 2: Vector search
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=TOP_K
    )

    retrieved_chunks = []

    # Step 3: Focus on Top-1 scheme
    top_metadata = results['metadatas'][0][0]
    top_scheme_id = top_metadata['parent_doc_id']
    top_scheme_name = top_metadata['scheme_name']

    # --- Fetch all chunks for the scheme ---
    all_scheme_chunks = collection.get(where={"parent_doc_id": top_scheme_id})

    # --- Auto-fetch Core Fields ---
    for doc, meta in zip(all_scheme_chunks['documents'], all_scheme_chunks['metadatas']):
        if meta['field'] in CORE_FIELDS:
            chunk_text = f"{meta['field']}: {doc.split(':', 1)[1].strip()}"
            if chunk_text not in retrieved_chunks:
                retrieved_chunks.append(chunk_text)

    # Step 4: Process retrieved chunks for sibling logic
    for doc_list, meta_list in zip(results['documents'][0], results['metadatas'][0]):
        parent_id = meta_list['parent_doc_id']
        field = meta_list['field']

        if field in LONG_FIELDS:
            # Fetch all chunks for this parent_doc_id and filter in Python
            all_sibling_chunks = collection.get(where={"parent_doc_id": parent_id})

            for sib_doc, sib_meta in zip(all_sibling_chunks['documents'], all_sibling_chunks['metadatas']):
                if sib_meta['field'] == field:
                    chunk_text = f"{sib_meta['field']}: {sib_doc.split(':', 1)[1].strip()}"
                    if chunk_text not in retrieved_chunks:
                        retrieved_chunks.append(chunk_text)
        else:
            chunk_text = f"{field}: {doc_list.split(':', 1)[1].strip()}"
            if chunk_text not in retrieved_chunks:
                retrieved_chunks.append(chunk_text)

    # Step 5: Assemble final context
    context_text = f"Scheme Name: {top_scheme_name}\n\n" + "\n\n".join(retrieved_chunks)

    return context_text

# === Example Usage ===
if __name__ == "__main__":
    query = input("Ask your question about government schemes: ")
    context = retrieve_context(query)
    print("\n==== Retrieved Context to Pass to LLM ====\n")
    print(context)
