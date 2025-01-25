# Chat with PDF  

Chat with PDF is an LLM app that utilizes **Retrieval Augmented Generation (RAG)** to enable meaningful interaction with PDF files. Powered by **DeepSeek-r1** running locally, the app provides accurate answers to your questions based on the content of the uploaded PDF.  

---

## Features  
- **Upload PDF Documents:** Easily upload any PDF document to start querying.  
- **Interactive Q&A:** Ask questions about the content of the uploaded PDF.  
- **Accurate Answers:** Get precise responses using RAG and the DeepSeek-r1 model.  

---

## Getting Started  

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/chat_with_deepseek_r1_locally
```  

### 2. Install Dependencies  
Install `uv` and the required dependencies:  
```bash  
curl -LsSf https://astral.sh/uv/install.sh | sh
exec bash
uv venv && source .venv/bin/activate && uv pip sync pyproject.toml
```  

You might have to install `unzip` as well.
```bash
sudo apt-get install unzip -y
```

### 3. Pull and Run DeepSeek-r1 Using Ollama  
Download and set up the DeepSeek-r1 model locally:  
```bash  
ollama pull deepseek-r1:1.5b
```  

### 4. Run the Reflex App  
Run the application to start chatting with your PDF:  
```bash  
reflex run  
```  
