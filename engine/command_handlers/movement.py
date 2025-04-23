"""Command handler for player movement."""

import logging
from typing import Optional, Dict, Any, Tuple, List
from ..game_state import GameState
from ..command_defs import ParsedIntent

# Helper function to determine 'a' or 'an' (improved)
def _get_indefinite_article(word: str) -> str:
    if not word:
        return "a" # Default
    # Simple vowel check, ignoring silent 'h' etc.
    return "an" if word.lower().startswith(('a', 'e', 'i', 'o', 'u')) else "a"

def _format_object_list(game_state: GameState, object_ids: list) -> str:
    """Formats a list of object IDs (or dicts with 'id') into a readable sentence,
       correctly handling plurals and articles."""
    logging.debug(f"[_format_object_list] Received object ID list: {object_ids}")
    if not object_ids:
        return ""

    processed_ids = []
    for item in object_ids:
        if isinstance(item, str):
            processed_ids.append(item)
        elif isinstance(item, dict) and 'id' in item:
            processed_ids.append(item['id'])
        else:
            logging.warning(f"_format_object_list: Skipping unknown item format in object list: {item}")

    logging.debug(f"[_format_object_list] Processed IDs: {processed_ids}")
    if not processed_ids:
        return ""

    formatted_names = []
    for pid in processed_ids:
        object_data = game_state.objects_data.get(pid)
        if not object_data:
            logging.warning(f"[_format_object_list] Object data not found for ID '{pid}'")
            continue # Skip objects not found in main data

        name = object_data.get("name", pid) # Fallback to ID if name missing
        is_plural = object_data.get("is_plural", False)

        # Skip if name is still just the ID (data likely incomplete)
        if name == pid and " " not in name: # Check if name is just the ID
            logging.debug(f"[_format_object_list] Filtering out ID-like name '{name}' for ID '{pid}'")
            continue

        logging.debug(f"[_format_object_list] ID: {pid}, Name: '{name}', Plural: {is_plural}")

        if is_plural:
            formatted_names.append(name)
        else:
            article = _get_indefinite_article(name)
            formatted_names.append(f"{article} {name}")

    logging.debug(f"[_format_object_list] Filtered & Formatted Names: {formatted_names}")
    if not formatted_names:
        return "" # Nothing nameable found

    # Format the final sentence
    if len(formatted_names) == 1:
        return f"You see {formatted_names[0]} here."
    elif len(formatted_names) == 2:
        return f"You see {formatted_names[0]} and {formatted_names[1]} here."
    else:
        # Oxford comma for lists of 3+
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

def get_location_description(game_state: GameState, room_id: str, area_id: Optional[str], force_long_description: bool = False) -> str:
    """Gets the appropriate description for a room or area, including objects and exits.

    Args:
        game_state: The current game state.
        room_id: The ID of the room.
        area_id: The ID of the area within the room (optional).
        force_long_description: If True, always returns the first_visit_description.

    Returns:
        A formatted string containing the location name, description, objects, and exits.
    """
    location_data: Optional[Dict[str, Any]] = None
    is_first_visit = True
    description_key = "first_visit_description"
    location_id_for_log = area_id or room_id
    objects_present_ids = []
    exits_list = []
    room_data = game_state.rooms_data.get(room_id)

    if not room_data:
        logging.error(f"get_location_description: Cannot find room data for {room_id}")
        return "[Unknown Location]\nYou are somewhere undefined... which is strange."

    exits_list = room_data.get("exits", [])
    location_name = room_data.get("name", room_id) # Default to room name

    # Determine if we are looking at an area or the room itself
    if area_id:
        location_found = False
        if isinstance(room_data.get("areas"), list):
            for ad in room_data["areas"]:
                if ad.get("area_id") == area_id:
                    location_data = ad
                    location_name = location_data.get("name", area_id) # Use area name
                    is_first_visit = not game_state.has_visited_area(area_id)
                    if is_first_visit: game_state.visit_area(area_id, room_id)
                    objects_present_ids = location_data.get("objects_present", [])
                    location_found = True
                    break # Found the area data
        if not location_found: # Area ID provided but not found
             logging.error(f"get_location_description: Cannot find area data for {area_id} in {room_id}")
             return f"[{area_id}]\nYou arrive, but the details of this area are unclear."
    else:
        # Looking at the room itself
        location_data = room_data
        location_name = location_data.get("name", room_id) # Use room name
        is_first_visit = not game_state.has_visited_room(room_id)
        if is_first_visit: game_state.visit_room(room_id)
        objects_present_ids = location_data.get("objects_present", [])

    # Determine which description key to use
    if not force_long_description and not is_first_visit:
        description_key = "short_description"

    # Get the base description based on power state
    power_state = game_state.power_state.value
    descriptions = location_data.get(description_key, {})
    if not isinstance(descriptions, dict):
        logging.warning(f"{description_key} data for {location_id_for_log} is not a dictionary! Trying fallback...")
        fallback_key = "short_description" if description_key == "first_visit_description" else "first_visit_description"
        descriptions = location_data.get(fallback_key, {})
        if not isinstance(descriptions, dict):
             logging.error(f"Both description keys missing or invalid for {location_id_for_log}")
             base_description = f"The description for this location seems missing."
        else:
             base_description = descriptions.get(power_state, descriptions.get("offline", f"It\'s too dark to see clearly."))
    else:
        base_description = descriptions.get(power_state, descriptions.get("offline", f"It\'s too dark to see clearly."))

    # Format object list
    if not isinstance(objects_present_ids, list):
         logging.warning(f"Object list for {location_id_for_log} is not a list: {objects_present_ids}")
         object_list_str = ""
    else:
         logging.debug(f"Formatting object list for {location_id_for_log}: {objects_present_ids}")
         object_list_str = _format_object_list(game_state, objects_present_ids)
         logging.debug(f"Formatted object string: '{object_list_str}'")

    # Format exit list
    if not isinstance(exits_list, list):
        logging.warning(f"Exit list for {room_id} is not a list: {exits_list}")
        exit_list_str = "It's unclear how to leave."
    else:
        exit_list_str = _format_exit_list(exits_list)

    # Format area list (if any areas exist in the room)
    area_list_str = ""
    if isinstance(room_data.get("areas"), list) and room_data["areas"]:
        area_names = [a.get("name", a.get("area_id", "unnamed area")) for a in room_data["areas"]]
        if area_names:
            if len(area_names) == 1:
                area_list_str = f"Area here: {area_names[0]}"
            elif len(area_names) == 2:
                area_list_str = f"Areas here: {area_names[0]} and {area_names[1]}"
            else:
                area_list_str = f"Areas here: {', '.join(area_names[:-1])}, and {area_names[-1]}"

    # Combine the parts, adding the location name header and area list
    location_header = f"[{location_name}]"
    # Include area_list_str only if it's not empty, placing it after object list
    full_description = f"{location_header}\n{base_description}\n\n{object_list_str}"
    if area_list_str:
         full_description += f"\n{area_list_str}"
    full_description += f"\n{exit_list_str}"
    # Clean up potential leading/trailing whitespace or multiple newlines
    return "\n".join(line.strip() for line in full_description.splitlines() if line.strip())

def handle_move(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the MOVE command intent. Checks Area movement first, then Directional exits."""
    target = parsed_intent.target # Might be an Area name/ID or other text
    direction_input = parsed_intent.direction # Normalized cardinal direction from parser (if found)
    current_room_id = game_state.current_room_id
    current_room_data = game_state.rooms_data.get(current_room_id)

    if not current_room_data:
        logging.error(f"Move failed: Current room '{current_room_id}' not found in rooms_data!")
        return [{'key': "error_internal", 'data': {"action": "move room data"}}]

    # --- Check for Area Movement FIRST (using target) ---
    if target:
        areas_list = current_room_data.get("areas", [])
        matched_area_id = None
        if isinstance(areas_list, list):
            target_lower = target.lower()
            for area_data in areas_list:
                area_id = area_data.get("area_id")
                # Add check for area_name later if needed
                area_aliases = [str(a).lower() for a in area_data.get("command_aliases", [])] # Handle potential non-strings
                if area_id and (target_lower == area_id.lower() or target_lower in area_aliases):
                    # Check for direct ID match or alias match
                    matched_area_id = area_id
                    break 
            
            if matched_area_id:
                if game_state.current_area_id == matched_area_id:
                     area_name = game_state._get_object_name(matched_area_id) # Try getting a proper name if possible
                     return [{'key': "move_fail_already_at_area", 'data': {"area_name": area_name or matched_area_id}}]
                else:
                     logging.info(f"Moving player to area: {matched_area_id} in room {current_room_id}")
                     game_state.move_to_area(matched_area_id)
                     desc_str = get_location_description(game_state, current_room_id, matched_area_id)
                     # Use correct key for returning a description
                     return [{'key': "move_success_description", 'data': {"description": desc_str}}]
        else:
             logging.warning(f"Areas data for room '{current_room_id}' is not a list! Skipping area check.")

    # --- If not moving to an area, check for Directional Room Exit (using direction_input) ---
    if direction_input: # Use the normalized direction from the parser
        exits_list = current_room_data.get("exits", [])
        if not isinstance(exits_list, list):
             logging.error(f"Exits data for room '{current_room_id}' is not a list!")
             return [{'key': "error_internal", 'data': {"action": "move exits"}}]
        found_exit = None
        for exit_data in exits_list:
            exit_direction_yaml = exit_data.get("direction")
            if isinstance(exit_direction_yaml, str):
                yaml_direction_normalized = exit_direction_yaml.replace(" ", "").lower()
                if yaml_direction_normalized == direction_input:
                    found_exit = exit_data
                    break 
        if found_exit:
            next_room_id = found_exit.get("destination")
            if not next_room_id:
                 logging.error(f"Exit '{direction_input}' in room '{current_room_id}' has no destination.")
                 return [{'key': "error_internal", 'data': {"action": "move destination"}}]
            # Use ONLY direction_input for logic checks from here
            if next_room_id in game_state.rooms_data:
                logging.info(f"Moving player via exit '{direction_input}' from {current_room_id} to {next_room_id}")
                game_state.move_to_room(next_room_id)
                desc_str = get_location_description(game_state, next_room_id, None)
                return [{'key': "move_success_description", 'data': {"description": desc_str}}]
            else:
                logging.warning(f"Exit '{direction_input}' leads to non-existent room '{next_room_id}' from '{current_room_id}'")
                # Pass the normalized direction for the failure message
                return [{'key': "move_fail_direction", 'data': {"direction": direction_input}}]
        else:
            # No matching exit found
            return [{'key': "move_fail_direction", 'data': {"direction": direction_input}}]
            
    # --- Fallback Messages if No Action Was Taken --- 
    # If we had a target but it wasn't a valid area
    if target:
         return [{'key': "move_fail_target_not_found", 'data': {"target_name": target}}]
    # If we had no direction and no target
    elif not direction_input:
         return [{'key': "move_fail_no_direction", 'data': {}}]
    # Should not be reached if direction_input was present but no exit found (handled above)
    else:
         logging.error("handle_move reached unexpected state.")
         return [{'key': "invalid_command", 'data': {}}] 