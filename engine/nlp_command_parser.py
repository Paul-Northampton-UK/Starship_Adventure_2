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
TARGET_TRIM_WORDS = {"the", "a", "an", "my", "at", "on", "in", "into", "onto", "under", "over", "with", "from", "to"}
ZERO_TARGET_INTENTS = {
    CommandIntent.MOVE,
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

        if self._is_inventory_request(stripped):
            return ParsedIntent(intent=CommandIntent.INVENTORY,
                                original_input=command_original_case,
                                confidence=1.0,
                                target="")

        if stripped == "q":
            return ParsedIntent(intent=CommandIntent.QUIT,
                                original_input=command_original_case,
                                confidence=1.0,
                                target="")

        if stripped in {"l", "look"}:
            target_phrase = "" if stripped == "l" else self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=CommandIntent.LOOK,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase)

        direction_map = {
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
            "up": "up",
            "down": "down",
        }
        if stripped in direction_map:
            direction = direction_map[stripped]
            return ParsedIntent(intent=CommandIntent.MOVE,
                                direction=direction,
                                original_input=command_original_case,
                                confidence=1.0,
                                target="")

        first_word = command_original_case.strip().split(" ", 1)[0].lower() if command_original_case else ""

        keyword_verbs = {
            "look": CommandIntent.LOOK,
            "use": CommandIntent.USE,
            "save": CommandIntent.SAVE,
            "load": CommandIntent.LOAD,
            "help": CommandIntent.HELP,
            "quit": CommandIntent.QUIT,
            "exit": CommandIntent.QUIT,
            "equip": CommandIntent.EQUIP,
            "wear": CommandIntent.EQUIP,
            "wait": CommandIntent.TIME,
            "rest": CommandIntent.TIME,
            "sleep": CommandIntent.TIME,
            "time": CommandIntent.TIME,
            "search": CommandIntent.SEARCH,
            "scan": CommandIntent.SEARCH,
            "find": CommandIntent.SEARCH,
            "open": CommandIntent.MANIPULATE,
            "close": CommandIntent.MANIPULATE,
            "push": CommandIntent.MANIPULATE,
            "pull": CommandIntent.MANIPULATE,
            "press": CommandIntent.MANIPULATE,
            "turn": CommandIntent.MANIPULATE,
            "activate": CommandIntent.MANIPULATE,
            "deactivate": CommandIntent.MANIPULATE,
            "lock": CommandIntent.MANIPULATE,
            "unlock": CommandIntent.MANIPULATE,
            "climb": CommandIntent.CLIMB,
            "jump": CommandIntent.CLIMB,
            "ascend": CommandIntent.CLIMB,
            "descend": CommandIntent.CLIMB,
            "talk": CommandIntent.SOCIAL,
            "speak": CommandIntent.SOCIAL,
            "greet": CommandIntent.SOCIAL,
            "ask": CommandIntent.SOCIAL,
            "hail": CommandIntent.COMMUNICATE,
            "call": CommandIntent.COMMUNICATE,
            "radio": CommandIntent.COMMUNICATE,
            "transmit": CommandIntent.COMMUNICATE,
            "attack": CommandIntent.COMBAT,
            "shoot": CommandIntent.COMBAT,
            "hit": CommandIntent.COMBAT,
        }

        if first_word in {"take", "grab"}:
            intent = CommandIntent.TAKE_FROM if self._has_take_from_pattern(command_lower) else CommandIntent.TAKE
            target_phrase = self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=intent,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_phrase or "")

        if first_word in keyword_verbs:
            intent = keyword_verbs[first_word]
            target_phrase = self._extract_target_after_verb(command_lower)
            target_value = "" if intent in ZERO_TARGET_INTENTS else target_phrase
            return ParsedIntent(intent=intent,
                                original_input=command_original_case,
                                confidence=1.0,
                                target=target_value)

        for prefix in QUESTION_PREFIXES:
            if stripped == prefix or stripped.startswith(prefix + " "):
                remainder = stripped[len(prefix):].strip()
                return ParsedIntent(intent=CommandIntent.GATHER_INFO,
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
                for token in doc[action_index + 1:]:
                    word_lower = token.text.lower()
                    if word_lower in stop_words:
                        break
                    if word_lower in articles:
                        continue
                    if token.is_alpha:
                        collected.append(word_lower)
                if collected:
                    primary_target = " ".join(collected).strip()
                    logger.debug(f"Primary target set to '{primary_target}' based on words after verb.")
            if not primary_target:
                primary_target = ""
                logger.debug("Primary target defaulted to empty string.")

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
        if final_intent == CommandIntent.TAKE_FROM and not self._has_take_from_pattern(command_original_case):
            final_intent = CommandIntent.TAKE

        confidence = 0.0 if final_intent == CommandIntent.UNKNOWN else 1.0
        final_target = (primary_target or "").strip().lower()
        if final_intent in ZERO_TARGET_INTENTS:
            final_target = ""

        return ParsedIntent(
            intent=final_intent,
            action=action_verb,
            target=final_target,
            target_object_id=target_object_id,
            original_input=command_original_case,  # Pass original case input
            confidence=confidence,
        )

    def _extract_target_after_verb(self, normalized_text: str) -> str:
        tokens = normalized_text.split()
        if len(tokens) <= 1:
            return ""
        remainder = tokens[1:]
        idx = 0
        while idx < len(remainder) and remainder[idx] in TARGET_TRIM_WORDS:
            idx += 1
        trimmed = remainder[idx:]
        collected: list[str] = []
        for token in trimmed:
            if token in TARGET_TRIM_WORDS:
                break
            collected.append(token)
        return " ".join(collected).strip()

    @staticmethod
    def _has_take_from_pattern(text: str) -> bool:
        normalized = (text or "").strip().lower()
        if not (normalized.startswith("take ") or normalized.startswith("grab ")):
            return False
        parts = normalized.split(None, 1)
        if len(parts) < 2:
            return False
        remainder = parts[1]
        if " from " not in remainder:
            return False
        before, after = remainder.split(" from ", 1)
        return bool(before.strip()) and bool(after.strip())

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
