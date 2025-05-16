# engine/command_handlers/locking.py
import logging
from typing import List, Dict, Optional

# Adjust relative imports based on file location
from ..game_state import GameState
from ..command_defs import CommandIntent, ParsedIntent

# --- Constants ---
# Placeholder for response keys - we'll add these to responses.yaml later
UNLOCK_SUCCESS = "unlock_success"
UNLOCK_FAIL_NO_KEY = "unlock_fail_no_key"
UNLOCK_FAIL_WRONG_KEY = "unlock_fail_wrong_key"
UNLOCK_FAIL_NOT_LOCKED = "unlock_fail_not_locked"
UNLOCK_FAIL_NOT_LOCKABLE = "unlock_fail_not_lockable"
UNLOCK_FAIL_TARGET_NOT_FOUND = "unlock_fail_target_not_found"
UNLOCK_FAIL_KEY_NOT_FOUND = "unlock_fail_key_not_found" # If key specified but not held

# TODO: Add LOCK response keys
LOCK_SUCCESS = "lock_success"
LOCK_FAIL_NO_KEY = "lock_fail_no_key"
LOCK_FAIL_WRONG_KEY = "lock_fail_wrong_key"
LOCK_FAIL_ALREADY_LOCKED = "lock_fail_already_locked"
LOCK_FAIL_NOT_LOCKABLE = "lock_fail_not_lockable"
LOCK_FAIL_TARGET_NOT_FOUND = "lock_fail_target_not_found"
LOCK_FAIL_KEY_NOT_FOUND = "lock_fail_key_not_found"

# --- Handler Functions ---

def handle_unlock(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the UNLOCK command.

    Attempts to unlock a specified target object, potentially using a key item.

    Args:
        game_state: The current state of the game.
        parsed_intent: The parsed player command, containing intent and targets.

    Returns:
        A list of dictionaries, each representing a message to be sent to the player.
    """
    logging.debug(f"Handling UNLOCK command: {parsed_intent}")

    target_name = parsed_intent.target # Keep for messages
    target_obj_id = parsed_intent.target_object_id # Use this ID directly
    key_name_from_command = parsed_intent.secondary_target # Keep for messages
    key_id_from_command = parsed_intent.secondary_target_id # Use this ID directly for the key specified in command

    if not target_obj_id: # If parser didn't resolve the target
        logging.warning(f"Unlock command failed: Target '{target_name}' could not be resolved to an ID by the parser.")
        # Attempt to find by name as a fallback, now including room context
        current_room_id, current_area_id = game_state.get_current_location()
        target_obj_id = game_state.find_object_id_by_name_in_location(
            object_name=target_name,
            room_id=current_room_id,
            area_id=current_area_id
        )
        if not target_obj_id:
            logging.warning(f"Unlock target '{target_name}' not found in current location even after fallback search.")
            return [{'key': UNLOCK_FAIL_TARGET_NOT_FOUND, 'data': {"target_name": target_name or "something"}}]

    # --- Get target object base data and runtime state ---
    target_obj_data = game_state.get_object_by_id(target_obj_id)
    # target_obj_state = game_state.get_object_state(target_obj_id) # State fetched later when needed

    if not target_obj_data:
        logging.error(f"Could not retrieve base data for target object ID '{target_obj_id}'.")
        return [{'key': 'error_internal', 'data': {'action': "unlock data missing for " + (target_name or target_obj_id)}}]

    # Use actual name from data for messages if available, fallback to parsed name
    actual_target_name = target_obj_data.get("name", target_name)

    # --- Check if the object is lockable ---
    lock_type_value = target_obj_data.get("lock_type")
    is_lockable = bool(lock_type_value) # or bool(target_obj_data.get("lock_details")) # Consider if lock_details implies lockable
    logging.debug(f"[handle_unlock] Checking lockability for '{actual_target_name}' (ID: {target_obj_id}) based on lock_type: '{lock_type_value}'. Result: {is_lockable}")

    if not is_lockable:
        logging.warning(f"Player tried to unlock non-lockable object: '{actual_target_name}' (ID: {target_obj_id})")
        return [{'key': UNLOCK_FAIL_NOT_LOCKABLE, 'data': {"target_name": actual_target_name}}]

    # --- Check lock status and required key ---
    target_obj_state = game_state.get_object_state(target_obj_id) # Get runtime state
    lock_details_state = target_obj_state.get("lock_details", {})
    
    # is_currently_locked: Check runtime state first, then base data as fallback.
    is_currently_locked = lock_details_state.get("locked", target_obj_data.get("is_locked", False))
    
    # required_key_id: This should primarily come from the object's base definition.
    required_key_id_base = target_obj_data.get("lock_key_id") # Key defined in objects.yaml
    # It could also be in lock_details from base data if that's the new pattern
    if not required_key_id_base and isinstance(target_obj_data.get("lock_details"), dict):
        required_key_id_base = target_obj_data.get("lock_details", {}).get("key_id") or target_obj_data.get("lock_details", {}).get("required_key")

    logging.debug(f"Target '{actual_target_name}' (ID: {target_obj_id}): Currently locked: {is_currently_locked}. Base required key ID: {required_key_id_base}. Key specified in command: '{key_name_from_command}' (ID: {key_id_from_command}).")

    # --- Check if the object is already unlocked ---
    if not is_currently_locked:
        logging.info(f"Object '{actual_target_name}' (ID: {target_obj_id}) is already unlocked.")
        return [{'key': UNLOCK_FAIL_NOT_LOCKED, 'data': {"target_name": actual_target_name}}]

    # --- Handle unlocking logic ---

    # Case 1: Lock requires a specific key ID (defined in its base data)
    if required_key_id_base:
        logging.debug(f"Lock '{actual_target_name}' requires key ID: '{required_key_id_base}'.")
        
        # Check if a key was specified in the command, and if it's the correct one
        if not key_id_from_command: # Player typed "unlock door" but a key is needed
            logging.warning(f"Player tried 'unlock {actual_target_name}' but key '{required_key_id_base}' is required and no key was specified in command.")
            return [{'key': UNLOCK_FAIL_NO_KEY, 'data': {"target_name": actual_target_name}}]

        # Check if the key specified in the command is actually held by the player
        # The parser provides key_id_from_command if it resolved a key name to an ID found in possession.
        if not game_state.find_item_id_held_or_worn(key_id_from_command): # Double check possession
             logging.warning(f"Player specified key '{key_name_from_command}' (resolved to ID: {key_id_from_command}), but it's not in their possession.")
             return [{'key': UNLOCK_FAIL_KEY_NOT_FOUND, 'data': {"key_name": key_name_from_command or "the key"}}]

        # Now, check if the key they specified (and possess) is the *correct* key
        if key_id_from_command == required_key_id_base:
            # Player has specified the correct key and possesses it.
            logging.info(f"Unlocking '{actual_target_name}' with correct key (ID: {required_key_id_base}). Player specified '{key_name_from_command}'.")
            success_update = game_state.update_object_lock_state(target_obj_id, locked=False)
            if success_update:
                actual_key_name_for_msg = game_state._get_object_name(required_key_id_base) or key_name_from_command or "the key"
                return [{'key': UNLOCK_SUCCESS, 'data': {"target_name": actual_target_name, "key_name": actual_key_name_for_msg}}]
            else:
                logging.error(f"Failed to update lock state for '{target_obj_id}' after successful key match.")
                return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed"}}]
        else:
            # Player specified a key they possess, but it's the wrong one for this lock.
            logging.warning(f"Player tried to unlock '{actual_target_name}' with key '{key_name_from_command}' (ID: {key_id_from_command}), but required key is '{required_key_id_base}'.")
            specified_key_actual_name = game_state._get_object_name(key_id_from_command) or key_name_from_command or "that key"
            return [{'key': UNLOCK_FAIL_WRONG_KEY, 'data': {"target_name": actual_target_name, "key_name": specified_key_actual_name}}]

    # Case 2: Lock does NOT require a specific key ID (e.g., a jammed lock, or just needs 'unlock' command)
    else: # required_key_id_base is None or empty
        logging.info(f"Object '{actual_target_name}' is locked but requires no specific key ID. Attempting generic unlock.")
        # If a key was specified in the command but none is needed, it's a bit odd.
        # For now, we'll ignore the specified key if none is required by the lock.
        # A different response might be needed if "unlock door with key" is used on a keyless but locked door.
        if key_id_from_command:
            logging.info(f"Player specified key '{key_name_from_command}' (ID: {key_id_from_command}) but no key is required for '{actual_target_name}'. Proceeding with generic unlock.")
            # Potentially add a response like "You don't need a key for that." if it remains locked.

        success_update = game_state.update_object_lock_state(target_obj_id, locked=False)
        if success_update:
            return [{'key': UNLOCK_SUCCESS, 'data': {"target_name": actual_target_name, "key_name": None}}] # No key was used/needed
        else:
            # This might happen if update_object_lock_state fails for other reasons,
            # or if the object isn't just "locked" but has a more complex state.
            logging.error(f"Failed to update lock state for '{target_obj_id}' (no specific key required case).")
            # Provide a more specific failure if possible, e.g. if it's "jammed" not just "locked"
            # For now, a generic failure.
            return [{'key': UNLOCK_FAIL_NOT_LOCKABLE, 'data': {"target_name": actual_target_name}}] # Or a new "unlock_fail_generic"


def handle_lock(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the LOCK command.

    Attempts to lock a specified target object, potentially using a key item.

    Args:
        game_state: The current state of the game.
        parsed_intent: The parsed player command, containing intent and targets.

    Returns:
        A list of dictionaries, each representing a message to be sent to the player.
    """
    logging.debug(f"Handling LOCK command: {parsed_intent}")

    target_name = parsed_intent.target # Keep for messages
    target_obj_id = parsed_intent.target_object_id # Use this ID directly
    key_name_from_command = parsed_intent.secondary_target # Keep for messages
    key_id_from_command = parsed_intent.secondary_target_id # Use this ID directly

    if not target_obj_id: # If parser didn't resolve the target
        logging.warning(f"Lock command failed: Target '{target_name}' could not be resolved to an ID by the parser.")
        # Attempt to find by name as a fallback, now including room context
        current_room_id, current_area_id = game_state.get_current_location()
        target_obj_id = game_state.find_object_id_by_name_in_location(
            object_name=target_name,
            room_id=current_room_id,
            area_id=current_area_id
        )
        if not target_obj_id:
            logging.warning(f"Lock target '{target_name}' not found in current location even after fallback search.")
            return [{'key': LOCK_FAIL_TARGET_NOT_FOUND, 'data': {"target_name": target_name or "something"}}]

    # --- Get target object base data and runtime state ---
    target_obj_data = game_state.get_object_by_id(target_obj_id)
    # target_obj_state = game_state.get_object_state(target_obj_id) # State fetched later

    if not target_obj_data:
        logging.error(f"Could not retrieve base data for target object ID '{target_obj_id}'.")
        return [{'key': 'error_internal', 'data': {'action': "lock data missing for " + (target_name or target_obj_id)}}]

    actual_target_name = target_obj_data.get("name", target_name)

    # --- Check if the object is lockable ---
    lock_type_value = target_obj_data.get("lock_type")
    is_lockable = bool(lock_type_value) # or bool(target_obj_data.get("lock_details"))
    logging.debug(f"[handle_lock] Checking lockability for '{actual_target_name}' (ID: {target_obj_id}) based on lock_type: '{lock_type_value}'. Result: {is_lockable}")

    if not is_lockable:
        logging.warning(f"Player tried to lock non-lockable object: '{actual_target_name}' (ID: {target_obj_id})")
        return [{'key': LOCK_FAIL_NOT_LOCKABLE, 'data': {"target_name": actual_target_name}}]

    # --- Check lock status and required key ---
    target_obj_state = game_state.get_object_state(target_obj_id) # Get runtime state
    lock_details_state = target_obj_state.get("lock_details", {})
    is_currently_locked = lock_details_state.get("locked", target_obj_data.get("is_locked", False)) # Fallback to base
    
    required_key_id_base = target_obj_data.get("lock_key_id")
    if not required_key_id_base and isinstance(target_obj_data.get("lock_details"), dict):
        required_key_id_base = target_obj_data.get("lock_details", {}).get("key_id") or target_obj_data.get("lock_details", {}).get("required_key")

    logging.debug(f"Target '{actual_target_name}' (ID: {target_obj_id}): Currently locked: {is_currently_locked}. Base required key ID: {required_key_id_base}. Key specified in command: '{key_name_from_command}' (ID: {key_id_from_command}).")

    # --- Check if the object is already locked ---
    if is_currently_locked:
        logging.info(f"Object '{actual_target_name}' (ID: {target_obj_id}) is already locked.")
        return [{'key': LOCK_FAIL_ALREADY_LOCKED, 'data': {"target_name": actual_target_name}}]

    # --- Handle locking logic ---

    # Case 1: Lock requires a specific key ID
    if required_key_id_base:
        logging.debug(f"Lock '{actual_target_name}' requires key ID: '{required_key_id_base}'.")
        if not key_id_from_command:
            logging.warning(f"Player tried 'lock {actual_target_name}' but key '{required_key_id_base}' is required and no key was specified.")
            return [{'key': LOCK_FAIL_NO_KEY, 'data': {"target_name": actual_target_name}}]

        if not game_state.find_item_id_held_or_worn(key_id_from_command): # Double check possession
             logging.warning(f"Player specified key '{key_name_from_command}' (resolved to ID: {key_id_from_command}), but it's not in their possession.")
             return [{'key': LOCK_FAIL_KEY_NOT_FOUND, 'data': {"key_name": key_name_from_command or "the key"}}]

        if key_id_from_command == required_key_id_base:
            logging.info(f"Locking '{actual_target_name}' with correct key (ID: {required_key_id_base}). Player specified '{key_name_from_command}'.")
            success_update = game_state.update_object_lock_state(target_obj_id, locked=True)
            if success_update:
                actual_key_name_for_msg = game_state._get_object_name(required_key_id_base) or key_name_from_command or "the key"
                return [{'key': LOCK_SUCCESS, 'data': {"target_name": actual_target_name, "key_name": actual_key_name_for_msg}}]
            else:
                logging.error(f"Failed to update lock state for '{target_obj_id}' after successful key match for lock.")
                return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed"}}]
        else:
            logging.warning(f"Player tried to lock '{actual_target_name}' with key '{key_name_from_command}' (ID: {key_id_from_command}), but required key is '{required_key_id_base}'.")
            specified_key_actual_name = game_state._get_object_name(key_id_from_command) or key_name_from_command or "that key"
            return [{'key': LOCK_FAIL_WRONG_KEY, 'data': {"target_name": actual_target_name, "key_name": specified_key_actual_name}}]

    # Case 2: Lock does NOT require a specific key ID
    else: # required_key_id_base is None or empty
        logging.info(f"Object '{actual_target_name}' can be locked without a specific key ID. Attempting generic lock.")
        if key_id_from_command:
            logging.info(f"Player specified key '{key_name_from_command}' (ID: {key_id_from_command}) but no key is required to lock '{actual_target_name}'. Proceeding with generic lock.")
        
        success_update = game_state.update_object_lock_state(target_obj_id, locked=True)
        if success_update:
            return [{'key': LOCK_SUCCESS, 'data': {"target_name": actual_target_name, "key_name": None}}]
        else:
            logging.error(f"Failed to update lock state for '{target_obj_id}' (no specific key required case for lock).")
            return [{'key': LOCK_FAIL_NOT_LOCKABLE, 'data': {"target_name": actual_target_name}}] # Or a new "lock_fail_generic"


# Ensure the functions are registered in game_loop.py map
COMMAND_HANDLERS = {
    CommandIntent.UNLOCK: handle_unlock,
    CommandIntent.LOCK: handle_lock,
} 