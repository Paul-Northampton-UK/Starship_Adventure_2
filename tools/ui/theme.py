"""Shared CustomTkinter theme values."""

from __future__ import annotations

from typing import Tuple

import customtkinter as ctk

PADDING = 8
GAP = 6
RADIUS = 8
FONT_BASE: Tuple[str, int] = ("Segoe UI", 12)
FONT_SMALL: Tuple[str, int] = ("Segoe UI", 11)
FONT_MONO: Tuple[str, int] = ("Consolas", 12)
ACCENT = "#1E6FB8"
PANEL_BG = "#1E1F24"
CANVAS_BG = "#14161A"
TEXT_FG = "#E8E8E8"
MUTED_FG = "#A7A7A7"


def apply_theme(root: ctk.CTkBaseClass) -> None:
    """Apply the shared appearance settings to the root window."""

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    try:
        root.configure(fg_color=CANVAS_BG)
    except Exception:
        pass
