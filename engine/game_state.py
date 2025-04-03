from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json
from datetime import datetime, timedelta

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
    power_state: PowerState
    current_area_id: Optional[str] = None
    inventory: List[str] = None  # List of object IDs
    visited_rooms: Set[str] = None  # Set of room IDs
    visited_areas: Set[str] = None  # Set of area IDs
    game_flags: Dict[str, bool] = None  # For tracking game progress/puzzles
    player_status: PlayerStatus = None  # Player's health and status
    game_time: datetime = None  # Current game time
    object_states: Dict[str, Dict] = None  # Track object states and positions
    last_save_time: Optional[datetime] = None  # Last time the game was saved

    def __post_init__(self):
        """Initialize collections if they're None."""
        if self.inventory is None:
            self.inventory = []
        if self.visited_rooms is None:
            self.visited_rooms = set()
        if self.visited_areas is None:
            self.visited_areas = set()
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

    def visit_area(self, area_id: str) -> None:
        """Mark an area as visited."""
        self.visited_areas.add(area_id)

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
            'visited_areas': list(self.visited_areas),
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
        game_state.visited_areas = set(save_data['visited_areas'])
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