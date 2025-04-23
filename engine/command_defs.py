from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any

class CommandIntent(Enum):
    """Enum representing different types of command intents."""
    UNKNOWN = auto()
    MOVE = auto()
    LOOK = auto()
    TAKE = auto()
    DROP = auto()
    USE = auto()
    INVENTORY = auto()
    HELP = auto()
    QUIT = auto()
    SAVE = auto()
    LOAD = auto()
    COMMUNICATE = auto()
    COMBAT = auto()
    SEARCH = auto()
    MANIPULATE = auto()
    CLIMB = auto()
    SOCIAL = auto()
    ENVIRONMENT = auto()
    GATHER_INFO = auto()
    EQUIP = auto()
    TIME = auto()
    COMPLEX = auto()
    PUT = auto()
    TAKE_FROM = auto()
    LOCK = auto()
    UNLOCK = auto()
    OPEN = auto()
    CLOSE = auto()
    SCORE = auto()
    INVALID = auto()

@dataclass
class ParsedIntent:
    """Class to hold the parsed command information."""
    intent: CommandIntent
    action: Optional[str] = None
    target: Optional[str] = None
    target_object_id: Optional[str] = None
    secondary_target: Optional[str] = None
    secondary_target_id: Optional[str] = None
    direction: Optional[str] = None
    preposition: Optional[str] = None
    original_input: str = ""