"""Command handlers for locking and unlocking objects."""

from typing import Any

from loguru import logger

from ..command_defs import CommandIntent, ParsedIntent
from ..game_state import GameState


def handle_lock(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict[str, Any]]:
    """Handles the LOCK command intent."""
    target_object_id = parsed_intent.target_object_id
    key_item_id = parsed_intent.secondary_target_id # The key to use
    target_object_name = parsed_intent.target or target_object_id
    key_item_name = parsed_intent.secondary_target or key_item_id

    logger.debug(f"[handle_lock] Attempting to lock: Target='{target_object_name}' (ID: {target_object_id}), Key='{key_item_name}' (ID: {key_item_id})")

    if not target_object_id:
        logger.warning("[handle_lock] No target object ID identified.")
        return [{ "key": "LOCK_NO_TARGET", "data": {} }]

    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"[handle_lock] Object data not found for target ID: {target_object_id}")
        return [{ "key": "LOCK_TARGET_NOT_FOUND", "data": {"target_name": target_object_name or "something"} }]

    obj_state = game_state.get_object_state(target_object_id) # Ensure state is initialized
    base_lock_details = obj_data.get("lock_details", {})
    runtime_lock_details = obj_state.get("lock_details", {})

    # Check if the object is lockable
    if not base_lock_details.get("type") and not runtime_lock_details.get("type"):
        logger.info(f"[handle_lock] Target '{target_object_name}' is not lockable.")
        return [{ "key": "LOCK_FAIL_NOT_LOCKABLE", "data": {"target_name": target_object_name} }]

    # Check if already locked
    if runtime_lock_details.get("locked", False):
        logger.info(f"[handle_lock] Target '{target_object_name}' is already locked.")
        return [{ "key": "ALREADY_LOCKED", "data": {"target_name": target_object_name} }]

    # Determine the required key ID from base data or runtime state
    # Runtime state might have a key_id if it was set dynamically, otherwise fallback to base.
    required_key_id = runtime_lock_details.get("key_id") or base_lock_details.get("key_id")

    if not required_key_id:
        logger.warning(f"[handle_lock] '{target_object_name}' is lockable but no key_id defined in base data or runtime state. Cannot lock.")
        return [{ "key": "LOCK_FAIL_NO_KEY_DEFINED", "data": {"target_name": target_object_name} }]

    # Check if the player provided a key and if it's the correct one
    if not key_item_id:
        # Attempt auto-use if exactly one correct key is held/worn
        held_or_worn_key = game_state.find_item_id_held_or_worn(required_key_id)
        if held_or_worn_key == required_key_id:
            key_item_id = required_key_id
            key_item_name = game_state._get_object_name(required_key_id)
            logger.info(f"[handle_lock] Auto-using held/worn required key '{required_key_id}'.")
        else:
            logger.info("[handle_lock] Player did not specify a key to lock with.")
            return [{ "key": "LOCK_FAIL_KEY_MISSING", "data": {"target_name": target_object_name} }]
    
    # Player provided a key_item_id, check if they have it (in hands or worn - keys are usually small)
    # find_item_id_held_or_worn checks hands, directly worn, and inside worn containers.
    actual_player_key_id = game_state.find_item_id_held_or_worn(key_item_id) 
    # key_item_id from parser is the player's input, actual_player_key_id is the resolved ID if found

    if not actual_player_key_id:
        logger.info(f"[handle_lock] Player does not possess the specified key item '{key_item_name}' (parsed ID: {key_item_id}).")
        return [{ "key": "LOCK_FAIL_KEY_NOT_HELD", "data": {"target_name": target_object_name, "key_name": key_item_name or "the key"} }]

    if actual_player_key_id != required_key_id:
        logger.info(f"[handle_lock] Player used wrong key. Target: '{target_object_name}', Required: '{required_key_id}', Provided: '{actual_player_key_id}' (Original input: '{key_item_name}').")
        key_data_provided = game_state.get_object_by_id(actual_player_key_id)
        provided_key_display_name = key_data_provided.get("name", actual_player_key_id) if key_data_provided else actual_player_key_id
        return [{ "key": "LOCK_FAIL_WRONG_KEY", "data": {"target_name": target_object_name, "key_name": provided_key_display_name} }]

    # Correct key, proceed to lock
    # update_object_lock_state ensures the lock_details dict exists and updates 'locked'
    if game_state.update_object_lock_state(target_object_id, True):
        logger.info(f"[handle_lock] Successfully locked '{target_object_name}' with key '{actual_player_key_id}'. State: {game_state.get_object_state(target_object_id)}")
        return [{ "key": "LOCK_SUCCESS", "data": {"target_name": target_object_name, "key_name": key_item_name or actual_player_key_id} }]
    else:
        logger.error(f"[handle_lock] Failed to update lock state for '{target_object_name}' via game_state.update_object_lock_state.")
        return [{ "key": "LOCK_FAIL_INTERNAL_ERROR", "data": {"target_name": target_object_name} }] 

def handle_unlock(game_state: GameState, parsed_intent: ParsedIntent) -> list[dict[str, Any]]:
    """Handles the UNLOCK command intent."""
    target_object_id = parsed_intent.target_object_id
    key_item_id = parsed_intent.secondary_target_id # The key to use
    target_object_name = parsed_intent.target or target_object_id
    key_item_name = parsed_intent.secondary_target or key_item_id

    logger.debug(f"[handle_unlock] Attempting to unlock: Target='{target_object_name}' (ID: {target_object_id}), Key='{key_item_name}' (ID: {key_item_id})")

    if not target_object_id:
        logger.warning("[handle_unlock] No target object ID identified.")
        return [{ "key": "UNLOCK_NO_TARGET", "data": {} }]

    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"[handle_unlock] Object data not found for target ID: {target_object_id}")
        return [{ "key": "UNLOCK_TARGET_NOT_FOUND", "data": {"target_name": target_object_name or "something"} }]

    obj_state = game_state.get_object_state(target_object_id) # Ensure state is initialized
    base_lock_details = obj_data.get("lock_details", {})
    runtime_lock_details = obj_state.get("lock_details", {})

    # Check if the object is lockable (implicitly, if it has lock details)
    if not base_lock_details.get("type") and not runtime_lock_details.get("type"):
        logger.info(f"[handle_unlock] Target '{target_object_name}' is not lockable (no lock type). Cannot unlock.")
        # This response implies it's not something that *can* be locked/unlocked
        return [{ "key": "UNLOCK_FAIL_NOT_LOCKABLE", "data": {"target_name": target_object_name} }]

    # Check if already unlocked
    # If 'locked' key is missing from runtime_lock_details, or it's explicitly False
    if not runtime_lock_details.get("locked", False):
        logger.info(f"[handle_unlock] Target '{target_object_name}' is already unlocked.")
        return [{ "key": "ALREADY_UNLOCKED", "data": {"target_name": target_object_name} }]

    # Determine the required key ID (runtime first, then base)
    required_key_id = runtime_lock_details.get("key_id") or base_lock_details.get("key_id")

    if not required_key_id:
        logger.warning(f"[handle_unlock] '{target_object_name}' is locked but no key_id defined in base or runtime state. Cannot unlock without a defined key.")
        return [{ "key": "UNLOCK_FAIL_NO_KEY_DEFINED", "data": {"target_name": target_object_name} }]

    # Check if the player provided a key and if it's the correct one
    if not key_item_id:
        # Attempt auto-use if exactly one correct key is held/worn
        held_or_worn_key = game_state.find_item_id_held_or_worn(required_key_id)
        if held_or_worn_key == required_key_id:
            key_item_id = required_key_id
            key_item_name = game_state._get_object_name(required_key_id)
            logger.info(f"[handle_unlock] Auto-using held/worn required key '{required_key_id}'.")
        else:
            logger.info("[handle_unlock] Player did not specify a key to unlock with.")
            return [{ "key": "UNLOCK_FAIL_KEY_MISSING", "data": {"target_name": target_object_name} }]

    # Player provided a key_item_id, check if they have it (in hands or worn)
    actual_player_key_id = game_state.find_item_id_held_or_worn(key_item_id)

    if not actual_player_key_id:
        logger.info(f"[handle_unlock] Player does not possess the specified key item '{key_item_name}' (parsed ID: {key_item_id}).")
        return [{ "key": "UNLOCK_FAIL_KEY_NOT_HELD", "data": {"target_name": target_object_name, "key_name": key_item_name or "the key"} }]

    if actual_player_key_id != required_key_id:
        logger.info(f"[handle_unlock] Player used wrong key. Target: '{target_object_name}', Required: '{required_key_id}', Provided: '{actual_player_key_id}' (Original input: '{key_item_name}').")
        key_data_provided = game_state.get_object_by_id(actual_player_key_id)
        provided_key_display_name = key_data_provided.get("name", actual_player_key_id) if key_data_provided else actual_player_key_id
        return [{ "key": "UNLOCK_FAIL_WRONG_KEY", "data": {"target_name": target_object_name, "key_name": provided_key_display_name} }]

    # Correct key, proceed to unlock
    if game_state.update_object_lock_state(target_object_id, False):
        logger.info(f"[handle_unlock] Successfully unlocked '{target_object_name}' with key '{actual_player_key_id}'. State: {game_state.get_object_state(target_object_id)}")
        return [{ "key": "UNLOCK_SUCCESS", "data": {"target_name": target_object_name, "key_name": key_item_name or actual_player_key_id} }]
    else:
        logger.error(f"[handle_unlock] Failed to update lock state for '{target_object_name}' via game_state.update_object_lock_state.")
        return [{ "key": "UNLOCK_FAIL_INTERNAL_ERROR", "data": {"target_name": target_object_name} }]

# Ensure the functions are registered in game_loop.py map
COMMAND_HANDLERS = {
    CommandIntent.UNLOCK: handle_unlock,
    CommandIntent.LOCK: handle_lock,
} 