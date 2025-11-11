"""Placeholder handlers for magic-related intents."""

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_cast(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    spell = parsed_intent.target or "spell"
    target = parsed_intent.secondary_target
    logger.info(f"[handle_cast] Casting '{spell}' at '{target}'.")
    return [
        {
            "key": "magic_cast",
            "data": {"spell": spell, "target": target or "target"},
        }
    ]


def handle_channel(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    power = parsed_intent.target or "power"
    logger.info(f"[handle_channel] Channeling '{power}'.")
    return [{"key": "magic_channel", "data": {"power": power}}]


def handle_summon(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    entity = parsed_intent.target or "entity"
    logger.info(f"[handle_summon] Summoning '{entity}'.")
    return [{"key": "magic_summon", "data": {"entity": entity}}]


def handle_dismiss(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    entity = parsed_intent.target or "entity"
    logger.info(f"[handle_dismiss] Dismissing '{entity}'.")
    return [{"key": "magic_dismiss", "data": {"entity": entity}}]


def handle_enchant(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    item = parsed_intent.target or "item"
    effect = parsed_intent.secondary_target
    logger.info(f"[handle_enchant] Enchanting '{item}' with '{effect}'.")
    data = {"item": item}
    if effect:
        data["effect"] = effect
    return [{"key": "magic_enchant", "data": data}]


def handle_identify(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target or "object"
    logger.info(f"[handle_identify] Identifying '{target}'.")
    return [{"key": "magic_identify", "data": {"target": target}}]


def handle_bless(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target or "target"
    logger.info(f"[handle_bless] Blessing '{target}'.")
    return [{"key": "magic_bless", "data": {"target": target}}]


def handle_curse(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    target = parsed_intent.target or "target"
    logger.info(f"[handle_curse] Cursing '{target}'.")
    return [{"key": "magic_curse", "data": {"target": target}}]


def handle_transmute(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    from_item = parsed_intent.target or "material"
    to_item = parsed_intent.secondary_target or "new form"
    logger.info(f"[handle_transmute] Transmuting '{from_item}' into '{to_item}'.")
    return [
        {"key": "magic_transmute", "data": {"from": from_item, "to": to_item}}
    ]


def handle_ritual(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict]:
    ritual_name = parsed_intent.target or "ritual"
    logger.info(f"[handle_ritual] Performing ritual '{ritual_name}'.")
    return [{"key": "magic_ritual", "data": {"name": ritual_name}}]
