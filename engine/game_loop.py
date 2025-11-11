# engine/game_loop.py

import importlib
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

from loguru import logger  # Changed from logging

from .command_defs import CommandIntent, ParsedIntent
from .command_handlers.basic_commands import (
    handle_help,
    handle_inventory,
    handle_load,
    handle_look,
    handle_save,
    handle_quit,
    handle_unknown,
)
from .command_handlers.combat import (
    handle_aim,
    handle_attack,
    handle_block,
    handle_check,
    handle_dodge,
    handle_flee,
    handle_reload,
    handle_shoot,
    handle_unload,
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
from .command_handlers.stealth import (
    handle_disarm_trap,
    handle_hide,
    handle_pickpocket,
    handle_sneak,
)
from .command_handlers.crafting import (
    handle_craft,
    handle_combine,
    handle_gather,
)
from .command_handlers.magic import (
    handle_bless,
    handle_cast,
    handle_channel,
    handle_curse,
    handle_dismiss,
    handle_enchant,
    handle_identify,
    handle_ritual,
    handle_summon,
    handle_transmute,
)
from .command_handlers.throw_catch import handle_catch, handle_throw
from .command_handlers.wait import handle_wait
from .command_handlers.interaction import handle_use, handle_use_on
from .command_handlers.transition import handle_enter, handle_exit
from .command_handlers.swim import handle_swim
from .command_handlers.social import handle_ask, handle_give, handle_show, handle_talk
from .active_pack import get_active_pack, get_content_root_from_config
from .game_state import GameState, PowerState
from .nlp_v2 import parser as parser_v2_module
from .nlp_v2.parser import NLPCommandParserV2
from .nlp_command_parser import NLPCommandParser as NLPCommandParserV1
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
        self.use_nlp_v2 = self._nlp_v2_enabled()
        parser_mode_label = "NLP parser v2" if self.use_nlp_v2 else "NLP parser v1 (legacy)"
        logger.info(f"Parser selection: {parser_mode_label}")
        if self.use_nlp_v2:
            logger.info("NLP v2 adapter active (MOVE+LOOK+INVENTORY+SOCIAL).")

        # Resolve content root based on active_pack, then load game data (rooms, objects, responses)
        active_pack = get_active_pack()
        self.content_root = get_content_root_from_config()
        banner = f"=== Content root: {self.content_root} (pack={active_pack}) ==="
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

        parser_kind = "legacy"
        if self.use_nlp_v2:
            try:
                importlib.reload(parser_v2_module)
                logger.info("Explicitly reloaded engine.nlp.parser module.")
            except Exception as e:
                logger.error(f"Failed to explicitly reload parser module: {e}", exc_info=True)
            self.command_parser = NLPCommandParserV2()
            parser_kind = "v2"
        else:
            self.command_parser = NLPCommandParserV1(self.game_state)
        logger.info(f"NLP parser initialized ({parser_kind}).")
        
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

    def _nlp_v2_enabled(self) -> bool:
        """Determines whether the experimental NLP v2 parser should be used."""
        env_value = os.environ.get("NLP_V2")
        if env_value is not None:
            return self._coerce_bool(env_value)
        config_value = self.config_data.get("nlp_v2")
        if config_value is not None:
            return self._coerce_bool(config_value)
        return False

    @staticmethod
    def _coerce_bool(value: Any) -> bool:
        """Converts common truthy/falsey representations into a boolean."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on"}:
                return True
            if normalized in {"0", "false", "no", "off"}:
                return False
        return False

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
                if self.use_nlp_v2:
                    v2_result = self.command_parser.parse(command_input)
                    logger.info(f"V2 parser result: {v2_result}")
                    parsed_intent = self._adapt_v2_result(v2_result, command_input)
                else:
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

    def _adapt_v2_result(self, result: dict[str, Any], original_input: str) -> ParsedIntent:
        """Converts the NLP v2 dict response into a ParsedIntent for shared handlers."""
        intent_str = (result or {}).get("intent") or "UNKNOWN"
        data = result.get("data") or {}
        intent = CommandIntent.UNKNOWN
        try:
            intent = CommandIntent[intent_str]
        except KeyError:
            logger.debug(f"Unknown v2 intent '{intent_str}', defaulting to UNKNOWN.")

        direction = data.get("direction")
        target: str | None = None
        target_object_id = None
        secondary_target = None
        secondary_target_id = None
        preposition = None
        action = None

        if intent == CommandIntent.LOOK:
            scope = data.get("scope")
            raw_target = data.get("target")
            if scope == "room" or not raw_target:
                target = None
            else:
                target = (raw_target or "").strip() or None
        elif intent in {CommandIntent.TAKE, CommandIntent.DROP}:
            item_name = (data.get("object") or "").strip()
            target = item_name or None
        elif intent == CommandIntent.PUT:
            item_name = (data.get("object") or "").strip()
            container_name = (data.get("container") or "").strip()
            target = item_name or None
            secondary_target = container_name or None
            preposition = (data.get("preposition") or "").strip() or None
        elif intent in {CommandIntent.READ, CommandIntent.SCAN}:
            read_target = (data.get("target") or "").strip()
            target = read_target or None
        elif intent in {
            CommandIntent.EQUIP,
            CommandIntent.UNEQUIP,
            CommandIntent.WEAR,
            CommandIntent.REMOVE,
            CommandIntent.WIELD,
        }:
            item_name = (data.get("target") or data.get("object") or "").strip()
            target = item_name or None
            action = (data.get("action") or intent_str.lower()).strip() or None
        elif intent == CommandIntent.ATTACK:
            attack_target = (data.get("target") or "").strip()
            target = attack_target or None
        elif intent == CommandIntent.AIM:
            aim_target = (data.get("target") or "").strip()
            target = aim_target or None
        elif intent == CommandIntent.SHOOT:
            shoot_target = (data.get("target") or "").strip()
            weapon_name = (data.get("weapon") or "").strip()
            target = shoot_target or None
            if weapon_name:
                secondary_target = weapon_name
        elif intent == CommandIntent.RELOAD:
            weapon_name = (data.get("weapon") or "").strip()
            ammo_name = (data.get("ammo") or "").strip()
            target = weapon_name or None
            secondary_target = ammo_name or None
        elif intent == CommandIntent.UNLOAD:
            weapon_name = (data.get("weapon") or "").strip()
            target = weapon_name or None
        elif intent == CommandIntent.CHECK:
            check_target = (data.get("target") or "").strip()
            target = check_target or None
        elif intent in {CommandIntent.SNEAK, CommandIntent.HIDE}:
            pass
        elif intent == CommandIntent.PICKPOCKET:
            npc_name = (data.get("npc") or "").strip()
            target = npc_name or None
        elif intent == CommandIntent.DISARM_TRAP:
            trap_name = (data.get("trap") or "").strip()
            target = trap_name or None
        elif intent == CommandIntent.CRAFT:
            item_name = (data.get("item") or "").strip()
            target = item_name or None
        elif intent == CommandIntent.COMBINE:
            item_a = (data.get("item_a") or "").strip()
            item_b = (data.get("item_b") or "").strip()
            target = item_a or None
            secondary_target = item_b or None
        elif intent == CommandIntent.GATHER:
            resource = (data.get("resource") or "").strip()
            target = resource or None
        elif intent == CommandIntent.CAST:
            spell_name = (data.get("spell") or "").strip()
            spell_target = (data.get("target") or "").strip()
            target = spell_name or None
            secondary_target = spell_target or None
        elif intent == CommandIntent.CHANNEL:
            power_name = (data.get("power") or "").strip()
            target = power_name or None
        elif intent == CommandIntent.SUMMON:
            entity_name = (data.get("entity") or "").strip()
            target = entity_name or None
        elif intent == CommandIntent.DISMISS:
            entity_name = (data.get("entity") or "").strip()
            target = entity_name or None
        elif intent == CommandIntent.ENCHANT:
            item_name = (data.get("item") or "").strip()
            effect_name = (data.get("effect") or "").strip()
            target = item_name or None
            secondary_target = effect_name or None
        elif intent == CommandIntent.IDENTIFY:
            identify_target = (data.get("target") or "").strip()
            target = identify_target or None
        elif intent == CommandIntent.BLESS:
            bless_target = (data.get("target") or "").strip()
            target = bless_target or None
        elif intent == CommandIntent.CURSE:
            curse_target = (data.get("target") or "").strip()
            target = curse_target or None
        elif intent == CommandIntent.TRANSMUTE:
            from_item = (data.get("from") or "").strip()
            to_item = (data.get("to") or "").strip()
            target = from_item or None
            secondary_target = to_item or None
        elif intent == CommandIntent.RITUAL:
            ritual_name = (data.get("name") or "").strip()
            target = ritual_name or None
        elif intent == CommandIntent.THROW:
            item_name = (data.get("item") or "").strip()
            target_name = (data.get("target") or "").strip()
            target = item_name or None
            secondary_target = target_name or None
        elif intent == CommandIntent.CATCH:
            catch_item = (data.get("item") or "").strip()
            target = catch_item or None
        elif intent == CommandIntent.USE:
            item_name = (data.get("item") or "").strip()
            target = item_name or None
        elif intent == CommandIntent.USE_ON:
            item_name = (data.get("item") or "").strip()
            target_name = (data.get("target") or "").strip()
            target = item_name or None
            secondary_target = target_name or None
        elif intent == CommandIntent.ENTER:
            place_name = (data.get("place") or "").strip()
            target = place_name or None
        elif intent == CommandIntent.EXIT:
            place_name = (data.get("place") or "").strip()
            target = place_name or None
        elif intent == CommandIntent.SWIM:
            swim_dir = (data.get("direction") or "").strip()
            direction = swim_dir or None
        elif intent == CommandIntent.SEARCH:
            scope = (data.get("scope") or "").strip()
            obj = (data.get("object") or "").strip()
            if scope == "room":
                search_scope = "room"
            else:
                search_scope = None
            target = obj or None
            if search_scope:
                preposition = search_scope
        elif intent == CommandIntent.CLIMB:
            climb_obj = (data.get("object") or "").strip()
            climb_direction = (data.get("direction") or "").strip()
            climb_scope = (data.get("scope") or "").strip()
            target = climb_obj or None
            direction = climb_direction or None
            if climb_scope:
                preposition = climb_scope or None
        elif intent in {CommandIntent.BLOCK, CommandIntent.DODGE, CommandIntent.FLEE}:
            pass
        elif intent == CommandIntent.TALK:
            npc_name = (data.get("npc") or "").strip()
            target = npc_name or None
        elif intent == CommandIntent.ASK:
            npc_name = (data.get("npc") or "").strip()
            topic = (data.get("topic") or "").strip()
            target = npc_name or None
            secondary_target = topic or None
        elif intent in {CommandIntent.GIVE, CommandIntent.SHOW}:
            object_name = (data.get("object") or "").strip()
            npc_name = (data.get("npc") or "").strip()
            target = object_name or None
            secondary_target = npc_name or None
        elif intent in {
            CommandIntent.OPEN,
            CommandIntent.CLOSE,
            CommandIntent.LOCK,
            CommandIntent.UNLOCK,
        }:
            target_name = (data.get("target") or "").strip()
            target = target_name or None
            if target_name:
                target_object_id = self._resolve_object_id_in_location(target_name)

            if intent in {CommandIntent.LOCK, CommandIntent.UNLOCK}:
                tool_name = (data.get("tool") or "").strip()
                if tool_name:
                    secondary_target = tool_name
                    resolved_tool_id = self._resolve_tool_id(tool_name)
                    secondary_target_id = resolved_tool_id or tool_name

        parsed = ParsedIntent(
            intent=intent,
            direction=direction,
            target=target,
            target_object_id=target_object_id,
            secondary_target=secondary_target,
            secondary_target_id=secondary_target_id,
            preposition=preposition,
            action=action,
            original_input=original_input,
            confidence=1.0 if intent != CommandIntent.UNKNOWN else 0.0,
        )
        return parsed

    def _resolve_object_id_in_location(self, target_name: str) -> str | None:
        if not target_name or not getattr(self, "game_state", None):
            return None
        try:
            return self.game_state.find_object_id_by_name_in_location(
                target_name,
                self.game_state.current_room_id,
                self.game_state.current_area_id,
            )
        except Exception as exc:
            logger.debug(f"Failed to resolve object '{target_name}' in location: {exc}")
            return None

    def _resolve_tool_id(self, tool_name: str) -> str | None:
        if not tool_name or not getattr(self, "game_state", None):
            return None
        try:
            return self.game_state.find_item_id_held_or_worn(tool_name)
        except Exception as exc:
            logger.debug(f"Failed to resolve tool '{tool_name}': {exc}")
            return None

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
            CommandIntent.READ: handle_look,
            CommandIntent.SCAN: handle_search,
            CommandIntent.INVENTORY: handle_inventory,
            CommandIntent.HELP: handle_help,
            CommandIntent.SAVE: handle_save,
            CommandIntent.LOAD: handle_load,
            CommandIntent.QUIT: handle_quit,
            CommandIntent.TAKE: handle_take,
            CommandIntent.DROP: handle_drop,
            CommandIntent.EQUIP: handle_equip, # Covers wear/remove/wield etc.
            CommandIntent.SEARCH: handle_search,
            CommandIntent.PUT: handle_put,
            CommandIntent.TAKE_FROM: handle_take_from,
            CommandIntent.TALK: handle_talk,
            CommandIntent.ASK: handle_ask,
            CommandIntent.GIVE: handle_give,
            CommandIntent.SHOW: handle_show,
            CommandIntent.UNEQUIP: handle_equip,
            CommandIntent.WEAR: handle_equip,
            CommandIntent.REMOVE: handle_equip,
            CommandIntent.WIELD: handle_equip,
            CommandIntent.ATTACK: handle_attack,
            CommandIntent.AIM: handle_aim,
            CommandIntent.SHOOT: handle_shoot,
            CommandIntent.BLOCK: handle_block,
            CommandIntent.DODGE: handle_dodge,
            CommandIntent.FLEE: handle_flee,
            CommandIntent.RELOAD: handle_reload,
            CommandIntent.UNLOAD: handle_unload,
            CommandIntent.CHECK: handle_check,
            CommandIntent.SNEAK: handle_sneak,
            CommandIntent.HIDE: handle_hide,
            CommandIntent.PICKPOCKET: handle_pickpocket,
            CommandIntent.DISARM_TRAP: handle_disarm_trap,
            CommandIntent.CRAFT: handle_craft,
            CommandIntent.COMBINE: handle_combine,
            CommandIntent.GATHER: handle_gather,
            CommandIntent.CAST: handle_cast,
            CommandIntent.CHANNEL: handle_channel,
            CommandIntent.SUMMON: handle_summon,
            CommandIntent.DISMISS: handle_dismiss,
            CommandIntent.ENCHANT: handle_enchant,
            CommandIntent.IDENTIFY: handle_identify,
            CommandIntent.BLESS: handle_bless,
            CommandIntent.CURSE: handle_curse,
            CommandIntent.TRANSMUTE: handle_transmute,
            CommandIntent.RITUAL: handle_ritual,
            CommandIntent.USE: handle_use,
            CommandIntent.USE_ON: handle_use_on,
            CommandIntent.THROW: handle_throw,
            CommandIntent.CATCH: handle_catch,
            CommandIntent.WAIT: handle_wait,
            CommandIntent.ENTER: handle_enter,
            CommandIntent.EXIT: handle_exit,
            CommandIntent.SWIM: handle_swim,
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
