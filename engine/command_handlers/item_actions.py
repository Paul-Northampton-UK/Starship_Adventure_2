"""Command handlers for taking, dropping, and putting items."""

import logging
from typing import Tuple, Dict
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name
from ..schemas import Object # Import the Object schema

def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the TAKE command intent. Returns (key, kwargs) tuple."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_take] Handling TAKE for target name: '{target_object_name}'")

    if not target_object_name:
        # TODO: Add take_fail_no_target key to responses.yaml
        return ("invalid_command", {}) # Placeholder

    # Check if hands are free *first*
    if game_state.hand_slot is not None:
        held_item_name = game_state._get_object_name(game_state.hand_slot)
        return ("take_fail_hands_full", {"held_item_name": held_item_name, "item_name": target_object_name})

    # Find the object in the location
    found_object_id = game_state._find_object_id_by_name_in_location(target_object_name)
    if not found_object_id:
        logging.debug(f"[handle_take] No object ID found for name '{target_object_name}'.")
        return ("take_fail_no_item", {"item_name": target_object_name})

    # Get object data to check its properties
    object_data = game_state.objects_data.get(found_object_id)
    if not object_data:
        logging.error(f"[handle_take] Found object ID '{found_object_id}' but no data exists in objects_data!")
        return ("error_internal", {"action": "take data missing"})

    # Use dictionary access
    is_plural = object_data.get('is_plural', False)
    item_name = object_data.get('name', 'unknown object') # Use .get() for safety

    # Call GameState.take_object 
    logging.debug(f"[handle_take] Calling GameState.take_object with ID: '{found_object_id}'")
    result_message = game_state.take_object(found_object_id)
    logging.debug(f"[handle_take] take_object returned: {result_message}")

    # Map GameState message to response key/kwargs
    if "You take the" in result_message:
        key = "take_success_plural" if is_plural else "take_success_singular"
        return (key, {"item_name": item_name})
    elif "cannot take" in result_message:
        # Determine if it's just not takeable or needs a specific action (e.g., unlock)
        # For now, use a generic non-takeable key
        key = "take_fail_not_takeable_plural" if is_plural else "take_fail_not_takeable_singular"
        return (key, {"item_name": item_name})
    elif "hands are full" in result_message: # Should be caught above, but as fallback
        held_item_id = game_state.hand_slot
        held_item_name = game_state._get_object_name(held_item_id) if held_item_id else "something"
        return ("take_fail_hands_full", {"held_item_name": held_item_name, "item_name": target_object_name})
    elif "seems stuck" in result_message:
        return ("error_internal", {"action": "take stuck"})
    else: # Default for unexpected messages from take_object
        logging.warning(f"Unexpected message from take_object: {result_message}")
        return ("error_internal", {"action": "take"})


def handle_drop(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the DROP command intent. Returns (key, kwargs) tuple."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_drop] Handling DROP for target name: '{target_object_name}'")

    if not target_object_name:
        # TODO: Add drop_fail_no_target key to responses.yaml
        return ("invalid_command", {}) # Placeholder

    held_object_id = game_state.hand_slot
    if held_object_id is None:
        # Check if they named an item they *possess* but aren't holding
        inv_id = game_state._find_object_id_by_name_in_inventory(target_object_name)
        worn_id = game_state._find_object_id_by_name_worn(target_object_name)
        if inv_id or worn_id:
             # TODO: Add drop_fail_possess_not_holding key to responses.yaml
             return("drop_fail_not_holding", {"item_name": target_object_name or "anything"})
        else:
             # TODO: Add drop_fail_not_holding_anything key to responses.yaml
             return ("drop_fail_not_holding", {"item_name": "anything"})

    # Get data for the item being held
    held_object_data = game_state.objects_data.get(held_object_id)
    if not held_object_data:
        logging.error(f"[handle_drop] Holding object ID '{held_object_id}' but no data exists in objects_data!")
        return ("error_internal", {"action": "drop data missing"})

    # Use dictionary access
    is_plural = held_object_data.get('is_plural', False)
    held_item_name = held_object_data.get('name', 'unknown object')

    # Use item_matches_name helper to check if the held item matches the target name
    if not item_matches_name(game_state, held_object_id, target_object_name):
         # TODO: Add drop_fail_target_mismatch key to responses.yaml
         # The message should maybe state what you *are* holding vs what you tried to drop
         key = "drop_fail_target_mismatch_plural" if is_plural else "drop_fail_target_mismatch_singular"
         return (key, {"item_name": target_object_name, "held_item_name": held_item_name})

    # If it matches, proceed to drop the item in hand
    logging.debug(f"[handle_drop] Calling GameState.drop_object with ID: '{held_object_id}'")
    result_dict = game_state.drop_object(held_object_id) # Returns dict now
    logging.debug(f"[handle_drop] drop_object returned: {result_dict}")

    success = result_dict.get("success", False)

    if success:
        key = "drop_success_plural" if is_plural else "drop_success_singular"
        return (key, {"item_name": held_item_name})
    else:
        return ("error_internal", {"action": "drop failed"})


def handle_put(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the PUT command intent (e.g., put item in container). Returns (key, kwargs)."""
    item_to_put_name = parsed_intent.target
    container_name = parsed_intent.secondary_target
    preposition = parsed_intent.preposition
    logging.debug(f"[handle_put] Item: '{item_to_put_name}', Prep: '{preposition}', Container: '{container_name}'")

    # --- Validation --- 
    if not item_to_put_name or not container_name or not preposition:
        logging.warning("[handle_put] Missing item, container, or preposition in parsed intent.")
        # TODO: Add put_fail_incomplete key
        return ("invalid_command", {}) # Generic fallback
    
    # Check if player is holding the item
    held_item_id = game_state.hand_slot
    if not held_item_id:
        # TODO: Add put_fail_not_holding_anything key
        return ("drop_fail_not_holding", {"item_name": "anything"}) # Reuse drop failure key?
        
    # Check if the held item matches the name they tried to put
    if not item_matches_name(game_state, held_item_id, item_to_put_name):
        held_item_data = game_state.get_object_by_id(held_item_id)
        held_item_display_name = held_item_data.get('name', held_item_id) if held_item_data else held_item_id
        # TODO: Add put_fail_holding_wrong_item key
        return ("drop_fail_target_mismatch_singular", {"item_name": item_to_put_name, "held_item_name": held_item_display_name}) # Reuse drop key?
        
    # Find the target container using the new comprehensive search
    container_id = game_state.find_container_id_by_name(container_name)
    if not container_id:
        # TODO: Add put_fail_container_not_found key
        return ("look_fail_not_found", {"item_name": container_name}) # Reuse look key?
        
    # Get container data
    container_data = game_state.get_object_by_id(container_id)
    if not container_data:
        logging.error(f"[handle_put] Container ID '{container_id}' found but data missing.")
        return ("error_internal", {"action": "put container data"})
        
    # Check if it's actually a container
    if not container_data.get('properties', {}).get('is_storage'):
        # TODO: Add put_fail_not_a_container key
        return ("store_fail_not_container", {"container_name": container_name}) # Reuse store key?
        
    # Check if the container is open (using object_states)
    container_state = game_state.get_object_state(container_id) or {}
    if not container_state.get('is_open', True): # Default to True if state not set?
        # TODO: Add put_fail_container_closed key
        return ("store_fail_container_closed", {"container_name": container_name}) # Reuse store key?
        
    # TODO: Implement container capacity checks based on:
    #       1. Size (Primary): Sum of item sizes <= container size capacity.
    #       2. Weight (Secondary, for movable containers): Sum of item weights <= container weight capacity.
    #       3. Item Count (Optional/Alternative): Number of items <= container item count capacity (current field).
    # capacity = container_data.get('properties', {}).get('storage_capacity')
    # current_contents = container_data.get('storage_contents', []) # This is default, need current state
    # current_contents_state = game_state.get_object_state(container_id).get('storage_contents', []) ?
    # Need a reliable way to get current contents and check capacity...

    # --- Execution --- 
    # For now, assume success if validations pass
    logging.info(f"Putting item '{held_item_id}' into container '{container_id}'")
    
    # 1. Add item to container's state
    current_contents = list(container_state.get('storage_contents', [])) # Get current or empty list
    if held_item_id not in current_contents:
        current_contents.append(held_item_id)
    container_state['storage_contents'] = current_contents
    game_state.set_object_state(container_id, container_state)
    
    # 2. Remove item from player's hand
    game_state.hand_slot = None
    
    # --- Response --- 
    held_item_data = game_state.get_object_by_id(held_item_id) # Re-get data for name
    held_item_display_name = held_item_data.get('name', held_item_id) if held_item_data else held_item_id
    container_display_name = container_data.get('name', container_id)
    
    # TODO: Add put_success key
    return ("store_success", {"item_name": held_item_display_name, "container_name": container_display_name}) # Reuse store key? 