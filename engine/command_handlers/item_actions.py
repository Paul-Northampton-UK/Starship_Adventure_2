"""Command handlers for taking and dropping items."""

import logging
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name

def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles the TAKE command intent, moving object to hand_slot."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_take] Handling TAKE for target name: '{target_object_name}'")

    if not target_object_name:
        return "What do you want to take?"

    # Check if hands are free *first*
    if game_state.hand_slot is not None:
        held_object_name = game_state._get_object_name(game_state.hand_slot)
        return f"Your hands are full (holding the {held_object_name}). You need to drop it or put it away first."

    # Find the object in the location
    found_object_id = game_state._find_object_id_by_name_in_location(target_object_name)
    if not found_object_id:
        logging.debug(f"[handle_take] No object ID found for name '{target_object_name}'. Returning 'not seen' message.")
        return f"You don't see a {target_object_name} here."
    
    # Call GameState.take_object (which handles takeability checks etc.)
    logging.debug(f"[handle_take] Calling GameState.take_object with ID: '{found_object_id}'")
    result = game_state.take_object(found_object_id)
    logging.debug(f"[handle_take] take_object returned: {result}")
    
    # The take_object method now returns a message string directly
    return result 
     
def handle_drop(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles the DROP command intent, checking hand slot."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_drop] Handling DROP for target name: '{target_object_name}'")

    if not target_object_name:
        return "What do you want to drop?"

    held_object_id = game_state.hand_slot
    if held_object_id is None:
        return "You aren't holding anything to drop."

    # Use item_matches_name helper to check if the held item matches the target name
    if not item_matches_name(game_state, held_object_id, target_object_name):
         held_object_name = game_state._get_object_name(held_object_id)
         return f"You aren't holding a {target_object_name}. You're holding the {held_object_name}."

    # If it matches, proceed to drop the item in hand
    object_id_to_drop = held_object_id 
    logging.debug(f"[handle_drop] Calling GameState.drop_object with ID: '{object_id_to_drop}'")
    result = game_state.drop_object(object_id_to_drop)
    logging.debug(f"[handle_drop] drop_object returned: {result}")
    
    # drop_object returns a dictionary {"success": bool, "message": str}
    return result.get("message", "An unknown error occurred while trying to drop the object.") 