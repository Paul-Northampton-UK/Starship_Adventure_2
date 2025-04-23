"""Command handlers for basic game actions like look, inventory, quit."""

import logging
from typing import Optional, Dict, Any, Tuple, List
from ..game_state import GameState
from ..command_defs import ParsedIntent
# Note: We need access to get_location_description, so we might import it
# or reconsider if _handle_look belongs here or requires its own module/utils.
# For now, let's assume GameLoop might pass the display_output function if needed.

# Import the enhanced description function
from .movement import get_location_description 
# Import utility for item matching (correct relative path)
from .utils import item_matches_name 

def handle_look(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the LOOK command intent. 
       Can look at the current location or a specific item/target.
    """
    target_name = parsed_intent.target # Get the target name from the parsed intent
    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id

    if not target_name or target_name.lower() in ["room", "area", "around", "here"]:
        # Look at the current room/area - Force the long description
        desc_str = get_location_description(game_state, current_room_id, current_area_id, force_long_description=True)
        return [{'key': "look_success_room", 'data': {"description": desc_str}}]
    else:
        # Look at a specific target (item, feature, etc.)
        obj_id_to_describe = game_state.find_object_id_by_name_in_location(target_name)
        
        if obj_id_to_describe:
            obj_data = game_state.get_object_by_id(obj_id_to_describe)
            if obj_data:
                # Use detailed description if available, otherwise fallback
                description = obj_data.get("detailed_description", obj_data.get("description", f"You see a {obj_data.get('name', target_name)}."))
                return [{'key': "look_success_item", 'data': {"description": description}}]
            else:
                logging.error(f"Look target '{target_name}' matched ID '{obj_id_to_describe}' but data is missing.")
                return [{'key': "error_internal", 'data': {'action': "look data missing"}}]
        else:
            # Item not found anywhere
            logging.debug(f"handle_look: FAILED - Target '{target_name}' not found in location, hands, worn, or inventory.")
            return [{'key': "look_fail_not_found", 'data': {"item_name": target_name}}]

def handle_inventory(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles the INVENTORY command intent by formatting and returning the status."""
    hand_slot = game_state.hand_slot
    worn_items = game_state.worn_items or []

    output_lines = ["You check your belongings."] # Start with a title

    # Display item(s) in hand
    held_items_section = []
    if hand_slot:
        for held_id in hand_slot:
            item_name = game_state._get_object_name(held_id)
            item_data = game_state.get_object_by_id(held_id)
            detail_line = f"  Holding: {item_name}"
            
            if item_data and item_data.get('properties', {}).get('is_storage'):
                 container_state = game_state.get_object_state(held_id) or {}
                 contents = container_state.get('contains', [])
                 if contents:
                     detail_line += ":"
                     held_items_section.append(detail_line)
                     for content_id in sorted(contents):
                         content_name = game_state._get_object_name(content_id)
                         held_items_section.append(f"    - {content_name}")
                 else:
                     detail_line += " (empty)"
                     held_items_section.append(detail_line)
            else:
                 held_items_section.append(detail_line)
    else:
        held_items_section.append("  Holding: Nothing")
    
    if held_items_section:
         output_lines.extend(held_items_section)

    # Display worn items
    output_lines.append("  Wearing:")
    if worn_items:
        worn_item_lines = []
        for item_id in sorted(worn_items):
            item_name = game_state._get_object_name(item_id)
            item_data = game_state.get_object_by_id(item_id)
            detail_line = f"    - {item_name}"
            if item_data:
                properties = item_data.get('properties', {})
                area = properties.get('wear_area', 'Unknown Area')
                layer = properties.get('wear_layer', '?')
                detail_line += f" (Area: {area}, Layer: {layer})"
                
                if properties.get('is_storage'):
                    container_state = game_state.get_object_state(item_id) or {}
                    contents = container_state.get('contains', [])
                    if contents:
                        detail_line += ":"
                        worn_item_lines.append(detail_line) # Add container line first
                        for content_id in sorted(contents):
                            content_name = game_state._get_object_name(content_id)
                            worn_item_lines.append(f"        - {content_name}") # Indent contents
                        continue # Skip adding the base container line again if contents were added
                    else:
                        detail_line += " (empty)"
            else:
                detail_line += " (Data missing!)"
                
            worn_item_lines.append(detail_line) 

        if worn_item_lines:
            output_lines.extend(worn_item_lines)
        else:
            output_lines.append("    Nothing") # Should not happen if worn_items not empty
    else:
        output_lines.append("    Nothing")

    # Format the final message string
    final_output = "\n".join(output_lines)
    
    # Return using the standard List[Dict] format with a new key
    # We'll add 'inventory_display' key to responses.yaml
    return [{'key': "inventory_display", 'data': {"inventory_text": final_output}}]

def handle_quit(game_state: GameState, parsed_intent: ParsedIntent) -> None:
    """Handles the QUIT command intent. Returns None to signal quit."""
    return None

def handle_unknown(game_state: GameState, parsed_intent: ParsedIntent) -> List[Dict]:
    """Handles unrecognized commands."""
    logging.info(f"Unknown command received: '{parsed_intent.original_input}'")
    # Return List[Dict]
    return [{'key': "invalid_command", 'data': {}}] 