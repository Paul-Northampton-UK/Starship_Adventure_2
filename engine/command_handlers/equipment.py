"""Command handler for equipping and unequipping items."""

import logging
from ..game_state import GameState
from ..command_defs import ParsedIntent
from .utils import item_matches_name # Import the shared helper

def handle_equip(game_state: GameState, parsed_intent: ParsedIntent) -> str:
    """Handles EQUIP/UNEQUIP intents by calling wear_item or remove_item."""
    target_item_name = parsed_intent.target
    action_verb = parsed_intent.action or "" # Get action from intent
    # Define verbs that mean 'wear' vs 'remove'
    wear_verbs = {"wear", "equip", "don", "puton", "put"} # Added "put"
    remove_verbs = {"remove", "unequip", "doff", "takeoff", "take"} # Added "take"

    logging.debug(f"[handle_equip] Handling EQUIP. Target: '{target_item_name}', Action: '{action_verb}'")

    if not target_item_name:
        return "What do you want to wear or remove?"

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
            return game_state.wear_item(object_id_to_wear)
        else:
            # If not found in hands or inventory, check if already worn
            worn_item_id = game_state._find_object_id_by_name_worn(target_item_name) # Renamed for clarity
            if worn_item_id:
                 return f"You are already wearing the {target_item_name}."
            else:
                 # Only reach here if not in hands, inventory, or worn
                 return f"You don't have a '{target_item_name}' to wear (checked hands and inventory)."

    elif is_removing:
        # Find the item in worn items first
        object_id_to_remove = game_state._find_object_id_by_name_worn(target_item_name)
        if not object_id_to_remove:
            # Check inventory *before* giving up
            inventory_item_id = game_state._find_object_id_by_name_in_inventory(target_item_name)
            if inventory_item_id:
                 return f"You have the {target_item_name} in your inventory, but you aren't wearing it."
            elif game_state.hand_slot and item_matches_name(game_state, game_state.hand_slot, target_item_name):
                 return f"You are holding the {target_item_name}, not wearing it."
            else:
                return f"You aren't wearing a '{target_item_name}' and don't seem to have one."
        # Attempt to remove
        return game_state.remove_item(object_id_to_remove)

    else:
        # If the NLP parser returned EQUIP intent but the action wasn't recognized
        logging.warning(f"handle_equip received EQUIP intent but unclear action verb: '{action_verb}'")
        return f"Do you want to wear or remove the {target_item_name}?" 