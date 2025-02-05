# OpenDeepResearcher

This project is based on the [OpenDeepResearcher](https://github.com/mshumer/OpenDeepResearcher) repository and includes an AI researcher that continuously searches for information based on a user query until the system is confident that it has gathered all the necessary details. Built with [Reflex](https://reflex.dev/) for seamless user interaction. It makes use of several services to do so:

### Services Used:
- **SERPAPI**: To perform Google searches.
- **Jina**: To fetch and extract webpage content.
- **Google Gemini**: To interact with a LLM for generating search queries, evaluating page relevance, and extracting context.

### Features:
- **Iterative Research Loop**: The system refines its search queries iteratively until no further queries are required.
- **Asynchronous Processing**: Searches, webpage fetching, evaluation, and context extraction are performed concurrently to improve speed.
- **Duplicate Filtering**: Aggregates and deduplicates links within each round, ensuring that the same link isn’t processed twice.
- **LLM-Powered Decision Making**: Uses Google Gemini to generate new search queries, decide on page usefulness, extract relevant context, and produce a final comprehensive report.

### Requirements:
API access and keys for:
- Google Gemini API
- SERPAPI API
- Jina API

### Setup:

1. **Clone or Open the Notebook**:
   - Download the notebook file or open it directly in Google Colab.

2. **Install nest_asyncio**:
   - Run the first cell to set up nest_asyncio.

3. **Configure API Keys**:
   - Replace the placeholder values in the notebook for `GOOGLE_GEMINI_API_KEY`, `SERPAPI_API_KEY`, and `JINA_API_KEY` with your actual API keys.

---

### Getting Started

1. **Clone the Repository**  
   Clone the GitHub repository to your local machine:
   ```bash
   git clone https://github.com/reflex-dev/reflex-llm-examples.git
   cd reflex-llm-examples/open_deep_researcher
   ```

2. **Install Dependencies**  
   Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up API Keys**  
   To use the Gemini 2.0 Flash model, SERPAPI, and Jina, you need API keys for each service. Follow these steps:

   - **Google Gemini API Key**:  
     Go to [Google AI Studio](https://cloud.google.com/ai), get your API Key, and set it as an environment variable:
     ```bash
     export GOOGLE_API_KEY="your-api-key-here"
     ```

   - **SERPAPI API Key**:  
     Go to [SERPAPI](https://serpapi.com/), sign up, and obtain your API key. Set it as an environment variable:
     ```bash
     export SERPAPI_API_KEY="your-serpapi-api-key-here"
     ```

   - **Jina API Key**:  
     Go to [Jina AI](https://jina.ai/), create an account, and obtain your API key. Set it as an environment variable:
     ```bash
     export JINA_API_KEY="your-jina-api-key-here"
     ```

4. **Run the Reflex App**  
   Start the application:
   ```bash
   reflex run
   ```

---

### How It Works:
1. **Input & Query Generation**:
   - The user enters a research topic, and Google Gemini generates up to four distinct search queries.

2. **Concurrent Search & Processing**:
   - **SERPAPI**: Each search query is sent to SERPAPI concurrently.
   - **Deduplication**: All retrieved links are aggregated and deduplicated within the current iteration.
   - **Jina & Google Gemini**: Each unique link is processed concurrently to fetch webpage content via Jina, evaluate its usefulness with Google Gemini, and extract relevant information if the page is deemed useful.

3. **Iterative Refinement**:
   - The system passes the aggregated context to Google Gemini to determine if further search queries are needed. New queries are generated if required; otherwise, the loop terminates.

4. **Final Report Generation**:
   - All gathered context is compiled and sent to Google Gemini to produce a final, comprehensive report addressing the original query.

---