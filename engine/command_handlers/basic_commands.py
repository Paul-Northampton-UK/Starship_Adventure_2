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
    target_object_id_from_parser = parsed_intent.target_object_id # Get the resolved ID

    current_room_id = game_state.current_room_id
    current_area_id = game_state.current_area_id

    logging.debug(f"[handle_look in basic_commands] Target Name: '{target_name}', Target ID from Parser: '{target_object_id_from_parser}'")

    if not target_name and not target_object_id_from_parser:
        # Look at the current room/area - Force the long description
        desc_str = get_location_description(game_state, current_room_id, current_area_id, force_long_description=True)
        return [{'key': "look_success_room", 'data': {"description": desc_str}}]
    else:
        # Player is looking AT something specific.
        obj_data_to_describe: Optional[Dict[str, Any]] = None
        obj_id_for_description: Optional[str] = None
        found_in_source: str = "unknown"

        # Priority 1: Use the ID from the parser if available
        if target_object_id_from_parser:
            # Check hand slot by ID
            if target_object_id_from_parser in game_state.hand_slot:
                obj_id_for_description = target_object_id_from_parser
                found_in_source = "hand_slot (by ID)"
                logging.debug(f"[handle_look] Found '{target_object_id_from_parser}' in hand_slot by ID.")
            
            # Check worn items by ID
            if not obj_id_for_description:
                if target_object_id_from_parser in game_state.worn_items: # worn_items is List[str]
                    obj_id_for_description = target_object_id_from_parser
                    found_in_source = "worn_items (by ID)"
                    logging.debug(f"[handle_look] Found '{target_object_id_from_parser}' in worn_items by ID.")

            # Check location by ID (if not found in hands/worn)
            if not obj_id_for_description:
                # Check if this ID is visible in the current location
                # This requires checking if the object_id is in the set of all visible objects in the location
                all_visible_in_loc = game_state._get_all_object_ids_in_current_location(visible_only=True)
                if target_object_id_from_parser in all_visible_in_loc:
                    obj_id_for_description = target_object_id_from_parser
                    found_in_source = "location (by ID)"
                    logging.debug(f"[handle_look] Found '{target_object_id_from_parser}' in location by ID (was visible).")
        
        # Priority 2: If no ID from parser OR ID not found in hands/worn/location by ID, try finding by name in location.
        if not obj_id_for_description and target_name:
            logging.debug(f"[handle_look] ID '{target_object_id_from_parser}' not confirmed or no ID from parser. Searching location for name: '{target_name}'")
            # This is the call that was causing the error
            obj_id_found_in_room_by_name = game_state.find_object_id_by_name_in_location(
                object_name=target_name,
                room_id=current_room_id,
                area_id=current_area_id,
                visible_only=True # Standard for "look at"
            )
            if obj_id_found_in_room_by_name:
                obj_id_for_description = obj_id_found_in_room_by_name
                found_in_source = "location (by name)"
                logging.debug(f"[handle_look] Found '{obj_id_for_description}' in location by name '{target_name}'.")

        # Now, if we have an obj_id_for_description, get its data and format description
        if obj_id_for_description:
            obj_data_to_describe = game_state.get_object_by_id(obj_id_for_description)
            if obj_data_to_describe:
                # Base description
                description = obj_data_to_describe.get("detailed_description", 
                                                     obj_data_to_describe.get("description"))
                if not description: # Fallback if no description fields
                    description = f"You see a {obj_data_to_describe.get('name', 'mysterious object')}."
                else: # Ensure the name is part of the description if using detailed_description
                    if obj_data_to_describe.get('name') and obj_data_to_describe.get('name').lower() not in description.lower() :
                         description = f"It's {game_state._get_object_name(obj_id_for_description)}. {description}"


                # Add stateful descriptions
                obj_state = game_state.get_object_state(obj_id_for_description)
                properties = obj_data_to_describe.get("properties", {})

                if properties.get("is_openable_closable"):
                    description += " It is currently " + ("open." if obj_state.get("is_open") else "closed.")
                
                # Check for lock_details in state first, then base data for lockable property
                is_lockable_prop = properties.get("is_lockable", False) # From YAML properties
                has_lock_type = bool(obj_data_to_describe.get("lock_type")) # From YAML direct
                
                if is_lockable_prop or has_lock_type:
                    lock_details_state = obj_state.get("lock_details", {})
                    # Fallback to base data's is_locked if not in runtime state (should be initialized by get_object_state)
                    is_obj_locked_runtime = lock_details_state.get("locked", obj_data_to_describe.get("is_locked", False))
                    description += " It appears to be " + ("locked." if is_obj_locked_runtime else "unlocked.")
                
                # Example: if it's a container and open, list contents? (Optional, can make descriptions long)
                if properties.get("is_storage") and obj_state.get("is_open"):
                    contained_item_ids = obj_state.get("contains", [])
                    if contained_item_ids:
                        item_names = [game_state._get_object_name(item_id) for item_id in contained_item_ids]
                        if item_names:
                             description += f" Inside, you see: {', '.join(item_names)}."
                        else: # Should not happen if IDs are present, but good fallback
                             description += " It's empty."
                    else:
                        description += " It's empty."
                
                logging.debug(f"[handle_look] Describing '{obj_data_to_describe.get('name')}' (ID: {obj_id_for_description}, Found in: {found_in_source}). Desc: {description[:100]}...")
                return [{'key': "look_success_item", 'data': {"item_name": obj_data_to_describe.get('name', target_name), "description": description}}]
            else:
                logging.error(f"Look target ID \'{obj_id_for_description}\' (found via {found_in_source} for name \'{target_name}\') but its data is missing.")
                return [{'key': "error_internal", 'data': {'action': "look data missing for " + obj_id_for_description}}]
        else:
            # Item not found anywhere
            final_search_term = target_name or target_object_id_from_parser or "something"
            logging.warning(f"[handle_look] FAILED - Target '{final_search_term}' not found after checking by ID (hands, worn, location) and by name (location).")
            return [{'key': "look_fail_not_found", 'data': {"item_name": final_search_term}}]

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