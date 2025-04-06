"""Command handler for player movement."""

import logging
from typing import Optional, Dict, Any
from ..game_state import GameState
from ..command_defs import ParsedIntent

def get_location_description(game_state: GameState, room_id: str, area_id: Optional[str]) -> str:
    """Gets the appropriate description (first visit or short) for a room or area."""
    location_data: Optional[Dict[str, Any]] = None
    is_first_visit = True
    description_key = "first_visit_description"
    location_name_for_fallback = "location"

    if area_id:
        # Get Area Data
        room_data = game_state.rooms_data.get(room_id)
        if room_data and isinstance(room_data.get("areas"), list):
            for ad in room_data["areas"]:
                if ad.get("area_id") == area_id:
                    location_data = ad
                    is_first_visit = not game_state.has_visited_area(area_id)
                    # Pass room_id when marking area visited
                    game_state.visit_area(area_id, room_id) 
                    location_name_for_fallback = location_data.get("name", "area")
                    break
        if not location_data:
             logging.error(f"_get_location_description: Cannot find area data for {area_id} in {room_id}")
             return "You arrive, but the details of this area are unclear."
    else:
        # Get Room Data
        location_data = game_state.rooms_data.get(room_id)
        if location_data:
            is_first_visit = not game_state.has_visited_room(room_id)
            game_state.visit_room(room_id) # Mark as visited
            location_name_for_fallback = location_data.get("name", "room")
        else:
            logging.error(f"_get_location_description: Cannot find room data for {room_id}")
            return "You arrive, but the details of this room are unclear."
    
    # Determine which description to use
    if not is_first_visit:
        description_key = "short_description"
        logging.debug(f"Location {area_id or room_id} already visited. Using short_description.")
    else:
         logging.debug(f"First visit to location {area_id or room_id}. Using first_visit_description.")

    # Get description based on power state
    power_state = game_state.power_state.value
    descriptions = location_data.get(description_key, {})
    if not isinstance(descriptions, dict):
        logging.error(f"{description_key} data for {area_id or room_id} is not a dictionary!")
        # Fallback to the other description type if possible
        fallback_key = "short_description" if description_key == "first_visit_description" else "first_visit_description"
        descriptions = location_data.get(fallback_key, {})
        if not isinstance(descriptions, dict):
             return f"The description for the {location_name_for_fallback} seems to be missing or malformed."
    
    description = descriptions.get(power_state, descriptions.get("offline", f"It's too dark to see the {location_name_for_fallback} clearly."))

    # TODO: Append exit/object info?
    return description

def handle_move(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles the MOVE command intent.
    
    Checks for movement to a specific Area or via a Directional Exit.
    Updates game state and returns the description of the new location.
    """
    target = parsed_intent.target
    direction = parsed_intent.direction
    current_room_id = game_state.current_room_id
    current_room_data = game_state.rooms_data.get(current_room_id)

    if not current_room_data:
        logging.error(f"Move failed: Current room '{current_room_id}' not found in rooms_data!")
        return "An internal error occurred: current room data missing."

    # --- Direction Normalization --- 
    normalized_direction_map = {
        "n": "north", "s": "south", "e": "east", "w": "west",
        "u": "up", "d": "down", 
        "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
        "north-east": "northeast", "north-west": "northwest", 
        "south-east": "southeast", "south-west": "southwest"
    }
    # Normalize player input direction ONLY if a direction was parsed
    player_direction_normalized = None # Initialize
    if direction: # Check if direction is not None
        processed_direction = normalized_direction_map.get(direction, direction).lower()
        # Also remove spaces from player input to match YAML processing
        player_direction_normalized = processed_direction.replace(" ", "") 
    else:
         logging.debug("[_handle_move] No direction provided by parser.")
    # --- End Direction Normalization --- 

    # --- Check for Area Movement FIRST ---
    if target:
        areas_list = current_room_data.get("areas", [])
        if isinstance(areas_list, list):
            target_lower = target.lower()
            for area_data in areas_list:
                area_id = area_data.get("area_id")
                area_aliases = area_data.get("command_aliases", [])
                
                # Match area ID or any of its aliases
                if area_id and (target_lower == area_id.lower() or target_lower in [str(a).lower() for a in area_aliases]):
                    # Check if already in this area
                    if game_state.current_area_id == area_id:
                         return f"You are already at the {area_data.get('name', area_id)}."
                         
                    # Successfully moving to a new area
                    logging.info(f"Moving player to area: {area_id} in room {current_room_id}")
                    game_state.move_to_area(area_id)
                    # Return description based on visit status
                    return get_location_description(game_state, current_room_id, area_id)
        else:
             logging.warning(f"Areas data for room '{current_room_id}' is not a list! Skipping area check.")

    # --- If not moving to an area, check for Directional Room Exit ---
    # Only check exits if a direction *was* actually processed
    if player_direction_normalized:
        exits_list = current_room_data.get("exits", [])
        if not isinstance(exits_list, list):
             logging.error(f"Exits data for room '{current_room_id}' is not a list!")
             return "An internal error occurred: room exits data malformed."

        # Find the matching exit in the list
        found_exit = None
        for exit_data in exits_list:
            # Ensure direction key exists and is a string before comparing
            exit_direction_yaml = exit_data.get("direction")
            # Compare lowercase versions after removing spaces for flexibility
            if isinstance(exit_direction_yaml, str):
                yaml_direction_normalized = exit_direction_yaml.replace(" ", "").lower()
                # player_direction_normalized is already processed
                if yaml_direction_normalized == player_direction_normalized:
                    found_exit = exit_data
                    break # Found the matching exit

        if found_exit:
            next_room_id = found_exit.get("destination")
            if not next_room_id:
                 logging.error(f"Exit '{player_direction_normalized}' in room '{current_room_id}' has no destination.")
                 # Use original direction input for message if available
                 return f"You try to go {direction or 'that way'}, but the destination seems undefined."

            # Check if the destination room exists
            if next_room_id in game_state.rooms_data:
                logging.info(f"Moving player via exit '{player_direction_normalized}' from {current_room_id} to {next_room_id}")
                game_state.move_to_room(next_room_id)
                # Return description based on visit status
                return get_location_description(game_state, next_room_id, None) # Area is None when entering a room
            else:
                logging.warning(f"Exit '{player_direction_normalized}' leads to non-existent room '{next_room_id}' from '{current_room_id}'")
                return f"You try to go {direction or 'that way'}, but the way seems blocked or leads nowhere defined."
        else:
            # Direction was given, but no matching exit found
            return f"You can't go {direction} from here."
            
    # --- Fallback Messages if No Action Was Taken --- 
    elif not target: # No direction AND no target was given (and area move didn't happen)
         return "Which direction or area do you want to move to? (e.g., north, n, nav station)"
         
    elif target: # Target was given but didn't match an area (and no direction given)
         # The area search loop above didn't find a match and didn't return.
         return f"You can't move to '{target}' like that. Try a direction (e.g. north) or a known area name."

    # Default fallback if something truly unexpected occurs (should be rare)
    logging.warning("[_handle_move] Reached unexpected fallback return.")
    return "You can't move that way." 