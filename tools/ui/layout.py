"""Layout helpers for consistent spacing."""

from __future__ import annotations

import customtkinter as ctk

from . import theme


def pad(p: int | None = None) -> dict[str, int]:
    """Return shared padding kwargs."""

    value = theme.PADDING if p is None else p
    return {"padx": value, "pady": value}


def sticky_all() -> str:
    """Return the standard sticky string."""

    return "nsew"


def style_button(button: ctk.CTkButton) -> None:
    """Apply the shared accent styling to a button."""

    button.configure(
        corner_radius=theme.RADIUS,
        fg_color=theme.ACCENT,
        hover_color="#155484",
    )
