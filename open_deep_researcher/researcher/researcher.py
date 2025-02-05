import reflex as rx
import aiohttp
import json
import asyncio
import ast
from typing import List, Dict, Optional, Tuple
import google.generativeai as genai
import time
import os

# ---------------------------
# Configuration Constants
# ---------------------------


GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
SERPAPI_API_KEY = os.environ.get("SERPAPI_API_KEY")
JINA_API_KEY = os.environ.get("JINA_API_KEY")

SERPAPI_URL = "https://serpapi.com/search"
JINA_BASE_URL = "https://r.jina.ai/"

genai.configure(api_key=GEMINI_API_KEY)


async def call_google_gemini(messages: List[Dict]) -> Optional[str]:
    """Call Google Gemini asynchronously."""
    try:
        prompt = "\n".join([msg["content"] for msg in messages])
        model = genai.GenerativeModel("gemini-1.5-flash")
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, lambda: model.generate_content(prompt)
        )
        return response.text
    except Exception as e:
        return None


async def generate_search_queries_async(
    session: aiohttp.ClientSession, user_query: str
) -> List[str]:
    """Generate search queries based on user query."""
    prompt = (
        "You are an expert research assistant. Given the user's query, generate up to four distinct, "
        "precise search queries that would help gather complete information on the topic. "
        "Return only a valid list of plain strings. Do not include markdown, code blocks, backticks, or explanations. "
        "Just return the list itself, for example: ['query1', 'query2', 'query3']."
    )
    messages = [
        {
            "role": "system",
            "content": "You are a helpful and precise research assistant.",
        },
        {"role": "user", "content": f"User Query: {user_query}\n\n{prompt}"},
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
    params = {"q": query, "api_key": SERPAPI_API_KEY, "engine": "google"}
    try:
        async with session.get(SERPAPI_URL, params=params) as resp:
            if resp.status == 200:
                results = await resp.json()
                return [
                    item.get("link")
                    for item in results.get("organic_results", [])
                    if "link" in item
                ]
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


async def is_page_useful_async(
    session: aiohttp.ClientSession, user_query: str, page_text: str
) -> bool:
    """Determine if the page content is useful for the query."""
    prompt = (
        "You are a critical research evaluator. Given the user's query and the content of a webpage, "
        "determine if the webpage contains information that is useful for addressing the query. "
        "Respond with exactly one word: 'Yes' if the page is useful, or 'No' if it is not."
    )
    messages = [
        {
            "role": "system",
            "content": "You are a strict and concise evaluator of research relevance.",
        },
        {
            "role": "user",
            "content": f"User Query: {user_query}\n\nWebpage Content:\n{page_text[:20000]}\n\n{prompt}",
        },
    ]
    response = await call_google_gemini(messages)
    return response and response.strip().lower() == "yes"


async def extract_relevant_context_async(
    session: aiohttp.ClientSession, user_query: str, search_query: str, page_text: str
) -> str:
    """Extract relevant information from page content."""
    prompt = (
        "Extract all pieces of information that are useful for answering the user's query. "
        "Return only the relevant context as plain text."
    )
    messages = [
        {
            "role": "system",
            "content": "You are an expert in extracting relevant information.",
        },
        {
            "role": "user",
            "content": f"Query: {user_query}\nSearch Query: {search_query}\n\nContent:\n{page_text[:20000]}\n\n{prompt}",
        },
    ]
    response = await call_google_gemini(messages)
    return response.strip() if response else ""


async def get_new_search_queries_async(
    session: aiohttp.ClientSession,
    user_query: str,
    previous_queries: List[str],
    contexts: List[str],
) -> List[str]:
    """Generate new search queries based on current findings."""
    prompt = (
        "Based on the findings so far, generate new search queries if needed. "
        "Return a Python list of strings, or an empty list if no more queries are needed."
    )
    messages = [
        {"role": "system", "content": "You are a systematic research planner."},
        {
            "role": "user",
            "content": f"Query: {user_query}\nPrevious: {previous_queries}\nContexts:\n{''.join(contexts)}\n\n{prompt}",
        },
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
    session: aiohttp.ClientSession, user_query: str, contexts: List[str]
) -> str:
    """Generate final research report."""
    prompt = (
        "Write a complete, well-structured report based on the gathered information in a markdown format. "
        "Include all useful insights and conclusions."
    )
    messages = [
        {"role": "system", "content": "You are a skilled report writer."},
        {
            "role": "user",
            "content": f"Query: {user_query}\nContexts:\n{''.join(contexts)}\n\n{prompt}",
        },
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
    copy_success: bool = False

    def clear_form(self):
        """Clear the form and reset state."""
        self.user_query = ""
        self.final_report = ""
        self.process_logs = ""
        self.is_processing = False
        self.copy_success = False

    def new_research(self):
        """Start a new research session."""
        self.clear_form()

    def update_logs(self, message: str):
        """Update process logs with timestamp."""
        timestamp = time.strftime("%H:%M:%S")
        if self.process_logs:
            self.process_logs += f"\n[{timestamp}] {message}"
        else:
            self.process_logs = f"[{timestamp}] {message}"

    async def process_link(
        self, session: aiohttp.ClientSession, link: str, search_query: str
    ) -> Optional[str]:
        """Process a single link and extract relevant information."""
        page_text = await fetch_webpage_text_async(session, link)
        if not page_text:
            return None

        if await is_page_useful_async(session, self.user_query, page_text):
            context = await extract_relevant_context_async(
                session, self.user_query, search_query, page_text
            )
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

                self.update_logs(
                    f"Generated {len(queries)} initial queries: {', '.join(queries)}"
                )
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
                            self.update_logs(
                                "Successfully extracted relevant information"
                            )
                            iteration_contexts.append(context)
                            yield  # Update UI after successful extraction
                        else:
                            self.update_logs("No useful information found in link")
                            yield

                    self.update_logs(
                        f"Extracted information from {len(iteration_contexts)} sources"
                    )
                    yield

                    contexts.extend(iteration_contexts)
                    queries = await get_new_search_queries_async(
                        session, self.user_query, queries, contexts
                    )

                    if not queries:
                        self.update_logs("No more queries needed, research complete")
                        yield
                        break

                    self.update_logs(
                        f"Generated {len(queries)} new queries for next iteration"
                    )
                    yield
                    iteration += 1

                self.update_logs("Generating final research report...")
                yield
                self.final_report = await generate_final_report_async(
                    session, self.user_query, contexts
                )
                self.update_logs("Research process completed successfully")

        except Exception as e:
            self.update_logs(f"Error occurred: {str(e)}")
        finally:
            self.is_processing = False
        yield

    async def copy_to_clipboard(self):
        """Copy report to clipboard and show success state."""
        # Set clipboard content using JavaScript
        yield rx.set_clipboard(self.final_report)

        # Show success state
        self.copy_success = True
        yield
        await asyncio.sleep(2)
        self.copy_success = False
        yield

    def export_to_pdf(self):
        """Trigger PDF export using browser's print functionality."""
        return rx.call_script(
            """
            const content = document.querySelector('#research-report').innerHTML;
            const printWindow = window.open('', '_blank');
            printWindow.document.write(`
                <html>
                    <head>
                        <title>Research Report</title>
                        <style>
                            body { font-family: Arial, sans-serif; padding: 20px; }
                            h1, h2, h3 { color: #2B6CB0; }
                        </style>
                    </head>
                    <body>${content}</body>
                </html>
            `);
            printWindow.document.close();
            printWindow.print();
        """
        )


def index() -> rx.Component:
    return rx.container(
        rx.vstack(
            # Header Section
            rx.hstack(
                rx.icon("microscope", color="blue.500", size=24),
                rx.heading("Open Deep Researcher", size="3"),
                spacing="3",
                align="center",
                margin_bottom="2rem",
            ),
            rx.text(
                "Enter your research query to generate a comprehensive report.",
                color="gray.600",
                font_size="lg",
                margin_bottom="2rem",
            ),
            # Input Section
            rx.card(
                rx.vstack(
                    rx.text_area(
                        placeholder="Enter your research query here...",
                        value=ResearchState.user_query,
                        on_change=ResearchState.set_user_query,
                        min_height="200px",
                        size="2",
                        border="1px solid",
                        border_color="gray.200",
                        _focus={
                            "border_color": "blue.500",
                            "box_shadow": "0 0 0 1px rgb(49, 130, 206)",
                        },
                    ),
                    rx.hstack(
                        rx.spacer(),  # This pushes the buttons to the right
                        rx.button(
                            rx.hstack(
                                rx.icon("search", size=16),
                                rx.text("Start Research"),
                                spacing="2",
                            ),
                            on_click=ResearchState.handle_submit,
                            loading=ResearchState.is_processing,
                            color_scheme="blue",
                            size="2",
                            min_width="150px",
                            padding_x="2rem",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("rotate-ccw", size=16),
                                rx.text("New Research"),
                                spacing="2",
                            ),
                            on_click=ResearchState.new_research,
                            color_scheme="green",
                            variant="outline",
                            size="2",
                            min_width="150px",
                            padding_x="2rem",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon("trash-2", size=16),
                                rx.text("Clear"),
                                spacing="2",
                            ),
                            on_click=ResearchState.clear_form,
                            color_scheme="red",
                            variant="ghost",
                            size="2",
                            min_width="100px",
                            padding_x="1.5rem",
                            margin_top="10px",
                        ),
                        spacing="4",
                        width="100%",
                        padding_top="1rem",
                    ),
                    spacing="4",
                    padding="1.5rem",
                    align_items="stretch",
                ),
                width="100%",
                border="1px solid",
                border_color="gray.100",
            ),
            # Results Section
            rx.cond(
                ResearchState.final_report,
                rx.card(
                    rx.vstack(
                        # Report Header with Actions
                        rx.hstack(
                            rx.hstack(
                                rx.icon("file-text", color="blue.500", size=20),
                                rx.heading("Research Report", size="4"),
                                spacing="2",
                            ),
                            rx.spacer(),
                            rx.hstack(
                                # Copy Button
                                rx.button(
                                    rx.cond(
                                        ResearchState.copy_success,
                                        rx.hstack(
                                            rx.icon("check", size=14),
                                            rx.text("Copied!"),
                                            spacing="2",
                                        ),
                                        rx.hstack(
                                            rx.icon("copy", size=14),
                                            rx.text("Copy"),
                                            spacing="2",
                                        ),
                                    ),
                                    on_click=ResearchState.copy_to_clipboard,
                                    color_scheme="gray",
                                    variant="ghost",
                                    size="2",
                                ),
                                # Export PDF Button
                                rx.button(
                                    rx.hstack(
                                        rx.icon("file-down", size=14),
                                        rx.text("Export PDF"),
                                        spacing="2",
                                    ),
                                    on_click=ResearchState.export_to_pdf,
                                    color_scheme="gray",
                                    variant="ghost",
                                    size="2",
                                ),
                                spacing="2",
                            ),
                            width="100%",
                            padding_bottom="4",
                            border_bottom="1px solid",
                            border_color="gray.200",
                            margin_bottom="4",
                        ),
                        # Report Content
                        rx.box(
                            rx.markdown(
                                ResearchState.final_report,
                                component_map={
                                    "p": lambda text: rx.text(text, color="gray.800"),
                                    "h1": lambda text: rx.heading(
                                        text, size="3", margin_y="1rem"
                                    ),
                                    "h2": lambda text: rx.heading(
                                        text, size="4", margin_y="0.75rem"
                                    ),
                                    "h3": lambda text: rx.heading(
                                        text, size="5", margin_y="0.5rem"
                                    ),
                                },
                            ),
                            id="research-report",  # Added ID for PDF export
                            width="100%",
                        ),
                        width="100%",
                        align_items="stretch",
                    ),
                    width="100%",
                    padding="1.5rem",
                ),
            ),
            # Logs Section
            rx.cond(
                ResearchState.process_logs,
                rx.card(
                    rx.vstack(
                        rx.hstack(
                            rx.icon("activity", color="blue.500", size=20),
                            rx.heading("Research Progress", size="4"),
                            margin_bottom="1rem",
                        ),
                        rx.box(
                            rx.markdown(
                                ResearchState.process_logs,
                                component_map={
                                    "p": lambda text: rx.text(
                                        text, color="gray.600", font_family="monospace"
                                    ),
                                },
                            ),
                            width="100%",
                            height="400px",
                            overflow_y="auto",
                            padding="1rem",
                            border="1px solid",
                            border_color="gray.200",
                            border_radius="md",
                            background="gray.50",
                        ),
                        width="100%",
                        align_items="stretch",
                    ),
                    width="100%",
                    padding="1.5rem",
                ),
            ),
            spacing="6",
            width="100%",
            max_width="1200px",
            padding_y="2rem",
        ),
        padding_x="2rem",
        background="gray.50",
        min_height="100vh",
    )


# Create app
app = rx.App(
    style={
        "font_family": "Inter, system-ui, sans-serif",
        "button": {
            "shadow": "md",
            "_hover": {
                "transform": "translateY(-2px)",
                "transition": "0.2s",
            },
        },
        "card": {
            "shadow": "lg",
            "border_radius": "lg",
            "background": "white",
        },
    }
)
app.add_page(index, title="Research Assistant")
