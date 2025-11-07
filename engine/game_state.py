import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from loguru import logger


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
    rooms_data: dict[str, Any]  # Added to store loaded room definitions
    objects_data: dict[str, Any]  # Added objects_data
    responses_data: dict[str, Any] # Added for storing loaded response templates
    power_state: PowerState
    current_area_id: str | None = None
    inventory: list[str] = field(default_factory=list)
    hand_slot: list[str] = field(default_factory=list)
    worn_items: list[str] = field(default_factory=list)
    visited_rooms: set[str] = field(default_factory=set)
    visited_areas: dict[str, list[str]] = field(default_factory=dict)
    game_flags: dict[str, bool] = field(default_factory=dict)
    player_status: PlayerStatus = field(default_factory=lambda: PlayerStatus())
    game_time: datetime = field(default_factory=datetime.now)
    object_states: dict[str, dict[str, Any]] = field(default_factory=dict)
    dynamic_room_objects: dict[str, list[str]] = field(default_factory=dict)
    last_save_time: datetime | None = None

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
        if self.responses_data is None: # Ensure responses_data is also initialized
            self.responses_data = {}

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

    def get_current_location(self) -> tuple[str, str | None]:
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
            'dynamic_room_objects': self.dynamic_room_objects,
            'last_save_time': datetime.now().isoformat()
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=4)
        self.last_save_time = datetime.now()

    @classmethod
    def load_game(cls, filename: str) -> 'GameState':
        """Load a game state from a file."""
        with open(filename) as f:
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
        game_state.dynamic_room_objects = save_data['dynamic_room_objects']
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

    def get_object_state(self, object_id: str) -> dict[str, Any]:
        """Get the current runtime state of an object, ensuring it's fully initialized."""
        base_data = self.get_object_by_id(object_id)
        if not base_data:
            logger.warning(f"get_object_state: Cannot find base data for '{object_id}'. Returning potentially empty state.")
            # Ensure at least an empty dict exists in object_states before returning
            return self.object_states.setdefault(object_id, {})

        current_state = self.object_states.get(object_id)
        needs_rebuild = False

        # Determine required state components based on base data
        is_lockable = bool(base_data.get("lock_type")) or "lockable" in base_data.get("attributes", []) or isinstance(base_data.get("lock_details"), dict)
        is_container = base_data.get("properties", {}).get("is_storage", False)

        # Check if state exists and is complete
        if current_state is None:
            logger.debug(f"State for '{object_id}' not found. Will create.")
            needs_rebuild = True
        else:
            # Check for missing essential components
            if is_lockable and "lock_details" not in current_state:
                logger.warning(f"State for lockable object '{object_id}' exists but missing 'lock_details'. Rebuilding.")
                needs_rebuild = True
            if is_container and "contains" not in current_state:
                logger.warning(f"State for container object '{object_id}' exists but missing 'contains'. Rebuilding.")
                needs_rebuild = True
            # Add checks for other essential state keys if needed

        # Build/Rebuild state if necessary
        if needs_rebuild:
            logger.debug(f"Building/Rebuilding state for '{object_id}'.")
            new_state = {}

            # Priority 1: Preserve simple existing state values from current_state
            # These are typically flags like is_open, is_visible, charge, etc.
            # Complex structures like lock_details and contains will be handled/rebuilt specifically.
            if current_state is not None:
                for key, value in current_state.items():
                    if key not in ["lock_details", "contains"]: # Don't blindly copy complex structures
                        new_state[key] = value
                logger.debug(f" > Preserved simple keys from current_state: {new_state}")

            # Priority 2: Initialize/Rebuild complex components if missing or explicitly needed.
            # Initialize lock details if not already preserved or if base_data dictates a structure
            if is_lockable and "lock_details" not in new_state: # Check new_state
                lock_init = base_data.get("lock_details", {}).copy() # Start with base_data.lock_details if present

                # If 'locked' is not in lock_init (either from base_data.lock_details or it was empty)
                # AND the object is lockable (e.g. has a lock_type defined at base_data level),
                # then initialize 'locked' status from base_data.is_locked.
                # Also, ensure lock_type and lock_key_id are populated from base_data if not in lock_init.
                if 'locked' not in lock_init and base_data.get("lock_type"):
                    lock_init['locked'] = base_data.get("is_locked", False) # Default to False if is_locked missing in base_data

                # Ensure lock_type from base_data is present if not in lock_init (and base_data has it)
                # This handles cases where lock_details might exist from save but lacks 'type'
                # or where lock_details is being built fresh.
                if 'type' not in lock_init and base_data.get("lock_type"):
                    lock_init['type'] = base_data.get("lock_type")
                
                # Ensure lock_key_id from base_data is present if not in lock_init (and base_data has it)
                if 'key_id' not in lock_init and base_data.get("lock_key_id"):
                    lock_init['key_id'] = base_data.get("lock_key_id")
                
                # Clean up key_id if it ended up as None after the above (e.g. base_data.get returned None)
                # This ensures we don't store {'key_id': null} if it wasn't actually defined.
                if lock_init.get('key_id') is None:
                    lock_init.pop('key_id', None)

                new_state["lock_details"] = lock_init
                logger.debug(f" > Initialized/Rebuilt lock_details for '{object_id}': {lock_init}")

            # Initialize container contents if not already preserved or if base_data dictates
            if is_container and "contains" not in new_state: # Check new_state
                initial_items = base_data.get("storage_contents")
                log_source = "storage_contents"
                if initial_items is None:
                    initial_items = base_data.get("contains")
                    log_source = "contains" if initial_items is not None else "storage_contents_was_None->contains_was_None"
                if initial_items is None:
                     initial_items = base_data.get("state", {}).get("contains") # Legacy from base_data.state
                     log_source = "state.contains" if initial_items is not None else (log_source + "->state.contains_was_None")
                if initial_items is None:
                    initial_items = []
                    log_source = log_source if log_source.endswith("None") else (log_source + "->default_empty")
                new_state["contains"] = list(initial_items) # Ensure it's a list copy
                logger.debug(f" > Initialized/Rebuilt contains for '{object_id}': {new_state['contains']} (Source: {log_source})")
            
            # Priority 3: Initialize simple properties from base_data IF NOT ALREADY in new_state (i.e., not preserved from current_state)
            if "is_open" in base_data and "is_open" not in new_state:
                new_state["is_open"] = base_data["is_open"]
                logger.debug(f" > Initialized is_open for '{object_id}' from base_data (was not in current_state): {new_state['is_open']}")
            
            # Example for 'is_visible' (if you want it to default from base_data if not in current_state)
            # This is important for items that might not have had state before but have an initial_state in YAML.
            if "initial_state" in base_data and "is_visible" not in new_state: # 'initial_state' in YAML often means 'is_visible'
                 new_state["is_visible"] = base_data["initial_state"]
                 logger.debug(f" > Initialized is_visible for '{object_id}' from base_data.initial_state (was not in current_state): {new_state['is_visible']}")
            elif "is_visible" in base_data and "is_visible" not in new_state: # Direct 'is_visible' in YAML
                 new_state["is_visible"] = base_data["is_visible"]
                 logger.debug(f" > Initialized is_visible for '{object_id}' from base_data.is_visible (was not in current_state): {new_state['is_visible']}")

            # Replace the old state (or add the new one)
            self.object_states[object_id] = new_state
            logger.debug(f"Final rebuilt state for '{object_id}': {self.object_states[object_id]}")
            return new_state # Return the newly built state
        else:
            # State exists and is considered complete
            logger.debug(f"State for '{object_id}' exists and seems complete. Returning: {current_state}")
            return current_state

    def set_object_state(self, object_id: str, state_key: str, value: Any) -> None:
        """Set a specific key within an object's runtime state."""
        # Ensure the base state dictionary exists and is initialized using get_object_state
        # This call will perform initialization/rebuild if needed
        _ = self.get_object_state(object_id) # Call primarily for side effect of initialization

        # Check if the state dict exists after the call
        if object_id not in self.object_states or not isinstance(self.object_states[object_id], dict):
             logger.error(f"set_object_state: Failed to get/initialize state dict for '{object_id}' via get_object_state. Cannot set key '{state_key}'.")
             return

        # Set the specific key in the object's state dictionary
        self.object_states[object_id][state_key] = value
        logger.debug(f"Updated object state for '{object_id}': Set '{state_key}' = {value}")

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
            logger.info(f"Updated lock state for '{object_id}': set locked = {locked}. Current State: {self.object_states[object_id]}")
            return True
        else:
            # Log the failure with the state that was returned by get_object_state
            logger.error(f"update_object_lock_state: Cannot update lock state for '{object_id}'. 'lock_details' dict not found in runtime state: {obj_state}")
            return False

    def is_object_interacted_with(self, object_id: str) -> bool:
        """Check if an object has been interacted with."""
        return object_id in self.object_states

    def get_player_status(self) -> dict:
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

    def get_object_by_id(self, object_id: str) -> dict[str, Any] | None:
        """Retrieves base object data from the stored dictionary."""
        return self.objects_data.get(object_id)

    def _get_object_name(self, object_id: str | None) -> str:
        """Safely gets the object's name or returns a default."""
        if not object_id:
            return "nothing"
        obj_data = self.get_object_by_id(object_id)
        return obj_data.get("name", object_id) if obj_data else object_id # Fallback to ID

    def find_object_id_by_name_in_location(self, object_name: str, room_id: str, area_id: str | None = None, visible_only: bool = True) -> str | None:
        """Finds an object ID by name/alias within the specified room or area (partial match allowed),
           considering dynamic visibility."""
        normalized_name = object_name.lower().strip()
        logger.debug(f"Searching for '{normalized_name}' in location {room_id}/{area_id or 'room'} (visible_only={visible_only})")

        current_room_data = self.rooms_data.get(room_id)
        if not current_room_data:
            logger.error(f"Cannot search location: Room data missing for {room_id}")
            return None

        potential_ids_in_location: set[str] = set()
        static_objects_present_refs: list[Any] = []

        if area_id:
            areas = current_room_data.get("areas", [])
            if isinstance(areas, list):
                for area_data_item in areas: # Renamed to avoid conflict
                    if isinstance(area_data_item, dict) and area_data_item.get("area_id") == area_id:
                        static_objects_present_refs = area_data_item.get("objects_present", [])
                        break
        else:
            static_objects_present_refs = current_room_data.get("objects_present", [])

        for item_ref in static_objects_present_refs:
            if isinstance(item_ref, str):
                potential_ids_in_location.add(item_ref)
            elif isinstance(item_ref, dict) and 'id' in item_ref:
                potential_ids_in_location.add(item_ref['id'])

        for obj_id_global, obj_data_global in self.objects_data.items():
            if obj_data_global.get("location") == room_id: # Check against the passed room_id
                potential_ids_in_location.add(obj_id_global)
        
        dynamic_ids_for_room = self.dynamic_room_objects.get(room_id, []) # Check against the passed room_id
        for dyn_obj_id in dynamic_ids_for_room:
            potential_ids_in_location.add(dyn_obj_id)

        exact_match_found_id: str | None = None
        for obj_id in potential_ids_in_location:
            obj_data = self.get_object_by_id(obj_id)
            if not obj_data: continue

            current_obj_state = self.get_object_state(obj_id)
            default_visibility = obj_data.get('initial_state', True)
            is_visible = current_obj_state.get('is_visible', default_visibility)

            if not visible_only or is_visible:
                name = obj_data.get('name', '').lower()
                # CHANGED: Use 'synonyms' instead of 'command_aliases'
                aliases = [s.lower() for s in obj_data.get('synonyms', []) if isinstance(s, str)]
                if normalized_name == obj_id.lower() or normalized_name == name or normalized_name in aliases:
                    if exact_match_found_id and exact_match_found_id != obj_id:
                        logger.warning(f"Ambiguous exact object name '{normalized_name}' (Matches: {exact_match_found_id}, {obj_id}) in location {room_id}.")
                        return None # Ambiguity
                    exact_match_found_id = obj_id
        
        if exact_match_found_id:
            return exact_match_found_id

        partial_match_ids: list[str] = []
        for obj_id in potential_ids_in_location:
            obj_data = self.get_object_by_id(obj_id)
            if not obj_data: continue
            current_obj_state = self.get_object_state(obj_id)
            default_visibility = obj_data.get('initial_state', True)
            is_visible = current_obj_state.get('is_visible', default_visibility)

            if not visible_only or is_visible:
                name = obj_data.get('name', '').lower()
                # CHANGED: Use 'synonyms' instead of 'command_aliases'
                aliases = [s.lower() for s in obj_data.get('synonyms', []) if isinstance(s, str)]
                if normalized_name in name or any(normalized_name in alias for alias in aliases):
                    if obj_id not in partial_match_ids:
                        partial_match_ids.append(obj_id)
        
        if len(partial_match_ids) == 1:
            return partial_match_ids[0]
        elif len(partial_match_ids) > 1:
            logger.warning(f"Ambiguous partial object name '{normalized_name}' (Matches: {partial_match_ids}) in location {room_id}.")
            return None # Ambiguity
            
        return None

    def _find_object_id_by_name_in_inventory(self, item_name_or_id: str) -> str | None:
        """Finds the object ID in inventory by name, alias, or ID (partial match allowed)."""
        normalized_name = item_name_or_id.lower().strip()
        logger.debug(f"Searching base inventory for '{normalized_name}'. Inventory: {self.inventory}")
        
        exact_match = None
        partial_matches = []
        
        # Pass 1: Exact Matches
        for object_id in self.inventory:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            # CHANGED: Use 'synonyms' instead of 'command_aliases'
            aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in aliases:
                if exact_match and exact_match != object_id:
                    logger.warning(f"Ambiguous exact item name '{normalized_name}' found in inventory (Matches: {exact_match}, {object_id}).")
                    return None
                exact_match = object_id
                
        if exact_match: return exact_match
        
        # Pass 2: Partial Matches
        for object_id in self.inventory:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            # CHANGED: Use 'synonyms' instead of 'command_aliases'
            aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
            if normalized_name in name or any(normalized_name in alias for alias in aliases):
                 if object_id not in partial_matches:
                     partial_matches.append(object_id)
                     
        if len(partial_matches) == 1:
             logger.debug(f"Found unique partial match in inventory: {partial_matches[0]}")
             return partial_matches[0]
        elif len(partial_matches) > 1:
             logger.warning(f"Ambiguous partial item name '{normalized_name}' found in inventory (Matches: {partial_matches}).")
             return None
             
        logger.debug(f"Item '{normalized_name}' not found in inventory (exact or partial).")
        return None

    def _find_object_id_by_name_worn(self, item_name_or_id: str) -> str | None:
        """Finds the object ID of a directly worn item by name, alias, or ID (partial match allowed)."""
        normalized_name = item_name_or_id.lower().strip()
        logger.debug(f"Searching directly worn items for '{normalized_name}'. Worn list: {self.worn_items}")
        
        exact_match = None
        partial_matches = []
        
        # Pass 1: Exact Matches
        for object_id in self.worn_items:
            item_data = self.get_object_by_id(object_id)
            if not item_data: continue
            name = item_data.get('name', '').lower()
            # CHANGED: Use 'synonyms' instead of 'command_aliases'
            aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
            if normalized_name == object_id.lower() or normalized_name == name or normalized_name in aliases:
                 if exact_match and exact_match != object_id:
                     logger.warning(f"Ambiguous exact item name '{normalized_name}' found in worn items (Matches: {exact_match}, {object_id}).")
                     return None
                 exact_match = object_id
                 
        if exact_match: return exact_match
        
        # Pass 2: Partial Matches
        for object_id in self.worn_items:
             item_data = self.get_object_by_id(object_id)
             if not item_data: continue
             name = item_data.get('name', '').lower()
             # CHANGED: Use 'synonyms' instead of 'command_aliases'
             aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
             if normalized_name in name or any(normalized_name in alias for alias in aliases):
                  if object_id not in partial_matches:
                      partial_matches.append(object_id)
                      
        if len(partial_matches) == 1:
              logger.debug(f"Found unique partial match in worn items: {partial_matches[0]}")
              return partial_matches[0]
        elif len(partial_matches) > 1:
              logger.warning(f"Ambiguous partial item name '{normalized_name}' found in worn items (Matches: {partial_matches}).")
              return None
              
        logger.debug(f"Item '{normalized_name}' not found directly worn (exact or partial).")
        return None

    def find_item_id_held_or_worn(self, item_name_or_id: str) -> str | None:
        """Finds an item ID by name/alias/ID in hands, directly worn, or inside worn containers."""
        normalized_name = item_name_or_id.lower().strip()
        logger.debug(f"Searching for item '{normalized_name}' in hands, worn, and inside worn containers.")

        # 1. Search hand slot
        logger.debug(f"Checking hand slot: {self.hand_slot}")
        for held_id in self.hand_slot:
             item_data = self.get_object_by_id(held_id)
             if not item_data:
                 logger.warning(f"Hand slot item ID '{held_id}' not found in objects data during find item search.")
                 continue
             name = item_data.get('name', '').lower()
             # CHANGED: Use 'synonyms' instead of 'command_aliases'
             aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
             if normalized_name == held_id.lower() or normalized_name == name or normalized_name in aliases:
                 logger.debug(f"Found item '{normalized_name}' (ID: {held_id}) in hand slot.")
                 return held_id # Found in hand
        
        # 2. Search directly worn items (using the helper)
        found_id = self._find_object_id_by_name_worn(normalized_name)
        if found_id:
            logger.debug(f"Found item '{normalized_name}' (ID: {found_id}) directly worn.")
            return found_id

        # 3. Search inside worn containers
        logger.debug(f"Checking inside worn containers. Worn list: {self.worn_items}")
        for worn_container_id in self.worn_items:
            container_data = self.get_object_by_id(worn_container_id)
            # Check if this worn item IS a container
            if not container_data or not container_data.get('properties', {}).get('is_storage'):
                continue # Skip worn items that are not containers
            
            # Get the container's current state (its contents)
            container_state = self.get_object_state(worn_container_id) # Use state method
            contained_item_ids = container_state.get('contains', [])
            logger.debug(f"Checking inside worn container '{worn_container_id}' ({container_data.get('name', '')}). Contains: {contained_item_ids}")
            
            if isinstance(contained_item_ids, list):
                 for item_id_inside in contained_item_ids:
                     item_data = self.get_object_by_id(item_id_inside)
                     if not item_data:
                         logger.warning(f"Item ID '{item_id_inside}' inside container '{worn_container_id}' not found in objects data.")
                         continue
                     name = item_data.get('name', '').lower()
                     # CHANGED: Use 'synonyms' instead of 'command_aliases'
                     aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
                     if normalized_name == item_id_inside.lower() or normalized_name == name or normalized_name in aliases:
                         logger.debug(f"Found item '{normalized_name}' (ID: {item_id_inside}) inside worn container '{worn_container_id}'.")
                         # Potential ambiguity: If multiple containers have the same item?
                         # For now, return the first match found.
                         return item_id_inside 

        # 4. Optional: Search base inventory as last resort? (Decide if keys can be loose)
        # found_id = self._find_object_id_by_name_in_inventory(normalized_name)
        # if found_id:
        #     logger.debug(f"Found item '{normalized_name}' (ID: {found_id}) in base inventory as fallback.")
        #     return found_id

        logger.debug(f"Item '{normalized_name}' not found in hands, worn, or inside worn containers.")
        return None

    def find_container_id_by_name(self, container_name: str) -> str | None:
        """Finds a container object ID by name/alias, searching location, hand slot, and worn items."""
        normalized_name = container_name.lower().strip()
        logger.debug(f"Searching for container '{normalized_name}' in location, hand slot, and worn items.")

        # 1. Search current location (room/area)
        found_id = self.find_object_id_by_name_in_location(normalized_name, self.current_room_id, self.current_area_id)
        if found_id:
            obj_data = self.get_object_by_id(found_id)
            if obj_data and obj_data.get('properties', {}).get('is_storage'):
                 logger.debug(f"Found container '{normalized_name}' (ID: {found_id}) in location.")
                 return found_id
            else:
                 logger.debug(f"Found object '{normalized_name}' (ID: {found_id}) in location, but it is not a container.")

        # 2. Search hand slot
        logger.debug(f"Searching hand slot for container '{normalized_name}'. Hand slot: {self.hand_slot}")
        for held_id in self.hand_slot:
             item_data = self.get_object_by_id(held_id)
             if not item_data or not item_data.get('properties', {}).get('is_storage'):
                 continue # Skip non-containers or missing data
             name = item_data.get('name', '').lower()
             # CHANGED: Use 'synonyms' instead of 'command_aliases'
             aliases = [s.lower() for s in item_data.get('synonyms', []) if isinstance(s, str)]
             if normalized_name == held_id.lower() or normalized_name == name or normalized_name in aliases:
                 logger.debug(f"Found container '{normalized_name}' (ID: {held_id}) in hand slot.")
                 return held_id

        # 3. Search worn items (using the helper)
        found_id = self._find_object_id_by_name_worn(normalized_name)
        if found_id:
            obj_data = self.get_object_by_id(found_id)
            if obj_data and obj_data.get('properties', {}).get('is_storage'):
                 logger.debug(f"Found container '{normalized_name}' (ID: {found_id}) worn.")
                 return found_id
            else:
                 logger.debug(f"Found object '{normalized_name}' (ID: {found_id}) worn, but it is not a container.")

        # 4. Optional: Search inventory? (If containers can be loose in inventory)
        # found_id = self._find_object_id_by_name_in_inventory(normalized_name)
        # if found_id:
        #    obj_data = self.get_object_by_id(found_id)
        #    if obj_data and obj_data.get('properties', {}).get('is_storage'):
        #        logger.debug(f"Found container '{normalized_name}' (ID: {found_id}) in inventory as fallback.")
        #        return found_id

        logger.debug(f"Container '{normalized_name}' not found in location, hand slot, or worn items.")
        return None

    def take_object(self, object_id: str) -> str:
        """Moves an object from its current location (room or container) into the player's hand_slot."""
        logger.debug(f"[take_object] Attempting to take object ID: {object_id}")
        # Ensure the object is 'takeable' based on its properties
        obj_data = self.get_object_by_id(object_id)
        if not obj_data:
            logger.error(f"[take_object] No base data found for {object_id}.")
            return "You can't find that item to take."

        if not obj_data.get("properties", {}).get("is_takeable", False):
            logger.warning(f"[take_object] Attempt to take non-takeable item {object_id} denied by properties.")
            return f"You cannot take the {obj_data.get('name', object_id)}."

        item_taken_from_container_id: str | None = None

        # Check if the item is in any open, visible container in the current location
        # MODIFICATION START: Changed to use the new get_containers_in_location method parameters
        open_visible_containers_ids = self.get_containers_in_location(must_be_open=True, must_be_visible=True)
        # MODIFICATION END
        logger.debug(f"[take_object] Checking open visible containers in location: {open_visible_containers_ids}")

        for container_id_check in open_visible_containers_ids:
            container_state = self.get_object_state(container_id_check)
            if container_state and object_id in container_state.get("contains", []):
                # Item is in this open, visible container.
                # Ensure the item *itself* is visible within that container (if such a state exists)
                item_state_in_container = self.get_object_state(object_id)
                if item_state_in_container.get("is_visible", True): # Default to true if no specific visibility for item itself
                    logger.info(f"[take_object] Item '{object_id}' found in open container '{container_id_check}'. Removing.")
                    current_contents = list(container_state.get("contains", []))
                    if object_id in current_contents:
                        current_contents.remove(object_id)
                        self.object_states[container_id_check]["contains"] = current_contents # Directly update state
                        item_taken_from_container_id = container_id_check
                        logger.debug(f"[take_object] Updated container '{container_id_check}' contents: {current_contents}")
                        break 
                else:
                    logger.debug(f"[take_object] Item '{object_id}' is in open container '{container_id_check}' but item's state is not visible.")
        
        # If not taken from a container, try removing from the room's general list
        if not item_taken_from_container_id:
            removed_from_room = self._remove_object_from_location(object_id) # This also handles dynamic visibility
            if not removed_from_room:
                # This could happen if the item was visible (e.g. from search) but not strictly in room's static list or dynamic list.
                # Or if it was in a closed container and shouldn't have been found by find_object_id_by_name_in_location.
                # If _remove_object_from_location couldn't find it, but properties said it was takeable & it was visible,
                # it implies a possible discrepancy. For now, we proceed if properties are okay.
                # Ensure its visibility state is updated if it was a dynamically revealed item not in a container.
                obj_state = self.get_object_state(object_id)
                if obj_state.get('is_visible', False) and not self.is_object_statically_in_room(object_id, self.current_room_id):
                    # If it was dynamically visible and not static, its removal is essentially making it not part of the room anymore.
                    # self.set_object_state(object_id, "is_visible", False) # No, taking it makes it possessed, not invisible in room
                    logger.debug(f"[take_object] Taking dynamically visible item '{object_id}' not found in a container or static/dynamic room lists.")
                else:
                    logger.warning(f"[take_object] Item '{object_id}' was not taken from a known open container and _remove_object_from_location failed or did not apply. Proceeding based on takeable property.")
        
        # Add object to hand slot (avoid duplicates)
        if object_id not in self.hand_slot:
            self.hand_slot.append(object_id)
        # Ensure the taken object itself is marked as visible (if it has such a state key)
        self.set_object_state(object_id, "is_visible", True) 
        object_name = self._get_object_name(object_id)
        logger.info(f"Player took '{object_id}' ({object_name}) into hand_slot. Source: {'container ' + item_taken_from_container_id if item_taken_from_container_id else 'location'}.")
        return f"You take the {object_name}."

    def get_containers_in_location(self, must_be_open: bool = False, must_be_visible: bool = True) -> list[str]:
        """
        Gets IDs of all storage containers in the current location (room/area) 
        that meet the specified criteria.
        """
        # Determine which set of objects to check based on visibility requirement.
        # _get_all_object_ids_in_current_location already handles filtering out held/worn items.
        # If must_be_visible is True (default), we only care about already visible objects.
        # If must_be_visible is False, we consider all objects in location regardless of their current visibility state.
        object_ids_to_check = self._get_all_object_ids_in_current_location(visible_only=must_be_visible)
        
        logger.debug(f"[get_containers_in_location] Checking IDs: {object_ids_to_check} (must_be_open={must_be_open}, must_be_visible={must_be_visible})")
        
        valid_container_ids: list[str] = []
        for obj_id in object_ids_to_check:
            obj_base_data = self.get_object_by_id(obj_id)
            if not obj_base_data:
                logger.warning(f"[get_containers_in_location] No base data for object ID '{obj_id}'. Skipping.")
                continue

            # Check if it's a storage container
            if not obj_base_data.get("properties", {}).get("is_storage", False):
                continue # Not a container

            obj_state = self.get_object_state(obj_id) # Ensure state is initialized

            # Check visibility if required (this is a bit redundant if visible_only=True was passed to _get_all_object_ids_in_current_location,
            # but good for explicit clarity and covers if must_be_visible=False but then we still want to check its state for some reason)
            if must_be_visible:
                # The object ID is already from a visible list if must_be_visible=True was used for object_ids_to_check.
                # However, its own state.is_visible is the ultimate truth for the object itself.
                # _get_all_object_ids_in_current_location(visible_only=True) checks this state.
                # So, if it's in object_ids_to_check when must_be_visible=True, it IS visible.
                pass # Already confirmed visible by the initial list generation if must_be_visible is True.

            # Check if it needs to be open and if it is
            if must_be_open:
                if not obj_state.get("is_open", False): # Default to False if is_open not set
                    logger.debug(f"[get_containers_in_location] Container '{obj_id}' skipped: must_be_open=True, but is_open={obj_state.get('is_open')}")
                    continue # Not open, and must be open

            valid_container_ids.append(obj_id)
            logger.debug(f"[get_containers_in_location] Container '{obj_id}' is valid with current criteria.")
            
        logger.debug(f"[get_containers_in_location] Returning valid containers: {valid_container_ids}")
        return valid_container_ids

    def _get_all_object_ids_in_current_location(self, visible_only: bool = False) -> set[str]:
        """Helper to get all object IDs in the current room/area, optionally filtered by visibility."""
        current_room_data = self.rooms_data.get(self.current_room_id)
        if not current_room_data:
            return set()

        potential_ids: set[str] = set()
        static_refs: list[Any] = []
        if self.current_area_id:
            areas = current_room_data.get("areas", [])
            if isinstance(areas, list):
                for area in areas:
                    if isinstance(area, dict) and area.get("area_id") == self.current_area_id:
                        static_refs = area.get("objects_present", [])
                        break
        else:
            static_refs = current_room_data.get("objects_present", [])
        
        for item_ref in static_refs:
            if isinstance(item_ref, str):
                potential_ids.add(item_ref)
            elif isinstance(item_ref, dict) and 'id' in item_ref:
                potential_ids.add(item_ref['id'])
        
        # Iterate through global objects_data and add if they belong to the current room/area
        for obj_id_global, obj_data_global in self.objects_data.items():
            obj_global_room = obj_data_global.get("location")
            obj_global_area = obj_data_global.get("area_location") # Get object's defined area

            if obj_global_room == self.current_room_id:
                if self.current_area_id:  # Player is in a specific area
                    if obj_global_area == self.current_area_id:
                        potential_ids.add(obj_id_global)
                else:  # Player is in the room generally (not a specific area)
                    if obj_global_area is None: # Object is for the room, not a sub-area
                        potential_ids.add(obj_id_global)
        
        dynamic_ids = self.dynamic_room_objects.get(self.current_room_id, [])
        for dyn_id in dynamic_ids:
            potential_ids.add(dyn_id)
        
        # Exclude items currently held, worn, or inside containers (worn/held/location)
        items_to_exclude = set(self.hand_slot) | set(self.worn_items) # Start with hands and directly worn
        for worn_item_id in self.worn_items:
            worn_item_data = self.get_object_by_id(worn_item_id)
            # Check if this worn item IS a container
            if worn_item_data and worn_item_data.get("properties", {}).get("is_storage", False):
                # Get the container's current state (its contents)
                # get_object_state ensures state is initialized and returns it
                worn_container_state = self.get_object_state(worn_item_id) 
                contained_item_ids = worn_container_state.get('contains', [])
                if isinstance(contained_item_ids, list):
                    for item_id_inside in contained_item_ids:
                        items_to_exclude.add(item_id_inside)
        # Held containers
        for held_id in self.hand_slot:
            held_data = self.get_object_by_id(held_id)
            if held_data and held_data.get('properties', {}).get('is_storage', False):
                held_state = self.get_object_state(held_id) or {}
                for item_id_inside in held_state.get('contains', []) or []:
                    items_to_exclude.add(item_id_inside)
        # Containers in current location
        for loc_obj_id in list(potential_ids):
            loc_data = self.get_object_by_id(loc_obj_id)
            if loc_data and loc_data.get('properties', {}).get('is_storage', False):
                loc_state = self.get_object_state(loc_obj_id) or {}
                for item_id_inside in loc_state.get('contains', []) or []:
                    items_to_exclude.add(item_id_inside)
        
        logger.debug(f"[GameState._get_all_object_ids_in_current_location] Before exclude: {potential_ids}, To exclude: {items_to_exclude}")
        potential_ids -= items_to_exclude
        logger.debug(f"[GameState._get_all_object_ids_in_current_location] After excluding held/worn/in_worn_container ({items_to_exclude}), potential_ids: {potential_ids}")
        
        if not visible_only:
            return potential_ids
        
        visible_ids: set[str] = set()
        for obj_id in potential_ids:
            obj_data = self.get_object_by_id(obj_id)
            if not obj_data: continue
            obj_state = self.get_object_state(obj_id)
            default_visibility = obj_data.get('initial_state', True)
            if obj_state.get('is_visible', default_visibility):
                visible_ids.add(obj_id)
        return visible_ids

    def drop_object(self, object_id: str) -> dict[str, Any]:
        """Moves an object from hand_slot to the current location."""
        # Corrected Check: Ensure the object ID is actually in the hand_slot list
        if object_id not in self.hand_slot:
            # This check ensures the handler doesn't proceed if the item isn't held.
            # The calling handler (handle_drop) should ideally verify this first.
            return {"success": False, "message": f"You aren't holding the {self._get_object_name(object_id)}."} 

        # Attempt to add the object to the current location FIRST
        added_to_location = self._add_object_to_location(object_id)
        if not added_to_location:
            logger.error(f"Failed to add '{object_id}' to location {self.current_room_id}/{self.current_area_id} when dropping.")
            # Keep the item in hand if adding to location fails
            return {"success": False, "message": f"You try to drop the {self._get_object_name(object_id)}, but can't find a place for it here."} 

        # If adding to location succeeded, now remove from hand_slot
        object_name = self._get_object_name(object_id) # Get name before removing
        self.hand_slot.remove(object_id)
        
        # Explicitly set the dropped object's state to visible in the room
        self.set_object_state(object_id, "is_visible", True)
        logger.info(f"Player dropped '{object_id}' ({object_name}) from hand_slot into location. Set is_visible=True.")
        
        return {"success": True, "message": f"You drop the {object_name}."}

    def wear_item(self, object_id: str) -> str:
        """Attempts to wear an item from inventory OR hand_slot. Checks rules and conflicts."""
        logger.debug(f"Attempting to wear item ID: {object_id}")
        
        # Check 1: Does the object exist?
        item_data = self.get_object_by_id(object_id)
        if not item_data:
            logger.error(f"wear_item: Cannot find data for object ID: {object_id}")
            return "Cannot find data for that item." # Keep generic message for player
            
        item_name = item_data.get("name", object_id) # Use name in messages
        
        # Check 2: Is the player actually holding it or has it in inventory?
        # (The calling function _handle_equip should ensure this, but double check)
        is_in_hands = (object_id in self.hand_slot)
        is_in_inventory = (object_id in self.inventory)
        
        if not is_in_hands and not is_in_inventory:
             logger.warning(f"wear_item: Item {object_id} ({item_name}) not found in hand_slot or inventory.")
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
             logger.error(f"wear_item: Item {object_id} ({item_name}) is wearable but missing wear_area or wear_layer.")
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
            logger.info(f"Item '{object_id}' ({item_name}) removed from hand_slot.")
        elif is_in_inventory:
            self.inventory.remove(object_id)
            logger.info(f"Item '{object_id}' ({item_name}) removed from inventory.")
            
        # Add to worn items
        self.worn_items.append(object_id)
        logger.info(f"Item '{object_id}' ({item_name}) added to worn_items.")
        
        return f"You put on the {item_name}."

    def wear_item_from_container(self, item_id_to_wear: str, container_id: str) -> str:
        """Attempts to wear an item directly from a container's storage."""
        logger.debug(f"Attempting to wear item '{item_id_to_wear}' from container '{container_id}'")

        # Check 1: Does the item exist?
        item_data = self.get_object_by_id(item_id_to_wear)
        if not item_data:
            logger.error(f"wear_item_from_container: Cannot find data for item ID: {item_id_to_wear}")
            return "Cannot find data for that item."
        item_name = item_data.get("name", item_id_to_wear)

        # Check 2: Does the container exist and have state?
        container_data = self.get_object_by_id(container_id)
        container_state = self.get_object_state(container_id)
        if not container_data or not container_state or 'contains' not in container_state:
            logger.error(f"wear_item_from_container: Container '{container_id}' data or state ('contains') missing.")
            return "Cannot access the container properly."
        container_name = container_data.get("name", container_id)

        # Check 3: Is the item actually in the container state?
        if item_id_to_wear not in container_state.get('contains', []): # Check state's list
            logger.warning(f"wear_item_from_container: Item '{item_id_to_wear}' not found in container '{container_id}' state: {container_state.get('contains', [])}")
            return f"You don't seem to have the {item_name} in the {container_name}."
        
        # Check 4: Is it wearable?
        props = item_data.get('properties', {})
        if not props.get('is_wearable'):
            return f"You cannot wear the {item_name}."
            
        # Check 5: Does it have valid wear configuration?
        wear_area = props.get('wear_area')
        wear_layer = props.get('wear_layer')
        if not wear_area or wear_layer is None:
             logger.error(f"wear_item_from_container: Item {item_id_to_wear} ({item_name}) is wearable but missing wear_area or wear_layer.")
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
            logger.info(f"Item '{item_id_to_wear}' ({item_name}) removed from container '{container_id}' ({container_name}).")
        except ValueError:
            logger.error(f"wear_item_from_container: Failed to remove '{item_id_to_wear}' from container '{container_id}' state after check.")
            return f"Something went wrong trying to take the {item_name} from the {container_name}."
            
        # Add to worn items
        self.worn_items.append(item_id_to_wear)
        logger.info(f"Item '{item_id_to_wear}' ({item_name}) added to worn_items.")
        
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
        
        logger.info(f"Item '{object_id}' ({item_name}) moved from worn_items to hand_slot.")
        return f"You take off the {item_name} and hold it."

    def _add_object_to_location(self, object_id: str) -> bool:
        """Adds an object ID to the current room or area's object list."""
        room_data = self.rooms_data.get(self.current_room_id)
        if not room_data:
            logger.error(f"_add_object_to_location: Cannot find room data for {self.current_room_id}")
            return False

        target_list_key = ""
        target_list_container = None
        target_list_index = -1 # Used only for areas

        if self.current_area_id:
            # Add to area's objects_present list
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logger.error(f"_add_object_to_location: Room {self.current_room_id} 'areas' is not a list.")
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
                logger.error(f"_add_object_to_location: Cannot find area {self.current_area_id} in room {self.current_room_id}.")
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
            logger.debug(f"Added '{object_id}' to {target_list_key} in {self.current_area_id or self.current_room_id}")
            # We might need to update the original rooms_data structure if areas list was modified
            # If we added to an area list directly from the iterated area_data, it should be reflected.
            return True
        else:
             logger.warning(f"Object '{object_id}' already present in {target_list_key} for {self.current_area_id or self.current_room_id}.")
             return False # Or True if adding duplicates is acceptable?

    def _remove_object_from_location(self, object_id: str) -> bool:
        """Removes an object ID from the current room or area's object list."""
        room_data = self.rooms_data.get(self.current_room_id)
        if not room_data:
            logger.error(f"_remove_object_from_location: Cannot find room data for {self.current_room_id}")
            return False

        target_list_key = ""
        target_list_container = None
        target_list_index = -1 # Only used for areas

        if self.current_area_id:
            # Remove from area's objects_present list
            areas = room_data.get("areas")
            if not isinstance(areas, list):
                logger.error(f"_remove_object_from_location: Room {self.current_room_id} 'areas' is not a list.")
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
                 logger.error(f"_remove_object_from_location: Cannot find area {self.current_area_id} in room {self.current_room_id}.")
                 return False
        else:
            # Remove from room's objects_present
            target_list_container = room_data
            target_list_key = "objects_present"

        # Check if the list exists and is a list
        if target_list_key not in target_list_container or not isinstance(target_list_container[target_list_key], list):
             logger.warning(f"_remove_object_from_location: List '{target_list_key}' not found or not a list in {self.current_area_id or self.current_room_id}.")
             return False

        target_list = target_list_container[target_list_key]
        original_length = len(target_list)
        item_was_in_static_list = False

        # Create a new list excluding the object_id (handles both str and dict formats)
        new_list = [item for item in target_list if not (isinstance(item, str) and item == object_id) and 
                                                      not (isinstance(item, dict) and item.get('id') == object_id)]

        if len(new_list) < original_length:
            # Update the list in the container
            target_list_container[target_list_key] = new_list
            logger.debug(f"Removed '{object_id}' from static list '{target_list_key}' in {self.current_area_id or self.current_room_id}")
            item_was_in_static_list = True
        else:
            logger.debug(f"Object '{object_id}' was not found in static list '{target_list_key}' for {self.current_area_id or self.current_room_id}. (This is okay for dynamically visible items)")
            item_was_in_static_list = False # Ensure this is false if not found in static list

        # --- BEGIN MODIFICATION for dynamic objects ---
        item_was_in_dynamic_list = False
        if self.current_room_id in self.dynamic_room_objects and \
           object_id in self.dynamic_room_objects[self.current_room_id]:
            try:
                self.dynamic_room_objects[self.current_room_id].remove(object_id)
                logger.debug(f"Removed '{object_id}' from dynamic_room_objects for room '{self.current_room_id}'.")
                item_was_in_dynamic_list = True
                if not self.dynamic_room_objects[self.current_room_id]: # If list is now empty
                    del self.dynamic_room_objects[self.current_room_id]
                    logger.debug(f"Dynamic object list for room '{self.current_room_id}' is now empty and removed.")
            except ValueError:
                # This case should ideally not be hit if the check `object_id in list` was True
                logger.warning(f"Attempted to remove '{object_id}' from dynamic list of '{self.current_room_id}', but it was not found (race condition?).")
        # --- END MODIFICATION ---

        # If the object is native to this room (has initial_room_id set to current_room_id)
        obj_base_data = self.get_object_by_id(object_id)
        if obj_base_data and obj_base_data.get("location") == self.current_room_id:
            # This object is intrinsically part of the room's definition, even if taken.
            # We set its visibility to False here to signify it's no longer 'visible loose in the room'
            # The 'take_object' method will separately handle making it visible in the player's hand.
            logger.debug(f"Marking native object '{object_id}' as not visible in room '{self.current_room_id}' after being taken/removed from lists.")
            self.set_object_state(object_id, "is_visible", False)
        elif item_was_in_static_list or item_was_in_dynamic_list:
            # If it was in the static or dynamic list and removed, its "presence" in the room is gone.
            # The 'take_object' or 'drop_object' methods will manage the object's specific 'is_visible' state.
            logger.debug(f"Object '{object_id}' removed from static or dynamic lists for room '{self.current_room_id}'. Its visibility is managed by take/drop.")

        # The operation is considered successful if it was removed from static list OR dynamic list.
        return item_was_in_static_list or item_was_in_dynamic_list

    def _get_objects_in_room(self, room_id: str) -> list[dict[str, Any]]:
        # This method is not provided in the original file or the code block
        # It's assumed to exist as it's called in the take_object method
        # Implement the logic to retrieve objects in a room based on the room_id
        # This is a placeholder and should be implemented according to your specific requirements
        return [] 

    def is_object_statically_in_room(self, object_id: str, room_id: str) -> bool:
        """Checks if an object_id is part of a room's static definition (rooms.yaml)."""
        room_data = self.rooms_data.get(room_id) # Assuming self.rooms_data holds loaded room structures
        if room_data:
            # The structure for objects in a room might be a list of dicts {'id': 'obj_id'}
            # or a list of strings (object_ids). Adjust based on actual structure.
            # Assuming 'objects' is the key in room_data for the list of object references.
            static_objects_refs = room_data.get("objects", []) # Check your rooms.yaml structure
            if static_objects_refs: # Ensure the list exists
                for obj_ref in static_objects_refs:
                    if isinstance(obj_ref, dict) and obj_ref.get('id') == object_id:
                        return True
                    elif isinstance(obj_ref, str) and obj_ref == object_id: # If it's just a list of IDs
                        return True
        return False

    def add_dynamic_object_to_room(self, room_id: str, object_id: str) -> None:
        """Adds an object ID to a room's list of dynamically present objects."""
        # from .schemas import ObjectInstance # <-- REMOVED IMPORT

        if room_id not in self.dynamic_room_objects:
            self.dynamic_room_objects[room_id] = []
        
        # Avoid duplicates if already there dynamically
        if object_id not in self.dynamic_room_objects[room_id]: # <-- SIMPLIFIED CHECK
            # Also ensure it's not a static object of the room already being managed that way
            # This check might be redundant if callers already do it, but good for safety.
            if not self.is_object_statically_in_room(object_id, room_id):
                 self.dynamic_room_objects[room_id].append(object_id) # <-- APPEND STRING ID
                 logger.debug(f"[GameState] Added dynamic object '{object_id}' to room '{room_id}'.")
            else:
                logger.debug(f"[GameState] Object '{object_id}' is static in room '{room_id}', not adding dynamically.")
        else:
            logger.debug(f"[GameState] Dynamic object '{object_id}' already present in room '{room_id}'.") 