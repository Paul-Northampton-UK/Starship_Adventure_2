from typing import Any

from engine.command_intent import CommandIntent
from engine.intent import ParsedIntent
from loguru import logger

from engine.game_state import GameState


def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict[str, Any]]:
    """Handles the TAKE command intent."""
    target_object_id = parsed_intent.target_object_id
    target_object_name = parsed_intent.target or target_object_id

    if not target_object_id:
        logger.warning("No target object ID identified for take command")
        return [{"key": "TAKE_NO_TARGET", "data": {}}]

    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"Object data not found for ID: {target_object_id}")
        return [{"key": "TAKE_TARGET_NOT_FOUND", "data": {"target_name": target_object_name or "something"}}]

    # Check if object is already in inventory
    if game_state.is_object_in_inventory(target_object_id):
        return [{"key": "TAKE_ALREADY_HAVE", "data": {"target_name": target_object_name}}]

    # Check if object is visible
    if not game_state.is_object_visible(target_object_id):
        return [{"key": "TAKE_NOT_VISIBLE", "data": {"target_name": target_object_name}}]

    # Check if object is takeable
    if not obj_data.get("properties", {}).get("is_takeable", False):
        return [{"key": "TAKE_NOT_TAKEABLE", "data": {"target_name": target_object_name}}]

    # Check if hands are full
    if len(game_state.hand_slot) >= 2:
        held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
        return [{"key": "TAKE_HANDS_FULL", "data": {"held_item_name": held_items_str, "item_name": target_object_name}}]

    # Check if item is on a surface
    current_room_id = game_state.current_room_id
    visible_objects = game_state._get_all_object_ids_in_current_location(visible_only=True)
    for surface_id in visible_objects:
        surface_data = game_state.get_object_by_id(surface_id)
        if surface_data and surface_data.get("properties", {}).get("is_surface"):
            surface_state = game_state.get_object_state(surface_id)
            if target_object_id in surface_state.get("on_surface_items", []):
                # Remove from surface
                current_items = surface_state.get("on_surface_items", [])
                current_items.remove(target_object_id)
                game_state.set_object_state(surface_id, "on_surface_items", current_items)
                # Add to inventory
                game_state.hand_slot.append(target_object_id)
                game_state.set_object_state(target_object_id, "is_visible", True)
                return [{"key": "TAKE_SUCCESS", "data": {"target_name": target_object_name}}]

    # If not on a surface, try taking from room
    result_message = game_state.take_object(target_object_id)
    if "You take the" in result_message:
        return [{"key": "TAKE_SUCCESS", "data": {"target_name": target_object_name}}]
    else:
        logger.warning(f"Failed to take object '{target_object_name}': {result_message}")
        return [{"key": "TAKE_FAIL", "data": {"target_name": target_object_name, "message": result_message}}]

    # Check if this was part of a compound command (take and wear)
    if parsed_intent.follow_up_intent and parsed_intent.follow_up_intent.intent == CommandIntent.EQUIP:
        # Create a new equip intent for the follow-up action
        equip_intent = ParsedIntent(
            intent=CommandIntent.EQUIP,
            target=parsed_intent.follow_up_intent.target,
            target_object_id=target_object_id  # Use the same object ID
        )
        # Call the equip handler
        from engine.command_handlers.equip_handler import handle_equip
        equip_response = handle_equip(game_state, equip_intent)
        return [{"key": "TAKE_SUCCESS", "data": {"target_name": target_object_name}}] + equip_response

    return [{"key": "TAKE_SUCCESS", "data": {"target_name": target_object_name}}] 