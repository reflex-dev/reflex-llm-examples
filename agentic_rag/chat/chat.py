import reflex as rx
from chat.components.chat import State, chat, action_bar, sidebar

def index() -> rx.Component:
    """The main app."""
    return rx.box(
        sidebar(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.heading("Agentic RAG using Gemini 2.0 Flash 🔥"),
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