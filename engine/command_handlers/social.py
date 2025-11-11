"""Placeholder social interaction handlers (talk/ask/give/show)."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def _safe_name(name: str | None, fallback: str) -> str:
    cleaned = (name or "").strip()
    return cleaned or fallback


def handle_talk(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    npc_name = _safe_name(parsed_intent.target, "someone")
    logger.info(f"[handle_talk] Attempting to talk to '{npc_name}'.")
    return [{"key": "social_talk_placeholder", "data": {"npc_name": npc_name}}]


def handle_ask(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    npc_name = _safe_name(parsed_intent.target, "someone")
    topic = _safe_name(parsed_intent.secondary_target, "that topic")
    logger.info(f"[handle_ask] Asking '{npc_name}' about '{topic}'.")
    return [{"key": "social_ask_placeholder", "data": {"npc_name": npc_name, "topic": topic}}]


def handle_give(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    object_name = _safe_name(parsed_intent.target, "something")
    npc_name = _safe_name(parsed_intent.secondary_target, "someone")
    logger.info(f"[handle_give] Giving '{object_name}' to '{npc_name}'.")
    return [
        {
            "key": "social_give_placeholder",
            "data": {"npc_name": npc_name, "object_name": object_name},
        }
    ]


def handle_show(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    object_name = _safe_name(parsed_intent.target, "something")
    npc_name = _safe_name(parsed_intent.secondary_target, "someone")
    logger.info(f"[handle_show] Showing '{object_name}' to '{npc_name}'.")
    return [
        {
            "key": "social_show_placeholder",
            "data": {"npc_name": npc_name, "object_name": object_name},
        }
    ]
