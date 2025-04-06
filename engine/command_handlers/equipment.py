"""Command handler for equipping and unequipping items."""

import logging
from typing import Tuple, Dict
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name # Import the shared helper
from ..schemas import Object # Import the Object schema

def handle_equip(game_state: GameState, parsed_intent: ParsedIntent) -> Tuple[str, Dict]:
    """Handles EQUIP/UNEQUIP intents. Returns (key, kwargs) tuple."""
    target_item_name = parsed_intent.target
    action_verb = parsed_intent.action or "" # Get action from intent
    # Define verbs that mean 'wear' vs 'remove'
    wear_verbs = {"wear", "equip", "don", "puton", "put"} # Added "put"
    remove_verbs = {"remove", "unequip", "doff", "takeoff", "take"} # Added "take"

    logging.debug(f"[handle_equip] Target: '{target_item_name}', Action: '{action_verb}'")

    if not target_item_name:
        # TODO: Add equip_fail_no_target key
        return ("invalid_command", {}) # Placeholder

    # Determine if the action is WEAR or REMOVE based on the verb
    is_wearing = action_verb.lower() in wear_verbs
    is_removing = action_verb.lower() in remove_verbs

    if is_wearing:
        object_id_to_wear = None
        # Check hand slot FIRST
        held_item_id = game_state.hand_slot
        if held_item_id and item_matches_name(game_state, held_item_id, target_item_name):
            object_id_to_wear = held_item_id
            logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in hand slot.")
        
        # If not in hand, check inventory
        if not object_id_to_wear:
            inventory_item_id = game_state._find_object_id_by_name_in_inventory(target_item_name)
            if inventory_item_id:
                object_id_to_wear = inventory_item_id
                logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in inventory.")

        # Now, attempt to wear if we found an ID
        if object_id_to_wear:
            # Get object data
            object_data = game_state.objects_data.get(object_id_to_wear)
            if not object_data:
                logging.error(f"[handle_equip] Wear target ID '{object_id_to_wear}' has no data!")
                return ("error_internal", {"action": "wear data missing"})
            
            # Use dictionary access
            is_plural = object_data.get('is_plural', False)
            item_name_actual = object_data.get('name', 'unknown object')
            
            result_message = game_state.wear_item(object_id_to_wear)
            logging.debug(f"[handle_equip] wear_item result: {result_message}")
            
            # Map message to key/kwargs
            if "You put on the" in result_message:
                key = "wear_success_plural" if is_plural else "wear_success_singular"
                return (key, {"item_name": item_name_actual})
            elif "cannot wear the" in result_message and "occupies that space" in result_message:
                 # TODO: Extract conflicting item name properly from GameState return
                 conflicting_item_name = "something else" # Placeholder
                 key = "wear_fail_conflict_plural" if is_plural else "wear_fail_conflict_singular"
                 return (key, {"item_name": item_name_actual, "other_item_name": conflicting_item_name})
            elif "cannot wear the" in result_message:
                 key = "wear_fail_not_wearable_plural" if is_plural else "wear_fail_not_wearable_singular"
                 return (key, {"item_name": item_name_actual})
            elif "isn't configured correctly" in result_message:
                 return ("error_internal", {"action": "wear config"})
            else:
                 logging.warning(f"Unexpected message from wear_item: {result_message}")
                 return ("error_internal", {"action": "wear"})
        else:
            # If not found in hands or inventory, check if already worn
            worn_item_id = game_state._find_object_id_by_name_worn(target_item_name)
            if worn_item_id:
                 # Get data for already worn item to check plural status
                 worn_object_data = game_state.objects_data.get(worn_item_id)
                 # Use dictionary access
                 is_plural = worn_object_data.get('is_plural', False) if worn_object_data else False
                 key = "wear_fail_already_wearing_plural" if is_plural else "wear_fail_already_wearing_singular"
                 return (key, {"item_name": target_item_name})
            else:
                 # Cannot determine plural status if item not found anywhere
                 return ("wear_fail_not_have", {"item_name": target_item_name})

    elif is_removing:
        # Find the item in worn items first
        object_id_to_remove = game_state._find_object_id_by_name_worn(target_item_name)
        if not object_id_to_remove:
            # Check inventory *before* giving up
            inventory_item_id = game_state._find_object_id_by_name_in_inventory(target_item_name)
            if inventory_item_id:
                 return ("remove_fail_not_wearing", {"item_name": target_item_name}) # Placeholder
            elif game_state.hand_slot and item_matches_name(game_state, game_state.hand_slot, target_item_name):
                 return ("remove_fail_not_wearing", {"item_name": target_item_name}) # Placeholder
            else:
                return ("remove_fail_not_wearing", {"item_name": target_item_name}) # Placeholder
        # Get data for the item being removed
        object_data = game_state.objects_data.get(object_id_to_remove)
        if not object_data:
            logging.error(f"[handle_equip] Remove target ID '{object_id_to_remove}' has no data!")
            return ("error_internal", {"action": "remove data missing"})
        
        # Use dictionary access
        is_plural = object_data.get('is_plural', False)
        item_name_actual = object_data.get('name', 'unknown object')

        result_message = game_state.remove_item(object_id_to_remove)
        logging.debug(f"[handle_equip] remove_item result: {result_message}")
        
        # Map message to key/kwargs
        if "take off the" in result_message and "hold it" in result_message:
            key = "remove_success_plural" if is_plural else "remove_success_singular"
            return (key, {"item_name": item_name_actual})
        elif "hands are full" in result_message:
            held_item_name = "something" 
            if game_state.hand_slot:
                 held_item_name = game_state._get_object_name(game_state.hand_slot) 
            key = "remove_fail_hands_full_plural" if is_plural else "remove_fail_hands_full_singular"
            return (key, {"item_name": item_name_actual, "held_item_name": held_item_name})
        else:
            logging.warning(f"Unexpected message from remove_item: {result_message}")
            return ("error_internal", {"action": "remove"})

    else:
        # If the NLP parser returned EQUIP intent but the action wasn't recognized
        logging.warning(f"handle_equip received EQUIP intent but unclear action verb: '{action_verb}'")
        return ("invalid_command", {}) # Placeholder 