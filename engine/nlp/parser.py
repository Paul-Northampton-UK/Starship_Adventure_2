# engine/nlp/parser.py
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
import spacy
from spacy.pipeline import EntityRuler
from fuzzywuzzy import fuzz

# Adjust imports to be relative to engine/ folder
from ..command_defs import CommandIntent, ParsedIntent
from ..game_state import GameState # GameState needed for object data access

# Import from the new nlp sub-package
from .constants import VERB_PATTERNS, INTENT_PRIORITIES, CONTEXT_WORDS
from .patterns import generate_patterns

# --- Helper Dataclasses ---
@dataclass
class NlpProcessingResult:
    """Holds the results of spaCy processing."""
    doc: spacy.tokens.Doc
    action_verb_token: Optional[spacy.tokens.Token] = None
    entities: Dict[str, spacy.tokens.Span] = field(default_factory=dict)
    game_object_ents: Dict[str, spacy.tokens.Span] = field(default_factory=dict)

@dataclass
class StructureParseResult:
    """Holds the results of parsing structured commands like PUT/TAKE_FROM."""
    success: bool = False
    intent: Optional[CommandIntent] = None
    primary_target: Optional[str] = None
    target_object_id: Optional[str] = None
    secondary_target: Optional[str] = None
    secondary_target_id: Optional[str] = None
    preposition: Optional[str] = None

@dataclass
class FallbackTargetResult:
    """Holds the results of fallback target extraction."""
    primary_target: Optional[str] = None
    target_object_id: Optional[str] = None

@dataclass # New dataclass to hold initial intent finding results
class InitialIntentResult:
    possible_intents: Dict[CommandIntent, float] = field(default_factory=dict)
    matched_keyword_token: Optional[spacy.tokens.Token] = None

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
            logging.info("spaCy model 'en_core_web_sm' loaded.")
            return nlp
        except OSError:
            logging.error("Could not load spaCy model 'en_core_web_sm'.")
            logging.info("Attempting to download model...")
            try:
                spacy.cli.download("en_core_web_sm")
                nlp = spacy.load("en_core_web_sm")
                logging.info("Successfully downloaded and loaded 'en_core_web_sm'.")
                return nlp
            except Exception as e:
                logging.critical(f"Failed to download or load spaCy model: {e}. NLP parser cannot function.")
                raise RuntimeError("Failed to initialize NLP model.") from e

    def _build_valid_words_set(self) -> Set[str]:
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
            logging.warning("No custom patterns generated for Entity Ruler.")
            return
        config = {"overwrite_ents": True}
        if "entity_ruler" not in self.nlp.pipe_names:
            self.nlp.add_pipe("entity_ruler", config=config, before="ner")
            logging.info("Added new Entity Ruler before 'ner'.")
        else:
            self.nlp.replace_pipe("entity_ruler", "entity_ruler", config=config)
            logging.warning("Replaced existing Entity Ruler.")
        try:
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.add_patterns(self.custom_patterns)
            logging.info(f"Entity Ruler updated with {len(self.custom_patterns)} patterns.")
        except Exception as e:
            logging.error(f"Error adding patterns to Entity Ruler: {e}", exc_info=True)

    # --- Main Parsing Method ---
    def parse_command(self, command: str) -> ParsedIntent:
        """Parse the raw command string into a ParsedIntent."""
        logging.debug(">>> PARSE_COMMAND START >>>")

        command_original_case, command_lower = self._preprocess_command(command)
        if not command_lower:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command_original_case)

        # 1. Handle single letter shortcuts
        single_letter_result = self._check_single_letter(command_lower, command_original_case)
        if single_letter_result: return single_letter_result

        # 2. Run spaCy NLP pipeline
        nlp_result = self._run_spacy(command_lower)

        # 3. Check for explicit DIRECTION entity (early exit for MOVE)
        direction_result = self._check_direction_entity(nlp_result.doc, command_original_case)
        if direction_result: return direction_result

        # 4. Identify potential intents based on verbs/keywords
        initial_intent_result = self._identify_initial_intents(nlp_result.doc)

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

    # --- Helper Methods ---
    def _preprocess_command(self, command: str) -> Tuple[str, str]:
        """Strip whitespace and convert command to lowercase."""
        command_original_case = command.strip()
        command_lower = command_original_case.lower()
        logging.debug(f"Preprocessing: Original='{command_original_case}', Lower='{command_lower}'")
        return command_original_case, command_lower

    def _check_single_letter(self, command_lower: str, command_original_case: str) -> Optional[ParsedIntent]:
        """Check for single-letter shortcut commands."""
        single_letter_intents = {
            "i": CommandIntent.INVENTORY, "l": CommandIntent.LOOK, "q": CommandIntent.QUIT,
            "n": CommandIntent.MOVE, "s": CommandIntent.MOVE, "e": CommandIntent.MOVE, "w": CommandIntent.MOVE,
            "u": CommandIntent.MOVE, "d": CommandIntent.MOVE,
            # Add other single letters like 'x' for examine if desired
        }
        if command_lower in single_letter_intents:
            intent = single_letter_intents[command_lower]
            logging.debug(f"Matched single-letter command '{command_lower}' to intent {intent}")
            direction = command_lower if intent == CommandIntent.MOVE else None
            # Normalize single letter directions
            if direction in ['n','s','e','w','u','d']:
                 direction = {'n':'north','s':'south','e':'east','w':'west','u':'up','d':'down'}.get(direction)
            return ParsedIntent(intent=intent, direction=direction, original_input=command_original_case)
        return None

    def _run_spacy(self, command_lower: str) -> NlpProcessingResult:
        """Run the spaCy NLP pipeline and extract key components."""
        doc = self.nlp(command_lower)
        logging.debug("--- NLP Processing Start ---")
        token_details = [(token.text, token.pos_, token.lemma_, token.i) for token in doc]
        logging.debug(f"Tokens (Text, POS, Lemma, Index): {token_details}")
        entity_details = [(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents]
        logging.debug(f"Entities (Text, Label, ID): {entity_details}")
        logging.debug("--- NLP Processing End ---")

        # Identify action verb (first verb found)
        action_verb_token: Optional[spacy.tokens.Token] = None
        for token in doc:
            if token.pos_ == "VERB":
                action_verb_token = token
                logging.debug(f"Action verb token identified (by POS): '{action_verb_token.text}' at index {action_verb_token.i}")
                break # Use the first verb

        entities = {ent.text: ent for ent in doc.ents}
        game_object_ents = {ent.text: ent for ent in doc.ents if ent.label_ == "GAME_OBJECT"}

        return NlpProcessingResult(
            doc=doc,
            action_verb_token=action_verb_token,
            entities=entities,
            game_object_ents=game_object_ents
        )

    def _check_direction_entity(self, doc: spacy.tokens.Doc, command_original_case: str) -> Optional[ParsedIntent]:
        """Check for a DIRECTION entity for immediate MOVE intent."""
        for ent in doc.ents:
            if ent.label_ == "DIRECTION":
                direction_text = ent.text
                normalized_direction = ent.ent_id_ # Use normalized ID from pattern
                logging.info(f"PARSER: Found DIRECTION entity '{direction_text}', normalized ID '{normalized_direction}', returning MOVE intent.")
                return ParsedIntent(
                    intent=CommandIntent.MOVE,
                    direction=normalized_direction,
                    original_input=command_original_case
                )
        return None

    def _identify_initial_intents(self, doc: spacy.tokens.Doc) -> InitialIntentResult:
        """Identify possible intents based on verbs/keywords, calculating initial scores and finding the trigger token."""
        possible_intents: Dict[CommandIntent, float] = {}
        matched_keyword_token: Optional[spacy.tokens.Token] = None

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
        first_verb_keyword_token: Optional[spacy.tokens.Token] = None
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
            logging.debug(f"First matched keyword token: '{matched_keyword_token.text}' at index {matched_keyword_token.i}")
            
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
                logging.debug(f"Verb/Keyword '{lookup_key}' added score {base_score} for intent {intent}")

                # Special handling for TAKE vs TAKE_FROM ambiguity based on "from"
                if intent == CommandIntent.TAKE:
                    # If "from" appears after "take", also add points to TAKE_FROM
                    for t in doc[matched_keyword_token.i:]: # Search from the verb onwards
                        if t.lemma_ == "from":
                            possible_intents[CommandIntent.TAKE_FROM] = possible_intents.get(CommandIntent.TAKE_FROM, 0) + INTENT_PRIORITIES.get(CommandIntent.TAKE_FROM, 87) # Higher base for TAKE_FROM
                            logging.debug(f"'from' found after '{lookup_key}', boosting TAKE_FROM.")
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
                    logging.debug(f"Fallback: Matched keyword token: '{matched_keyword_token.text}' at index {matched_keyword_token.i}")
                    intent = verb_to_intent_map[lemma]
                    base_score = INTENT_PRIORITIES.get(intent, 40) # Lower score for fallback
                    possible_intents[intent] = possible_intents.get(intent, 0) + base_score
                    logging.debug(f"Fallback Keyword '{lemma}' added score {base_score} for intent {intent}")


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
                logging.debug(f"Pattern-based scoring added {score} to {intent} (verbs: {pattern_data.get('verbs', [])}, context: {pattern_data.get('context_words', [])})")

        logging.debug(f"Intents initially matched by verbs/keywords: {list(possible_intents.keys())}")
        return InitialIntentResult(possible_intents=possible_intents, matched_keyword_token=matched_keyword_token)

    def _parse_structured_command(self, nlp_result: NlpProcessingResult, verb_token: Optional[spacy.tokens.Token], possible_intents: Dict) -> StructureParseResult:
        """Tries to parse structured commands like 'PUT item IN container' or 'TAKE item FROM container',
           or 'LOCK/UNLOCK target WITH key'.
        """
        doc = nlp_result.doc
        
        # 1. Check for custom UNLOCK_WITH_KEY / LOCK_WITH_KEY entities first
        for ent in doc.ents:
            if ent.label_ in ["UNLOCK_WITH_KEY", "LOCK_WITH_KEY"]:
                logging.debug(f"Found structured entity: {ent.label_} ('{ent.text}')")
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
                    logging.debug(f"{ent.label_} structure parsed from entity: T1='{target_str}', Key='{key_item_str}'")

                    # Boost the intent score significantly if structure is matched
                    if intent_to_set in possible_intents:
                        possible_intents[intent_to_set] += 1000 
                        logging.debug(f"Applied boost 1000 to {intent_to_set} due to successful structure parsing.")
                    else: # If not in possible intents, add it with high score
                        possible_intents[intent_to_set] = 1000
                        logging.debug(f"Added {intent_to_set} with score 1000 due to successful structure parsing.")

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
                    logging.warning(f"Could not properly parse UNLOCK/LOCK_WITH_KEY entity: '{ent.text}'")


        # 2. Check for PUT/TAKE_FROM prepositional logic
        # This requires a verb like "put" or "take" and a preposition like "in", "on", "from"
        if not verb_token or verb_token.lemma_.lower() not in ["put", "place", "store", "insert", "take", "get", "pick", "grab"]:
            logging.debug("Skipping PUT/TAKE_FROM structured command check (verb missing or PUT/TAKE_FROM not likely).")
            return StructureParseResult(success=False)
        
        logging.debug("Attempting to parse structured command (verb obj1 prep obj2) using PREPOSITION logic.")
        
        preposition_token: Optional[spacy.tokens.Token] = None
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
            logging.debug(f"No clear PUT/TAKE_FROM intent for verb '{verb_lemma}'. Skipping preposition logic.")
            return StructureParseResult(success=False)

        # Find the preposition after the verb
        for token in doc[verb_token.i + 1:]:
            if token.lemma_ in relevant_preps:
                preposition_token = token
                logging.debug(f"Found preposition '{preposition_token.lemma_}' at index {preposition_token.i}")
                break
        
        if not preposition_token:
            logging.debug(f"{current_intent_for_prep} intent likely, but no relevant preposition found (PREPOSITION logic).")
            return StructureParseResult(success=False)

        # We have a verb and a preposition. Now extract primary and secondary targets.
        # Primary target: spans between verb and preposition.
        # Secondary target: spans after preposition to end of command.
        
        primary_target_span: Optional[spacy.tokens.Span] = None
        if verb_token.i + 1 < preposition_token.i:
            primary_target_span = doc[verb_token.i + 1 : preposition_token.i]
        
        secondary_target_span: Optional[spacy.tokens.Span] = None
        if preposition_token.i + 1 < len(doc):
            secondary_target_span = doc[preposition_token.i + 1 :]

        if not primary_target_span or not secondary_target_span:
            logging.warning(f"Structured command parse: Missing primary or secondary target span for verb '{verb_lemma}' and prep '{preposition_token.lemma_}'.")
            return StructureParseResult(success=False)

        primary_target_str = primary_target_span.text.strip()
        secondary_target_str = secondary_target_span.text.strip()

        logging.debug(f"Extracted from structure: Verb='{verb_lemma}', Primary='{primary_target_str}', Prep='{preposition_token.lemma_}', Secondary='{secondary_target_str}'")

        # Try to resolve to actual object IDs
        # For PUT: primary is the item, secondary is the container
        # For TAKE_FROM: primary is the item, secondary is the container
        primary_target_id = self._find_id_for_entity_text(primary_target_str, nlp_result.game_object_ents, preferred_source='possession_or_location')
        secondary_target_id = self._find_id_for_entity_text(secondary_target_str, nlp_result.game_object_ents, preferred_source='location_or_container')
        
        # Boost the intent score significantly if structure is matched
        if current_intent_for_prep in possible_intents:
            possible_intents[current_intent_for_prep] += 1000
            logging.debug(f"Applied boost 1000 to {current_intent_for_prep} due to successful structure parsing.")
        else: # If not in possible intents (e.g. only TAKE was found, but "from" implies TAKE_FROM)
            possible_intents[current_intent_for_prep] = 1000
            logging.debug(f"Added {current_intent_for_prep} with score 1000 due to successful structure parsing.")


        return StructureParseResult(
            success=True,
            intent=current_intent_for_prep,
            primary_target=primary_target_str,
            target_object_id=primary_target_id,
            secondary_target=secondary_target_str,
            secondary_target_id=secondary_target_id,
            preposition=preposition_token.lemma_
        )

    def _find_id_for_entity_text(self, text: str, candidate_entities: List[Dict[str, Any]], preferred_source: str = 'location') -> Optional[str]:
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


    def _extract_fallback_target(self, nlp_result: NlpProcessingResult, token_to_look_after: Optional[spacy.tokens.Token]) -> FallbackTargetResult:
        """Extracts a primary target if structured parsing failed or wasn't applicable.
           Looks for GAME_OBJECT entities after the main action verb/keyword.
        """
        doc = nlp_result.doc
        game_object_ents = nlp_result.game_object_ents
        
        logging.debug("Using general fallback target extraction logic.")

        # Try to find the most relevant GAME_OBJECT entity
        # Option 1: Look for a GAME_OBJECT entity immediately after the verb/keyword
        if token_to_look_after:
            for i in range(token_to_look_after.i + 1, len(doc)):
                token_span = doc[i:i+1] # Check single tokens first
                if token_span.text in game_object_ents:
                    ent_span = game_object_ents[token_span.text]
                    logging.debug(f"Fallback - Primary target from GAME_OBJECT entity after verb: '{ent_span.text}' (ID: {ent_span.ent_id_})")
                    return FallbackTargetResult(primary_target=ent_span.text, target_object_id=ent_span.ent_id_)
                # Check for multi-token entities that start here
                for ent_text, ent_span in game_object_ents.items():
                     if ent_span.start == i: # Entity starts at current token
                         logging.debug(f"Fallback - Primary target from multi-token GAME_OBJECT entity after verb: '{ent_span.text}' (ID: {ent_span.ent_id_})")
                         return FallbackTargetResult(primary_target=ent_span.text, target_object_id=ent_span.ent_id_)


        # Option 2: If none after verb, take the last GAME_OBJECT entity in the command
        # (This can be problematic if there are multiple, e.g. "take red key with blue key")
        last_game_object_ent: Optional[spacy.tokens.Span] = None
        for ent_text, ent_span in game_object_ents.items():
            if not last_game_object_ent or ent_span.start > last_game_object_ent.start:
                last_game_object_ent = ent_span
        
        if last_game_object_ent:
            logging.debug(f"Fallback - Primary target from last GAME_OBJECT entity: '{last_game_object_ent.text}' (ID: {last_game_object_ent.ent_id_})")
            return FallbackTargetResult(primary_target=last_game_object_ent.text, target_object_id=last_game_object_ent.ent_id_)

        # Option 3: No GAME_OBJECT entities found, use noun chunks after the verb
        if token_to_look_after:
            for chunk in doc.noun_chunks:
                if chunk.start > token_to_look_after.i:
                    logging.debug(f"Fallback - Primary target from noun chunk after verb: '{chunk.text}'")
                    # This won't have an ID unless we try to resolve it further
                    return FallbackTargetResult(primary_target=chunk.text, target_object_id=None)
        
        logging.debug("Fallback - No clear primary target found.")
        return FallbackTargetResult()


    def _resolve_final_intent(self, possible_intents: Dict, structured_intent: Optional[CommandIntent], structure_success: bool) -> CommandIntent:
        """Determines the final intent based on scores and structured parsing results."""
        if structure_success and structured_intent:
            logging.debug(f"Structure parsing successful, using structured intent: {structured_intent}")
            return structured_intent
        
        if not possible_intents:
            logging.warning("No possible intents identified.")
            return CommandIntent.UNKNOWN

        # Sort intents by score (descending)
        sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
        logging.debug(f"Intent scores after potential structure boost: {sorted_intents}")
        
        if not sorted_intents: # Should be caught by possible_intents check, but defensive
            return CommandIntent.UNKNOWN

        highest_scored_intent = sorted_intents[0][0]
        highest_score = sorted_intents[0][1]
        logging.debug(f"Highest scored intent initially: {highest_scored_intent}")

        # --- AMBIGUITY RESOLUTION & OVERRIDES ---
        
        # 1. TAKE vs TAKE_FROM
        # If TAKE_FROM was scored high due to "from" but structure parsing failed (e.g. no valid container)
        # and TAKE is also a possibility, prefer TAKE.
        if highest_scored_intent == CommandIntent.TAKE_FROM and not structure_success:
            if CommandIntent.TAKE in possible_intents and possible_intents[CommandIntent.TAKE] > 0:
                logging.debug("TAKE_FROM scored highest, but structure parsing failed. Overriding to TAKE.")
                return CommandIntent.TAKE
        
        # 2. EQUIP vs REMOVE (placeholder for more complex logic if needed)
        # Currently, "remove" maps to EQUIP. If we need a distinct REMOVE intent, handle here.

        # 3. LOOK vs other actions if "look" is present but not the primary verb
        # If "look" is present but another action verb is primary, the other verb usually wins.
        # (This is implicitly handled by how `matched_keyword_token` is found and scored)

        return highest_scored_intent

    def _guess_action_verb(self, doc: spacy.tokens.Doc, final_intent: CommandIntent) -> Optional[str]:
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
            logging.debug(f"Guessed action verb '{guessed_verb}' based on final intent {final_intent}")
            return guessed_verb
        
        # Last resort: use the first verb in the command if any
        for token in doc:
            if token.pos_ == "VERB":
                logging.debug(f"Guessed action verb '{token.lemma_}' from first verb in command as last resort.")
                return token.lemma_
        return None

    def _build_parsed_intent(self, final_intent: CommandIntent, action_verb: Optional[str],
                             primary_target: Optional[str], target_object_id: Optional[str],
                             secondary_target: Optional[str], secondary_target_id: Optional[str],
                             preposition: Optional[str], command_original_case: str) -> ParsedIntent:
        """Constructs the final ParsedIntent object."""
        
        # If intent is MOVE, direction is usually in primary_target if not already set by _check_direction_entity
        direction_from_target: Optional[str] = None
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
            logging.debug(f"Target ID is None for primary target '{primary_target}'. Attempting final GameState lookup.")
            # Determine search preference based on intent
            search_pref = "any"
            if final_intent in [CommandIntent.TAKE, CommandIntent.PUT, CommandIntent.EQUIP, CommandIntent.DROP, CommandIntent.USE, CommandIntent.LOCK, CommandIntent.UNLOCK, CommandIntent.OPEN, CommandIntent.CLOSE]:
                search_pref = "possession_or_location" # These actions usually target things you have or see
            
            resolved_id = self._find_id_for_entity_text(primary_target, {}, search_pref) # Pass empty game_obj_ents as entities already processed
            if resolved_id:
                target_object_id = resolved_id
                logging.debug(f"Final lookup resolved primary target '{primary_target}' to ID '{target_object_id}'")

        if not secondary_target_id and secondary_target:
            logging.debug(f"Secondary Target ID is None for secondary target '{secondary_target}'. Attempting final GameState lookup.")
            search_pref = "location_or_container" # Secondary targets are often containers or items in location
            resolved_id = self._find_id_for_entity_text(secondary_target, {}, search_pref)
            if resolved_id:
                secondary_target_id = resolved_id
                logging.debug(f"Final lookup resolved secondary target '{secondary_target}' to ID '{secondary_target_id}'")

        parsed_intent_obj = ParsedIntent(
            intent=final_intent,
            action=final_action_verb,
            target=primary_target,
            target_object_id=target_object_id,
            secondary_target=secondary_target,
            secondary_target_id=secondary_target_id,
            direction=direction_from_target, # Will be None if not MOVE or no direction found
            preposition=preposition,
            original_input=command_original_case
        )
        logging.info(f"Final Parsed Intent: {final_intent.name}, Action: {parsed_intent_obj.action}, Target: '{parsed_intent_obj.target}' (ID: {parsed_intent_obj.target_object_id}), Secondary: '{parsed_intent_obj.secondary_target}' (ID: {parsed_intent_obj.secondary_target_id}), Prep: {parsed_intent_obj.preposition}")
        logging.debug(f"Parsed: {parsed_intent_obj}")
        return parsed_intent_obj

    # --- Utility for fuzzy matching (if needed, currently not heavily used) ---
    def _find_closest_match(self, word: str, threshold: int = 80) -> Optional[str]:
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
            logging.debug(f"Fuzzy matched '{word}' to '{best_match}' with ratio {highest_ratio}")
            return best_match
        return None

# End of file