import reflex as rx
from typing import List, Optional
from dataclasses import dataclass
import tempfile
import base64
from pathlib import Path
import asyncio
import os
import time

from agno.agent import Agent
from agno.document import Document
from agno.document.reader.pdf_reader import PDFReader
from agno.utils.log import logger
from agno.agent import Agent, AgentMemory
from agno.embedder.google import GeminiEmbedder
from agno.knowledge import AgentKnowledge
from agno.memory.db.postgres import PgMemoryDb
from agno.models.google import Gemini
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.pgvector import PgVector

import traceback

from typing import Optional

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

def get_agentic_rag_agent(
    model_id: str = "gemini-2.0-flash",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:
    """Get an Agentic RAG Agent with Memory optimized for Deepseek and PDFs."""
    
    # Initialize Deepseek model
    model = Gemini(id=model_id) 

    # Define persistent memory for chat history
    memory = AgentMemory(
        db=PgMemoryDb(
            table_name="pdf_agent_memory",
            db_url=db_url
        ),
        create_user_memories=False,
        create_session_summary=False,
    )

    # PDF-optimized knowledge base
    knowledge_base = AgentKnowledge(
        vector_db=PgVector(
            db_url=db_url,
            table_name="pdf_documents_v2",
            schema="ai",
            embedder=GeminiEmbedder(),
        ),
        num_documents=4,  # Optimal for PDF chunking
        document_processor=PDFReader(chunk_size=1000
            ),
            batch_size=32,
            parallel_processing=True
    )

    # Create the PDF-focused Agent
    pdf_rag_agent: Agent = Agent(
        name="pdf_rag_agent",
        session_id=session_id,
        user_id=user_id,
        model=model,
        storage=PostgresAgentStorage(
            table_name="pdf_agent_sessions",
            db_url=db_url
        ),
        memory=memory,
        knowledge=knowledge_base,
        description="You are a helpful Agent called 'Agentic RAG' and your goal is to assist the user in the best way possible.",
        instructions=[
            "1. Knowledge Base Search:",
            "   - ALWAYS start by searching the knowledge base using search_knowledge_base tool",
            "   - Analyze ALL returned documents thoroughly before responding",
            "   - If multiple documents are returned, synthesize the information coherently",
            "2. External Search:",
            "   - If knowledge base search yields insufficient results, use duckduckgo_search",
            "   - Focus on reputable sources and recent information",
            "   - Cross-reference information from multiple sources when possible",
            "3. Citation Precision:",
            "   - Reference page numbers and section headers",
            "   - Distinguish between main content and appendices",
            "4. Response Quality:",
            "   - Provide specific citations and sources for claims",
            "   - Structure responses with clear sections and bullet points when appropriate",
            "   - Include relevant quotes from source materials",
            "   - Avoid hedging phrases like 'based on my knowledge' or 'depending on the information'",
            "5. Response Structure:",
            "   - Use markdown for formatting technical content",
            "   - Create bullet points for lists found in documents",
            "   - Preserve important formatting from original PDF",
            "6. User Interaction:",
            "   - Ask for clarification if the query is ambiguous",
            "   - Break down complex questions into manageable parts",
            "   - Proactively suggest related topics or follow-up questions",
            "7. Error Handling:",
            "   - If no relevant information is found, clearly state this",
            "   - Suggest alternative approaches or questions",
            "   - Be transparent about limitations in available information",
        ],
        search_knowledge=True,
        read_chat_history=False,
        tools=[DuckDuckGoTools()],
        markdown=True,
        show_tool_calls=True,
        add_history_to_messages=True,
        add_datetime_to_instructions=True,
        debug_mode=debug_mode,
        read_tool_call_history=True,
        num_history_responses=3,
    )

    return pdf_rag_agent


# Styles
message_style = dict(
    display="inline-block", 
    padding="1em", 
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"]
)

SIDEBAR_STYLE = dict(
    width="300px",
    height="100vh",
    position="fixed",
    left=0,
    top=0,
    padding="2em",
    background_color=rx.color("mauve", 2),
    border_right=f"1px solid {rx.color('mauve', 3)}",
)

UPLOAD_BUTTON_STYLE = dict(
    color=rx.color("mauve", 12),
    bg="transparent",
    border=f"1px solid {rx.color('mauve', 6)}",
    margin_y="1em",
    _hover={"bg": rx.color("mauve", 3)},
)

@dataclass
class QA:
    """A question and answer pair."""
    question: str
    answer: str

class LoadingIcon(rx.Component):
    """A custom loading icon component."""
    library = "react-loading-icons"
    tag = "SpinningCircles"
    stroke: rx.Var[str]
    stroke_opacity: rx.Var[str]
    fill: rx.Var[str]
    fill_opacity: rx.Var[str]
    stroke_width: rx.Var[str]
    speed: rx.Var[str]
    height: rx.Var[str]

    def get_event_triggers(self) -> dict:
        return {"on_change": lambda status: [status]}

loading_icon = LoadingIcon.create


class State(rx.State):
    """The app state."""
    chats: List[List[QA]] = [[]]
    base64_pdf: str = ""
    uploading: bool = False
    current_chat: int = 0
    processing: bool = False
    pdf_filename: str = ""
    knowledge_base_files: List[str] = []
    upload_status: str = ""
    loaded_files: set[str] = set()

    # Only store the path, not the agent
    _temp_dir: Optional[Path] = None
    _session_id: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True
        exclude = {"_temp_dir"}
        json_encoders = {
            Path: lambda v: str(v),
            tempfile.TemporaryDirectory: lambda v: None
        }

    def _create_agent(self) -> Agent:
        """Create a fresh agent instance for each interaction"""
        try:
            # Generate a consistent session ID based on current chat
            if not self._session_id:
                self._session_id = f"session_{int(time.time())}"
            
            return get_agentic_rag_agent(
                model_id="gemini-2.0-flash",
                session_id=self._session_id,
                user_id=None,
                debug_mode=True
            )
        except Exception as e:
            logger.error(f"Agent creation error: {str(e)}")
            raise

    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle PDF file upload and processing"""
        try:
            if not files:
                self.upload_status = "No file uploaded!"
                return

            self.uploading = True
            yield

            file = files[0]
            upload_data = await file.read()
            
            # Create persistent temp directory
            if self._temp_dir is None:
                self._temp_dir = Path(tempfile.mkdtemp())

            outfile = self._temp_dir / file.filename
            self.pdf_filename = file.filename

            # Check if file already loaded
            file_identifier = f"{file.filename}_{len(upload_data)}"
            if file_identifier in self.loaded_files:
                self.upload_status = f"{file.filename} already loaded"
                return

            with outfile.open("wb") as f:
                f.write(upload_data)

            # Create a temporary agent to load the document
            try:
                agent = self._create_agent()
                reader = PDFReader()
                docs = reader.read(outfile)
                agent.knowledge.load_documents(docs, upsert=True)
                self.loaded_files.add(file_identifier)
                self.upload_status = f"Added {file.filename} to knowledge base"
            except Exception as e:
                self.upload_status = f"Invalid PDF: {str(e)}"
                return

            # Store base64 for preview
            base64_pdf = base64.b64encode(upload_data).decode('utf-8')
            self.base64_pdf = base64_pdf
            self.knowledge_base_files.append(file.filename)

        except Exception as e:
            logger.error(traceback.format_exc())
            self.upload_status = f"Upload error: {str(e)}"
        finally:
            self.uploading = False
            yield
    
    @rx.event(background=True)
    async def process_question(self, form_data: dict):
        """Process a question using streaming responses"""
        if self.processing or not form_data.get("question"):
            return

        question = form_data["question"]
        
        async with self:
            self.processing = True
            self.chats[self.current_chat].append(QA(question=question, answer=""))
            yield
            await asyncio.sleep(0.1)

        try:
            agent = self._create_agent()
            queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def run_stream():
                """Run synchronous stream in a thread"""
                try:
                    stream_response = agent.run(question, stream=True)
                    for chunk in stream_response:
                        if chunk.content:
                            asyncio.run_coroutine_threadsafe(queue.put(chunk.content), loop)
                    asyncio.run_coroutine_threadsafe(queue.put(None), loop)
                except Exception as e:
                    error_msg = f"Error: {str(e)}"
                    asyncio.run_coroutine_threadsafe(queue.put(error_msg), loop)

            # Start streaming in background thread
            loop.run_in_executor(None, run_stream)

            answer_content = ""
            while True:
                chunk = await queue.get()
                if chunk is None:  # End of stream
                    break
                if isinstance(chunk, str) and chunk.startswith("Error: "):
                    answer_content = chunk
                    break
                
                answer_content += chunk
                async with self:
                    self.chats[self.current_chat][-1].answer = answer_content
                    self.chats = self.chats  # Trigger refresh
                    yield

        except Exception as e:
            answer_content = f"Error processing question: {str(e)}"
            async with self:
                self.chats[self.current_chat][-1].answer = answer_content
                self.chats = self.chats
                yield

        finally:
            async with self:
                self.processing = False
                yield
        

    def clear_knowledge_base(self):
        """Clear knowledge base and reset state"""
        try:
            # Create temporary agent to clear vector store
            agent = self._create_agent()
            agent.knowledge.vector_db.delete()
            
            # Reset state
            self.loaded_files.clear()
            self.knowledge_base_files.clear()
            self.base64_pdf = ""
            self._temp_dir = None
            self._session_id = None
            self.upload_status = "Knowledge base cleared"
        except Exception as e:
            self.upload_status = f"Error clearing knowledge base: {str(e)}"
        
    def create_new_chat(self):
        """Create a new chat"""
        self.chats.append([])
        self.current_chat = len(self.chats) - 1

def pdf_preview() -> rx.Component:
    return rx.box(
        rx.heading("PDF Preview", size="4", margin_bottom="1em"),
        rx.cond(
            State.base64_pdf != "",
            rx.html(
                f'''
                <iframe 
                    src="data:application/pdf;base64,{State.base64_pdf}"
                    width="100%" 
                    height="600px"
                    style="border: none; border-radius: 8px;">
                </iframe>
                '''
            ),
            rx.text("No PDF uploaded yet", color="red"),
        ),
        width="100%",
        margin_top="1em",
        border_radius="md",
        overflow="hidden",
    )

def message(qa: QA) -> rx.Component:
    return rx.box(
        rx.box(
            rx.markdown(
                qa.question,
                background_color=rx.color("mauve", 4),
                color=rx.color("mauve", 12),
                **message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.markdown(
                qa.answer,
                background_color=rx.color("accent", 4),
                color=rx.color("accent", 12),
                **message_style,
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )

def chat() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.foreach(State.chats[State.current_chat], message),
            width="100%"
        ),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow_y="auto",
        padding_bottom="5em",
    )

def action_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask the Agent...",
                        id="question",
                        width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        disabled=State.processing,
                        border_color=rx.color("mauve", 6),
                        _focus={"border_color": rx.color("mauve", 8)},
                        background_color="transparent",
                    ),
                    rx.button(
                        rx.cond(
                            State.processing,
                            loading_icon(height="1em"),
                            rx.text("Send"),
                        ),
                        type_="submit",
                        disabled=State.processing,
                        bg=rx.color("accent", 9),
                        color="white",
                        _hover={"bg": rx.color("accent", 10)},
                    ),
                    align_items="center",
                    spacing="3",
                ),
                on_submit=State.process_question,
                width="100%",
                reset_on_submit=True,
            ),
            align_items="center",
            width="100%",
        ),
        position="sticky",
        bottom="0",
        left="0",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        width="100%",
    )

def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.heading("PDF Upload", size="6", margin_bottom="1em"),
            rx.upload(
                rx.vstack(
                    rx.button(
                        "Browse files",
                        **UPLOAD_BUTTON_STYLE,
                    ),
                    rx.text(
                        "Drag and drop PDF file here",
                        font_size="sm",
                        color=rx.color("mauve", 11),
                    ),
                ),
                border=f"1px dashed {rx.color('mauve', 6)}",
                padding="2em",
                border_radius="md",
                accept={".pdf": "application/pdf"},
                max_files=1,
                multiple=False,
            ),
            rx.button(
                "Add to Knowledge Base",
                on_click=State.handle_upload(rx.upload_files()),
                loading=State.uploading,
                **UPLOAD_BUTTON_STYLE,
            ),
            rx.button(
                "Clear Knowledge Base",
                on_click=State.clear_knowledge_base,
                color_scheme="red",
                **UPLOAD_BUTTON_STYLE,
            ),
            rx.cond(
                State.pdf_filename != "",
                pdf_preview(),
            ),
            rx.foreach(
                State.knowledge_base_files,
                lambda file: rx.box(
                    rx.text(file, font_size="sm"),
                    padding="0.5em",
                    border_radius="md",
                    width="100%",
                ),
            ),
            rx.text(
                State.upload_status,
                color=rx.color("mauve", 11),
                font_size="sm"
            ),
            align_items="stretch",
            height="100%",
        ),
        **SIDEBAR_STYLE,
    )
