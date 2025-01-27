import reflex as rx
from typing import List
from dataclasses import dataclass
import tempfile
import base64
from pathlib import Path
import asyncio
import os

from llama_index.core import VectorStoreIndex, Settings, SimpleDirectoryReader
from llama_index.llms.ollama import Ollama
from llama_index.core import PromptTemplate
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# Styles remain the same
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
    db_path: str = tempfile.mkdtemp()
    pdf_filename: str = ""
    knowledge_base_files: List[str] = []
    upload_status: str = ""

    _query_engine = None
    _temp_dir = None

    def setup_llamaindex(self):
        """Setup LlamaIndex with models and prompt template."""
        if self._query_engine is None and self._temp_dir:
            # Setup LLM
            llm = Ollama(model="deepseek-r1:1.5b", request_timeout=120.0)
            
            # Setup embedding model
            embed_model = HuggingFaceEmbedding(
                model_name="BAAI/bge-large-en-v1.5",
                trust_remote_code=True
            )
            
            # Configure settings
            Settings.embed_model = embed_model
            Settings.llm = llm

            # Load documents
            loader = SimpleDirectoryReader(
                input_dir=self._temp_dir,
                required_exts=[".pdf"],
                recursive=True
            )
            docs = loader.load_data()

            # Create index and query engine
            index = VectorStoreIndex.from_documents(docs, show_progress=True)
            
            # Setup streaming query engine with custom prompt
            qa_prompt_tmpl_str = (
                "Context information is below.\n"
                "---------------------\n"
                "{context_str}\n"
                "---------------------\n"
                "Given the context information above I want you to think step by step to answer the query in a crisp manner, incase case you don't know the answer say 'I don't know!'.\n"
                "Query: {query_str}\n"
                "Answer: "
            )
            qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
            
            self._query_engine = index.as_query_engine(streaming=True)
            self._query_engine.update_prompts(
                {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
            )

    @rx.event(background=True)
    async def process_question(self, form_data: dict):
        """Process a question and update the chat."""
        if self.processing or not form_data.get("question") or not self._query_engine:
            return

        question = form_data["question"]
        
        async with self:
            self.processing = True
            self.chats[self.current_chat].append(QA(question=question, answer=""))
            yield
            await asyncio.sleep(0.1)

        # Get streaming response from LlamaIndex
        streaming_response = self._query_engine.query(question)
        answer = ""

        # Process the streaming response
        async with self:
            for chunk in streaming_response.response_gen:
                answer += chunk
                self.chats[self.current_chat][-1].answer = answer
                self.chats = self.chats
                yield
                await asyncio.sleep(0.05)

            self.processing = False
            yield

    async def handle_upload(self, files: List[rx.UploadFile]):
        """Handle file upload and processing."""
        if not files:
            self.upload_status = "No file uploaded!"
            return
            yield

        self.uploading = True
        yield

        file = files[0]
        upload_data = await file.read()
        
        # Create temporary directory if not exists
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp()
            
        outfile = Path(self._temp_dir) / file.filename
        self.pdf_filename = file.filename

        with outfile.open("wb") as file_object:
            file_object.write(upload_data)

        # Base64 encode the PDF content
        base64_pdf = base64.b64encode(upload_data).decode('utf-8')
        self.base64_pdf = base64_pdf

        # Setup LlamaIndex
        self.setup_llamaindex()
        
        self.knowledge_base_files.append(self.pdf_filename)
        self.upload_status = f"Added {self.pdf_filename} to knowledge base"

        self.uploading = False
        yield

    def create_new_chat(self):
        """Create a new chat."""
        self.chats.append([])
        self.current_chat = len(self.chats) - 1

def pdf_preview() -> rx.Component:
    """PDF preview component."""
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
    """A single question/answer message."""
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
    """List all the messages in a conversation."""
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
    """The action bar to send a new message."""
    return rx.box(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask about the PDF...",
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
    """The sidebar component."""
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