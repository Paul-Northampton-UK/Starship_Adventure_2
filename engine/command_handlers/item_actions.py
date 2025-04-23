"""Command handlers for taking, dropping, and putting items."""

import logging
from typing import Tuple, Dict, List
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name
from ..schemas import Object # Import the Object schema

def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the TAKE command intent. Returns List[Dict]."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_take] Handling TAKE for target name: '{target_object_name}'")

    if not target_object_name:
        # TODO: Add take_fail_no_target key to responses.yaml
        return [{'key': "take_fail_no_target", 'data': {}}]

    # Check if hands are free *first*
    if len(game_state.hand_slot) >= 2:
        held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
        return [{'key': "take_fail_hands_full", 'data': {"held_item_name": held_items_str, "item_name": target_object_name}}]

    # Find the object in the location
    found_object_id = game_state.find_object_id_by_name_in_location(target_object_name)
    if not found_object_id:
        logging.debug(f"[handle_take] No object ID found for name '{target_object_name}'.")
        return [{'key': "take_fail_no_item", 'data': {"item_name": target_object_name}}]

    # Get object data to check its properties
    object_data = game_state.get_object_by_id(found_object_id)
    if not object_data:
        logging.error(f"[handle_take] Found object ID '{found_object_id}' but no data exists in objects_data!")
        return [{'key': "error_internal", 'data': {"action": "take data missing"}}]

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
        return [{'key': key, 'data': {"item_name": item_name}}]
    elif "cannot take" in result_message:
        # Determine if it's just not takeable or needs a specific action (e.g., unlock)
        # For now, use a generic non-takeable key
        key = "take_fail_not_takeable_plural" if is_plural else "take_fail_not_takeable_singular"
        return [{'key': key, 'data': {"item_name": item_name}}]
    elif "hands are full" in result_message: # Should be caught above, but as fallback
        held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
        return [{'key': "take_fail_hands_full", 'data': {"held_item_name": held_items_str, "item_name": target_object_name}}]
    elif "seems stuck" in result_message:
        return [{'key': "error_internal", 'data': {"action": "take stuck"}}]
    else: # Default for unexpected messages from take_object
        logging.warning(f"Unexpected message from take_object: {result_message}")
        return [{'key': "error_internal", 'data': {"action": "take unknown"}}]


def handle_drop(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the DROP command intent. Returns List[Dict]."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_drop] Handling DROP for target name: '{target_object_name}'")

    if not target_object_name:
        # If holding only one item, maybe assume they mean that one?
        if len(game_state.hand_slot) == 1:
             target_object_name = game_state._get_object_name(game_state.hand_slot[0])
             logging.debug(f"[handle_drop] No target specified, assuming the only held item: '{target_object_name}'")
        else:
            # TODO: Add drop_fail_no_target key
            # TODO: Potentially list held items in the response?
            return [{'key': "drop_fail_no_target_specified", 'data': {}}]

    if not game_state.hand_slot: # Check if hands are empty
        # TODO: Check inventory/worn and provide possess_not_holding message?
        return [{'key': "drop_fail_not_holding", 'data': {"item_name": "anything"}}]

    # Find which item in hand matches the target name
    object_id_to_drop = None
    match_count = 0
    held_item_names = [] # For potential ambiguity message
    for held_id in game_state.hand_slot:
        held_item_names.append(game_state._get_object_name(held_id) or held_id)
        if item_matches_name(game_state, held_id, target_object_name):
            object_id_to_drop = held_id
            match_count += 1
            
    # Handle ambiguity or no match
    if match_count > 1:
        # TODO: Add drop_fail_ambiguous key
        return [{'key': "drop_fail_ambiguous", 'data': {"item_name": target_object_name, "held_items": ", ".join(held_item_names)}}]
    elif match_count == 0:
        # TODO: Add drop_fail_target_not_held key
        return [{'key': "drop_fail_not_holding", 'data': {"item_name": target_object_name}}]
        
    # Exactly one match found, proceed to drop
    held_object_data = game_state.get_object_by_id(object_id_to_drop)
    if not held_object_data:
        logging.error(f"[handle_drop] Matched object ID '{object_id_to_drop}' but no data exists!")
        return [{'key': "error_internal", 'data': {"action": "drop data missing"}}]
        
    is_plural = held_object_data.get('is_plural', False)
    held_item_name = held_object_data.get('name', 'unknown object')

    logging.debug(f"[handle_drop] Calling GameState.drop_object with ID: '{object_id_to_drop}'")
    result_dict = game_state.drop_object(object_id_to_drop)
    logging.debug(f"[handle_drop] drop_object returned: {result_dict}")

    success = result_dict.get("success", False)

    if success:
        key = "drop_success_plural" if is_plural else "drop_success_singular"
        return [{'key': key, 'data': {"item_name": held_item_name}}]
    else:
        # Use message from drop_object if available, otherwise generic error
        error_msg = result_dict.get("message", "drop failed internally") 
        logging.warning(f"drop_object indicated failure: {error_msg}")
        
        # Map specific failure messages from GameState to user-facing keys
        if "not holding" in error_msg.lower():
            return [{'key': "drop_fail_not_holding", 'data': {"item_name": target_object_name}}] # Use the name user typed
        # Add other specific mappings here if drop_object can fail in other ways
        
        # Fallback to generic internal error if message is unrecognized
        return [{'key': "error_internal", 'data': {"action": f"drop failed: {error_msg}"}}]


def handle_put(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the PUT command intent (e.g., put item in container). Returns List[Dict]."""
    item_to_put_name = parsed_intent.target
    container_name = parsed_intent.secondary_target
    preposition = parsed_intent.preposition
    logging.debug(f"[handle_put] Item: '{item_to_put_name}', Prep: '{preposition}', Container: '{container_name}'")

    # --- Validation --- 
    if not item_to_put_name or not container_name or not preposition:
        logging.warning("[handle_put] Missing item, container, or preposition in parsed intent.")
        # TODO: Add put_fail_incomplete key
        return [{'key': "invalid_command", 'data': {}}] # Generic fallback
        
    # --- Find the specific item in hand ---
    if not game_state.hand_slot: # Check if hands are empty
        return [{'key': "put_fail_not_holding_anything", 'data': {"item_name": item_to_put_name}}] # Need response key

    object_id_to_put = None
    match_count = 0
    held_item_names = [] # For potential ambiguity message
    for held_id in game_state.hand_slot:
        held_item_names.append(game_state._get_object_name(held_id) or held_id)
        if item_matches_name(game_state, held_id, item_to_put_name):
            object_id_to_put = held_id
            match_count += 1
            
    # Handle ambiguity or no match in hands
    if match_count > 1:
        # TODO: Add put_fail_ambiguous key
        return [{'key': "put_fail_ambiguous", 'data': {"item_name": item_to_put_name, "held_items": ", ".join(held_item_names)}}]
    elif match_count == 0:
        # TODO: Add put_fail_target_not_held key
        return [{'key': "put_fail_not_holding", 'data': {"item_name": item_to_put_name}}]
    
    # --- Found the item to put (object_id_to_put) --- 
        
    # Find the target container using the new comprehensive search
    container_id = game_state.find_container_id_by_name(container_name)
    
    # --- ADDED: Check for self-insertion --- 
    if object_id_to_put == container_id:
        item_data = game_state.get_object_by_id(object_id_to_put)
        item_name = item_data.get('name', 'item') if item_data else 'item' # Get name for message
        return [{'key': "put_fail_self_insertion", 'data': {"item_name": item_name}}]
    # --- END ADDED ---
        
    if not container_id:
        # TODO: Add put_fail_container_not_found key
        return [{'key': "look_fail_not_found", 'data': {"item_name": container_name}}] # Reuse look key?
        
    # Get container data
    container_data = game_state.get_object_by_id(container_id)
    if not container_data:
        logging.error(f"[handle_put] Container ID '{container_id}' found but data missing.")
        return [{'key': "error_internal", 'data': {"action": "put container data"}}]
        
    # Check if it's actually a container
    if not container_data.get('properties', {}).get('is_storage'):
        # TODO: Add put_fail_not_a_container key
        return [{'key': "store_fail_not_container", 'data': {"container_name": container_name}}] # Reuse store key?
        
    # Check if the container is open (using object_states)
    container_state = game_state.get_object_state(container_id) or {}
    if not container_state.get('is_open', True): # Default to True if state not set?
        # TODO: Add put_fail_container_closed key
        return [{'key': "store_fail_container_closed", 'data': {"container_name": container_name}}] # Reuse store key?
        
    # TODO: Implement container capacity checks (Size, Weight, Count)
    # ... capacity check logic goes here ...

    # --- Execution --- 
    logging.info(f"Putting item '{object_id_to_put}' into container '{container_id}'")
    
    # 1. Add item to container's state
    # Ensure container_state is a mutable dictionary if it wasn't already
    if not isinstance(container_state, dict): container_state = {} # Safety check
    # Use 'contains' key for consistency with retrieval logic
    current_contents = list(container_state.get('contains', [])) # Get current or empty list using 'contains'
    if object_id_to_put not in current_contents:
        current_contents.append(object_id_to_put)
    container_state['contains'] = current_contents # Store under 'contains'
    game_state.set_object_state(container_id, container_state)
    
    # 2. Remove item from player's hand list
    game_state.hand_slot.remove(object_id_to_put)
    
    # --- Response --- 
    # Get data for the item that was actually put
    held_item_data = game_state.get_object_by_id(object_id_to_put)
    if not held_item_data:
        logging.error(f"[handle_put] Data missing for successfully put item '{object_id_to_put}'!")
        return [{'key': "error_internal", 'data': {"action": "put success data missing"}}] 
        
    held_item_display_name = held_item_data.get('name', object_id_to_put)
    is_plural = held_item_data.get('is_plural', False)
    container_display_name = container_data.get('name', container_id)
    
    # Use specific put_success keys based on plural status
    key = "put_success_plural" if is_plural else "put_success_singular"
    kwargs = {"item_name": held_item_display_name, "container_name": container_display_name}
    logging.debug(f"[handle_put] Returning success: key='{key}', kwargs={kwargs}")
    return [{'key': key, 'data': kwargs}] 

def handle_take_from(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles taking an item FROM a container."""
    item_to_take_name = parsed_intent.target
    container_name = parsed_intent.secondary_target
    logging.debug(f"[handle_take_from] Item: '{item_to_take_name}', Container: '{container_name}'")

    # --- Validation ---
    if not item_to_take_name or not container_name:
        logging.warning("[handle_take_from] Missing item or container in parsed intent.")
        # TODO: Add take_from_fail_incomplete key
        return [{'key': "invalid_command", 'data': {}}] 

    # --- Find the container ---
    container_id = game_state.find_container_id_by_name(container_name)
    if not container_id:
        return [{'key': "take_from_fail_container_not_found", 'data': {"container_name": container_name}}]
        
    container_data = game_state.get_object_by_id(container_id)
    container_display_name = container_data.get('name', container_id) if container_data else container_id
    
    # Check if it's actually storage (should be caught by find_container... but double check)
    if not container_data or not container_data.get('properties', {}).get('is_storage'):
         logging.warning(f"[handle_take_from] Target '{container_name}' (ID: {container_id}) is not storage.")
         return [{'key': "take_from_fail_not_container", 'data': {"container_name": container_display_name}}] # Need new key
         
    # --- Check if container is open (if applicable) ---
    container_state = game_state.get_object_state(container_id) or {}
    # TODO: Check 'is_open' property? Assumes open for now if not specified.
    # if not container_state.get('is_open', True):
    #     return ("take_from_fail_container_closed", {"container_name": container_display_name})

    # --- Find the specific item within the container ---
    contents = container_state.get('contains', [])
    item_id_to_take = None
    item_name_actual = item_to_take_name # Fallback
    is_plural = False # Default
    
    if not contents:
        return [{'key': "take_from_fail_not_in_container", 'data': {"item_name": item_to_take_name, "container_name": container_display_name}}]
        
    found_match = None
    match_count = 0
    for item_id in contents:
        if item_matches_name(game_state, item_id, item_to_take_name):
             found_match = item_id
             match_count += 1
             # Get actual name and plural status for the response
             item_data = game_state.get_object_by_id(item_id)
             if item_data:
                 item_name_actual = item_data.get('name', item_id)
                 is_plural = item_data.get('is_plural', False)
                 
    if match_count > 1:
         # TODO: Add take_from_fail_ambiguous key
         return [{'key': "take_from_fail_ambiguous", 'data': {"item_name": item_to_take_name, "container_name": container_display_name}}]
    elif match_count == 0:
         return [{'key': "take_from_fail_not_in_container", 'data': {"item_name": item_to_take_name, "container_name": container_display_name}}]
    else:
        item_id_to_take = found_match

    # --- Check hand capacity ---
    if len(game_state.hand_slot) >= 2:
        held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
        # TODO: Add take_from_fail_hands_full key
        return [{'key': "take_fail_hands_full", 'data': {"held_item_name": held_items_str, "item_name": item_name_actual, "container_name": container_display_name}}]

    # --- Execution --- 
    logging.info(f"Taking item '{item_id_to_take}' from container '{container_id}'")
    
    # 1. Remove item from container's state (safer approach)
    # Retrieve the state again to ensure we have the latest
    current_container_state = game_state.get_object_state(container_id) or {}
    current_contents = current_container_state.get('contains', [])
    
    if item_id_to_take in current_contents:
        # Create a new list excluding the item
        new_contents = [item for item in current_contents if item != item_id_to_take]
        # Update the state dictionary with the new list
        current_container_state['contains'] = new_contents
        # Save the updated state
        game_state.set_object_state(container_id, current_container_state)
        logging.debug(f"Successfully updated container '{container_id}' state. New contents: {new_contents}")
    else:
        # This should not happen if the item was found earlier, but handle defensively
        logging.error(f"[handle_take_from] Item '{item_id_to_take}' was not in container '{container_id}' contents during removal attempt.")
        return [{'key': "error_internal", 'data': {"action": "take_from consistency error"}}]
        
    # 2. Add item to player's hand list
    game_state.hand_slot.append(item_id_to_take)
    
    # --- Response ---
    key = "take_from_success_plural" if is_plural else "take_from_success_singular"
    kwargs = {"item_name": item_name_actual, "container_name": container_display_name}
    logging.debug(f"[handle_take_from] Returning success: key='{key}', kwargs={kwargs}")
    return [{'key': key, 'data': kwargs}] 