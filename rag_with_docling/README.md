# Chat with Excel Files using Docling and   

Chat with Excel is an LLM app that utilizes **Retrieval Augmented Generation (RAG)** to enable meaningful interaction with Excel files. Powered by **DeepSeek-r1** running locally and [Docling Library](https://github.com/DS4SD/docling), the app provides accurate answers to your questions based on the content of the uploaded Excel file.  

---

## Features  
- **Upload Excel Documents:** Easily upload any Excel document to start querying.  
- **Interactive Q&A:** Ask questions about the content of the uploaded Excel.  
- **Accurate Answers:** Get precise responses using RAG and the DeepSeek-r1 model.  

---

## Getting Started  

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/rag_with_docling
```  

### 2. Install Dependencies  
Install the required dependencies:  
```bash  
pip install -r requirements.txt  
```  

### 3. Pull and Run DeepSeek-r1 Using Ollama  
Download and set up the DeepSeek-r1 model locally:  
```bash  
ollama pull deepseek-r1:1.5b
```  

### 4. Run the Reflex App  
Run the application to start chatting with your Excel File:  
```bash  
reflex run  
```  
