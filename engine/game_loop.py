# engine/game_loop.py

import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger  # Changed from logging

from .command_defs import CommandIntent, ParsedIntent
from .command_handlers.basic_commands import (
    handle_inventory,
    handle_look,
    handle_quit,
    handle_unknown,
)
from .command_handlers.equipment import handle_equip
from .command_handlers.item_actions import handle_drop, handle_put, handle_take, handle_take_from
from .command_handlers.locking import handle_lock, handle_unlock

# --- Import the new handler functions ---
from .command_handlers.movement import get_location_description, handle_move
from .command_handlers.open_close_handler import (  # Added import for open/close
    handle_close,
    handle_open,
)
from .command_handlers.search import handle_search
from .content_root import get_content_root
from .game_state import GameState, PowerState
from .nlp import parser
from .nlp.parser import CommandIntent, NLPCommandParser, ParsedIntent
from .yaml_loader import YAMLLoader

# --------------------------------------

print("--- engine.game_loop module loading ---")
import sys

print(f"Python Path: {sys.path}")

# Define default paths (can be overridden)
DEFAULT_CONFIG_YAML = "game_config.yaml"
DEFAULT_ROOMS_YAML = "data/rooms.yaml"
DEFAULT_OBJECTS_YAML = "data/objects.yaml"

class GameLoop:
    """Manages the main game loop and orchestrates game flow.
    
    Responsibilities:
    - Loading configuration and game data.
    - Initializing game state and command parser.
    - Running the main input-process-output loop.
    - Dispatching parsed commands to appropriate handlers.
    - Displaying output to the player.
    """

    def __init__(self, 
                 config_yaml_path: str = DEFAULT_CONFIG_YAML,
                 rooms_yaml_path: str = DEFAULT_ROOMS_YAML, 
                 objects_yaml_path: str = DEFAULT_OBJECTS_YAML):
        """Initializes the Game Loop."""
        logger.info("Initializing Game Loop...")
        self.config_data: dict[str, Any] = {}
        self.rooms_data: dict[str, Any] = {}
        self.objects_data: dict[str, Any] = {}
        self.responses_data: dict[str, list[str]] = {} # Added for responses
        self.is_running = False
        self.content_root: Path | None = None

        # Load config first
        self.load_config(config_yaml_path)

        # Resolve content root based on active_pack, then load game data (rooms, objects, responses)
        active_pack = self.config_data.get("active_pack")
        self.content_root = get_content_root(active_pack)
        banner = f"=== Content root: {self.content_root} (pack={active_pack or 'legacy data/'}) ==="
        logger.info(banner)
        print(banner)
        self.load_game_data(rooms_yaml_path, objects_yaml_path, "data/responses.yaml")

        # Determine starting conditions from config (with defaults)
        start_room_id = self.config_data.get("start_room_id", "player_cabin") # Default to player_cabin
        start_power_str = self.config_data.get("start_power_state", "emergency") # Default to emergency
        try:
            start_power_state = PowerState(start_power_str.lower())
        except ValueError:
            logger.warning(f"Invalid start_power_state '{start_power_str}' in config. Defaulting to emergency.")
            start_power_state = PowerState.EMERGENCY
        
        # Validate start room exists
        if start_room_id not in self.rooms_data:
             logger.warning(f"Configured start_room_id '{start_room_id}' not found in loaded rooms. Defaulting to first available room.")
             start_room_id = next(iter(self.rooms_data), "unknown_start_room") # Provide a fallback key
             if start_room_id == "unknown_start_room":
                  logger.error("No rooms loaded! Cannot start game.")
                  # Handle this critical error appropriately - maybe raise an exception?
                  raise ValueError("Failed to load any rooms, cannot initialize GameState.")

        # Initialize game state, passing processed room data and initial power state
        self.game_state = GameState(current_room_id=start_room_id, 
                                    rooms_data=self.rooms_data,
                                    objects_data=self.objects_data,
                                    responses_data=self.responses_data,
                                    power_state=start_power_state) # Use loaded power state
        logger.info(f"GameState initialized. Starting room: {self.game_state.current_room_id}, Power State: {self.game_state.power_state.value}")

        # Force reload of the parser module to ensure latest code is used
        try:
            importlib.reload(parser)
            logger.info("Explicitly reloaded engine.nlp.parser module.")
        except Exception as e:
            logger.error(f"Failed to explicitly reload parser module: {e}", exc_info=True)

        # Initialize command parser, passing the game state
        self.command_parser = NLPCommandParser(self.game_state)
        logger.info("NLPCommandParser initialized.")
        
        # Initialize and setup the intent map - **NOW POINTS TO IMPORTED FUNCTIONS**
        self.intent_map: dict[CommandIntent, Callable[..., str | None]] = {}
        self._setup_intent_map()
        
        logger.info("Game Loop initialized.")

    def load_config(self, config_yaml_path: str):
        """Loads the main game configuration file."""
        logger.info(f"Loading configuration from {config_yaml_path}")
        loader = YAMLLoader(data_dir=".") # Point loader to root
        try:
            config_filename = Path(config_yaml_path).name
            self.config_data = loader.load_file(config_filename)
            logger.info("Configuration loaded successfully.")
        except FileNotFoundError:
            logger.warning(f"Config file not found: {config_yaml_path}. Using default settings.")
            self.config_data = {}
        except Exception as e:
            logger.error(f"Error loading config from {config_yaml_path}: {e}", exc_info=True)
            self.config_data = {}

    def load_game_data(self, rooms_yaml_path: str, objects_yaml_path: str, responses_yaml_path: str):
        """Loads room, object, and response data from YAML files."""
        logger.info(f"Loading game data from {rooms_yaml_path}, {objects_yaml_path}, and {responses_yaml_path}")
        data_dir = str(self.content_root) if self.content_root else "data"
        loader = YAMLLoader(data_dir=data_dir)
        self.rooms_data = {}
        self.objects_data = {}
        self.responses_data = {} # Initialize responses_data

        # --- Load Rooms --- 
        try:
            rooms_filename = Path(rooms_yaml_path).name
            loaded_room_structure = loader.load_file(rooms_filename)
            if isinstance(loaded_room_structure, dict) and 'rooms' in loaded_room_structure and isinstance(loaded_room_structure['rooms'], list):
                raw_room_list = loaded_room_structure['rooms']
                self.rooms_data = {room_data['room_id']: room_data for room_data in raw_room_list if 'room_id' in room_data}
                logger.info(f"Processed {len(self.rooms_data)} rooms into dictionary.")
            else:
                logger.error(f"Unexpected structure in {rooms_filename}. Expected dict with 'rooms' list.")
        except FileNotFoundError:
            logger.error(f"Rooms file not found: {rooms_yaml_path}. Cannot load rooms.")
            # Consider raising an error here if rooms are essential
        except Exception as e:
            logger.error(f"Error loading/processing rooms from {rooms_yaml_path}: {e}", exc_info=True)
            
        # --- Load Objects --- 
        try:
            objects_filename = Path(objects_yaml_path).name
            loaded_object_structure = loader.load_file(objects_filename)
            if isinstance(loaded_object_structure, dict) and 'objects' in loaded_object_structure and isinstance(loaded_object_structure['objects'], list):
                raw_object_list = loaded_object_structure['objects']
                self.objects_data = {obj_data['id']: obj_data for obj_data in raw_object_list if 'id' in obj_data}
                logger.info(f"Processed {len(self.objects_data)} objects into dictionary.")
            else:
                 logger.warning(f"Unexpected structure in {objects_filename}. Expected dict with 'objects' list.")
        except FileNotFoundError:
            logger.warning(f"Objects file not found: {objects_yaml_path}. Proceeding without objects.")
        except Exception as e:
            logger.error(f"Error loading/processing objects from {objects_yaml_path}: {e}", exc_info=True)
            
        # --- Load Responses --- 
        try:
            responses_filename = Path(responses_yaml_path).name
            loaded_responses = loader.load_file(responses_filename)
            if isinstance(loaded_responses, dict):
                 self.responses_data = loaded_responses
                 logger.info(f"Loaded {len(self.responses_data)} response categories.")
                 logger.debug(f"Loaded response keys: {list(self.responses_data.keys())}") # Added logging for keys
            else:
                 logger.warning(f"Unexpected structure in {responses_filename}. Expected a dictionary.")
        except FileNotFoundError:
            logger.warning(f"Responses file not found: {responses_yaml_path}. Using default responses.")
            # We might want default hardcoded responses here as a fallback
        except Exception as e:
            logger.error(f"Error loading responses from {responses_yaml_path}: {e}", exc_info=True)

    def run(self):
        """Starts and runs the main game loop."""
        self.is_running = True
        logger.info("Starting game loop...")
        print("\nWelcome to Starship Adventure 2!\n")

        # Display initial location description using the imported helper
        initial_description = get_location_description(self.game_state, self.game_state.current_room_id, self.game_state.current_area_id)
        self.display_output(initial_description)

        while self.is_running:
            command_input = input("> ").strip()
            if not command_input:
                continue

            try:
                parsed_intent = self.command_parser.parse_command(command_input)
                logger.debug(f"Parsed: {parsed_intent}") 
            except Exception as e:
                logger.error(f"Error parsing command '{command_input}': {e}", exc_info=True)
                self.display_output("An error occurred while parsing your command.")
                continue

            # Process command and get the message OR None (for quit)
            message = self.process_command(parsed_intent)

            # Check if the handler signaled to quit (returned None)
            if message is None:
                 self.is_running = False
                 message = "Quitting game. Goodbye!" # Provide final message

            # Display the message if it's not empty (handle_inventory returns "")
            if message:
                 self.display_output(message)
                
        logger.info("Game loop stopped.")
        # Final goodbye is now handled within the loop

    def process_command(self, parsed_intent: ParsedIntent) -> str | None:
        """Processes the parsed command intent and returns the response message."""
        handler = self.intent_map.get(parsed_intent.intent, handle_unknown)
        logger.info(f"Dispatching intent {parsed_intent.intent} to handler: {handler.__name__}")

        try:
            # Pass game_state and parsed_intent to the handler
            result_messages = handler(self.game_state, parsed_intent)
            
            # Handlers now return a list of message dictionaries or None to quit
            if result_messages is None:
                return None # Signal to quit
                
            if not isinstance(result_messages, list):
                logger.error(f"Handler {handler.__name__} returned unexpected type: {type(result_messages)}. Expected List[Dict].")
                return "An internal error occurred with that command."
                
            # Format the list of messages into a single string for display
            formatted_output = []
            for msg_dict in result_messages:
                 if isinstance(msg_dict, dict) and 'key' in msg_dict:
                     key = msg_dict['key']
                     data = msg_dict.get('data', {})
                     # Get formatted response using the game loop's method
                     formatted_output.append(self.get_formatted_response(key, **data))
                 else:
                     # Handle direct string messages or invalid formats if necessary
                     logger.warning(f"Handler {handler.__name__} returned non-standard message format: {msg_dict}")
                     formatted_output.append(str(msg_dict)) # Attempt basic string conversion
                     
            return "\n".join(formatted_output)
            
        except Exception as e:
            logger.error(f"Error executing handler {handler.__name__} for intent {parsed_intent.intent}: {e}", exc_info=True)
            return self.get_formatted_response("error_generic") # Use a response key for generic errors

    def _setup_intent_map(self):
        """Initializes the mapping from CommandIntent to handler functions."""
        # Map intents to their corresponding handler functions
        self.intent_map = {
            CommandIntent.MOVE: handle_move,
            CommandIntent.LOOK: handle_look,
            CommandIntent.INVENTORY: handle_inventory,
            CommandIntent.QUIT: handle_quit,
            CommandIntent.TAKE: handle_take,
            CommandIntent.DROP: handle_drop,
            CommandIntent.EQUIP: handle_equip, # Covers wear/remove/wield etc.
            CommandIntent.SEARCH: handle_search,
            CommandIntent.PUT: handle_put,
            CommandIntent.TAKE_FROM: handle_take_from,
            CommandIntent.LOCK: handle_lock,         # <-- ADD LOCK
            CommandIntent.UNLOCK: handle_unlock,     # <-- ADD UNLOCK
            CommandIntent.OPEN: handle_open,      # Added OPEN mapping
            CommandIntent.CLOSE: handle_close,    # Added CLOSE mapping
            # Add other intents and handlers here as they are implemented
            # e.g., CommandIntent.HELP: handle_help,
            CommandIntent.UNKNOWN: handle_unknown
        }
        logger.info("Command intent map configured.")
        logger.debug(f"Intent Map: {[(intent.name, func.__name__) for intent, func in self.intent_map.items()]}")

    def get_formatted_response(self, key: str, **kwargs) -> str:
        """Retrieves and formats a response string from loaded responses."""
        logger.debug(f"Attempting to get response for key: >>>{key}<<<Data: {kwargs}") # Added logging for requested key & data
        response_list = self.responses_data.get(key, [])
        if not response_list:
            logger.warning(f"No responses found for key: '{key}'")
            return f"(Action '{key}' occurred, but response text is missing.)"
            
        import random
        chosen_template = random.choice(response_list)
        logger.debug(f"[get_formatted_response] Key: '{key}', Chosen Template: '{chosen_template}'") # Log chosen template
        
        try:
            formatted_message = chosen_template.format(**kwargs)
            logger.debug(f"[get_formatted_response] Formatted Message: '{formatted_message}'") # Log result
            return formatted_message
        except KeyError as e:
            logger.error(f"Missing placeholder '{e}' in response template for key '{key}': '{chosen_template}'")
            # Return the template with a warning if formatting fails
            return f"(Response formatting error for '{key}': {chosen_template})"
        except Exception as e:
            logger.error(f"Unexpected error formatting response for key '{key}': {e}", exc_info=True)
            return f"(Response formatting error for '{key}')"

    def display_output(self, message: str):
        """Prints the game's output to the console."""
        if message: # Ensure message is not empty
            print(f"\n{message}\n") # Removed marker

    def main():
        """Entry point for running the game loop directly (e.g., for testing)."""
        # Setup basic logging for testing this module directly
        # Change level to DEBUG to see detailed parser logs
        logger.configure(handlers=[{"sink": sys.stderr, "level": "CRITICAL", "format": "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"}]) # Changed to logger.configure
        
        try:
            game_loop = GameLoop()
            game_loop.run() 
        except Exception as e:
             logger.critical(f"Game loop failed to initialize or run: {e}", exc_info=True)
             print(f"\nCRITICAL ERROR: {e}") 

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    GameLoop.main() 