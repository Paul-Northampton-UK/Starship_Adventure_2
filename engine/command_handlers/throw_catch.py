"""Placeholder handlers for throw and catch commands."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_throw(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    target = parsed_intent.secondary_target or "target"
    logger.info(f"[handle_throw] Throwing '{item}' at '{target}'.")
    return [{"key": "throw_action", "data": {"item": item, "target": target}}]


def handle_catch(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    logger.info(f"[handle_catch] Catching '{item}'.")
    return [{"key": "catch_action", "data": {"item": item}}]
