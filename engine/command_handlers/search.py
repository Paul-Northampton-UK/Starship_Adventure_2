"""Command handler for searching locations and objects."""

import logging
from typing import Tuple, Dict, List
from ..game_state import GameState
from ..command_defs import ParsedIntent
import random

def handle_search(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the SEARCH command intent.
    
    Allows searching the current location or a specific object within it
    to potentially find hidden items or trigger events.
    """
    target_name = parsed_intent.target
    logging.debug(f"[handle_search] Handling SEARCH for target: '{target_name}'")

    if not target_name:
        # Search the current location (room/area)
        logging.debug("[handle_search] No target specified, searching current location.")
        room_id, area_id = game_state.get_current_location()
        location_id = area_id if area_id else room_id
        location_data = None
        if area_id:
            room_data = game_state.rooms_data.get(room_id)
            if room_data and isinstance(room_data.get("areas"), list):
                 for area in room_data["areas"]:
                     if isinstance(area, dict) and area.get("area_id") == area_id:
                         location_data = area
                         break
        else:
            location_data = game_state.rooms_data.get(room_id)
            
        if not location_data:
            logging.error(f"Could not find location data for {location_id} to search.")
            return [{'key': "error_internal", 'data': {'action': "search location data"}}]

        # Check for hidden items in the location
        hidden_items = location_data.get("hidden_objects", []) # Assuming hidden_objects key
        if hidden_items:
            found_item_id = random.choice(hidden_items) # Simple: find one random item
            # TODO: Add difficulty checks, perception skills, etc.
            
            # Add item to location's objects_present list
            # TODO: Need a GameState method to add item to location state, 
            #       similar to drop, but without requiring player to hold it.
            # For now, let's just reveal it in the message.
            item_data = game_state.get_object_by_id(found_item_id)
            item_name = item_data.get("name", found_item_id) if item_data else found_item_id
            
            # TODO: Remove the item from hidden_objects once found?
            
            # Return success message revealing the item
            # TODO: Need search_success_hidden_item_found key in responses.yaml
            return [{'key': "search_success_hidden_item_found", 'data': {"target_name": location_id, "item_name": item_name}}]
        else:
            # Nothing hidden found in the location
            # TODO: Need search_fail_nothing_hidden key in responses.yaml
            return [{'key': "search_fail_nothing_hidden", 'data': {"target_name": location_id}}]
            
    else:
        # Search a specific object
        logging.debug(f"[handle_search] Target is an object: {target_name}")
        # Use the public method name here
        target_object_id = game_state.find_object_id_by_name_in_location(target_name)
        
        if not target_object_id:
            # TODO: Need search_fail_target_not_found key
            return [{'key': "search_fail_target_not_found", 'data': {"target_name": target_name}}]
            
        # Get object data
        target_object_data = game_state.get_object_by_id(target_object_id)
        if not target_object_data:
            logging.error(f"Search target '{target_name}' matched ID '{target_object_id}' but data is missing.")
            return [{'key': "error_internal", 'data': {"action": "search object data"}}]
            
        # --- !!! Special Case: Searching the Bed !!! ---
        if target_object_id == "cab_bed":
            logging.debug(f"[handle_search] Special check for cab_bed search.")
            # Check if the keycard has already been found using a game flag
            if not game_state.get_game_flag("found_keycard_in_bed"):
                logging.debug(f"[handle_search] Keycard not yet found in bed. Attempting to reveal.")

                # Add the keycard object ID to the current location's list
                added_to_location = game_state._add_object_to_location("cab_locker_keycard")

                if added_to_location:
                    # Set the flag to indicate the keycard has been found
                    game_state.set_game_flag("found_keycard_in_bed", True)
                    logging.info(f"Player searched bed and revealed cab_locker_keycard in the location.")
                    # Return the specific reveal message
                    return [{'key': "search_reveal_keycard_bed", 'data': {}}]
                else:
                    # Failed to add to location (e.g., already there? Error in _add_object?)
                    logging.error(f"_add_object_to_location failed for cab_locker_keycard when searching bed.")
                    # Fall back to generic search fail message
                    return [{'key': "search_fail_nothing_hidden", 'data': {"target_name": target_name}}]
            else:
                # Keycard already found, return standard nothing found message
                logging.debug(f"[handle_search] Keycard already found (flag 'found_keycard_in_bed' is true).")
                return [{'key': "search_fail_nothing_hidden", 'data': {"target_name": target_name}}]
        # --- !!! End Special Case !!! ---

        # Check if the object *can* be searched (e.g., is it a container, furniture?)
        # For now, assume any object can potentially hide things.
        
        # Check for hidden items *within* the object definition
        # This requires a specific structure in objects.yaml, e.g.:
        # hidden_items: [key_001]
        hidden_items = target_object_data.get("hidden_items", []) 
        
        if hidden_items:
             found_item_id = random.choice(hidden_items)
             item_data = game_state.get_object_by_id(found_item_id)
             item_name = item_data.get("name", found_item_id) if item_data else found_item_id
             
             # TODO: Add found item to the location? Or directly to player inventory/hands?
             # Let's add it to the location for now.
             added = game_state._add_object_to_location(found_item_id)
             if not added:
                 logging.error(f"Failed to add found hidden item '{found_item_id}' to location.")
                 # Still tell the player they found it, even if adding failed
                 return [{'key': "search_success_hidden_item_found", 'data': {"target_name": target_name, "item_name": item_name}}, 
                         {'key': "error_internal", 'data': {"action": "search add item failed"}}]
                 
             # TODO: Remove item from target object's hidden_items state? Needs state update method.
             
             return [{'key': "search_success_hidden_item_found", 'data': {"target_name": target_name, "item_name": item_name}}]
        else:
             # Nothing hidden found in the object
             return [{'key': "search_fail_nothing_hidden", 'data': {"target_name": target_name}}] 