import streamlit as st
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# === CONFIGURATION ===
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
INDEX_NAME = st.secrets["INDEX_NAME"]
TOP_K = 15
GEMINI_MODEL = "models/gemini-2.0-flash"
API_KEY = st.secrets["GEMINI_API_KEY"]

CORE_FIELDS = {"Description"}
LONG_FIELDS = {"Application Process", "Eligibility Criteria", "Documents Required", "Benefits"}

# === Initialize Clients ===
@st.cache_resource
def init_clients():
    pc = Pinecone(api_key=PINECONE_API_KEY)
    index = pc.Index(INDEX_NAME)
    embed_model = SentenceTransformer('all-MiniLM-L6-v2')
    genai.configure(api_key=API_KEY)
    gemini = genai.GenerativeModel(GEMINI_MODEL)
    return index, embed_model, gemini

index, embed_model, gemini = init_clients()

# === FUNCTIONS ===
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
        return None

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

        if idx == 0 and relevant_field:
            for match in scheme_results.matches:
                doc = match.metadata['text']
                meta = match.metadata
                if meta['field'] == relevant_field:
                    section.append(f"{relevant_field}: {doc.split(':',1)[1].strip()}")

        final_context.append("\n".join(section))

    return "\n\n---\n\n".join(final_context)

def generate_answer(query, context):
    prompt = f"""
You are an expert assistant for Indian Government Schemes with deep knowledge of welfare programs, eligibility criteria, application processes, and benefits.

CONTEXT FROM DATABASE:
{context}

USER QUESTION: "{query}"

RESPONSE QUALITY GUIDELINES:
- Provide accurate, helpful information based strictly on the retrieved context
- Use clear, simple language that any citizen can understand
- Be specific with numbers, amounts, dates, and deadlines when available
- If the user asks about application process, eligibility, or documents, be specific and detailed
- Use bullet points or numbered lists for complex procedures and requirements
- If multiple schemes are mentioned, clearly distinguish between them with proper headings
- Include relevant scheme names and ministry/department information in your response
- If the context doesn't fully answer the question, acknowledge limitations and suggest what additional information might be helpful
- Keep the tone friendly, empathetic and accessible while being informative
- Prioritize actionable information over general descriptions

RESPONSE STRUCTURE:
- Start with a direct, clear answer to the user's question
- Provide scheme-specific details with proper formatting if applicable
- Include eligibility criteria in bullet points when relevant
- List required documents clearly if mentioned
- Specify application procedures step-by-step when available
- Mention benefits/amounts/duration clearly
- End with actionable next steps or contact information if available

TONE & STYLE:
- Be encouraging and supportive, especially for welfare schemes
- Use "you" to make it personal and direct
- Avoid jargon; explain technical terms simply
- Be confident in your answers when context supports them
- Show empathy for citizens seeking government assistance
- Make complex procedures sound manageable

FORMATTING:
- Use headings for different schemes (### Scheme Name)
- Use bullet points (•) for lists
- Use numbered lists (1., 2., 3.) for step-by-step processes
- Bold important information like amounts, deadlines, eligibility
- Keep paragraphs short and scannable

Answer the user's question clearly, comprehensively, and helpfully:
"""
    response = gemini.generate_content(prompt)
    return response.text

# === STREAMLIT UI ===
st.set_page_config(page_title="IndiaGov Schemes Assistant", layout="wide")
st.title("🇮🇳 Government Schemes Assistant")
st.write("Ask about schemes, eligibility, benefits, or how to apply – chat style!")

# Session state for chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Input box
user_input = st.chat_input("Ask your question about Indian government schemes...")

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Handle new user message
if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            context = retrieve_context(user_input)
            answer = generate_answer(user_input, context)
            st.markdown(answer)

        # Store assistant response
        st.session_state.messages.append({"role": "assistant", "content": answer})

        with st.expander("🔍 View Retrieved Context (For Debugging)"):
            st.text(context)
