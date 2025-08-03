from pinecone import Pinecone
from sentence_transformers import SentenceTransformer

# === CONFIGURATION ===
PINECONE_API_KEY = "pcsk_7BBQFT_EBYYTvYSxwJdQyeEUb2ztjKJTJUzJEvP8rTEhxkAhPUU1WEsUSRkYZEG2xmaEcS"
INDEX_NAME = 'government-schemes-chunks'
TOP_K = 15

# Fields Setup
CORE_FIELDS = {"Description"}
LONG_FIELDS = {"Application Process", "Eligibility Criteria", "Documents Required", "Benefits"}

# Initialize Pinecone client
pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(INDEX_NAME)
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

# === FUNCTION: Improved Action Intent Detection ===
def detect_relevant_field(query):
    query = query.lower()
    if any(word in query for word in ["apply", "application", "register", "procedure", "how to avail"]):
        return "Application Process"
    elif "benefit" in query or "advantages" in query:
        return "Benefits"
    elif "eligibility" in query or "eligible" in query or "who can apply" in query:
        return "Eligibility Criteria"
    elif "document" in query or "paperwork" in query:
        return "Documents Required"
    else:
        return None  # No forced field if intent isn't clear

# === FUNCTION: Retrieve Answer Context ===
def retrieve_context(user_query):
    relevant_field = detect_relevant_field(user_query)
    query_embedding = embed_model.encode([user_query]).tolist()

    results = index.query(
        vector=query_embedding,
        top_k=TOP_K,
        include_metadata=True
    )

    # Extract documents and metadata from Pinecone results
    docs = [match.metadata['text'] for match in results.matches]
    metas = [match.metadata for match in results.matches]

    # Identify Top-2 unique schemes
    scheme_order = []
    for meta in metas:
        pid = meta['parent_doc_id']
        if pid not in scheme_order:
            scheme_order.append(pid)
        if len(scheme_order) == 2:
            break

    final_context = []

    for idx, pid in enumerate(scheme_order):
        # Query Pinecone for all chunks of this scheme
        scheme_results = index.query(
            vector=[0] * 384,  # Dummy vector, we'll filter by metadata
            filter={"parent_doc_id": pid},
            top_k=50,  # Get enough chunks for the scheme
            include_metadata=True
        )
        
        scheme_name = ""
        section = []

        for match in scheme_results.matches:
            doc = match.metadata['text']
            meta = match.metadata
            field = meta['field']
            if field == "Scheme Name" and not scheme_name:
                scheme_name = doc.split(":",1)[1].strip()
                section.append(f"Scheme Name: {scheme_name}")
            if field in CORE_FIELDS:
                section.append(f"{field}: {doc.split(':',1)[1].strip()}")

        # === Action Intent Handling for Top-1 Scheme ===
        if idx == 0 and relevant_field:
            for match in scheme_results.matches:
                doc = match.metadata['text']
                meta = match.metadata
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
