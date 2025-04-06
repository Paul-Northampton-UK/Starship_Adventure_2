# engine/game_loop.py

import logging
from typing import Dict, Any, Optional, Callable
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
                                    objects_data=self.objects_data,
                                    power_state=start_power_state) # Use loaded power state
        logging.info(f"GameState initialized. Starting room: {self.game_state.current_room_id}, Power State: {self.game_state.power_state.value}")

        # Initialize command parser, passing the game state
        self.command_parser = NLPCommandParser(self.game_state)
        logging.info("NLPCommandParser initialized.")
        
        # --- Initialize and setup the intent map --- 
        self.intent_map: Dict[CommandIntent, Callable[[ParsedIntent], str]] = {} # Type hint
        self._setup_intent_map()
        # -------------------------------------------
        
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
        """Processes the parsed command intent by dispatching to the appropriate handler via intent_map."""
        intent = parsed_intent.intent
        logging.debug(f"Processing intent: {intent} with data: {parsed_intent}")

        handler = self.intent_map.get(intent)

        if handler:
            try:
                # Call the handler associated with the intent
                # Pass the whole ParsedIntent object
                message = handler(parsed_intent)
                return message # Return the message from the handler
            except Exception as e:
                logging.exception(f"Error executing handler for intent: {intent}")
                return "An internal error occurred while processing your command."
        else:
            # Default handling if no specific handler is mapped for a recognized intent
            # or handle CommandIntent.UNKNOWN explicitly in the map
            logging.warning(f"No handler found for intent: {intent}")
            # Check if it was UNKNOWN or just unhandled
            if intent == CommandIntent.UNKNOWN:
                return "I don't understand that command."
            else:
                 return f"I understand you want to '{intent.name.lower()}', but that action isn't fully implemented yet."

    # --- NEW method to setup the intent map --- 
    def _setup_intent_map(self):
        """Initializes the mapping from CommandIntent to handler methods."""
        self.intent_map = {
            CommandIntent.MOVE: self._handle_move,
            CommandIntent.LOOK: self._handle_look,
            # --- Add placeholders for handlers we need to implement/fix ---
            CommandIntent.TAKE: self._handle_take, # Needs implementation
            CommandIntent.DROP: self._handle_drop, # Needs implementation
            CommandIntent.INVENTORY: self._handle_inventory, # Needs implementation
            CommandIntent.EQUIP: self._handle_equip, # Needs implementation
            CommandIntent.QUIT: self._handle_quit, # Needs implementation/verification
            CommandIntent.UNKNOWN: self._handle_unknown, # Add explicit unknown handler
            # Add other intents here as needed, mapping to placeholder handlers initially
            # e.g., CommandIntent.USE: self._handle_use_placeholder, 
        }
        logging.info(f"Intent map initialized with {len(self.intent_map)} handlers.")

    # --- Placeholder Handlers (To be replaced/implemented) ---
    # Need implementations for TAKE, DROP, INVENTORY, EQUIP, QUIT, UNKNOWN
    # Ensure method signatures accept ParsedIntent

    def _handle_take(self, parsed_intent: ParsedIntent) -> str:
        """Handles the TAKE command intent, checking hand slot first."""
        target_object_name = parsed_intent.target
        logging.debug(f"[_handle_take] Handling TAKE for target name: '{target_object_name}'")

        if not target_object_name:
            return "What do you want to take?"

        # Check if hands are full FIRST
        if self.game_state.hand_slot is not None:
            held_object_name = self.game_state._get_object_name(self.game_state.hand_slot)
            logging.debug(f"[_handle_take] Hand slot occupied by '{self.game_state.hand_slot}'. Cannot take '{target_object_name}'")
            # Try to find the target name for a better message even if hands are full
            target_object_id_if_exists = self.game_state._find_object_id_by_name_in_location(target_object_name)
            target_object_name_display = self.game_state._get_object_name(target_object_id_if_exists) if target_object_id_if_exists else target_object_name
            return f"Your hands are full (holding the {held_object_name}). You need to drop it or put it away before taking the {target_object_name_display}."

        # If hands are empty, find the object ID in the location
        logging.debug(f"[_handle_take] Calling _find_object_id_by_name_in_location for '{target_object_name}'...")
        found_object_id = self.game_state._find_object_id_by_name_in_location(target_object_name)
        logging.debug(f"[_handle_take] _find_object_id_by_name_in_location returned: '{found_object_id}'")

        if not found_object_id:
            logging.debug(f"[_handle_take] No object ID found for name '{target_object_name}'. Returning 'not seen' message.")
            return f"You don't see a {target_object_name} here."
        
        # Call GameState.take_object
        logging.debug(f"[_handle_take] Calling take_object with ID: '{found_object_id}'")
        result = self.game_state.take_object(found_object_id)
        logging.debug(f"[_handle_take] take_object returned: {result}")
        
        # The take_object method now returns a message string directly
        return result 
         
    def _handle_drop(self, parsed_intent: ParsedIntent) -> str:
        """Handles the DROP command intent, checking hand slot."""
        target_object_name = parsed_intent.target
        logging.debug(f"[_handle_drop] Handling DROP for target name: '{target_object_name}'")

        if not target_object_name:
            return "What do you want to drop?"

        held_object_id = self.game_state.hand_slot
        if held_object_id is None:
            return "You aren't holding anything to drop."

        # Use _item_matches_name helper to check if the held item matches the target name
        if not self._item_matches_name(held_object_id, target_object_name):
             held_object_name = self.game_state._get_object_name(held_object_id)
             return f"You aren't holding a {target_object_name}. You're holding the {held_object_name}."

        # If it matches, proceed to drop the item in hand
        object_id_to_drop = held_object_id 
        logging.debug(f"[_handle_drop] Calling drop_object with ID: '{object_id_to_drop}'")
        result = self.game_state.drop_object(object_id_to_drop)
        logging.debug(f"[_handle_drop] drop_object returned: {result}")
        
        # drop_object returns a dictionary {"success": bool, "message": str}
        return result.get("message", "An unknown error occurred while trying to drop the object.")
         
    def _handle_inventory(self, parsed_intent: ParsedIntent) -> str:
        """Handles the INVENTORY command intent by displaying status."""
        inventory = self.game_state.inventory or [] 
        hand_slot = self.game_state.hand_slot
        worn_items = self.game_state.worn_items or []

        output = "You check your belongings.\n"

        # Display item in hand
        if hand_slot:
            hand_item_name = self.game_state._get_object_name(hand_slot)
            output += f"  Holding: {hand_item_name}\n"
        else:
            output += "  Holding: Nothing\n"

        # Display worn items
        output += "  Wearing:\n"
        if worn_items:
            worn_item_details = []
            for item_id in sorted(worn_items): 
                item_name = self.game_state._get_object_name(item_id)
                item_data = self.game_state.get_object_by_id(item_id)
                if item_data:
                    area = item_data.get('properties',{}).get('wear_area', 'Unknown Area')
                    layer = item_data.get('properties',{}).get('wear_layer', '?')
                    worn_item_details.append(f"    - {item_name} (Area: {area}, Layer: {layer})")
                else:
                    worn_item_details.append(f"    - {item_id} (Data missing!)") 
            if worn_item_details:
                output += "\n".join(worn_item_details) + "\n"
            else:
                output += "    Nothing\n"
        else:
            output += "    Nothing\n"

        # Display inventory items
        output += "  Carrying in Inventory:\n"
        if inventory:
            inventory_names = []
            for item_id in sorted(inventory):
                 inventory_names.append(f"    - {self.game_state._get_object_name(item_id)}")
            if inventory_names:
                output += "\n".join(inventory_names) + "\n"
            else:
                output += "    Nothing\n"
        else:
            output += "    Nothing\n"

        # Handler should display output directly and return empty string or confirmation?
        # Let's display directly for now.
        self.display_output(output.strip())
        return "" # Return empty string as message is already displayed

    def _handle_equip(self, parsed_intent: ParsedIntent) -> str:
        """Handles EQUIP/UNEQUIP intents by calling wear_item or remove_item."""
        target_item_name = parsed_intent.target
        action_verb = parsed_intent.action or "" # Get action from intent
        # Define verbs that mean 'wear' vs 'remove'
        wear_verbs = {"wear", "equip", "don", "puton", "put"} # Added "put"
        remove_verbs = {"remove", "unequip", "doff", "takeoff", "take"} # Added "take"

        logging.debug(f"[_handle_equip] Handling EQUIP. Target: '{target_item_name}', Action: '{action_verb}'")

        if not target_item_name:
            return "What do you want to wear or remove?"

        # Determine if the action is WEAR or REMOVE based on the verb
        is_wearing = action_verb.lower() in wear_verbs
        is_removing = action_verb.lower() in remove_verbs

        if is_wearing:
            object_id_to_wear = None
            # Check hand slot FIRST
            held_item_id = self.game_state.hand_slot
            if held_item_id and self._item_matches_name(held_item_id, target_item_name):
                object_id_to_wear = held_item_id
                logging.debug(f"[_handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in hand slot.")
            
            # If not in hand, check inventory
            if not object_id_to_wear:
                inventory_item_id = self.game_state._find_object_id_by_name_in_inventory(target_item_name)
                if inventory_item_id:
                    object_id_to_wear = inventory_item_id
                    logging.debug(f"[_handle_equip] Found target '{target_item_name}' (ID: {object_id_to_wear}) in inventory.")

            # Now, attempt to wear if we found an ID
            if object_id_to_wear:
                return self.game_state.wear_item(object_id_to_wear)
            else:
                # If not found in hands or inventory, check if already worn
                if self.game_state._find_object_id_by_name_worn(target_item_name):
                     return f"You are already wearing the {target_item_name}."
                else:
                     # Only reach here if not in hands, inventory, or worn
                     return f"You don't have a '{target_item_name}' to wear (checked hands and inventory)."

        elif is_removing:
            # Find the item in worn items first
            object_id_to_remove = self.game_state._find_object_id_by_name_worn(target_item_name)
            if not object_id_to_remove:
                 if self.game_state._find_object_id_by_name_in_inventory(target_item_name):
                     return f"You have the {target_item_name}, but you aren't wearing it."
                 else:
                    return f"You aren't wearing a '{target_item_name}'."
            # Attempt to remove
            return self.game_state.remove_item(object_id_to_remove)

        else:
            # If the NLP parser returned EQUIP intent but the action wasn't recognized
            logging.warning(f"_handle_equip received EQUIP intent but unclear action verb: '{action_verb}'")
            return f"Do you want to wear or remove the {target_item_name}?" 
         
    def _handle_quit(self, parsed_intent: ParsedIntent) -> str:
         self.is_running = False # Set flag to stop the loop
         # Don't print directly here, let the calling code handle final message
         return "Quitting game. Goodbye!"
         
    def _handle_unknown(self, parsed_intent: ParsedIntent) -> str:
         return "I don't understand that command."

    # --- Existing Implemented Handlers (Verify signature) ---
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

        # --- Direction Normalization --- 
        normalized_direction_map = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "u": "up", "d": "down", 
            "ne": "northeast", "nw": "northwest", "se": "southeast", "sw": "southwest",
            "north-east": "northeast", "north-west": "northwest", 
            "south-east": "southeast", "south-west": "southwest"
        }
        # Normalize player input direction ONLY if a direction was parsed
        player_direction_normalized = None # Initialize
        if direction: # Check if direction is not None
            processed_direction = normalized_direction_map.get(direction, direction).lower()
            # Also remove spaces from player input to match YAML processing
            player_direction_normalized = processed_direction.replace(" ", "") 
        else:
             logging.debug("[_handle_move] No direction provided by parser.")
        # --- End Direction Normalization --- 

        # --- Check for Area Movement FIRST ---
        if target:
            areas_list = current_room_data.get("areas", [])
            if isinstance(areas_list, list):
                target_lower = target.lower()
                for area_data in areas_list:
                    area_id = area_data.get("area_id")
                    area_aliases = area_data.get("command_aliases", [])
                    
                    # Match area ID or any of its aliases
                    if area_id and (target_lower == area_id.lower() or target_lower in [str(a).lower() for a in area_aliases]):
                        # Check if already in this area
                        if self.game_state.current_area_id == area_id:
                             return f"You are already at the {area_data.get('name', area_id)}."
                             
                        # Successfully moving to a new area
                        logging.info(f"Moving player to area: {area_id} in room {current_room_id}")
                        self.game_state.move_to_area(area_id)
                        # Return description based on visit status
                        return self._get_location_description(current_room_id, area_id)
            else:
                 logging.warning(f"Areas data for room '{current_room_id}' is not a list! Skipping area check.")

        # --- If not moving to an area, check for Directional Room Exit ---
        # Only check exits if a direction *was* actually processed
        if player_direction_normalized:
            exits_list = current_room_data.get("exits", [])
            if not isinstance(exits_list, list):
                 logging.error(f"Exits data for room '{current_room_id}' is not a list!")
                 return "An internal error occurred: room exits data malformed."

            # Find the matching exit in the list
            found_exit = None
            for exit_data in exits_list:
                # Ensure direction key exists and is a string before comparing
                exit_direction_yaml = exit_data.get("direction")
                # Compare lowercase versions after removing spaces for flexibility
                if isinstance(exit_direction_yaml, str):
                    yaml_direction_normalized = exit_direction_yaml.replace(" ", "").lower()
                    # player_direction_normalized is already processed
                    if yaml_direction_normalized == player_direction_normalized:
                        found_exit = exit_data
                        break # Found the matching exit

            if found_exit:
                next_room_id = found_exit.get("destination")
                if not next_room_id:
                     logging.error(f"Exit '{player_direction_normalized}' in room '{current_room_id}' has no destination.")
                     # Use original direction input for message if available
                     return f"You try to go {direction or 'that way'}, but the destination seems undefined."

                # Check if the destination room exists
                if next_room_id in self.game_state.rooms_data:
                    logging.info(f"Moving player via exit '{player_direction_normalized}' from {current_room_id} to {next_room_id}")
                    self.game_state.move_to_room(next_room_id)
                    # Return description based on visit status
                    return self._get_location_description(next_room_id, None) # Area is None when entering a room
                else:
                    logging.warning(f"Exit '{player_direction_normalized}' leads to non-existent room '{next_room_id}' from '{current_room_id}'")
                    return f"You try to go {direction or 'that way'}, but the way seems blocked or leads nowhere defined."
            else:
                # Direction was given, but no matching exit found
                return f"You can't go {direction} from here."
                
        # --- Fallback Messages if No Action Was Taken --- 
        elif not target: # No direction AND no target was given (and area move didn't happen)
             return "Which direction or area do you want to move to? (e.g., north, n, nav station)"
             
        elif target: # Target was given but didn't match an area (and no direction given)
             # The area search loop above didn't find a match and didn't return.
             return f"You can't move to '{target}' like that. Try a direction (e.g. north) or a known area name."

        # Default fallback if something truly unexpected occurs (should be rare)
        logging.warning("[_handle_move] Reached unexpected fallback return.")
        return "You can't move that way."

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
                        # Pass room_id when marking area visited
                        self.game_state.visit_area(area_id, room_id) 
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

    # --- ADD MISSING HELPER for item matching ---
    def _item_matches_name(self, item_id: str, name_to_match: str) -> bool:
         """Checks if the item ID matches the name/synonym/ID provided."""
         if not item_id or not name_to_match:
             return False

         name_lower = name_to_match.lower().strip()

         # Direct ID match (case-insensitive)
         if item_id.lower() == name_lower:
             return True

         # Name/Synonym match - use game_state's object data
         object_data = self.game_state.get_object_by_id(item_id) # Use get_object_by_id
         if object_data:
             if object_data.get("name", "").lower() == name_lower:
                 return True
             synonyms = object_data.get("synonyms", [])
             if isinstance(synonyms, list):
                 if name_lower in [str(syn).lower().strip() for syn in synonyms if isinstance(syn, (str, int, float))]:
                     return True
         return False

    def display_output(self, message: str):
        """Prints output to the console (can be overridden for GUI)."""
        print(f"\n{message}\n") # Add blank lines for readability

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    # Setup basic logging for testing this module directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    game_loop = GameLoop()
    # In a real scenario, we'd load game data and initialize game_state/parser properly here
    # game_loop.setup_game()
    game_loop.run() 