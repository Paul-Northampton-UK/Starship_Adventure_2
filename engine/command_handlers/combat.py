"""Basic combat command handlers (placeholder implementations)."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_attack(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target
    if target:
        logger.info(f"[handle_attack] Attacking '{target}'.")
        return [{"key": "combat_attack_target", "data": {"target": target}}]
    logger.info("[handle_attack] Preparing to attack.")
    return [{"key": "combat_attack_ready", "data": {}}]


def handle_aim(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target
    if target:
        logger.info(f"[handle_aim] Aiming at '{target}'.")
        return [{"key": "combat_aim_target", "data": {"target": target}}]
    logger.info("[handle_aim] Aiming weapon.")
    return [{"key": "combat_aim_ready", "data": {}}]


def handle_shoot(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    weapon = parsed_intent.secondary_target
    target = parsed_intent.target
    logger.info(f"[handle_shoot] Shooting weapon='{weapon}' target='{target}'.")
    return [
        {
            "key": "combat_shoot",
            "data": {"weapon": weapon or "weapon", "target": target or "target"},
        }
    ]

def handle_reload(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    weapon = parsed_intent.target
    ammo = parsed_intent.secondary_target
    logger.info(f"[handle_reload] Reloading weapon='{weapon}' ammo='{ammo}'.")
    return [
        {
            "key": "combat_reload",
            "data": {"weapon": weapon or "weapon", "ammo": ammo or "ammo"},
        }
    ]


def handle_unload(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    weapon = parsed_intent.target
    logger.info(f"[handle_unload] Unloading weapon='{weapon}'.")
    return [
        {
            "key": "combat_unload",
            "data": {"weapon": weapon or "weapon"},
        }
    ]


def handle_check(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target or "status"
    key = "combat_check_ammo" if target == "ammo" else "combat_check_weapon"
    logger.info(f"[handle_check] Checking '{target}'.")
    return [{"key": key, "data": {"target": target}}]


def handle_block(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_block] Blocking incoming attack.")
    return [{"key": "combat_block", "data": {}}]


def handle_dodge(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_dodge] Dodging.")
    return [{"key": "combat_dodge", "data": {}}]


def handle_flee(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    logger.info("[handle_flee] Attempting to flee.")
    return [{"key": "combat_flee", "data": {}}]
