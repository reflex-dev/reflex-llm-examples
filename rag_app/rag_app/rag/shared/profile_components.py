from typing import Callable

import reflex as rx

from ..state import State
from ..style import Typography
from .style import ProfileComponentStyle


def profile_item_unit():
    return rx.radio(
        ["metric", "imperial"],
        default_value="metric",
        on_change=State.set_units,
        direction="row",
    )


def profile_item_physical_stats(value: str, unit: str, fn: Callable):
    return rx.hstack(
        rx.input(
            value=value,
            on_change=fn,
            **ProfileComponentStyle.profile_item_input,
        ),
        rx.hstack(
            rx.divider(orientation="vertical", width="2px", height="20px"),
            rx.text(
                State.units[State.selected_unit][unit],
                **ProfileComponentStyle.profile_item_input_unit,
                **Typography.passive,
            ),
        ),
        **ProfileComponentStyle.profile_item_input_parent,
    )


def profile_item_activity_stats(title: str, options: list[str]):
    return rx.vstack(
        rx.text(title, size="1", weight="bold", **Typography.passive),
        rx.select(
            options,
            placeholder="Select an option",
            on_change=lambda e: State.set_profile_stats([title, e]),
            **ProfileComponentStyle.profile_item_activity,
        ),
        spacing="2",
        width="100%",
    )
