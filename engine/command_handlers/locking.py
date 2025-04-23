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

    target_name = parsed_intent.target
    key_name = parsed_intent.secondary_target # The key specified, e.g., "unlock door with keycard"
    
    if not target_name:
        logging.error("UNLOCK command missing target object.")
        # Return dictionary directly
        return [{'key': 'error_generic', 'data': {'reason': "Specify what you want to unlock."}}]

    # --- Find the target object in the current location --- 
    target_obj_id = game_state.find_object_id_by_name_in_location(target_name)
    
    if not target_obj_id:
         logging.warning(f"Unlock target '{target_name}' not found in current location.")
         # Return dictionary directly
         return [{'key': UNLOCK_FAIL_TARGET_NOT_FOUND, 'data': {"target": target_name}}]

    # --- Get target object base data and runtime state ---
    target_obj_data = game_state.get_object_by_id(target_obj_id)
    target_obj_state = game_state.get_object_state(target_obj_id)
    
    if not target_obj_data:
        logging.error(f"Could not retrieve base data for target object ID '{target_obj_id}' despite finding it in location.")
        # Return dictionary directly
        return [{'key': 'error_internal', 'data': {'action': "unlock data missing"}}]

    # --- Check if the object is lockable (use lock_type presence) ---
    # Reverted: Check top-level key
    # --- Add Final Focused Logging --- 
    raw_lockable_value = target_obj_data.get("lockable") # Get raw value without default
    logging.debug(f"[handle_unlock] FINAL CHECK - Raw value for 'lockable': {raw_lockable_value} (Type: {type(raw_lockable_value)})")
    # --- End Final Focused Logging ---
    # MODIFIED CHECK: Determine lockable status based on presence of lock_type
    lock_type_value = target_obj_data.get("lock_type")
    is_lockable = bool(lock_type_value) 
    logging.debug(f"[handle_unlock] Checking lockability based on lock_type: '{lock_type_value}'. Result: {is_lockable}")
    # is_lockable = target_obj_data.get("lockable", False) # Previous check
    # Remove extra logging
    if not is_lockable:
        logging.warning(f"Player tried to unlock non-lockable object (based on lock_type): '{target_name}' (ID: {target_obj_id})")
        # Return dictionary directly
        return [{'key': UNLOCK_FAIL_NOT_LOCKABLE, 'data': {"target": target_name}}]

    # --- Check lock status and required key --- 
    # Use top-level is_locked for initial status, and top-level lock_key_id
    target_obj_state = game_state.get_object_state(target_obj_id) # Get runtime state
    lock_details = target_obj_state.get("lock_details", {}) 
    # Runtime state determines current lock status
    is_currently_locked = lock_details.get("locked", target_obj_data.get("is_locked", False)) # Fallback to base data if needed
    # Base data determines the key required
    required_key_id = target_obj_data.get("lock_key_id") 
    
    # --- Check if the object is already unlocked ---
    if not is_currently_locked:
        logging.info(f"Object '{target_name}' (ID: {target_obj_id}) is already unlocked.")
        # Return dictionary directly
        return [{'key': UNLOCK_FAIL_NOT_LOCKED, 'data': {"target": target_name}}]

    # --- Handle unlocking logic --- 

    # Case 1: Lock requires a specific key ID
    if required_key_id:
        logging.debug(f"Lock '{target_name}' requires key ID: '{required_key_id}'. Player specified key: '{key_name}'")
        # Check if the player specified a key in the command
        if not key_name:
             logging.warning(f"Player tried 'unlock {target_name}' but key '{required_key_id}' is required and none was specified.")
             # Return dictionary directly
             return [{'key': UNLOCK_FAIL_NO_KEY, 'data': {"target": target_name}}]

        # Player specified a key, try to find the *required* key in their possession
        # Use required_key_id for the search, not the potentially ambiguous key_name
        logging.debug(f"Searching player possession for required key ID: '{required_key_id}' (Player typed: '{key_name}')")
        player_has_required_key = game_state.find_item_id_held_or_worn(required_key_id)

        # if not player_key_id: # Old check using ambiguous key_name
        if not player_has_required_key:
            player_specified_key_actual_id = game_state.find_item_id_held_or_worn(key_name) # Check if they HAVE the key they named
            if player_specified_key_actual_id:
                logging.warning(f"Player tried to unlock with key '{key_name}', which they have (ID: {player_specified_key_actual_id}), but the required key '{required_key_id}' was not found in possession.")
                # Give wrong key message if they specified a key they possess, but it's not the right one
                return [{'key': UNLOCK_FAIL_WRONG_KEY, 'data': {"target": target_name, "key_name": key_name}}]
            else:
                # Give not found message if the key they specified wasn't found either
                logging.warning(f"Player tried to unlock with key '{key_name}', but the required key '{required_key_id}' was not found, AND '{key_name}' was not found in possession either.")
                return [{'key': UNLOCK_FAIL_KEY_NOT_FOUND, 'data': {"key_name": key_name}}]

        # Player has the required key, proceed with unlocking
        # Use the required_key_id for logging consistency
        logging.info(f"Unlocking '{target_name}' with required key (ID: {required_key_id}). Player specified '{key_name}'.")
        # --- !!! Update Game State !!! ---
        success_update = game_state.update_object_lock_state(target_obj_id, locked=False)
        if success_update:
             # Use the actual name of the required key in the message if possible
             actual_key_name = game_state._get_object_name(required_key_id) or key_name
             return [{'key': UNLOCK_SUCCESS, 'data': {"target": target_name, "key_name": actual_key_name}}]
        else:
             logging.error(f"Failed to update lock state for '{target_obj_id}' after successful key match.")
             # Return dictionary directly (using error_generic for now)
             return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed"}}]

    # Case 2: Lock does NOT require a specific key ID (e.g., maybe a puzzle lock, or just needs 'unlock')
    else: # required_key_id is None or empty
         logging.info(f"Object '{target_name}' is locked but requires no specific key ID. Attempting generic unlock.")
         # If the lock requires no key, simply attempting to unlock it might be enough.
         # Or, this could be where a skill check (like lockpicking) would go.
         # For now, let's assume unlocking succeeds if no key is required.
         success_update = game_state.update_object_lock_state(target_obj_id, locked=False)
         if success_update:
             # Return dictionary directly, passing key_name=None
             return [{'key': UNLOCK_SUCCESS, 'data': {"target": target_name, "key_name": None}}]
         else:
             logging.error(f"Failed to update lock state for '{target_obj_id}' (no key required case).")
             # Return dictionary directly
             return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed (no key)"}}]


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

    target_name = parsed_intent.target
    key_name = parsed_intent.secondary_target # The key specified, e.g., "lock door with keycard"
    
    if not target_name:
        logging.error("LOCK command missing target object.")
        # Return dictionary directly
        return [{'key': 'error_generic', 'data': {'reason': "Specify what you want to lock."}}]

    # --- Find the target object in the current location --- 
    target_obj_id = game_state.find_object_id_by_name_in_location(target_name)
    
    if not target_obj_id:
         logging.warning(f"Lock target '{target_name}' not found in current location.")
         # Return dictionary directly
         return [{'key': LOCK_FAIL_TARGET_NOT_FOUND, 'data': {"target": target_name}}]

    # --- Get target object base data and runtime state ---
    target_obj_data = game_state.get_object_by_id(target_obj_id)
    target_obj_state = game_state.get_object_state(target_obj_id)
    
    if not target_obj_data:
        logging.error(f"Could not retrieve base data for target object ID '{target_obj_id}'.")
        # Return dictionary directly
        return [{'key': 'error_internal', 'data': {'action': "lock data missing"}}]

    # --- Check if the object is lockable (use lock_type presence) ---
    # Reverted: Check top-level key
    # --- Add Final Focused Logging --- 
    raw_lockable_value = target_obj_data.get("lockable") # Get raw value without default
    logging.debug(f"[handle_lock] FINAL CHECK - Raw value for 'lockable': {raw_lockable_value} (Type: {type(raw_lockable_value)})")
    # --- End Final Focused Logging ---
    # MODIFIED CHECK: Determine lockable status based on presence of lock_type
    lock_type_value = target_obj_data.get("lock_type")
    is_lockable = bool(lock_type_value)
    logging.debug(f"[handle_lock] Checking lockability based on lock_type: '{lock_type_value}'. Result: {is_lockable}")
    # is_lockable = target_obj_data.get("lockable", False) # Previous check
    # Remove extra logging
    if not is_lockable:
        logging.warning(f"Player tried to lock non-lockable object (based on lock_type): '{target_name}' (ID: {target_obj_id})")
        # Return dictionary directly
        return [{'key': LOCK_FAIL_NOT_LOCKABLE, 'data': {"target": target_name}}]

    # --- Check lock status and required key --- 
    lock_details = target_obj_state.get("lock_details", {})
    # Runtime state determines current lock status
    is_currently_locked = lock_details.get("locked", target_obj_data.get("is_locked", False)) # Fallback to base data if needed
    # Base data determines the key required
    required_key_id = target_obj_data.get("lock_key_id")
    
    # --- Check if the object is already locked ---
    if is_currently_locked:
        logging.info(f"Object '{target_name}' (ID: {target_obj_id}) is already locked.")
        # Return dictionary directly
        return [{'key': LOCK_FAIL_ALREADY_LOCKED, 'data': {"target": target_name}}]

    # --- Handle locking logic --- 

    # Case 1: Lock requires a specific key ID
    if required_key_id:
        logging.debug(f"Lock '{target_name}' requires key ID: '{required_key_id}'. Player specified key: '{key_name}'")
        if not key_name:
             logging.warning(f"Player tried 'lock {target_name}' but key '{required_key_id}' is required and none was specified.")
             # Return dictionary directly
             return [{'key': LOCK_FAIL_NO_KEY, 'data': {"target": target_name}}]

        # Player specified a key, try to find it
        player_key_id = game_state.find_item_id_held_or_worn(key_name)
        
        if not player_key_id:
            logging.warning(f"Player tried to lock with key '{key_name}', but they don't have it accessible.")
            # Return dictionary directly, using new key 'key_name'
            return [{'key': LOCK_FAIL_KEY_NOT_FOUND, 'data': {"key_name": key_name}}]

        # Player has the key, check if it's the right one
        if player_key_id == required_key_id:
            logging.info(f"Locking '{target_name}' with matching key '{key_name}' (ID: {player_key_id})")
            # --- !!! Update Game State !!! ---
            success_update = game_state.update_object_lock_state(target_obj_id, locked=True) # Set locked to True
            if success_update:
                 # Return dictionary directly, using new key 'key_name'
                 return [{'key': LOCK_SUCCESS, 'data': {"target": target_name, "key_name": key_name}}]
            else:
                 logging.error(f"Failed to update lock state for '{target_obj_id}' after successful key match.")
                 # Return dictionary directly
                 return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed"}}]
        else:
            # Wrong key
            logging.warning(f"Player tried to lock '{target_name}' with wrong key '{key_name}' (ID: {player_key_id}). Required: '{required_key_id}'")
            # Return dictionary directly, using new key 'key_name'
            return [{'key': LOCK_FAIL_WRONG_KEY, 'data': {"target": target_name, "key_name": key_name}}]

    # Case 2: Lock does NOT require a specific key ID
    else: # required_key_id is None or empty
         logging.info(f"Object '{target_name}' is unlockable but requires no specific key ID. Attempting generic lock.")
         # If the lock requires no key, simply attempting to lock it might be enough.
         success_update = game_state.update_object_lock_state(target_obj_id, locked=True) # Set locked to True
         if success_update:
             # Return dictionary directly, passing key_name=None
             return [{'key': LOCK_SUCCESS, 'data': {"target": target_name, "key_name": None}}]
         else:
             logging.error(f"Failed to update lock state for '{target_obj_id}' (no key required case).")
             # Return dictionary directly
             return [{'key': 'error_generic', 'data': {'reason': "Lock state update failed (no key)"}}]


# Ensure the functions are registered in game_loop.py map
COMMAND_HANDLERS = {
    CommandIntent.UNLOCK: handle_unlock,
    CommandIntent.LOCK: handle_lock,
} 