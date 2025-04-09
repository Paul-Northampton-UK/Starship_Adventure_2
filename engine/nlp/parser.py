# engine/nlp/parser.py
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import spacy
from spacy.pipeline import EntityRuler
from fuzzywuzzy import fuzz

# Adjust imports to be relative to engine/ folder
from ..command_defs import CommandIntent, ParsedIntent
from ..game_state import GameState # GameState needed for object data access in pattern generation (now external)

# Import from the new nlp sub-package
from .constants import VERB_PATTERNS, INTENT_PRIORITIES, CONTEXT_WORDS
from .patterns import generate_patterns

class NLPCommandParser:
    """Handles parsing and processing of player commands using NLP."""

    def __init__(self, game_state: GameState):
        """Initialize the NLP command parser."""
        self.game_state = game_state
        # Load the spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logging.info("spaCy model 'en_core_web_sm' loaded.")
        except OSError:
            logging.error("Could not load spaCy model 'en_core_web_sm'.")
            logging.info("Attempting to download model...")
            try:
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
                logging.info("Successfully downloaded and loaded 'en_core_web_sm'.")
            except Exception as e:
                logging.critical(f"Failed to download or load spaCy model: {e}. NLP parser cannot function.")
                # Propagate the error or handle it gracefully
                raise RuntimeError("Failed to initialize NLP model.") from e


        # Create a list of all valid words for fuzzy matching (uses imported VERB_PATTERNS)
        self.valid_words = set()
        for pattern_intent, pattern_data in VERB_PATTERNS.items():
            self.valid_words.update(pattern_data.get("verbs", []))
            self.valid_words.update(pattern_data.get("context_words", []))
        # Add common game objects/NPCs to valid words
        self.valid_words.update([
            "key", "door", "button", "lever", "card", "torch", "computer", "terminal",
            "screen", "panel", "tool", "device", "sword", "shield", "potion", "book",
            "scroll", "map", "coin", "gem", "crystal", "backpack", "chest", "box",
            "window", "gate", "rope", "ladder", "guard", "merchant", "captain",
            "soldier", "villager", "alien", "robot", "scientist", "doctor", "engineer",
            "pilot", "crew", "room", "area", "cabinet", "gap", "hole", "note",
            "ingredients", "items", "materials", "parts", "tools", "weapons",
            "armor", "equipment", "structures", "buildings", "machines"
        ]) # Keep this updated or generate dynamically?

        # Add game-specific vocabulary exceptions
        self.add_game_vocabulary()

        # Generate patterns using the external function
        self.custom_patterns = generate_patterns(self.game_state)

        # Initialize the Entity Ruler with the generated patterns
        self.initialize_entity_ruler()

    def add_game_vocabulary(self) -> None:
        """Add game-specific vocabulary exceptions to the NLP pipeline's tokenizer."""
        # (Current implementation is empty, add tokenizer exceptions here if needed)
        pass

    def initialize_entity_ruler(self) -> None:
        """Initializes the Entity Ruler with custom patterns and adds it to the pipeline."""
        if not self.custom_patterns:
            logging.warning("No custom patterns generated for Entity Ruler.")
            return

        # Ensure the ruler is added before 'ner' and overwrites entities
        config = {"overwrite_ents": True}
        if "entity_ruler" not in self.nlp.pipe_names:
            self.nlp.add_pipe("entity_ruler", config=config, before="ner")
            logging.info(f"Added new Entity Ruler before 'ner'.")
        else:
            # If it exists, replace it to ensure config and patterns are updated
            self.nlp.replace_pipe("entity_ruler", "entity_ruler", config=config)
            logging.warning(f"Replaced existing Entity Ruler.")

        try:
            # Get the ruler pipe and add patterns
            ruler = self.nlp.get_pipe("entity_ruler")
            ruler.add_patterns(self.custom_patterns)
            logging.info(f"Entity Ruler updated with {len(self.custom_patterns)} patterns.")
        except Exception as e:
            logging.error(f"Error adding patterns to Entity Ruler: {e}", exc_info=True)

    def parse_command(self, command: str) -> ParsedIntent:
        print(">>> PARSER METHOD ENTERED <<<") # <-- ADDED FOR DIAGNOSTICS
        """Parse the raw command string into a ParsedIntent."""
        logging.debug(">>> PARSE_COMMAND START >>>")
        # --- Initial Setup & Single Letter Check ---
        command_original_case = command.strip()
        command_lower = command_original_case.lower()
        if not command_lower:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command_original_case)

        single_letter_intents = {
            "i": CommandIntent.INVENTORY, "l": CommandIntent.LOOK, "q": CommandIntent.QUIT,
            "n": CommandIntent.MOVE, "s": CommandIntent.MOVE, "e": CommandIntent.MOVE, "w": CommandIntent.MOVE,
            "u": CommandIntent.MOVE, "d": CommandIntent.MOVE,
        }
        if command_lower in single_letter_intents:
            intent = single_letter_intents[command_lower]
            logging.debug(f"Matched single-letter command '{command_lower}' to intent {intent}")
            direction = command_lower if intent == CommandIntent.MOVE else None
            return ParsedIntent(intent=intent, direction=direction, original_input=command_original_case)

        # --- NLP Processing ---
        doc = self.nlp(command_lower)
        logging.debug("--- NLP Processing Start ---")
        token_details = [(token.text, token.pos_, token.lemma_, token.i) for token in doc]
        logging.debug(f"Tokens (Text, POS, Lemma, Index): {token_details}")
        entity_details = [(ent.text, ent.label_, ent.ent_id_) for ent in doc.ents]
        logging.debug(f"Entities (Text, Label, ID): {entity_details}")
        logging.debug("--- NLP Processing End ---")

        verbs = [token for token in doc if token.pos_ == "VERB"]
        nouns = [token for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        adpositions = [token for token in doc if token.pos_ == "ADP"]
        entities = doc.ents
        game_object_ents = {ent.text: ent for ent in entities if ent.label_ == "GAME_OBJECT"}

        # --- Prioritize DIRECTION Entity ---
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

        # --- Verb/Intent Matching ---
        possible_intents: Dict[CommandIntent, float] = {}
        matched_verb_intents: Set[CommandIntent] = set()
        action_verb_token: Optional[spacy.tokens.Token] = None
        for i, token in enumerate(doc):
            token_check_forms = {token.lemma_, token.text.lower()}
            for intent, data in VERB_PATTERNS.items():
                verb_list = data.get("verbs", [])
                if any(form in verb_list for form in token_check_forms):
                    if not action_verb_token:
                        action_verb_token = token
                        logging.debug(f"Action verb token identified: '{action_verb_token.text}' at index {action_verb_token.i}")
                    if intent not in matched_verb_intents:
                        matched_verb_intents.add(intent)
                        possible_intents[intent] = possible_intents.get(intent, 0) + 1.0 * INTENT_PRIORITIES.get(intent, 1)
        logging.debug(f"Intents initially matched by verbs/keywords: {matched_verb_intents}")
        if not action_verb_token and verbs: # Fallback verb ID
            action_verb_token = verbs[0]
            logging.debug(f"Using first POS-tagged VERB as action verb: '{action_verb_token.text}'")
        elif not action_verb_token:
            logging.debug("No action verb token identified.")

        logging.debug("--- CHECKING FOR PUT STRUCTURE --- ")
        # --- Target Extraction & Intent Refinement (Prioritize PUT Structure) ---
        primary_target: Optional[str] = None
        target_object_id: Optional[str] = None
        secondary_target: Optional[str] = None
        secondary_target_id: Optional[str] = None
        preposition: Optional[str] = None
        preposition_token: Optional[spacy.tokens.Token] = None
        put_structure_success = False
        take_from_structure_success = False # New flag

        # Define prepositions to look for
        target_prepositions = {"in", "on", "into", "onto", "from"}

        # 1. Attempt Structure Parsing (PUT or TAKE_FROM) if verb suggests it
        likely_intents = {CommandIntent.PUT, CommandIntent.TAKE_FROM}
        if any(intent in possible_intents for intent in likely_intents) and action_verb_token:
            logging.debug("Attempting to parse structured command (verb obj1 prep obj2)")
            # Find the first relevant preposition after the verb
            for adp in adpositions:
                if adp.i > action_verb_token.i and adp.text.lower() in target_prepositions:
                    preposition_token = adp
                    preposition = adp.text.lower()
                    logging.debug(f"Relevant preposition found: '{preposition}' at index {adp.i}")
                    break # Use the first relevant preposition

            if preposition_token:
                 # Extract primary target (tokens between verb and preposition)
                 target1_tokens = [t for t in doc if action_verb_token.i < t.i < preposition_token.i and t.pos_ != 'ADP']
                 if target1_tokens:
                      primary_target = " ".join([t.text for t in target1_tokens])
                      logging.debug(f"PUT structure: Primary target tokens: {[t.text for t in target1_tokens]}, Combined: '{primary_target}'")
                      # Check if this matches a known entity
                      if primary_target in game_object_ents:
                           target_object_id = game_object_ents[primary_target].ent_id_
                           logging.debug(f"PUT structure: Primary target matched entity ID: {target_object_id}")

                 # Extract secondary target (tokens after preposition)
                 target2_tokens = [t for t in doc if t.i > preposition_token.i and t.pos_ != 'ADP']
                 if target2_tokens:
                      secondary_target = " ".join([t.text for t in target2_tokens])
                      logging.debug(f"PUT structure: Secondary target tokens: {[t.text for t in target2_tokens]}, Combined: '{secondary_target}'")
                      # Check if this matches a known entity
                      if secondary_target in game_object_ents:
                           secondary_target_id = game_object_ents[secondary_target].ent_id_
                           logging.debug(f"PUT structure: Secondary target matched entity ID: {secondary_target_id}")

                 # Check if we successfully got both targets for the structure
                 if primary_target and secondary_target:
                      structure_parsed = True # General flag
                      # Determine intent based on verb and preposition
                      verb_lemma = action_verb_token.lemma_
                      if verb_lemma in ["put", "place", "insert", "store"] and preposition != "from":
                           put_structure_success = True
                           logging.debug(f"PUT structure successfully parsed: T1='{primary_target}', P='{preposition}', T2='{secondary_target}'")
                      elif verb_lemma in ["take", "get", "retrieve"] and preposition == "from":
                           take_from_structure_success = True
                           logging.debug(f"TAKE_FROM structure successfully parsed: T1='{primary_target}', P='{preposition}', T2='{secondary_target}'")
                      else:
                           logging.warning(f"Parsed verb-prep structure ('{verb_lemma}' ... '{preposition}'), but combination doesn't match known PUT/TAKE_FROM patterns.")
                           structure_parsed = False # Treat as failed structure

                 if not structure_parsed:
                      logging.warning("Structured command parsing failed: Missing primary or secondary target after finding preposition.")
                      # Reset targets if structure failed despite finding a preposition
                      primary_target, target_object_id, secondary_target, secondary_target_id, preposition = None, None, None, None, None
            else:
                 logging.debug("PUT/TAKE_FROM intent likely, but no relevant preposition found after verb. Proceeding to fallback.")
        else:
            logging.debug("Skipping structured command check (PUT/TAKE_FROM not likely or no action verb).")

        # 2. Fallback Target Extraction (Only run if structured parsing did NOT succeed)
        if not put_structure_success and not take_from_structure_success:
            logging.debug("Using general fallback target extraction logic.")
            # Ensure targets are reset before fallback
            primary_target, target_object_id, secondary_target, secondary_target_id, preposition = None, None, None, None, None

            # Try extracting from known game object entities first
            if game_object_ents:
                 # Heuristic: use the entity closest to the verb? For now, just take the first one identified.
                 first_ent_text = next(iter(game_object_ents)) # This is fragile, relies on dict order
                 primary_target = first_ent_text
                 target_object_id = game_object_ents[first_ent_text].ent_id_
                 logging.debug(f"Fallback - Primary target from first GAME_OBJECT entity: '{primary_target}' (ID: {target_object_id}) ")
            # If no entities, try grabbing nouns/proper nouns after the verb
            elif action_verb_token:
                 potential_target_tokens = [token for token in doc if token.i > action_verb_token.i and token.pos_ in ["NOUN", "PROPN", "ADJ", "DET"]] # Include adjectives/determiners
                 if potential_target_tokens:
                      primary_target = " ".join([t.text for t in potential_target_tokens])
                      logging.debug(f"Fallback - Primary target guessed from tokens after verb: '{primary_target}'")
            # Last resort: just grab the first noun if no verb was identified
            elif nouns:
                 primary_target = nouns[0].text
                 logging.debug(f"Fallback - Primary target guessed from first noun (no verb found): '{primary_target}'")
            else:
                 logging.debug("Fallback - Could not identify any primary target.")

        # 3. Intent Scoring Refinement
        if put_structure_success:
            possible_intents[CommandIntent.PUT] = possible_intents.get(CommandIntent.PUT, 0) + 1000 # Strong boost
        elif take_from_structure_success:
            possible_intents[CommandIntent.TAKE_FROM] = possible_intents.get(CommandIntent.TAKE_FROM, 0) + 1000 # Strong boost
        # Add other scoring refinements here...

        # 4. Determine Final Intent
        final_intent = CommandIntent.UNKNOWN
        if possible_intents:
            sorted_intents = sorted(possible_intents.items(), key=lambda item: item[1], reverse=True)
            logging.debug(f"Intent scores after potential PUT/TAKE_FROM boost: {sorted_intents}")

            if sorted_intents:
                 highest_intent = sorted_intents[0][0]
                 logging.debug(f"Highest scored intent initially: {highest_intent}")

                 # --- Override logic based on structure parsing success --- 
                 if highest_intent == CommandIntent.TAKE_FROM and not take_from_structure_success:
                     logging.debug("TAKE_FROM scored highest, but structure parsing failed. Overriding to TAKE.")
                     # We should only override if TAKE was actually possible based on the verb
                     if CommandIntent.TAKE in possible_intents:
                          final_intent = CommandIntent.TAKE
                     else: # If TAKE wasn't possible, TAKE_FROM was likely wrong anyway
                          logging.warning("TAKE_FROM structure failed, and TAKE was not a possible intent. Setting to UNKNOWN.")
                          final_intent = CommandIntent.UNKNOWN 
                          
                 elif highest_intent == CommandIntent.PUT and not put_structure_success:
                     logging.debug("PUT scored highest, but structure parsing failed. Overriding to DROP.")
                     # Override to DROP, assuming 'put X' without structure means 'drop X'
                     # (The check for 'put down' is implicitly handled as structure would fail)
                     if CommandIntent.DROP in possible_intents:
                          final_intent = CommandIntent.DROP
                     else: # If DROP wasn't possible, PUT was likely wrong anyway
                          logging.warning("PUT structure failed, and DROP was not a possible intent. Setting to UNKNOWN.")
                          final_intent = CommandIntent.UNKNOWN 
                          
                 else:
                     # Structure parsing matched the highest intent, or it's a different intent
                     final_intent = highest_intent 
                     # Log the warning if structure failed but wasn't overridden (e.g., PUT won but DROP wasn't possible)
                     if final_intent == CommandIntent.TAKE_FROM and not take_from_structure_success:
                         logging.warning("TAKE_FROM intent chosen BUT structure parsing failed/skipped.")
                     if final_intent == CommandIntent.PUT and not put_structure_success:
                         logging.warning("PUT intent chosen BUT structure parsing failed/skipped.")
                         
            else: 
                 logging.warning("Intent scoring yielded no results despite initial possibilities.")
                 final_intent = CommandIntent.UNKNOWN
        else:
            logging.warning("No possible intents identified from verbs/keywords.")
            final_intent = CommandIntent.UNKNOWN

        # 5. Extract Action Verb (or guess based on intent)
        action_verb = action_verb_token.lemma_ if action_verb_token else None
        if not action_verb and final_intent != CommandIntent.UNKNOWN and final_intent in VERB_PATTERNS:
            verbs_for_intent = VERB_PATTERNS[final_intent].get("verbs", [])
            for token in doc:
                if token.text.lower() in verbs_for_intent:
                    action_verb = token.text.lower()
                    logging.debug(f"Guessed action verb '{action_verb}' from matched intent keyword.")
                    break

        # 7. Build the final ParsedIntent
        logging.info(f"Final Parsed Intent: {final_intent}, Action: {action_verb}, Target: '{primary_target}' (ID: {target_object_id}), Secondary: '{secondary_target}' (ID: {secondary_target_id}), Prep: {preposition}")
        return ParsedIntent(
            intent=final_intent,
            action=action_verb,
            target=primary_target,
            target_object_id=target_object_id,
            secondary_target=secondary_target,
            secondary_target_id=secondary_target_id,
            preposition=preposition,
            original_input=command_original_case
        )

    def _find_closest_match(self, word: str, threshold: int = 80) -> Optional[str]:
        """Find the closest match for a word from the valid vocabulary using fuzzy matching."""
        if not word:
            return None
        word = word.lower()
        best_match: Optional[str] = None
        best_ratio = threshold - 1 # Ensure ratio must be >= threshold

        for valid_word in self.valid_words:
            ratio = fuzz.ratio(word, valid_word)
            if ratio > best_ratio: # Find highest ratio >= threshold
                best_ratio = ratio
                best_match = valid_word

        # Only return if above threshold
        return best_match if best_ratio >= threshold else None

# End of file