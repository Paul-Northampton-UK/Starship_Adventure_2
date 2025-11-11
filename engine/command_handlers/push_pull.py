"""Placeholder handlers for push and pull commands."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_push(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    obj = parsed_intent.target or "object"
    logger.info(f"[handle_push] Pushing '{obj}'.")
    return [{"key": "interaction_push", "data": {"object": obj}}]


def handle_pull(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    obj = parsed_intent.target or "object"
    logger.info(f"[handle_pull] Pulling '{obj}'.")
    return [{"key": "interaction_pull", "data": {"object": obj}}]
