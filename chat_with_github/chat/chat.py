import reflex as rx
from typing import List
from dataclasses import dataclass
import tempfile
import asyncio
import os
from embedchain import App
from embedchain.loaders.github import GithubLoader

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Styles from the reference code
message_style = dict(
    display="inline-block",
    padding="1em",
    border_radius="8px",
    max_width=["30em", "30em", "50em", "50em", "50em", "50em"],
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
    current_chat: int = 0
    processing: bool = False
    db_path: str = tempfile.mkdtemp()
    upload_status: str = ""
    is_loading: bool = False
    repo: str = ""

    _app_instance = None

    def get_app(self):
        """Get or create the app instance."""
        if State._app_instance is None:
            State._app_instance = App.from_config(
                config={
                    "llm": {
                        "provider": "ollama",
                        "config": {
                            "model": "llama3:instruct",
                            "max_tokens": 250,
                            "temperature": 0.5,
                            "stream": True,
                            "base_url": "http://localhost:11434",
                        },
                    },
                    "vectordb": {"provider": "chroma", "config": {"dir": self.db_path}},
                    "embedder": {
                        "provider": "ollama",
                        "config": {
                            "model": "llama3:instruct",
                            "base_url": "http://localhost:11434",
                        },
                    },
                }
            )
        return State._app_instance

    def get_loader(self):
        return GithubLoader(config={"token": GITHUB_TOKEN})

    @rx.event(background=True)
    async def process_question(self, form_data: dict):
        """Process a question and update the chat."""
        if self.processing or not form_data.get("question"):
            return

        question = form_data["question"]

        async with self:
            self.processing = True
            self.chats[self.current_chat].append(QA(question=question, answer=""))
            yield
            await asyncio.sleep(1)

        app = self.get_app()
        answer = app.chat(question)

        async with self:
            self.chats[self.current_chat][-1].answer = answer
            self.processing = False
            self.chats = self.chats
            yield
            await asyncio.sleep(1)

    @rx.event(background=True)
    async def handle_repo_input(self):
        """Handle repository addition."""
        if self.repo == "":
            return

        async with self:
            self.is_loading = True
            yield
            await asyncio.sleep(1)

        try:
            app = self.get_app()
            loader = self.get_loader()
            app.add(f"repo:{self.repo} type:repo", data_type="github", loader=loader)

            async with self:
                self.upload_status = f"Added {self.repo} to knowledge base!"
                yield
        except Exception as e:
            async with self:
                self.upload_status = f"Error: {str(e)}"
        finally:
            async with self:
                self.processing = False
                self.is_loading = False
                yield

    def update_repo(self, repo: str):
        """Update the repo"""
        self.repo = repo


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
        rx.box(rx.foreach(State.chats[State.current_chat], message), width="100%"),
        py="8",
        flex="1",
        width="100%",
        max_width="50em",
        padding_x="4px",
        align_self="center",
        overflow="hidden",
        padding_bottom="5em",
    )


def action_bar() -> rx.Component:
    """The action bar to send a new message."""
    return rx.box(
        rx.vstack(
            rx.form(
                rx.hstack(
                    rx.input(
                        placeholder="Ask about the repository...",
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
                        variant="surface",
                        cursor="pointer",
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
        # border_top=f"1px solid {rx.color('mauve', 3)}",
        # background_color=rx.color("mauve", 2),
        width="100%",
    )


def nav_icon(component: rx.Component) -> rx.badge:
    return rx.badge(
        component,
        color_scheme="gray",
        variant="soft",
        width="21px",
        height="21px",
        display="flex",
        align_items="center",
        justify_content="center",
        background="none",
    )


theme = nav_icon(
    rx.el.button(
        rx.color_mode.icon(
            light_component=rx.icon(
                "moon",
                size=14,
                color=rx.color("slate", 12),
            ),
            dark_component=rx.icon(
                "sun",
                size=14,
                color=rx.color("slate", 12),
            ),
        ),
        on_click=rx.toggle_color_mode,
    ),
)


def index():
    return rx.vstack(
        rx.hstack(
            rx.hstack(
                rx.heading("Chat with GitHub Repository", size="2", weight="medium"),
            ),
            rx.hstack(
                theme,
            ),
            border_bottom=f"1px solid {rx.color('gray', 5)}",
            width="100%",
            height="3em",
            bg=rx.color("gray", 2),
            position="absolute",
            top="0",
            left="0",
            align="center",
            justify="between",
            padding="1em",
        ),
        rx.vstack(
            rx.vstack(
                rx.heading(
                    "Chat with GitHub Repositories",
                    size="7",
                    weight="medium",
                    align="center",
                    width="100%",
                ),
                rx.heading(
                    "Llama-3.2 running with Ollama",
                    size="5",
                    weight="medium",
                    align="center",
                    width="100%",
                    color=rx.color("slate", 11),
                ),
                width="100%",
                spacing="1",
            ),
            rx.divider(height="2em", opacity="0"),
            rx.hstack(
                rx.text(
                    "Github Repo",  # Use last word of label as display text
                    size="1",
                    weight="bold",
                    color=rx.color("slate", 10),
                    width="120px",
                    border_right="1px solid gray",
                    margin_right="0.5em",
                ),
                rx.input(
                    value=State.repo,
                    on_change=State.update_repo,
                    width="100%",
                    variant="soft",
                    bg="transparent",
                    outline="none",
                ),
                align="center",
                width="100%",
                border_bottom=f"0.75px solid {rx.color('gray', 4)}",
            ),
            rx.divider(height="0.5em", opacity="0"),
            rx.button(
                "Process",
                on_click=State.handle_repo_input,
                loading=State.is_loading,
                width="100%",
                variant="surface",
                cursor="pointer",
            ),
            rx.divider(height="2em", opacity="0"),
            rx.vstack(
                rx.text(State.upload_status, size="1", align="center", width="100%"),
                chat(),
                action_bar(),
                width="100%",
            ),
            width="100%",
            max_width="30em",
        ),
        width="100%",
        height="100vh",
        align="center",
        justify="center",
    )


app = rx.App()
app.add_page(
    index,
    title="GitHub Repository Chat",
    description="Chat with GitHub repositories using AI",
    route="/",
)
