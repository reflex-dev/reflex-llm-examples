import os
import uuid
import tempfile
import gc
import pandas as pd
from dataclasses import dataclass
from typing import Optional

import asyncio

from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    PromptTemplate,
)
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.docling import DoclingReader
from llama_index.core.node_parser import MarkdownNodeParser
import reflex as rx


# Data Models
@dataclass
class QA:
    """A question and answer pair."""

    question: str
    answer: str


# Custom Loading Icon
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

# Styles
message_style = dict(
    display="inline-block",
    padding="1em",
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
)

SIDEBAR_STYLE = dict(
    width="300px",
    height="100vh",
    position="fixed",
    left=0,
    top=0,
    padding="2em",
    background_color=rx.color("blue", 2),
    border_right=f"1px solid {rx.color('blue', 3)}",
)

UPLOAD_BUTTON_STYLE = dict(
    color=rx.color("mauve", 12),
    bg="transparent",
    border=f"1px solid {rx.color('mauve', 6)}",
    margin_y="1em",
    _hover={"bg": rx.color("mauve", 3)},
)


# Application State
class State(rx.State):
    chats: list[list[QA]] = [[]]
    uploaded_file: Optional[str] = None
    uploading: bool = False
    processing: bool = False
    current_chat: int = 0
    file_cache: dict = {}
    session_id: str = str(uuid.uuid4())
    upload_status: str = ""
    preview_df: list = []
    preview_columns: list = []

    _query_engine = None

    def load_llm(self):
        return Ollama(model="deepseek-r1:1.5b", request_timeout=120.0)

    async def handle_upload(self, files: list[rx.UploadFile]):
        if not files:
            self.upload_status = "No file selected, Please select a file to continue"
            return
            yield

        self.uploading = True
        yield

        try:
            file = files[0]
            upload_data = await file.read()
            file_name = file.filename

            with tempfile.TemporaryDirectory() as temp_dir:
                file_path = os.path.join(temp_dir, file_name)
                with open(file_path, "wb") as f:
                    f.write(upload_data)

                file_key = f"{self.session_id}-{file_name}"

                if file_key not in self.file_cache:
                    reader = DoclingReader()
                    loader = SimpleDirectoryReader(
                        input_dir=temp_dir,
                        file_extractor={".xlsx": reader},
                    )
                    docs = loader.load_data()

                    llm = self.load_llm()
                    embed_model = HuggingFaceEmbedding(
                        model_name="BAAI/bge-large-en-v1.5", trust_remote_code=True
                    )

                    Settings.embed_model = embed_model
                    node_parser = MarkdownNodeParser()
                    index = VectorStoreIndex.from_documents(
                        documents=docs,
                        transformations=[node_parser],
                        show_progress=True,
                    )

                    Settings.llm = llm
                    query_engine = index.as_query_engine(streaming=True)

                    qa_prompt_tmpl_str = """
                    Context information is below.
                    ---------------------
                    {context_str}
                    ---------------------
                    Given the context information above I want you to think step by step to answer 
                    the query in a highly precise and crisp manner focused on the final answer, 
                    incase case you don't know the answer say 'I don't know!'.
                    Query: {query_str}
                    Answer: 
                    """
                    qa_prompt_tmpl = PromptTemplate(qa_prompt_tmpl_str)
                    query_engine.update_prompts(
                        {"response_synthesizer:text_qa_template": qa_prompt_tmpl}
                    )

                    self.file_cache[file_key] = query_engine
                    self._query_engine = query_engine
                    df = pd.read_excel(file_path)
                    self.preview_columns = [
                        {"field": col, "header": col} for col in df.columns
                    ]
                    self.preview_df = df.to_dict(orient="records")
                    self.upload_status = f"Uploaded {file_name} successfully"
                    self.uploading = False
                    yield

                else:
                    self._query_engine = self.file_cache[file_key]

                yield
        except Exception as e:
            self.uploading = False
            self.upload_status = f"Error uploading file: {str(e)}"
            yield

    def create_new_chat(self):
        """Create a new chat."""
        self.chats.append([])
        self.current_chat = len(self.chats) - 1

    def reset_chat(self):
        self.messages = []
        gc.collect()

    @rx.event(background=True)
    async def process_query(self, form_data: dict):
        if self.processing or not form_data.get("question") or not self._query_engine:
            return

        question = form_data.get("question")
        if not question:
            return

        async with self:
            self.processing = True
            self.chats[self.current_chat].append(QA(question=question, answer=""))
            yield
            await asyncio.sleep(0.1)

        try:
            streaming_response = self._query_engine.query(question)
            answer = ""

            async with self:
                for chunk in streaming_response.response_gen:
                    answer += chunk
                    self.chats[self.current_chat][-1].answer = answer
                    self.chats = self.chats
                    yield
                    await asyncio.sleep(0.05)

                self.processing = False
                yield

        except Exception as e:
            async with self:
                self.chats[self.current_chat][
                    -1
                ].answer = f"Error processing query: {str(e)}"
                self.processing = False
                yield


def excel_preview() -> rx.Component:
    if State.preview_df is None:
        return rx.box()

    return rx.box(
        rx.heading("Excel Preview", size="4"),
        rx.data_table(
            data=State.preview_df,
            columns=State.preview_columns,
            pagination=True,
            search=True,
            sort=True,
        ),
        padding="1em",
        border_radius="8px",
        border=f"1px solid {rx.color('blue', 3)}",
        margin_top="-2em",
        margin_bottom="2em",
    )


def message(qa: QA) -> rx.Component:
    return rx.box(
        rx.box(
            rx.markdown(
                qa.question,
                background_color=rx.color("blue", 4),
                color=rx.color("blue", 12),
                **message_style,
            ),
            text_align="right",
            margin_top="1em",
        ),
        rx.box(
            rx.markdown(
                qa.answer,
                background_color=rx.color("green", 4),
                color=rx.color("green", 12),
                **message_style,
            ),
            text_align="left",
            padding_top="1em",
        ),
        width="100%",
    )


def action_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask your question here...",
                        id="question",
                        width=["15em", "20em", "45em", "50em", "50em", "50em"],
                        disabled=State.processing,
                        border_color=rx.color("blue", 6),
                        _focus={"border_color": rx.color("blue", 8)},
                        background_color="transparent",
                    ),
                    rx.button(
                        rx.cond(
                            State.processing,
                            loading_icon(height="1em"),
                            rx.text("Process"),
                        ),
                        type_="submit",
                        disabled=State.processing,
                        bg=rx.color("green", 9),
                        color="white",
                        _hover={"bg": rx.color("green", 10)},
                    ),
                    align_items="center",
                    spacing="3",
                ),
                on_submit=State.process_query,
                width="100%",
                reset_on_submit=True,
            ),
            align_items="center",
            width="100%",
        ),
        position="fixed",
        bottom="0",
        left="0",
        padding_x="20em",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        background_color=rx.color("mauve", 2),
        border_top=f"1px solid {rx.color('blue', 3)}",
        width="100%",
    )


def sidebar() -> rx.Component:
    """The sidebar component."""
    return rx.box(
        rx.vstack(
            rx.heading("Upload Document", size="6", margin_bottom="1em"),
            rx.upload(
                rx.vstack(
                    rx.button(
                        "Select Excel File",
                        **UPLOAD_BUTTON_STYLE,
                    ),
                    rx.text(
                        "Drag and drop file here",
                        font_size="sm",
                        color=rx.color("mauve", 11),
                    ),
                ),
                border=f"1px dashed {rx.color('mauve', 6)}",
                padding="2em",
                border_radius="md",
                accept={
                    ".xls": "application/vnd.ms-excel",
                    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                },
                max_files=1,
                multiple=False,
            ),
            rx.button(
                "Add to Knowledge Base",
                on_click=State.handle_upload(rx.upload_files()),
                loading=State.uploading,
                **UPLOAD_BUTTON_STYLE,
            ),
            rx.text(State.upload_status, color=rx.color("mauve", 11), font_size="sm"),
            align_items="stretch",
            height="100%",
        ),
        **SIDEBAR_STYLE,
    )


def chat() -> rx.Component:
    return rx.vstack(
        rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow_y="auto",
        padding_bottom="5em",
    )


def index() -> rx.Component:
    """The main app."""
    return rx.box(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading(
                        "Chat with Excel using DeepSeek-R1 💬", margin_right="4em"
                    ),
                    rx.button(
                        "New Chat",
                        on_click=State.create_new_chat,
                        margin_left="auto",
                    ),
                ),
                chat(),
                action_bar(),
                spacing="4",
                align_items="center",
                height="100vh",
                padding="4em",
            ),
            margin_left="300px",
            width="calc(100% - 300px)",
        ),
        width="100%",
        height="100vh",
        background_color=rx.color("mauve", 1),
    )


app = rx.App()
app.add_page(index)
