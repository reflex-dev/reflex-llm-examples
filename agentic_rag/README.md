# Agentic RAG with Gemini 2.0 Flash  

This is not just a simple "Chat with PDF" app. It's an **Agentic RAG (Retrieval Augmented Generation)** system powered by **Gemini 2.0 Flash**. The app first searches through the uploaded document for relevant information. If the required information is not found in the document, it seamlessly searches the web and returns a comprehensive response.  

---

## Features  
- **Upload PDF Documents:** Easily upload any PDF document to start querying.  
- **Agentic RAG Workflow:** Combines document retrieval with web search for accurate and comprehensive answers.  
- **Interactive Q&A:** Ask questions about the content of the uploaded PDF or general queries.  
- **Powered by Gemini 2.0 Flash:** Utilizes Google's Gemini 2.0 Flash model for fast and accurate responses.  
- **Web Search Integration:** If the document doesn't contain the required information, the app searches the web and provides relevant results.  

---

## Getting Started  

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/agentic_rag
```  

### 2. Install Dependencies  
Install the required dependencies:  
```bash  
pip install -r requirements.txt  
```  

### 3. Set Up Gemini API Key  
To use the Gemini 2.0 Flash model, you need a **Google API Key**. Follow these steps:  
Go to [Google AI Studio](https://aistudio.google.com/apikey), get your API Key an set the API key as an environment variable:  
   ```bash  
   export GOOGLE_API_KEY="your-api-key-here"  
   ```  

### 4. Run PgVector  
The app uses **PgVector** for vector storage and retrieval. Follow these steps to set it up:  

Install Docker Desktop first, then run:  
```bash  
docker run -d \
  -e POSTGRES_DB=ai \
  -e POSTGRES_USER=ai \
  -e POSTGRES_PASSWORD=ai \
  -e PGDATA=/var/lib/postgresql/data/pgdata \
  -v pgvolume:/var/lib/postgresql/data \
  -p 5532:5432 \
  --name pgvector \
  agnohq/pgvector:16
```  

### 5. Run the Reflex App  
Start the application to begin interacting with your PDF:  
```bash  
reflex run  
```  

---

## How It Works  
1. **Upload a PDF:** The app processes the document and creates a searchable knowledge base.  
2. **Ask Questions:** The app first searches the uploaded document for relevant information.  
3. **Web Search Fallback:** If the document doesn't contain the required information, the app searches the web using **DuckDuckGo** and returns the most relevant results.  
4. **Comprehensive Responses:** The app combines information from the document and the web to provide accurate and detailed answers.  

---

## Why Agentic RAG?  
- **Document-Centric:** Focuses on extracting information from the uploaded PDF.  
- **Web-Augmented:** Ensures no query goes unanswered by leveraging web search when needed.  
- **Efficient and Accurate:** Combines the best of both worlds for a seamless experience.  

---

## Troubleshooting  
- **Gemini API Key Not Set:** Ensure the `GOOGLE_API_KEY` environment variable is set correctly.  
- **PgVector Not Running:** Verify that the PgVector Docker container is running and accessible on port `5532`.
---

## Contributing  
Contributions are welcome! Feel free to open issues or submit pull requests to improve the app.  

---
