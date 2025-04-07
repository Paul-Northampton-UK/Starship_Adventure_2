from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import spacy
from spacy.pipeline import EntityRuler
from fuzzywuzzy import fuzz
from .command_defs import CommandIntent, ParsedIntent
from .game_state import GameState, PowerState
import logging

class NLPCommandParser:
    """Handles parsing and processing of player commands using NLP."""
    
    # Define verb patterns for each intent
    VERB_PATTERNS = {
        CommandIntent.MOVE: {
            "verbs": ["go", "walk", "run", "move", "head", "travel", "n", "s", "e", "w", "u", "d", "ne", "nw", "se", "sw", "float", "drift"],
            "context_words": ["to", "towards", "into", "through", "north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest", "forward", "backward",
                            "corridor", "hallway", "airlock", "hatch", "vent", "tunnel", "passage", "bridge", "cargo bay", "engineering"],
            "priority": 70
        },
        CommandIntent.LOOK: {
            "verbs": ["look", "l", "examine", "ex", "inspect", "check", "survey"],
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
            "verbs": ["talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast", "say"],
            "context_words": ["to", "with", "at", "npc", "person", "creature", "alien", "robot", "android", "ai", "computer",
                            "comm", "radio", "intercom", "transmitter", "receiver", "channel", "frequency"],
            "priority": 75
        },
        CommandIntent.COMBAT: {
            "verbs": ["attack", "fight", "hit", "strike", "shoot", "fire", "blast", "discharge", "engage", "neutralize", "kill"],
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
        },
        CommandIntent.DROP: {
            "verbs": ["drop", "put"],
            "context_words": ["down", "item", "object", "backpack", "key", "datapad"],
            "priority": 35
        }
    }
    
    def __init__(self, game_state: GameState):
        """Initialize the NLP command parser."""
        self.game_state = game_state
        self.nlp = spacy.load("en_core_web_sm")
        
        # Create a list of all valid words for fuzzy matching
        self.valid_words = set()
        for pattern_intent, pattern_data in self.VERB_PATTERNS.items(): # Iterate through items directly
            self.valid_words.update(pattern_data.get("verbs", []))
            self.valid_words.update(pattern_data.get("context_words", []))
        
        # Add common game objects and NPCs to valid words (can be refined later)
        self.valid_words.update([
            "key", "door", "button", "lever", "card", "torch", "computer",
            "terminal", "screen", "panel", "tool", "device", "sword", "shield",
            "potion", "book", "scroll", "map", "coin", "gem", "crystal",
            "backpack", "chest", "box", "window", "gate", "rope", "ladder",
            "guard", "merchant", "captain", "soldier", "villager", "alien",
            "robot", "scientist", "doctor", "engineer", "pilot", "crew",
            "room", "area", "cabinet", "gap", "hole", "note",
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
        
        # Define context words for each intent (optional, can be removed if relying solely on verbs/entities)
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
        
        # Add game-specific vocabulary (e.g., tokenizer exceptions)
        self.add_game_vocabulary()
        
        # Initialize the custom patterns list BEFORE initializing the ruler
        self.custom_patterns = [] 
        self._populate_custom_patterns() # Ensure patterns are generated first
        
        # Initialize the Entity Ruler with custom patterns AFTER they are populated
        self.initialize_entity_ruler()
    
    def add_game_vocabulary(self) -> None:
        """Add game-specific vocabulary exceptions to the NLP pipeline's tokenizer."""
        # Example: Prevent splitting on hyphen
        # special_cases = [
        #     ("state-of-the-art", [{spacy.symbols.ORTH: "state-of-the-art"}]),
        # ]
        # Example: Handle specific contraction
        # special_cases.append(("what's", [{spacy.symbols.ORTH: "what"}, {spacy.symbols.ORTH: "'s"}]))

        # The multi-word entities like "nav station" are handled by the EntityRuler patterns,
        # not tokenizer special cases.
        pass # No special tokenizer cases needed currently

        # Original problematic code commented out:
        # special_cases = [
        #     ("nav station", [{spacy.symbols.ORTH: "nav"}, {spacy.symbols.ORTH: "station"}]),
        #     ("power core", [{spacy.symbols.ORTH: "power"}, {spacy.symbols.ORTH: "core"}]),
        #     ("access card", [{spacy.symbols.ORTH: "access"}, {spacy.symbols.ORTH: "card"}]),
        # ]
        # for text, case in special_cases:
        #     if text not in self.nlp.tokenizer.vocab.strings:
        #          self.nlp.tokenizer.add_special_case(text, case)

    def _populate_custom_patterns(self) -> None:
        """Builds the list of custom entity patterns."""
        self.custom_patterns = [] # Start fresh
        logging.debug("Populating custom entity patterns...")

        # --- Define pattern lists --- 
        # Include single letter, full names, hyphenated, and two-word variants
        direction_list = [
            # Standard Directions
            "north", "south", "east", "west", "up", "down", 
            "n", "s", "e", "w", "u", "d", 
            "ne", "nw", "se", "sw",
            "northeast", "northwest", "southeast", "southwest",
            # Hyphenated (will be handled specifically below)
            "north-east", "north-west", "south-east", "south-west", 
            # Two-word 
            "north east", "north west", "south east", "south west" 
        ]
        
        # Define specific patterns for hyphenated directions first for clarity
        hyphenated_patterns = {
            "north-east": [{"LOWER": "north"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "east"}],
            "north-west": [{"LOWER": "north"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "west"}],
            "south-east": [{"LOWER": "south"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "east"}],
            "south-west": [{"LOWER": "south"}, {"IS_PUNCT": True, "ORTH": "-"}, {"LOWER": "west"}],
        }
        for text, pattern in hyphenated_patterns.items():
             logging.debug(f"Adding hyphenated DIRECTION pattern: {pattern}")
             self.custom_patterns.append({"label": "DIRECTION", "pattern": pattern, "id": text.replace('-', '')}) # Store normalized ID

        # Add patterns for other directions (single word, abbreviations, two-word)
        for direction in direction_list:
            direction_lower = direction.lower()
            
            # Skip hyphenated ones, already handled
            if '-' in direction_lower:
                continue

            # Handle two-word directions
            if ' ' in direction_lower:
                 parts = direction_lower.split()
                 pattern = [{spacy.symbols.LOWER: part} for part in parts]
                 normalized_id = direction_lower.replace(' ','')
            # Handle single word/abbreviation
            else:
                 pattern = [{spacy.symbols.LOWER: direction_lower}]
                 normalized_id = direction_lower
            
            if pattern: # Ensure pattern is not empty
                 logging.debug(f"Adding standard/multi-word DIRECTION pattern: {pattern}")
                 self.custom_patterns.append({"label": "DIRECTION", "pattern": pattern, "id": normalized_id})

        # --- Add patterns for specific game objects/locations dynamically? ---
        # Example: Patterns for specific items using their names and synonyms
        logging.debug("Adding GAME_OBJECT patterns...")
        for obj_id, obj_data in self.game_state.objects_data.items():
            names_to_pattern = set()
            # Add the primary name
            primary_name = obj_data.get('name')
            if primary_name:
                 names_to_pattern.add(primary_name.lower())
            # Add command aliases
            aliases = obj_data.get('command_aliases', [])
            if isinstance(aliases, list):
                 for alias in aliases:
                      if isinstance(alias, str):
                           names_to_pattern.add(alias.lower())

            for name in names_to_pattern:
                 if name: # Ensure name is not empty
                     # Simple pattern based on lower case name tokens
                     pattern = [{spacy.symbols.LOWER: token.lower()} for token in name.split()]
                     if pattern:
                          # Add the object ID to the pattern for easy retrieval later
                          self.custom_patterns.append({
                               "label": "GAME_OBJECT", 
                               "pattern": pattern, 
                               "id": obj_id # Store the actual object ID here
                          })
                          logging.debug(f"Added GAME_OBJECT pattern for ID '{obj_id}': {pattern}")
        
        logging.debug(f"Finished populating custom patterns. Total: {len(self.custom_patterns)}")

    def initialize_entity_ruler(self) -> None:
        """Initializes the Entity Ruler with custom patterns and adds it to the pipeline."""
        if not self.custom_patterns:
             logging.warning("No custom patterns defined for Entity Ruler.")
             return

        # Check if 'entity_ruler' already exists
        if 'entity_ruler' in self.nlp.pipe_names:
            logging.warning("Entity Ruler already exists in pipeline. Removing and re-adding.")
            self.nlp.remove_pipe('entity_ruler')
            
        # Create the EntityRuler
        # config={"overwrite_ents": True} ensures our patterns take precedence over spaCy's NER
        ruler = self.nlp.add_pipe("entity_ruler", config={"overwrite_ents": True}, before="ner") 
        
        try:
             # Add patterns to the ruler
             ruler.add_patterns(self.custom_patterns)
             logging.info(f"Entity Ruler added to pipeline with {len(self.custom_patterns)} patterns.")
        except Exception as e:
             logging.error(f"Error adding patterns to Entity Ruler: {e}", exc_info=True)

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
        """Parse the raw command string into a ParsedIntent."""
        command = command.strip().lower()
        if not command:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command)

        doc = self.nlp(command)
        logging.debug(f"Tokens: {[token.text for token in doc]}")
        logging.debug(f"Entities: {[(ent.text, ent.label_) for ent in doc.ents]}")

        # --- Prioritize DIRECTION entity for MOVE intent --- 
        parsed_direction: Optional[str] = None
        for ent in doc.ents:
            if ent.label_ == "DIRECTION":
                # Normalize multi-word/hyphenated directions (e.g., "north west" -> "northwest", "north-west" -> "northwest")
                direction_text = ent.text
                normalized_direction = direction_text.replace(' ', '').replace('-', '') # Remove spaces AND hyphens
                logging.debug(f"Normalized direction entity: '{direction_text}' -> '{normalized_direction}'")
                
                # !!! ADDED DEBUG LOGGING HERE !!!
                logging.info(f"PARSER: Found DIRECTION entity '{direction_text}', normalized to '{normalized_direction}', returning MOVE intent.")

                # Found a direction, assume MOVE intent and return immediately
                return ParsedIntent(
                    intent=CommandIntent.MOVE,
                    direction=normalized_direction, # Use the fully normalized direction
                    original_input=command
                )

        # --- If no DIRECTION entity, proceed with verb/entity analysis --- 
        # (Keep existing logic for verb identification, entity extraction, intent scoring, etc.)
        
        # Extract potential verbs and nouns/entities
        verbs = [token for token in doc if token.pos_ == "VERB"]
        entities = doc.ents # Get named entities recognized by EntityRuler or NER
        nouns = [token for token in doc if token.pos_ in ["NOUN", "PROPN"]] # Simple noun check as fallback
        
        logging.debug(f"Verbs: {[v.text for v in verbs]}")
        logging.debug(f"Entities: {[(ent.text, ent.label_) for ent in entities]}")
        logging.debug(f"Nouns: {[n.text for n in nouns]}")

        # Determine Intent based on verbs, entities, and context
        possible_intents: Dict[CommandIntent, float] = {}
        
        # --- Simple Verb Matching --- (Could be improved with lemmatization)
        matched_verb_intents: Set[CommandIntent] = set()
        for token in doc:
            for intent, data in self.VERB_PATTERNS.items():
                if token.lemma_ in data.get("verbs", []): # Use lemma for broader matching
                    matched_verb_intents.add(intent)
                    # Initial score based on verb match
                    possible_intents[intent] = possible_intents.get(intent, 0) + 1.0 * self.intent_priorities.get(intent, 1)
        logging.debug(f"Intents matched by verbs: {matched_verb_intents}")

        # --- Entity Analysis --- 
        primary_target: Optional[str] = None
        target_object_id: Optional[str] = None
        target_type: Optional[str] = None # e.g., GAME_OBJECT, LOCATION, NPC
        
        # Prioritize GAME_OBJECT entities found by EntityRuler
        game_object_ents = [ent for ent in entities if ent.label_ == "GAME_OBJECT"]
        if game_object_ents:
             # Take the first recognized game object as the primary target
             primary_target = game_object_ents[0].text
             target_object_id = game_object_ents[0].ent_id_ # Get the ID stored in the pattern
             target_type = "GAME_OBJECT"
             logging.debug(f"Primary target identified as GAME_OBJECT: '{primary_target}' (ID: {target_object_id})")
        else:
            # Fallback: Look for simple nouns if no specific GAME_OBJECT entity found
            # Try to reconstruct a target from nouns following the verb
            if verbs:
                verb_index = verbs[0].i
                potential_target_tokens = [token for token in doc if token.i > verb_index and token.pos_ in ["NOUN", "PROPN", "ADJ", "DET"]]
                if potential_target_tokens:
                     primary_target = " ".join([t.text for t in potential_target_tokens])
                     logging.debug(f"Primary target guessed from nouns after verb: '{primary_target}'")
            elif nouns: # If no verb, just take first noun chunk?
                 primary_target = nouns[0].text # Simplistic fallback
                 logging.debug(f"Primary target guessed from first noun: '{primary_target}'")

        # --- Intent Scoring Refinement (Example) --- 
        # Boost score if target object properties match intent context (e.g., wear + clothing)
        if target_object_id:
            obj_data = self.game_state.objects_data.get(target_object_id)
            if obj_data:
                 obj_category = obj_data.get('category')
                 # Example boosts
                 if CommandIntent.EQUIP in possible_intents and obj_category in ['clothing', 'equipment', 'weapon']:
                      possible_intents[CommandIntent.EQUIP] = possible_intents.get(CommandIntent.EQUIP, 0) + 50 # Big boost
                 if CommandIntent.TAKE in possible_intents and obj_data.get('properties', {}).get('is_takeable'):
                      possible_intents[CommandIntent.TAKE] = possible_intents.get(CommandIntent.TAKE, 0) + 20
                 # Add more boosting rules based on categories/properties

        # --- Determine Final Intent --- 
        if not possible_intents:
             logging.warning("No possible intents identified.")
             final_intent = CommandIntent.UNKNOWN
        else:
             # Sort by score (highest first)
             sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
             logging.debug(f"Intent scores: {sorted_intents}")
             final_intent = sorted_intents[0][0]

        # --- Extract Action Verb --- 
        action_verb = verbs[0].lemma_ if verbs else None # Use lemma of first verb

        # Handle specific cases / overrides
        if final_intent == CommandIntent.MOVE and not parsed_direction: # Move verb but no direction entity
             # Maybe try to extract direction from target? e.g., "go door" -> find door exit dir?
             logging.warning("MOVE intent determined but no DIRECTION entity found.")
             final_intent = CommandIntent.UNKNOWN # Fallback to unknown if direction unclear

        # Correct Drop/Put interpretation
        if action_verb == "put" and primary_target and "down" not in command: # Avoid conflict with "put X in Y"
            # If the intent wasn't already DROP, check if it makes sense
            if final_intent != CommandIntent.DROP:
                # If context suggests putting something *somewhere else* (e.g., container), it's not DROP
                # Simple check for now: if a location/container is mentioned, it's not DROP
                has_location_context = any(ent.label_ in ["LOCATION", "CONTAINER"] for ent in entities) 
                if not has_location_context: 
                    final_intent = CommandIntent.DROP 
                    logging.debug("Interpreting 'put' as DROP based on context.")
        
        # Build the final ParsedIntent
        return ParsedIntent(
            intent=final_intent,
            action=action_verb, 
            target=primary_target,
            target_object_id=target_object_id,
            # direction=parsed_direction, # This is now handled by the priority check above
            original_input=command
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
    