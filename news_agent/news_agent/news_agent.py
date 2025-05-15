import reflex as rx
from duckduckgo_search import DDGS
from swarm import Swarm, Agent
from datetime import datetime
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Initialize Swarm and set model

MODEL = "llama3.2"
client = Swarm()


def fetch_latest_news(topic):
    """Retrieve the latest news articles related to a given topic using DuckDuckGo."""

    query = f"{topic} news {datetime.now().strftime('%Y-%m')}"

    with DDGS() as search_engine:
        articles = search_engine.text(query, max_results=3)

        if articles:
            formatted_results = "\n\n".join(
                f"Title: {article['title']}\nURL: {article['href']}\nSummary: {article['body']}"
                for article in articles
            )
            return formatted_results

        return f"No news articles found on the topic: {topic}."


# Create specialized agents
search_agent = Agent(
    name="News Searcher",
    instructions="""
    You are an expert in news discovery. Your role involves:
    1. Identifying the latest and most pertinent news articles on the provided topic.
    2. Ensuring all sources are credible and trustworthy.
    3. Presenting the raw search results in a clear and organized manner.
    """,
    functions=[fetch_latest_news],
    model=MODEL,
)

summary_agent = Agent(
    name="Comprehensive News Synthesizer",
    instructions="""
    You are a skilled news analyst, proficient in synthesizing multiple sources and crafting engaging, concise summaries. Your responsibilities include:

    **Synthesis and Analysis:**
    1. Review the provided news articles thoroughly, extracting key insights and essential details.
    2. Merge information from various sources into a unified narrative, ensuring factual accuracy and journalistic neutrality.
    3. Highlight the main event, key players, significant data, and context to ensure a comprehensive overview.

    **Writing Style and Delivery:**
    4. Write in a clear, active, and accessible tone that balances professionalism with readability.
    5. Simplify complex concepts for a broader audience while maintaining depth and accuracy.
    6. Use specifics over generalities, ensuring that each word adds value.
    7. Craft a synthesis of the main points in a structured format: 
        - **Main Event:** Clearly introduce the core topic or event.
        - **Key Details/Data:** Provide supporting information, such as statistics, facts, or context.
        - **Relevance/Implications:** Explain its significance and potential effects.

    **Deliverable:**
    Compose an engaging, multi-paragraph summary (300-400 words) with the following structure:
    - Start with the most critical development, including key players and their actions.
    - Follow with context and supporting details drawn from multiple sources.
    - Conclude with the immediate relevance, significance, and any potential short-term implications.

    **IMPORTANT NOTE:** Deliver the content as polished news analysis only. Avoid labels, introductions, or meta-comments. Begin directly with the story, ensuring neutrality and factual accuracy throughout.
    """,
    model=MODEL,
)


class State(rx.State):
    """Manage the application state."""

    topic: str = "AI Agents"
    raw_news: str = ""
    final_summary: str = ""
    is_loading: bool = False
    error_message: str = ""

    @rx.event(background=True)
    async def process_news(self):
        """Asynchronous news processing workflow using Swarm agents"""
        # Reset previous state
        async with self:
            self.is_loading = True
            self.error_message = ""
            self.raw_news = ""
            self.final_summary = ""

            yield
            await asyncio.sleep(1)

        try:
            # Search news using search agent
            search_response = client.run(
                agent=search_agent,
                messages=[
                    {"role": "user", "content": f"Find recent news about {self.topic}"}
                ],
            )
            async with self:
                self.raw_news = search_response.messages[-1]["content"]

            # Synthesize and Generate summary using summary agent
            summary_response = client.run(
                agent=summary_agent,
                messages=[
                    {
                        "role": "user",
                        "content": f"Synthesize these news articles and summarize the synthesis:\n{self.raw_news}",
                    }
                ],
            )

            async with self:
                self.final_summary = summary_response.messages[-1]["content"]
                self.is_loading = False

        except Exception as e:
            async with self:
                self.error_message = f"An error occurred: {str(e)}"
                self.is_loading = False

    def update_topic(self, topic: str):
        """Update the search topic"""
        self.topic = topic


def news_page() -> rx.Component:
    """Render the main news processing page"""
    return rx.box(
        rx.section(
            rx.heading("📰 AI News Agent", size="8"),
            rx.input(
                placeholder="Enter the news topic",
                value=State.topic,
                on_change=State.update_topic,
                width="300px",
            ),
            rx.button(
                "Process News",
                on_click=State.process_news,
                color_scheme="blue",
                loading=State.is_loading,
                width="fit-content",
            ),
            display="flex",
            flex_direction="column",
            gap="1rem",
        ),
        # Results Section
        rx.cond(
            State.final_summary != "",
            rx.vstack(
                rx.heading("📝 News Summary", size="4"),
                rx.markdown(State.final_summary),
                rx.button(
                    "Copy the Summary",
                    on_click=[
                        rx.set_clipboard(State.final_summary),
                        rx.toast.info("Summary copied"),
                    ],
                ),
                spacing="4",
                width="100%",
            ),
        ),
        spacing="4",
        max_width="800px",
        margin="auto",
        padding="20px",
    )


app = rx.App(theme=rx.theme(appearance="light", accent_color="blue"))
app.add_page(news_page, route="/")
