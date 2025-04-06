"""Command handlers for basic game actions like look, inventory, quit."""

import logging
from typing import Optional, Dict, Any
from ..game_state import GameState
from ..command_defs import ParsedIntent
# Note: We need access to get_location_description, so we might import it
# or reconsider if _handle_look belongs here or requires its own module/utils.
# For now, let's assume GameLoop might pass the display_output function if needed.

def handle_look(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles the LOOK command intent.

    Provides a detailed description of the current room or area, 
    or looks at a specific target (placeholder).
    """
    target = parsed_intent.target
    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id # Check area first
    current_room_data = game_state.rooms_data.get(current_room_id)

    if not current_room_data:
        logging.error(f"Look failed: Current room '{current_room_id}' not found in rooms_data!")
        return "An internal error occurred: you seem to be nowhere defined."

    # Simple check if player is looking at the location vs. a specific object
    if not target or target in ["room", "around", "area"]:
        # --- Always show detailed description on explicit LOOK --- 
        # This requires the get_location_description logic. 
        # TODO: Refactor to call get_location_description from movement.py or move it to utils?
        # For now, duplicate minimal logic or return placeholder:
        
        # Let's try getting the description using the existing GameState method temporarily
        # We need a way to force the detailed description.
        # Maybe the GameLoop calls get_location_description directly in this case?
        # For this refactor, let's just return a simplified message.
        # We can refine LOOK later.
        
        loc_name = "current location"
        if current_area_id:
             room_data = game_state.rooms_data.get(current_room_id)
             if room_data and isinstance(room_data.get("areas"), list):
                  for ad in room_data["areas"]:
                       if ad.get("area_id") == current_area_id:
                            loc_name = ad.get("name", current_area_id)
                            break
        elif current_room_data:
            loc_name = current_room_data.get("name", current_room_id)
            
        # Simplified output - Does not handle power state or detailed descriptions yet
        base_desc = f"You look around the {loc_name}."
        # TODO: Add object listing and exit listing here
        return base_desc 
    else:
        # Look at a specific target (placeholder)
        # TODO: Implement logic to find the target (object/NPC/feature) in the room 
        #       and return its description.
        return f"You look closely at the {target}. (Description not implemented)"

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