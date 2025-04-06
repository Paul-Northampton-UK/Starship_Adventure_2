"""Command handler for player movement."""

import logging
from typing import Optional, Dict, Any, Tuple
from ..game_state import GameState
from ..command_defs import ParsedIntent

def _format_object_list(game_state: GameState, object_ids: list) -> str:
    """Formats a list of object IDs (or dicts with 'id') into a readable sentence."""
    if not object_ids:
        return ""

    # Process input list to extract only valid string IDs
    processed_ids = []
    for item in object_ids:
        if isinstance(item, str):
            processed_ids.append(item)
        elif isinstance(item, dict) and 'id' in item:
            processed_ids.append(item['id'])
        else:
            logging.warning(f"_format_object_list: Skipping unknown item format in object list: {item}")
            
    if not processed_ids:
        return ""
        
    object_names = [game_state._get_object_name(pid) for pid in processed_ids]
    
    # Filter out names that are likely just the IDs (because data was missing)
    # This assumes object IDs don't usually look like proper names.
    valid_object_names = [
        name for name in object_names 
        if name and name not in processed_ids # Check if the retrieved name is just the ID itself
    ]
    
    if not valid_object_names:
        return "" # Nothing nameable found
        
    # Simple formatting for now, can be improved (a/an, singular/plural)
    if len(valid_object_names) == 1:
        return f"You see a {valid_object_names[0]} here."
    elif len(valid_object_names) == 2:
        return f"You see a {valid_object_names[0]} and a {valid_object_names[1]} here."
    else:
        # Oxford comma for lists of 3+
        # Apply 'a'/'an' logic simply based on first letter (can be improved)
        formatted_names = []
        for name in valid_object_names:
            prefix = "an" if name.lower().startswith(('a', 'e', 'i', 'o', 'u')) else "a"
            formatted_names.append(f"{prefix} {name}")
            
        all_but_last = ", ".join(formatted_names[:-1])
        last = formatted_names[-1]
        return f"You see {all_but_last}, and {last} here."

def _format_exit_list(exit_data_list: list[dict]) -> str:
    """Formats a list of exit data into a readable sentence."""
    if not exit_data_list:
        return "There are no obvious exits."
    
    directions = [exit_data.get("direction", "an unknown way") for exit_data in exit_data_list]
    
    if len(directions) == 1:
        return f"The only obvious exit is {directions[0]}."
    elif len(directions) == 2:
        return f"Obvious exits are {directions[0]} and {directions[1]}."
    else:
        all_but_last = ", ".join(directions[:-1])
        last = directions[-1]
        return f"Obvious exits are {all_but_last}, and {last}."

def get_location_description(game_state: GameState, room_id: str, area_id: Optional[str]) -> str:
    """Gets the appropriate description (first visit or short) for a room or area,
       including objects and exits.
       NOTE: Returns a pre-formatted string, unlike other handlers. Needs refactor if
             base descriptions also need variation.
    """
    location_data: Optional[Dict[str, Any]] = None
    is_first_visit = True
    description_key = "first_visit_description"
    location_name_for_fallback = "location"
    objects_present_ids = []
    exits_list = []
    room_data = game_state.rooms_data.get(room_id)

    if not room_data:
        logging.error(f"get_location_description: Cannot find room data for {room_id}")
        return "You are somewhere undefined... which is strange."

    exits_list = room_data.get("exits", [])

    if area_id:
        if isinstance(room_data.get("areas"), list):
            for ad in room_data["areas"]:
                if ad.get("area_id") == area_id:
                    location_data = ad
                    is_first_visit = not game_state.has_visited_area(area_id)
                    game_state.visit_area(area_id, room_id) 
                    location_name_for_fallback = location_data.get("name", "area")
                    objects_present_ids = location_data.get("area_objects", [])
                    break
        if not location_data:
             logging.error(f"get_location_description: Cannot find area data for {area_id} in {room_id}")
             return "You arrive, but the details of this area are unclear."
    else:
        location_data = room_data
        is_first_visit = not game_state.has_visited_room(room_id)
        game_state.visit_room(room_id) 
        location_name_for_fallback = location_data.get("name", "room")
        objects_present_ids = location_data.get("objects_present", [])
    
    if not is_first_visit:
        description_key = "short_description"
    
    power_state = game_state.power_state.value
    descriptions = location_data.get(description_key, {})
    if not isinstance(descriptions, dict):
        logging.error(f"{description_key} data for {area_id or room_id} is not a dictionary!")
        fallback_key = "short_description" if description_key == "first_visit_description" else "first_visit_description"
        descriptions = location_data.get(fallback_key, {})
        if not isinstance(descriptions, dict):
             base_description = f"You are in the {location_name_for_fallback}. The description seems missing."
        else:
             base_description = descriptions.get(power_state, descriptions.get("offline", f"It's too dark to see the {location_name_for_fallback} clearly."))
    else:
        base_description = descriptions.get(power_state, descriptions.get("offline", f"It's too dark to see the {location_name_for_fallback} clearly."))

    # Format and append object list
    if not isinstance(objects_present_ids, list):
         logging.warning(f"Object list for {area_id or room_id} is not a list: {objects_present_ids}")
         object_list_str = ""
    else:
         object_list_str = _format_object_list(game_state, objects_present_ids)

    # Format and append exit list
    if not isinstance(exits_list, list):
        logging.warning(f"Exit list for {room_id} is not a list: {exits_list}")
        exit_list_str = "It's unclear how to leave."
    else:
        exit_list_str = _format_exit_list(exits_list)

    # Combine the parts
    full_description = f"{base_description}\n\n{object_list_str}\n{exit_list_str}"
    # Clean up potential leading/trailing whitespace or multiple newlines
    return "\n".join(line.strip() for line in full_description.splitlines() if line.strip())

def handle_move(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the MOVE command intent. Returns (key, kwargs) tuple."""
    target = parsed_intent.target
    direction = parsed_intent.direction # Original player input direction
    current_room_id = game_state.current_room_id
    current_room_data = game_state.rooms_data.get(current_room_id)

    if not current_room_data:
        logging.error(f"Move failed: Current room '{current_room_id}' not found in rooms_data!")
        return ("error_internal", {"action": "move"}) # Generic error key

    # --- Direction Normalization --- 
    normalized_direction_map = {
        "n": "north", "s": "south", "e": "east", "w": "west",
        "u": "up", "d": "down", 
        "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
        "north-east": "northeast", "north-west": "northwest", 
        "south-east": "southeast", "south-west": "southwest"
    }
    player_direction_normalized = None # Initialize
    if direction:
        processed_direction = normalized_direction_map.get(direction, direction).lower()
        player_direction_normalized = processed_direction.replace(" ", "") 
    # --- End Direction Normalization ---

    # --- Check for Area Movement FIRST ---
    if target:
        areas_list = current_room_data.get("areas", [])
        if isinstance(areas_list, list):
            target_lower = target.lower()
            for area_data in areas_list:
                area_id = area_data.get("area_id")
                area_aliases = area_data.get("command_aliases", [])
                if area_id and (target_lower == area_id.lower() or target_lower in [str(a).lower() for a in area_aliases]):
                    if game_state.current_area_id == area_id:
                         area_name = area_data.get('name', area_id)
                         # TODO: Add move_fail_already_at_area key to responses.yaml
                         return ("move_fail_direction", {"direction": f"already at {area_name}"}) # Placeholder
                    logging.info(f"Moving player to area: {area_id} in room {current_room_id}")
                    game_state.move_to_area(area_id)
                    desc_str = get_location_description(game_state, current_room_id, area_id)
                    # Return description directly until get_location_description is refactored
                    return ("move_success", {"description": desc_str})
        else:
             logging.warning(f"Areas data for room '{current_room_id}' is not a list! Skipping area check.")

    # --- If not moving to an area, check for Directional Room Exit ---
    if player_direction_normalized:
        exits_list = current_room_data.get("exits", [])
        if not isinstance(exits_list, list):
             logging.error(f"Exits data for room '{current_room_id}' is not a list!")
             return ("error_internal", {"action": "move exits"})
        found_exit = None
        for exit_data in exits_list:
            exit_direction_yaml = exit_data.get("direction")
            if isinstance(exit_direction_yaml, str):
                yaml_direction_normalized = exit_direction_yaml.replace(" ", "").lower()
                if yaml_direction_normalized == player_direction_normalized:
                    found_exit = exit_data
                    break 
        if found_exit:
            next_room_id = found_exit.get("destination")
            if not next_room_id:
                 logging.error(f"Exit '{player_direction_normalized}' in room '{current_room_id}' has no destination.")
                 return ("error_internal", {"action": "move destination"})
            if next_room_id in game_state.rooms_data:
                logging.info(f"Moving player via exit '{player_direction_normalized}' from {current_room_id} to {next_room_id}")
                game_state.move_to_room(next_room_id)
                # Get description here so room visit is marked
                desc_str = get_location_description(game_state, next_room_id, None)
                # Return the description directly with a specific key
                return ("move_success_description", {"description": desc_str})
            else:
                logging.warning(f"Exit '{player_direction_normalized}' leads to non-existent room '{next_room_id}' from '{current_room_id}'")
                # TODO: Add move_fail_blocked key to responses.yaml
                return ("move_fail_direction", {"direction": direction or 'that way'}) # Placeholder
        else:
            return ("move_fail_direction", {"direction": direction})
            
    # --- Fallback Messages if No Action Was Taken --- 
    elif not target: 
         # TODO: Add move_fail_no_target key to responses.yaml
         return ("invalid_command", {}) # Placeholder
    elif target: 
         return ("move_fail_area", {"target_name": target})

    # Default fallback
    logging.warning("[handle_move] Reached unexpected fallback return.")
    return ("error_internal", {"action": "move fallback"}) 