from enum import Enum
from dataclasses import dataclass
from typing import Optional

class CommandIntent(Enum):
    """Enum representing different types of command intents."""
    UNKNOWN = "unknown"
    MOVE = "move"
    LOOK = "look"
    TAKE = "take"
    DROP = "drop"
    USE = "use"
    INVENTORY = "inventory"
    HELP = "help"
    QUIT = "quit"
    SAVE = "save"
    LOAD = "load"
    COMMUNICATE = "communicate"
    COMBAT = "combat"
    SEARCH = "search"
    MANIPULATE = "manipulate"
    CLIMB = "climb"
    SOCIAL = "social"
    ENVIRONMENT = "environment"
    GATHER_INFO = "gather_info"
    EQUIP = "equip"
    TIME = "time"
    COMPLEX = "complex"

@dataclass
class ParsedIntent:
    """Class to hold the parsed command information."""
    intent: CommandIntent
    action: Optional[str] = None
    target: Optional[str] = None
    target_object_id: Optional[str] = None
    direction: Optional[str] = None
    confidence: float = 0.0
    original_input: str = "" 