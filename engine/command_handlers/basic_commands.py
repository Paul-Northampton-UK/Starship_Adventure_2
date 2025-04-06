"""Command handlers for basic game actions like look, inventory, quit."""

import logging
from typing import Optional, Dict, Any
from ..game_state import GameState
from ..command_defs import ParsedIntent
# Note: We need access to get_location_description, so we might import it
# or reconsider if _handle_look belongs here or requires its own module/utils.
# For now, let's assume GameLoop might pass the display_output function if needed.

# Import the enhanced description function
from .movement import get_location_description 

def handle_look(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles the LOOK command intent.

    Provides a detailed description of the current room or area by calling
    get_location_description, or looks at a specific target (placeholder).
    """
    target = parsed_intent.target
    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id 

    # Simple check if player is looking at the location vs. a specific object
    if not target or target.lower() in ["room", "around", "area", "here"]:
        # Always show detailed description on explicit LOOK
        # Call the main description function from movement handler
        return get_location_description(game_state, current_room_id, current_area_id)
    else:
        # Look at a specific target (placeholder)
        # TODO: Implement logic to find the target (object/NPC/feature) in the room/area 
        #       and return its description.
        target_object_id = game_state._find_object_id_by_name_in_location(target)
        if target_object_id:
             target_data = game_state.get_object_by_id(target_object_id)
             if target_data:
                 # Use detailed description if available, else default
                 # TODO: Add state-dependent descriptions?
                 obj_desc = target_data.get("description", f"You see nothing special about the {target_data.get('name', target)}.")
                 return obj_desc
             else:
                 return f"You see the {target}, but details are missing."
        else:
             # Check inventory/worn/held
             inv_id = game_state._find_object_id_by_name_in_inventory(target)
             worn_id = game_state._find_object_id_by_name_worn(target)
             
             # Check hand slot using item_matches_name
             held_id = None
             # We need the item_matches_name function here!
             # It was moved to utils.py, need to import it.
             from .utils import item_matches_name 
             if game_state.hand_slot and item_matches_name(game_state, game_state.hand_slot, target):
                 held_id = game_state.hand_slot

             obj_id_to_describe = inv_id or worn_id or held_id # Prioritize inv/worn if ambiguous? Or handle ambiguity?
             
             if obj_id_to_describe:
                 target_data = game_state.get_object_by_id(obj_id_to_describe)
                 if target_data:
                     # Use detailed description if available, else default
                     obj_desc = target_data.get("description", f"You examine your {target_data.get('name', target)}. Nothing seems out of the ordinary.")
                     return obj_desc
                 else:
                     # This case means the ID exists in inv/worn/held but not in objects_data (shouldn't happen)
                     logging.error(f"handle_look: Found ID {obj_id_to_describe} in player possession but missing from objects_data.")
                     return f"You have the {target}, but its details seem corrupted."

             # If not found anywhere
             return f"You don't see a {target} here, nor are you carrying or wearing one."

def handle_inventory(game_state: GameState, parsed_intent: ParsedIntent, display_callback) -> str:
    """Handles the INVENTORY command intent by displaying status via callback."""
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
    return "" # Return empty string as message is displayed via callback

def handle_quit(game_state: GameState, parsed_intent: ParsedIntent) -> Optional[str]:
    """Handles the QUIT command intent. Returns None to signal quit."""
    # The signal to quit will be returning None instead of a message string.
    # The main loop will check for this.
    return None
     
def handle_unknown(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles unrecognized commands."""
    # Log the unrecognized input for potential NLP tuning
    logging.info(f"Unknown command received: '{parsed_intent.raw_input}'") 
    return "I don't understand that command." 