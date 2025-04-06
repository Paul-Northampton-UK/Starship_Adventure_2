"""Command handlers for taking and dropping items."""

import logging
from typing import Tuple, Dict
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name
from ..schemas import Object # Import the Object schema

def handle_take(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the TAKE command intent. Returns (key, kwargs) tuple."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_take] Handling TAKE for target name: '{target_object_name}'")

    if not target_object_name:
        # TODO: Add take_fail_no_target key to responses.yaml
        return ("invalid_command", {}) # Placeholder

    # Check if hands are free *first*
    if game_state.hand_slot is not None:
        held_item_name = game_state._get_object_name(game_state.hand_slot)
        return ("take_fail_hands_full", {"held_item_name": held_item_name, "item_name": target_object_name})

    # Find the object in the location
    found_object_id = game_state._find_object_id_by_name_in_location(target_object_name)
    if not found_object_id:
        logging.debug(f"[handle_take] No object ID found for name '{target_object_name}'.")
        return ("take_fail_no_item", {"item_name": target_object_name})

    # Get object data to check its properties
    object_data = game_state.objects_data.get(found_object_id)
    if not object_data:
        logging.error(f"[handle_take] Found object ID '{found_object_id}' but no data exists in objects_data!")
        return ("error_internal", {"action": "take data missing"})

    # Use dictionary access
    is_plural = object_data.get('is_plural', False)
    item_name = object_data.get('name', 'unknown object') # Use .get() for safety

    # Call GameState.take_object 
    logging.debug(f"[handle_take] Calling GameState.take_object with ID: '{found_object_id}'")
    result_message = game_state.take_object(found_object_id)
    logging.debug(f"[handle_take] take_object returned: {result_message}")

    # Map GameState message to response key/kwargs
    if "You take the" in result_message:
        key = "take_success_plural" if is_plural else "take_success_singular"
        return (key, {"item_name": item_name})
    elif "cannot take" in result_message:
        # Determine if it's just not takeable or needs a specific action (e.g., unlock)
        # For now, use a generic non-takeable key
        key = "take_fail_not_takeable_plural" if is_plural else "take_fail_not_takeable_singular"
        return (key, {"item_name": item_name})
    elif "hands are full" in result_message: # Should be caught above, but as fallback
        held_item_id = game_state.hand_slot
        held_item_name = game_state._get_object_name(held_item_id) if held_item_id else "something"
        return ("take_fail_hands_full", {"held_item_name": held_item_name, "item_name": target_object_name})
    elif "seems stuck" in result_message:
        return ("error_internal", {"action": "take stuck"})
    else: # Default for unexpected messages from take_object
        logging.warning(f"Unexpected message from take_object: {result_message}")
        return ("error_internal", {"action": "take"})


def handle_drop(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles the DROP command intent. Returns (key, kwargs) tuple."""
    target_object_name = parsed_intent.target
    logging.debug(f"[handle_drop] Handling DROP for target name: '{target_object_name}'")

    if not target_object_name:
        # TODO: Add drop_fail_no_target key to responses.yaml
        return ("invalid_command", {}) # Placeholder

    held_object_id = game_state.hand_slot
    if held_object_id is None:
        # Check if they named an item they *possess* but aren't holding
        inv_id = game_state._find_object_id_by_name_in_inventory(target_object_name)
        worn_id = game_state._find_object_id_by_name_worn(target_object_name)
        if inv_id or worn_id:
             # TODO: Add drop_fail_possess_not_holding key to responses.yaml
             return("drop_fail_not_holding", {"item_name": target_object_name or "anything"})
        else:
             # TODO: Add drop_fail_not_holding_anything key to responses.yaml
             return ("drop_fail_not_holding", {"item_name": "anything"})

    # Get data for the item being held
    held_object_data = game_state.objects_data.get(held_object_id)
    if not held_object_data:
        logging.error(f"[handle_drop] Holding object ID '{held_object_id}' but no data exists in objects_data!")
        return ("error_internal", {"action": "drop data missing"})

    # Use dictionary access
    is_plural = held_object_data.get('is_plural', False)
    held_item_name = held_object_data.get('name', 'unknown object')

    # Use item_matches_name helper to check if the held item matches the target name
    if not item_matches_name(game_state, held_object_id, target_object_name):
         # TODO: Add drop_fail_target_mismatch key to responses.yaml
         # The message should maybe state what you *are* holding vs what you tried to drop
         key = "drop_fail_target_mismatch_plural" if is_plural else "drop_fail_target_mismatch_singular"
         return (key, {"item_name": target_object_name, "held_item_name": held_item_name})

    # If it matches, proceed to drop the item in hand
    logging.debug(f"[handle_drop] Calling GameState.drop_object with ID: '{held_object_id}'")
    result_dict = game_state.drop_object(held_object_id) # Returns dict now
    logging.debug(f"[handle_drop] drop_object returned: {result_dict}")

    success = result_dict.get("success", False)

    if success:
        key = "drop_success_plural" if is_plural else "drop_success_singular"
        return (key, {"item_name": held_item_name})
    else:
        return ("error_internal", {"action": "drop failed"}) 