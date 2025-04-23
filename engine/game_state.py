from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict, field
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
    inventory: List[str] = field(default_factory=list)
    hand_slot: List[str] = field(default_factory=list)
    worn_items: List[str] = field(default_factory=list)
    visited_rooms: Set[str] = field(default_factory=set)
    visited_areas: Dict[str, List[str]] = field(default_factory=dict)
    game_flags: Dict[str, bool] = field(default_factory=dict)
    player_status: PlayerStatus = field(default_factory=lambda: PlayerStatus())
    game_time: datetime = field(default_factory=datetime.now)
    object_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    last_save_time: Optional[datetime] = None

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

    def get_object_state(self, object_id: str) -> Dict[str, Any]:
        """Get the current runtime state of an object, ensuring it's fully initialized."""
        base_data = self.get_object_by_id(object_id)
        if not base_data:
            logging.warning(f"get_object_state: Cannot find base data for '{object_id}'. Returning potentially empty state.")
            # Ensure at least an empty dict exists in object_states before returning
            return self.object_states.setdefault(object_id, {})

        current_state = self.object_states.get(object_id)
        needs_rebuild = False

        # Determine required state components based on base data
        is_lockable = bool(base_data.get("lock_type")) or "lockable" in base_data.get("attributes", []) or isinstance(base_data.get("lock_details"), dict)
        is_container = "container" in base_data.get("attributes", [])

        # Check if state exists and is complete
        if current_state is None:
            logging.debug(f"State for '{object_id}' not found. Will create.")
            needs_rebuild = True
        else:
            # Check for missing essential components
            if is_lockable and "lock_details" not in current_state:
                logging.warning(f"State for lockable object '{object_id}' exists but missing 'lock_details'. Rebuilding.")
                needs_rebuild = True
            if is_container and "contains" not in current_state:
                logging.warning(f"State for container object '{object_id}' exists but missing 'contains'. Rebuilding.")
                needs_rebuild = True
            # Add checks for other essential state keys if needed

        # Build/Rebuild state if necessary
        if needs_rebuild:
            logging.debug(f"Building/Rebuilding state for '{object_id}'.")
            new_state = {}
            # Initialize lock details
            if is_lockable:
                lock_init = base_data.get("lock_details", {}).copy() # Prioritize lock_details dict
                if not lock_init and "lockable" in base_data.get("attributes", []): # Fallback to legacy
                    lock_init = {
                        "locked": base_data.get("is_locked", True),
                        "key_id": base_data.get("lock_key_id"),
                        "required_key": base_data.get("required_key")
                    }
                    # Clean up None values from legacy keys if they exist
                    if lock_init.get("key_id") is None: lock_init.pop("key_id", None)
                    if lock_init.get("required_key") is None: lock_init.pop("required_key", None)
                new_state["lock_details"] = lock_init
                logging.debug(f" > Initialized lock_details for '{object_id}': {lock_init}")

            # Initialize container contents
            if is_container:
                base_contents = base_data.get("state", {}).get("contains")
                if base_contents is None: base_contents = base_data.get("contains", [])
                new_state["contains"] = list(base_contents) # Ensure list copy
                logging.debug(f" > Initialized contains for '{object_id}': {new_state['contains']}")
                
            # Add other initial state components here if needed (e.g., charge, fuel)
            
            # Preserve existing state keys if they are not part of the rebuild
            preserved_keys = set()
            if current_state is not None:
                 for key, value in current_state.items():
                      if key not in new_state: # Don't overwrite rebuilt keys
                           new_state[key] = value
                           preserved_keys.add(key)
                 if preserved_keys:
                      logging.debug(f" > Preserved existing keys: {preserved_keys}")

            # Replace the old state (or add the new one)
            self.object_states[object_id] = new_state
            logging.debug(f"Final rebuilt state for '{object_id}': {self.object_states[object_id]}")
            return new_state # Return the newly built state
        else:
            # State exists and is considered complete
            logging.debug(f"State for '{object_id}' exists and seems complete. Returning: {current_state}")
            return current_state

    def set_object_state(self, object_id: str, state_key: str, value: Any) -> None:
        """Set a specific key within an object's runtime state."""
        # Ensure the base state dictionary exists and is initialized using get_object_state
        # This call will perform initialization/rebuild if needed
        _ = self.get_object_state(object_id) # Call primarily for side effect of initialization

        # Check if the state dict exists after the call
        if object_id not in self.object_states or not isinstance(self.object_states[object_id], dict):
             logging.error(f"set_object_state: Failed to get/initialize state dict for '{object_id}' via get_object_state. Cannot set key '{state_key}'.")
             return

        # Set the specific key in the object's state dictionary
        self.object_states[object_id][state_key] = value
        logging.debug(f"Updated object state for '{object_id}': Set '{state_key}' = {value}")

    def update_object_lock_state(self, object_id: str, locked: bool) -> bool:
        """Updates the 'locked' status within an object's runtime lock_details."""
        # Ensure the state is initialized (this will rebuild if necessary)
        obj_state = self.get_object_state(object_id)

        # Check if lock_details dictionary exists and is a dictionary
        if "lock_details" in obj_state and isinstance(obj_state["lock_details"], dict):
            # Update the 'locked' value directly within the dictionary referenced by obj_state
            obj_state["lock_details"]["locked"] = locked
            # No need to reassign self.object_states[object_id] = obj_state here, 
            # because obj_state is already the reference to the dictionary within self.object_states.
            logging.info(f"Updated lock state for '{object_id}': set locked = {locked}. Current State: {self.object_states[object_id]}")
            return True
        else:
            # Log the failure with the state that was returned by get_object_state
            logging.error(f"update_object_lock_state: Cannot update lock state for '{object_id}'. 'lock_details' dict not found in runtime state: {obj_state}")
            return False

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
        """Retrieves base object data from the stored dictionary."""
        return self.objects_data.get(object_id)

    def _get_object_name(self, object_id: Optional[str]) -> str:
        """Safely gets the object's name or returns a default."""
        if not object_id:
            return "nothing"
        obj_data = self.get_object_by_id(object_id)
        return obj_data.get("name", object_id) if obj_data else object_id # Fallback to ID

    def find_object_id_by_name_in_location(self, object_name: str) -> Optional[str]:
        """Finds an object ID by name/alias within the current room or area (partial match allowed)."""
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
                     if isinstance(area, dict) and area.get("area_id") == self.current_area_id:
                         # Use the stateful list if available, otherwise fallback to base data
                         # This assumes area state might eventually track object presence
                         # For now, using base area['objects_present']
                         search_list = area.get("objects_present", [])
                         logging.debug(f"Searching within area '{self.current_area_id}', using base objects_present: {search_list}")
                         break # Found the area
                 if not search_list and self.current_area_id in [a.get("area_id") for a in areas if isinstance(a, dict)]:
                     logging.debug(f"Area '{self.current_area_id}' found, but no 'objects_present' list or list is empty.")
             else:
                 logging.warning(f"Room '{self.current_room_id}' has 'areas' but it is not a list.")
        else:
            # If not in an area, search room's base objects_present list
            search_list = current_room_data.get("objects_present", [])
            logging.debug(f"Searching within room '{self.current_room_id}', using base objects_present: {search_list}")
            
        # Now search the list (either from area or room)
        logging.debug(f"[find_in_loc] Attempting to search through list: {search_list}")
        found_id = None
        # --- ADDED: Prioritize exact matches first --- 
        # Pass 1: Exact Matches
        if isinstance(search_list, list):
             for item_ref in search_list:
                 object_id = None
                 if isinstance(item_ref, str):
                     object_id = item_ref
                 elif isinstance(item_ref, dict) and 'id' in item_ref:
                     object_id = item_ref['id']
                 
                 if object_id:
                     obj_data = self.get_object_by_id(object_id)
                     if obj_data:
                         name = obj_data.get('name', '').lower()
                         aliases = [a.lower() for a in obj_data.get('command_aliases', []) if isinstance(a, str)]
                         # Exact match ID, name, or alias
                         if normalized_name == object_id.lower() or normalized_name == name or normalized_name in aliases:
                             logging.debug(f"[find_in_loc] EXACT Match FOUND for '{normalized_name}' with ID '{object_id}'")
                             if found_id and found_id != object_id:
                                 logging.warning(f"Ambiguous exact object name '{normalized_name}' in location (Matches: {found_id}, {object_id}). Returning None.")
                                 return None
                             found_id = object_id
                             
        # If an exact match was found, return it immediately
        if found_id:
             logging.debug(f"Returning exact match: {found_id}")
             return found_id
             
        # Pass 2: Partial Matches (if no exact match found)
        logging.debug(f"[find_in_loc] No exact match found for '{normalized_name}'. Checking partial matches.")
        partial_matches = []
        if isinstance(search_list, list):
             for item_ref in search_list:
                 object_id = None
                 if isinstance(item_ref, str):
                     object_id = item_ref
                 elif isinstance(item_ref, dict) and 'id' in item_ref:
                     object_id = item_ref['id']
                     
                 if object_id:
                     obj_data = self.get_object_by_id(object_id)
                     if obj_data:
                         name = obj_data.get('name', '').lower()
                         aliases = [a.lower() for a in obj_data.get('command_aliases', []) if isinstance(a, str)]
                         # Check if normalized_name is IN name or any alias
                         if normalized_name in name or any(normalized_name in alias for alias in aliases):
                             logging.debug(f"[find_in_loc] PARTIAL Match FOUND for '{normalized_name}' with ID '{object_id}' (Name: '{name}', Aliases: {aliases})")
                             if object_id not in partial_matches:
                                 partial_matches.append(object_id)
                                 
        # Handle partial match results
        if len(partial_matches) == 1:
             found_id = partial_matches[0]
             logging.debug(f"Found unique partial match: {found_id}")
        elif len(partial_matches) > 1:
             logging.warning(f"Ambiguous partial object name '{normalized_name}' in location (Matches: {partial_matches}). Returning None.")
             return None # Ambiguous partial match
             
        if not found_id:
             logging.debug(f"Object '{normalized_name}' not found in current location (exact or partial)." )
             
        return found_id

    def _find_object_id_by_name_in_inventory(self, item_name_or_id: str) -> Optional[str]:
        """Finds the object ID in inventory by name, alias, or ID (partial match allowed)."""
        normalized_name = item_name_or_id.lower().strip()
        logging.debug(f"Searching base inventory for '{normalized_name}'. Inventory: {self.inventory}")
        
        exact_match = None
        partial_matches = []
        
        # Pass 1: Exact Matches
        for object_id in self.inventory:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in aliases:
                if exact_match and exact_match != object_id:
                    logging.warning(f"Ambiguous exact item name '{normalized_name}' found in inventory (Matches: {exact_match}, {object_id}).")
                    return None
                exact_match = object_id
                
        if exact_match: return exact_match
        
        # Pass 2: Partial Matches
        for object_id in self.inventory:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
            if normalized_name in name or any(normalized_name in alias for alias in aliases):
                 if object_id not in partial_matches:
                     partial_matches.append(object_id)
                     
        if len(partial_matches) == 1:
             logging.debug(f"Found unique partial match in inventory: {partial_matches[0]}")
             return partial_matches[0]
        elif len(partial_matches) > 1:
             logging.warning(f"Ambiguous partial item name '{normalized_name}' found in inventory (Matches: {partial_matches}).")
             return None
             
        logging.debug(f"Item '{normalized_name}' not found in inventory (exact or partial).")
        return None

    def _find_object_id_by_name_worn(self, item_name_or_id: str) -> Optional[str]:
        """Finds the object ID of a directly worn item by name, alias, or ID (partial match allowed)."""
        normalized_name = item_name_or_id.lower().strip()
        logging.debug(f"Searching directly worn items for '{normalized_name}'. Worn list: {self.worn_items}")
        
        exact_match = None
        partial_matches = []
        
        # Pass 1: Exact Matches
        for object_id in self.worn_items:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in aliases:
                 if exact_match and exact_match != object_id:
                     logging.warning(f"Ambiguous exact item name '{normalized_name}' found in worn items (Matches: {exact_match}, {object_id}).")
                     return None
                 exact_match = object_id
                 
        if exact_match: return exact_match
        
        # Pass 2: Partial Matches
        for object_id in self.worn_items:
             item_data = self.get_object_by_id(object_id)
             if not item_data: continue
             name = item_data.get('name', '').lower()
             aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
             if normalized_name in name or any(normalized_name in alias for alias in aliases):
                  if object_id not in partial_matches:
                      partial_matches.append(object_id)
                      
        if len(partial_matches) == 1:
              logging.debug(f"Found unique partial match in worn items: {partial_matches[0]}")
              return partial_matches[0]
        elif len(partial_matches) > 1:
              logging.warning(f"Ambiguous partial item name '{normalized_name}' found in worn items (Matches: {partial_matches}).")
              return None
              
        logging.debug(f"Item '{normalized_name}' not found directly worn (exact or partial).")
        return None

    def find_item_id_held_or_worn(self, item_name_or_id: str) -> Optional[str]:
        """Finds an item ID by name/alias/ID in hands, directly worn, or inside worn containers."""
        normalized_name = item_name_or_id.lower().strip()
        logging.debug(f"Searching for item '{normalized_name}' in hands, worn, and inside worn containers.")

        # 1. Search hand slot
        logging.debug(f"Checking hand slot: {self.hand_slot}")
        for held_id in self.hand_slot:
             item_data = self.get_object_by_id(held_id)
             if not item_data:
                 logging.warning(f"Hand slot item ID '{held_id}' not found in objects data during find item search.")
                 continue
             name = item_data.get('name', '').lower()
             aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
             if normalized_name == held_id.lower() or normalized_name == name or normalized_name in aliases:
                 logging.debug(f"Found item '{normalized_name}' (ID: {held_id}) in hand slot.")
                 return held_id # Found in hand
        
        # 2. Search directly worn items (using the helper)
        found_id = self._find_object_id_by_name_worn(normalized_name)
        if found_id:
            logging.debug(f"Found item '{normalized_name}' (ID: {found_id}) directly worn.")
            return found_id

        # 3. Search inside worn containers
        logging.debug(f"Checking inside worn containers. Worn list: {self.worn_items}")
        for worn_container_id in self.worn_items:
            container_data = self.get_object_by_id(worn_container_id)
            # Check if this worn item IS a container
            if not container_data or not container_data.get('properties', {}).get('is_storage'):
                continue # Skip worn items that are not containers
            
            # Get the container's current state (its contents)
            container_state = self.get_object_state(worn_container_id) # Use state method
            contained_item_ids = container_state.get('contains', [])
            logging.debug(f"Checking inside worn container '{worn_container_id}' ({container_data.get('name', '')}). Contains: {contained_item_ids}")
            
            if isinstance(contained_item_ids, list):
                 for item_id_inside in contained_item_ids:
                     item_data = self.get_object_by_id(item_id_inside)
                     if not item_data:
                         logging.warning(f"Item ID '{item_id_inside}' inside container '{worn_container_id}' not found in objects data.")
                         continue
                     name = item_data.get('name', '').lower()
                     aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
                     if normalized_name == item_id_inside.lower() or normalized_name == name or normalized_name in aliases:
                         logging.debug(f"Found item '{normalized_name}' (ID: {item_id_inside}) inside worn container '{worn_container_id}'.")
                         # Potential ambiguity: If multiple containers have the same item?
                         # For now, return the first match found.
                         return item_id_inside 

        # 4. Optional: Search base inventory as last resort? (Decide if keys can be loose)
        # found_id = self._find_object_id_by_name_in_inventory(normalized_name)
        # if found_id:
        #     logging.debug(f"Found item '{normalized_name}' (ID: {found_id}) in base inventory as fallback.")
        #     return found_id

        logging.debug(f"Item '{normalized_name}' not found in hands, worn, or inside worn containers.")
        return None

    def find_container_id_by_name(self, container_name: str) -> Optional[str]:
        """Finds a container object ID by name/alias, searching location, hand slot, and worn items."""
        normalized_name = container_name.lower().strip()
        logging.debug(f"Searching for container '{normalized_name}' in location, hand slot, and worn items.")

        # 1. Search current location (room/area)
        found_id = self.find_object_id_by_name_in_location(normalized_name) # Use public method
        if found_id:
            obj_data = self.get_object_by_id(found_id)
            if obj_data and obj_data.get('properties', {}).get('is_storage'):
                 logging.debug(f"Found container '{normalized_name}' (ID: {found_id}) in location.")
                 return found_id
            else:
                 logging.debug(f"Found object '{normalized_name}' (ID: {found_id}) in location, but it is not a container.")

        # 2. Search hand slot
        logging.debug(f"Searching hand slot for container '{normalized_name}'. Hand slot: {self.hand_slot}")
        for held_id in self.hand_slot:
             item_data = self.get_object_by_id(held_id)
             if not item_data or not item_data.get('properties', {}).get('is_storage'):
                 continue # Skip non-containers or missing data
             name = item_data.get('name', '').lower()
             aliases = [a.lower() for a in item_data.get('command_aliases', []) if isinstance(a, str)]
             if normalized_name == held_id.lower() or normalized_name == name or normalized_name in aliases:
                 logging.debug(f"Found container '{normalized_name}' (ID: {held_id}) in hand slot.")
                 return held_id

        # 3. Search worn items (using the helper)
        found_id = self._find_object_id_by_name_worn(normalized_name)
        if found_id:
            obj_data = self.get_object_by_id(found_id)
            if obj_data and obj_data.get('properties', {}).get('is_storage'):
                 logging.debug(f"Found container '{normalized_name}' (ID: {found_id}) worn.")
                 return found_id
            else:
                 logging.debug(f"Found object '{normalized_name}' (ID: {found_id}) worn, but it is not a container.")

        # 4. Optional: Search inventory? (If containers can be loose in inventory)
        # found_id = self._find_object_id_by_name_in_inventory(normalized_name)
        # if found_id:
        #    obj_data = self.get_object_by_id(found_id)
        #    if obj_data and obj_data.get('properties', {}).get('is_storage'):
        #        logging.debug(f"Found container '{normalized_name}' (ID: {found_id}) in inventory as fallback.")
        #        return found_id

        logging.debug(f"Container '{normalized_name}' not found in location, hand slot, or worn items.")
        return None

    def take_object(self, object_id: str) -> str:
        """Moves an object from the location to the player's hand slot."""
        # Check 1: Hand Capacity
        if len(self.hand_slot) >= 2:
            # TODO: Add response key take_fail_hands_full
            # Try to list items currently held
            held_items_str = " and ".join([self._get_object_name(item) or "something" for item in self.hand_slot])
            return f"Your hands are full (holding the {held_items_str})."

        # Check 2: If object exists in location (redundant if GameLoop checks?)
        if self.find_object_id_by_name_in_location(object_id) != object_id:
             # Attempt lookup by ID directly if name search failed but ID was passed
             if self.get_object_by_id(object_id) and self.find_object_id_by_name_in_location(self._get_object_name(object_id)) == object_id:
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
        self.hand_slot.append(object_id)
        object_name = self._get_object_name(object_id)
        logging.info(f"Player took '{object_id}' ({object_name}) into hand_slot from location.")
        return f"You take the {object_name}."

    def drop_object(self, object_id: str) -> Dict[str, Any]:
        """Moves an object from hand_slot to the current location."""
        # Corrected Check: Ensure the object ID is actually in the hand_slot list
        if object_id not in self.hand_slot:
            # This check ensures the handler doesn't proceed if the item isn't held.
            # The calling handler (handle_drop) should ideally verify this first.
            return {"success": False, "message": f"You aren't holding the {self._get_object_name(object_id)}."} 

        # Attempt to add the object to the current location FIRST
        added = self._add_object_to_location(object_id)
        if not added:
            logging.error(f"Failed to add '{object_id}' to location {self.current_room_id}/{self.current_area_id} when dropping.")
            # Keep the item in hand if adding to location fails
            return {"success": False, "message": f"You try to drop the {self._get_object_name(object_id)}, but can't find a place for it here."} 

        # If adding to location succeeded, now remove from hand_slot
        object_name = self._get_object_name(object_id) # Get name before removing
        self.hand_slot.remove(object_id)
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
        is_in_hands = (object_id in self.hand_slot)
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
            self.hand_slot.remove(object_id)
            logging.info(f"Item '{object_id}' ({item_name}) removed from hand_slot.")
        elif is_in_inventory:
            self.inventory.remove(object_id)
            logging.info(f"Item '{object_id}' ({item_name}) removed from inventory.")
            
        # Add to worn items
        self.worn_items.append(object_id)
        logging.info(f"Item '{object_id}' ({item_name}) added to worn_items.")
        
        return f"You put on the {item_name}."

    def wear_item_from_container(self, item_id_to_wear: str, container_id: str) -> str:
        """Attempts to wear an item directly from a container's storage."""
        logging.debug(f"Attempting to wear item '{item_id_to_wear}' from container '{container_id}'")

        # Check 1: Does the item exist?
        item_data = self.get_object_by_id(item_id_to_wear)
        if not item_data:
            logging.error(f"wear_item_from_container: Cannot find data for item ID: {item_id_to_wear}")
            return "Cannot find data for that item."
        item_name = item_data.get("name", item_id_to_wear)

        # Check 2: Does the container exist and have state?
        container_data = self.get_object_by_id(container_id)
        container_state = self.get_object_state(container_id)
        if not container_data or not container_state or 'contains' not in container_state:
            logging.error(f"wear_item_from_container: Container '{container_id}' data or state ('contains') missing.")
            return "Cannot access the container properly."
        container_name = container_data.get("name", container_id)

        # Check 3: Is the item actually in the container state?
        if item_id_to_wear not in container_state.get('contains', []): # Check state's list
            logging.warning(f"wear_item_from_container: Item '{item_id_to_wear}' not found in container '{container_id}' state: {container_state.get('contains', [])}")
            return f"You don't seem to have the {item_name} in the {container_name}."
        
        # Check 4: Is it wearable?
        props = item_data.get('properties', {})
        if not props.get('is_wearable'):
            return f"You cannot wear the {item_name}."
            
        # Check 5: Does it have valid wear configuration?
        wear_area = props.get('wear_area')
        wear_layer = props.get('wear_layer')
        if not wear_area or wear_layer is None:
             logging.error(f"wear_item_from_container: Item {item_id_to_wear} ({item_name}) is wearable but missing wear_area or wear_layer.")
             return f"The {item_name} isn't configured correctly for wearing."
             
        # Check 6: Does it conflict with currently worn items?
        for worn_item_id in self.worn_items:
            worn_item_data = self.get_object_by_id(worn_item_id)
            if not worn_item_data: continue
            worn_props = worn_item_data.get('properties', {})
            worn_area = worn_props.get('wear_area')
            worn_layer = worn_props.get('wear_layer')
            
            if worn_area == wear_area and worn_layer is not None and wear_layer <= worn_layer:
                 worn_item_name = self._get_object_name(worn_item_id)
                 return f"You cannot wear the {item_name} there; you are already wearing the {worn_item_name} which occupies that space/layer."

        # --- All checks passed ---
        
        # Remove from container's state
        try:
            # Modify the list obtained from container_state
            current_contents = container_state.get('contains', [])
            current_contents.remove(item_id_to_wear)
            # Update the state using set_object_state 
            self.set_object_state(container_id, 'contains', current_contents) 
            logging.info(f"Item '{item_id_to_wear}' ({item_name}) removed from container '{container_id}' ({container_name}).")
        except ValueError:
            logging.error(f"wear_item_from_container: Failed to remove '{item_id_to_wear}' from container '{container_id}' state after check.")
            return f"Something went wrong trying to take the {item_name} from the {container_name}."
            
        # Add to worn items
        self.worn_items.append(item_id_to_wear)
        logging.info(f"Item '{item_id_to_wear}' ({item_name}) added to worn_items.")
        
        return f"You take the {item_name} from the {container_name} and put it on."

    def remove_item(self, object_id: str) -> str:
        """Attempts to remove a worn item and place it in hand_slot."""
        # Check 1: Is the item actually worn?
        if object_id not in self.worn_items:
            # Check if they have it elsewhere?
            item_name = self._get_object_name(object_id) or object_id
            if object_id in self.inventory:
                return f"You have the {item_name} in your inventory, but you aren't wearing it."
            elif object_id in self.hand_slot:
                return f"You are holding the {item_name}, not wearing it."
            else:
                return f"You aren't wearing the {item_name}."

        item_name = self._get_object_name(object_id)

        # Check 2: Is the hand_slot list not full?
        if len(self.hand_slot) >= 2:
            # TODO: Add response key remove_fail_hands_full
            held_items_str = " and ".join([self._get_object_name(item) or "something" for item in self.hand_slot])
            return f"Your hands are full (holding the {held_items_str}). You need to drop something before taking off the {item_name}."

        # Remove from worn_items
        self.worn_items.remove(object_id)
        
        # Add to hand_slot list
        self.hand_slot.append(object_id)
        
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
            # Add to area's objects_present list
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logging.error(f"_add_object_to_location: Room {self.current_room_id} 'areas' is not a list.")
                return False
            
            found_area = False
            for i, area_data in enumerate(areas):
                if isinstance(area_data, dict) and area_data.get("area_id") == self.current_area_id:
                    target_list_container = area_data
                    target_list_key = "objects_present"
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
            # Remove from area's objects_present list
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logging.error(f"_remove_object_from_location: Room {self.current_room_id} 'areas' is not a list.")
                return False
                
            found_area = False
            for i, area_data in enumerate(areas):
                 if isinstance(area_data, dict) and area_data.get("area_id") == self.current_area_id:
                     target_list_container = area_data
                     target_list_key = "objects_present"
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