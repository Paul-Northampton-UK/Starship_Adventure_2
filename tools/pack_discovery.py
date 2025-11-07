"""Utility helpers for listing available packs."""

from __future__ import annotations

from pathlib import Path

from engine import active_pack


def has_game_yaml(path: Path) -> bool:
    """Return True if the provided directory contains a game.yaml file."""

    return path.is_dir() and (path / "game.yaml").is_file()


def list_packs(base: Path | None = None) -> list[str]:
    """List pack directory names under ``base`` (default: repo packs/)."""

    base_dir = base or (Path(__file__).resolve().parents[1] / "packs")
    if not base_dir.is_dir():
        return []
    names: list[str] = []
    for child in sorted(base_dir.iterdir()):
        if has_game_yaml(child):
            names.append(child.name)
    return names


def current_active_pack() -> str:
    """Expose the active pack helper for testability."""

    return active_pack.get_active_pack()
