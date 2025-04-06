from typing import List, Tuple, Optional, Set, Dict, Union
from pydantic import BaseModel, Field, field_validator, constr
from enum import Enum
import re

class WearArea(str, Enum):
    """Defines areas on the body where items can be worn."""
    HEAD = "head"
    FACE = "face" # For masks, visors
    NECK = "neck"
    TORSO = "torso" # ADDED Single torso area
    BACK = "back" # Backpacks, tanks
    ARMS = "arms"
    HANDS = "hands" # Gloves
    LEGS = "legs" # Trousers
    FEET = "feet" # Boots, socks

class LocationMode(str, Enum):
    MAIN_SHIP = "main_ship"
    YACHT = "yacht"
    SPACE = "space"

class DeckLevel(int, Enum):
    CAPTAINS_SUITE = 1
    BRIDGE_DECK = 2
    CREW_QUARTERS = 3
    ENGINEERING = 4
    CARGO_BAY = 5

class RoomState(str, Enum):
    OFFLINE = "offline"
    EMERGENCY = "emergency"
    MAIN_POWER = "main_power"
    TORCH_LIGHT = "torch_light"

class RoomDescription(BaseModel):
    """Model for room descriptions in different states"""
    offline: constr(min_length=1, max_length=1000) = Field(..., description="Description when room is offline")
    emergency: constr(min_length=1, max_length=1000) = Field(..., description="Description when room is in emergency mode")
    main_power: constr(min_length=1, max_length=1000) = Field(..., description="Description when room has main power")
    torch_light: constr(min_length=1, max_length=1000) = Field(..., description="Description when room is lit by torch")

class RoomExit(BaseModel):
    """Model for room exits"""
    direction: constr(min_length=1, max_length=20) = Field(..., description="Direction of the exit")
    destination: constr(min_length=1, max_length=50) = Field(..., description="Room ID of the destination")

    @field_validator('direction')
    @classmethod
    def validate_direction(cls, v: str) -> str:
        """Validate exit direction is one of the standard directions"""
        valid_directions = {
            'north', 'n', 'south', 's', 'east', 'e', 'west', 'w',
            'northeast', 'ne', 'northwest', 'nw', 'southeast', 'se',
            'southwest', 'sw', 'up', 'u', 'down', 'd', 'in', 'out'
        }
        if v.lower() not in valid_directions:
            raise ValueError(f"Invalid direction: {v}. Must be one of {valid_directions}")
        return v.lower()

class Room(BaseModel):
    """Main model for room data"""
    room_id: constr(min_length=1, max_length=50, pattern=r'^[a-z0-9_]+$') = Field(
        ..., 
        description="Unique identifier for the room (lowercase letters, numbers, and underscores only)"
    )
    name: constr(min_length=1, max_length=100) = Field(..., description="Display name of the room")
    room_count: int = Field(..., description="Number of instances of this room")
    location_mode: LocationMode = Field(..., description="Global environment state")
    deck_level: DeckLevel = Field(..., description="Deck level number")
    grid_reference: Tuple[int, int] = Field(..., description="Bottom-left corner coordinates")
    grid_size: Tuple[int, int] = Field(..., description="Room dimensions in grid units")
    
    # Room properties
    windows_present: bool = Field(..., description="Whether the room has windows")
    backup_power: bool = Field(..., description="Whether the room has backup power")
    emergency_exit: bool = Field(..., description="Whether emergency lighting is present")
    requires_light_source: bool = Field(..., description="Whether a light source is needed")
    
    # Room descriptions
    first_visit_description: RoomDescription
    short_description: RoomDescription
    
    # Room connections
    exits: List[RoomExit] = Field(default_factory=list)

    @field_validator('grid_reference', 'grid_size')
    @classmethod
    def validate_grid_coordinates(cls, v: Tuple[int, int]) -> Tuple[int, int]:
        """Ensure grid coordinates are non-negative"""
        if any(x < 0 for x in v):
            raise ValueError("Grid coordinates must be non-negative")
        return v

    @field_validator('room_count')
    @classmethod
    def validate_room_count(cls, v: int) -> int:
        """Ensure room count is positive"""
        if v < 1:
            raise ValueError("Room count must be positive")
        return v

    @field_validator('exits')
    @classmethod
    def validate_exits(cls, v: List[RoomExit]) -> List[RoomExit]:
        """Validate room exits"""
        # Check for duplicate directions
        directions = [exit.direction for exit in v]
        if len(directions) != len(set(directions)):
            raise ValueError("Each room can only have one exit in each direction")
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate room name"""
        # Remove leading/trailing whitespace
        v = v.strip()
        # Ensure name doesn't contain only whitespace
        if not v:
            raise ValueError("Room name cannot be empty or only whitespace")
        return v

class ObjectCategory(str, Enum):
    """Categories of objects in the game"""
    CONTAINER = "container"
    WEAPON = "weapon"
    TOOL = "tool"
    CONSUMABLE = "consumable"
    KEY_ITEM = "key_item"
    DECORATIVE = "decorative"
    READABLE = "readable"
    EQUIPMENT = "equipment"
    CLOTHING = "clothing"
    FURNITURE = "furniture"
    DEVICE = "device"
    LIGHTING = "lighting"
    FIXTURE = "fixture"
    STRUCTURE = "structure"
    ITEM = "item"

class ObjectProperties(BaseModel):
    """Properties specific to different object categories"""
    # General Object Properties
    is_interactive: bool = True
    is_takeable: bool = False
    is_dangerous: bool = False
    is_destroyable: bool = False
    is_lockable: bool = False
    is_storage: bool = False
    is_operational: bool = False
    is_edible: bool = False
    is_weapon: bool = False
    
    # Physical Object Attributes
    weight: float = 1.0
    size: float = 1.0
    is_movable: bool = False
    is_wearable: bool = False
    wear_area: Optional[WearArea] = None
    wear_layer: Optional[int] = None
    is_flammable: bool = False
    is_toxic: bool = False
    is_food: bool = False
    is_cookable: bool = False
    
    # Special Object Functions
    is_consumable: bool = False
    has_durability: bool = False
    is_hackable: bool = False
    is_hidden: bool = False
    is_rechargeable: bool = False
    is_fuel_source: bool = False
    regenerates: bool = False
    is_modular: bool = False
    
    # Digital & Interactive Objects
    is_stored: bool = False
    is_transferable: bool = False
    is_activatable: bool = False
    is_networked: bool = False
    
    # Interaction Rules
    requires_power: bool = False
    requires_item: bool = False
    has_security: bool = False
    is_sensitive: bool = False
    is_fragile: bool = False
    is_secret: bool = False
    
    # Storage properties (for containers)
    storage_capacity: Optional[float] = None
    can_store_liquids: bool = False
    
    # Combat properties (for weapons)
    damage: Optional[float] = None
    durability: Optional[int] = None
    range: Optional[float] = None
    
    @field_validator('weight', 'size', 'storage_capacity', 'damage', 'durability', 'range', 'wear_layer')
    @classmethod
    def validate_non_negative(cls, v: Optional[Union[float, int]]) -> Optional[Union[float, int]]:
        if v is not None and v < 0:
            raise ValueError("Numeric value must be non-negative")
        return v

class ObjectInteraction(BaseModel):
    """How the object can be interacted with"""
    required_state: List[str] = []  # Game states needed
    required_items: List[str] = []  # Items needed
    primary_actions: List[str] = []  # Main actions possible
    effects: List[str] = []  # What happens when used
    success_message: Optional[str] = None
    failure_message: Optional[str] = None

class Object(BaseModel):
    """Main object schema"""
    object_id: str = Field(..., pattern="^[a-z0-9_]+$", max_length=50)
    name: str = Field(..., max_length=100)
    category: ObjectCategory
    count: int = Field(..., ge=1)
    weight: float = Field(..., ge=0)
    size: float = Field(..., ge=0)
    description: str = Field(..., max_length=1000)
    is_plural: bool = False # Added flag for singular/plural distinction
    
    # Optional fields
    synonyms: List[str] = []
    initial_state: bool = True  # Visible by default
    properties: ObjectProperties = ObjectProperties()
    interaction: ObjectInteraction = ObjectInteraction()
    
    # Power and state
    power_state: Optional[str] = None  # offline, emergency, main_power, torch_light
    is_locked: bool = False
    lock_type: Optional[str] = None  # key, code, biometric
    lock_code: Optional[str] = None
    lock_key_id: Optional[str] = None
    
    # Storage
    storage_contents: List[str] = []
    
    # Optional descriptions for different states
    state_descriptions: Dict[str, str] = {}
    
    @field_validator('object_id')
    @classmethod
    def validate_object_id(cls, v: str) -> str:
        if not v.replace('_', '').isalnum():
            raise ValueError("object_id must contain only letters, numbers, and underscores")
        return v.lower()
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("description cannot be empty")
        return v
    
    @field_validator('power_state')
    @classmethod
    def validate_power_state(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_states = ["offline", "emergency", "main_power", "torch_light"]
            if v not in valid_states:
                raise ValueError(f"power_state must be one of {valid_states}")
        return v
    
    @field_validator('lock_type')
    @classmethod
    def validate_lock_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = ["key", "code", "biometric"]
            if v not in valid_types:
                raise ValueError(f"lock_type must be one of {valid_types}")
        return v 