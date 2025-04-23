# GUI for creating, editing, and deleting game objects. 

import FreeSimpleGUI as sg
import logging
import sys # Add sys import
import os  # Add os import
from pathlib import Path

# --- Add project root to Python path ---
# This allows importing modules from the 'engine' directory when running this script directly.
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent # Navigate up two levels (tools/object_editor -> tools -> project root)
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
# --- End path addition ---

# Now imports from engine should work
from object_data_manager import ObjectDataManager # Import our data manager
from engine.schemas import ObjectCategory, WearArea # IMPORT WEARAREA
from typing import Optional

# Basic logging setup
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Constants for GUI Element Keys ---
# Top Controls
KEY_OBJECT_DROPDOWN = "-OBJECT_ID_DROPDOWN-"
KEY_LOAD_BUTTON = "-LOAD_BUTTON-"
KEY_NEW_BUTTON = "-NEW_BUTTON-"
KEY_TOTAL_OBJECT_COUNT = "-TOTAL_OBJECT_COUNT-"

# Basic Info Frame
KEY_OBJECT_ID = "-OBJECT_ID-"
KEY_OBJECT_NAME = "-OBJECT_NAME-"
KEY_OBJECT_IS_PLURAL = "-OBJECT_IS_PLURAL-"
KEY_OBJECT_CATEGORY = "-OBJECT_CATEGORY-"
KEY_OBJECT_LOCATION = "-OBJECT_LOCATION-" # Room ID dropdown
KEY_OBJECT_AREA_LOCATION = "-OBJECT_AREA_LOCATION-"
KEY_OBJECT_COUNT = "-OBJECT_COUNT-"
KEY_OBJECT_WEIGHT = "-OBJECT_WEIGHT-"
KEY_OBJECT_SIZE = "-OBJECT_SIZE-"
KEY_OBJECT_DESCRIPTION = "-OBJECT_DESCRIPTION-"
KEY_OBJECT_SYNONYMS = "-OBJECT_SYNONYMS-"

# State & Lock Frame
KEY_OBJECT_INITIAL_STATE = "-OBJECT_INITIAL_STATE-" # is_visible in editor?
KEY_OBJECT_IS_LOCKED = "-OBJECT_IS_LOCKED-"
KEY_OBJECT_POWER_STATE = "-OBJECT_POWER_STATE-"
KEY_OBJECT_LOCK_TYPE = "-OBJECT_LOCK_TYPE-"
KEY_OBJECT_LOCK_CODE = "-OBJECT_LOCK_CODE-"
KEY_OBJECT_LOCK_KEY_ID = "-OBJECT_LOCK_KEY_ID-"

# --- Property Frame Keys ---
KEY_PROP_IS_TAKEABLE = "-PROP_IS_TAKEABLE-"
KEY_PROP_IS_INTERACTIVE = "-PROP_IS_INTERACTIVE-"
KEY_PROP_IS_DANGEROUS = "-PROP_IS_DANGEROUS-"
KEY_PROP_IS_DESTROYABLE = "-PROP_IS_DESTROYABLE-"
# KEY_PROP_IS_LOCKABLE = "-PROP_IS_LOCKABLE-" # Use state frame 'is_locked'
KEY_PROP_IS_STORAGE = "-PROP_IS_STORAGE-"
KEY_PROP_IS_OPERATIONAL = "-PROP_IS_OPERATIONAL-"
KEY_PROP_IS_EDIBLE = "-PROP_IS_EDIBLE-"
KEY_PROP_IS_WEAPON = "-PROP_IS_WEAPON-"
# KEY_PROP_WEIGHT = "-PROP_WEIGHT-" # Use basic info frame weight
# KEY_PROP_SIZE = "-PROP_SIZE-"     # Use basic info frame size
KEY_PROP_IS_MOVABLE = "-PROP_IS_MOVABLE-"
KEY_PROP_IS_WEARABLE = "-PROP_IS_WEARABLE-"
KEY_PROP_IS_FLAMMABLE = "-PROP_IS_FLAMMABLE-"
KEY_PROP_IS_TOXIC = "-PROP_IS_TOXIC-"
KEY_PROP_IS_FOOD = "-PROP_IS_FOOD-"
KEY_PROP_IS_COOKABLE = "-PROP_IS_COOKABLE-"
KEY_PROP_IS_CONSUMABLE = "-PROP_IS_CONSUMABLE-"
KEY_PROP_HAS_DURABILITY = "-PROP_HAS_DURABILITY-"
KEY_PROP_IS_HACKABLE = "-PROP_IS_HACKABLE-"
KEY_PROP_IS_HIDDEN = "-PROP_IS_HIDDEN-"
KEY_PROP_IS_RECHARGEABLE = "-PROP_IS_RECHARGEABLE-"
KEY_PROP_IS_FUEL_SOURCE = "-PROP_IS_FUEL_SOURCE-"
KEY_PROP_REGENERATES = "-PROP_REGENERATES-"
KEY_PROP_IS_MODULAR = "-PROP_IS_MODULAR-"
KEY_PROP_IS_STORED = "-PROP_IS_STORED-"
KEY_PROP_IS_TRANSFERABLE = "-PROP_IS_TRANSFERABLE-"
KEY_PROP_IS_ACTIVATABLE = "-PROP_IS_ACTIVATABLE-"
KEY_PROP_IS_NETWORKED = "-PROP_IS_NETWORKED-"
KEY_PROP_REQUIRES_POWER = "-PROP_REQUIRES_POWER-"
KEY_PROP_REQUIRES_ITEM = "-PROP_REQUIRES_ITEM-"
KEY_PROP_HAS_SECURITY = "-PROP_HAS_SECURITY-"
KEY_PROP_IS_SENSITIVE = "-PROP_IS_SENSITIVE-"
KEY_PROP_IS_FRAGILE = "-PROP_IS_FRAGILE-"
KEY_PROP_IS_SECRET = "-PROP_IS_SECRET-"
KEY_PROP_STORAGE_CAPACITY = "-PROP_STORAGE_CAPACITY-"
KEY_PROP_CAN_STORE_LIQUIDS = "-PROP_CAN_STORE_LIQUIDS-"
KEY_PROP_DAMAGE = "-PROP_DAMAGE-"
KEY_PROP_DURABILITY = "-PROP_DURABILITY-" # For weapons/items
KEY_PROP_RANGE = "-PROP_RANGE-"

# --- Interaction Frame Keys ---
KEY_INTERACTION_REQUIRED_STATE = "-INTERACTION_REQUIRED_STATE-"
KEY_INTERACTION_REQUIRED_ITEMS = "-INTERACTION_REQUIRED_ITEMS-"
KEY_INTERACTION_PRIMARY_ACTIONS = "-INTERACTION_PRIMARY_ACTIONS-"
KEY_INTERACTION_EFFECTS = "-INTERACTION_EFFECTS-"
KEY_INTERACTION_SUCCESS = "-INTERACTION_SUCCESS-"
KEY_INTERACTION_FAILURE = "-INTERACTION_FAILURE-"

# Other Frame
KEY_OBJECT_STORAGE_CONTENTS = "-OBJECT_STORAGE_CONTENTS-"
KEY_OBJECT_STATE_DESCRIPTIONS = "-OBJECT_STATE_DESCRIPTIONS-"
KEY_OBJECT_DIGITAL_CONTENT = "-OBJECT_DIGITAL_CONTENT-"

# Bottom Area
KEY_YAML_PREVIEW = "-YAML_PREVIEW-"
KEY_SAVE_BUTTON = "-SAVE_BUTTON-"
KEY_DELETE_BUTTON = "-DELETE_BUTTON-"
KEY_VALIDATE_BUTTON = "-VALIDATE_BUTTON-"
KEY_VALIDATE_INDICATOR = "-VALIDATE_INDICATOR-"
KEY_STATUS_BAR = "-STATUS_BAR-"
KEY_CLOSE_BUTTON = "-CLOSE-" # Explicit key for Close button

# --- New Keys for Wearability Frame ---
KEY_WEAR_AREA = "-WEAR_AREA-"
KEY_WEAR_LAYER = "-WEAR_LAYER-"

# --- New Keys for Surface and Charger ---
KEY_PROP_IS_SURFACE = '-PROP_IS_SURFACE-'
KEY_PROP_IS_CHARGER = '-PROP_IS_CHARGER-'

# --- Helper Functions ---
def get_object_categories() -> list[str]:
    """Returns a list of ObjectCategory enum values."""
    return [category.value for category in ObjectCategory]

def _parse_list_to_csv(data_list: list) -> str:
    """Converts a list to a comma-separated string."""
    return ", ".join(str(item) for item in data_list) if data_list else ""

def _parse_dict_to_multiline(data_dict: dict) -> str:
    """Converts a dict to key:value lines."""
    return "\n".join(f"{k}:{v}" for k, v in data_dict.items()) if data_dict else ""

# --- NEW HELPER FUNCTIONS for Digital Content ---
def _parse_multiline_to_digital_content(multiline_string: str) -> dict:
    """Converts structured multiline text to a digital content dictionary."""
    content_dict = {}
    if not multiline_string or not isinstance(multiline_string, str):
        return content_dict
    
    current_file_key = None
    current_content_lines = []
    
    lines = multiline_string.splitlines()
    
    for i, line in enumerate(lines):
        # Check for separator or end of input
        is_separator = (line.strip() == '---')
        is_last_line = (i == len(lines) - 1)

        if is_separator or is_last_line:
            if current_file_key:
                # Add content for the previous file
                if is_last_line and not is_separator:
                     current_content_lines.append(line) # Include last line if not separator
                content_dict[current_file_key] = '\n'.join(current_content_lines).strip()
                current_file_key = None
                current_content_lines = []
            continue # Skip the separator line itself

        # Check for new file key (key: value format on the first line of a block)
        if current_file_key is None and ':' in line:
            key, first_line_content = line.split(':', 1)
            current_file_key = key.strip()
            if current_file_key: # Ensure key is not empty
                 current_content_lines.append(first_line_content.strip()) 
            else: # Malformed line, treat as content for potential previous block?
                 current_content_lines.append(line)
                 current_file_key = None # Reset key
        elif current_file_key is not None:
            # Append content line to the current file
            current_content_lines.append(line)
        else:
             # Line before any key is defined, ignore? Or log warning?
             logging.warning(f"Ignoring line outside of file block: {line}")
             pass 

    return content_dict

def _parse_digital_content_to_multiline(data_dict: Optional[dict]) -> str:
    """Converts a digital content dictionary to structured multiline text."""
    if not data_dict:
        return ""
    
    output_lines = []
    first_item = True
    for key, value in data_dict.items():
        if not first_item:
            output_lines.append("---") # Separator between files
        output_lines.append(f"{key}: {value}")
        first_item = False
        
    return "\n".join(output_lines)
# --- END NEW HELPER FUNCTIONS ---

def clear_fields(window):
    """Clears all input fields and resets controls to default for a NEW object."""
    logging.debug("Clearing all fields for new object.")
    # Basic Info
    window[KEY_OBJECT_ID].update("", disabled=False) # Enable ID for new
    window[KEY_OBJECT_NAME].update("")
    window[KEY_OBJECT_IS_PLURAL].update(False)
    window[KEY_OBJECT_CATEGORY].update("")
    window[KEY_OBJECT_LOCATION].update("")
    window[KEY_OBJECT_AREA_LOCATION].update(values=[], value=None) # Clear area selection

    # Set Count field to indicate automatic assignment for new objects
    window[KEY_OBJECT_COUNT].update("(Auto)") # Indicate automatic count

    # State & Lock
    window[KEY_OBJECT_INITIAL_STATE].update(True)
    window[KEY_OBJECT_IS_LOCKED].update(False)
    window[KEY_OBJECT_POWER_STATE].update("")
    window[KEY_OBJECT_LOCK_TYPE].update("")
    window[KEY_OBJECT_LOCK_CODE].update("")
    window[KEY_OBJECT_LOCK_KEY_ID].update("")

    # Properties (Checkboxes reset to default, inputs cleared)
    props = window.AllKeysDict # Get all keys
    for key in props:
        # --- Add check for string type ---
        if isinstance(key, str):
            if key.startswith("-PROP_") and isinstance(window[key], sg.Checkbox):
                 # Reset checkboxes based on their default definition in layout (tricky, easier to list common ones)
                 if key in [KEY_PROP_IS_INTERACTIVE]: # Default True properties
                     window[key].update(True)
                 else: # Most properties default False
                     window[key].update(False)
            elif key.startswith("-PROP_") and isinstance(window[key], sg.Input):
                window[key].update("") # Clear property inputs like capacity, damage

    # Interaction (Inputs cleared)
    window[KEY_INTERACTION_REQUIRED_STATE].update("")
    window[KEY_INTERACTION_REQUIRED_ITEMS].update("")
    window[KEY_INTERACTION_PRIMARY_ACTIONS].update("")
    window[KEY_INTERACTION_EFFECTS].update("")
    window[KEY_INTERACTION_SUCCESS].update("")
    window[KEY_INTERACTION_FAILURE].update("")

    # Other
    window[KEY_OBJECT_STORAGE_CONTENTS].update("")
    window[KEY_OBJECT_STATE_DESCRIPTIONS].update("")
    window[KEY_OBJECT_DIGITAL_CONTENT].update("")

    # Clear Wearability Frame (keep fields enabled)
    window[KEY_WEAR_AREA].update(value='') # No disabled=True
    window[KEY_WEAR_LAYER].update(value='') # No disabled=True

    # Reset Wearable Checkbox
    window[KEY_PROP_IS_WEARABLE].update(False)

    # YAML Preview
    window[KEY_YAML_PREVIEW].update("")

    # Set focus to ID field for new object
    window[KEY_OBJECT_ID].set_focus(True)
    # Reset validation indicator
    window[KEY_VALIDATE_INDICATOR].update("❓", text_color='grey')
    window[KEY_STATUS_BAR].update("Enter details for new object.")

def populate_fields(window, object_data: dict, manager: ObjectDataManager):
    """Populates GUI fields from the loaded object_data dictionary."""
    if not object_data:
        logging.warning("populate_fields called with empty object_data.")
        clear_fields(window) # Clear fields if no data
        return

    object_id = object_data.get('id')
    logging.debug(f"Populating fields for object ID: {object_id}")

    # --- No need to call clear_fields here anymore, clearing happens on NEW ---

    # --- Get nested dictionaries safely ---
    properties = object_data.get('properties', {}) or {} # Ensure dict
    interaction = object_data.get('interaction', {}) or {} # Ensure dict

    # --- Basic Info ---
    window[KEY_OBJECT_ID].update(object_id)
    window[KEY_OBJECT_ID].update(disabled=True) # Disable ID for existing object
    window[KEY_OBJECT_NAME].update(object_data.get('name', ''))
    window[KEY_OBJECT_IS_PLURAL].update(object_data.get('is_plural', False))
    window[KEY_OBJECT_CATEGORY].update(object_data.get('category', ''))

    # Populate Count field with the actual count from data for existing objects
    window[KEY_OBJECT_COUNT].update(str(object_data.get('count', ''))) # Display existing count

    # Find and set location
    found_room_id, found_area_id = manager.find_object_location(object_id)
    logging.debug(f"find_object_location returned: room='{found_room_id}', area='{found_area_id}'") # DEBUG LOG
    window[KEY_OBJECT_LOCATION].update(value=found_room_id)

    # Update area dropdown based on found room
    area_ids = []
    if found_room_id:
        area_ids = manager.get_area_ids_for_room(found_room_id)
    # Workaround: Ensure list is not empty to prevent shrinking
    display_area_ids = area_ids if area_ids else ['']
    # Explicitly set readonly and size during update
    window[KEY_OBJECT_AREA_LOCATION].update(values=display_area_ids, value=found_area_id, readonly=True, size=(30,1))

    window[KEY_OBJECT_WEIGHT].update(str(object_data.get('weight', 1.0)))
    window[KEY_OBJECT_SIZE].update(str(object_data.get('size', 1.0)))
    window[KEY_OBJECT_DESCRIPTION].update(object_data.get('description', ''))
    window[KEY_OBJECT_SYNONYMS].update(_parse_list_to_csv(object_data.get('synonyms', [])))

    # --- State & Lock ---
    window[KEY_OBJECT_INITIAL_STATE].update(object_data.get('initial_state', True)) # Note: Schema name vs Checkbox text
    window[KEY_OBJECT_IS_LOCKED].update(object_data.get('is_locked', False))
    window[KEY_OBJECT_POWER_STATE].update(object_data.get('power_state', '') or '') # Ensure empty string if None
    window[KEY_OBJECT_LOCK_TYPE].update(object_data.get('lock_type', '') or '')
    window[KEY_OBJECT_LOCK_CODE].update(object_data.get('lock_code', '') or '')
    window[KEY_OBJECT_LOCK_KEY_ID].update(object_data.get('lock_key_id', '') or '')

    # --- Properties ---
    # Booleans
    window[KEY_PROP_IS_TAKEABLE].update(properties.get('is_takeable', False))
    window[KEY_PROP_IS_INTERACTIVE].update(properties.get('is_interactive', True))
    window[KEY_PROP_IS_DANGEROUS].update(properties.get('is_dangerous', False))
    window[KEY_PROP_IS_DESTROYABLE].update(properties.get('is_destroyable', False))
    window[KEY_PROP_IS_STORAGE].update(properties.get('is_storage', False))
    window[KEY_PROP_IS_OPERATIONAL].update(properties.get('is_operational', False))
    window[KEY_PROP_IS_EDIBLE].update(properties.get('is_edible', False))
    window[KEY_PROP_IS_WEAPON].update(properties.get('is_weapon', False))
    window[KEY_PROP_IS_MOVABLE].update(properties.get('is_movable', False))
    window[KEY_PROP_IS_WEARABLE].update(properties.get('is_wearable', False))
    window[KEY_PROP_IS_FLAMMABLE].update(properties.get('is_flammable', False))
    window[KEY_PROP_IS_TOXIC].update(properties.get('is_toxic', False))
    window[KEY_PROP_IS_FOOD].update(properties.get('is_food', False))
    window[KEY_PROP_IS_COOKABLE].update(properties.get('is_cookable', False))
    window[KEY_PROP_IS_CONSUMABLE].update(properties.get('is_consumable', False))
    window[KEY_PROP_HAS_DURABILITY].update(properties.get('has_durability', False))
    window[KEY_PROP_IS_HACKABLE].update(properties.get('is_hackable', False))
    window[KEY_PROP_IS_HIDDEN].update(properties.get('is_hidden', False))
    window[KEY_PROP_IS_RECHARGEABLE].update(properties.get('is_rechargeable', False))
    window[KEY_PROP_IS_FUEL_SOURCE].update(properties.get('is_fuel_source', False))
    window[KEY_PROP_REGENERATES].update(properties.get('regenerates', False))
    window[KEY_PROP_IS_MODULAR].update(properties.get('is_modular', False))
    window[KEY_PROP_IS_STORED].update(properties.get('is_stored', False))
    window[KEY_PROP_IS_TRANSFERABLE].update(properties.get('is_transferable', False))
    window[KEY_PROP_IS_ACTIVATABLE].update(properties.get('is_activatable', False))
    window[KEY_PROP_IS_NETWORKED].update(properties.get('is_networked', False))
    window[KEY_PROP_REQUIRES_POWER].update(properties.get('requires_power', False))
    window[KEY_PROP_REQUIRES_ITEM].update(properties.get('requires_item', False))
    window[KEY_PROP_HAS_SECURITY].update(properties.get('has_security', False))
    window[KEY_PROP_IS_SENSITIVE].update(properties.get('is_sensitive', False))
    window[KEY_PROP_IS_FRAGILE].update(properties.get('is_fragile', False))
    window[KEY_PROP_IS_SECRET].update(properties.get('is_secret', False))
    window[KEY_PROP_CAN_STORE_LIQUIDS].update(properties.get('can_store_liquids', False))
    window[KEY_PROP_IS_SURFACE].update(properties.get('is_surface', False))
    window[KEY_PROP_IS_CHARGER].update(properties.get('is_charger', False))
    # Numeric/String Properties
    window[KEY_PROP_STORAGE_CAPACITY].update(str(properties.get('storage_capacity', '')) if properties.get('storage_capacity') is not None else '')
    window[KEY_PROP_DAMAGE].update(str(properties.get('damage', '')) if properties.get('damage') is not None else '')
    window[KEY_PROP_DURABILITY].update(str(properties.get('durability', '')) if properties.get('durability') is not None else '')
    window[KEY_PROP_RANGE].update(str(properties.get('range', '')) if properties.get('range') is not None else '')

    # Populate Wearability Frame (keep fields enabled)
    wear_area_val = properties.get('wear_area', '')
    wear_layer_val = properties.get('wear_layer', None)

    window[KEY_WEAR_AREA].update(value=wear_area_val) # No disabled update
    layer_str = str(wear_layer_val) if wear_layer_val is not None else ''
    window[KEY_WEAR_LAYER].update(value=layer_str) # No disabled update

    # Ensure the wearable checkbox itself is updated too
    window[KEY_PROP_IS_WEARABLE].update(properties.get('is_wearable', False))

    # --- Interaction ---
    window[KEY_INTERACTION_REQUIRED_STATE].update(_parse_list_to_csv(interaction.get('required_state', [])))
    window[KEY_INTERACTION_REQUIRED_ITEMS].update(_parse_list_to_csv(interaction.get('required_items', [])))
    window[KEY_INTERACTION_PRIMARY_ACTIONS].update(_parse_list_to_csv(interaction.get('primary_actions', [])))
    window[KEY_INTERACTION_EFFECTS].update(_parse_list_to_csv(interaction.get('effects', [])))
    window[KEY_INTERACTION_SUCCESS].update(interaction.get('success_message', '') or '')
    window[KEY_INTERACTION_FAILURE].update(interaction.get('failure_message', '') or '')

    # --- Other ---
    window[KEY_OBJECT_STORAGE_CONTENTS].update(_parse_list_to_csv(object_data.get('storage_contents', [])))
    window[KEY_OBJECT_STATE_DESCRIPTIONS].update(_parse_dict_to_multiline(object_data.get('state_descriptions', {})))
    window[KEY_OBJECT_DIGITAL_CONTENT].update(_parse_digital_content_to_multiline(object_data.get('digital_content', {})))

    logging.debug("Finished populating fields.")
    # Update the YAML preview after populating, passing the manager
    update_yaml_preview(window, object_data, manager) # Pass manager here

def update_yaml_preview(window, object_data: Optional[dict], manager: ObjectDataManager):
    """Updates the YAML preview pane with the object's data."""
    if not object_data:
        window[KEY_YAML_PREVIEW].update("")
        return

    from io import StringIO
    string_stream = StringIO()
    # Dump only the single object - might need refinement if order matters strictly
    # or to show context, but good start.
    try:
        manager.yaml.dump([object_data], string_stream) # Dump as a list containing the dict
        preview_text = string_stream.getvalue()
        # Remove the list indicator '-' at the start if present
        if preview_text.startswith('- '):
             preview_text = preview_text[2:]
        window[KEY_YAML_PREVIEW].update(preview_text)
        logging.debug("Updated YAML preview.")
    except Exception as e:
        logging.error(f"Error generating YAML preview: {e}")
        window[KEY_YAML_PREVIEW].update(f"# Error generating preview:\n# {e}")

def _parse_csv_to_list(csv_string: str) -> list:
    """Converts a comma-separated string to a list of stripped strings."""
    if not csv_string or not isinstance(csv_string, str):
        return []
    return [item.strip() for item in csv_string.split(',') if item.strip()]

def _parse_multiline_to_dict(multiline_string: str) -> dict:
    """Converts key:value lines to a dictionary."""
    data_dict = {}
    if not multiline_string or not isinstance(multiline_string, str):
        return data_dict
    for line in multiline_string.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            data_dict[key.strip()] = value.strip()
    return data_dict

def gather_data_from_fields(window: sg.Window, manager: ObjectDataManager) -> tuple[Optional[dict], Optional[str], Optional[str]]:
    """Gathers data from GUI fields into a dictionary matching YAML structure, plus location."""
    values = window.read(timeout=0)[1] # Get current values without blocking
    gathered_data = {}
    properties = {}
    interaction = {}
    error = None

    try:
        # --- Basic Info ---
        object_id = values[KEY_OBJECT_ID].strip().lower()
        if not object_id:
            raise ValueError("Object ID cannot be empty.")
        gathered_data['id'] = object_id

        is_new_object = not window[KEY_OBJECT_ID].Disabled # Check if ID field is enabled

        # Handle Count based on whether it's new or existing
        if is_new_object:
            gathered_data['count'] = manager.get_object_count() + 1
            logging.info(f"Assigning automatic count {gathered_data['count']} for new object '{object_id}'.")
        else:
            # For existing, read the value populated in the read-only field
            count_str = window[KEY_OBJECT_COUNT].get()
            gathered_data['count'] = int(count_str) if count_str and count_str.isdigit() else 0 # Use 0 if invalid

        gathered_data['name'] = values[KEY_OBJECT_NAME].strip() or object_id
        gathered_data['is_plural'] = values[KEY_OBJECT_IS_PLURAL]
        gathered_data['category'] = values[KEY_OBJECT_CATEGORY] or None
        gathered_data['weight'] = float(values[KEY_OBJECT_WEIGHT] or 1.0)
        gathered_data['size'] = float(values[KEY_OBJECT_SIZE] or 1.0)
        gathered_data['description'] = values[KEY_OBJECT_DESCRIPTION].strip()
        gathered_data['synonyms'] = _parse_csv_to_list(values[KEY_OBJECT_SYNONYMS])

        # --- State & Lock ---
        gathered_data['initial_state'] = values[KEY_OBJECT_INITIAL_STATE]
        gathered_data['is_locked'] = values[KEY_OBJECT_IS_LOCKED]
        gathered_data['power_state'] = values[KEY_OBJECT_POWER_STATE] or None
        gathered_data['lock_type'] = values[KEY_OBJECT_LOCK_TYPE] or None
        gathered_data['lock_code'] = values[KEY_OBJECT_LOCK_CODE] or None
        gathered_data['lock_key_id'] = values[KEY_OBJECT_LOCK_KEY_ID] or None

        # --- Properties ---
        # (Gather boolean properties)
        properties['is_takeable'] = values[KEY_PROP_IS_TAKEABLE]
        properties['is_interactive'] = values[KEY_PROP_IS_INTERACTIVE]
        properties['is_dangerous'] = values[KEY_PROP_IS_DANGEROUS]
        properties['is_destroyable'] = values[KEY_PROP_IS_DESTROYABLE]
        properties['is_storage'] = values[KEY_PROP_IS_STORAGE]
        properties['is_operational'] = values[KEY_PROP_IS_OPERATIONAL]
        properties['is_edible'] = values[KEY_PROP_IS_EDIBLE]
        properties['is_weapon'] = values[KEY_PROP_IS_WEAPON]
        properties['is_movable'] = values[KEY_PROP_IS_MOVABLE]
        properties['is_wearable'] = values[KEY_PROP_IS_WEARABLE]
        properties['is_flammable'] = values[KEY_PROP_IS_FLAMMABLE]
        properties['is_toxic'] = values[KEY_PROP_IS_TOXIC]
        properties['is_food'] = values[KEY_PROP_IS_FOOD]
        properties['is_cookable'] = values[KEY_PROP_IS_COOKABLE]
        properties['is_consumable'] = values[KEY_PROP_IS_CONSUMABLE]
        properties['has_durability'] = values[KEY_PROP_HAS_DURABILITY]
        properties['is_hackable'] = values[KEY_PROP_IS_HACKABLE]
        properties['is_hidden'] = values[KEY_PROP_IS_HIDDEN]
        properties['is_rechargeable'] = values[KEY_PROP_IS_RECHARGEABLE]
        properties['is_fuel_source'] = values[KEY_PROP_IS_FUEL_SOURCE]
        properties['regenerates'] = values[KEY_PROP_REGENERATES]
        properties['is_modular'] = values[KEY_PROP_IS_MODULAR]
        properties['is_stored'] = values[KEY_PROP_IS_STORED]
        properties['is_transferable'] = values[KEY_PROP_IS_TRANSFERABLE]
        properties['is_activatable'] = values[KEY_PROP_IS_ACTIVATABLE]
        properties['is_networked'] = values[KEY_PROP_IS_NETWORKED]
        properties['requires_power'] = values[KEY_PROP_REQUIRES_POWER]
        properties['requires_item'] = values[KEY_PROP_REQUIRES_ITEM]
        properties['has_security'] = values[KEY_PROP_HAS_SECURITY]
        properties['is_sensitive'] = values[KEY_PROP_IS_SENSITIVE]
        properties['is_fragile'] = values[KEY_PROP_IS_FRAGILE]
        properties['is_secret'] = values[KEY_PROP_IS_SECRET]
        properties['can_store_liquids'] = values[KEY_PROP_CAN_STORE_LIQUIDS]
        properties['is_surface'] = values[KEY_PROP_IS_SURFACE]
        properties['is_charger'] = values[KEY_PROP_IS_CHARGER]
        
        # (Gather numeric/string properties)
        try:
            capacity_str = values[KEY_PROP_STORAGE_CAPACITY].strip()
            properties['storage_capacity'] = int(capacity_str) if capacity_str else None
        except ValueError:
            raise ValueError("Storage Capacity must be a whole number.")
            
        try:
            damage_str = values[KEY_PROP_DAMAGE].strip()
            properties['damage'] = int(damage_str) if damage_str else None
        except ValueError:
            raise ValueError("Damage must be a whole number.")
            
        try:
            durability_str = values[KEY_PROP_DURABILITY].strip()
            properties['durability'] = int(durability_str) if durability_str else None
        except ValueError:
            raise ValueError("Durability must be a whole number.")
        
        try:
            range_str = values[KEY_PROP_RANGE].strip()
            properties['range'] = int(range_str) if range_str else None # Assuming range is numeric for now
        except ValueError:
            raise ValueError("Range must be a whole number.")

        # (Gather wearability properties)
        if properties['is_wearable']:
            properties['wear_area'] = values[KEY_WEAR_AREA] or None
            try:
                layer_str = values[KEY_WEAR_LAYER].strip()
                properties['wear_layer'] = int(layer_str) if layer_str else None
            except ValueError:
                raise ValueError("Wear Layer must be a whole number.")
        else:
            properties.pop('wear_area', None) # Remove if not wearable
            properties.pop('wear_layer', None)

        if properties: # Only add properties key if there's data
             gathered_data['properties'] = properties

        # --- Interaction ---
        interaction['required_state'] = _parse_csv_to_list(values[KEY_INTERACTION_REQUIRED_STATE])
        interaction['failure_message'] = values[KEY_INTERACTION_FAILURE] or None
        if any(interaction.values()): # Only add interaction key if there's data
             gathered_data['interaction'] = interaction

        # --- Other --- (storage_contents, state_descriptions, digital_content)
        gathered_data['storage_contents'] = _parse_csv_to_list(values[KEY_OBJECT_STORAGE_CONTENTS])
        gathered_data['state_descriptions'] = _parse_multiline_to_dict(values[KEY_OBJECT_STATE_DESCRIPTIONS])
        gathered_data['digital_content'] = _parse_multiline_to_digital_content(values[KEY_OBJECT_DIGITAL_CONTENT])

        # --- Location Data (Returned separately) ---
        location_room_id = values.get(KEY_OBJECT_LOCATION) or None
        location_area_id = values.get(KEY_OBJECT_AREA_LOCATION) or None

        # Clean final data - remove keys with None value if desired
        # Optional: Depends on schema strictness
        # gathered_data = {k: v for k, v in gathered_data.items() if v is not None}
        # if 'properties' in gathered_data: gathered_data['properties'] = {k: v for k, v in gathered_data['properties'].items() if v is not None}
        # if 'interaction' in gathered_data: gathered_data['interaction'] = {k: v for k, v in gathered_data['interaction'].items() if v is not None}

        return gathered_data, location_room_id, location_area_id

    except ValueError as e:
        error = f"Invalid input value: {e}"
    except Exception as e:
        error = f"Unexpected error gathering data: {e}"
        logging.exception("Error in gather_data_from_fields")

    # If error occurred
    sg.popup_error(error, title="Data Input Error")
    return None, None, None # Indicate failure

def validate_object_data(object_data: dict, is_new: bool, manager: ObjectDataManager) -> list[str]:
    """Performs validation checks. Returns list of errors."""
    errors = []
    if not object_data:
        return ["No data gathered."]

    # Required fields
    if not object_data.get('id'):
        errors.append("Object ID is required.")
    elif is_new and object_data['id'] in manager.get_object_ids():
        errors.append(f"Object ID '{object_data['id']}' already exists.")
    if not object_data.get('name'):
        errors.append("Name is required.")
    if not object_data.get('category'):
        errors.append("Category is required.")
    if not object_data.get('description'):
        errors.append("Description is required.")

    # --- Add Weight and Size Range Checks ---
    weight = object_data.get('weight')
    size = object_data.get('size') # Should be float/int after gather_data

    # Weight Check
    if weight is not None:
        try:
            w = float(weight) # Ensure it's treated as number
            if not (0.01 <= w <= 250.0):
                 errors.append(f"Weight ({w}) must be between 0.01 and 250.0 kg.")
        except (ValueError, TypeError):
             errors.append(f"Weight must be a valid number (e.g., 1.0, 0.5). Got: '{weight}'")

    # Size Check
    if size is not None:
        try:
            s = float(size) # Allow float input, check range based on int logic
            if not (1 <= s <= 50):
                 errors.append(f"Size ({s}) must be between 1 and 50.")
            # Optional: Check if it's reasonably an integer if needed?
            # if s != int(s): errors.append("Size should ideally be a whole number.")
        except (ValueError, TypeError):
             errors.append(f"Size must be a valid number (e.g., 1, 5, 25). Got: '{size}'")
    # --- End Range Checks ---

    # --- Validate Wearability ---
    properties = object_data.get('properties', {})
    is_wearable_prop = properties.get('is_wearable', False)
    wear_area_prop = properties.get('wear_area')
    wear_layer_prop = properties.get('wear_layer')

    # Check 1: If wearable, must have area. Layer must be valid if present.
    if is_wearable_prop:
        if not wear_area_prop:
            errors.append("Wearable items must have a 'Wear Area' selected.")
        if wear_layer_prop is not None:
             try:
                 layer = int(wear_layer_prop)
                 if not (1 <= layer <= 10):
                      errors.append("Wear Layer must be between 1 and 10.")
             except (ValueError, TypeError):
                  errors.append("Wear Layer must be a whole number.")

    # Check 2: If area or layer is set, must be wearable.
    if (wear_area_prop or wear_layer_prop is not None) and not is_wearable_prop:
        errors.append("Wear Area/Layer is set, but 'Wearable' property is not checked.")

    # --- Validate other numeric properties (Capacity, Damage, Durability, Range) ---
    # ... (existing validation for these) ...

    return errors

# --- Main Application ---
def main():
    """Main function to create and run the Object Editor GUI."""
    # --- Data Initialization ---
    # Create an instance of the data manager (adjust path if needed)
    # Assuming the script runs from 'tools/object_editor'
    data_dir = Path(__file__).resolve().parent.parent / "data" # Corrected path assumption
    manager = ObjectDataManager(data_dir=data_dir)

    # Get initial data for dropdowns
    object_ids = manager.get_object_ids()
    room_ids = manager.get_room_ids()
    area_ids = [] # Initially empty, populated when a room is selected
    categories = get_object_categories()
    wear_areas = [area.value for area in WearArea]

    sg.theme("DarkGrey2") # Use a theme

# === START OF NEW LAYOUT CODE ===

    # --- Persistent Top Controls Layout ---
    top_controls_layout = [
        sg.Text("Select Object:"),
        sg.Combo(object_ids, key=KEY_OBJECT_DROPDOWN, size=(30, 1), enable_events=True, readonly=True, tooltip="Select an existing object ID to load its data."),
        # sg.Button("Load", key=KEY_LOAD_BUTTON, tooltip="Load the selected object's data into the editor."), # Load is triggered by Combo change
        sg.Button("New Object", key=KEY_NEW_BUTTON, tooltip="Clear all fields to create a new object definition."),
        sg.Text(f"Total Objects: {len(object_ids)}", key=KEY_TOTAL_OBJECT_COUNT, size=(15,1), justification='right')
    ]

    # --- Tab Layout Definitions ---

    # Tab 1: Basic Info
    basic_info_layout = [
        [sg.Text("Object ID:", size=(15,1)), sg.Input(key=KEY_OBJECT_ID, size=(40, 1), disabled=True, tooltip="Unique internal ID (lowercase_snake_case).\nCannot be changed after saving.")],
        [sg.Text("Name:", size=(15,1)), sg.Input(key=KEY_OBJECT_NAME, size=(40, 1), tooltip="User-friendly name displayed in the game.")],
        [sg.Text("Category:", size=(15,1)), sg.Combo(categories, key=KEY_OBJECT_CATEGORY, size=(20, 1), readonly=True, tooltip="Broad classification for the object.")],
        [sg.Text("Is Plural:", size=(15,1)), sg.Checkbox("", key=KEY_OBJECT_IS_PLURAL, default=False, tooltip="Check if the object name represents a plural entity (e.g., 'boots').\nAffects some output messages.")],
        [sg.Text("Description:", size=(15,1)), sg.Multiline(key=KEY_OBJECT_DESCRIPTION, size=(60, 5), tooltip="Detailed text shown when the player examines the object.")],
        [sg.Text("Synonyms:", size=(15,1)), sg.Input(key=KEY_OBJECT_SYNONYMS, size=(60, 1), tooltip="Comma-separated list of alternative names players might use.")],
        [sg.Text("Weight (kg):", size=(15,1)), sg.Input(key=KEY_OBJECT_WEIGHT, size=(10, 1), tooltip="Object's weight (0.01-250.0).\nAffects inventory and movability.")],
        [sg.Text("Size (1-50):", size=(15,1)), sg.Input(key=KEY_OBJECT_SIZE, size=(10, 1), tooltip="Abstract size rating (1-50).\n1-25=Takeable, 26-49=Movable, 50=Fixed.")],
        [sg.Text("Count:", size=(15,1)), sg.Input(key=KEY_OBJECT_COUNT, size=(10, 1), tooltip="Number of instances of this object at this location (usually 1).\nSet to '(Auto)' for new objects.")]
    ]
    basic_info_tab = sg.Tab('Basic Info', basic_info_layout, key='-TAB_BASIC_INFO-')

    # Tab 2: Location
    location_layout = [
        [sg.Text("Room Location:", size=(15,1)), sg.Combo(room_ids, key=KEY_OBJECT_LOCATION, size=(30, 1), enable_events=True, readonly=True, tooltip="The room_id where this object is located.")],
        [sg.Text("Area Location:", size=(15,1)), sg.Combo(area_ids, key=KEY_OBJECT_AREA_LOCATION, size=(30, 1), readonly=True, tooltip="Optional area_id within the room where the object is located.")]
    ]
    location_tab = sg.Tab('Location', location_layout, key='-TAB_LOCATION-')

    # Tab 3: State & Locking
    state_lock_layout = [
        [sg.Checkbox("Visible Initially", key=KEY_OBJECT_INITIAL_STATE, default=True, tooltip="Is the object visible immediately upon entering the location?\n(Uncheck for hidden/contained items).")],
        [sg.Checkbox("Is Locked", key=KEY_OBJECT_IS_LOCKED, default=False, tooltip="Does the object start locked, requiring an action to unlock?")],
        [sg.Text("Lock Type:", size=(15,1)), sg.Combo(['', 'key', 'code', 'biometric'], key=KEY_OBJECT_LOCK_TYPE, size=(15, 1), readonly=True, tooltip="Mechanism required to unlock (if 'Is Locked' is checked).")],
        [sg.Text("Lock Code:", size=(15,1)), sg.Input(key=KEY_OBJECT_LOCK_CODE, size=(20, 1), tooltip="The specific code required if Lock Type is 'code'.")],
        [sg.Text("Lock Key ID:", size=(15,1)), sg.Input(key=KEY_OBJECT_LOCK_KEY_ID, size=(30, 1), tooltip="The object_id of the key item required if Lock Type is 'key'.")],
        [sg.Text("Power State:", size=(15,1)), sg.Combo(['', 'offline', 'emergency', 'main_power', 'torch_light'], key=KEY_OBJECT_POWER_STATE, size=(15, 1), readonly=True, tooltip="Object's functional state based on power conditions\n(affects descriptions/interactions).")],
        [sg.Checkbox("Is Operational", key=KEY_PROP_IS_OPERATIONAL, default=True, tooltip="Is the device/tool currently functional (independent of power,\nunless Requires Power is also checked)?")]
    ]
    state_lock_tab = sg.Tab('State & Locking', state_lock_layout, key='-TAB_STATE_LOCK-')

    # Tab 4: Properties (General)
    # Use columns for better organization
    props_col1 = [
        [sg.Checkbox("Takeable", key=KEY_PROP_IS_TAKEABLE, default=False, tooltip="Can the player pick this up and put it in inventory?")],
        [sg.Checkbox("Interactive", key=KEY_PROP_IS_INTERACTIVE, default=True, tooltip="Can the player interact with this beyond just looking?")],
        [sg.Checkbox("Dangerous", key=KEY_PROP_IS_DANGEROUS, default=False, tooltip="Does interacting with this pose a threat?")],
        [sg.Checkbox("Destroyable", key=KEY_PROP_IS_DESTROYABLE, default=False, tooltip="Can this object be destroyed by player actions?")],
        [sg.Checkbox("Movable", key=KEY_PROP_IS_MOVABLE, default=False, tooltip="Can the player push/pull this object?")],
        [sg.Checkbox("Flammable", key=KEY_PROP_IS_FLAMMABLE, default=False, tooltip="Can this object be set on fire?")],
        [sg.Checkbox("Toxic", key=KEY_PROP_IS_TOXIC, default=False, tooltip="Is this object poisonous or harmful if ingested/touched?")],
        [sg.Checkbox("Requires Power", key=KEY_PROP_REQUIRES_POWER, default=False, tooltip="Does this object need power to function?")]
    ]
    props_col2 = [
        [sg.Checkbox("Has Durability", key=KEY_PROP_HAS_DURABILITY, default=False, tooltip="Does this item have a durability value that degrades?")],
        [sg.Checkbox("Hackable", key=KEY_PROP_IS_HACKABLE, default=False, tooltip="Can the player attempt to hack this device?")],
        [sg.Checkbox("Hidden", key=KEY_PROP_IS_HIDDEN, default=False, tooltip="Is this property difficult to discern initially?\n(Affects examine text)")],
        [sg.Checkbox("Rechargeable", key=KEY_PROP_IS_RECHARGEABLE, default=False, tooltip="Can this item be recharged (e.g., battery)?")],
        [sg.Checkbox("Is Fuel Source", key=KEY_PROP_IS_FUEL_SOURCE, default=False, tooltip="Can this item be used as fuel?")],
        [sg.Checkbox("Regenerates", key=KEY_PROP_REGENERATES, default=False, tooltip="Does this object replenish itself over time?")],
        [sg.Checkbox("Modular", key=KEY_PROP_IS_MODULAR, default=False, tooltip="Can this object accept or be part of modifications?")],
        [sg.Checkbox("Is Surface", key=KEY_PROP_IS_SURFACE, default=False, tooltip="Does this object provide a surface to place items on?")]
    ]
    props_col3 = [
        [sg.Checkbox("Transferable", key=KEY_PROP_IS_TRANSFERABLE, default=False, tooltip="Can this be transferred (e.g., data, power)?")],
        [sg.Checkbox("Activatable", key=KEY_PROP_IS_ACTIVATABLE, default=False, tooltip="Can this be activated/deactivated (e.g., a switch)?")],
        [sg.Checkbox("Networked", key=KEY_PROP_IS_NETWORKED, default=False, tooltip="Is this object part of a network?")],
        [sg.Checkbox("Requires Item", key=KEY_PROP_REQUIRES_ITEM, default=False, tooltip="Does using this object require another specific item?")],
        [sg.Checkbox("Has Security", key=KEY_PROP_HAS_SECURITY, default=False, tooltip="Does this object have security measures?")],
        [sg.Checkbox("Sensitive", key=KEY_PROP_IS_SENSITIVE, default=False, tooltip="Is this object sensitive to environmental conditions?")],
        [sg.Checkbox("Fragile", key=KEY_PROP_IS_FRAGILE, default=False, tooltip="Is this object easily broken?")],
        [sg.Checkbox("Secret", key=KEY_PROP_IS_SECRET, default=False, tooltip="Does this object contain a secret or hidden feature?")],
        [sg.Checkbox("Is Charger", key=KEY_PROP_IS_CHARGER, default=False, tooltip="Can this object charge other items?")]
        # Removed KEY_PROP_IS_STORED as it seemed redundant/unclear
    ]
    properties_layout = [[sg.Column(props_col1), sg.VSeperator(), sg.Column(props_col2), sg.VSeperator(), sg.Column(props_col3)]]
    properties_tab = sg.Tab('Properties', properties_layout, key='-TAB_PROPERTIES-')

    # Tab 5: Container
    container_layout = [
        [sg.Checkbox("Is Storage Container", key=KEY_PROP_IS_STORAGE, default=False, tooltip="Can this object hold other items?")],
        [sg.Text("Storage Capacity:", size=(15,1)), sg.Input(key=KEY_PROP_STORAGE_CAPACITY, size=(10, 1), tooltip="Maximum number or volume of items it can hold (optional).")],
        [sg.Checkbox("Can Store Liquids", key=KEY_PROP_CAN_STORE_LIQUIDS, default=False, tooltip="Can this container hold liquids?")],
        [sg.Text("Initial Contents (ID per line):"), sg.Multiline(key=KEY_OBJECT_STORAGE_CONTENTS, size=(60, 5), tooltip="List the object IDs initially inside this container, one ID per line.")]
    ]
    container_tab = sg.Tab('Container', container_layout, key='-TAB_CONTAINER-')

    # Tab 6: Wearable
    wearable_layout = [
        [sg.Checkbox("Is Wearable", key=KEY_PROP_IS_WEARABLE, default=False, tooltip="Can the player wear this item?")],
        [sg.Text("Wear Area:", size=(15,1)), sg.Combo(wear_areas, key=KEY_WEAR_AREA, size=(20, 1), readonly=True, tooltip="Body area where this item is worn (e.g., head, torso, feet).")],
        [sg.Text("Wear Layer:", size=(15,1)), sg.Input(key=KEY_WEAR_LAYER, size=(10, 1), tooltip="Layering order (e.g., 0=skin, 1=under, 2=over).\nLower layers block higher ones in same area.")]
    ]
    wearable_tab = sg.Tab('Wearable', wearable_layout, key='-TAB_WEARABLE-')

    # Tab 7: Weapon/Tool
    weapon_tool_layout = [
        [sg.Checkbox("Is Weapon", key=KEY_PROP_IS_WEAPON, default=False, tooltip="Can this be used as a weapon?")],
        [sg.Text("Damage:", size=(15,1)), sg.Input(key=KEY_PROP_DAMAGE, size=(10, 1), tooltip="Damage value if used as a weapon (numeric).")],
        [sg.Text("Durability:", size=(15,1)), sg.Input(key=KEY_PROP_DURABILITY, size=(10, 1), tooltip="Item's durability points (numeric, if Has Durability is checked).")],
        [sg.Text("Range:", size=(15,1)), sg.Input(key=KEY_PROP_RANGE, size=(10, 1), tooltip="Effective range if used as a weapon (numeric/abstract).")]
        # Add tool-specific properties here later if needed
    ]
    weapon_tool_tab = sg.Tab('Weapon/Tool', weapon_tool_layout, key='-TAB_WEAPON_TOOL-')

    # Tab 8: Consumable
    consumable_layout = [
        [sg.Checkbox("Is Consumable", key=KEY_PROP_IS_CONSUMABLE, default=False, tooltip="Is this item used up when used/eaten?")],
        [sg.Checkbox("Is Edible", key=KEY_PROP_IS_EDIBLE, default=False, tooltip="Can the player attempt to eat this?")],
        [sg.Checkbox("Is Food", key=KEY_PROP_IS_FOOD, default=False, tooltip="Is this beneficial food?")],
        [sg.Checkbox("Is Cookable", key=KEY_PROP_IS_COOKABLE, default=False, tooltip="Can this item be cooked?")]
        # Add nutritional value, effects (e.g., heal amount) fields later
    ]
    consumable_tab = sg.Tab('Consumable', consumable_layout, key='-TAB_CONSUMABLE-')

    # Tab 9: Interaction
    interaction_layout = [
        [sg.Text("Required State:"), sg.Multiline(key=KEY_INTERACTION_REQUIRED_STATE, size=(60, 3), tooltip="Conditions required for interaction (e.g., 'power:on', 'locked:false').\nKey:Value per line.")],
        [sg.Text("Required Items:"), sg.Multiline(key=KEY_INTERACTION_REQUIRED_ITEMS, size=(60, 3), tooltip="Object IDs of items needed for interaction, one ID per line.")],
        [sg.Text("Primary Actions:"), sg.Multiline(key=KEY_INTERACTION_PRIMARY_ACTIONS, size=(60, 3), tooltip="Main actions possible (e.g., 'use', 'open', 'activate').\nKey:Effect per line.")],
        [sg.Text("Effects:"), sg.Multiline(key=KEY_INTERACTION_EFFECTS, size=(60, 4), tooltip="Resulting changes from actions (e.g., 'set_state:is_open:true', 'add_flag:puzzle_solved').\nKey:Value per line.")],
        [sg.Text("Success Message:"), sg.Multiline(key=KEY_INTERACTION_SUCCESS, size=(60, 3), tooltip="Text displayed on successful interaction.")],
        [sg.Text("Failure Message:"), sg.Multiline(key=KEY_INTERACTION_FAILURE, size=(60, 3), tooltip="Text displayed on failed interaction (e.g., locked, missing item).")]
    ]
    interaction_tab = sg.Tab('Interaction', interaction_layout, key='-TAB_INTERACTION-')

    # Tab 10: Other Details
    other_details_layout = [
        [sg.Text("State Descriptions (state: description):"), sg.Multiline(key=KEY_OBJECT_STATE_DESCRIPTIONS, size=(60, 5), tooltip="Alternative descriptions based on state (e.g., 'offline: The screen is dark.').\nKey:Value per line.")],
        [sg.Text("Digital Content (filename: content \\n---): "), sg.Multiline(key=KEY_OBJECT_DIGITAL_CONTENT, size=(60, 5), tooltip="Text content for readable devices.\nFormat: 'filename: content line1\\ncontent line2\\n---'.")]
    ]
    other_details_tab = sg.Tab('Other Details', other_details_layout, key='-TAB_OTHER_DETAILS-')

    # Tab 11: YAML Preview
    yaml_preview_layout = [
        [sg.Multiline(key=KEY_YAML_PREVIEW, size=(80, 20), disabled=True, expand_x=True, expand_y=True, tooltip="Preview of the object data structure (read-only).")]
    ]
    yaml_preview_tab = sg.Tab('YAML Preview', yaml_preview_layout, key='-TAB_YAML_PREVIEW-')

    # --- Tab Group Definition ---
    tab_group_layout = [[sg.TabGroup([
        basic_info_tab,
        location_tab,
        state_lock_tab,
        properties_tab,
        container_tab,
        wearable_tab,
        weapon_tool_tab,
        consumable_tab,
        interaction_tab,
        other_details_tab,
        yaml_preview_tab
    ], enable_events=True, key='-TABGROUP-', expand_x=True, expand_y=True)]] # Added expand options

    # --- Persistent Bottom Controls Layout ---
    bottom_controls_layout = [
        [sg.Text("❓", size=(2,1), key=KEY_VALIDATE_INDICATOR, text_color="grey", tooltip="Validation Status (❓=Unknown, ✅=Valid, ❌=Invalid)"), # Changed size, added tooltip
         sg.Button("Validate", key=KEY_VALIDATE_BUTTON, tooltip="Check the current data for errors before saving."),
         sg.Button("Save Changes", key=KEY_SAVE_BUTTON, tooltip="Save the current object data (new or updated) to objects.yaml and update location in rooms.yaml."),
         sg.Button("Delete Object", key=KEY_DELETE_BUTTON, button_color=('white', 'red'), tooltip="Permanently delete the currently loaded object from objects.yaml and rooms.yaml.", disabled=True)], # Start disabled
        [sg.StatusBar("Ready.", key=KEY_STATUS_BAR, size=(80, 1), justification='left')]
    ]

    # --- Final Window Layout ---
    layout = [
        top_controls_layout,
        [sg.HorizontalSeparator()],
        tab_group_layout, # Add the TabGroup
        [sg.HorizontalSeparator()],
        bottom_controls_layout
        # Removed Close button from layout, use window X
    ]
# === END OF NEW LAYOUT CODE ===

    # --- Window Creation ---
    window = sg.Window("Starship Adventure 2 - Object Editor (Tabs WIP)", layout, resizable=True, finalize=True)

    # Manually set initial focus if desired (e.g., to Object ID if starting blank)
    # window[KEY_OBJECT_ID].set_focus()
    # Set minimum window size if needed
    # window.set_min_size((800, 600))

    # --- Event Loop ---
    current_object_id = None
    is_new_object = False

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

        window[KEY_STATUS_BAR].update("") # Clear status on new event
        window[KEY_VALIDATE_INDICATOR].update("") # Clear validation indicator

        try:
            if event == KEY_OBJECT_DROPDOWN:
                selected_id = values[KEY_OBJECT_DROPDOWN]
                if selected_id:
                    logging.info(f"Dropdown changed: Selected Object ID = {selected_id}")
                    object_data = manager.get_object_by_id(selected_id)
                    if object_data:
                        populate_fields(window, object_data, manager)
                        # update_yaml_preview(window, object_data, manager) # Preview not fully wired yet
                        current_object_id = selected_id
                        is_new_object = False
                        window[KEY_OBJECT_ID].update(disabled=True) # Disable ID field for existing object
                        window[KEY_DELETE_BUTTON].update(disabled=False)
                        window[KEY_STATUS_BAR].update(f"Loaded data for: {selected_id}")
                    else:
                        logging.error(f"Failed to retrieve data for selected ID: {selected_id}")
                        clear_fields(window)
                        # update_yaml_preview(window, None, manager)
                        current_object_id = None
                        is_new_object = False
                        window[KEY_DELETE_BUTTON].update(disabled=True)
                        window[KEY_STATUS_BAR].update(f"Error: Could not load data for {selected_id}", text_color="red")

            elif event == KEY_NEW_BUTTON:
                logging.info("New Object button clicked.")
                clear_fields(window)
                # update_yaml_preview(window, None, manager)
                current_object_id = None
                is_new_object = True
                window[KEY_OBJECT_ID].update(disabled=False) # Enable ID field for new object
                window[KEY_OBJECT_ID].set_focus()
                window[KEY_DELETE_BUTTON].update(disabled=True)
                window[KEY_STATUS_BAR].update("Enter details for new object. ID must be unique.")

            elif event == KEY_OBJECT_LOCATION: # Room selection changed
                 selected_room_id = values[KEY_OBJECT_LOCATION]
                 if selected_room_id:
                      area_ids = manager.get_area_ids_for_room(selected_room_id)
                      window[KEY_OBJECT_AREA_LOCATION].update(values=area_ids, value=None) # Update area dropdown
                 else:
                      window[KEY_OBJECT_AREA_LOCATION].update(values=[], value=None) # Clear if no room selected

            elif event == KEY_VALIDATE_BUTTON:
                object_data, _, _ = gather_data_from_fields(window, manager)
                if not object_data:
                    window[KEY_VALIDATE_INDICATOR].update("Cannot Validate", text_color="red")
                    window[KEY_STATUS_BAR].update("Failed to gather data from fields for validation.", text_color="red")
                    continue

                errors = validate_object_data(object_data, is_new_object, manager)
                if errors:
                    window[KEY_VALIDATE_INDICATOR].update("Invalid!", text_color="red")
                    error_message = "Validation Errors:\n- " + "\n- ".join(errors)
                    sg.popup_error(error_message, title="Validation Failed")
                    window[KEY_STATUS_BAR].update(f"{len(errors)} validation errors found.", text_color="red")
                else:
                    window[KEY_VALIDATE_INDICATOR].update("Valid", text_color="green")
                    window[KEY_STATUS_BAR].update("Data is valid.", text_color="green")
                    # Re-populate YAML preview with validated/cleaned data
                    # update_yaml_preview(window, object_data, manager)

            elif event == KEY_SAVE_BUTTON:
                object_data, room_id, area_id = gather_data_from_fields(window, manager)
                if not object_data:
                    window[KEY_STATUS_BAR].update("Error: Could not gather data from fields to save.", text_color="red")
                    continue

                obj_id_to_save = object_data.get('id')
                if not obj_id_to_save:
                     window[KEY_STATUS_BAR].update("Error: Object ID is missing.", text_color="red")
                     sg.popup_error("Object ID cannot be empty.", title="Save Error")
                     continue

                # Validate before saving
                errors = validate_object_data(object_data, is_new_object, manager)
                if errors:
                    window[KEY_VALIDATE_INDICATOR].update("Invalid!", text_color="red")
                    error_message = "Cannot save due to validation errors:\n- " + "\n- ".join(errors)
                    sg.popup_error(error_message, title="Save Failed")
                    window[KEY_STATUS_BAR].update("Cannot save. Please fix validation errors.", text_color="red")
                    continue

                # Confirmation
                action = "create new object" if is_new_object else "update existing object"
                confirm = sg.popup_yes_no(f"Are you sure you want to {action} '{obj_id_to_save}' and save all changes to objects.yaml and rooms.yaml?", title="Confirm Save")
                if confirm != 'Yes':
                    window[KEY_STATUS_BAR].update("Save cancelled.")
                    continue

                # Perform Add or Update using manager
                success = False
                if is_new_object:
                    success = manager.add_object(object_data)
                else:
                    # Use current_object_id which should be the originally loaded ID
                    if current_object_id:
                        success = manager.update_object(current_object_id, object_data)
                    else:
                         logging.error("Save Error: Trying to update but no current_object_id is set.")
                         window[KEY_STATUS_BAR].update("Error: Cannot determine which object to update.", text_color="red")
                         success = False

                if success:
                     # Update location in rooms data separately
                     loc_success = manager._update_object_location_in_rooms(obj_id_to_save, room_id, area_id)
                     if not loc_success:
                          logging.warning(f"Object data saved/updated for {obj_id_to_save}, but failed to update its location in rooms data.")
                          # Consider if this should be a bigger error shown to user

                     # Attempt to save both files
                     save_all_ok = manager.save_all_changes()

                     if save_all_ok:
                         window[KEY_STATUS_BAR].update(f"Object '{obj_id_to_save}' saved successfully.", text_color="green")
                         # Refresh dropdown
                         object_ids = manager.get_object_ids()
                         window[KEY_OBJECT_DROPDOWN].update(values=object_ids, value=obj_id_to_save)
                         window[KEY_TOTAL_OBJECT_COUNT].update(f"Total Objects: {len(object_ids)}")
                         current_object_id = obj_id_to_save # Ensure current ID is set
                         is_new_object = False # It's now an existing object
                         window[KEY_OBJECT_ID].update(disabled=True)
                         window[KEY_DELETE_BUTTON].update(disabled=False)
                         window[KEY_VALIDATE_INDICATOR].update("Saved", text_color="green")
                     else:
                          window[KEY_STATUS_BAR].update(f"Error saving YAML files after updating '{obj_id_to_save}'. Check logs.", text_color="red")
                          sg.popup_error("Failed to save changes to data files after updating. Object changes might be lost on exit.", title="Save Error")
                else:
                    window[KEY_STATUS_BAR].update(f"Failed to add/update object '{obj_id_to_save}' in manager.", text_color="red")
                    sg.popup_error(f"Could not {{'add' if is_new_object else 'update'}} object data internally. Check logs.", title="Save Error")

            elif event == KEY_DELETE_BUTTON:
                if current_object_id:
                    confirm = sg.popup_yes_no(f"WARNING: Are you absolutely sure you want to permanently delete the object '{current_object_id}'?\nThis cannot be undone.", title="Confirm Deletion", button_color=('white', 'red'))
                    if confirm == 'Yes':
                        deleted = manager.delete_object(current_object_id)
                        if deleted:
                             save_all_ok = manager.save_all_changes()
                             if save_all_ok:
                                 window[KEY_STATUS_BAR].update(f"Object '{current_object_id}' deleted successfully.", text_color="orange")
                                 clear_fields(window)
                                 # update_yaml_preview(window, None, manager)
                                 object_ids = manager.get_object_ids()
                                 window[KEY_OBJECT_DROPDOWN].update(values=object_ids, value='')
                                 window[KEY_TOTAL_OBJECT_COUNT].update(f"Total Objects: {len(object_ids)}")
                                 current_object_id = None
                                 is_new_object = False
                                 window[KEY_DELETE_BUTTON].update(disabled=True)
                             else:
                                 window[KEY_STATUS_BAR].update(f"Error saving YAML files after deleting '{current_object_id}'. Check logs.", text_color="red")
                                 sg.popup_error("Failed to save changes to data files after deletion. Object might reappear on next load.", title="Deletion Save Error")
                        else:
                             window[KEY_STATUS_BAR].update(f"Failed to delete object '{current_object_id}'. Check logs.", text_color="red")
                             sg.popup_error(f"Could not delete object '{current_object_id}'. It might not exist or an error occurred.", title="Deletion Error")
                    else:
                        window[KEY_STATUS_BAR].update("Deletion cancelled.")
                else:
                     window[KEY_STATUS_BAR].update("No object selected to delete.", text_color="yellow")

            # --- Update preview on tab change (simplified) ---
            if event == '-TABGROUP-':
                # temp_data, _, _ = gather_data_from_fields(window, manager) # Don't gather here yet
                # if temp_data:
                #     update_yaml_preview(window, temp_data, manager)
                # else:
                #     update_yaml_preview(window, None, manager)
                pass # Preview update deferred until full layout is done

        except Exception as e:
            logging.exception("An unexpected error occurred in the GUI event loop.")
            sg.popup_error(f"An unexpected error occurred: {e}\n\nPlease check the console logs for more details.", title="GUI Error")
            # Optionally, try to save unsaved changes here?
            # break # Might be too abrupt, depends on the error

    # --- Cleanup ---
    window.close()
    logging.info("Object Editor GUI closed.")

if __name__ == '__main__':
    main() 