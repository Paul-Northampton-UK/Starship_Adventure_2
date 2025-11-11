from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


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
    ATTACK = auto()
    AIM = auto()
    SHOOT = auto()
    BLOCK = auto()
    DODGE = auto()
    FLEE = auto()
    SEARCH = auto()
    SCAN = auto()
    MANIPULATE = auto()
    CLIMB = auto()
    SOCIAL = auto()
    READ = auto()
    TALK = auto()
    ASK = auto()
    GIVE = auto()
    SHOW = auto()
    ENVIRONMENT = auto()
    GATHER_INFO = auto()
    EQUIP = auto()
    UNEQUIP = auto()
    WEAR = auto()
    REMOVE = auto()
    WIELD = auto()
    RELOAD = auto()
    UNLOAD = auto()
    CHECK = auto()
    SNEAK = auto()
    HIDE = auto()
    PICKPOCKET = auto()
    DISARM_TRAP = auto()
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
    action: str | None = None
    target: str | None = None
    target_object_id: str | None = None
    secondary_target: str | None = None
    secondary_target_id: str | None = None
    direction: str | None = None
    preposition: str | None = None
    original_input: str = ""
    confidence: float = 1.0

@dataclass
class CommandResponse:
    """Class to hold the response from a command handler."""
    handler_name: str
    intent_name: CommandIntent # Using the CommandIntent enum for type safety
    original_input: str
    message: str
    status_code: int # HTTP-like status codes (e.g., 200 OK, 400 Bad Request, 404 Not Found)
    room_id: str # Current room ID, useful for client updates
    target_object_name: str | None = None
    extra_data: dict[str, Any] | None = field(default_factory=dict)
