
# MySchemeMultiLingualBot

A **Conversational AI Assistant** to help citizens easily query Indian government schemes using a smart **Chunked Retrieval-Augmented Generation (CRAG)** pipeline. This assistant supports both **English** and **Hindi**, combining efficient vector search with LLM-powered responses.

---

## Project Overview

With thousands of government schemes spread across various ministries, citizens often struggle to find accurate and relevant information. This project solves that problem by:

- Using **vector search** to fetch only the most relevant scheme data.
- Leveraging **Google Gemini 2.0 Flash** for generating clear, conversational answers.
- Supporting multilingual queries (**English** & **Hindi**) with real-time translation.
- Providing a simple, interactive UI built with **Streamlit**.

---

## Tech Stack

- **Python** – Core language
- **ChromaDB** – Local vector database for efficient retrieval
- **Sentence Transformers** – `all-MiniLM-L6-v2` for generating embeddings
- **Google Gemini 2.0 Flash** – LLM for generating responses
- **Streamlit** – Frontend conversational UI
- **Deep Translator** – For handling Hindi ↔ English translations
- **Selenium + Chrome WebDriver** – For advanced web scraping
- **NLTK** – For token-aware chunking and sentence handling

---

## Key Features

- 🔹 **Multilingual Support** – Ask queries in **Hindi** or **English**.
- 🔹 **Smart Retrieval** – Fetches only relevant chunks to stay within LLM token limits.
- 🔹 **Optimized Cost & Speed** – Uses CRAG to minimize unnecessary LLM calls.
- 🔹 **Simple UI** – Clean chat interface powered by Streamlit.
- 🔹 **Custom Chunking Strategy** – Hybrid approach to handle verbose government data effectively.


---

## How to Run the Project

Follow these steps to get the assistant up and running locally:

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/your-username/MySchemeMultiLingualBot.git
cd MySchemeMultiLingualBot
```

### 2️⃣ Install Required Packages
```bash
pip install -r requirements.txt
```

### 3️⃣ Navigate to the App Directory
```bash
cd src/app
```

### 4️⃣ Run the Hindi Conversational App
```bash
python -m streamlit run hindiConvoApp.py
```

💡 For the English-only version, run:
```bash
python -m streamlit run convoApp.py
```

### 5️⃣ Open in Browser
Streamlit will provide a local URL, typically:
```
http://localhost:8501
```

---

## Prerequisites

- **Python** 3.8+
- **Google Gemini API Key**  
  Ensure it's configured in your environment or directly within the app script.
- **Google Chrome** installed (required for Selenium-based scraping tasks).

---

