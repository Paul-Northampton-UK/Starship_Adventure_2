# engine/game_loop.py

import logging
from typing import Dict, Any, Optional, Callable
from .game_state import GameState, PowerState
from .nlp_command_parser import NLPCommandParser
from .command_defs import CommandIntent, ParsedIntent
from .yaml_loader import YAMLLoader
from pathlib import Path

# --- Import the new handler functions ---
from .command_handlers.movement import handle_move, get_location_description
from .command_handlers.item_actions import handle_take, handle_drop
from .command_handlers.equipment import handle_equip
from .command_handlers.basic_commands import handle_look, handle_inventory, handle_quit, handle_unknown
# --------------------------------------

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
        logging.info("Initializing Game Loop...")
        self.config_data: Dict[str, Any] = {}
        self.rooms_data: Dict[str, Any] = {}
        self.objects_data: Dict[str, Any] = {}
        self.is_running = False

        # Load config first
        self.load_config(config_yaml_path)

        # Load and process game data
        self.load_game_data(rooms_yaml_path, objects_yaml_path)

        # Determine starting conditions from config (with defaults)
        start_room_id = self.config_data.get("start_room_id", "player_cabin") # Default to player_cabin
        start_power_str = self.config_data.get("start_power_state", "emergency") # Default to emergency
        try:
            start_power_state = PowerState(start_power_str.lower())
        except ValueError:
            logging.warning(f"Invalid start_power_state '{start_power_str}' in config. Defaulting to emergency.")
            start_power_state = PowerState.EMERGENCY
        
        # Validate start room exists
        if start_room_id not in self.rooms_data:
             logging.warning(f"Configured start_room_id '{start_room_id}' not found in loaded rooms. Defaulting to first available room.")
             start_room_id = next(iter(self.rooms_data), "unknown_start_room") # Provide a fallback key
             if start_room_id == "unknown_start_room":
                  logging.error("No rooms loaded! Cannot start game.")
                  # Handle this critical error appropriately - maybe raise an exception?
                  raise ValueError("Failed to load any rooms, cannot initialize GameState.")

        # Initialize game state, passing processed room data and initial power state
        self.game_state = GameState(current_room_id=start_room_id, 
                                    rooms_data=self.rooms_data,
                                    objects_data=self.objects_data,
                                    power_state=start_power_state) # Use loaded power state
        logging.info(f"GameState initialized. Starting room: {self.game_state.current_room_id}, Power State: {self.game_state.power_state.value}")

        # Initialize command parser, passing the game state
        self.command_parser = NLPCommandParser(self.game_state)
        logging.info("NLPCommandParser initialized.")
        
        # Initialize and setup the intent map - **NOW POINTS TO IMPORTED FUNCTIONS**
        self.intent_map: Dict[CommandIntent, Callable[..., Optional[str]]] = {}
        self._setup_intent_map()
        
        logging.info("Game Loop initialized.")

    def load_config(self, config_yaml_path: str):
        """Loads the main game configuration file."""
        logging.info(f"Loading configuration from {config_yaml_path}")
        loader = YAMLLoader(data_dir=".") # Point loader to root
        try:
            config_filename = Path(config_yaml_path).name
            self.config_data = loader.load_file(config_filename)
            logging.info(f"Configuration loaded successfully.")
        except FileNotFoundError:
            logging.warning(f"Config file not found: {config_yaml_path}. Using default settings.")
            self.config_data = {}
        except Exception as e:
            logging.error(f"Error loading config from {config_yaml_path}: {e}", exc_info=True)
            self.config_data = {}

    def load_game_data(self, rooms_yaml_path: str, objects_yaml_path: str):
        """Loads room and object data from YAML files and processes them into dictionaries keyed by ID."""
        logging.info(f"Loading game data from {rooms_yaml_path} and {objects_yaml_path}")
        loader = YAMLLoader() # Uses default data_dir='data'
        self.rooms_data = {}
        self.objects_data = {}

        try:
            rooms_filename = Path(rooms_yaml_path).name
            loaded_room_structure = loader.load_file(rooms_filename)
            if isinstance(loaded_room_structure, dict) and 'rooms' in loaded_room_structure and isinstance(loaded_room_structure['rooms'], list):
                raw_room_list = loaded_room_structure['rooms']
                self.rooms_data = {room_data['room_id']: room_data for room_data in raw_room_list if 'room_id' in room_data}
                logging.info(f"Processed {len(self.rooms_data)} rooms into dictionary.")
            else:
                logging.error(f"Unexpected structure in {rooms_filename}. Expected dict with 'rooms' list.")
        except FileNotFoundError:
            logging.error(f"Rooms file not found: {rooms_yaml_path}. Cannot load rooms.")
        except Exception as e:
            logging.error(f"Error loading/processing rooms from {rooms_yaml_path}: {e}", exc_info=True)
            
        try:
            objects_filename = Path(objects_yaml_path).name
            loaded_object_structure = loader.load_file(objects_filename)
            if isinstance(loaded_object_structure, dict) and 'objects' in loaded_object_structure and isinstance(loaded_object_structure['objects'], list):
                raw_object_list = loaded_object_structure['objects']
                self.objects_data = {obj_data['id']: obj_data for obj_data in raw_object_list if 'id' in obj_data}
                logging.info(f"Processed {len(self.objects_data)} objects into dictionary.")
            else:
                 logging.warning(f"Unexpected structure in {objects_filename}. Expected dict with 'objects' list.")
        except FileNotFoundError:
            logging.warning(f"Objects file not found: {objects_yaml_path}. Proceeding without objects.")
        except Exception as e:
            logging.error(f"Error loading/processing objects from {objects_yaml_path}: {e}", exc_info=True)

    def run(self):
        """Starts and runs the main game loop."""
        self.is_running = True
        logging.info("Starting game loop...")
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
                logging.debug(f"Parsed: {parsed_intent}") 
            except Exception as e:
                logging.error(f"Error parsing command '{command_input}': {e}", exc_info=True)
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
                
        logging.info("Game loop stopped.")
        # Final goodbye is now handled within the loop

    def process_command(self, parsed_intent: ParsedIntent) -> Optional[str]:
        """Processes the parsed command intent by dispatching to the appropriate handler."""
        intent = parsed_intent.intent
        logging.debug(f"Processing intent: {intent} with data: {parsed_intent}")

        handler = self.intent_map.get(intent)

        if handler:
            try:
                # Pass game_state and parsed_intent to all handlers
                # Special case for handle_inventory to pass display_output callback
                if handler == handle_inventory:
                    # handle_inventory returns "", output is via callback
                    return handler(self.game_state, parsed_intent, self.display_output)
                else:
                    # Other handlers return a message string or None (for quit)
                    return handler(self.game_state, parsed_intent)
                    
            except Exception as e:
                logging.exception(f"Error executing handler for intent: {intent}")
                return "An internal error occurred while processing your command."
        else:
            # This case should ideally be handled by handle_unknown, but as a fallback:
            logging.warning(f"No handler explicitly mapped for intent: {intent}")
            return "I don't understand that command or it hasn't been implemented yet."

    def _setup_intent_map(self):
        """Initializes the mapping from CommandIntent to imported handler functions."""
        self.intent_map = {
            CommandIntent.MOVE: handle_move,
            CommandIntent.LOOK: handle_look,
            CommandIntent.TAKE: handle_take,
            CommandIntent.DROP: handle_drop,
            CommandIntent.INVENTORY: handle_inventory,
            CommandIntent.EQUIP: handle_equip,
            CommandIntent.QUIT: handle_quit,
            CommandIntent.UNKNOWN: handle_unknown,
            # Add other intents here and map them to appropriate handlers 
            # (e.g., handle_use, handle_interact, etc.) when implemented.
        }
        logging.info(f"Intent map initialized with {len(self.intent_map)} handlers pointing to imported functions.")

    def display_output(self, message: str):
        """Prints output to the console (can be overridden for GUI)."""
        print(f"\n{message}\n") # Add blank lines for readability

# --- Old handler methods removed from GameLoop class --- 

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    # Setup basic logging for testing this module directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        game_loop = GameLoop()
        game_loop.run() 
    except Exception as e:
         logging.critical(f"Game loop failed to initialize or run: {e}", exc_info=True)
         print(f"\nCRITICAL ERROR: {e}") 