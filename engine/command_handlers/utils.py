"""Utility functions shared across command handlers."""

import logging
from typing import Optional
from ..game_state import GameState # Relative import from parent directory

def item_matches_name(game_state: GameState, item_id: str, name_to_match: str) -> bool:
    """Checks if the item ID matches the name/synonym/ID provided."""
    if not item_id or not name_to_match:
        return False

    name_lower = name_to_match.lower().strip()

    # Direct ID match (case-insensitive)
    if item_id.lower() == name_lower:
        return True

    # Name/Synonym match - use game_state's object data
    object_data = game_state.get_object_by_id(item_id) # Use get_object_by_id from game_state
    if object_data:
        if object_data.get("name", "").lower() == name_lower:
            return True
        synonyms = object_data.get("synonyms", [])
        # Ensure synonyms are strings before lowercasing
        if isinstance(synonyms, list):
             if name_lower in [str(syn).lower().strip() for syn in synonyms if isinstance(syn, (str, int, float))]:
                 return True
                 
    logging.debug(f"item_matches_name: No match found for ID '{item_id}' and name '{name_to_match}'")
    return False 