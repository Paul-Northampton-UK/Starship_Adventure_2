from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from .game_state import GameState, PowerState

class CommandType(Enum):
    """Types of commands that can be processed."""
    LOOK = "look"
    GO = "go"
    TAKE = "take"
    DROP = "drop"
    USE = "use"
    INVENTORY = "inventory"
    SAVE = "save"
    LOAD = "load"
    QUIT = "quit"
    HELP = "help"
    UNKNOWN = "unknown"

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
class ParsedCommand:
    """Represents a parsed command with its components."""
    command_type: CommandType
    target: Optional[str] = None
    preposition: Optional[str] = None
    indirect_object: Optional[str] = None
    raw_input: str = ""

@dataclass
class ParsedIntent:
    """Class to hold the parsed command information."""
    intent: CommandIntent
    action: Optional[str] = None
    target: Optional[str] = None
    direction: Optional[str] = None
    confidence: float = 0.0
    raw_input: str = ""

class CommandParser:
    """Handles parsing and processing of player commands."""
    
    # Command aliases mapping
    COMMAND_ALIASES: Dict[str, CommandType] = {
        # Look commands
        "look": CommandType.LOOK,
        "l": CommandType.LOOK,
        "examine": CommandType.LOOK,
        "x": CommandType.LOOK,
        
        # Movement commands
        "go": CommandType.GO,
        "move": CommandType.GO,
        "walk": CommandType.GO,
        "run": CommandType.GO,
        "north": CommandType.GO,
        "n": CommandType.GO,
        "south": CommandType.GO,
        "s": CommandType.GO,
        "east": CommandType.GO,
        "e": CommandType.GO,
        "west": CommandType.GO,
        "w": CommandType.GO,
        "up": CommandType.GO,
        "u": CommandType.GO,
        "down": CommandType.GO,
        "d": CommandType.GO,
        
        # Inventory commands
        "take": CommandType.TAKE,
        "get": CommandType.TAKE,
        "grab": CommandType.TAKE,
        "pick up": CommandType.TAKE,
        "drop": CommandType.DROP,
        "put down": CommandType.DROP,
        "inventory": CommandType.INVENTORY,
        "i": CommandType.INVENTORY,
        "inv": CommandType.INVENTORY,
        
        # Interaction commands
        "use": CommandType.USE,
        "activate": CommandType.USE,
        "operate": CommandType.USE,
        
        # System commands
        "save": CommandType.SAVE,
        "load": CommandType.LOAD,
        "quit": CommandType.QUIT,
        "q": CommandType.QUIT,
        "exit": CommandType.QUIT,
        "help": CommandType.HELP,
        "h": CommandType.HELP,
        "?": CommandType.HELP,
    }
    
    # Prepositions that can be used in commands
    PREPOSITIONS = {"with", "on", "in", "at", "to", "from", "into", "onto", "through"}
    
    def __init__(self, game_state: GameState):
        """Initialize the command parser with a game state."""
        self.game_state = game_state
    
    def parse_command(self, command_input: str) -> ParsedCommand:
        """Parse a command string into a ParsedCommand object."""
        # Clean and normalize input
        command_input = command_input.strip().lower()
        if not command_input:
            return ParsedCommand(CommandType.UNKNOWN, raw_input=command_input)
        
        # Split input into words
        words = command_input.split()
        
        # Check for command type
        command_type = self.COMMAND_ALIASES.get(words[0], CommandType.UNKNOWN)
        
        # Handle movement commands that are just directions
        if command_type == CommandType.GO and len(words) == 1:
            return ParsedCommand(
                command_type=CommandType.GO,
                target=words[0],
                raw_input=command_input
            )
        
        # Handle simple commands without targets
        if command_type in {CommandType.INVENTORY, CommandType.SAVE, 
                          CommandType.LOAD, CommandType.QUIT, CommandType.HELP}:
            return ParsedCommand(
                command_type=command_type,
                raw_input=command_input
            )
        
        # Handle commands with targets
        if len(words) < 2:
            return ParsedCommand(
                command_type=command_type,
                raw_input=command_input
            )
        
        # Special handling for look commands with "at"
        if command_type == CommandType.LOOK and len(words) >= 3 and words[1] == "at":
            return ParsedCommand(
                command_type=command_type,
                target=" ".join(words[2:]),
                raw_input=command_input
            )
        
        # Check for preposition
        preposition = None
        target = words[1]
        indirect_object = None
        
        for i, word in enumerate(words[2:], 2):
            if word in self.PREPOSITIONS:
                preposition = word
                if i + 1 < len(words):
                    indirect_object = " ".join(words[i + 1:])
                break
        
        return ParsedCommand(
            command_type=command_type,
            target=target,
            preposition=preposition,
            indirect_object=indirect_object,
            raw_input=command_input
        )
    
    def process_command(self, command_input: str) -> Tuple[str, bool]:
        """Process a command and return the result and whether the game should continue."""
        parsed = self.parse_command(command_input)
        
        if parsed.command_type == CommandType.UNKNOWN:
            return "I don't understand that command.", True
        
        # Process the command based on its type
        if parsed.command_type == CommandType.LOOK:
            return self._process_look(parsed), True
        elif parsed.command_type == CommandType.GO:
            return self._process_go(parsed), True
        elif parsed.command_type == CommandType.TAKE:
            return self._process_take(parsed), True
        elif parsed.command_type == CommandType.DROP:
            return self._process_drop(parsed), True
        elif parsed.command_type == CommandType.USE:
            return self._process_use(parsed), True
        elif parsed.command_type == CommandType.INVENTORY:
            return self._process_inventory(), True
        elif parsed.command_type == CommandType.SAVE:
            return self._process_save(), True
        elif parsed.command_type == CommandType.LOAD:
            return self._process_load(), True
        elif parsed.command_type == CommandType.QUIT:
            return "Goodbye!", False
        elif parsed.command_type == CommandType.HELP:
            return self._process_help(), True
        
        return "I don't know how to do that.", True
    
    def _process_look(self, parsed: ParsedCommand) -> str:
        """Process a look command."""
        if not parsed.target:
            # Look at current location
            return f"You are in the {self.game_state.current_room_id}"
        else:
            # Look at specific object
            return f"You look at the {parsed.target}"
    
    def _process_go(self, parsed: ParsedCommand) -> str:
        """Process a go command."""
        if not parsed.target:
            return "Go where?"
        
        # Handle direction commands
        if parsed.target in {"north", "n", "south", "s", "east", "e", 
                           "west", "w", "up", "u", "down", "d"}:
            return f"You move {parsed.target}"
        else:
            return f"You try to go to the {parsed.target}"
    
    def _process_take(self, parsed: ParsedCommand) -> str:
        """Process a take command."""
        if not parsed.target:
            return "Take what?"
        return f"You try to take the {parsed.target}"
    
    def _process_drop(self, parsed: ParsedCommand) -> str:
        """Process a drop command."""
        if not parsed.target:
            return "Drop what?"
        return f"You try to drop the {parsed.target}"
    
    def _process_use(self, parsed: ParsedCommand) -> str:
        """Process a use command."""
        if not parsed.target:
            return "Use what?"
        if parsed.preposition and parsed.indirect_object:
            return f"You try to use the {parsed.target} {parsed.preposition} the {parsed.indirect_object}"
        return f"You try to use the {parsed.target}"
    
    def _process_inventory(self) -> str:
        """Process an inventory command."""
        if not self.game_state.inventory:
            return "Your inventory is empty."
        return f"Your inventory contains: {', '.join(self.game_state.inventory)}"
    
    def _process_save(self) -> str:
        """Process a save command."""
        try:
            self.game_state.save_game("save_game.json")
            return "Game saved successfully."
        except Exception as e:
            return f"Failed to save game: {str(e)}"
    
    def _process_load(self) -> str:
        """Process a load command."""
        try:
            self.game_state = GameState.load_game("save_game.json")
            return "Game loaded successfully."
        except Exception as e:
            return f"Failed to load game: {str(e)}"
    
    def _process_help(self) -> str:
        """Process a help command."""
        return """Available commands:
- look/l/examine/x [object]: Look around or examine an object
- go/move/walk/run [direction]: Move in a direction
- take/get/grab [object]: Pick up an object
- drop/put down [object]: Drop an object
- inventory/i/inv: Check your inventory
- use/activate/operate [object] [with/on/in] [target]: Use an object
- save: Save your game
- load: Load your game
- quit/q/exit: Exit the game
- help/h/?: Show this help message""" 