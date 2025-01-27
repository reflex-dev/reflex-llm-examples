import reflex as rx

from chat.components import loading_icon
from chat.state import QA, State


message_style = dict(display="inline-block", padding="1em", border_radius="8px", max_width=["30em", "30em", "50em", "50em", "50em", "50em"])


def message(qa: QA) -> rx.Component:
    """A single question/answer message.

    Args:
        qa: The question/answer pair.

    Returns:
        A component displaying the question/answer pair.
    """
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
    """List all the messages in a single conversation."""
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
                        placeholder="Type something...",
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
        padding_x="450px",
        padding_y="16px",
        backdrop_filter="auto",
        backdrop_blur="lg",
        border_top=f"1px solid {rx.color('mauve', 3)}",
        background_color=rx.color("mauve", 2),
        width="100%",
    )
