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
        result = InitialIntentResult()
        matched_verb_intents: Set[CommandIntent] = set()
        first_match_token: Optional[spacy.tokens.Token] = None

        # Score based on verbs matching VERB_PATTERNS
        for token in doc:
            token_check_forms = {token.lemma_, token.text.lower()}
            for intent, data in VERB_PATTERNS.items():
                verb_list = data.get("verbs", [])
                if any(form in verb_list for form in token_check_forms):
                    # Store the first token that matches any intent keyword
                    if first_match_token is None:
                        first_match_token = token
                        logging.debug(f"First matched keyword token: '{token.text}' at index {token.i}")
                        
                    if intent not in matched_verb_intents:
                        matched_verb_intents.add(intent)
                        priority = INTENT_PRIORITIES.get(intent, 1)
                        result.possible_intents[intent] = result.possible_intents.get(intent, 0) + 1.0 * priority
                        logging.debug(f"Verb/Keyword '{token.text}' added score {priority} for intent {intent}")

        result.matched_keyword_token = first_match_token
        logging.debug(f"Intents initially matched by verbs/keywords: {list(result.possible_intents.keys())}")
        return result

    def _parse_structured_command(self, nlp_result: NlpProcessingResult, verb_token: Optional[spacy.tokens.Token], possible_intents: Dict) -> StructureParseResult:
        """Attempts to parse structured commands like PUT/TAKE_FROM and LOCK/UNLOCK_WITH_KEY."""
        doc = nlp_result.doc
        game_object_ents = nlp_result.game_object_ents

        result = StructureParseResult()

        # --- NEW: Check for LOCK/UNLOCK_WITH_KEY Entities first ---
        for ent in doc.ents:
            if ent.label_ in ["LOCK_WITH_KEY", "UNLOCK_WITH_KEY"]:
                logging.debug(f"Found structured entity: {ent.label_} ('{ent.text}')")
                # --- MODIFIED: Extract components directly from entity span --- 
                verb_token = ent[0] # Assume first token is verb
                preposition_token = None
                target_tokens = []
                key_tokens = []
                prep_found = False

                for token in ent:
                    if token.i == verb_token.i: # Skip the verb itself
                        continue
                    if not prep_found and token.lower_ in ["with", "using"]:
                        preposition_token = token
                        prep_found = True
                        continue # Skip the preposition itself
                    
                    if not prep_found:
                        target_tokens.append(token)
                    else:
                        key_tokens.append(token)
                # --- End Modification ---

                # Check if we extracted all parts
                if target_tokens and key_tokens and verb_token and preposition_token:
                    # --- NEW: Strip leading determiners from target and key --- 
                    if target_tokens and target_tokens[0].pos_ == "DET":
                        target_tokens = target_tokens[1:]
                    if key_tokens and key_tokens[0].pos_ == "DET":
                        key_tokens = key_tokens[1:]
                    # --- End Stripping ---
                    
                    result.primary_target = " ".join([t.text for t in target_tokens])
                    # Look up ID if the target text matches a known game object entity
                    # We might need to search game_object_ents based on the joined text, not just exact match
                    # Simple check for now:
                    target_ent = game_object_ents.get(result.primary_target)
                    if target_ent:
                        result.target_object_id = target_ent.ent_id_
                    else:
                         # Maybe try finding object ID via game_state if entity ruler missed it?
                         # result.target_object_id = self.game_state.find_object_id... (complex)
                         pass # Leave ID None if no direct entity match

                    result.secondary_target = " ".join([t.text for t in key_tokens])
                    # Look up key ID similarly
                    key_ent = game_object_ents.get(result.secondary_target)
                    if key_ent:
                        result.secondary_target_id = key_ent.ent_id_
                    else:
                         pass # Leave key ID None

                    result.preposition = preposition_token.text.lower()
                    result.success = True

                    if ent.label_ == "LOCK_WITH_KEY":
                        result.intent = CommandIntent.LOCK
                        logging.debug(f"LOCK_WITH_KEY structure parsed from entity: T1='{result.primary_target}', Key='{result.secondary_target}'")
                    else: # UNLOCK_WITH_KEY
                        result.intent = CommandIntent.UNLOCK
                        logging.debug(f"UNLOCK_WITH_KEY structure parsed from entity: T1='{result.primary_target}', Key='{result.secondary_target}'")
                    return result # Found a specific lock/unlock structure, we're done.
                else:
                    logging.warning(f"Found {ent.label_} entity, but failed to extract required components (verb, target, key, prep) from span: {ent.text}")
                    # Don't return yet, fall through to old logic

        # --- Fallback to existing PUT/TAKE_FROM logic if no lock/unlock entity found ---
        likely_put_take_intents = {CommandIntent.PUT, CommandIntent.TAKE_FROM}
        # Use the original verb_token passed to the function for PUT/TAKE_FROM
        if not verb_token or not any(intent in possible_intents for intent in likely_put_take_intents):
            logging.debug("Skipping PUT/TAKE_FROM structured command check (verb missing or PUT/TAKE_FROM not likely).")
            return result # Return default failure

        logging.debug("Attempting to parse structured command (verb obj1 prep obj2) using PREPOSITION logic.")
        target_prepositions = {"in", "on", "into", "onto", "from"}
        preposition_token: Optional[spacy.tokens.Token] = None
        preposition: Optional[str] = None

        # Find the first relevant preposition after the verb
        for token in doc:
            if token.i > verb_token.i and token.pos_ == "ADP" and token.text.lower() in target_prepositions:
                preposition_token = token
                preposition = token.text.lower()
                logging.debug(f"Relevant preposition found: '{preposition}' at index {token.i}")
                break

        if preposition_token:
            # Extract primary target (tokens between verb and preposition)
            target1_tokens = [t for t in doc if verb_token.i < t.i < preposition_token.i and t.pos_ != 'ADP']
            if target1_tokens:
                result.primary_target = " ".join([t.text for t in target1_tokens])
                if result.primary_target in game_object_ents:
                    result.target_object_id = game_object_ents[result.primary_target].ent_id_

            # Extract secondary target (tokens after preposition)
            target2_tokens = [t for t in doc if t.i > preposition_token.i and t.pos_ != 'ADP']
            if target2_tokens:
                result.secondary_target = " ".join([t.text for t in target2_tokens])
                if result.secondary_target in game_object_ents:
                    result.secondary_target_id = game_object_ents[result.secondary_target].ent_id_

            # Check if structure is complete and determine intent
            if result.primary_target and result.secondary_target:
                result.preposition = preposition
                verb_lemma = verb_token.lemma_
                if verb_lemma in ["put", "place", "insert", "store"] and preposition != "from":
                    result.success = True
                    result.intent = CommandIntent.PUT
                    logging.debug(f"PUT structure successfully parsed (PREPOSITION logic): T1='{result.primary_target}', P='{result.preposition}', T2='{result.secondary_target}'")
                elif verb_lemma in ["take", "get", "retrieve", "remove", "extract", "withdraw"] and preposition == "from":
                    result.success = True
                    result.intent = CommandIntent.TAKE_FROM
                    logging.debug(f"TAKE_FROM structure successfully parsed (PREPOSITION logic): T1='{result.primary_target}', P='{result.preposition}', T2='{result.secondary_target}'")
                else:
                    logging.warning(f"Parsed verb-prep structure ('{verb_lemma}' ... '{preposition}'), but combination doesn't match known PUT/TAKE_FROM patterns (PREPOSITION logic).")
            else:
                 logging.warning("Structured command parsing failed (PREPOSITION logic): Missing primary or secondary target.")
        else:
             logging.debug("PUT/TAKE_FROM intent likely, but no relevant preposition found (PREPOSITION logic).")

        return result

    def _extract_fallback_target(self, nlp_result: NlpProcessingResult, token_to_look_after: Optional[spacy.tokens.Token]) -> FallbackTargetResult:
        """Extracts the most likely primary target when structured parsing fails."""
        logging.debug("Using general fallback target extraction logic.")
        doc = nlp_result.doc
        game_object_ents = nlp_result.game_object_ents
        result = FallbackTargetResult()

        # Try extracting from known game object entities first
        if game_object_ents:
             last_ent = doc.ents[-1]
             if last_ent.label_ == "GAME_OBJECT":
                 result.primary_target = last_ent.text
                 result.target_object_id = last_ent.ent_id_
                 logging.debug(f"Fallback - Primary target from last GAME_OBJECT entity: '{result.primary_target}'")

        # If no entities, try grabbing nouns/proper nouns/adj AFTER the verb/keyword token
        if not result.primary_target and token_to_look_after:
             potential_target_tokens = [
                 token for token in doc
                 if token.i > token_to_look_after.i # Use the index of the verb OR keyword
                 and token.pos_ in ["NOUN", "PROPN", "ADJ", "DET", "NUM"]
             ]
             if potential_target_tokens:
                  result.primary_target = " ".join([t.text for t in potential_target_tokens])
                  logging.debug(f"Fallback - Primary target guessed from tokens after verb/keyword '{token_to_look_after.text}': '{result.primary_target}'")
        
        # Last resort: if no verb/keyword identified OR no tokens after it, grab first noun
        elif not result.primary_target:
             nouns = [token for token in doc if token.pos_ in ["NOUN", "PROPN"]]
             if nouns:
                 result.primary_target = nouns[0].text
                 logging.debug(f"Fallback - Primary target guessed from first noun (no verb/keyword or tokens after): '{result.primary_target}'")

        if not result.primary_target:
             logging.debug("Fallback - Could not identify any primary target.")

        return result

    def _resolve_final_intent(self, possible_intents: Dict, structured_intent: Optional[CommandIntent], structure_success: bool) -> CommandIntent:
        """Determines the final intent based on scoring and structure parsing results."""
        final_intent = CommandIntent.UNKNOWN

        if not possible_intents:
            logging.warning("No possible intents identified from verbs/keywords.")
            return CommandIntent.UNKNOWN

        # Apply scoring boost based on structure parsing success
        if structure_success and structured_intent:
            boost = 1000 # Strong boost for successful structure match
            possible_intents[structured_intent] = possible_intents.get(structured_intent, 0) + boost
            logging.debug(f"Applied boost {boost} to {structured_intent} due to successful structure parsing.")

        sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
        logging.debug(f"Intent scores after potential structure boost: {sorted_intents}")

        if sorted_intents:
             highest_intent = sorted_intents[0][0]
             logging.debug(f"Highest scored intent initially: {highest_intent}")

             # --- Override logic based on structure parsing success ---
             if highest_intent == CommandIntent.TAKE_FROM and not structure_success:
                 logging.debug("TAKE_FROM scored highest, but structure parsing failed. Overriding to TAKE.")
                 final_intent = CommandIntent.TAKE if CommandIntent.TAKE in possible_intents else CommandIntent.UNKNOWN
             elif highest_intent == CommandIntent.PUT and not structure_success:
                 logging.debug("PUT scored highest, but structure parsing failed. Overriding to DROP.")
                 final_intent = CommandIntent.DROP if CommandIntent.DROP in possible_intents else CommandIntent.UNKNOWN
             else:
                 final_intent = highest_intent # Use the highest score if structure matched or different intent

             # Log warnings if overrides resulted in UNKNOWN
             if final_intent == CommandIntent.UNKNOWN and highest_intent in [CommandIntent.TAKE_FROM, CommandIntent.PUT]:
                 logging.warning(f"{highest_intent} structure failed, and fallback intent not possible. Setting to UNKNOWN.")
             # Log warnings if final intent doesn't match structure success (shouldn't happen with override)
             if final_intent == CommandIntent.TAKE_FROM and not structure_success: logging.warning("TAKE_FROM intent chosen BUT structure parsing failed/skipped.")
             if final_intent == CommandIntent.PUT and not structure_success: logging.warning("PUT intent chosen BUT structure parsing failed/skipped.")

        else:
             logging.warning("Intent scoring yielded no results despite initial possibilities.")
             final_intent = CommandIntent.UNKNOWN

        return final_intent

    def _guess_action_verb(self, doc: spacy.tokens.Doc, final_intent: CommandIntent) -> Optional[str]:
        """Guesses the action verb lemma based on intent if not found via POS."""
        if final_intent != CommandIntent.UNKNOWN and final_intent in VERB_PATTERNS:
            verbs_for_intent = VERB_PATTERNS[final_intent].get("verbs", [])
            for token in doc:
                if token.text.lower() in verbs_for_intent:
                    logging.debug(f"Guessed action verb '{token.lemma_}' from matched intent keyword '{token.text.lower()}'.")
                    return token.lemma_ # Return lemma for consistency
        logging.debug("Could not guess action verb.")
        return None

    def _build_parsed_intent(self, final_intent: CommandIntent, action_verb: Optional[str],
                             primary_target: Optional[str], target_object_id: Optional[str],
                             secondary_target: Optional[str], secondary_target_id: Optional[str],
                             preposition: Optional[str], command_original_case: str) -> ParsedIntent:
        """Constructs the final ParsedIntent object."""
        # Direction is only relevant for MOVE intent, handled earlier
        direction = None
        if final_intent == CommandIntent.MOVE:
             # We should ideally get direction from the entity check or guess if not present
             # This part might need refinement if MOVE intent is resolved here without direction
             logging.warning("_build_parsed_intent: MOVE intent resolved without explicit direction.")

        logging.info(f"Final Parsed Intent: {final_intent}, Action: {action_verb}, Target: '{primary_target}' (ID: {target_object_id}), Secondary: '{secondary_target}' (ID: {secondary_target_id}), Prep: {preposition}")
        return ParsedIntent(
            intent=final_intent,
            action=action_verb,
            target=primary_target,
            target_object_id=target_object_id,
            secondary_target=secondary_target,
            secondary_target_id=secondary_target_id,
            preposition=preposition,
            direction=direction, # Will be None unless MOVE was handled earlier
            original_input=command_original_case
        )

    # --- Fuzzy Matching (Placeholder) ---
    def _find_closest_match(self, word: str, threshold: int = 80) -> Optional[str]:
        """Find the closest match for a word from the valid vocabulary using fuzzy matching."""
        # NOTE: This is not currently integrated into the main parsing flow.
        # Needs to be called during target/verb identification if exact match fails.
        if not word: return None
        word = word.lower()
        best_match: Optional[str] = None
        best_ratio = threshold - 1
        for valid_word in self.valid_words:
            ratio = fuzz.ratio(word, valid_word)
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = valid_word
        return best_match if best_ratio >= threshold else None

# End of file