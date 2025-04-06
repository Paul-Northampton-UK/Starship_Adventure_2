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
# Import utility for item matching
from .utils import item_matches_name 

def handle_look(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the LOOK command intent.

    Returns a tuple: (response_key, format_kwargs).
    For general look, calls get_location_description which now returns the formatted string directly.
    For specific items, returns description string directly (needs refactor).
    """
    target = parsed_intent.target
    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id 

    # Simple check if player is looking at the location vs. a specific object
    if not target or target.lower() in ["room", "around", "area", "here"]:
        # Always show detailed description on explicit LOOK
        # Call the main description function - IT ALREADY FORMATS!
        # So, we just return this directly as a special case for now.
        # TODO: Refactor get_location_description to return key/kwargs too?
        full_description = get_location_description(game_state, current_room_id, current_area_id)
        # Using a generic key - the value is the pre-formatted description
        return ("look_success_location", {"description": full_description})
    else:
        # Look at a specific target
        target_object_id = game_state._find_object_id_by_name_in_location(target)
        obj_id_to_describe = None
        description = None
        item_name = target # Fallback name

        if target_object_id:
            obj_id_to_describe = target_object_id
            source = "location"
        else: 
             # Check inventory/worn/held
             inv_id = game_state._find_object_id_by_name_in_inventory(target)
             worn_id = game_state._find_object_id_by_name_worn(target)
             held_id = None
             if game_state.hand_slot and item_matches_name(game_state, game_state.hand_slot, target):
                 held_id = game_state.hand_slot

             if held_id:
                 obj_id_to_describe = held_id
                 source = "hand"
             elif worn_id:
                 obj_id_to_describe = worn_id
                 source = "worn"
             elif inv_id:
                 obj_id_to_describe = inv_id
                 source = "inventory"
             
        if obj_id_to_describe:
             target_data = game_state.get_object_by_id(obj_id_to_describe)
             if target_data:
                 item_name = target_data.get('name', target)
                 # Use detailed description if available, else default
                 # TODO: Make a specific response key for this?
                 description = target_data.get("description", f"You examine your {item_name}. Nothing seems out of the ordinary.")
                 # Returning pre-formatted string in description for now
                 return ("look_success_item", {"description": description})
             else:
                 logging.error(f"handle_look: Found ID {obj_id_to_describe} in player possession but missing from objects_data.")
                 return ("error_internal", {"action": "examine"}) # Generic error key

        # If not found anywhere
        return ("look_fail_not_found", {"target_name": target})

def handle_inventory(game_state: GameState, parsed_intent: ParsedIntent, display_callback) -> Tuple:
    """Handles the INVENTORY command intent by displaying status via callback. Returns empty tuple."""
    inventory = game_state.inventory or [] 
    hand_slot = game_state.hand_slot
    worn_items = game_state.worn_items or []

    output = "You check your belongings.\n"

    # Display item in hand
    if hand_slot:
        hand_item_name = game_state._get_object_name(hand_slot)
        output += f"  Holding: {hand_item_name}\n"
    else:
        output += "  Holding: Nothing\n"

    # Display worn items
    output += "  Wearing:\n"
    if worn_items:
        worn_item_details = []
        for item_id in sorted(worn_items):
            item_name = game_state._get_object_name(item_id)
            item_data = game_state.get_object_by_id(item_id)
            if item_data:
                area = item_data.get('properties',{}).get('wear_area', 'Unknown Area')
                layer = item_data.get('properties',{}).get('wear_layer', '?')
                worn_item_details.append(f"    - {item_name} (Area: {area}, Layer: {layer})")
            else:
                worn_item_details.append(f"    - {item_id} (Data missing!)")
        if worn_item_details:
            output += "\n".join(worn_item_details) + "\n"
        else:
            output += "    Nothing\n"
    else:
        output += "    Nothing\n"

    # Display inventory items
    output += "  Carrying in Inventory:\n"
    if inventory:
        inventory_names = []
        for item_id in sorted(inventory):
             inventory_names.append(f"    - {game_state._get_object_name(item_id)}")
        if inventory_names:
            output += "\n".join(inventory_names) + "\n"
        else:
            output += "    Nothing\n"
    else:
        output += "    Nothing\n"

    # Use the passed callback to display output
    display_callback(output.strip())
    return () # Return empty tuple as signal that output was handled

def handle_quit(game_state: GameState, parsed_intent: ParsedIntent) -> None:
    """Handles the QUIT command intent. Returns None to signal quit."""
    # The signal to quit will be returning None instead of a message string.
    return None

def handle_unknown(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles unrecognized commands. Returns key/kwargs tuple."""
    logging.info(f"Unknown command received: '{parsed_intent.raw_input}'")
    # Return key for invalid command response, no kwargs needed for this one
    return ("invalid_command", {}) 