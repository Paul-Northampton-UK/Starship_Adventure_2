"""Placeholder handlers for enter/exit commands."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_enter(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    place = parsed_intent.target or "area"
    logger.info(f"[handle_enter] Entering '{place}'.")
    return [{"key": "enter_action", "data": {"place": place}}]


def handle_exit(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    place = parsed_intent.target or "area"
    logger.info(f"[handle_exit] Exiting '{place}'.")
    return [{"key": "exit_action", "data": {"place": place}}]
