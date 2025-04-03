from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import spacy
from spacy.pipeline import EntityRuler
from fuzzywuzzy import fuzz
from .command_defs import CommandIntent, ParsedIntent
from .game_state import GameState, PowerState

class NLPCommandParser:
    """Handles parsing and processing of player commands using NLP."""
    
    # Define verb patterns for each intent
    VERB_PATTERNS = {
        CommandIntent.MOVE: {
            "verbs": ["go", "walk", "run", "move", "head", "travel", "n", "s", "e", "w", "u", "d", "float", "drift"],
            "context_words": ["to", "towards", "into", "through", "north", "south", "east", "west", "up", "down", "forward", "backward",
                            "corridor", "hallway", "airlock", "hatch", "vent", "tunnel", "passage", "bridge", "cargo bay", "engineering"],
            "priority": 70
        },
        CommandIntent.LOOK: {
            "verbs": ["look", "l", "examine", "inspect", "check", "survey"],
            "context_words": ["at", "around", "room", "area", "location", "object", "item", "person", "creature",
                            "console", "panel", "display", "screen", "monitor", "hologram", "terminal", "device"],
            "priority": 65
        },
        CommandIntent.INVENTORY: {
            "verbs": ["inventory", "inv", "i", "items", "stuff", "equipment", "gear", "loadout", "cargo"],
            "context_words": ["carrying", "holding", "wearing", "wielding", "equipped", "stored", "packed", "loaded"],
            "priority": 60
        },
        CommandIntent.QUIT: {
            "verbs": ["quit", "exit", "q", "leave", "logout", "disconnect", "end"],
            "context_words": ["game", "program", "system", "session"],
            "priority": 100
        },
        CommandIntent.HELP: {
            "verbs": ["help", "h", "?", "assist", "guide", "tutorial", "manual", "info", "information"],
            "context_words": ["how", "what", "where", "when", "why", "commands", "controls", "interface"],
            "priority": 50
        },
        CommandIntent.COMMUNICATE: {
            "verbs": ["talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast"],
            "context_words": ["to", "with", "at", "npc", "person", "creature", "alien", "robot", "android", "ai", "computer",
                            "comm", "radio", "intercom", "transmitter", "receiver", "channel", "frequency"],
            "priority": 75
        },
        CommandIntent.COMBAT: {
            "verbs": ["attack", "fight", "hit", "strike", "shoot", "fire", "blast", "discharge", "engage", "neutralize"],
            "context_words": ["with", "using", "enemy", "monster", "weapon", "sword", "axe", "bow", "target", "opponent", "foe", "creature",
                            "phaser", "blaster", "laser", "pulse", "beam", "alien", "robot", "android", "drone", "hostile", "threat"],
            "priority": 90
        },
        CommandIntent.SEARCH: {
            "verbs": ["search", "find", "locate", "seek", "probe", "detect", "discover", "track"],
            "context_words": ["for", "room", "area", "chest", "key", "item", "object", "person", "creature",
                            "console", "panel", "terminal", "device", "data", "information", "signal", "lifeform", "artifact",
                            "radiation", "energy", "heat", "anomaly", "signature", "frequency", "emission"],
            "priority": 80
        },
        CommandIntent.MANIPULATE: {
            "verbs": ["open", "close", "lock", "unlock", "push", "pull", "turn", "press", "activate", "deactivate", "engage", "disengage",
                     "weld", "repair", "fix", "hack", "override", "bypass", "jump", "modify", "adjust", "calibrate"],
            "context_words": ["door", "chest", "box", "window", "button", "lever", "key", "card", "torch", "computer", "terminal", "screen",
                            "panel", "console", "switch", "control", "hatch", "airlock", "gate", "valve", "circuit", "system"],
            "priority": 85
        },
        CommandIntent.CLIMB: {
            "verbs": ["climb", "jump", "crawl", "swim", "hover", "fly", "launch", "land"],
            "context_words": ["ladder", "wall", "rope", "gap", "fence", "pit", "tunnel", "vent", "pipe", "space",
                            "platform", "catwalk", "shaft", "conduit", "grav shaft", "elevator", "lift", "jetpack", "thruster"],
            "priority": 75
        },
        CommandIntent.SOCIAL: {
            "verbs": ["give", "show", "trade", "follow", "greet", "salute", "wave", "gesture", "signal"],
            "context_words": ["to", "for", "with", "item", "sword", "key", "potion", "map", "badge", "document", "picture",
                            "credits", "data", "information", "artifact", "device", "tool", "weapon", "equipment", "supplies"],
            "priority": 70
        },
        CommandIntent.ENVIRONMENT: {
            "verbs": ["dig", "cut", "burn", "pour", "light", "extinguish", "fill", "break", "smash", "destroy", "shatter"],
            "context_words": ["with", "using", "into", "onto", "hole", "rope", "torch", "fire", "wall", "door", "window", "box",
                            "object", "item", "glass", "wood", "stone", "metal", "circuit", "panel", "console", "terminal",
                            "system", "device", "equipment", "machinery", "power", "energy", "shield", "barrier"],
            "priority": 85
        },
        CommandIntent.GATHER_INFO: {
            "verbs": ["read", "listen", "smell", "touch", "taste", "study", "scan", "analyze", "monitor"],
            "context_words": ["book", "sign", "note", "scroll", "sound", "music", "noise", "conversation", "food", "flower",
                            "smoke", "potion", "wall", "surface", "object", "material", "data", "information", "signal",
                            "display", "screen", "terminal", "console", "hologram", "sensor", "scanner", "detector"],
            "priority": 75
        },
        CommandIntent.EQUIP: {
            "verbs": ["equip", "wear", "remove", "unequip", "wield", "hold", "power", "charge"],
            "context_words": ["sword", "armor", "shield", "weapon", "helmet", "boots", "gloves", "ring", "tool", "device",
                            "phaser", "blaster", "laser", "suit", "armor", "shield", "generator", "battery", "power pack",
                            "jetpack", "thruster", "scanner", "communicator", "medkit", "toolkit"],
            "priority": 80
        },
        CommandIntent.TIME: {
            "verbs": ["wait", "rest", "sleep", "pause", "meditate", "nap", "stop", "delay", "hold", "standby"],
            "context_words": ["for", "until", "while", "briefly", "moment", "time", "cycle", "rotation", "orbit", "period"],
            "priority": 80
        },
        CommandIntent.COMPLEX: {
            "verbs": ["combine", "craft", "build", "create", "construct", "forge", "brew", "synthesize", "fabricate", "assemble"],
            "context_words": ["items", "ingredients", "parts", "materials", "potion", "tool", "weapon", "armor", "shelter",
                            "bridge", "wall", "structure", "device", "machine", "equipment", "circuit", "component",
                            "module", "system", "device", "artifact", "technology", "power", "energy", "shield"],
            "priority": 95
        },
        CommandIntent.TAKE: {
            "verbs": ["take", "grab", "pick", "get", "collect", "acquire", "obtain", "retrieve", "recover"],
            "context_words": ["up", "item", "object", "torch", "key", "sword", "potion", "book", "scroll", "map", "coin", "gem",
                            "phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"],
            "priority": 85
        }
    }
    
    def __init__(self, game_state: GameState):
        """Initialize the NLP command parser."""
        self.game_state = game_state
        self.nlp = spacy.load("en_core_web_sm")
        
        # Create a list of all valid words for fuzzy matching
        self.valid_words = set()
        for pattern in self.VERB_PATTERNS.values():
            self.valid_words.update(pattern["verbs"])
            self.valid_words.update(pattern["context_words"])
        
        # Add common game objects and NPCs to valid words
        self.valid_words.update([
            "key", "door", "button", "lever", "card", "torch", "computer",
            "terminal", "screen", "panel", "tool", "device", "sword", "shield",
            "potion", "book", "scroll", "map", "coin", "gem", "crystal",
            "backpack", "chest", "box", "window", "gate", "rope", "ladder",
            "guard", "merchant", "captain", "soldier", "villager", "alien",
            "robot", "scientist", "doctor", "engineer", "pilot", "crew",
            "room", "area", "chest", "cabinet", "gap", "hole", "note",
            "ingredients", "items", "materials", "parts", "tools", "weapons",
            "armor", "equipment", "structures", "buildings", "machines"
        ])
        
        # Define intent priorities (higher number = higher priority)
        self.intent_priorities = {
            CommandIntent.COMBAT: 100,
            CommandIntent.COMPLEX: 95,
            CommandIntent.EQUIP: 90,
            CommandIntent.MANIPULATE: 85,
            CommandIntent.ENVIRONMENT: 80,
            CommandIntent.CLIMB: 75,
            CommandIntent.SOCIAL: 70,
            CommandIntent.GATHER_INFO: 65,
            CommandIntent.SEARCH: 60,
            CommandIntent.COMMUNICATE: 55,
            CommandIntent.LOOK: 50,
            CommandIntent.MOVE: 45,
            CommandIntent.TAKE: 40,
            CommandIntent.DROP: 35,
            CommandIntent.USE: 30,
            CommandIntent.TIME: 25,
            CommandIntent.INVENTORY: 20,
            CommandIntent.QUIT: 15,
            CommandIntent.HELP: 10,
            CommandIntent.UNKNOWN: -1
        }
        
        # Define context words for each intent
        self.context_words = {
            CommandIntent.COMBAT: ["enemy", "target", "weapon", "fight", "battle", "attack", "alien", "monster", "position", "opponent", "foe", "creature", "beast"],
            CommandIntent.EQUIP: ["armor", "weapon", "helmet", "shield", "gear", "equipment", "sword", "staff", "boots", "gloves", "ring", "amulet", "cloak", "bow", "dagger", "axe"],
            CommandIntent.MANIPULATE: ["door", "window", "chest", "light", "lever", "button", "switch", "lock", "panel", "gate", "lid", "hatch", "valve", "box", "cabinet", "safe"],
            CommandIntent.COMPLEX: ["items", "potion", "shelter", "device", "tool", "craft", "materials", "ingredients", "components", "recipe", "blueprint", "formula", "mixture", "weapon", "armor"],
            CommandIntent.ENVIRONMENT: ["hole", "rope", "paper", "water", "fire", "ground", "dirt", "wall", "tree", "rock", "bush", "plant", "torch"],
            CommandIntent.CLIMB: ["ladder", "gap", "tunnel", "river", "wall", "cliff", "mountain", "tree", "rope", "stairs", "platform", "ledge", "bridge", "fence", "pit"],
            CommandIntent.SOCIAL: ["merchant", "guide", "npc", "person", "character", "ally", "item", "map", "friend", "companion", "trader", "villager", "guard", "sword", "key"],
            CommandIntent.GATHER_INFO: ["book", "music", "flowers", "wall", "text", "sign", "sound", "smell", "scroll", "note", "letter", "inscription", "writing", "noise", "conversation"],
            CommandIntent.SEARCH: ["room", "key", "area", "noise", "clue", "evidence", "place", "location", "spot", "corner", "chest", "container", "box", "tunnel", "drawer"],
            CommandIntent.COMMUNICATE: ["npc", "captain", "mission", "story", "quest", "dialogue", "person", "guard", "merchant", "villager", "companion", "friend", "ally"]
        }
        
        # Add game-specific vocabulary
        self.add_game_vocabulary()
        
        # Initialize custom entity patterns
        self.custom_patterns = []
        self.initialize_custom_patterns()
    
    def add_game_vocabulary(self) -> None:
        """Add game-specific vocabulary to the NLP pipeline."""
        # Add special case patterns
        special_cases = [
            ("nav_station", [{"ORTH": "nav_station"}]),
            ("power_core", [{"ORTH": "power_core"}]),
            ("access_card", [{"ORTH": "access_card"}])
        ]
        for text, case in special_cases:
            self.nlp.tokenizer.add_special_case(text, case)
    
    def initialize_custom_patterns(self) -> None:
        """Initialize custom entity patterns for game objects and locations."""
        # Add patterns for directions
        direction_patterns = [
            {"label": "DIRECTION", "pattern": direction}
            for direction in self.VERB_PATTERNS[CommandIntent.MOVE]["verbs"]
            if direction in ["north", "south", "east", "west", "up", "down"]
        ]
        self.custom_patterns.extend(direction_patterns)

        # Add common game objects
        object_patterns = [
            {"label": "OBJECT", "pattern": obj}
            for obj in [
                "key", "door", "button", "lever", "card", "torch", "computer",
                "terminal", "screen", "panel", "tool", "device", "sword", "shield",
                "potion", "book", "scroll", "map", "coin", "gem", "crystal",
                "backpack", "chest", "box", "window", "gate", "rope", "ladder"
            ]
        ]
        self.custom_patterns.extend(object_patterns)

        # Add common NPCs
        npc_patterns = [
            {"label": "NPC", "pattern": npc}
            for npc in [
                "guard", "merchant", "captain", "soldier", "villager", "alien",
                "robot", "scientist", "doctor", "engineer", "pilot", "crew"
            ]
        ]
        self.custom_patterns.extend(npc_patterns)

        # Add common locations
        location_patterns = [
            {"label": "LOCATION", "pattern": loc}
            for loc in [
                "bridge", "engine_room", "cargo_bay", "medbay", "quarters",
                "airlock", "corridor", "storage", "lab", "cafeteria"
            ]
        ]
        self.custom_patterns.extend(location_patterns)

        # Add the patterns to the NLP pipeline
        if "entity_ruler" not in self.nlp.pipe_names:
            ruler = EntityRuler(self.nlp)
            ruler.add_patterns(self.custom_patterns)
            self.nlp.add_pipe("entity_ruler", before="ner")
        else:
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.add_patterns(self.custom_patterns)
    
    def _find_closest_match(self, word: str, threshold: int = 80) -> Optional[str]:
        """Find the closest matching word using fuzzy string matching."""
        if not word:
            return None
            
        # First try exact match
        if word in self.valid_words:
            return word
            
        # Try fuzzy matching
        best_match = None
        best_ratio = 0
        
        for valid_word in self.valid_words:
            ratio = fuzz.ratio(word, valid_word)
            if ratio > best_ratio and ratio >= threshold:
                best_ratio = ratio
                best_match = valid_word
                
        return best_match
    
    def parse_command(self, command: str) -> ParsedIntent:
        """Parse a command string into a ParsedIntent object."""
        if not command:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, action="", target="", direction=None, confidence=0.0, raw_input=command)

        # Convert command to lowercase for consistent matching
        command = command.lower().strip()

        # Handle single-word commands first
        if command in ["i", "inventory", "inv", "items", "cargo", "loadout"]:
            return ParsedIntent(intent=CommandIntent.INVENTORY, action="inventory", target="", direction=None, confidence=1.0, raw_input=command)
        elif command in ["q", "quit", "exit", "bye", "logout", "disconnect"]:
            return ParsedIntent(intent=CommandIntent.QUIT, action="quit", target="", direction=None, confidence=1.0, raw_input=command)
        elif command in ["h", "help", "?", "commands", "tutorial", "manual"]:
            return ParsedIntent(intent=CommandIntent.HELP, action="help", target="", direction=None, confidence=1.0, raw_input=command)
        elif command in ["wait", "rest", "sleep", "pause", "meditate", "nap", "stop", "delay", "hold", "standby"]:
            return ParsedIntent(intent=CommandIntent.TIME, action=command, target="", direction=None, confidence=1.0, raw_input=command)

        # Handle direction commands
        directions = ["north", "south", "east", "west", "up", "down", "forward", "backward"]
        if command in directions:
            return ParsedIntent(intent=CommandIntent.MOVE, action="move", target="", direction=command, confidence=1.0, raw_input=command)

        # Split command into words
        words = command.split()
        if not words:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, action="", target="", direction=None, confidence=0.0, raw_input=command)

        # Get the verb (first word)
        verb = words[0]
        remaining_words = words[1:]

        # Find the best matching intent based on verb and context
        best_intent = CommandIntent.UNKNOWN
        best_confidence = 0.0
        best_action = verb
        target = ""
        direction = None

        # Check each intent pattern
        for intent, pattern in self.VERB_PATTERNS.items():
            # Check if verb matches any of the pattern's verbs
            if verb in pattern["verbs"]:
                # Calculate confidence based on verb match and context
                confidence = 0.9  # Base confidence for verb match
                
                # Check context words in remaining words
                context_matches = sum(1 for word in remaining_words if word in pattern["context_words"])
                if context_matches > 0:
                    confidence += 0.1 * context_matches

                # Update best match if this is better
                if confidence > best_confidence:
                    best_intent = intent
                    best_confidence = confidence
                    best_action = verb

        # Extract target and direction based on intent
        if best_intent != CommandIntent.UNKNOWN:
            if best_intent == CommandIntent.MOVE:
                # Look for direction in remaining words
                for word in remaining_words:
                    if word in directions:
                        direction = word
                        remaining_words.remove(word)
                        break
                # Use remaining words as target (location)
                target = " ".join(remaining_words)
            else:
                # For other intents, look for target in remaining words
                # Skip common prepositions and articles
                skip_words = {"the", "a", "an", "to", "at", "in", "on", "with", "using", "for", "of", "from", "by"}
                target_words = [word for word in remaining_words if word not in skip_words]
                target = " ".join(target_words)

        return ParsedIntent(
            intent=best_intent,
            action=best_action,
            target=target,
            direction=direction,
            confidence=best_confidence,
            raw_input=command
        )
    
    def _determine_intent(self, verb: str, command: str, target: str) -> CommandIntent:
        """Determine the command intent based on the verb and context."""
        if not verb:
            return CommandIntent.UNKNOWN

        # Check each intent's verb patterns
        matching_intents = []
        for intent, pattern in self.VERB_PATTERNS.items():
            # Check if verb matches
            if verb in pattern["verbs"]:
                matching_intents.append((intent, pattern["priority"]))
                continue
            
            # Check context words
            for context_word in pattern["context_words"]:
                if context_word in command:
                    matching_intents.append((intent, pattern["priority"] - 20))  # Lower priority for context matches
                    break

        # If no matches found, return UNKNOWN
        if not matching_intents:
            return CommandIntent.UNKNOWN

        # Sort by priority and return highest
        matching_intents.sort(key=lambda x: x[1], reverse=True)
        return matching_intents[0][0]

    def _calculate_confidence(self, intent: CommandIntent, verb: str, target: str) -> float:
        """Calculate confidence score for the parsed intent."""
        if intent == CommandIntent.UNKNOWN:
            return 0.0
        
        base_confidence = 0.8  # Base confidence for recognized intents
        
        # Boost confidence based on verb recognition
        if verb in self.VERB_PATTERNS[intent]["verbs"]:
            base_confidence += 0.1
            
        # Boost confidence based on target recognition
        if target and intent in self.context_words:
            if any(word in target for word in self.context_words[intent]):
                base_confidence += 0.1
                
        return min(base_confidence, 1.0)
    
    def process_command(self, command_input: str) -> Tuple[str, bool]:
        """Process a command and return the result and whether the game should continue."""
        parsed = self.parse_command(command_input)
        
        if parsed.intent == CommandIntent.UNKNOWN:
            return "I'm not sure what you want to do. Try rephrasing that.", True
        
        # Process the command based on its intent
        if parsed.intent == CommandIntent.LOOK:
            return self._process_look(parsed), True
        elif parsed.intent == CommandIntent.MOVE:
            return self._process_move(parsed), True
        elif parsed.intent == CommandIntent.TAKE:
            return self._process_take(parsed), True
        elif parsed.intent == CommandIntent.DROP:
            return self._process_drop(parsed), True
        elif parsed.intent == CommandIntent.USE:
            return self._process_use(parsed), True
        elif parsed.intent == CommandIntent.INVENTORY:
            return self._process_inventory(), True
        elif parsed.intent == CommandIntent.SAVE:
            return self._process_save(), True
        elif parsed.intent == CommandIntent.LOAD:
            return self._process_load(), True
        elif parsed.intent == CommandIntent.QUIT:
            return "Goodbye!", False
        elif parsed.intent == CommandIntent.HELP:
            return self._process_help(), True
        # New intent handlers
        elif parsed.intent == CommandIntent.COMMUNICATE:
            return self._process_communicate(parsed), True
        elif parsed.intent == CommandIntent.COMBAT:
            return self._process_combat(parsed), True
        elif parsed.intent == CommandIntent.SEARCH:
            return self._process_search(parsed), True
        elif parsed.intent == CommandIntent.MANIPULATE:
            return self._process_manipulate(parsed), True
        elif parsed.intent == CommandIntent.CLIMB:
            return self._process_climb(parsed), True
        elif parsed.intent == CommandIntent.SOCIAL:
            return self._process_social(parsed), True
        elif parsed.intent == CommandIntent.ENVIRONMENT:
            return self._process_environment(parsed), True
        elif parsed.intent == CommandIntent.GATHER_INFO:
            return self._process_gather_info(parsed), True
        elif parsed.intent == CommandIntent.EQUIP:
            return self._process_equip(parsed), True
        elif parsed.intent == CommandIntent.TIME:
            return self._process_time(parsed), True
        elif parsed.intent == CommandIntent.COMPLEX:
            return self._process_complex(parsed), True
        
        return "I don't know how to do that.", True
    
    def _process_look(self, parsed: ParsedIntent) -> str:
        """Process a look command."""
        if not parsed.target:
            # Look at current location
            return f"You are in the {self.game_state.current_room_id}"
        else:
            # Look at specific object
            return f"You examine the {parsed.target} carefully"
    
    def _process_move(self, parsed: ParsedIntent) -> str:
        """Process a movement command."""
        if not parsed.direction:
            return "Which direction do you want to go?"
        return f"You move {parsed.direction}"
    
    def _process_take(self, parsed: ParsedIntent) -> str:
        """Process a take command."""
        if not parsed.target:
            return "What do you want to take?"
        return f"You try to take the {parsed.target}"
    
    def _process_drop(self, parsed: ParsedIntent) -> str:
        """Process a drop command."""
        if not parsed.target:
            return "What do you want to drop?"
        return f"You try to drop the {parsed.target}"
    
    def _process_use(self, parsed: ParsedIntent) -> str:
        """Process a use command."""
        if not parsed.target:
            return "What do you want to use?"
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
- Look/examine/inspect [object]: Look around or examine something
- Go/move/walk [direction]: Move in a direction (north, south, east, west, up, down)
- Take/grab/get [object]: Pick up an object
- Drop/put down [object]: Drop an object
- Use/activate/operate [object]: Use or activate something
- Inventory: Check what you're carrying
- Save: Save your game
- Load: Load your game
- Quit/exit: Exit the game
- Help: Show this help message

You can also use natural language commands like:
- "Check what's in my inventory"
- "Walk towards the north door"
- "Take a look around"
- "Use the key on the door"
""" 

    def _process_communicate(self, parsed: ParsedIntent) -> str:
        """Process communication commands."""
        if not parsed.target:
            return "Who would you like to communicate with?"
        return f"You attempt to {parsed.action} with {parsed.target}."

    def _process_combat(self, parsed: ParsedIntent) -> str:
        """Process combat commands."""
        if not parsed.target:
            return "What would you like to attack?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_search(self, parsed: ParsedIntent) -> str:
        """Process search commands."""
        if not parsed.target:
            return "What would you like to search for?"
        return f"You search for {parsed.target}."

    def _process_manipulate(self, parsed: ParsedIntent) -> str:
        """Process manipulation commands."""
        if not parsed.target:
            return "What would you like to manipulate?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_climb(self, parsed: ParsedIntent) -> str:
        """Process climbing and movement commands."""
        if not parsed.target:
            return "What would you like to climb?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_social(self, parsed: ParsedIntent) -> str:
        """Process social interaction commands."""
        if not parsed.target:
            return "Who would you like to interact with?"
        return f"You attempt to {parsed.action} with {parsed.target}."

    def _process_environment(self, parsed: ParsedIntent) -> str:
        """Process environmental interaction commands."""
        if not parsed.target:
            return "What would you like to interact with?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_gather_info(self, parsed: ParsedIntent) -> str:
        """Process information gathering commands."""
        if not parsed.target:
            return "What would you like to gather information about?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_equip(self, parsed: ParsedIntent) -> str:
        """Process equipment commands."""
        if not parsed.target:
            return "What would you like to equip?"
        return f"You attempt to {parsed.action} {parsed.target}."

    def _process_time(self, parsed: ParsedIntent) -> str:
        """Process time-related commands."""
        if parsed.action in {"wait", "rest", "sleep", "meditate"}:
            return f"You {parsed.action} for a moment."
        elif parsed.action in {"pause", "resume"}:
            return f"You {parsed.action} the game."
        return f"You attempt to {parsed.action}."

    def _process_complex(self, parsed: ParsedIntent) -> str:
        """Process complex action commands."""
        if not parsed.target:
            return "What would you like to work on?"
        return f"You attempt to {parsed.action} {parsed.target}."
    