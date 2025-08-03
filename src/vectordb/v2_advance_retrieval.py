import chromadb
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
CHROMA_DB_DIR = '../../chroma_db'
COLLECTION_NAME = 'government_schemes_chunks'
TOP_K = 15   # Fetch enough chunks to detect Top-2 schemes

# Fields Setup
CORE_FIELDS = {"Description"}
LONG_FIELDS = {"Application Process", "Eligibility Criteria", "Documents Required", "Benefits"}

# Initialize ChromaDB client
client = chromadb.PersistentClient(path=CHROMA_DB_DIR)
collection = client.get_collection(COLLECTION_NAME)

# Initialize embedding model
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# === FUNCTION: Detect Query-Relevant Field ===
def detect_relevant_field(query):
    query = query.lower()
    if "apply" in query or "application" in query:
        return "Application Process"
    elif "benefit" in query:
        return "Benefits"
    elif "eligibility" in query or "eligible" in query:
        return "Eligibility Criteria"
    elif "document" in query:
        return "Documents Required"
    else:
        return "Eligibility Criteria"   # Default fallback

# === FUNCTION: Retrieve Answer Context ===
def retrieve_context(user_query):
    relevant_field = detect_relevant_field(user_query)

    query_embedding = embed_model.encode([user_query])

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=TOP_K
    )

    docs = results['documents'][0]
    metas = results['metadatas'][0]

    # Identify Top-2 unique schemes
    scheme_order = []
    scheme_chunks = {}

    for doc, meta in zip(docs, metas):
        pid = meta['parent_doc_id']
        if pid not in scheme_order:
            scheme_order.append(pid)
            if len(scheme_order) == 2:
                break

    # Group chunks by scheme
    for doc, meta in zip(docs, metas):
        pid = meta['parent_doc_id']
        if pid in scheme_order:
            scheme_chunks.setdefault(pid, []).append((doc, meta))

    final_context = []

    for idx, pid in enumerate(scheme_order):
        scheme_data = collection.get(where={"parent_doc_id": pid})
        scheme_name = ""
        section = []

        for doc, meta in zip(scheme_data['documents'], scheme_data['metadatas']):
            field = meta['field']
            if field == "Scheme Name" and not scheme_name:
                scheme_name = doc.split(":",1)[1].strip()
                section.append(f"Scheme Name: {scheme_name}")

            if field in CORE_FIELDS:
                section.append(f"{field}: {doc.split(':',1)[1].strip()}")

        if idx == 0:
            # For Top-1 Scheme ➜ Fetch relevant field + siblings
            if relevant_field:
                all_chunks = collection.get(where={"parent_doc_id": pid})
                for doc, meta in zip(all_chunks['documents'], all_chunks['metadatas']):
                    if meta['field'] == relevant_field:
                        section.append(f"{relevant_field}: {doc.split(':',1)[1].strip()}")

        final_context.append("\n".join(section))

    return "\n\n---\n\n".join(final_context)

# === Example Usage ===
if __name__ == "__main__":
    query = input("Ask your question about government schemes: ")
    context = retrieve_context(query)
    print("\n==== Retrieved Context to Pass to LLM ====\n")
    print(context)
