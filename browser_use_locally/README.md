# Browser Use Task Automation

Browser Use Task Automation is an Open Source Version of Operator released by Open AI that leverages **Browser Use** and **Ollama** to automate various browser-based tasks. The app allows you to input any task description and automates browsing, searching, summarizing, or any web-based interaction you require.

---

## Features
- **Custom Task Input:** Enter any browser-based task description for automation.
- **Task Automation:** Automate tasks like browsing, searching, summarizing, or interacting with the web.
- **Flexible and Scalable:** Use the app for various tasks across different websites or categories.

---

## Getting Started

### 1. Clone the Repository  
Clone the GitHub repository to your local machine:  
```bash  
git clone https://github.com/reflex-dev/reflex-llm-examples.git  
cd reflex-llm-examples/browser_use_locally  
```  

### 2. Install Dependencies  
Install the required dependencies:  
```bash  
pip install -r requirements.txt  
```  

### 3. Install Playwright  
Playwright is required for browser automation. Install it by running:  
```bash  
python -m playwright install  
```  

### 4. Pull and Run DeepSeek-r1 Using Ollama  
Download and set up the **DeepSeek-r1** model locally via Ollama:  
```bash  
ollama pull qwen2.5:latest
```  

### 5. Run the Reflex App  
Run the application to start automating browser tasks:  
```bash  
reflex run  
```  

---

## Usage

Once the app is running, you can enter any browser task description (e.g., "Search for AI research papers on arXiv" or "Find the latest tech news") and click **Run Task**. The app will use **Browser Use** to execute the task as described and return the results or summaries.

---

## Example Task Description

Here’s an example of a task you can provide:

```
1. Go to https://arxiv.org
2. Search for "Artificial Intelligence" or browse AI-related categories
3. Identify the latest papers (published in the last 7 days)
4. Summarize the title, authors, abstract, and publication date for each paper
```

Or, feel free to create your own custom task descriptions for a wide range of automation needs!

--