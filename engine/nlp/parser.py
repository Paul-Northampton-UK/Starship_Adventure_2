# engine/nlp/parser.py
from dataclasses import dataclass, field
from typing import Any

import spacy
from fuzzywuzzy import fuzz
from loguru import logger

# Adjust imports to be relative to engine/ folder
from ..command_defs import CommandIntent, ParsedIntent
from ..game_state import GameState  # GameState needed for object data access

# Import from the new nlp sub-package
from .constants import INTENT_PRIORITIES, VERB_PATTERNS
from .constants import VERB_PATTERNS as _VP
from .patterns import generate_patterns

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

# --- Helper Dataclasses ---
@dataclass
class NlpProcessingResult:
    """Holds the results of spaCy processing."""
    doc: spacy.tokens.Doc
    action_verb_token: spacy.tokens.Token | None = None
    entities: dict[str, spacy.tokens.Span] = field(default_factory=dict)
    game_object_ents: dict[str, spacy.tokens.Span] = field(default_factory=dict)

@dataclass
class StructureParseResult:
    """Holds the results of parsing structured commands like PUT/TAKE_FROM."""
    success: bool = False
    intent: CommandIntent | None = None
    primary_target: str | None = None
    target_object_id: str | None = None
    secondary_target: str | None = None
    secondary_target_id: str | None = None
    preposition: str | None = None

@dataclass
class FallbackTargetResult:
    """Holds the results of fallback target extraction."""
    primary_target: str | None = None
    target_object_id: str | None = None

@dataclass # New dataclass to hold initial intent finding results
class InitialIntentResult:
    possible_intents: dict[CommandIntent, float] = field(default_factory=dict)
    matched_keyword_token: spacy.tokens.Token | None = None

# --- Main Parser Class ---
class NLPCommandParser:
    """Handles parsing and processing of player commands using NLP."""

    def __init__(self, game_state: GameState):
        """Initialize the NLP command parser."""
        self.game_state = game_state
        self.nlp = self._load_spacy_model()
        self.valid_words = self._build_valid_words_set()
        self.add_game_vocabulary() # Placeholder for tokenizer exceptions
        self.custom_patterns = generate_patterns(self.game_state)
        self.initialize_entity_ruler()

    def _load_spacy_model(self) -> spacy.language.Language:
        """Loads or downloads the spaCy model."""
        try:
            nlp = spacy.load("en_core_web_sm")
            logger.info("spaCy model 'en_core_web_sm' loaded.")
            return nlp
        except OSError:
            logger.error("Could not load spaCy model 'en_core_web_sm'.")
            logger.info("Attempting to download model...")
            try:
                spacy.cli.download("en_core_web_sm")
                nlp = spacy.load("en_core_web_sm")
                logger.info("Successfully downloaded and loaded 'en_core_web_sm'.")
                return nlp
            except Exception as e:
                logger.critical(f"Failed to download or load spaCy model: {e}. NLP parser cannot function.")
                raise RuntimeError("Failed to initialize NLP model.") from e

    def _build_valid_words_set(self) -> set[str]:
        """Builds a set of valid words for potential fuzzy matching."""
        valid_words = set()
        for pattern_data in VERB_PATTERNS.values():
            valid_words.update(pattern_data.get("verbs", []))
            valid_words.update(pattern_data.get("context_words", []))
        # Add common game objects/NPCs - consider making dynamic or external
        valid_words.update([
            "key", "door", "button", "lever", "card", "torch", "computer", "terminal",
            "screen", "panel", "tool", "device", "backpack", "chest", "box",
            "window", "gate", "rope", "ladder", "room", "area", "cabinet", "note",
            # Add specific object names/synonyms dynamically if needed
        ])
        return valid_words

    def add_game_vocabulary(self) -> None:
        """Add game-specific vocabulary exceptions to the NLP pipeline's tokenizer."""
        # Example: if "datapad" should always be one token
        # special_case = [{"ORTH": "datapad"}]
        # self.nlp.tokenizer.add_special_case("datapad", special_case)
        pass

    def initialize_entity_ruler(self) -> None:
        """Initializes the Entity Ruler with custom patterns and adds it to the pipeline."""
        if not self.custom_patterns:
            logger.warning("No custom patterns generated for Entity Ruler.")
            return
        config = {"overwrite_ents": True}
        if "entity_ruler" not in self.nlp.pipe_names:
            self.nlp.add_pipe("entity_ruler", config=config, before="ner")
            logger.info("Added new Entity Ruler before 'ner'.")
        else:
            self.nlp.replace_pipe("entity_ruler", "entity_ruler", config=config)
            logger.warning("Replaced existing Entity Ruler.")
        try:
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.add_patterns(self.custom_patterns)
            logger.info(f"Entity Ruler updated with {len(self.custom_patterns)} patterns.")
        except Exception as e:
            logger.error(f"Error adding patterns to Entity Ruler: {e}", exc_info=True)

    # --- Main Parsing Method ---
    def parse_command(self, command: str) -> ParsedIntent:
        """Parse the raw command string into a ParsedIntent."""
        logger.debug(">>> PARSE_COMMAND START >>>")

        normalized = (command or "").strip().lower()
        normalized = normalized.replace("i\u2019m", "i am").replace("i'm", "i am")
        if not normalized:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command or "", target=None)
        command_original_case, command_lower = command.strip(), normalized

        if self._is_inventory_request(command_lower):
            return ParsedIntent(intent=CommandIntent.INVENTORY,
                                original_input=command_original_case,
                                target="")

        first_word = command_original_case.strip().split(" ", 1)[0].lower() if command_original_case else ""

        single_letter_intents = {
            "q": CommandIntent.QUIT,
            "l": CommandIntent.LOOK,
            "n": CommandIntent.MOVE,
            "s": CommandIntent.MOVE,
            "e": CommandIntent.MOVE,
            "w": CommandIntent.MOVE,
            "u": CommandIntent.MOVE,
            "d": CommandIntent.MOVE,
        }
        direction_shortcuts = {
            "n": "north",
            "s": "south",
            "e": "east",
            "w": "west",
            "u": "up",
            "d": "down",
        }
        stripped = command_lower.strip()
        if stripped in single_letter_intents:
            letter_intent = single_letter_intents[stripped]
            direction = None
            if letter_intent == CommandIntent.MOVE:
                direction = direction_shortcuts[stripped]
            return ParsedIntent(intent=letter_intent,
                                direction=direction,
                                original_input=command_original_case,
                                target="")

        direction_words = {
            "north": "north",
            "south": "south",
            "east": "east",
            "west": "west",
            "up": "up",
            "down": "down",
        }
        if stripped in direction_words:
            direction = direction_words[stripped]
            return ParsedIntent(intent=CommandIntent.MOVE,
                                direction=direction,
                                original_input=command_original_case,
                                target="")

        keyword_verbs = {
            "look": CommandIntent.LOOK,
            "use": CommandIntent.USE,
            "save": CommandIntent.SAVE,
            "load": CommandIntent.LOAD,
            "help": CommandIntent.HELP,
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
            return ParsedIntent(intent=intent, original_input=command_original_case, target=target_phrase)

        if first_word in keyword_verbs:
            intent = keyword_verbs[first_word]
            target_phrase = "" if intent in ZERO_TARGET_INTENTS else self._extract_target_after_verb(command_lower)
            return ParsedIntent(intent=intent, original_input=command_original_case, target=target_phrase)

        # Questions -> Gather Info
        for prefix in QUESTION_PREFIXES:
            if stripped == prefix or stripped.startswith(prefix + " "):
                remainder = stripped[len(prefix):].strip()
                return ParsedIntent(intent=CommandIntent.GATHER_INFO,
                                    original_input=command_original_case,
                                    target=remainder)

        # 2. Run spaCy NLP pipeline
        nlp_result = self._run_spacy(command_lower)

        # 3. Check for explicit DIRECTION entity (early exit for MOVE)
        direction_result = self._check_direction_entity(nlp_result.doc, command_original_case)
        if direction_result: return direction_result

        # 4. Identify potential intents based on verbs/keywords
        initial_intent_result = self._identify_initial_intents(nlp_result.doc)
        self._apply_inventory_tiebreaker(command_lower, initial_intent_result.possible_intents)
        self._apply_look_tiebreaker(command_lower, initial_intent_result.possible_intents)

        # 5. Attempt to parse structured commands (PUT/TAKE_FROM)
        verb_token_for_structure = nlp_result.action_verb_token or initial_intent_result.matched_keyword_token
        structure_result = self._parse_structured_command(
            nlp_result, verb_token_for_structure, initial_intent_result.possible_intents
        )

        # 6. If structure not found/applicable, use fallback target extraction
        fallback_target = FallbackTargetResult()
        if not structure_result.success:
            token_to_look_after = nlp_result.action_verb_token or initial_intent_result.matched_keyword_token
            fallback_target = self._extract_fallback_target(nlp_result, token_to_look_after)

        # Consolidate targets - Use structured if available, else fallback
        primary_target = structure_result.primary_target if structure_result.success else fallback_target.primary_target
        target_object_id = structure_result.target_object_id if structure_result.success else fallback_target.target_object_id
        secondary_target = structure_result.secondary_target if structure_result.success else None
        secondary_target_id = structure_result.secondary_target_id if structure_result.success else None
        preposition = structure_result.preposition if structure_result.success else None

        # 7. Determine final intent
        final_intent = self._resolve_final_intent(
            initial_intent_result.possible_intents,
            structure_result.intent,
            structure_result.success
        )

        # 8. Extract final action verb lemma
        action_token = nlp_result.action_verb_token or initial_intent_result.matched_keyword_token
        action_verb = action_token.lemma_ if action_token else self._guess_action_verb(nlp_result.doc, final_intent)

        # 9. Build and return the final ParsedIntent object
        return self._build_parsed_intent(
            final_intent, action_verb,
            primary_target, target_object_id,
            secondary_target, secondary_target_id,
            preposition, command_original_case
        )

    def process_command(self, command: str) -> ParsedIntent:
        """Public shim that currently delegates directly to parse_command."""
        return self.parse_command(command)

    # --- Helper Methods ---
    def _preprocess_command(self, command: str) -> tuple[str, str]:
        """Normalize casing and basic synonyms; keep key prepositions for structured parsing."""
        command_original_case = command.strip()
        text = command_original_case.lower()
        # Canonicalize common multi-word items
        replacements = {
            "key card": "keycard",
            "blue key card": "blue keycard",
            "phaser gun": "phaser",
            "back pack": "backpack",
            "data pad": "datapad",
            "foot locker": "footlocker",
        }
        for src, dst in replacements.items():
            text = text.replace(src, dst)
        # Remove trivial stopwords (not structural)
        STOPWORDS = {" the ", " a ", " an "}
        padded = f" {text} "
        for sw in STOPWORDS:
            padded = padded.replace(sw, " ")
        command_lower = padded.strip()
        logger.debug(f"Preprocessing: Original='{command_original_case}', Lower='{command_lower}'")
        return command_original_case, command_lower

    def _check_single_letter(self, command_lower: str, command_original_case: str) -> ParsedIntent | None:
        """Check for single-letter shortcut commands."""
        single_letter_intents = {
            "i": CommandIntent.INVENTORY, "l": CommandIntent.LOOK, "q": CommandIntent.QUIT,
            "n": CommandIntent.MOVE, "s": CommandIntent.MOVE, "e": CommandIntent.MOVE, "w": CommandIntent.MOVE,
            "u": CommandIntent.MOVE, "d": CommandIntent.MOVE,
            # Add other single letters like 'x' for examine if desired
        }
        if command_lower in single_letter_intents:
            intent = single_letter_intents[command_lower]
            logger.debug(f"Matched single-letter command '{command_lower}' to intent {intent}")
            direction = None
            target = ""
            if intent == CommandIntent.MOVE:
                direction = {'n':'north','s':'south','e':'east','w':'west','u':'up','d':'down'}.get(command_lower, command_lower)
                target = direction or ""
            return ParsedIntent(intent=intent,
                                direction=direction,
                                original_input=command_original_case,
                                target=target)
        return None

    def _run_spacy(self, command_lower: str) -> NlpProcessingResult:
        """Run the spaCy NLP pipeline and extract key components."""
        doc = self.nlp(command_lower)
        logger.debug("--- NLP Processing Start ---")
        token_details = [(token.text, token.pos_, token.lemma_, token.i) for token in doc]
        logger.debug(f"Tokens (Text, POS, Lemma, Index): {token_details}")
        entity_details = [(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents]
        logger.debug(f"Entities (Text, Label, ID): {entity_details}")
        logger.debug("--- NLP Processing End ---")

        # Identify action verb (first verb found)
        action_verb_token: spacy.tokens.Token | None = None
        for token in doc:
            if token.pos_ == "VERB":
                action_verb_token = token
                logger.debug(f"Action verb token identified (by POS): '{action_verb_token.text}' at index {action_verb_token.i}")
                break # Use the first verb

        entities = {ent.text: ent for ent in doc.ents}
        game_object_ents = {ent.text: ent for ent in doc.ents if ent.label_ == "GAME_OBJECT"}

        return NlpProcessingResult(
            doc=doc,
            action_verb_token=action_verb_token,
            entities=entities,
            game_object_ents=game_object_ents
        )

    def _check_direction_entity(self, doc: spacy.tokens.Doc, command_original_case: str) -> ParsedIntent | None:
        """Check for a DIRECTION entity for immediate MOVE intent."""
        for ent in doc.ents:
            if ent.label_ == "DIRECTION":
                direction_text = ent.text
                normalized_direction = ent.ent_id_ # Use normalized ID from pattern
                logger.info(f"PARSER: Found DIRECTION entity '{direction_text}', normalized ID '{normalized_direction}', returning MOVE intent.")
                canonical_direction = normalized_direction or direction_text.lower()
                return ParsedIntent(
                    intent=CommandIntent.MOVE,
                    direction=canonical_direction,
                    original_input=command_original_case,
                    target=""
                )
        return None

    def _identify_initial_intents(self, doc: spacy.tokens.Doc) -> InitialIntentResult:
        """Identify possible intents based on verbs/keywords, calculating initial scores and finding the trigger token."""
        possible_intents: dict[CommandIntent, float] = {}
        matched_keyword_token: spacy.tokens.Token | None = None

        # More direct mapping of specific verbs to intents
        verb_to_intent_map = {
            "take": CommandIntent.TAKE,
            "get": CommandIntent.TAKE, # Alias for TAKE
            "pick up": CommandIntent.TAKE, # Phrase for TAKE
            "grab": CommandIntent.TAKE,
            "collect": CommandIntent.TAKE,
            "acquire": CommandIntent.TAKE,
            "drop": CommandIntent.DROP,
            "leave": CommandIntent.DROP, # Alias for DROP
            "discard": CommandIntent.DROP,
            "use": CommandIntent.USE,
            "activate": CommandIntent.USE,
            "operate": CommandIntent.USE,
            "manipulate": CommandIntent.MANIPULATE, # Generic manipulation
            "interact": CommandIntent.MANIPULATE,
            "equip": CommandIntent.EQUIP,
            "wear": CommandIntent.EQUIP,
            "don": CommandIntent.EQUIP, # Archaic, but sometimes used
            "remove": CommandIntent.EQUIP, # Often implies 'take off' then hold
            "doff": CommandIntent.EQUIP,   # Archaic for remove
            "unequip": CommandIntent.EQUIP,
            "search": CommandIntent.SEARCH,
            "examine": CommandIntent.LOOK, # Examine is more like LOOK AT
            "inspect": CommandIntent.LOOK, # Inspect is more like LOOK AT
            "look": CommandIntent.LOOK,    # General LOOK or LOOK AT
            "check": CommandIntent.LOOK,   # Can be LOOK AT or a more specific CHECK action
            "put": CommandIntent.PUT,
            "place": CommandIntent.PUT,
            "store": CommandIntent.PUT,
            "insert": CommandIntent.PUT,
            "unlock": CommandIntent.UNLOCK,
            "lock": CommandIntent.LOCK,
            "open": CommandIntent.OPEN,
            "close": CommandIntent.CLOSE,
            "shut": CommandIntent.CLOSE, # Alias for close
            # QUIT, INVENTORY, HELP are often single words/letters, handled earlier or differently
        }

        # Find the first token that is a known verb/keyword from our map
        first_verb_keyword_token: spacy.tokens.Token | None = None
        for token in doc:
            # Check single token
            if token.lemma_.lower() in verb_to_intent_map:
                first_verb_keyword_token = token
                break
            # Check two-token phrases (like "pick up")
            if token.i + 1 < len(doc):
                phrase = doc[token.i : token.i + 2].text.lower()
                if phrase in verb_to_intent_map:
                    # For phrases, consider the first token of the phrase as the matched one
                    first_verb_keyword_token = token 
                    break
        
        if first_verb_keyword_token:
            matched_keyword_token = first_verb_keyword_token
            logger.debug(f"First matched keyword token: '{matched_keyword_token.text}' at index {matched_keyword_token.i}")
            
            # Determine the text to use for map lookup (single lemma or phrase text)
            lookup_key = matched_keyword_token.lemma_.lower()
            if matched_keyword_token.i + 1 < len(doc):
                phrase_key = doc[matched_keyword_token.i : matched_keyword_token.i + 2].text.lower()
                if phrase_key in verb_to_intent_map:
                    lookup_key = phrase_key # Use the phrase if it's a direct map key

            if lookup_key in verb_to_intent_map:
                intent = verb_to_intent_map[lookup_key]
                # Base score, higher for direct verb matches
                base_score = INTENT_PRIORITIES.get(intent, 50) 
                possible_intents[intent] = possible_intents.get(intent, 0) + base_score
                logger.debug(f"Verb/Keyword '{lookup_key}' added score {base_score} for intent {intent}")

                # Special handling for TAKE vs TAKE_FROM ambiguity based on "from"
                if intent == CommandIntent.TAKE:
                    # If "from" appears after "take", also add points to TAKE_FROM
                    for t in doc[matched_keyword_token.i:]: # Search from the verb onwards
                        if t.lemma_ == "from":
                            possible_intents[CommandIntent.TAKE_FROM] = possible_intents.get(CommandIntent.TAKE_FROM, 0) + INTENT_PRIORITIES.get(CommandIntent.TAKE_FROM, 87) # Higher base for TAKE_FROM
                            logger.debug(f"'from' found after '{lookup_key}', boosting TAKE_FROM.")
                            break
            
            # If the primary verb was 'look', but there's a target, it's likely LOOK_AT (handled by LOOK intent with a target)
            # If verb is "examine" or "inspect", it's also LOOK.

        # Fallback: Iterate through all tokens if no direct verb_to_intent_map match
        # This can catch keywords that aren't the first verb-like token
        if not possible_intents:
            for token in doc:
                lemma = token.lemma_.lower()
                if lemma in verb_to_intent_map and not matched_keyword_token: # Only if we haven't already matched one
                    matched_keyword_token = token # Take the first one encountered
                    logger.debug(f"Fallback: Matched keyword token: '{matched_keyword_token.text}' at index {matched_keyword_token.i}")
                    intent = verb_to_intent_map[lemma]
                    base_score = INTENT_PRIORITIES.get(intent, 40) # Lower score for fallback
                    possible_intents[intent] = possible_intents.get(intent, 0) + base_score
                    logger.debug(f"Fallback Keyword '{lemma}' added score {base_score} for intent {intent}")

        # Fuzzy verb autocorrect: if still no match, try correcting first token
        if not possible_intents:
            if len(doc) > 0:
                first_tok = doc[0].text
                # Gather candidate verbs from patterns and map to a likely intent
                cand_to_intent: dict[str, CommandIntent] = {}
                for intent, pdata in _VP.items():
                    if hasattr(intent, 'name'):
                        for v in pdata.get("verbs", []):
                            cand_to_intent[v] = intent if isinstance(intent, CommandIntent) else None
                best = None
                best_ratio = 0
                for cand, ci in cand_to_intent.items():
                    r = fuzz.ratio(first_tok, cand)
                    if r > best_ratio:
                        best_ratio = r
                        best = (cand, ci)
                if best and best_ratio >= 90 and best[1]:
                    # High confidence autocorrect
                    intent = best[1]
                    possible_intents[intent] = INTENT_PRIORITIES.get(intent, 50) + 5
                    matched_keyword_token = doc[0]
                    logger.debug(f"Fuzzy verb autocorrect: '{first_tok}' -> '{best[0]}' (ratio {best_ratio}), intent {intent}")


        # Further context word scoring (Original VERB_PATTERNS logic adapted)
        for intent, pattern_data in VERB_PATTERNS.items():
            score = 0
            # Check verbs (lemmas) from pattern_data
            for verb in pattern_data.get("verbs", []):
                if any(token.lemma_ == verb for token in doc):
                    score += pattern_data.get("verb_score", 20)
            # Check context words from pattern_data
            for context_word in pattern_data.get("context_words", []):
                if any(token.text == context_word for token in doc): # Check exact text for context
                    score += pattern_data.get("context_score", 10)
            if score > 0:
                possible_intents[intent] = possible_intents.get(intent, 0) + score
                logger.debug(f"Pattern-based scoring added {score} to {intent} (verbs: {pattern_data.get('verbs', [])}, context: {pattern_data.get('context_words', [])})")

        logger.debug(f"Intents initially matched by verbs/keywords: {list(possible_intents.keys())}")
        return InitialIntentResult(possible_intents=possible_intents, matched_keyword_token=matched_keyword_token)

    def _parse_structured_command(self, nlp_result: NlpProcessingResult, verb_token: spacy.tokens.Token | None, possible_intents: dict) -> StructureParseResult:
        """Tries to parse structured commands like 'PUT item IN container' or 'TAKE item FROM container',
           or 'LOCK/UNLOCK target WITH key'.
        """
        doc = nlp_result.doc
        
        # 1. Check for custom UNLOCK_WITH_KEY / LOCK_WITH_KEY entities first
        for ent in doc.ents:
            if ent.label_ in ["UNLOCK_WITH_KEY", "LOCK_WITH_KEY"]:
                logger.debug(f"Found structured entity: {ent.label_} ('{ent.text}')")
                # Extract target and key from the entity text (simple split for now)
                # Example: "unlock locker with key" -> target="locker", key_item="key"
                parts = ent.text.lower().split()
                action_verb_str = parts[0] # "unlock" or "lock"
                
                # Find preposition "with" or "using"
                prep_index = -1
                prep_word = None
                for i, word in enumerate(parts):
                    if word in ["with", "using"]:
                        prep_index = i
                        prep_word = word
                        break
                
                if prep_index != -1 and prep_index > 1 and prep_index < len(parts) -1: # e.g. unlock TARGET PREP KEY
                    target_str = " ".join(parts[1:prep_index])
                    key_item_str = " ".join(parts[prep_index+1:])

                    # Try to resolve to actual object IDs
                    target_obj_id = self._find_id_for_entity_text(target_str, nlp_result.game_object_ents, preferred_source='location')
                    key_obj_id = self._find_id_for_entity_text(key_item_str, nlp_result.game_object_ents, preferred_source='possession')
                    
                    intent_to_set = CommandIntent.UNLOCK if action_verb_str == "unlock" else CommandIntent.LOCK
                    logger.debug(f"{ent.label_} structure parsed from entity: T1='{target_str}', Key='{key_item_str}'")

                    # Boost the intent score significantly if structure is matched
                    if intent_to_set in possible_intents:
                        possible_intents[intent_to_set] += 1000 
                        logger.debug(f"Applied boost 1000 to {intent_to_set} due to successful structure parsing.")
                    else: # If not in possible intents, add it with high score
                        possible_intents[intent_to_set] = 1000
                        logger.debug(f"Added {intent_to_set} with score 1000 due to successful structure parsing.")

                    return StructureParseResult(
                        success=True, 
                        intent=intent_to_set,
                        primary_target=target_str, 
                        target_object_id=target_obj_id,
                        secondary_target=key_item_str, 
                        secondary_target_id=key_obj_id,
                        preposition=prep_word
                    )
                else:
                    logger.warning(f"Could not properly parse UNLOCK/LOCK_WITH_KEY entity: '{ent.text}'")

        # 1.b Generic 'unlock/lock X with Y' parse even without entities
        try:
            # find verb token for lock/unlock and a 'with/using' later
            vtok = None
            for t in doc:
                if t.lemma_ in ["unlock", "lock"]:
                    vtok = t
                    break
            if vtok:
                prep_idx = None
                for t in doc[vtok.i+1:]:
                    if t.lemma_ in ["with", "using"]:
                        prep_idx = t.i
                        break
                if prep_idx and prep_idx > vtok.i+1 and prep_idx < len(doc)-1:
                    target_str = doc[vtok.i+1:prep_idx].text.strip()
                    key_str = doc[prep_idx+1:].text.strip()
                    target_obj_id = self._find_id_for_entity_text(target_str, nlp_result.game_object_ents, preferred_source='location')
                    key_obj_id = self._find_id_for_entity_text(key_str, nlp_result.game_object_ents, preferred_source='possession')
                    intent_to_set = CommandIntent.UNLOCK if vtok.lemma_ == "unlock" else CommandIntent.LOCK
                    possible_intents[intent_to_set] = possible_intents.get(intent_to_set, 0) + 1000
                    return StructureParseResult(
                        success=True,
                        intent=intent_to_set,
                        primary_target=target_str,
                        target_object_id=target_obj_id,
                        secondary_target=key_str,
                        secondary_target_id=key_obj_id,
                        preposition="with"
                    )
        except Exception:
            pass

        # 2. Check for PUT/TAKE_FROM prepositional logic
        # This requires a verb like "put" or "take" and a preposition like "in", "on", "from"
        if not verb_token or verb_token.lemma_.lower() not in ["put", "place", "store", "insert", "take", "get", "pick", "grab"]:
            logger.debug("Skipping PUT/TAKE_FROM structured command check (verb missing or PUT/TAKE_FROM not likely).")
            return StructureParseResult(success=False)
        
        logger.debug("Attempting to parse structured command (verb obj1 prep obj2) using PREPOSITION logic.")
        
        preposition_token: spacy.tokens.Token | None = None
        # Define prepositions relevant to PUT and TAKE_FROM
        # For PUT: "in", "on", "into", "onto"
        # For TAKE: "from"
        put_preps = ["in", "on", "into", "onto"]
        take_preps = ["from"]
        relevant_preps = []

        verb_lemma = verb_token.lemma_.lower()
        current_intent_for_prep = None

        if verb_lemma in ["put", "place", "store", "insert"]:
            relevant_preps = put_preps
            current_intent_for_prep = CommandIntent.PUT
        elif verb_lemma in ["take", "get", "pick", "grab"]: # "take" can be TAKE or TAKE_FROM
            relevant_preps = take_preps
            # Check if TAKE_FROM is a likely intent from initial scoring
            if CommandIntent.TAKE_FROM in possible_intents and possible_intents[CommandIntent.TAKE_FROM] > possible_intents.get(CommandIntent.TAKE, 0):
                current_intent_for_prep = CommandIntent.TAKE_FROM
            else: # Default to TAKE if TAKE_FROM is not more likely or no "from"
                 current_intent_for_prep = CommandIntent.TAKE 
                 # if "from" is not present, this structure won't match for TAKE anyway.
        
        if not current_intent_for_prep:
            logger.debug(f"No clear PUT/TAKE_FROM intent for verb '{verb_lemma}'. Skipping preposition logic.")
            return StructureParseResult(success=False)

        # Find the preposition after the verb
        for token in doc[verb_token.i + 1:]:
            if token.lemma_ in relevant_preps:
                preposition_token = token
                logger.debug(f"Found preposition '{preposition_token.lemma_}' at index {preposition_token.i}")
                break
        
        if not preposition_token:
            logger.debug(f"{current_intent_for_prep} intent likely, but no relevant preposition found (PREPOSITION logic).")
            return StructureParseResult(success=False)

        # We have a verb and a preposition. Now extract primary and secondary targets.
        # Primary target: spans between verb and preposition.
        # Secondary target: spans after preposition to end of command.
        
        primary_target_span: spacy.tokens.Span | None = None
        if verb_token.i + 1 < preposition_token.i:
            primary_target_span = doc[verb_token.i + 1 : preposition_token.i]
        
        secondary_target_span: spacy.tokens.Span | None = None
        if preposition_token.i + 1 < len(doc):
            secondary_target_span = doc[preposition_token.i + 1 :]

        if not primary_target_span or not secondary_target_span:
            logger.warning(f"Structured command parse: Missing primary or secondary target span for verb '{verb_lemma}' and prep '{preposition_token.lemma_}'.")
            return StructureParseResult(success=False)

        primary_target_str = primary_target_span.text.strip()
        secondary_target_str = secondary_target_span.text.strip()

        logger.debug(f"Extracted from structure: Verb='{verb_lemma}', Primary='{primary_target_str}', Prep='{preposition_token.lemma_}', Secondary='{secondary_target_str}'")

        # Try to resolve to actual object IDs
        # For PUT: primary is the item, secondary is the container
        # For TAKE_FROM: primary is the item, secondary is the container
        primary_target_id = self._find_id_for_entity_text(primary_target_str, nlp_result.game_object_ents, preferred_source='possession_or_location')
        secondary_target_id = self._find_id_for_entity_text(secondary_target_str, nlp_result.game_object_ents, preferred_source='location_or_container')
        
        # Boost the intent score significantly if structure is matched
        if current_intent_for_prep in possible_intents:
            possible_intents[current_intent_for_prep] += 1000
            logger.debug(f"Applied boost 1000 to {current_intent_for_prep} due to successful structure parsing.")
        else: # If not in possible intents (e.g. only TAKE was found, but "from" implies TAKE_FROM)
            possible_intents[current_intent_for_prep] = 1000
            logger.debug(f"Added {current_intent_for_prep} with score 1000 due to successful structure parsing.")


        return StructureParseResult(
            success=True,
            intent=current_intent_for_prep,
            primary_target=primary_target_str,
            target_object_id=primary_target_id,
            secondary_target=secondary_target_str,
            secondary_target_id=secondary_target_id,
            preposition=preposition_token.lemma_
        )

    def _find_id_for_entity_text(self, text: str, candidate_entities: list[dict[str, Any]], preferred_source: str = 'location') -> str | None:
        """Helper to find the most likely object ID for a given text string from candidate entities or by broader search."""
        # This method needs to be more robust. For now, a simple search in location/inventory.
        # TODO: Enhance to consider candidate_entities more directly if provided.

        if preferred_source == 'location':
            # Pass current room and area IDs from game_state
            current_room_id, current_area_id = self.game_state.get_current_location()
            found_id = self.game_state.find_object_id_by_name_in_location(
                object_name=text, 
                room_id=current_room_id, 
                area_id=current_area_id,
                visible_only=True # Parser usually looks for visible things
            )
            if found_id: return found_id
            # Fallback to inventory if not found in location by preferred search
            found_id = self.game_state.find_item_id_held_or_worn(text) # This searches hands, worn, and inside worn containers
            if found_id: return found_id
            # As a further fallback, check general inventory if not found held/worn
            return self.game_state._find_object_id_by_name_in_inventory(text)
        
        elif preferred_source == 'inventory':
            found_id = self.game_state.find_item_id_held_or_worn(text)
            if found_id: return found_id
            found_id = self.game_state._find_object_id_by_name_in_inventory(text)
            if found_id: return found_id
            # Fallback to location
            current_room_id, current_area_id = self.game_state.get_current_location()
            return self.game_state.find_object_id_by_name_in_location(
                object_name=text, 
                room_id=current_room_id, 
                area_id=current_area_id,
                visible_only=True
            )
        
        # Default catch-all if preferred_source is not specified or unknown
        current_room_id, current_area_id = self.game_state.get_current_location()
        found_id = self.game_state.find_object_id_by_name_in_location(
            object_name=text, 
            room_id=current_room_id, 
            area_id=current_area_id,
            visible_only=True
        )
        if found_id: return found_id
        found_id = self.game_state.find_item_id_held_or_worn(text)
        if found_id: return found_id
        return self.game_state._find_object_id_by_name_in_inventory(text)


    def _extract_fallback_target(self, nlp_result: NlpProcessingResult, token_to_look_after: spacy.tokens.Token | None) -> FallbackTargetResult:
        """Extracts a primary target if structured parsing failed or wasn't applicable.
           Looks for GAME_OBJECT or AREA entities after the main action verb/keyword.
        """
        doc = nlp_result.doc
        # Use all entities from nlp_result, not just game_object_ents
        all_found_entities = nlp_result.entities # This is {text: span} for ALL entities
        
        logger.debug("Using general fallback target extraction logic (checking GAME_OBJECT and AREA).")

        # Option 1: Look for a GAME_OBJECT or AREA entity immediately after the verb/keyword
        if token_to_look_after:
            for i in range(token_to_look_after.i + 1, len(doc)):
                # Check for multi-token entities that start here first
                # Iterate through a copy of items for safe modification or just direct use
                for ent_text, ent_span in list(all_found_entities.items()): # Use list() if modifying, else direct iter is fine
                     if ent_span.start == i: # Entity starts at current token
                         if ent_span.label_ in ["GAME_OBJECT", "AREA"]:
                             logger.debug(f"Fallback - Primary target from multi-token {ent_span.label_} entity after verb: '{ent_span.text}' (ID: {ent_span.ent_id_})")
                             return FallbackTargetResult(primary_target=ent_span.text, target_object_id=ent_span.ent_id_)
                
                # Check single tokens (often caught by multi-token if entity is multi-token and starts here)
                # This can catch single-word entities if not caught above or if preferred.
                token_span_text = doc[i:i+1].text
                if token_span_text in all_found_entities:
                    ent_span = all_found_entities[token_span_text]
                    if ent_span.label_ in ["GAME_OBJECT", "AREA"]:
                        logger.debug(f"Fallback - Primary target from single-token {ent_span.label_} entity after verb: '{ent_span.text}' (ID: {ent_span.ent_id_})")
                        return FallbackTargetResult(primary_target=ent_span.text, target_object_id=ent_span.ent_id_)

        # Option 2: If none after verb, take the last GAME_OBJECT or AREA entity in the command
        last_targetable_ent: spacy.tokens.Span | None = None
        for ent_text, ent_span in all_found_entities.items():
            if ent_span.label_ in ["GAME_OBJECT", "AREA"]:
                if not last_targetable_ent or ent_span.start > last_targetable_ent.start:
                    last_targetable_ent = ent_span
        
        if last_targetable_ent:
            logger.debug(f"Fallback - Primary target from last {last_targetable_ent.label_} entity: '{last_targetable_ent.text}' (ID: {last_targetable_ent.ent_id_})")
            return FallbackTargetResult(primary_target=last_targetable_ent.text, target_object_id=last_targetable_ent.ent_id_)

        # Option 3: No GAME_OBJECT or AREA entities found, use noun chunks after the verb
        if token_to_look_after:
            for chunk in doc.noun_chunks:
                if chunk.start > token_to_look_after.i:
                    logger.debug(f"Fallback - Primary target from noun chunk after verb: '{chunk.text}'")
                    # This won't have an ID unless we try to resolve it further
                    return FallbackTargetResult(primary_target=chunk.text, target_object_id=None)
        
        logger.debug("Fallback - No clear primary target found.")
        return FallbackTargetResult()


    def _resolve_final_intent(self, possible_intents: dict, structured_intent: CommandIntent | None, structure_success: bool) -> CommandIntent:
        """Determines the final intent based on scores and structured parsing results."""
        if structure_success and structured_intent:
            logger.debug(f"Structure parsing successful, using structured intent: {structured_intent}")
            return structured_intent
        
        if not possible_intents:
            logger.warning("No possible intents identified.")
            return CommandIntent.UNKNOWN

        # Sort intents by score (descending)
        sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
        logger.debug(f"Intent scores after potential structure boost: {sorted_intents}")
        
        if not sorted_intents: # Should be caught by possible_intents check, but defensive
            return CommandIntent.UNKNOWN

        highest_scored_intent = sorted_intents[0][0]
        highest_score = sorted_intents[0][1]
        logger.debug(f"Highest scored intent initially: {highest_scored_intent}")

        # --- AMBIGUITY RESOLUTION & OVERRIDES ---
        
        # 1. TAKE vs TAKE_FROM
        # If TAKE_FROM was scored high due to "from" but structure parsing failed (e.g. no valid container)
        # and TAKE is also a possibility, prefer TAKE.
        if highest_scored_intent == CommandIntent.TAKE_FROM and not structure_success:
            if CommandIntent.TAKE in possible_intents and possible_intents[CommandIntent.TAKE] > 0:
                logger.debug("TAKE_FROM scored highest, but structure parsing failed. Overriding to TAKE.")
                return CommandIntent.TAKE
        
        # 2. EQUIP vs REMOVE (placeholder for more complex logic if needed)
        # Currently, "remove" maps to EQUIP. If we need a distinct REMOVE intent, handle here.

        # 3. LOOK vs other actions if "look" is present but not the primary verb
        # If "look" is present but another action verb is primary, the other verb usually wins.
        # (This is implicitly handled by how `matched_keyword_token` is found and scored)

        return highest_scored_intent

    def _guess_action_verb(self, doc: spacy.tokens.Doc, final_intent: CommandIntent) -> str | None:
        """Guesses the action verb based on the final intent if not explicitly found."""
        # This is a fallback if action_verb_token was None.
        # Try to get a verb associated with the intent.
        intent_to_verb_fallback = {
            CommandIntent.MOVE: "go",
            CommandIntent.LOOK: "look",
            CommandIntent.TAKE: "take",
            CommandIntent.DROP: "drop",
            CommandIntent.USE: "use",
            CommandIntent.EQUIP: "equip", # or "wear"/"remove" depending on context
            CommandIntent.SEARCH: "search",
            CommandIntent.PUT: "put",
            CommandIntent.TAKE_FROM: "take", # "take ... from"
            CommandIntent.LOCK: "lock",
            CommandIntent.UNLOCK: "unlock",
            CommandIntent.OPEN: "open",
            CommandIntent.CLOSE: "close",
            # For UNKNOWN or very generic intents, it's hard to guess a verb.
        }
        guessed_verb = intent_to_verb_fallback.get(final_intent)
        if guessed_verb:
            logger.debug(f"Guessed action verb '{guessed_verb}' based on final intent {final_intent}")
            return guessed_verb
        
        # Last resort: use the first verb in the command if any
        for token in doc:
            if token.pos_ == "VERB":
                logger.debug(f"Guessed action verb '{token.lemma_}' from first verb in command as last resort.")
                return token.lemma_
        return None

    def _build_parsed_intent(self, final_intent: CommandIntent, action_verb: str | None,
                             primary_target: str | None, target_object_id: str | None,
                             secondary_target: str | None, secondary_target_id: str | None,
                             preposition: str | None, command_original_case: str) -> ParsedIntent:
        """Constructs the final ParsedIntent object."""
        
        # If intent is MOVE, direction is usually in primary_target if not already set by _check_direction_entity
        direction_from_target: str | None = None
        if final_intent == CommandIntent.MOVE and primary_target:
            # Check if primary_target is a known direction (e.g., if "go north" was parsed this way)
            # This is a bit redundant if _check_direction_entity worked, but covers other cases.
            # For simplicity, assume primary_target IS the direction if intent is MOVE and no explicit direction entity was found.
            # A more robust check would involve matching primary_target against known direction aliases.
            # However, `_check_direction_entity` should handle most explicit directions.
            # If primary_target matched a DIRECTION entity, target_object_id *would be* the normalized direction.
            if target_object_id and target_object_id in ["north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest"] : # Check if ID is a direction
                direction_from_target = target_object_id
                # Clear target fields if they were just used for direction
                # primary_target = None 
                # target_object_id = None
            elif primary_target.lower() in ["north", "south", "east", "west", "up", "down", "northeast", "northwest", "southeast", "southwest"]:
                 direction_from_target = primary_target.lower()
                 # primary_target = None
                 # target_object_id = None

        # Action verb refinement
        final_action_verb = action_verb
        if not final_action_verb:
            # If still no action verb, use the intent name as a fallback (e.g., "TAKE" -> "take")
            final_action_verb = final_intent.name.lower() if final_intent != CommandIntent.UNKNOWN else None
        
        # If target_object_id is None but primary_target exists, try one last GameState lookup
        # This helps if fallback target extraction got text but not ID, or if structure parsing got text not ID
        if not target_object_id and primary_target:
            logger.debug(f"Target ID is None for primary target '{primary_target}'. Attempting final GameState lookup.")
            # Determine search preference based on intent
            search_pref = "any"
            if final_intent in [CommandIntent.TAKE, CommandIntent.PUT, CommandIntent.EQUIP, CommandIntent.DROP, CommandIntent.USE, CommandIntent.LOCK, CommandIntent.UNLOCK, CommandIntent.OPEN, CommandIntent.CLOSE]:
                search_pref = "possession_or_location" # These actions usually target things you have or see
            
            resolved_id = self._find_id_for_entity_text(primary_target, {}, search_pref) # Pass empty game_obj_ents as entities already processed
            if resolved_id:
                target_object_id = resolved_id
                logger.debug(f"Final lookup resolved primary target '{primary_target}' to ID '{target_object_id}'")

        if not secondary_target_id and secondary_target:
            logger.debug(f"Secondary Target ID is None for secondary target '{secondary_target}'. Attempting final GameState lookup.")
            search_pref = "location_or_container" # Secondary targets are often containers or items in location
            resolved_id = self._find_id_for_entity_text(secondary_target, {}, search_pref)
            if resolved_id:
                secondary_target_id = resolved_id
                logger.debug(f"Final lookup resolved secondary target '{secondary_target}' to ID '{secondary_target_id}'")

        if final_intent == CommandIntent.TAKE_FROM and not self._has_take_from_pattern(command_lower):
            final_intent = CommandIntent.TAKE

        final_target = (primary_target or "").strip().lower()
        if final_intent in ZERO_TARGET_INTENTS:
            final_target = ""
        parsed_intent_obj = ParsedIntent(
            intent=final_intent,
            action=final_action_verb,
            target=final_target,
            target_object_id=target_object_id,
            secondary_target=secondary_target,
            secondary_target_id=secondary_target_id,
            direction=direction_from_target, # Will be None if not MOVE or no direction found
            preposition=preposition,
            original_input=command_original_case
        )
        logger.info(f"Final Parsed Intent: {final_intent.name}, Action: {parsed_intent_obj.action}, Target: '{parsed_intent_obj.target}' (ID: {parsed_intent_obj.target_object_id}), Secondary: '{parsed_intent_obj.secondary_target}' (ID: {parsed_intent_obj.secondary_target_id}), Prep: {parsed_intent_obj.preposition}")
        logger.debug(f"Parsed: {parsed_intent_obj}")
        return parsed_intent_obj

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

    # --- Utility for fuzzy matching (if needed, currently not heavily used) ---
    def _find_closest_match(self, word: str, threshold: int = 80) -> str | None:
        """Finds the closest match for a word from a predefined list if above threshold."""
        if not self.valid_words: return None
        best_match = None
        highest_ratio = 0
        for valid_word in self.valid_words:
            ratio = fuzz.ratio(word, valid_word)
            if ratio > highest_ratio:
                highest_ratio = ratio
                best_match = valid_word
        
        if highest_ratio >= threshold:
            logger.debug(f"Fuzzy matched '{word}' to '{best_match}' with ratio {highest_ratio}")
            return best_match
        return None

# End of file
