"""Command handlers for taking, dropping, and putting items."""

import logging
from typing import Tuple, Dict, List, Optional
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name
from ..schemas import Object # Import the Object schema

def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the TAKE command intent. Returns List[Dict]."""
    target_object_name = parsed_intent.target
    target_object_id_from_parser = parsed_intent.target_object_id

    logging.debug(f"[handle_take] Attempting to TAKE: Name='{target_object_name}', ParserID='{target_object_id_from_parser}'")

    if not target_object_name and not target_object_id_from_parser:
        return [{'key': "take_fail_no_target", 'data': {}}]

    if len(game_state.hand_slot) >= 2:
        held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
        return [{'key': "take_fail_hands_full", 'data': {"held_item_name": held_items_str, "item_name": target_object_name or "the item"}}]

    found_object_id: Optional[str] = None
    source_description: str = "" # For messages: "in the room", "in the {container_name}"

    # 1. Identify Candidate Object ID:
    #    - If parser gave an ID, use it.
    #    - Else, try to find an object by name in the current location (room or open containers).
    candidate_object_id: Optional[str] = None

    current_room_id = game_state.current_room_id
    # current_area_id = game_state.current_area_id # Not strictly needed for 'take' as items are in rooms/containers

    if target_object_id_from_parser:
        logging.debug(f"[handle_take] Parser provided candidate ID: {target_object_id_from_parser}")
        # Validate if this object is actually accessible (visible in room or visible in an open container)
        
        # Check if it's loose in the room and visible
        visible_loose_objects = game_state._get_all_object_ids_in_current_location(
            visible_only=True
        )
        if target_object_id_from_parser in visible_loose_objects:
            candidate_object_id = target_object_id_from_parser
            source_description = "in the room"
            logging.debug(f"[handle_take] Parser ID {target_object_id_from_parser} confirmed loose and visible in room.")
        else:
            # Check if it's in an open, visible container in the current room
            # MODIFICATION: Removed room_id=current_room_id
            open_visible_containers = game_state.get_containers_in_location(
                must_be_open=True, must_be_visible=True
            )
            for container_id in open_visible_containers:
                container_state = game_state.get_object_state(container_id)
                if container_state and target_object_id_from_parser in container_state.get("contains", []):
                    # Further check: is the item *itself* visible? (e.g. not hidden inside the container by some other property)
                    # For now, if it's in 'contains' of an open container, we assume it's takeable.
                    # This could be expanded if items within containers can have their own visibility state.
                    item_state_in_container = game_state.get_object_state(target_object_id_from_parser)
                    if item_state_in_container and item_state_in_container.get("is_visible", True): # Default to true if no specific visibility
                        candidate_object_id = target_object_id_from_parser
                        container_name = game_state._get_object_name(container_id) or "container"
                        source_description = f"in the {container_name}"
                        logging.debug(f"[handle_take] Parser ID {target_object_id_from_parser} confirmed in open container {container_id}.")
                        break
            if not candidate_object_id:
                logging.debug(f"[handle_take] Parser ID {target_object_id_from_parser} is not loose in room or in an accessible container.")
    
    if not candidate_object_id and target_object_name: # If parser ID didn't work out or wasn't provided, try by name
        logging.debug(f"[handle_take] No valid candidate ID from parser, or no parser ID. Searching by name: '{target_object_name}'")
        # Try to find by name, prioritizing loose items, then items in open containers.
        
        all_loc_objects = game_state._get_all_object_ids_in_current_location(
            visible_only=True
        )
        found_ids_by_name_loose: List[str] = []
        if target_object_name: # Ensure there's a name to search for
            for obj_id_in_loc in all_loc_objects:
                if item_matches_name(game_state, obj_id_in_loc, target_object_name):
                    found_ids_by_name_loose.append(obj_id_in_loc)
        
        if found_ids_by_name_loose:
            if len(found_ids_by_name_loose) == 1:
                candidate_object_id = found_ids_by_name_loose[0]
                source_description = "in the room"
                logging.debug(f"[handle_take] Found unique loose item by name: {candidate_object_id}")

    if not candidate_object_id:
        logging.debug(f"[handle_take] No candidate object ID found for '{target_object_name or target_object_id_from_parser}'.")
        return [{'key': "take_fail_no_item", 'data': {'item_name': target_object_name or "the item"}}]

    # --- Stage 2: Validate accessibility and 'is_takeable' property of the candidate_object_id ---
    logging.debug(f"[handle_take] Validating candidate ID: {candidate_object_id}")
    obj_data_to_take = game_state.get_object_by_id(candidate_object_id)

    if not obj_data_to_take:
        logging.error(f"[handle_take] Data not found for candidate ID {candidate_object_id} after search!")
        return [{'key': "error_internal", 'data': {'action': "take data missing for candidate"}}]

    # Check 'is_takeable' property first
    if not obj_data_to_take.get("properties", {}).get("is_takeable", False):
        item_name_for_msg = obj_data_to_take.get("name", target_object_name or "that item")
        is_plural_for_msg = obj_data_to_take.get("is_plural", False)
        key = "take_fail_not_takeable_plural" if is_plural_for_msg else "take_fail_not_takeable_singular"
        logging.debug(f"[handle_take] Candidate '{item_name_for_msg}' (ID: {candidate_object_id}) is not 'is_takeable'.")
        return [{'key': key, 'data': {"item_name": item_name_for_msg}}]

    # Now, check ACCESSIBILITY: Is it visible loose OR visible in an open container?
    is_accessible = False
    
    # Check if loose and visible
    obj_state_to_take = game_state.get_object_state(candidate_object_id)
    if obj_state_to_take.get("is_visible", False): # Check its own visibility state
        # Is it part of the room's general visible items (not inside a container)?
        # We can check if it's one of the IDs returned by find_object_id_by_name_in_location
        # when specifically searching for THIS candidate_object_id by its name.
        # Or, more directly, check if it's in _get_all_object_ids_in_current_location (visible)
        # AND not inside any container (this is implicitly handled by game_state.take_object later)

        # A simpler check: if its state says it's visible, and it's not inside a *closed* container,
        # it's potentially accessible from the room. game_state.take_object will verify its exact source.
        # Let's assume for now if obj_state_to_take.is_visible is true, it's considered accessible from the room level
        # UNLESS it's inside a closed container.

        # More robust check: Iterate all visible objects in location. Is our candidate_object_id one of them?
        visible_loose_objects = game_state._get_all_object_ids_in_current_location(
            visible_only=True
        )
        if candidate_object_id in visible_loose_objects:
            # Further check if it's *not* inside any known container (or if it is, that container is open)
            # This check is complex here. Let's rely on GameState.take_object's refined logic for source.
            # The main point here is that the object ITSELF must be 'is_visible: True' in its state.
            is_accessible = True
            logging.debug(f"[handle_take] Candidate '{candidate_object_id}' is visible in its own state.")


    # Check if inside an open, visible container AND visible itself
    if not is_accessible:
        all_loc_objects = game_state._get_all_object_ids_in_current_location(
            visible_only=True # Only care about visible containers
        )
        for loc_obj_id_container_check in all_loc_objects:
            loc_obj_data_container_check = game_state.get_object_by_id(loc_obj_id_container_check)
            loc_obj_state_container_check = game_state.get_object_state(loc_obj_id_container_check)
            if (loc_obj_data_container_check and loc_obj_data_container_check.get("properties", {}).get("is_storage") and
                    loc_obj_state_container_check and loc_obj_state_container_check.get("is_open") and 
                    loc_obj_state_container_check.get("is_visible")): # Container itself is open and visible
                
                if candidate_object_id in loc_obj_state_container_check.get("contains", []):
                    # The item is in this open, visible container. Ensure the item itself is visible.
                    if obj_state_to_take.get("is_visible", False): # Already fetched obj_state_to_take
                        is_accessible = True
                        logging.debug(f"[handle_take] Candidate '{candidate_object_id}' found accessible inside open container '{loc_obj_data_container_check.get('name')}'.")
                        break 
    
    if not is_accessible:
        logging.debug(f"[handle_take] Candidate '{candidate_object_id}' ({obj_data_to_take.get('name')}) was identified but is not accessible (not visible loose, or not in an open & visible container).")
        return [{'key': "take_fail_no_item", 'data': {'item_name': obj_data_to_take.get('name', target_object_name or "the item")}}]

    # If we reach here, candidate_object_id is set, 'is_takeable' property is true, and it's accessible.
    found_object_id = candidate_object_id
    logging.info(f"[handle_take] Confirmed takeable and accessible object: '{obj_data_to_take.get('name')}' (ID: {found_object_id}).")

    # --- Stage 3: Perform the take action ---
    is_plural = obj_data_to_take.get('is_plural', False)
    item_name_for_response = obj_data_to_take.get('name', 'unknown object')

    logging.debug(f"[handle_take] Calling GameState.take_object with ID: '{found_object_id}'")
    result_message = game_state.take_object(found_object_id) # GameState.take_object handles removal from source
    logging.debug(f"[handle_take] take_object returned: {result_message}")

    if "You take the" in result_message:
        key = "take_success_plural" if is_plural else "take_success_singular"
        return [{'key': key, 'data': {"item_name": item_name_for_response}}]
    elif "cannot take that" in result_message: 
        # This case might be redundant if 'is_takeable' property check above is exhaustive,
        # but GameState.take_object might have other reasons (e.g. too heavy, bolted down if we add such logic)
        key = "take_fail_not_takeable_plural" if is_plural else "take_fail_not_takeable_singular"
        return [{'key': key, 'data': {"item_name": item_name_for_response}}]
    else:
        # Fallback for other messages from take_object
        logging.warning(f"Unexpected message from take_object: {result_message}. Using it directly.")
        return [{'key': "generic_message_from_action", 'data': {"message": result_message}}]


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
    game_state.set_object_state(container_id, "contains", current_contents) # Corrected call
    
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
        # current_container_state['contains'] = new_contents # No longer needed to modify this local dict directly for the set_object_state call
        # Save the updated state
        game_state.set_object_state(container_id, 'contains', new_contents) # CORRECTED CALL
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