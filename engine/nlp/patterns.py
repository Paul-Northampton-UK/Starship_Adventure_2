"""Functions for generating NLP entity patterns."""

import logging
from typing import List, Dict, Any, Set
import spacy # Needed for spacy.symbols
from ..game_state import GameState # Import GameState for accessing object data

def generate_patterns(game_state: GameState) -> List[Dict[str, Any]]:
    """Builds and returns the list of custom entity patterns for the Entity Ruler."""
    custom_patterns: List[Dict[str, Any]] = []
    logging.debug("Generating custom entity patterns...")

    # --- Define Direction Patterns --- 
    direction_list = [
        # Tuples: (Input variations, Normalized ID)
        (("north", "n"), "north"),
        (("south", "s"), "south"),
        (("east", "e"), "east"),
        (("west", "w"), "west"),
        (("up", "u"), "up"),
        (("down", "d"), "down"),
        (("northeast", "north east", "north-east", "ne"), "northeast"),
        (("northwest", "north west", "north-west", "nw"), "northwest"),
        (("southeast", "south east", "south-east", "se"), "southeast"),
        (("southwest", "south west", "south-west", "sw"), "southwest"),
    ]
    
    # Generate patterns for all variations, mapping to the normalized ID
    for variations, normalized_id in direction_list:
        for direction_text in variations:
            direction_lower = direction_text.lower()
            pattern = []
            
            # Handle specific hyphenated case
            if '-' in direction_lower:
                 parts = direction_lower.split('-')
                 if len(parts) == 2:
                     pattern = [{spacy.symbols.LOWER: parts[0]}, {"IS_PUNCT": True, "ORTH": "-"}, {spacy.symbols.LOWER: parts[1]}]
                 else: continue # Skip invalid hyphenated formats
            # Handle two-word case
            elif ' ' in direction_lower:
                 parts = direction_lower.split()
                 pattern = [{spacy.symbols.LOWER: part} for part in parts]
            # Handle single word/abbreviation
            else:
                 pattern = [{spacy.symbols.LOWER: direction_lower}]
            
            if pattern:
                 logging.debug(f"Adding DIRECTION pattern: {pattern} -> ID: {normalized_id}")
                 custom_patterns.append({"label": "DIRECTION", "pattern": pattern, "id": normalized_id})

    # --- Define GAME_OBJECT Patterns --- 
    logging.debug("Adding GAME_OBJECT patterns...")
    if not game_state or not game_state.objects_data:
        logging.warning("Cannot generate GAME_OBJECT patterns: game_state or objects_data is missing.")
    else:
        for obj_id, obj_data in game_state.objects_data.items():
            names_to_pattern: Set[str] = set()
            # Add the primary name
            primary_name = obj_data.get('name')
            if primary_name and isinstance(primary_name, str):
                 names_to_pattern.add(primary_name.lower())
            # Add command aliases
            aliases = obj_data.get('command_aliases', [])
            if isinstance(aliases, list):
                 for alias in aliases:
                      if isinstance(alias, str):
                           names_to_pattern.add(alias.lower())

            for name in names_to_pattern:
                 if name: # Ensure name is not empty
                     # Simple pattern based on lower case name tokens
                     pattern = [{spacy.symbols.LOWER: token.lower()} for token in name.split()]
                     if pattern:
                          # Add the object ID to the pattern for easy retrieval later
                          custom_patterns.append({
                               "label": "GAME_OBJECT", 
                               "pattern": pattern, 
                               "id": obj_id # Store the actual object ID here
                          })
                          logging.debug(f"Added GAME_OBJECT pattern for ID '{obj_id}': {pattern}")
        
    # --- Define AREA Patterns --- 
    logging.debug("Adding AREA patterns...")
    if not game_state or not game_state.rooms_data:
        logging.warning("Cannot generate AREA patterns: game_state or rooms_data is missing.")
    else:
        for room_id, room_data in game_state.rooms_data.items():
            areas = room_data.get("areas", [])
            if isinstance(areas, list):
                for area_data in areas:
                    if isinstance(area_data, dict):
                        area_id = area_data.get("area_id")
                        # TODO: Add area_name and area_aliases later if needed
                        names_to_pattern: Set[str] = set()
                        if area_id and isinstance(area_id, str):
                            names_to_pattern.add(area_id.lower()) # Use area_id as pattern for now
                            # Add simple abbreviation if ID contains underscore?
                            if '_' in area_id:
                                parts = area_id.split('_')
                                if len(parts) > 1:
                                     # Simple abbreviation like 'nav' from 'navigation_station'
                                     # Be careful this doesn't conflict!
                                     abbr = parts[0][:3] # e.g., 'nav' 
                                     names_to_pattern.add(abbr.lower())
                        
                        for name in names_to_pattern:
                             if name:
                                 pattern = [{spacy.symbols.LOWER: token.lower()} for token in name.split()]
                                 if pattern:
                                     custom_patterns.append({
                                         "label": "AREA", 
                                         "pattern": pattern, 
                                         "id": area_id # Store the actual area ID
                                     })
                                     logging.debug(f"Added AREA pattern for ID '{area_id}': {pattern}")
            # else: Room has no areas list or it's invalid
        
    logging.debug(f"Finished generating custom patterns. Total: {len(custom_patterns)}")
    return custom_patterns 