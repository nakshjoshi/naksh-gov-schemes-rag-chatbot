import streamlit as st
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
import google.generativeai as genai
from deep_translator import GoogleTranslator
from langdetect import detect
import warnings
st.set_page_config(page_title="IndiaGov Schemes Assistant", layout="wide")
warnings.filterwarnings("ignore")



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

def generate_answer(query, context, language='en'):
    if language == 'hi':
        prompt = f"""
You are an expert assistant for Indian Government Schemes (भारतीय सरकारी योजनाएं). You MUST respond ONLY in Hindi (हिंदी में जवाब दें).

CONTEXT FROM DATABASE:
{context}

USER QUESTION: "{query}"

IMPORTANT: Respond completely in Hindi language only. Do not use English except for official scheme names if necessary.

RESPONSE GUIDELINES (हिंदी में जवाब देने के नियम):
- सभी जानकारी सिर्फ हिंदी में दें
- सरकारी योजनाओं की सटीक जानकारी दें जो context में दी गई है
- संख्या, राशि, तारीखें जब उपलब्ध हों तो स्पष्ट रूप से बताएं
- अगर user आवेदन प्रक्रिया, पात्रता, या दस्तावेज़ों के बारे में पूछे तो विस्तार से बताएं
- जटिल प्रक्रियाओं के लिए bullet points या numbered lists का उपयोग करें
- अगर कई योजनाएं हैं तो उन्हें अलग-अलग headings के साथ बताएं
- योजना के नाम और मंत्रालय/विभाग की जानकारी शामिल करें
- यदि context में पूरी जानकारी नहीं है तो इसे स्वीकार करें और अगले कदम सुझाएं
- सम्मानजनक, मित्रवत और सुलभ भाषा का उपयोग करें
- व्यावहारिक जानकारी को प्राथमिकता दें जो नागरिकों को अगले कदम उठाने में मदद करे

उत्तर दें:
"""
    else:
        prompt = f"""
You are an expert assistant for Indian Government Schemes. You MUST respond ONLY in English.

CONTEXT FROM DATABASE:
{context}

USER QUESTION: "{query}"

IMPORTANT: Respond completely in English language only.

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

Answer the user's question clearly and comprehensively:
"""
    
    response = genai.GenerativeModel(GEMINI_MODEL).generate_content(prompt)
    return response.text

# === STREAMLIT UI ===
st.title("🇮🇳 Government Schemes Assistant")
st.write("Ask about schemes, eligibility, benefits, or how to apply – chat style! (Supports Hindi 🇮🇳)")

if "messages" not in st.session_state:
    st.session_state.messages = []

user_input = st.chat_input("💬 अपने प्रश्न पूछें या Type your question...")

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
            # Detect language
            lang = detect(user_input)
            
            # For Hindi questions, translate to English for retrieval but answer in Hindi
            if lang == 'hi':
                query_en = GoogleTranslator(source='auto', target='en').translate(user_input)
                context = retrieve_context(query_en)
                answer = generate_answer(user_input, context, language='hi')  # Pass original Hindi query and language
            else:
                # For English questions, keep everything in English
                context = retrieve_context(user_input)
                answer = generate_answer(user_input, context, language='en')
            
            st.markdown(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})

        with st.expander("🔍 View Retrieved Context (For Debugging)"):
            st.text(context)
