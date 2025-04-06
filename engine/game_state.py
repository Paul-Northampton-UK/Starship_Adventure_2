from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime, timedelta
import logging

class PowerState(Enum):
    """Enum for different power states in the game."""
    OFFLINE = "offline"
    EMERGENCY = "emergency"
    MAIN_POWER = "main_power"
    TORCH_LIGHT = "torch_light"

@dataclass
class PlayerStatus:
    """Tracks player's health and status."""
    health: int = 100
    energy: int = 100
    oxygen: int = 100
    radiation: int = 0
    max_health: int = 100
    max_energy: int = 100
    max_oxygen: int = 100
    max_radiation: int = 100

@dataclass
class GameState:
    """Manages the current state of the game."""
    current_room_id: str
    rooms_data: Dict[str, Any]  # Added to store loaded room definitions
    objects_data: Dict[str, Any]  # Added objects_data
    power_state: PowerState
    current_area_id: Optional[str] = None
    inventory: List[str] = None  # List of object IDs
    hand_slot: Optional[str] = None  # Added hand_slot
    worn_items: List[str] = None  # Added worn_items
    visited_rooms: Set[str] = None  # Set of room IDs
    visited_areas: Dict[str, List[str]] = None  # Set of area IDs
    game_flags: Dict[str, bool] = None  # For tracking game progress/puzzles
    player_status: PlayerStatus = None  # Player's health and status
    game_time: datetime = None  # Current game time
    object_states: Dict[str, Dict] = None  # Track object states and positions
    last_save_time: Optional[datetime] = None  # Last time the game was saved

    def __post_init__(self):
        """Initialize collections if they're None."""
        if self.inventory is None:
            self.inventory = []
        if self.worn_items is None:
            self.worn_items = []
        if self.visited_rooms is None:
            self.visited_rooms = set()
        if self.visited_areas is None:
            self.visited_areas = {}
        if self.game_flags is None:
            self.game_flags = {}
        if self.player_status is None:
            self.player_status = PlayerStatus()
        if self.game_time is None:
            self.game_time = datetime.now()
        if self.object_states is None:
            self.object_states = {}

    def visit_room(self, room_id: str) -> None:
        """Mark a room as visited."""
        self.visited_rooms.add(room_id)

    def visit_area(self, area_id: str, room_id: str) -> None:
        """Mark an area within a specific room as visited."""
        if area_id not in self.visited_areas:
            self.visited_areas[area_id] = []
        # Store the room_id to know which room this area visit was in
        # (Prevents marking area X in room A as visited when entering area X in room B)
        # For simplicity now, let's just record the visit. A more complex structure
        # might store (room_id, area_id) tuples or similar.
        if room_id not in self.visited_areas[area_id]: # Avoid duplicates if re-entering
             self.visited_areas[area_id].append(room_id)

    def has_visited_room(self, room_id: str) -> bool:
        """Check if a room has been visited."""
        return room_id in self.visited_rooms

    def has_visited_area(self, area_id: str) -> bool:
        """Check if an area has been visited."""
        return area_id in self.visited_areas

    def add_to_inventory(self, object_id: str) -> None:
        """Add an object to the player's inventory."""
        if object_id not in self.inventory:
            self.inventory.append(object_id)

    def remove_from_inventory(self, object_id: str) -> None:
        """Remove an object from the player's inventory."""
        if object_id in self.inventory:
            self.inventory.remove(object_id)

    def has_object(self, object_id: str) -> bool:
        """Check if the player has a specific object."""
        return object_id in self.inventory

    def set_power_state(self, state: PowerState) -> None:
        """Change the current power state."""
        self.power_state = state

    def set_game_flag(self, flag: str, value: bool = True) -> None:
        """Set a game flag (for tracking puzzles/progress)."""
        self.game_flags[flag] = value

    def get_game_flag(self, flag: str) -> bool:
        """Get the value of a game flag."""
        return self.game_flags.get(flag, False)

    def move_to_room(self, room_id: str) -> None:
        """Move the player to a new room and clears the current area."""
        self.current_room_id = room_id
        # self.visit_room(room_id) # Removed: Visiting is handled by description logic
        # Clear current area when changing rooms
        self.current_area_id = None

    def move_to_area(self, area_id: str) -> None:
        """Move the player to a new area within the current room."""
        self.current_area_id = area_id
        # self.visit_area(area_id) # Removed: Visiting is handled by description logic

    def get_current_location(self) -> tuple[str, Optional[str]]:
        """Get the current room and area IDs."""
        return self.current_room_id, self.current_area_id

    def save_game(self, filename: str) -> None:
        """Save the current game state to a file."""
        save_data = {
            'current_room_id': self.current_room_id,
            'current_area_id': self.current_area_id,
            'power_state': self.power_state.value,
            'inventory': self.inventory,
            'visited_rooms': list(self.visited_rooms),
            'visited_areas': self.visited_areas,
            'game_flags': self.game_flags,
            'player_status': asdict(self.player_status),
            'game_time': self.game_time.isoformat(),
            'object_states': self.object_states,
            'last_save_time': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=4)
        self.last_save_time = datetime.now()

    @classmethod
    def load_game(cls, filename: str) -> 'GameState':
        """Load a game state from a file."""
        with open(filename, 'r') as f:
            save_data = json.load(f)
        
        game_state = cls(current_room_id=save_data['current_room_id'], power_state=PowerState(save_data['power_state']))
        game_state.current_area_id = save_data['current_area_id']
        game_state.inventory = save_data['inventory']
        game_state.visited_rooms = set(save_data['visited_rooms'])
        game_state.visited_areas = save_data['visited_areas']
        game_state.game_flags = save_data['game_flags']
        game_state.player_status = PlayerStatus(**save_data['player_status'])
        game_state.game_time = datetime.fromisoformat(save_data['game_time'])
        game_state.object_states = save_data['object_states']
        game_state.last_save_time = datetime.fromisoformat(save_data['last_save_time'])
        
        return game_state

    def update_player_status(self, health_change: int = 0, energy_change: int = 0,
                           oxygen_change: int = 0, radiation_change: int = 0) -> None:
        """Update player's status values."""
        self.player_status.health = max(0, min(self.player_status.max_health,
                                             self.player_status.health + health_change))
        self.player_status.energy = max(0, min(self.player_status.max_energy,
                                             self.player_status.energy + energy_change))
        self.player_status.oxygen = max(0, min(self.player_status.max_oxygen,
                                             self.player_status.oxygen + oxygen_change))
        self.player_status.radiation = max(0, min(self.player_status.max_radiation,
                                                self.player_status.radiation + radiation_change))

    def advance_game_time(self, minutes: int) -> None:
        """Advance the game time by a specified number of minutes."""
        self.game_time += timedelta(minutes=minutes)
        # Update status based on time passed
        self.update_player_status(
            energy_change=-minutes // 30,  # Lose energy every 30 minutes
            oxygen_change=-minutes // 60   # Lose oxygen every hour
        )

    def set_object_state(self, object_id: str, state: Dict) -> None:
        """Set the state of an object (e.g., locked/unlocked, position)."""
        self.object_states[object_id] = state

    def get_object_state(self, object_id: str) -> Optional[Dict]:
        """Get the current state of an object."""
        return self.object_states.get(object_id)

    def is_object_interacted_with(self, object_id: str) -> bool:
        """Check if an object has been interacted with."""
        return object_id in self.object_states

    def get_player_status(self) -> Dict:
        """Get a dictionary of player's current status."""
        return {
            'health': self.player_status.health,
            'energy': self.player_status.energy,
            'oxygen': self.player_status.oxygen,
            'radiation': self.player_status.radiation,
            'max_health': self.player_status.max_health,
            'max_energy': self.player_status.max_energy,
            'max_oxygen': self.player_status.max_oxygen,
            'max_radiation': self.player_status.max_radiation
        }

    def is_player_alive(self) -> bool:
        """Check if the player is still alive."""
        return (self.player_status.health > 0 and 
                self.player_status.oxygen > 0 and 
                self.player_status.radiation < self.player_status.max_radiation)

    def get_object_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves object data from the stored dictionary."""
        return self.objects_data.get(object_id)

    def _get_object_name(self, object_id: Optional[str]) -> str:
        """Safely gets the object's name or returns a default."""
        if not object_id:
            return "nothing"
        obj_data = self.get_object_by_id(object_id)
        return obj_data.get("name", object_id) if obj_data else object_id # Fallback to ID

    def _find_object_id_by_name_in_location(self, object_name: str) -> Optional[str]:
        """Finds an object ID by name/synonym within the current room or area."""
        normalized_name = object_name.lower().strip()
        logging.debug(f"Searching for '{normalized_name}' in location {self.current_room_id}/{self.current_area_id or 'room'}")

        current_room_data = self.rooms_data.get(self.current_room_id)
        if not current_room_data:
            logging.error(f"Cannot search location: Room data missing for {self.current_room_id}")
            return None

        search_list = []
        # Search current area first if applicable
        if self.current_area_id:
             areas = current_room_data.get("areas", [])
             if isinstance(areas, list):
                 for area in areas:
                     if area.get("area_id") == self.current_area_id:
                         search_list = area.get("area_objects", [])
                         break # Found the area
        else:
            # If not in an area, search room objects using the correct key
            search_list = current_room_data.get("objects_present", []) # Use "objects_present"
            
        # Now search the list (either area_objects or objects_present)
        found_id = None
        if isinstance(search_list, list):
             for item in search_list:
                 # Handle simple string IDs vs object dictionaries
                 object_id = None
                 if isinstance(item, str):
                     object_id = item
                 elif isinstance(item, dict) and 'id' in item:
                     object_id = item['id']
                 
                 if object_id:
                     obj_data = self.get_object_by_id(object_id)
                     if obj_data:
                         name = obj_data.get('name', '').lower()
                         synonyms = [s.lower() for s in obj_data.get('synonyms', [])]
                         # Match ID, name, or synonym
                         if normalized_name == object_id.lower() or normalized_name == name or normalized_name in synonyms:
                             if found_id:
                                 logging.warning(f"Ambiguous object name '{normalized_name}' in location (Matches: {found_id}, {object_id})")
                                 return None # Ambiguous match
                             found_id = object_id
                             logging.debug(f"Found match for '{normalized_name}' in location: {object_id}")
                         
        if not found_id:
             logging.debug(f"Object '{normalized_name}' not found in current location.")
             
        return found_id

    def _find_object_id_by_name_in_inventory(self, item_name_or_id: str) -> Optional[str]:
        """Finds the object ID in the player's inventory by its name, synonym, or ID."""
        normalized_name = item_name_or_id.lower().strip()
        logging.debug(f"Searching inventory for '{normalized_name}'. Inventory: {self.inventory}")
        
        found_id = None
        for object_id in self.inventory:
            item_data = self.get_object_by_id(object_id)
            if not item_data:
                logging.warning(f"Inventory item ID '{object_id}' not found in objects data during search.")
                continue # Skip if data is missing
            
            name = item_data.get('name', '').lower()
            synonyms = [s.lower() for s in item_data.get('synonyms', [])]
            
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in synonyms:
                if found_id:
                    logging.warning(f"Ambiguous item name '{normalized_name}' found in inventory (Matches: {found_id}, {object_id}).")
                    return None # Ambiguous match
                found_id = object_id
                logging.debug(f"Found match for '{normalized_name}' in inventory: {object_id}")

        if not found_id:
            logging.debug(f"Item '{normalized_name}' not found in inventory.")
            
        return found_id

    def _find_object_id_by_name_worn(self, item_name_or_id: str) -> Optional[str]:
        """Finds the object ID of a worn item by its name, synonym, or ID."""
        normalized_name = item_name_or_id.lower().strip()
        logging.debug(f"Searching worn items for '{normalized_name}'. Worn list: {self.worn_items}")
        
        found_id = None
        for object_id in self.worn_items:
            item_data = self.get_object_by_id(object_id)
            if not item_data:
                logging.warning(f"Worn item ID '{object_id}' not found in objects data during search.")
                continue
            
            name = item_data.get('name', '').lower()
            synonyms = [s.lower() for s in item_data.get('synonyms', [])]
            
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in synonyms:
                if found_id:
                    logging.warning(f"Ambiguous item name '{normalized_name}' found in worn items (Matches: {found_id}, {object_id}).")
                    return None
                found_id = object_id
                logging.debug(f"Found match for '{normalized_name}' in worn items: {object_id}")

        if not found_id:
            logging.debug(f"Item '{normalized_name}' not found in worn items.")
            
        return found_id

    def take_object(self, object_id: str) -> str:
        """Moves an object from the location to the player's hand slot."""
        if self.hand_slot is not None:
            # This check should ideally happen in GameLoop before calling
            return f"Your hands are full holding the {self._get_object_name(self.hand_slot)}."

        # Check if object exists in location (redundant if GameLoop checks?)
        # For safety, let's assume GameLoop might not have checked yet.
        if self._find_object_id_by_name_in_location(object_id) != object_id:
             # Attempt lookup by ID directly if name search failed but ID was passed
             if self.get_object_by_id(object_id) and self._find_object_id_by_name_in_location(self._get_object_name(object_id)) == object_id:
                 pass # Object found by ID/name lookup
             else:
                logging.warning(f"take_object called for '{object_id}' not found in location.")
                return f"You don't see a {self._get_object_name(object_id)} here."
        
        object_data = self.get_object_by_id(object_id)
        if not object_data:
             return f"Cannot get data for {object_id}."
             
        if not object_data.get('properties', {}).get('is_takeable', False):
             return f"You cannot take the {self._get_object_name(object_id)}."
        
        # Remove object from room/area
        removed = self._remove_object_from_location(object_id)
        if not removed:
            # This shouldn't happen if find_object_id worked, but handle defensively
            logging.error(f"Failed to remove '{object_id}' from location {self.current_room_id}/{self.current_area_id} after finding it.")
            return f"You try to take the {self._get_object_name(object_id)}, but it seems stuck."

        # Add object to hand slot
        self.hand_slot = object_id
        object_name = self._get_object_name(object_id)
        logging.info(f"Player took '{object_id}' ({object_name}) into hand_slot from location.")
        return f"You take the {object_name}."

    def drop_object(self, object_id: str) -> Dict[str, Any]:
        """Moves an object from hand_slot to the current location."""
        if self.hand_slot != object_id:
            # Check should happen in GameLoop
            return {"success": False, "message": f"You aren't holding the {self._get_object_name(object_id)}."} 

        # Add object to current location (room or area)
        added = self._add_object_to_location(object_id)
        if not added:
             logging.error(f"Failed to add '{object_id}' to location {self.current_room_id}/{self.current_area_id}.")
             return {"success": False, "message": f"You try to drop the {self._get_object_name(object_id)}, but can't find a place for it."} 

        # Clear hand slot
        object_name = self._get_object_name(self.hand_slot)
        self.hand_slot = None
        logging.info(f"Player dropped '{object_id}' ({object_name}) from hand_slot into location.")
        return {"success": True, "message": f"You drop the {object_name}."}

    def wear_item(self, object_id: str) -> str:
        """Attempts to wear an item from inventory OR hand_slot. Checks rules and conflicts."""
        logging.debug(f"Attempting to wear item ID: {object_id}")
        
        # Check 1: Does the object exist?
        item_data = self.get_object_by_id(object_id)
        if not item_data:
            logging.error(f"wear_item: Cannot find data for object ID: {object_id}")
            return "Cannot find data for that item." # Keep generic message for player
            
        item_name = item_data.get("name", object_id) # Use name in messages
        
        # Check 2: Is the player actually holding it or has it in inventory?
        # (The calling function _handle_equip should ensure this, but double check)
        is_in_hands = (self.hand_slot == object_id)
        is_in_inventory = (object_id in self.inventory)
        
        if not is_in_hands and not is_in_inventory:
             logging.warning(f"wear_item: Item {object_id} ({item_name}) not found in hand_slot or inventory.")
             # This message *shouldn't* be reached if _handle_equip works correctly.
             return f"You don't seem to have the {item_name} right now."

        # Check 3: Is it wearable?
        props = item_data.get('properties', {})
        if not props.get('is_wearable'):
            return f"You cannot wear the {item_name}."
            
        # Check 4: Does it have valid wear configuration?
        wear_area = props.get('wear_area')
        wear_layer = props.get('wear_layer')
        if not wear_area or wear_layer is None:
             logging.error(f"wear_item: Item {object_id} ({item_name}) is wearable but missing wear_area or wear_layer.")
             return f"The {item_name} isn't configured correctly for wearing."
             
        # Check 5: Does it conflict with currently worn items?
        for worn_item_id in self.worn_items:
            worn_item_data = self.get_object_by_id(worn_item_id)
            if not worn_item_data: continue # Skip check if data missing for worn item
            worn_props = worn_item_data.get('properties', {})
            worn_area = worn_props.get('wear_area')
            worn_layer = worn_props.get('wear_layer')
            
            # Conflict: Same area, and new item's layer is <= existing item's layer
            if worn_area == wear_area and worn_layer is not None and wear_layer <= worn_layer: # Corrected logic? Assume higher layer goes over lower.
                 worn_item_name = self._get_object_name(worn_item_id)
                 return f"You cannot wear the {item_name} there; you are already wearing the {worn_item_name} which occupies that space/layer."

        # --- All checks passed ---
        
        # Remove from original location (hand or inventory)
        if is_in_hands:
            self.hand_slot = None
            logging.info(f"Item '{object_id}' ({item_name}) removed from hand_slot.")
        elif is_in_inventory:
            self.inventory.remove(object_id)
            logging.info(f"Item '{object_id}' ({item_name}) removed from inventory.")
            
        # Add to worn items
        self.worn_items.append(object_id)
        logging.info(f"Item '{object_id}' ({item_name}) added to worn_items.")
        
        return f"You put on the {item_name}."

    def remove_item(self, object_id: str) -> str:
        """Attempts to remove a worn item and place it in the player's hand_slot."""
        logging.debug(f"Attempting to remove worn item ID: {object_id} into hand_slot.")
        item_name = self._get_object_name(object_id)

        # Check 1: Is the item actually worn?
        if object_id not in self.worn_items:
            # Provide more specific feedback if it's in inventory vs not possessed
            if object_id in self.inventory:
                 return f"You have the {item_name} in your inventory, but you aren't wearing it."
            elif self.hand_slot == object_id:
                 return f"You are holding the {item_name}, not wearing it."
            else:
                 # Check if it exists elsewhere (like location) could be added, but for now:
                 return f"You aren't wearing a {item_name}."

        # Check 2: Is the hand_slot free?
        if self.hand_slot is not None:
            held_item_name = self._get_object_name(self.hand_slot)
            return f"Your hands are full (holding the {held_item_name}). You need to drop it or put it away before taking off the {item_name}."

        # --- All checks passed --- 

        # Remove from worn items
        self.worn_items.remove(object_id)
        
        # Add to hand_slot
        self.hand_slot = object_id
        
        logging.info(f"Item '{object_id}' ({item_name}) moved from worn_items to hand_slot.")
        return f"You take off the {item_name} and hold it."

    def _add_object_to_location(self, object_id: str) -> bool:
        """Adds an object ID to the current room or area's object list."""
        room_data = self.rooms_data.get(self.current_room_id)
        if not room_data:
            logging.error(f"_add_object_to_location: Cannot find room data for {self.current_room_id}")
            return False

        target_list_key = ""
        target_list_container = None
        target_list_index = -1 # Used only for areas

        if self.current_area_id:
            # Add to area_objects
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logging.error(f"_add_object_to_location: Room {self.current_room_id} 'areas' is not a list.")
                return False
            
            found_area = False
            for i, area_data in enumerate(areas):
                if isinstance(area_data, dict) and area_data.get("area_id") == self.current_area_id:
                    target_list_container = area_data
                    target_list_key = "area_objects"
                    target_list_index = i # Store index for potential update
                    found_area = True
                    break
            if not found_area:
                logging.error(f"_add_object_to_location: Cannot find area {self.current_area_id} in room {self.current_room_id}.")
                return False
        else:
            # Add to room's objects_present
            target_list_container = room_data
            target_list_key = "objects_present"

        # Get or create the target list
        if target_list_key not in target_list_container or not isinstance(target_list_container[target_list_key], list):
             target_list_container[target_list_key] = [] # Create if missing or wrong type
             
        target_list = target_list_container[target_list_key]
        
        # Add the object ID (as string) if not already present
        if object_id not in target_list and not any(isinstance(item, dict) and item.get('id') == object_id for item in target_list):
            target_list.append(object_id) # Append simple string ID
            logging.debug(f"Added '{object_id}' to {target_list_key} in {self.current_area_id or self.current_room_id}")
            # We might need to update the original rooms_data structure if areas list was modified
            # If we added to an area list directly from the iterated area_data, it should be reflected.
            return True
        else:
             logging.warning(f"Object '{object_id}' already present in {target_list_key} for {self.current_area_id or self.current_room_id}.")
             return False # Or True if adding duplicates is acceptable?

    def _remove_object_from_location(self, object_id: str) -> bool:
        """Removes an object ID from the current room or area's object list."""
        room_data = self.rooms_data.get(self.current_room_id)
        if not room_data:
            logging.error(f"_remove_object_from_location: Cannot find room data for {self.current_room_id}")
            return False

        target_list_key = ""
        target_list_container = None
        target_list_index = -1 # Only used for areas

        if self.current_area_id:
            # Remove from area_objects
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logging.error(f"_remove_object_from_location: Room {self.current_room_id} 'areas' is not a list.")
                return False
                
            found_area = False
            for i, area_data in enumerate(areas):
                 if isinstance(area_data, dict) and area_data.get("area_id") == self.current_area_id:
                     target_list_container = area_data
                     target_list_key = "area_objects"
                     target_list_index = i
                     found_area = True
                     break
            if not found_area:
                 logging.error(f"_remove_object_from_location: Cannot find area {self.current_area_id} in room {self.current_room_id}.")
                 return False
        else:
            # Remove from room's objects_present
            target_list_container = room_data
            target_list_key = "objects_present"

        # Check if the list exists and is a list
        if target_list_key not in target_list_container or not isinstance(target_list_container[target_list_key], list):
             logging.warning(f"_remove_object_from_location: List '{target_list_key}' not found or not a list in {self.current_area_id or self.current_room_id}.")
             return False

        target_list = target_list_container[target_list_key]
        original_length = len(target_list)

        # Create a new list excluding the object_id (handles both str and dict formats)
        new_list = [item for item in target_list if not (isinstance(item, str) and item == object_id) and 
                                                      not (isinstance(item, dict) and item.get('id') == object_id)]

        if len(new_list) < original_length:
            # Update the list in the container
            target_list_container[target_list_key] = new_list
            logging.debug(f"Removed '{object_id}' from {target_list_key} in {self.current_area_id or self.current_room_id}")
            # Again, modification should be reflected if container was area_data
            return True
        else:
            logging.warning(f"_remove_object_from_location: Object '{object_id}' not found in list '{target_list_key}' for {self.current_area_id or self.current_room_id}.")
            return False 