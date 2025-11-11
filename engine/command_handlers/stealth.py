"""Stealth and thievery command handlers."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_sneak(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_sneak] Attempting to move quietly.")
    return [{"key": "stealth_sneak", "data": {}}]


def handle_hide(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_hide] Trying to remain unseen.")
    return [{"key": "stealth_hide", "data": {}}]


def handle_pickpocket(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    npc = parsed_intent.target or "target"
    logger.info(f"[handle_pickpocket] Attempting to pickpocket '{npc}'.")
    return [{"key": "stealth_pickpocket", "data": {"npc": npc}}]


def handle_disarm_trap(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    trap = parsed_intent.target or "trap"
    logger.info(f"[handle_disarm_trap] Attempting to disarm '{trap}'.")
    return [{"key": "stealth_disarm_trap", "data": {"trap": trap}}]
