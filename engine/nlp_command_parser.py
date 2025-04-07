from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
import spacy
from spacy.pipeline import EntityRuler
from fuzzywuzzy import fuzz
from .command_defs import CommandIntent, ParsedIntent
from .game_state import GameState, PowerState
import logging

# Import the constants from the new module
from .nlp.constants import VERB_PATTERNS, INTENT_PRIORITIES, CONTEXT_WORDS
# Import the pattern generation function
from .nlp.patterns import generate_patterns

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
    
    def parse_command(self, command: str) -> ParsedIntent:
        """Parse the raw command string into a ParsedIntent."""
        command_original_case = command.strip() # Preserve original case for exact match
        command_lower = command_original_case.lower()
        
        if not command_lower:
            return ParsedIntent(intent=CommandIntent.UNKNOWN, original_input=command_original_case)

        # --- Quick check for single-letter commands (case-insensitive) --- 
        single_letter_intents = {
            "i": CommandIntent.INVENTORY,
            "l": CommandIntent.LOOK,
            "q": CommandIntent.QUIT,
            # Add others like n, s, e, w? Maybe handled better by DIRECTION entity?
        }
        if command_lower in single_letter_intents:
            intent = single_letter_intents[command_lower]
            logging.debug(f"Matched single-letter command '{command_lower}' to intent {intent}")
            return ParsedIntent(intent=intent, original_input=command_original_case)
            
        # --- Process with NLP --- 
        doc = self.nlp(command_lower) # Use lowercased version for NLP
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
                logging.info(f"PARSER: Found DIRECTION entity '{ent.text}', normalized to '{normalized_direction}', returning MOVE intent.")

                # Found a direction, assume MOVE intent and return immediately
                return ParsedIntent(
                    intent=CommandIntent.MOVE,
                    direction=normalized_direction, 
                    original_input=command_original_case # Return original case input
                )

        # --- If no DIRECTION entity, proceed with verb/entity analysis --- 
        verbs = [token for token in doc if token.pos_ == "VERB"]
        entities = doc.ents 
        nouns = [token for token in doc if token.pos_ in ["NOUN", "PROPN"]]
        
        logging.debug(f"Verbs: {[v.text for v in verbs]}")
        logging.debug(f"Entities: {[(ent.text, ent.label_) for ent in entities]}")
        logging.debug(f"Nouns: {[n.text for n in nouns]}")

        # Determine Intent based on verbs, entities, and context
        possible_intents: Dict[CommandIntent, float] = {}
        matched_verb_intents: Set[CommandIntent] = set()
        for token in doc:
            # Handle cases like "inventory" where it might not be tagged as VERB
            # Check both lemma and lowercased text against verbs
            token_check_forms = {token.lemma_, token.text.lower()}
            for intent, data in VERB_PATTERNS.items():
                verb_list = data.get("verbs", [])
                if any(form in verb_list for form in token_check_forms):
                    matched_verb_intents.add(intent)
                    possible_intents[intent] = possible_intents.get(intent, 0) + 1.0 * INTENT_PRIORITIES.get(intent, 1)
        logging.debug(f"Intents matched by verbs/keywords: {matched_verb_intents}")

        # --- Entity Analysis --- 
        primary_target: Optional[str] = None
        target_object_id: Optional[str] = None
        target_type: Optional[str] = None 
        
        game_object_ents = [ent for ent in entities if ent.label_ == "GAME_OBJECT"]
        if game_object_ents:
             primary_target = game_object_ents[0].text
             target_object_id = game_object_ents[0].ent_id_ 
             target_type = "GAME_OBJECT"
             logging.debug(f"Primary target identified as GAME_OBJECT: '{primary_target}' (ID: {target_object_id})")
        else:
            # Fallback: Reconstruct target from nouns/adjectives after the *first* verb/noun-acting-as-verb
            first_action_token_index = -1
            # Find first verb or inventory/look command word
            for i, token in enumerate(doc):
                if token.pos_ == "VERB" or token.text.lower() in ["inventory", "i", "look", "l", "examine", "ex"]:
                     first_action_token_index = i
                     break
            
            if first_action_token_index != -1:
                 potential_target_tokens = [token for token in doc if token.i > first_action_token_index and token.pos_ in ["NOUN", "PROPN", "ADJ", "DET"]]
                 if potential_target_tokens:
                      primary_target = " ".join([t.text for t in potential_target_tokens])
                      logging.debug(f"Primary target guessed from tokens after action word: '{primary_target}'")
            elif nouns: # If no clear action word, just take first noun chunk?
                 primary_target = nouns[0].text 
                 logging.debug(f"Primary target guessed from first noun: '{primary_target}'")

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
            logging.debug(f"Intent scores: {sorted_intents}")
            final_intent = sorted_intents[0][0]
        else:
            logging.warning("No possible intents identified after verb matching.")
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
                         logging.debug(f"Guessed action verb '{action_verb}' from matched intent keyword.")
                         break 

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
        
        # Build the final ParsedIntent - Ensure primary_target is included
        return ParsedIntent(
            intent=final_intent,
            action=action_verb, 
            target=primary_target, # Pass the identified target
            target_object_id=target_object_id,
            original_input=command_original_case # Pass original case input
        )
    
    # --- Unused methods removed --- 
    # _determine_intent 
    # _calculate_confidence 
    # process_command 
    # (and any related _process_... methods if they existed) 

# --- End of NLPCommandParser class --- 
    