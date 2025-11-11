"""Placeholder handlers for basic item interactions like USE."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_use(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    logger.info(f"[handle_use] Using '{item}'.")
    return [{"key": "interaction_use", "data": {"item": item}}]


def handle_use_on(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    target = parsed_intent.secondary_target or "target"
    logger.info(f"[handle_use_on] Using '{item}' on '{target}'.")
    return [{"key": "interaction_use_on", "data": {"item": item, "target": target}}]
