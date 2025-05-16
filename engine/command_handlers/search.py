"""Command handler for searching locations and objects."""

import logging
from typing import Dict, List, Any # Changed Tuple to Any for data dict
from ..game_state import GameState
from ..command_defs import ParsedIntent # CommandResponse removed, random removed
# get_response_text removed as GameLoop will handle formatting

def handle_search(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict[str, Any]]: # Changed return type
    """
    Handles the 'search' command.

    Allows the player to search specific objects or areas in the current room
    to find hidden items or clues.
    """
    target_object_id = parsed_intent.target_object_id
    target_object_name_player = parsed_intent.target or target_object_id

    if not target_object_id:
        # Player typed "search" without a target or parser didn't ID it
        return [{
            "key": "SEARCH_NO_TARGET",
            "data": {}
        }]

    # Check if the target object is in the current room
    obj_data = game_state.get_object_by_id(target_object_id)
    
    # Get objects in the current room
    current_room_data = game_state.rooms_data.get(game_state.current_room_id)
    current_room_objects_refs: List[Any] = [] # Store references (IDs or dicts)
    if current_room_data:
        # For now, assuming we are not in a specific sub-area for the 'search' command's context.
        # If 'search' needs to be area-aware, this logic would need to check game_state.current_area_id
        current_room_objects_refs = current_room_data.get("objects_present", [])
    else:
        logging.error(f"handle_search: Could not find room data for current_room_id: {game_state.current_room_id}")
        # Fallback to an empty list, error message will be generated later if obj_data is None

    # Ensure current_room_objects is a list of objects with an 'id' attribute for comparison
    target_is_in_room = False
    # The list can contain strings (object_ids) or dicts (like {'id': 'obj_id', 'state': ...})
    # We need to extract the ID in either case for comparison.
    if current_room_objects_refs and isinstance(current_room_objects_refs, list):
        for item_ref in current_room_objects_refs:
            item_id_in_room = None
            if isinstance(item_ref, str):
                item_id_in_room = item_ref
            elif isinstance(item_ref, dict) and 'id' in item_ref:
                item_id_in_room = item_ref['id']
            
            if item_id_in_room == target_object_id:
                target_is_in_room = True
                break

    if not obj_data or not target_is_in_room:
        obj_name_for_msg = target_object_name_player if target_object_name_player != target_object_id else target_object_id
        return [{
            "key": "OBJECT_NOT_FOUND_IN_ROOM",
            "data": {"item_name": obj_name_for_msg}
        }]

    # Get the canonical name of the object being searched for messages
    searched_object_canonical_name = obj_data.get('name', target_object_id)

    # --- Special Search Logic ---
    if target_object_id == "cab_bed":
        keycard_id = "cab_locker_keycard"
        keycard_data = game_state.get_object_by_id(keycard_id)
        # Ensure keycard_data exists before proceeding
        if not keycard_data:
            logging.error(f"[handle_search] Data for '{keycard_id}' not found. Cannot proceed with bed search logic.")
            # Potentially return a generic search failure or a specific error response
            return [{"key": "SEARCH_EMPTY_GENERIC", "data": {"target_name": target_object_name_player}}]

        if not game_state.get_game_flag(f"{keycard_id}_found_in_bed"):
            game_state.set_object_state(keycard_id, "is_visible", True)
            # If the keycard isn't already considered part of the room's static objects, add it dynamically.
            if not game_state.is_object_statically_in_room(keycard_id, game_state.current_room_id):
                game_state.add_dynamic_object_to_room(game_state.current_room_id, keycard_id)
            game_state.set_game_flag(f"{keycard_id}_found_in_bed", True)
            
            keycard_name = keycard_data.get("name", keycard_id)
            bed_name = target_object_name_player # Use the name the player used or the default name
            logging.info(f"Object '{keycard_id}' state 'is_visible' set to True after searching '{target_object_id}'. Flag '{keycard_id}_found_in_bed' set.")
            
            return [{
                "key": "SEARCH_BED_FINDS_KEYCARD",
                "data": {"bed_name": bed_name, "keycard_name": keycard_name, "found_item_id": keycard_id}
            }]
        else:
            # Player has already found the keycard by searching the bed
            # GameLoop will handle missing key fallback if necessary
            return [{
                "key": "SEARCH_BED_ALREADY_FOUND_KEYCARD",
                "data": {"item_name": target_object_name_player}
            }]
    
    # --- Default Search Logic (if no special case matched) ---
    # GameLoop will handle missing key fallback if necessary
    return [{
        "key": "SEARCH_EMPTY_GENERIC",
        "data": {"item_name": searched_object_canonical_name}
    }] 