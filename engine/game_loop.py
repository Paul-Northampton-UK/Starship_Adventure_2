# engine/game_loop.py

import logging
from typing import Dict, Any, Optional
from .game_state import GameState, PowerState
from .nlp_command_parser import NLPCommandParser
from .command_defs import CommandIntent, ParsedIntent
from .yaml_loader import YAMLLoader
from pathlib import Path

# Define default paths (can be overridden)
DEFAULT_CONFIG_YAML = "game_config.yaml"
DEFAULT_ROOMS_YAML = "data/rooms.yaml"
DEFAULT_OBJECTS_YAML = "data/objects.yaml"

class GameLoop:
    """Manages the main game loop and orchestrates game flow."""

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

        # --- Determine starting conditions from config (with defaults) ---
        start_room_id = self.config_data.get("start_room_id", "bridge") 
        start_power_str = self.config_data.get("start_power_state", "offline")
        try:
            start_power_state = PowerState(start_power_str)
        except ValueError:
            logging.warning(f"Invalid start_power_state '{start_power_str}' in config. Defaulting to offline.")
            start_power_state = PowerState.OFFLINE
        # -----------------------------------------------------------------
        
        # Validate start room exists
        if start_room_id not in self.rooms_data:
             logging.warning(f"Configured start_room_id '{start_room_id}' not found in loaded rooms. Defaulting to first available room or 'bridge'.")
             start_room_id = next(iter(self.rooms_data), "bridge")

        # Initialize game state, passing processed room data and initial power state
        self.game_state = GameState(current_room_id=start_room_id, 
                                    rooms_data=self.rooms_data,
                                    power_state=start_power_state) # Use loaded power state
        logging.info(f"GameState initialized. Starting room: {self.game_state.current_room_id}, Power State: {self.game_state.power_state.value}")

        # Initialize command parser, passing the game state
        self.command_parser = NLPCommandParser(self.game_state)
        logging.info("NLPCommandParser initialized.")
        
        logging.info("Game Loop initialized.")

    def load_config(self, config_yaml_path: str):
        """Loads the main game configuration file."""
        logging.info(f"Loading configuration from {config_yaml_path}")
        # Use YAMLLoader but load from root directory, not data subdir
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
        loader = YAMLLoader()
        self.rooms_data = {} # Ensure it's a dict
        self.objects_data = {} # Ensure it's a dict

        try:
            rooms_filename = Path(rooms_yaml_path).name
            loaded_room_structure = loader.load_file(rooms_filename)
            # --- Process the loaded room structure --- 
            if isinstance(loaded_room_structure, dict) and 'rooms' in loaded_room_structure and isinstance(loaded_room_structure['rooms'], list):
                raw_room_list = loaded_room_structure['rooms']
                # Transform list into dict keyed by room_id
                self.rooms_data = {room_data['room_id']: room_data for room_data in raw_room_list if 'room_id' in room_data}
                logging.info(f"Processed {len(self.rooms_data)} rooms into dictionary.")
            else:
                logging.error(f"Unexpected structure in {rooms_filename}. Expected {'rooms': [list_of_rooms]}.")
        except FileNotFoundError:
            logging.error(f"Rooms file not found: {rooms_yaml_path}. Cannot load rooms.")
        except Exception as e:
            logging.error(f"Error loading/processing rooms from {rooms_yaml_path}: {e}", exc_info=True)
            
        try:
            objects_filename = Path(objects_yaml_path).name
            loaded_object_structure = loader.load_file(objects_filename)
            # --- Process the loaded object structure (assuming similar structure) --- 
            if isinstance(loaded_object_structure, dict) and 'objects' in loaded_object_structure and isinstance(loaded_object_structure['objects'], list):
                raw_object_list = loaded_object_structure['objects']
                # Transform list into dict keyed by id
                self.objects_data = {obj_data['id']: obj_data for obj_data in raw_object_list if 'id' in obj_data}
                logging.info(f"Processed {len(self.objects_data)} objects into dictionary.")
            else:
                # Attempt to load if it's just a dict keyed by ID directly
                if isinstance(loaded_object_structure, dict):
                    self.objects_data = loaded_object_structure
                    logging.info(f"Loaded {len(self.objects_data)} objects directly from dictionary.")
                else:
                    logging.warning(f"Unexpected structure in {objects_filename}. Expected {'objects': [list_of_objects]} or dict keyed by ID.")
        except FileNotFoundError:
            logging.warning(f"Objects file not found: {objects_yaml_path}. Proceeding without objects.")
        except Exception as e:
            logging.error(f"Error loading/processing objects from {objects_yaml_path}: {e}", exc_info=True)
            
        # TODO: Add schema validation if needed
        # TODO: Pass object data to GameState or make available some other way

    def run(self):
        """Starts and runs the main game loop."""
        self.is_running = True
        logging.info("Starting game loop...")

        print("Welcome to Starship Adventure 2!")

        # --- Display initial location description --- 
        initial_description = self._get_location_description(self.game_state.current_room_id, self.game_state.current_area_id)
        print(initial_description)
        # ---------------------------------------------

        while self.is_running:
            # TODO: Implement core loop:
            # 1. Get player input
            # 2. Parse command (Current Step)
            # 3. Process command (update game state)
            # 4. Display output/result
            # 5. Check for quit condition
            
            # 1. Get player input
            command_input = input("> ").strip()
            if not command_input:
                continue # Ask for input again if empty

            # 5. Check for quit condition (early check)
            if command_input.lower() == "quit":
                 self.is_running = False
                 continue # Skip parsing/processing if quitting

            # 2. Parse command
            try:
                parsed_intent = self.command_parser.parse_command(command_input)
                # For now, just print the parsed intent to see the result
                print(f"Parsed: {parsed_intent}") 
            except Exception as e:
                logging.error(f"Error parsing command '{command_input}': {e}", exc_info=True)
                print("An error occurred while parsing your command.")

            # TODO: 3. Process command using parsed_intent
            # TODO: 4. Display output/result from processing
            # Call process_command and display the result
            message = self.process_command(parsed_intent)
            print(message)
                
        logging.info("Game loop stopped.")
        print("Goodbye!")

    def process_command(self, parsed_intent: ParsedIntent) -> str:
        """Processes the parsed command intent and updates the game state.

        Args:
            parsed_intent: The ParsedIntent object from the command parser.

        Returns:
            A message string to display to the player.
        """
        intent = parsed_intent.intent
        logging.debug(f"Processing intent: {intent} with data: {parsed_intent}")

        # --- Handle different command intents ---
        if intent == CommandIntent.MOVE:
            return self._handle_move(parsed_intent)
        elif intent == CommandIntent.LOOK:
            return self._handle_look(parsed_intent)
        elif intent == CommandIntent.TAKE:
            # TODO: Implement _handle_take(parsed_intent)
            return f"TAKE command recognized. Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.DROP:
            # TODO: Implement _handle_drop(parsed_intent)
            return f"DROP command recognized. Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.INVENTORY:
            # TODO: Implement _handle_inventory()
            return "INVENTORY command recognized. (Not implemented)"
        elif intent == CommandIntent.HELP:
            # TODO: Implement _handle_help()
            return "HELP command recognized. (Not implemented)"
        elif intent == CommandIntent.USE:
            # TODO: Implement _handle_use(parsed_intent)
             return f"USE command recognized. Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.COMBAT:
            # TODO: Implement _handle_combat(parsed_intent)
             return f"COMBAT command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.COMMUNICATE:
            # TODO: Implement _handle_communicate(parsed_intent)
             return f"COMMUNICATE command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        # --- Add branches for remaining intents ---
        elif intent == CommandIntent.SEARCH:
            # TODO: Implement _handle_search(parsed_intent)
            return f"SEARCH command recognized. Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.MANIPULATE:
            # TODO: Implement _handle_manipulate(parsed_intent)
            return f"MANIPULATE command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.CLIMB:
            # TODO: Implement _handle_climb(parsed_intent)
            return f"CLIMB command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.SOCIAL:
            # TODO: Implement _handle_social(parsed_intent)
            return f"SOCIAL command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.ENVIRONMENT:
            # TODO: Implement _handle_environment(parsed_intent)
            return f"ENVIRONMENT command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.GATHER_INFO:
            # TODO: Implement _handle_gather_info(parsed_intent)
            return f"GATHER_INFO command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.EQUIP:
            # TODO: Implement _handle_equip(parsed_intent)
            return f"EQUIP command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.TIME:
            # TODO: Implement _handle_time(parsed_intent)
            return f"TIME command recognized. Action: {parsed_intent.action}. (Not implemented)"
        elif intent == CommandIntent.COMPLEX:
            # TODO: Implement _handle_complex(parsed_intent)
            return f"COMPLEX command recognized. Action: {parsed_intent.action}, Target: {parsed_intent.target}. (Not implemented)"
        elif intent == CommandIntent.SAVE:
            # TODO: Implement _handle_save()
            return "SAVE command recognized. (Not implemented)"
        elif intent == CommandIntent.LOAD:
            # TODO: Implement _handle_load()
            return "LOAD command recognized. (Not implemented)"
        # --- End of added branches ---
        elif intent == CommandIntent.UNKNOWN:
            return "I don't understand that command."
        else:
            # Handle any other recognized intents that don't have logic yet
            return f"{intent.name} command recognized, but not implemented yet."

    # --- Placeholder helper methods (to be implemented later) ---
    # def _handle_move(self, parsed_intent: ParsedIntent) -> str:
    #     pass
    # def _handle_look(self, parsed_intent: ParsedIntent) -> str:
    #     pass
    # def _handle_take(self, parsed_intent: ParsedIntent) -> str:
    #     pass
    # ... etc ...

    # --- Command Handler Methods ---

    def _handle_move(self, parsed_intent: ParsedIntent) -> str:
        """Handles the MOVE command intent.
        
        Checks for movement to a specific Area or via a Directional Exit.
        Updates game state and returns the description of the new location.
        """
        target = parsed_intent.target
        direction = parsed_intent.direction
        current_room_id = self.game_state.current_room_id
        current_room_data = self.game_state.rooms_data.get(current_room_id)

        if not current_room_data:
            logging.error(f"Move failed: Current room '{current_room_id}' not found in rooms_data!")
            return "An internal error occurred: current room data missing."

        # Normalize player input direction
        normalized_direction_map = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "u": "up", "d": "down", 
            "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
            # Added hyphenated forms
            "north-east": "northeast", "north-west": "northwest", 
            "south-east": "southeast", "south-west": "southwest"
        }
        # Use lowercase for consistent matching with YAML
        normalized_player_direction = normalized_direction_map.get(direction, direction).lower()

        # --- Check for Area Movement FIRST ---
        if target:
            areas_list = current_room_data.get("areas", [])
            if isinstance(areas_list, list):
                target_lower = target.lower()
                for area_data in areas_list:
                    area_id = area_data.get("area_id")
                    area_aliases = area_data.get("command_aliases", [])
                    
                    if area_id and (target_lower == area_id.lower() or target_lower in area_aliases):
                        # Check if already in this area
                        if self.game_state.current_area_id == area_id:
                             return f"You are already at the {area_data.get('name', area_id)}."
                             
                        # Successfully moving to a new area
                        self.game_state.move_to_area(area_id)
                        # Return description based on visit status
                        return self._get_location_description(current_room_id, area_id)
            else:
                 logging.warning(f"Areas data for room '{current_room_id}' is not a list! Skipping area check.")

        # --- If not moving to an area, check for Directional Room Exit ---
        if not direction:
            # Only return this if no area movement was attempted/found
            if not target: 
                 return "Which direction or area do you want to move to? (e.g., north, n, nav station)"
            else:
                # Target was specified but didn't match an area
                return f"You can't move to '{target}' like that. Try a direction (e.g. north) or a known area name."

        # Exits data is a LIST of dictionaries, not a dictionary itself
        exits_list = current_room_data.get("exits", [])
        if not isinstance(exits_list, list):
             logging.error(f"Exits data for room '{current_room_id}' is not a list!")
             return "An internal error occurred: room exits data malformed."

        # Find the matching exit in the list
        found_exit = None
        for exit_data in exits_list:
            # Ensure direction key exists and is a string before comparing
            exit_direction = exit_data.get("direction")
            # Compare lowercase versions after removing spaces for flexibility
            if isinstance(exit_direction, str):
                yaml_direction_normalized = exit_direction.replace(" ", "").lower()
                player_direction_normalized = normalized_player_direction # Already lowercase via map
                if yaml_direction_normalized == player_direction_normalized:
                    found_exit = exit_data
                    break # Found the matching exit

        if found_exit:
            next_room_id = found_exit.get("destination")
            if not next_room_id:
                 logging.error(f"Exit '{normalized_player_direction}' in room '{current_room_id}' has no destination.")
                 return f"You try to go {normalized_player_direction}, but the destination seems undefined."

            # Check if the destination room exists
            if next_room_id in self.game_state.rooms_data:
                self.game_state.move_to_room(next_room_id)
                # Return description based on visit status
                return self._get_location_description(next_room_id, None) # Area is None when entering a room
            else:
                logging.warning(f"Exit '{normalized_player_direction}' leads to non-existent room '{next_room_id}' from '{current_room_id}'")
                return f"You try to go {normalized_player_direction}, but the way seems blocked or leads nowhere defined."
        else:
            # Use the player's input direction in the failure message
            return f"You can't go {direction} from here."

    def _get_location_description(self, room_id: str, area_id: Optional[str]) -> str:
        """Gets the appropriate description (first visit or short) for a room or area."""
        location_data: Optional[Dict[str, Any]] = None
        is_first_visit = True
        description_key = "first_visit_description"
        location_name_for_fallback = "location"

        if area_id:
            # Get Area Data
            room_data = self.game_state.rooms_data.get(room_id)
            if room_data and isinstance(room_data.get("areas"), list):
                for ad in room_data["areas"]:
                    if ad.get("area_id") == area_id:
                        location_data = ad
                        is_first_visit = not self.game_state.has_visited_area(area_id)
                        self.game_state.visit_area(area_id) # Mark as visited
                        location_name_for_fallback = location_data.get("name", "area")
                        break
            if not location_data:
                 logging.error(f"_get_location_description: Cannot find area data for {area_id} in {room_id}")
                 return "You arrive, but the details of this area are unclear."
        else:
            # Get Room Data
            location_data = self.game_state.rooms_data.get(room_id)
            if location_data:
                is_first_visit = not self.game_state.has_visited_room(room_id)
                self.game_state.visit_room(room_id) # Mark as visited
                location_name_for_fallback = location_data.get("name", "room")
            else:
                logging.error(f"_get_location_description: Cannot find room data for {room_id}")
                return "You arrive, but the details of this room are unclear."
        
        # Determine which description to use
        if not is_first_visit:
            description_key = "short_description"
            logging.debug(f"Location {area_id or room_id} already visited. Using short_description.")
        else:
             logging.debug(f"First visit to location {area_id or room_id}. Using first_visit_description.")

        # Get description based on power state
        power_state = self.game_state.power_state.value
        descriptions = location_data.get(description_key, {})
        if not isinstance(descriptions, dict):
            logging.error(f"{description_key} data for {area_id or room_id} is not a dictionary!")
            # Fallback to the other description type if possible
            fallback_key = "short_description" if description_key == "first_visit_description" else "first_visit_description"
            descriptions = location_data.get(fallback_key, {})
            if not isinstance(descriptions, dict):
                 return f"The description for the {location_name_for_fallback} seems to be missing or malformed."
        
        description = descriptions.get(power_state, descriptions.get("offline", f"It's too dark to see the {location_name_for_fallback} clearly."))

        # TODO: Append exit/object info?
        return description

    def _handle_look(self, parsed_intent: ParsedIntent) -> str:
        """Handles the LOOK command intent.

        Provides a detailed description of the current room or area, 
        or looks at a specific target (placeholder).
        """
        target = parsed_intent.target
        current_room_id = self.game_state.current_room_id
        current_area_id = self.game_state.current_area_id # Check area first
        current_room_data = self.game_state.rooms_data.get(current_room_id)

        if not current_room_data:
            logging.error(f"Look failed: Current room '{current_room_id}' not found in rooms_data!")
            return "An internal error occurred: you seem to be nowhere defined."

        # Simple check if player is looking at the location vs. a specific object
        if not target or target in ["room", "around", "area"]:
            # --- Always show detailed description on explicit LOOK --- 
            # Use the helper, but force it to use 'first_visit_description'
            location_data: Optional[Dict[str, Any]] = None
            location_name_for_fallback = "location"
            description_key = "first_visit_description" # Always use detailed key for LOOK

            if current_area_id:
                # Get Area Data
                areas_list = current_room_data.get("areas", [])
                if isinstance(areas_list, list):
                     for ad in areas_list:
                         if ad.get("area_id") == current_area_id:
                             location_data = ad
                             location_name_for_fallback = location_data.get("name", "area")
                             break
                if not location_data:
                    return "You are in an area, but its details are unclear."
            else:
                # Get Room Data
                location_data = current_room_data
                location_name_for_fallback = location_data.get("name", "room")
            
            # Get description based on power state
            power_state = self.game_state.power_state.value
            descriptions = location_data.get(description_key, {})
            if not isinstance(descriptions, dict):
                 logging.error(f"{description_key} data for {current_area_id or current_room_id} is not a dictionary!")
                 return f"The detailed description for the {location_name_for_fallback} seems to be missing or malformed."
            
            description = descriptions.get(power_state, descriptions.get("offline", f"It's too dark to see the {location_name_for_fallback} clearly."))
            # TODO: Add information about visible objects and exits to the description
            return description
        else:
            # Look at a specific target (placeholder)
            # TODO: Implement logic to find the target (object/NPC/feature) in the room 
            #       and return its description.
            return f"You look closely at the {target}. (Description not implemented)"

    # def _handle_take(self, parsed_intent: ParsedIntent) -> str:
    #     pass
    # ... etc ...

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    # Setup basic logging for testing this module directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    game_loop = GameLoop()
    # In a real scenario, we'd load game data and initialize game_state/parser properly here
    # game_loop.setup_game()
    game_loop.run() 