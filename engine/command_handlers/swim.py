"""Placeholder handler for swim intent."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_swim(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    direction = parsed_intent.direction or "any direction"
    logger.info(f"[handle_swim] Swimming direction='{direction}'.")
    return [{"key": "swim_action", "data": {"direction": direction}}]
