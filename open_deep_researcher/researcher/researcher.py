import reflex as rx
import aiohttp
import json
import asyncio
import ast
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
import time

# ---------------------------
# Configuration Constants
# ---------------------------
GEMINI_API_KEY = "ADD_YOUR_GEMINI_API_KEY"
SERPAPI_API_KEY = "ADD_YOUR_SERPAPI_API_KEY"
JINA_API_KEY = "ADD_YOUR_JINA_API_KEY"

SERPAPI_URL = "https://serpapi.com/search"
JINA_BASE_URL = "https://r.jina.ai/"

genai.configure(api_key=GEMINI_API_KEY)

async def call_google_gemini(messages: List[Dict]) -> Optional[str]:
    """Call Google Gemini asynchronously."""
    try:
        prompt = "\n".join([msg["content"] for msg in messages])
        model = genai.GenerativeModel('gemini-1.5-flash')
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: model.generate_content(prompt))
        return response.text
    except Exception as e:
        return None

async def generate_search_queries_async(session: aiohttp.ClientSession, user_query: str) -> List[str]:
    """Generate search queries based on user query."""
    prompt = (
        "You are an expert research assistant. Given the user's query, generate up to four distinct, "
        "precise search queries that would help gather complete information on the topic. "
        "Return only a valid list of plain strings. Do not include markdown, code blocks, backticks, or explanations. "
        "Just return the list itself, for example: ['query1', 'query2', 'query3'].")
    messages = [
        {"role": "system", "content": "You are a helpful and precise research assistant."},
        {"role": "user", "content": f"User Query: {user_query}\n\n{prompt}"}
    ]
    response = await call_google_gemini(messages)
    if response:
        try:
            queries = eval(response.strip("`").strip())
            return queries if isinstance(queries, list) else []
        except Exception:
            return []
    return []

async def perform_search_async(session: aiohttp.ClientSession, query: str) -> List[str]:
    """Perform search using SERPAPI."""
    params = {
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "engine": "google"
    }
    try:
        async with session.get(SERPAPI_URL, params=params) as resp:
            if resp.status == 200:
                results = await resp.json()
                return [item.get("link") for item in results.get("organic_results", []) if "link" in item]
            return []
    except Exception:
        return []

async def fetch_webpage_text_async(session: aiohttp.ClientSession, url: str) -> str:
    """Fetch webpage text using Jina API."""
    full_url = f"{JINA_BASE_URL}{url}"
    headers = {"Authorization": f"Bearer {JINA_API_KEY}"}
    try:
        async with session.get(full_url, headers=headers) as resp:
            return await resp.text() if resp.status == 200 else ""
    except Exception:
        return ""

async def is_page_useful_async(session: aiohttp.ClientSession, user_query: str, page_text: str) -> bool:
    """Determine if the page content is useful for the query."""
    prompt = (
        "You are a critical research evaluator. Given the user's query and the content of a webpage, "
        "determine if the webpage contains information that is useful for addressing the query. "
        "Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not."
    )
    messages = [
        {"role": "system", "content": "You are a strict and concise evaluator of research relevance."},
        {"role": "user", "content": f"User Query: {user_query}\n\nWebpage Content:\n{page_text[:20000]}\n\n{prompt}"}
    ]
    response = await call_google_gemini(messages)
    return response and response.strip().lower() == "yes"

async def extract_relevant_context_async(
    session: aiohttp.ClientSession, 
    user_query: str, 
    search_query: str, 
    page_text: str
) -> str:
    """Extract relevant information from page content."""
    prompt = (
        "Extract all pieces of information that are useful for answering the user's query. "
        "Return only the relevant context as plain text."
    )
    messages = [
        {"role": "system", "content": "You are an expert in extracting relevant information."},
        {"role": "user", "content": f"Query: {user_query}\nSearch Query: {search_query}\n\nContent:\n{page_text[:20000]}\n\n{prompt}"}
    ]
    response = await call_google_gemini(messages)
    return response.strip() if response else ""

async def get_new_search_queries_async(
    session: aiohttp.ClientSession,
    user_query: str,
    previous_queries: List[str],
    contexts: List[str]
) -> List[str]:
    """Generate new search queries based on current findings."""
    prompt = (
        "Based on the findings so far, generate new search queries if needed. "
        "Return a Python list of strings, or an empty list if no more queries are needed."
    )
    messages = [
        {"role": "system", "content": "You are a systematic research planner."},
        {"role": "user", "content": f"Query: {user_query}\nPrevious: {previous_queries}\nContexts:\n{''.join(contexts)}\n\n{prompt}"}
    ]
    response = await call_google_gemini(messages)
    if response:
        try:
            queries = eval(response.strip("`").strip())
            return queries if isinstance(queries, list) else []
        except Exception:
            return []
    return []

async def generate_final_report_async(
    session: aiohttp.ClientSession,
    user_query: str,
    contexts: List[str]
) -> str:
    """Generate final research report."""
    prompt = (
        "Write a complete, well-structured report based on the gathered information in a markdown format. "
        "Include all useful insights and conclusions."
    )
    messages = [
        {"role": "system", "content": "You are a skilled report writer."},
        {"role": "user", "content": f"Query: {user_query}\nContexts:\n{''.join(contexts)}\n\n{prompt}"}
    ]
    response = await call_google_gemini(messages)
    return response if response else "Unable to generate report."

class ResearchState(rx.State):
    """State management for the research assistant."""
    user_query: str = ""
    iteration_limit: int = 2
    final_report: str = ""
    process_logs: list
    is_processing: bool = False

    def update_logs(self, message: str):
        """Update process logs with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if self.process_logs:
            self.process_logs += f"\n[{timestamp}] {message}"
        else:
            self.process_logs = f"[{timestamp}] {message}"


    async def process_link(self, session: aiohttp.ClientSession, link: str, search_query: str) -> Optional[str]:
        """Process a single link and extract relevant information."""
        page_text = await fetch_webpage_text_async(session, link)
        if not page_text:
            return None

        if await is_page_useful_async(session, self.user_query, page_text):
            context = await extract_relevant_context_async(session, self.user_query, search_query, page_text)
            return context
        return None

    async def handle_submit(self):
        """Handle research submission."""
        self.is_processing = True
        self.final_report = ""
        self.process_logs = ""
        self.update_logs("Starting research process...")
        yield
        await asyncio.sleep(0.1)

        try:
            async with aiohttp.ClientSession() as session:
                self.update_logs("Generating initial search queries...")
                yield
                    
                queries = await generate_search_queries_async(session, self.user_query)
                if not queries:
                    self.update_logs("No initial queries could be generated")
                    yield
                    return

                self.update_logs(f"Generated {len(queries)} initial queries: {', '.join(queries)}")
                yield

                contexts = []
                iteration = 0
                    
                while iteration < self.iteration_limit:
                    self.update_logs(f"Starting research iteration {iteration + 1}")
                    yield

                    all_links = []
                    for query in queries:
                        if len(all_links) >= 10:
                            break

                        self.update_logs(f"Searching for: {query}")
                        yield
                        links = await perform_search_async(session, query)

                        for link in links:
                            if len(all_links) >= 10:
                                break
                            all_links.extend(links)
                    
                    self.update_logs(f"Found {len(all_links)} links to process")
                    yield

                    iteration_contexts = []
                    for link in all_links:
                        self.update_logs(f"Processing link: {link}")
                        yield  # Update UI after log entry
                        
                        context = await self.process_link(session, link, query)
                        if context:
                            self.update_logs("Successfully extracted relevant information")
                            iteration_contexts.append(context)
                            yield  # Update UI after successful extraction
                        else:
                            self.update_logs("No useful information found in link")
                            yield
                    
                    self.update_logs(f"Extracted information from {len(iteration_contexts)} sources")
                    yield
                    
                    contexts.extend(iteration_contexts)
                    queries = await get_new_search_queries_async(session, self.user_query, queries, contexts)
                    
                    if not queries:
                        self.update_logs("No more queries needed, research complete")
                        yield
                        break
                    
                    self.update_logs(f"Generated {len(queries)} new queries for next iteration")
                    yield
                    iteration += 1

                self.update_logs("Generating final research report...")
                yield
                self.final_report = await generate_final_report_async(session, self.user_query, contexts)
                self.update_logs("Research process completed successfully")

        except Exception as e:
            self.update_logs(f"Error occurred: {str(e)}")
        finally:
            self.is_processing = False
        yield
    
def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            rx.heading("Open Deep Researcher 🔬", size="8", margin_bottom="1rem", margin_left="16rem"),
            rx.text("Enter your research query to generate a report."),
            
            # Input Section
            rx.box(
                rx.vstack(
                    rx.input(
                        placeholder="Research Query/Topic",
                        value=ResearchState.user_query,
                        on_change=ResearchState.set_user_query,
                        width="100%",
                    ),
                    rx.button(
                        "Start Research",
                        on_click=ResearchState.handle_submit,
                        loading=ResearchState.is_processing,
                        color_scheme="blue",
                        width="40%",
                        align_self="center",
                    ),
                    spacing="3",
                ),
                width="100%",
                padding="1rem",
                border="1px solid #e0e0e0",
                border_radius="lg",
            ),
            
            # Results Section
            rx.cond(
                ResearchState.final_report,
                rx.box(
                    rx.vstack(
                        rx.heading("Final Report", size="4"),
                        rx.markdown(ResearchState.final_report),
                        spacing="2",
                    ),
                    width="100%",
                    padding="1rem",
                    border="1px solid #e0e0e0",
                    border_radius="lg",
                    margin_top="1rem",
                ),
            ),
            
            # Logs Section
            rx.cond(
                ResearchState.process_logs,
                rx.box(
                    rx.vstack(
                        rx.heading("Process Logs", size="4"),
                        rx.markdown(ResearchState.process_logs),
                        spacing="2",
                    ),
                    width="100%",
                    height="400px",
                    padding="1rem",
                    border="1px solid #e0e0e0",
                    border_radius="lg",
                    margin_top="1rem",
                    overflow_y="auto",
                ),
            ),
            spacing="4",
            width="100%",
            max_width="1200px",
        ),
        padding="2rem",
    )

# Create app
app = rx.App()
app.add_page(index, title="Research Assistant")