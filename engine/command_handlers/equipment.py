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
        source_container_id = None # Track if found in a container

        # Check hand slot FIRST
        match_in_hand = None
        for held_id in game_state.hand_slot:
            if item_matches_name(game_state, held_id, target_item_name):
                match_in_hand = held_id
                break # Found a match in hand
                
        if match_in_hand:
            object_id_to_wear = match_in_hand
            logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in hand slot.")
        
        # If not in hand, check worn containers SECOND
        if not object_id_to_wear:
            logging.debug(f"[handle_equip] Item not in hand slot. Checking worn containers...")
            for worn_container_id in game_state.worn_items:
                container_data = game_state.get_object_by_id(worn_container_id)
                if container_data and container_data.get('properties', {}).get('is_storage'):
                    container_state = game_state.get_object_state(worn_container_id)
                    if container_state and 'contains' in container_state:
                        logging.debug(f"[handle_equip] Checking container {worn_container_id} with contents: {container_state['contains']}")
                        # Find item within container's 'contains' list
                        for item_id_in_container in container_state['contains']:
                            if item_matches_name(game_state, item_id_in_container, target_item_name):
                                object_id_to_wear = item_id_in_container
                                source_container_id = worn_container_id # Remember where we found it
                                logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) inside worn container '{source_container_id}'.")
                                break # Found the item in this container
                        if object_id_to_wear:
                            break # Found the item, stop checking containers
                    else:
                        logging.debug(f"[handle_equip] Worn item {worn_container_id} is storage but has no state or 'contains' key.")
                # else: Not storage or no data, skip

        # If not in hand or worn containers, check HELD containers THIRD
        if not object_id_to_wear:
            logging.debug(f"[handle_equip] Item not in worn containers. Checking held containers...")
            for held_container_id in game_state.hand_slot:
                # Avoid trying to wear the container itself if it matches target name by mistake
                if held_container_id == object_id_to_wear: continue 
                
                container_data = game_state.get_object_by_id(held_container_id)
                # Ensure it's storage and NOT the item we're trying to wear
                if container_data and container_data.get('properties', {}).get('is_storage'):
                    container_state = game_state.get_object_state(held_container_id) or {}
                    if container_state and 'contains' in container_state:
                        logging.debug(f"[handle_equip] Checking HELD container {held_container_id} with contents: {container_state['contains']}")
                        for item_id_in_container in container_state['contains']:
                            if item_matches_name(game_state, item_id_in_container, target_item_name):
                                object_id_to_wear = item_id_in_container
                                source_container_id = held_container_id # Remember where we found it (now could be held or worn)
                                logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) inside HELD container '{source_container_id}'.")
                                break
                        if object_id_to_wear:
                            break 
                    # else: Held container empty or no state
                # else: Held item not storage

        # If not found anywhere yet, check general inventory FOURTH (less likely path now)
        if not object_id_to_wear:
            logging.debug(f"[handle_equip] Item not in hand, worn, or held containers. Checking inventory...")
            inventory_item_id = game_state._find_object_id_by_name_in_inventory(target_item_name)
            if inventory_item_id:
                object_id_to_wear = inventory_item_id
                logging.debug(f"[handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in inventory.")

        # Now, attempt to wear if we found an ID
        if object_id_to_wear:
            # Get object data (we need this regardless of source)
            object_data = game_state.get_object_by_id(object_id_to_wear)
            if not object_data:
                logging.error(f"[handle_equip] Wear target ID '{object_id_to_wear}' has no data!")
                return ("error_internal", {"action": "wear data missing"})
            
            # Use dictionary access
            is_plural = object_data.get('is_plural', False)
            item_name_actual = object_data.get('name', 'unknown object')
            
            result_message = ""
            if source_container_id:
                # Call the new GameState method for wearing from a container
                result_message = game_state.wear_item_from_container(object_id_to_wear, source_container_id)
                logging.debug(f"[handle_equip] wear_item_from_container result: {result_message}")
            else:
                # Call the original GameState method for wearing from hand/inventory
                result_message = game_state.wear_item(object_id_to_wear)
                logging.debug(f"[handle_equip] wear_item result: {result_message}")
            
            # Map message to key/kwargs (using item_name_actual identified above)
            if "You put on the" in result_message:
                 key = "wear_success_plural" if is_plural else "wear_success_singular"
                 return (key, {"item_name": item_name_actual})
            # Add check for the specific success message from wear_item_from_container
            elif "You take the" in result_message and "and put it on" in result_message:
                 key = "wear_from_container_success_plural" if is_plural else "wear_from_container_success_singular"
                 # We need the container name for the response template
                 container_name = game_state._get_object_name(source_container_id) # Get container name from ID
                 return (key, {"item_name": item_name_actual, "container_name": container_name})
            elif "cannot wear the" in result_message and "occupies that space" in result_message:
                 # Extract conflicting item name from the message like:
                 # "You cannot wear the {item_name} there; you are already wearing the {worn_item_name} which occupies that space/layer."
                 try:
                    # Find the part after "wearing the " and before " which occupies"
                    start_index = result_message.index("wearing the ") + len("wearing the ")
                    end_index = result_message.index(" which occupies that space/layer.")
                    conflicting_item_name = result_message[start_index:end_index]
                 except ValueError:
                    logging.warning(f"Could not extract conflicting item name from message: {result_message}")
                    conflicting_item_name = "something else" # Fallback
                 key = "wear_fail_conflict_plural" if is_plural else "wear_fail_conflict_singular"
                 return (key, {"item_name": item_name_actual, "other_item_name": conflicting_item_name})
            elif "cannot wear the" in result_message:
                 key = "wear_fail_not_wearable_plural" if is_plural else "wear_fail_not_wearable_singular"
                 return (key, {"item_name": item_name_actual})
            elif "isn't configured correctly" in result_message:
                 return ("error_internal", {"action": "wear config"})
            # Handle potential failure from wear_item_from_container (e.g., container not found?)
            elif "Cannot find container" in result_message: # Example - adjust based on GameState implementation
                 return ("error_internal", {"action": "wear container missing"})
            else:
                 logging.warning(f"Unexpected message from wear attempt: {result_message}")
                 return ("error_internal", {"action": "wear general fail"})
        else:
            # If not found anywhere (hands, containers, inventory), check if already worn
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
            match_in_hand = None
            for held_id in game_state.hand_slot:
                 if item_matches_name(game_state, held_id, target_item_name):
                      match_in_hand = held_id
                      break
            if match_in_hand:
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
            held_items_str = "something you are holding"
            if game_state.hand_slot:
                 held_items_str = " and ".join([game_state._get_object_name(item) or "something" for item in game_state.hand_slot])
            key = "remove_fail_hands_full_plural" if is_plural else "remove_fail_hands_full_singular"
            return (key, {"item_name": item_name_actual, "held_item_name": held_items_str})
        else:
            logging.warning(f"Unexpected message from remove_item: {result_message}")
            return ("error_internal", {"action": "remove"})

    else:
        # If the NLP parser returned EQUIP intent but the action wasn't recognized
        logging.warning(f"handle_equip received EQUIP intent but unclear action verb: '{action_verb}'")
        return ("invalid_command", {}) # Placeholder 