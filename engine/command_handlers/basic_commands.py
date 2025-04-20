"""Command handlers for basic game actions like look, inventory, quit."""

import logging
from typing import Optional, Dict, Any, Tuple
from ..game_state import GameState
from ..command_defs import ParsedIntent
# Note: We need access to get_location_description, so we might import it
# or reconsider if _handle_look belongs here or requires its own module/utils.
# For now, let's assume GameLoop might pass the display_output function if needed.

# Import the enhanced description function
from .movement import get_location_description 
# Import utility for item matching (correct relative path)
from .utils import item_matches_name 

def handle_look(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the LOOK command intent. 
       Can look at the current location or a specific item/target.
    """
    target_name = parsed_intent.target # Get the target name from the parsed intent
    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id

    if not target_name or target_name.lower() in ["room", "area", "around", "here"]:
        # Look at the current room/area - Force the long description
        desc_str = get_location_description(game_state, current_room_id, current_area_id, force_long_description=True)
        return ("look_success_room", {"description": desc_str})
    else:
        # Look at a specific target (item, feature, etc.)
        obj_id_to_describe: Optional[str] = None
        
        # 1. Check location (current room/area)
        obj_id_to_describe = game_state._find_object_id_by_name_in_location(target_name)
        
        # 2. If not in location, check if held
        if not obj_id_to_describe and game_state.hand_slot:
            for held_id in game_state.hand_slot:
                if item_matches_name(game_state, held_id, target_name):
                    obj_id_to_describe = held_id # Assign the specific matched ID
                    break # Found it, stop checking hands

        # 3. If not held or found in location, check worn items
        if not obj_id_to_describe:
            obj_id_to_describe = game_state._find_object_id_by_name_worn(target_name)

        # 4. If not worn, check inventory
        if not obj_id_to_describe:
            obj_id_to_describe = game_state._find_object_id_by_name_in_inventory(target_name)

        # Now check if we found the object ID
        if obj_id_to_describe:
            item_data = game_state.get_object_by_id(obj_id_to_describe)
            if item_data:
                # Use item's description, fallback to generic
                item_description = item_data.get("description", f"You look closely at the {item_data.get('name', target_name)}.")
                logging.debug(f"handle_look: SUCCESS - Found {target_name} (ID: {obj_id_to_describe}). Returning description.")
                return ("look_success_item", {"description": item_description})
            else:
                # This case should ideally not happen if IDs are consistent
                logging.error(f"Look target '{target_name}' resolved to ID '{obj_id_to_describe}' but no data found.")
                return ("error_internal", {"action": f"look for {target_name}"})
        else:
            # Item not found anywhere
            logging.debug(f"handle_look: FAILED - Target '{target_name}' not found in location, hands, worn, or inventory.")
            return ("look_fail_not_found", {"item_name": target_name})

def handle_inventory(game_state: GameState, parsed_intent: ParsedIntent, display_callback) -> Tuple:
    """Handles the INVENTORY command intent by displaying status via callback. Returns empty tuple."""
    inventory = game_state.inventory or [] 
    hand_slot = game_state.hand_slot
    worn_items = game_state.worn_items or []

    output = "You check your belongings.\n"

    # Display item(s) in hand
    if hand_slot:
        held_items_lines = []
        for held_id in hand_slot:
            item_name = game_state._get_object_name(held_id)
            item_data = game_state.get_object_by_id(held_id)
            detail_line = f"  Holding: {item_name}"
            
            # --- ADDED: Check if held item is storage and display contents ---
            if item_data and item_data.get('properties', {}).get('is_storage'):
                 container_state = game_state.get_object_state(held_id) or {}
                 contents = container_state.get('contains', [])
                 if contents:
                     detail_line += ":"
                     held_items_lines.append(detail_line) # Add the container line first
                     for content_id in sorted(contents):
                         content_name = game_state._get_object_name(content_id)
                         held_items_lines.append(f"    - {content_name}") # Indent contents
                 else:
                     detail_line += " (empty)"
                     held_items_lines.append(detail_line)
            else:
                 held_items_lines.append(detail_line) # Append non-container item line
            # --- END ADDED --- 
            
        if held_items_lines:
            output += "\n".join(held_items_lines) + "\n"
        else: # Should not happen if hand_slot is not empty, but safety check
            output += "  Holding: Nothing\n"
    else:
        output += "  Holding: Nothing\n"

    # Display worn items
    output += "  Wearing:\n"
    if worn_items:
        worn_item_details = []
        for item_id in sorted(worn_items):
            item_name = game_state._get_object_name(item_id)
            item_data = game_state.get_object_by_id(item_id)
            detail_line = f"    - {item_name}"
            if item_data:
                properties = item_data.get('properties', {})
                area = properties.get('wear_area', 'Unknown Area')
                layer = properties.get('wear_layer', '?')
                detail_line += f" (Area: {area}, Layer: {layer})"
                
                # --- ADDED: Check if worn item is storage and display contents ---
                if properties.get('is_storage'):
                    container_state = game_state.get_object_state(item_id) or {}
                    # Use the correct 'contains' key
                    contents = container_state.get('contains', [])
                    if contents:
                        detail_line += ":\n"
                        for content_id in sorted(contents):
                            content_name = game_state._get_object_name(content_id)
                            # Make sure indentation is correct for nested display
                            detail_line += f"        - {content_name}\n" # Adjusted indentation
                        detail_line = detail_line.rstrip() # Remove trailing newline from last item
                    else:
                        detail_line += " (empty)"
                # No need for an explicit newline adding here, handled by join later
                # else:
                #      detail_line += "\n" # Add newline if not storage
                # --- END ADDED --- 
            else:
                detail_line += " (Data missing!)"
                
            worn_item_details.append(detail_line) # Append without extra newline

        if worn_item_details:
            output += "\n".join(worn_item_details) + "\n"
        else:
            output += "    Nothing\n"
    else:
        output += "    Nothing\n"

    # --- REMOVED Inventory Section ---
    # output += "  Carrying in Inventory:\n"
    # if inventory:
    #     inventory_names = []
    #     for item_id in sorted(inventory):
    #          inventory_names.append(f"    - {game_state._get_object_name(item_id)}")
    #     if inventory_names:
    #         output += "\n".join(inventory_names) + "\n"
    #     else:
    #         output += "    Nothing\n"
    # else:
    #     output += "    Nothing\n"
    # --- END REMOVED ---

    # Use the passed callback to display output
    display_callback(output.strip())
    return () # Return empty tuple as signal that output was handled

def handle_quit(game_state: GameState, parsed_intent: ParsedIntent) -> None:
    """Handles the QUIT command intent. Returns None to signal quit."""
    # The signal to quit will be returning None instead of a message string.
    return None

def handle_unknown(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles unrecognized commands."""
    # Log the raw input for debugging
    logging.info(f"Unknown command received: '{parsed_intent.original_input}'") # Corrected attribute name
    # Return a key that maps to confused responses
    return ("invalid_command", {}) 