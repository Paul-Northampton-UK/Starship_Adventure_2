"""Command handlers for open and close actions."""

from loguru import logger
from typing import List, Dict, Any, Optional

from ..game_state import GameState
from ..command_defs import ParsedIntent, CommandIntent

def handle_open(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict[str, Any]]:
    """Handles the OPEN command intent."""
    target_object_id = parsed_intent.target_object_id
    target_object_name = parsed_intent.target or target_object_id # Player-facing name

    logger.debug(f"[handle_open] Attempting to open: ID='{target_object_id}', Name='{target_object_name}'")

    if not target_object_id:
        logger.warning("[handle_open] No target object ID identified by parser.")
        return [{ "key": "OPEN_NO_TARGET", "data": {} }]

    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"[handle_open] Object data not found for ID: {target_object_id}")
        return [{ "key": "OPEN_TARGET_NOT_FOUND", "data": {"target_name": target_object_name or "something"} }]

    obj_state = game_state.get_object_state(target_object_id)
    obj_props = obj_data.get("properties", {})

    # Check if it's even openable/closable first
    if not obj_props.get("is_openable_closable", False):
        logger.debug(f"[handle_open] Object '{target_object_name}' is not openable/closable based on properties.")
        return [{"key": "OPEN_FAIL_NOT_OPENABLE", "data": {"target_name": target_object_name}}]

    # Check if locked
    lock_details = obj_state.get("lock_details", {})
    if lock_details.get("locked", False): # Check runtime state
        logger.info(f"[handle_open] '{target_object_name}' is locked.")
        return [{"key": "OPEN_FAIL_LOCKED", "data": {"target_name": target_object_name}}]

    # Check if already open
    if obj_state.get("is_open", False):
        logger.info(f"[handle_open] '{target_object_name}' is already open.")
        # If it's storage, list contents or say empty
        if obj_props.get("is_storage", False):
            items_in_container_data: List[Dict[str, Any]] = []
            contained_item_references = obj_state.get("contains", [])

            if contained_item_references:
                for item_ref in contained_item_references:
                    item_id_in_container = None
                    if isinstance(item_ref, str):
                        item_id_in_container = item_ref
                    elif isinstance(item_ref, dict) and 'id' in item_ref: # Handles if contains stores dicts like {'id': 'X'}
                        item_id_in_container = item_ref['id']
                    else:
                        logger.warning(f"[handle_open] Found a reference in container '{target_object_name}' of unexpected type or missing ID: {item_ref}")
                        continue

                    if not item_id_in_container: # Should be redundant if above logic is sound
                        logger.warning(f"[handle_open] Null or empty item_id_in_container from ref: {item_ref}")
                        continue
                        
                    # Make items visible (if they weren't already)
                    game_state.set_object_state(item_id_in_container, "is_visible", True)
                    
                    # Get the full data for the item to get its name etc.
                    item_data_for_list = game_state.get_object_by_id(item_id_in_container)
                    if item_data_for_list:
                        items_in_container_data.append(item_data_for_list)
                    else:
                        logger.warning(f"[handle_open] Could not retrieve data for item ID '{item_id_in_container}' found in '{target_object_name}'.")

                if items_in_container_data:
                    # Correctly extract names from the dictionaries in items_in_container_data
                    item_names = [item_data.get("name", "an unknown item") for item_data in items_in_container_data]
                    response_key = "OPEN_SUCCESS_CONTENTS"
                    response_data = {"container_name": target_object_name, "item_list_str": ", ".join(item_names)}
                else: # Contained references but couldn't get data for any of them, or container was empty from start
                    response_key = "OPEN_SUCCESS_EMPTY"
                    response_data = {"container_name": target_object_name}
            else: # No contained_item_references
                logger.info(f"[handle_open] '{target_object_name}' is empty according to its 'contains' state.")
                response_key = "OPEN_SUCCESS_EMPTY"
                response_data = {"container_name": target_object_name}
            
            # Ensure the object's state is updated to "open"
            game_state.set_object_state(target_object_id, "is_open", True)
            return [{"key": response_key, "data": response_data}]
        # TODO: Add specific handling for "readable" if needed, e.g., ALREADY_OPEN_READABLE
        else: # For non-storage openables
            return [{ "key": "ALREADY_OPEN_GENERIC", "data": {"target_name": target_object_name} }]

    # If unlocked and closed, proceed to open
    game_state.set_object_state(target_object_id, "is_open", True)
    obj_state = game_state.get_object_state(target_object_id) # Re-fetch state after modification
    logger.info(f"[handle_open] Successfully opened '{target_object_name}'. State: {obj_state}")
    
    if obj_props.get("is_storage", False):
        items_in_container_data = []
        # Correctly access 'contains' from the obj_state dictionary
        for item_ref in obj_state.get("contains", []) or []:
            item_id_in_container = None
            if hasattr(item_ref, 'id'): # Handle if item_ref is an ObjectInstance or similar
                item_id_in_container = item_ref.id
            elif isinstance(item_ref, dict):
                item_id_in_container = item_ref.get('id')
            else: # Assuming item_ref is a simple string ID if not a dict or object with .id
                item_id_in_container = str(item_ref)

            if not item_id_in_container:
                logger.warning(f"[handle_open] Found an item_ref in container '{target_object_id}' without a valid ID: {item_ref}")
                continue

            item_data_in_container = game_state.get_object_by_id(item_id_in_container)
            if item_data_in_container:
                items_in_container_data.append(item_data_in_container)
                # Make items visible (if they weren't already)
                game_state.set_object_state(item_id_in_container, "is_visible", True)

        if items_in_container_data:
            # Format the list of item names for the message
            # Correctly extract names from the dictionaries in items_in_container_data
            item_names = [item_data.get("name", "an unknown item") for item_data in items_in_container_data]
            item_list_str = ", ".join(item_names) if item_names else "nothing special"
            logger.info(f"[handle_open] '{target_object_name}' contains: {item_list_str}")
            # Ensure the key is "item_list_str" for consistency
            return [{ "key": "OPEN_SUCCESS_CONTENTS", "data": {"container_name": target_object_name, "item_list_str": item_list_str} }]
        else:
            logger.info(f"[handle_open] '{target_object_name}' is empty.")
            return [{ "key": "OPEN_SUCCESS_EMPTY", "data": {"container_name": target_object_name} }]
    # TODO: Add specific success message for "readable" if "open book" should have unique text, e.g., OPEN_SUCCESS_READABLE_GENERIC
    else: # For non-storage openables
        return [{ "key": "OPEN_SUCCESS_GENERIC", "data": {"target_name": target_object_name} }]

def handle_close(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict[str, Any]]:
    """Handles the CLOSE command intent."""
    target_object_id = parsed_intent.target_object_id
    target_object_name = parsed_intent.target or target_object_id

    logger.debug(f"[handle_close] Attempting to close: ID='{target_object_id}', Name='{target_object_name}'")

    if not target_object_id:
        logger.warning("[handle_close] No target object ID identified by parser.")
        return [{ "key": "CLOSE_NO_TARGET", "data": {} }]

    obj_data = game_state.get_object_by_id(target_object_id)
    if not obj_data:
        logger.warning(f"[handle_close] Object data not found for ID: {target_object_id}")
        return [{ "key": "CLOSE_TARGET_NOT_FOUND", "data": {"target_name": target_object_name or "something"} }]

    obj_state = game_state.get_object_state(target_object_id)
    obj_display_name = obj_data.get("name", target_object_id)
    obj_properties = obj_data.get("properties", {})

    if not obj_properties.get("is_openable_closable"):
        logger.info(f"[handle_close] Target '{obj_display_name}' cannot be closed.")
        return [{ "key": "CLOSE_FAIL_NOT_CLOSABLE", "data": {"target_name": obj_display_name} }]
    
    base_is_open = obj_data.get('is_open', False) 
    is_open = obj_state.get("is_open", base_is_open)

    if not is_open:
        logger.info(f"[handle_close] Target '{obj_display_name}' is already closed.")
        return [{ "key": "ALREADY_CLOSED", "data": {"target_name": obj_display_name} }]

    game_state.set_object_state(target_object_id, "is_open", False)
    # If storage, hide its contents from general visibility
    try:
        if obj_properties.get("is_storage", False):
            for item_ref in (obj_state.get("contains", []) or []):
                item_id = None
                if isinstance(item_ref, str):
                    item_id = item_ref
                elif isinstance(item_ref, dict):
                    item_id = item_ref.get('id')
                if item_id:
                    game_state.set_object_state(item_id, "is_visible", False)
    except Exception:
        pass
    logger.info(f"[handle_close] Successfully closed '{obj_display_name}'. State: {game_state.get_object_state(target_object_id)}")
    return [{ "key": "CLOSE_SUCCESS", "data": {"target_name": obj_display_name} }] 