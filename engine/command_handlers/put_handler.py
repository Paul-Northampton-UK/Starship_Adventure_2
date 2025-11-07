"""Put command handler."""

from typing import Any

from loguru import logger

from ..command_defs import ParsedIntent
from ..game_state import GameState


def handle_put(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict[str, Any]]:
    """Handles the PUT command intent."""
    target_object_id = parsed_intent.target_object_id
    container_id = parsed_intent.secondary_target_object_id
    target_object_name = parsed_intent.target or target_object_id
    container_name = parsed_intent.secondary_target or container_id

    if not target_object_id or not container_id:
        logger.warning("Missing target or container ID for put command")
        return [{"key": "PUT_MISSING_TARGET", "data": {}}]

    # Check if target object exists and is in inventory
    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"Target object not found: {target_object_id}")
        return [{"key": "PUT_TARGET_NOT_FOUND", "data": {"target_name": target_object_name}}]

    if not game_state.is_object_in_inventory(target_object_id):
        return [{"key": "PUT_NOT_IN_INVENTORY", "data": {"target_name": target_object_name}}]

    # Check if container exists and is a storage container
    container_data = game_state.get_object_by_id(container_id)
    if not container_data:
        logger.warning(f"Container not found: {container_id}")
        return [{"key": "PUT_CONTAINER_NOT_FOUND", "data": {"container_name": container_name}}]

    if not container_data.get("properties", {}).get("is_storage", False):
        return [{"key": "PUT_NOT_STORAGE", "data": {"container_name": container_name}}]

    # Check if container is in inventory or worn
    container_state = game_state.get_object_state(container_id)
    is_worn = container_state.get("is_worn", False)
    if not game_state.is_object_in_inventory(container_id) and not is_worn:
        return [{"key": "PUT_CONTAINER_NOT_ACCESSIBLE", "data": {"container_name": container_name}}]

    # Check if container is open
    if not container_state.get("is_open", False):
        return [{"key": "PUT_CONTAINER_CLOSED", "data": {"container_name": container_name}}]

    # Add to container
    game_state.add_to_container(container_id, target_object_id)
    game_state.remove_from_inventory(target_object_id)
    game_state.set_object_state(target_object_id, "is_visible", True)

    return [{"key": "PUT_SUCCESS", "data": {"target_name": target_object_name, "container_name": container_name}}] 