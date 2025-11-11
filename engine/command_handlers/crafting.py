"""Placeholder crafting and survival command handlers."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_craft(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    logger.info(f"[handle_craft] Crafting '{item}'.")
    return [{"key": "craft_make", "data": {"item": item}}]


def handle_combine(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item_a = parsed_intent.target or "item A"
    item_b = parsed_intent.secondary_target or "item B"
    logger.info(f"[handle_combine] Combining '{item_a}' with '{item_b}'.")
    return [{"key": "craft_combine", "data": {"item_a": item_a, "item_b": item_b}}]


def handle_gather(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    resource = parsed_intent.target or "resource"
    logger.info(f"[handle_gather] Gathering '{resource}'.")
    return [{"key": "craft_gather", "data": {"resource": resource}}]
