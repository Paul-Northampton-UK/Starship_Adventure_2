"""Placeholder handler for wait intent."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_wait(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_wait] Player waits for a moment.")
    return [{"key": "wait_action", "data": {}}]
