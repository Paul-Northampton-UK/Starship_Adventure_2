import re

import spacy
from fuzzywuzzy import fuzz
from loguru import logger

from .command_defs import CommandIntent, ParsedIntent
from .game_state import GameState

# Import the constants from the new module
from .nlp.constants import INTENT_PRIORITIES, VERB_PATTERNS

# Import the pattern generation function
from .nlp.patterns import generate_patterns

QUESTION_PREFIXES = ("who", "what", "where", "when", "why", "how")
TARGET_TRIM_WORDS = {"the", "a", "an", "my", "at", "on", "in", "into", "onto", "under", "over", "with", "from", "to", "for", "toward", "towards"}
ZERO_TARGET_INTENTS = {
    CommandIntent.INVENTORY,
    CommandIntent.QUIT,
    CommandIntent.SAVE,
    CommandIntent.LOAD,
    CommandIntent.HELP,
    CommandIntent.TIME,
}
INVENTORY_REQUEST_PHRASES = {
    "i",
    "inv",
    "inventory",
    "check inventory",
    "show inventory",
    "open inventory",
    "what am i carrying",
    "what i am carrying",
    "what do i have",
    "what am i holding",
    "show what i am carrying",
    "check what i am carrying",
}
INVENTORY_PREFIXES = ("check", "show", "what")
INVENTORY_PRIORITY_KEYWORDS = ("inventory", "carrying", "items", "gear", "equipment")
LOOK_PRIORITY_KEYWORDS = ("look", "examine", "inspect", "view", "observe")
LOOK_VERBS = {"look", "examine", "inspect", "check", "scan"}
TAKE_KEYWORDS = {"take", "grab", "collect"}
MOVE_VERBS = {"move", "go", "walk", "run", "head", "float", "drift"}
COMBAT_VERBS = {"attack", "hit", "strike", "shoot", "punch", "kick", "fight", "kill", "stab", "blast", "engage"}
MANIPULATE_PRIORITY_VERBS = {
    "push",
    "pull",
    "press",
    "flip",
    "switch",
    "toggle",
    "activate",
    "deactivate",
    "operate",
    "manipulate",
    "engage",
    "disengage",
}
MANIPULATE_VERBS = set(MANIPULATE_PRIORITY_VERBS) | {"open", "close", "turn", "lock"}
EQUIP_PRIORITY_VERBS = {"equip", "wear", "put", "don", "ready"}
SEARCH_VERBS = {"search", "find", "locate", "seek", "probe", "detect", "discover", "track"}
COMMUNICATE_VERBS = {"talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast", "ask", "tell"}
SOCIAL_VERBS = {"give", "show", "trade", "follow", "greet", "salute", "wave", "gesture", "signal"}
ENVIRONMENT_VERBS = {"dig", "cut", "burn", "pour", "light", "extinguish", "fill", "break", "smash", "destroy", "shatter"}
GATHER_INFO_VERBS = {"read", "listen", "smell", "touch", "taste", "study", "analyze", "monitor", "review"}
EQUIP_VERBS = {"equip", "wear", "put", "don", "ready"}
TIME_VERBS = {"wait", "rest", "sleep"}
INVENTORY_KEYWORDS = {"inventory", "inv", "items", "item", "backpack", "bag"}
HELP_KEYWORDS = {"help", "commands", "tutorial", "manual", "guide", "assist", "info", "information"}
QUIT_KEYWORDS = {"quit", "exit", "bye", "logout", "disconnect"}
COMPLEX_VERBS = {"combine", "craft", "build", "create", "construct", "forge", "brew", "synthesize", "fabricate", "assemble"}
GATHER_INFO_HINT_WORDS = {"data", "information", "signal", "display", "screen", "terminal", "console", "hologram", "sensor", "scanner", "log", "logs"}
MANIPULATION_OBJECT_HINTS = {
    "button",
    "lever",
    "switch",
    "terminal",
    "console",
    "control panel",
    "panel",
    "keypad",
    "machine",
}
COMBAT_OBJECT_HINTS = {"robot", "enemy", "creature", "guard", "alien", "intruder"}
INVENTORY_ANYWHERE_KEYWORDS = {"inventory", "inv", "backpack", "bag"}
INVENTORY_KEYWORD_PHRASES = {
    "what am i carrying",
    "what i am carrying",
    "what i'm carrying",
    "what am i holding",
    "what i am holding",
    "my items",
    "my inventory",
    "show me my items",
    "show me what i'm carrying",
    "show me what i am carrying",
    "open my backpack",
    "open backpack",
    "open my bag",
    "check inventory",
    "show inventory",
    "open inventory",
    "display inventory",
    "show me my inventory",
    "show me items",
    "tell me what i'm carrying",
}
INVENTORY_ITEM_HELPERS = {"items", "item"}
KNOWN_OBJECT_WORDS = {
    "console", "panel", "terminal", "display", "hologram", "device", "equipment", "machinery", "machine", "robot",
    "door", "key", "button", "lever", "card", "torch", "computer", "screen", "tool", "sword", "shield",
    "potion", "book", "scroll", "map", "coin", "gem", "crystal", "backpack", "chest", "box", "window", "gate",
    "rope", "ladder", "guard", "merchant", "captain", "soldier", "villager", "alien", "android", "crew", "officer",
    "drone", "hostile", "threat", "enemy", "creature", "phaser", "blaster", "laser", "pulse", "beam", "torpedo",
    "missile", "room", "area", "cargo", "bay", "engineering", "bridge", "airlock", "medbay", "quarters", "data",
    "information", "lifeform", "artifact", "hatch", "valve", "circuit", "system", "wall", "gap",
    "fence", "pit", "tunnel", "vent", "pipe", "space", "credits", "power", "energy", "shield", "sensor",
    "scanner", "suit", "armor", "generator", "battery", "jetpack", "component", "module", "technology",
    "ai", "logs", "log", "ladder"
}
KNOWN_OBJECT_PHRASES = {
    ("data", "pad"),
    ("power", "pack"),
    ("control", "terminal"),
    ("control", "panel"),
    ("control", "console"),
    ("access", "card"),
    ("engine", "room"),
    ("cargo", "bay"),
    ("med", "bay"),
    ("power", "core"),
}
SINGLE_LETTER_INTENTS: dict[str, CommandIntent] = {
    "q": CommandIntent.QUIT,
    "i": CommandIntent.INVENTORY,
    "h": CommandIntent.HELP,
    "?": CommandIntent.HELP,
}
DIRECTION_KEYWORDS: dict[str, str] = {
    "n": "north",
    "s": "south",
    "e": "east",
    "w": "west",
    "u": "up",
    "d": "down",
    "north": "north",
    "south": "south",
    "east": "east",
    "west": "west",
    "northward": "north",
    "northwards": "north",
    "northern": "north",
    "southward": "south",
    "southwards": "south",
    "southern": "south",
    "eastward": "east",
    "eastwards": "east",
    "eastern": "east",
    "westward": "west",
    "westwards": "west",
    "western": "west",
    "up": "up",
    "upward": "up",
    "upwards": "up",
    "down": "down",
    "downward": "down",
    "downwards": "down",
    "forward": "forward",
    "forwards": "forward",
    "ahead": "forward",
    "back": "backward",
    "backward": "backward",
    "backwards": "backward",
}
CHECK_LOGS_PREFIXES = (
    "check log",
    "check logs",
    "check the log",
    "check the logs",
)


def _build_keyword_intents() -> dict[str, CommandIntent]:
    mapping: dict[str, CommandIntent] = {}

    intent_word_map: list[tuple[CommandIntent, set[str]]] = [
        (CommandIntent.LOOK, LOOK_VERBS | {"l"}),
        (CommandIntent.TAKE, TAKE_KEYWORDS),
        (CommandIntent.MOVE, MOVE_VERBS | {"move"}),
        (CommandIntent.USE, {"use", "unlock"}),
        (CommandIntent.SAVE, {"save"}),
        (CommandIntent.LOAD, {"load"}),
        (CommandIntent.HELP, HELP_KEYWORDS),
        (CommandIntent.QUIT, QUIT_KEYWORDS),
        (CommandIntent.EQUIP, EQUIP_VERBS),
        (CommandIntent.TIME, TIME_VERBS),
        (CommandIntent.SEARCH, SEARCH_VERBS),
        (CommandIntent.GATHER_INFO, GATHER_INFO_VERBS),
        (CommandIntent.MANIPULATE, MANIPULATE_VERBS),
        (CommandIntent.CLIMB, {"climb", "jump", "crawl", "swim", "hover", "fly", "launch", "land"}),
        (CommandIntent.COMMUNICATE, COMMUNICATE_VERBS),
        (CommandIntent.SOCIAL, SOCIAL_VERBS),
        (CommandIntent.ENVIRONMENT, ENVIRONMENT_VERBS),
        (CommandIntent.COMBAT, COMBAT_VERBS),
        (CommandIntent.INVENTORY, INVENTORY_KEYWORDS),
        (CommandIntent.COMPLEX, COMPLEX_VERBS),
    ]

    for intent, words in intent_word_map:
        for word in words:
            mapping[word] = intent

    return mapping


KEYWORD_VERB_INTENTS = _build_keyword_intents()


class NLPCommandParser:
    """Handles parsing and processing of player commands using NLP."""
    
    # --- Constants moved to engine/nlp/constants.py --- 
    
    def __init__(self, game_state: GameState):
        """Initialize the NLP command parser."""
        self.game_state = game_state
        self.nlp = spacy.load("en_core_web_sm")
        
        # Create a list of all valid words for fuzzy matching
        # NOTE: This uses VERB_PATTERNS which is now imported
        self.valid_words = set()
        for pattern_intent, pattern_data in VERB_PATTERNS.items(): # Use imported constant
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
        
        # --- intent_priorities moved to engine/nlp/constants.py --- 
        
        # --- context_words moved to engine/nlp/constants.py --- 
        
        # Add game-specific vocabulary (e.g., tokenizer exceptions)
        self.add_game_vocabulary()
        
        # Generate patterns using the external function
        self.custom_patterns = generate_patterns(self.game_state)
        
        # Initialize the Entity Ruler with the generated patterns
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

    def initialize_entity_ruler(self) -> None:
        """Initializes the Entity Ruler with custom patterns and adds it to the pipeline."""
        if not self.custom_patterns:
             logger.warning("No custom patterns defined for Entity Ruler.")
             return

        # Check if 'entity_ruler' already exists
        if 'entity_ruler' in self.nlp.pipe_names:
            logger.warning("Entity Ruler already exists in pipeline. Removing and re-adding.")
            self.nlp.remove_pipe('entity_ruler')
            
        # Create the EntityRuler
        # config={"overwrite_ents": True} ensures our patterns take precedence over spaCy's NER
        ruler = self.nlp.add_pipe("entity_ruler", config={"overwrite_ents": True}, before="ner") 
        
        try:
             # Add patterns to the ruler
             ruler.add_patterns(self.custom_patterns)
             logger.info(f"Entity Ruler added to pipeline with {len(self.custom_patterns)} patterns.")
        except Exception as e:
             logger.error(f"Error adding patterns to Entity Ruler: {e}", exc_info=True)

    def _find_closest_match(self, word: str, threshold: int = 80) -> str | None:
        """Find the closest match for a word from the valid vocabulary using fuzzy matching."""
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
    
    def process_command(self, command: str) -> ParsedIntent:
        """External entry point that delegates to parse_command for now."""
        return self.parse_command(command)

    def parse_command(self, command: str) -> ParsedIntent:
        """Parse the raw command string into a ParsedIntent."""
        normalized = (command or "").strip().lower()
        normalized = normalized.replace("i\u2019m", "i am").replace("i'm", "i am")
        if not normalized:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command or "", confidence=0.0, target=None)
        command_original_case = command.strip()
        command_lower = normalized

        stripped = command_lower
        tokens_for_match = self._tokenize_for_matching(command_lower)
        direction_hint = self._detect_direction_from_tokens(tokens_for_match)
        contains_look_keyword = any(token in LOOK_VERBS for token in tokens_for_match)
        contains_manipulation_reference = self._contains_manipulation_reference(tokens_for_match)
        contains_equip_reference = self._contains_equip_reference(command_lower, tokens_for_match)
        contains_inventory_reference = self._contains_inventory_reference(command_lower, tokens_for_match)
        combat_reference = self._contains_combat_reference(tokens_for_match)

        first_word = stripped.split(" ", 1)[0] if stripped else ""
        first_word_lower = first_word.lower()

        # Directions
        if stripped in DIRECTION_KEYWORDS:
            direction = DIRECTION_KEYWORDS[stripped]
            return ParsedIntent(intent=CommandIntent.MOVE,
                                action="move",
                                direction=direction,
                                original_input=command_original_case,
                                confidence=1.0,
                                target="")

        if first_word_lower in DIRECTION_KEYWORDS:
            direction = DIRECTION_KEYWORDS[first_word_lower]
            remainder = stripped[len(first_word_lower):].strip()
            return ParsedIntent(intent=CommandIntent.MOVE,
                                action="move",
                                direction=direction,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=remainder)

        # Quit / Inventory
        if stripped in SINGLE_LETTER_INTENTS:
            intent = SINGLE_LETTER_INTENTS[stripped]
            action_lookup = {
                CommandIntent.QUIT: "quit",
                CommandIntent.INVENTORY: "inventory",
                CommandIntent.HELP: "help",
            }
            return ParsedIntent(intent=intent,
                                action=action_lookup.get(intent),
                                original_input=command_original_case,
                                confidence=1.0,
                                target="")

        if self._is_inventory_request(stripped) or (contains_inventory_reference and not contains_equip_reference):
            return self._build_inventory_intent(command_original_case)

        # Look
        if self._is_look_command(first_word_lower, stripped):
            return self._build_look_intent(command_original_case, command_lower)

        if any(stripped.startswith(prefix) for prefix in CHECK_LOGS_PREFIXES):
            target_phrase = self._extract_target_after_verb(command_lower) or "logs"
            return ParsedIntent(intent=CommandIntent.GATHER_INFO,
                                action="check",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase)

        keyword_verbs = KEYWORD_VERB_INTENTS

        if first_word_lower in MOVE_VERBS:
            move_target = self._extract_post_verb_phrase(command_lower)
            direction = direction_hint
            cleaned_target = move_target
            if direction and cleaned_target and cleaned_target.startswith(direction):
                cleaned_target = cleaned_target[len(direction):].strip()
            return ParsedIntent(intent=CommandIntent.MOVE,
                                action=first_word_lower,
                                direction=direction,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=cleaned_target or "")

        # Take
        if stripped.startswith("pick up"):
            target_phrase = self._extract_target_after_phrase(stripped, "pick up")
            return ParsedIntent(intent=CommandIntent.TAKE,
                                action="pick",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        if first_word_lower in TAKE_KEYWORDS:
            if contains_look_keyword:
                return self._build_look_intent(command_original_case, command_lower)
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.TAKE,
                                action=first_word_lower,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Combat
        if combat_reference:
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.COMBAT,
                                action=first_word_lower or "attack",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Manipulate
        if first_word_lower in MANIPULATE_VERBS or contains_manipulation_reference or self._tokens_have_manipulation_object(tokens_for_match):
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.MANIPULATE,
                                action=first_word_lower if first_word_lower in MANIPULATE_VERBS else "manipulate",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Use
        if first_word_lower == "use":
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.USE,
                                action="use",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Gather info
        if first_word_lower in GATHER_INFO_VERBS:
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.GATHER_INFO,
                                action=first_word_lower,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Equip
        if contains_equip_reference or self._is_equip_command(first_word_lower, stripped):
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.EQUIP,
                                action="equip",
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or None)

        # Time
        if first_word_lower in TIME_VERBS:
            return ParsedIntent(intent=CommandIntent.TIME,
                                action=first_word_lower,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=None)

        keyword_verbs = KEYWORD_VERB_INTENTS

        if first_word_lower in keyword_verbs:
            intent = keyword_verbs[first_word_lower]
            target_phrase = self._extract_target_after_verb(command_lower)
            if intent == CommandIntent.TAKE and contains_look_keyword:
                return self._build_look_intent(command_original_case, command_lower)
            if first_word_lower == "hold" and not target_phrase:
                intent = CommandIntent.TIME
            if first_word_lower == "scan" and any(hint in stripped for hint in GATHER_INFO_HINT_WORDS):
                intent = CommandIntent.GATHER_INFO
            if first_word_lower == "engage":
                if target_phrase and any(hint in target_phrase for hint in MANIPULATION_OBJECT_HINTS):
                    intent = CommandIntent.MANIPULATE
                else:
                    intent = CommandIntent.COMBAT
            if first_word_lower == "use" and (
                contains_manipulation_reference or self._target_matches_manipulation_hint(target_phrase)
            ):
                intent = CommandIntent.MANIPULATE
            target_value = "" if intent in ZERO_TARGET_INTENTS else (target_phrase or None)
            return ParsedIntent(intent=intent,
                                action=first_word_lower,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_value)

        for prefix in QUESTION_PREFIXES:
            if stripped == prefix or stripped.startswith(prefix + " "):
                remainder = stripped[len(prefix):].strip()
                return ParsedIntent(intent=CommandIntent.GATHER_INFO,
                                    action=prefix,
                                    original_input=command_original_case,
                                    confidence=1.0,
                                    target=remainder)

        # --- Process with NLP --- 
        doc = self.nlp(command_lower) # Use lowercased version for NLP
        logger.debug(f"Tokens: {[token.text for token in doc]}")
        logger.debug(f"Entities: {[(ent.text, ent.label_) for ent in doc.ents]}")

        verbs = [token for token in doc if token.pos_ == "VERB"]
        entities = doc.ents 
        nouns = [token for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        
        logger.debug(f"Verbs: {[v.text for v in verbs]}")
        logger.debug(f"Entities: {[(ent.text, ent.label_) for ent in entities]}")
        logger.debug(f"Nouns: {[n.text for n in nouns]}")

        # Determine Intent based on verbs, entities, and context
        possible_intents: dict[CommandIntent, float] = {}
        matched_verb_intents: set[CommandIntent] = set()
        for token in doc:
            # Handle cases like "inventory" where it might not be tagged as VERB
            # Check both lemma and lowercased text against verbs
            token_check_forms = {token.lemma_, token.text.lower()}
            for intent, data in VERB_PATTERNS.items():
                verb_list = data.get("verbs", [])
                if any(form in verb_list for form in token_check_forms):
                    matched_verb_intents.add(intent)
                    possible_intents[intent] = possible_intents.get(intent, 0) + 1.0 * INTENT_PRIORITIES.get(intent, 1)
        logger.debug(f"Intents matched by verbs/keywords: {matched_verb_intents}")
        self._apply_inventory_tiebreaker(stripped, possible_intents)
        self._apply_look_tiebreaker(stripped, possible_intents)

        # --- Entity Analysis --- 
        primary_target: str | None = None
        target_object_id: str | None = None
        target_type: str | None = None 
        
        game_object_ents = [ent for ent in entities if ent.label_ == "GAME_OBJECT"]
        if game_object_ents:
             primary_target = game_object_ents[0].text
             target_object_id = game_object_ents[0].ent_id_ 
             target_type = "GAME_OBJECT"
             logger.debug(f"Primary target identified as GAME_OBJECT: '{primary_target}' (ID: {target_object_id})")
        else:
            primary_target = None
            action_index = -1
            for token in doc:
                if token.pos_ == "VERB":
                    action_index = token.i
                    break
            if action_index != -1:
                collected: list[str] = []
                stop_words = {"from", "with", "to", "at", "in", "on", "into", "onto", "under", "over"}
                articles = {"the", "a", "an", "my"}
                collecting = False
                for token in doc[action_index + 1:]:
                    word_lower = token.text.lower()
                    if word_lower in articles:
                        continue
                    if word_lower in stop_words:
                        if collecting:
                            break
                        continue
                    if token.is_alpha:
                        collecting = True
                        collected.append(word_lower)
                if collected:
                    primary_target = " ".join(collected).strip()
                    logger.debug(f"Primary target set to '{primary_target}' based on words after verb.")

        if not primary_target:
            phrase_candidate = self._match_known_object_phrase(tokens_for_match)
            if phrase_candidate:
                primary_target = phrase_candidate
                logger.debug(f"Primary target inferred from known phrases: '{primary_target}'.")

        # --- Intent Scoring Refinement --- 
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
        final_intent = CommandIntent.UNKNOWN # Default to UNKNOWN
        if possible_intents: 
            sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
            logger.debug(f"Intent scores: {sorted_intents}")
            final_intent = sorted_intents[0][0]
        else:
            logger.warning("No possible intents identified after verb matching.")
            # No fallback to LOOK here, stays UNKNOWN

        if final_intent == CommandIntent.UNLOCK:
            final_intent = CommandIntent.USE

        # --- Extract Action Verb --- 
        action_verb = verbs[0].lemma_ if verbs else None 
        # If no verb tagged, but we matched a verb keyword, use that?
        if not action_verb and matched_verb_intents:
             # Find the token that caused the match (simplistic: first token in command that is in matched intent verbs)
             matched_intent_for_verb = final_intent # Assume highest scoring intent is the one we want verb from
             if matched_intent_for_verb in VERB_PATTERNS:
                 verbs_for_intent = VERB_PATTERNS[matched_intent_for_verb].get("verbs", [])
                 for token in doc:
                     if token.text.lower() in verbs_for_intent:
                         action_verb = token.text.lower()
                         logger.debug(f"Guessed action verb '{action_verb}' from matched intent keyword.")
                         break 

        # Handle specific cases / overrides
        # Correct Drop/Put interpretation
        if action_verb == "put" and primary_target and "down" not in command: # Avoid conflict with "put X in Y"
            # If the intent wasn't already DROP, check if it makes sense
            if final_intent != CommandIntent.DROP:
                # If context suggests putting something *somewhere else* (e.g., container), it's not DROP
                # Simple check for now: if a location/container is mentioned, it's not DROP
                has_location_context = any(ent.label_ in ["LOCATION", "CONTAINER"] for ent in entities) 
                if not has_location_context: 
                    final_intent = CommandIntent.DROP 
                    logger.debug("Interpreting 'put' as DROP based on context.")
        
        # Build the final ParsedIntent - Ensure primary_target is included
        manip_hint_present = contains_manipulation_reference or self._target_matches_manipulation_hint(primary_target)
        combat_hint_present = combat_reference or self._target_matches_combat_hint(primary_target)

        if contains_look_keyword and final_intent == CommandIntent.TAKE:
            final_intent = CommandIntent.LOOK
            action_verb = "look"
            look_target = self._extract_target_after_keywords(command_lower, LOOK_VERBS)
            if look_target:
                primary_target = look_target

        if combat_hint_present and final_intent != CommandIntent.COMBAT:
            final_intent = CommandIntent.COMBAT
            action_verb = action_verb or "attack"

        if contains_equip_reference and final_intent == CommandIntent.INVENTORY:
            final_intent = CommandIntent.EQUIP
            action_verb = action_verb or "equip"
        if manip_hint_present and final_intent == CommandIntent.USE:
            final_intent = CommandIntent.MANIPULATE

        confidence = 0.0 if final_intent == CommandIntent.UNKNOWN else 1.0
        final_target = primary_target.strip().lower() if isinstance(primary_target, str) and primary_target else None
        if final_intent in ZERO_TARGET_INTENTS:
            final_target = ""
        direction_value = direction_hint if final_intent == CommandIntent.MOVE else None

        return ParsedIntent(
            intent=final_intent,
            action=action_verb,
            target=final_target,
            target_object_id=target_object_id,
            original_input=command_original_case,  # Pass original case input
            confidence=confidence,
            direction=direction_value,
        )

    def _extract_target_after_verb(self, normalized_text: str) -> str:
        tokens = normalized_text.split()
        if len(tokens) <= 1:
            return ""
        remainder = tokens[1:]
        collected: list[str] = []
        collecting = False
        for token in remainder:
            cleaned = token.strip(",.!?")
            if not cleaned:
                continue
            lower = cleaned.lower()
            if not collecting and lower in TARGET_TRIM_WORDS:
                continue
            if collecting and lower in TARGET_TRIM_WORDS:
                break
            collecting = True
            collected.append(lower)
        if not collected:
            return ""
        phrase_candidate = self._match_known_object_phrase(collected)
        if phrase_candidate:
            return phrase_candidate
        return " ".join(collected).strip()

    def _extract_target_after_phrase(self, text: str, phrase: str) -> str:
        remainder = text[len(phrase):].strip()
        if " from " in remainder:
            remainder = remainder.split(" from ", 1)[0].strip()
        return remainder or ""

    def _extract_target_after_keywords(self, normalized_text: str, keywords: set[str]) -> str:
        lower = normalized_text or ""
        best_substring = None
        best_index = len(lower) + 1
        for keyword in keywords:
            match = re.search(rf"\b{re.escape(keyword)}\b", lower)
            if match and match.start() < best_index:
                best_index = match.start()
                best_substring = lower[match.start():]
        if not best_substring:
            return ""
        return self._extract_target_after_verb(best_substring)

    def _build_look_intent(
        self,
        original_input: str,
        normalized_text: str,
    ) -> ParsedIntent:
        target_phrase = self._extract_target_after_keywords(normalized_text, LOOK_VERBS)
        if normalized_text.strip() in {"look", "l"}:
            target_value: str | None = ""
        else:
            target_value = target_phrase or None

        return ParsedIntent(
            intent=CommandIntent.LOOK,
            action="look",
            target=target_value,
            original_input=original_input,
            confidence=1.0,
        )

    def _build_inventory_intent(self, original_input: str) -> ParsedIntent:
        return ParsedIntent(
            intent=CommandIntent.INVENTORY,
            action="inventory",
            target="",
            original_input=original_input,
            confidence=1.0,
        )

    @staticmethod
    def _extract_post_verb_phrase(normalized_text: str) -> str:
        parts = normalized_text.split(None, 1)
        if len(parts) < 2:
            return ""
        return parts[1].strip()

    @staticmethod
    def _tokenize_for_matching(text: str) -> list[str]:
        if not text:
            return []
        return re.findall(r"[a-z0-9']+", text.lower())

    @staticmethod
    def _detect_direction_from_tokens(tokens: list[str]) -> str | None:
        for token in tokens:
            if token in DIRECTION_KEYWORDS:
                return DIRECTION_KEYWORDS[token]
        return None

    @staticmethod
    def _match_known_object_phrase(tokens: list[str]) -> str | None:
        if not tokens:
            return None
        length = len(tokens)
        for span in (3, 2):
            for idx in range(length - span + 1):
                candidate = tuple(tokens[idx:idx + span])
                if candidate in KNOWN_OBJECT_PHRASES:
                    return " ".join(candidate)
        for token in tokens:
            if token in KNOWN_OBJECT_WORDS:
                return token
        return None

    @staticmethod
    def _is_look_command(first_word: str, stripped: str) -> bool:
        if stripped in {"l", "look"}:
            return True
        if first_word in LOOK_VERBS:
            return True
        return stripped.startswith("look at ")

    @staticmethod
    def _is_equip_command(first_word: str, stripped: str) -> bool:
        if first_word in EQUIP_VERBS:
            return True
        return stripped.startswith("put on ")

    @staticmethod
    def _contains_inventory_reference(normalized_text: str, tokens: list[str]) -> bool:
        if not normalized_text:
            return False
        text = normalized_text.lower()
        for phrase in INVENTORY_KEYWORD_PHRASES:
            if phrase in text:
                return True
        token_set = set(tokens)
        if token_set & INVENTORY_ANYWHERE_KEYWORDS:
            return True
        if token_set & INVENTORY_ITEM_HELPERS and token_set & {"my", "what", "show", "tell", "display", "check", "open"}:
            return True
        if "pack" in tokens:
            for idx, token in enumerate(tokens):
                if token != "pack":
                    continue
                prev = tokens[idx - 1] if idx else ""
                if prev in {"my", "the", "open", "check", "show"}:
                    return True
        return False

    @staticmethod
    def _contains_equip_reference(normalized_text: str, tokens: list[str]) -> bool:
        token_set = set(tokens)
        if token_set & EQUIP_PRIORITY_VERBS:
            return True
        if "put on" in (normalized_text or ""):
            return True
        return False

    @staticmethod
    def _contains_combat_reference(tokens: list[str]) -> bool:
        if not tokens:
            return False
        token_set = set(tokens)
        if token_set & COMBAT_VERBS:
            return True
        return bool(token_set & COMBAT_OBJECT_HINTS)

    @staticmethod
    def _contains_manipulation_reference(tokens: list[str]) -> bool:
        if not tokens:
            return False
        token_set = set(tokens)
        return bool(token_set & MANIPULATE_PRIORITY_VERBS)

    @staticmethod
    def _tokens_have_manipulation_object(tokens: list[str]) -> bool:
        if not tokens:
            return False
        return any(token in MANIPULATION_OBJECT_HINTS for token in tokens)

    @staticmethod
    def _target_matches_manipulation_hint(target: str | None) -> bool:
        if not target:
            return False
        value = target.lower()
        return any(hint in value for hint in MANIPULATION_OBJECT_HINTS)

    @staticmethod
    def _target_matches_combat_hint(target: str | None) -> bool:
        if not target:
            return False
        value = target.lower()
        return any(hint in value for hint in COMBAT_OBJECT_HINTS)

    @staticmethod
    def _is_inventory_request(normalized_text: str) -> bool:
        text = (normalized_text or "").strip()
        if not text:
            return False
        text = text.rstrip("?!.,").strip()
        if text in INVENTORY_REQUEST_PHRASES:
            return True
        if any(text.startswith(prefix) for prefix in INVENTORY_PREFIXES) and "carrying" in text:
            return True
        return False

    @staticmethod
    def _apply_inventory_tiebreaker(normalized_text: str, possible_intents: dict[CommandIntent, float]) -> None:
        if CommandIntent.INVENTORY not in possible_intents or CommandIntent.LOOK not in possible_intents:
            return
        text = normalized_text or ""
        if any(keyword in text for keyword in INVENTORY_PRIORITY_KEYWORDS):
            possible_intents[CommandIntent.INVENTORY] = max(
                possible_intents.get(CommandIntent.INVENTORY, 0.0),
                possible_intents.get(CommandIntent.LOOK, 0.0) + 0.1,
            )

    @staticmethod
    def _apply_look_tiebreaker(normalized_text: str, possible_intents: dict[CommandIntent, float]) -> None:
        if CommandIntent.LOOK not in possible_intents or len(possible_intents) <= 1:
            return
        text = normalized_text or ""
        if not any(keyword in text for keyword in LOOK_PRIORITY_KEYWORDS):
            return
        best_other = max(score for intent, score in possible_intents.items() if intent != CommandIntent.LOOK)
        possible_intents[CommandIntent.LOOK] = max(
            possible_intents.get(CommandIntent.LOOK, 0.0),
            best_other + 0.1,
        )

    # --- Unused methods removed --- 
    # _determine_intent 
    # _calculate_confidence 
    # process_command 
    # (and any related _process_... methods if they existed) 

# --- End of NLPCommandParser class --- 
