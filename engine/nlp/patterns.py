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
        # Standard Directions
        "north", "south", "east", "west", "up", "down", 
        "n", "s", "e", "w", "u", "d", 
        "ne", "nw", "se", "sw",
        "northeast", "northwest", "southeast", "southwest",
        # Hyphenated (handled specifically below)
        "north-east", "north-west", "south-east", "south-west", 
        # Two-word 
        "north east", "north west", "south east", "south west" 
    ]
    
    # Specific patterns for hyphenated directions
    hyphenated_patterns = {
        "north-east": [{"LOWER": "north"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "east"}],
        "north-west": [{"LOWER": "north"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "west"}],
        "south-east": [{"LOWER": "south"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "east"}],
        "south-west": [{"LOWER": "south"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "west"}],
    }
    for text, pattern in hyphenated_patterns.items():
         logging.debug(f"Adding hyphenated DIRECTION pattern: {pattern}")
         custom_patterns.append({"label": "DIRECTION", "pattern": pattern, "id": text.replace('-', '')}) # Store normalized ID

    # Patterns for other directions (single word, abbreviations, two-word)
    for direction in direction_list:
        direction_lower = direction.lower()
        
        if '-' in direction_lower: # Skip hyphenated, handled above
            continue

        if ' ' in direction_lower: # Handle two-word
             parts = direction_lower.split()
             pattern = [{spacy.symbols.LOWER: part} for part in parts]
             normalized_id = direction_lower.replace(' ','')
        else: # Handle single word/abbreviation
             pattern = [{spacy.symbols.LOWER: direction_lower}]
             normalized_id = direction_lower
        
        if pattern:
             logging.debug(f"Adding standard/multi-word DIRECTION pattern: {pattern}")
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
        
    logging.debug(f"Finished generating custom patterns. Total: {len(custom_patterns)}")
    return custom_patterns 