# engine/game_loop.py

import logging
from typing import Dict, Any, Optional, Callable, List
from .game_state import GameState, PowerState
from .nlp.parser import NLPCommandParser, ParsedIntent, CommandIntent
from .command_defs import CommandIntent, ParsedIntent
from .yaml_loader import YAMLLoader
from pathlib import Path
import importlib
from .nlp import parser

# --- Import the new handler functions ---
from .command_handlers.movement import handle_move, get_location_description
from .command_handlers.item_actions import handle_take, handle_drop, handle_put, handle_take_from
from .command_handlers.equipment import handle_equip
from .command_handlers.basic_commands import handle_look, handle_inventory, handle_quit, handle_unknown
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
        logging.info("Initializing Game Loop...")
        self.config_data: Dict[str, Any] = {}
        self.rooms_data: Dict[str, Any] = {}
        self.objects_data: Dict[str, Any] = {}
        self.responses_data: Dict[str, List[str]] = {} # Added for responses
        self.is_running = False

        # Load config first
        self.load_config(config_yaml_path)

        # Load game data (rooms, objects, responses)
        self.load_game_data(rooms_yaml_path, objects_yaml_path, "data/responses.yaml")

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

        # Force reload of the parser module to ensure latest code is used
        try:
            importlib.reload(parser)
            logging.info("Explicitly reloaded engine.nlp.parser module.")
        except Exception as e:
            logging.error(f"Failed to explicitly reload parser module: {e}", exc_info=True)

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

    def load_game_data(self, rooms_yaml_path: str, objects_yaml_path: str, responses_yaml_path: str):
        """Loads room, object, and response data from YAML files."""
        logging.info(f"Loading game data from {rooms_yaml_path}, {objects_yaml_path}, and {responses_yaml_path}")
        loader = YAMLLoader() # Uses default data_dir='data'
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
                logging.info(f"Processed {len(self.rooms_data)} rooms into dictionary.")
            else:
                logging.error(f"Unexpected structure in {rooms_filename}. Expected dict with 'rooms' list.")
        except FileNotFoundError:
            logging.error(f"Rooms file not found: {rooms_yaml_path}. Cannot load rooms.")
            # Consider raising an error here if rooms are essential
        except Exception as e:
            logging.error(f"Error loading/processing rooms from {rooms_yaml_path}: {e}", exc_info=True)
            
        # --- Load Objects --- 
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
            
        # --- Load Responses --- 
        try:
            responses_filename = Path(responses_yaml_path).name
            loaded_responses = loader.load_file(responses_filename)
            if isinstance(loaded_responses, dict):
                 self.responses_data = loaded_responses
                 logging.info(f"Loaded {len(self.responses_data)} response categories.")
            else:
                 logging.warning(f"Unexpected structure in {responses_filename}. Expected a dictionary.")
        except FileNotFoundError:
            logging.warning(f"Responses file not found: {responses_yaml_path}. Using default responses.")
            # We might want default hardcoded responses here as a fallback
        except Exception as e:
            logging.error(f"Error loading responses from {responses_yaml_path}: {e}", exc_info=True)

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
        """Processes the parsed command intent, calls the handler,
           and formats the response using get_formatted_response.
           Returns the final message string or None (for quit).
        """
        intent = parsed_intent.intent
        logging.debug(f"Processing intent: {intent} with data: {parsed_intent}")

        handler = self.intent_map.get(intent)

        if handler:
            try:
                # Special case for handle_inventory which uses a display callback
                if handler == handle_inventory:
                    handler_result = handler(self.game_state, parsed_intent, self.display_output)
                    # It returns () on success, handle if it raises an error instead?
                    return "" # Indicate no further message needed

                # Call other handlers
                handler_result = handler(self.game_state, parsed_intent)

                # Check handler result type
                if handler_result is None:
                    # Signal to quit the game loop (handled in run method)
                    return None
                elif isinstance(handler_result, tuple) and len(handler_result) == 2:
                    # Expected result: (response_key, kwargs_dict)
                    key, kwargs = handler_result

                    # Handle direct description returns (from move or look)
                    if key in ["move_success_description", "look_success_room", "look_success_item"]:
                        return kwargs.get("description", "(Description missing)") # Return pre-formatted description
                    else:
                         # Format other responses using the key and kwargs
                         logging.debug(f"Calling get_formatted_response with key='{key}', kwargs={kwargs}") # Log before call
                         formatted_message = self.get_formatted_response(key, **kwargs)
                         logging.debug(f"Received formatted message: '{formatted_message}'") # Log after call
                         return formatted_message
                else:
                    # Handler returned something unexpected
                    logging.error(f"Handler for {intent} returned unexpected result type: {handler_result}")
                    # Pass action as a keyword argument
                    return self.get_formatted_response("error_internal", action=f"handle_{intent.name.lower()}")

            except Exception as e:
                logging.exception(f"Error executing handler for intent: {intent}")
                # Use generic error key
                # TODO: Add error_internal key to responses.yaml
                return self.get_formatted_response("invalid_command", **{})
        else:
            # No handler mapped for this intent (should be caught by UNKNOWN mapping)
            logging.warning(f"No handler explicitly mapped for intent: {intent}")
            return self.get_formatted_response("invalid_command", **{})

    def _setup_intent_map(self):
        """Initializes the mapping from CommandIntent to imported handler functions."""
        self.intent_map = {
            CommandIntent.UNKNOWN: handle_unknown,
            CommandIntent.MOVE: handle_move,
            CommandIntent.LOOK: handle_look,
            CommandIntent.TAKE: handle_take,
            CommandIntent.DROP: handle_drop,
            CommandIntent.INVENTORY: handle_inventory,
            CommandIntent.QUIT: handle_quit,
            CommandIntent.EQUIP: handle_equip,
            CommandIntent.PUT: handle_put,
            CommandIntent.TAKE_FROM: handle_take_from,
            # Add other intents here and map them to appropriate handlers 
            # (e.g., handle_use, handle_interact, etc.) when implemented.
        }
        logging.info(f"Intent map initialized with {len(self.intent_map)} handlers pointing to imported functions.")

    def get_formatted_response(self, key: str, **kwargs) -> str:
        """Gets a random response for the key, formats it, and returns it."""
        response_list = self.responses_data.get(key, [])
        if not response_list:
            logging.warning(f"No responses found for key: '{key}'")
            return f"(Action '{key}' occurred, but response text is missing.)"
            
        import random
        chosen_template = random.choice(response_list)
        logging.debug(f"[get_formatted_response] Key: '{key}', Chosen Template: '{chosen_template}'") # Log chosen template
        
        try:
            formatted_message = chosen_template.format(**kwargs)
            logging.debug(f"[get_formatted_response] Formatted Message: '{formatted_message}'") # Log result
            return formatted_message
        except KeyError as e:
            logging.error(f"Missing placeholder '{e}' in response template for key '{key}': '{chosen_template}'")
            # Return the template with a warning if formatting fails
            return f"(Response formatting error for '{key}': {chosen_template})"
        except Exception as e:
            logging.error(f"Unexpected error formatting response for key '{key}': {e}", exc_info=True)
            return f"(Response formatting error for '{key}')"

    def display_output(self, message: str):
        """Prints output to the console (can be overridden for GUI)."""
        print(f"\n{message}\n") # Add blank lines for readability

# --- Old handler methods removed from GameLoop class --- 

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    # Setup basic logging for testing this module directly
    # Change level to DEBUG to see detailed parser logs
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    
    try:
        game_loop = GameLoop()
        game_loop.run() 
    except Exception as e:
         logging.critical(f"Game loop failed to initialize or run: {e}", exc_info=True)
         print(f"\nCRITICAL ERROR: {e}") 