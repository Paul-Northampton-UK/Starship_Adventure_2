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
        properties['is_dangerous'] = values.get(KEY_PROP_IS_DANGEROUS, False)
        properties['is_destroyable'] = values.get(KEY_PROP_IS_DESTROYABLE, False)
        properties['is_storage'] = values[KEY_PROP_IS_STORAGE]
        properties['is_operational'] = values.get(KEY_PROP_IS_OPERATIONAL, False)
        properties['is_edible'] = values.get(KEY_PROP_IS_EDIBLE, False)
        properties['is_weapon'] = values.get(KEY_PROP_IS_WEAPON, False)
        properties['is_movable'] = values.get(KEY_PROP_IS_MOVABLE, False)
        properties['is_wearable'] = values[KEY_PROP_IS_WEARABLE]
        properties['is_flammable'] = values.get(KEY_PROP_IS_FLAMMABLE, False)
        properties['is_toxic'] = values.get(KEY_PROP_IS_TOXIC, False)
        properties['is_food'] = values.get(KEY_PROP_IS_FOOD, False)
        properties['is_cookable'] = values.get(KEY_PROP_IS_COOKABLE, False)
        properties['is_consumable'] = values.get(KEY_PROP_IS_CONSUMABLE, False)
        properties['has_durability'] = values.get(KEY_PROP_HAS_DURABILITY, False)
        properties['is_hackable'] = values.get(KEY_PROP_IS_HACKABLE, False)
        properties['is_hidden'] = values.get(KEY_PROP_IS_HIDDEN, False)
        properties['is_rechargeable'] = values.get(KEY_PROP_IS_RECHARGEABLE, False)
        properties['is_fuel_source'] = values.get(KEY_PROP_IS_FUEL_SOURCE, False)
        properties['regenerates'] = values.get(KEY_PROP_REGENERATES, False)
        properties['is_modular'] = values.get(KEY_PROP_IS_MODULAR, False)
        properties['is_stored'] = values.get(KEY_PROP_IS_STORED, False)
        properties['is_transferable'] = values.get(KEY_PROP_IS_TRANSFERABLE, False)
        properties['is_activatable'] = values.get(KEY_PROP_IS_ACTIVATABLE, False)
        properties['is_networked'] = values.get(KEY_PROP_IS_NETWORKED, False)
        properties['requires_power'] = values.get(KEY_PROP_REQUIRES_POWER, False)
        properties['requires_item'] = values.get(KEY_PROP_REQUIRES_ITEM, False)
        properties['has_security'] = values.get(KEY_PROP_HAS_SECURITY, False)
        properties['is_sensitive'] = values.get(KEY_PROP_IS_SENSITIVE, False)
        properties['is_fragile'] = values.get(KEY_PROP_IS_FRAGILE, False)
        properties['is_secret'] = values.get(KEY_PROP_IS_SECRET, False)
        properties['can_store_liquids'] = values[KEY_PROP_CAN_STORE_LIQUIDS]

        # (Gather numeric/string properties)
        properties['storage_capacity'] = int(values[KEY_PROP_STORAGE_CAPACITY]) if values[KEY_PROP_STORAGE_CAPACITY] else None
        properties['damage'] = int(values[KEY_PROP_DAMAGE]) if values[KEY_PROP_DAMAGE] else None
        properties['durability'] = int(values[KEY_PROP_DURABILITY]) if values[KEY_PROP_DURABILITY] else None
        properties['range'] = int(values[KEY_PROP_RANGE]) if values[KEY_PROP_RANGE] else None

        # (Gather wearability properties)
        if properties['is_wearable']:
            properties['wear_area'] = values[KEY_WEAR_AREA] or None
            properties['wear_layer'] = int(values[KEY_WEAR_LAYER]) if values[KEY_WEAR_LAYER] else None
        else:
            properties.pop('wear_area', None) # Remove if not wearable
            properties.pop('wear_layer', None)

        if properties: # Only add properties key if there's data
             gathered_data['properties'] = properties

        # --- Interaction ---
        interaction['required_state'] = _parse_csv_to_list(values[KEY_INTERACTION_REQUIRED_STATE])
        # ... gather rest of interaction fields ...
        interaction['failure_message'] = values[KEY_INTERACTION_FAILURE] or None
        if any(interaction.values()): # Only add interaction key if there's data
             gathered_data['interaction'] = interaction

        # --- Other --- (storage_contents, state_descriptions)
        gathered_data['storage_contents'] = _parse_csv_to_list(values[KEY_OBJECT_STORAGE_CONTENTS])
        gathered_data['state_descriptions'] = _parse_multiline_to_dict(values[KEY_OBJECT_STATE_DESCRIPTIONS])

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
    # Location validation will happen during save logic
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
    sg.theme("DarkBlue3")
    try:
        manager = ObjectDataManager(data_dir=Path("data"))
        object_ids = manager.get_object_ids()
        room_ids = manager.get_room_ids()
        initial_total_objects = manager.get_object_count() # Get initial count
    except Exception as e:
        logging.error(f"Failed to initialize ObjectDataManager: {e}")
        sg.popup_error(f"Failed to load data files.\nError: {e}", title="Initialization Error")
        return

    # --- Define Layout Sections ---
    # Top controls - ADDED PUSH and TOTAL COUNT DISPLAY
    top_controls = [
        sg.Text("Select Object:"),
        sg.Combo(object_ids, key=KEY_OBJECT_DROPDOWN, readonly=True, size=(30, 1), enable_events=True),
        sg.Button("Load", key=KEY_LOAD_BUTTON),
        sg.Button("New Object", key=KEY_NEW_BUTTON),
        sg.Push(), # Pushes subsequent elements to the right
        sg.Text(f"Total Objects: {initial_total_objects}", key=KEY_TOTAL_OBJECT_COUNT) # Display total count
    ]

    # Basic Info Frame - Made Count READONLY and removed default_text
    basic_info_frame = sg.Frame("Basic Information", [
        [sg.Text("Object ID:", size=(12,1)), sg.Input(key=KEY_OBJECT_ID, size=(30,1), readonly=True)],
        [sg.Text("Name:", size=(12,1)), sg.Input(key=KEY_OBJECT_NAME, size=(40,1))],
        [sg.Text("Is Plural?", size=(12,1)), sg.Checkbox('', key=KEY_OBJECT_IS_PLURAL, default=False)],
        [sg.Text("Category:", size=(12,1)), sg.Combo(get_object_categories(), key=KEY_OBJECT_CATEGORY, readonly=True, size=(20,1))],
        [sg.Text("Room Location:", size=(12,1)), sg.Combo(room_ids, key=KEY_OBJECT_LOCATION, readonly=True, size=(30,1), enable_events=True)],
        [sg.Text("Area Location:", size=(12,1)), sg.Combo([], key=KEY_OBJECT_AREA_LOCATION, readonly=True, size=(30,1))],
        [sg.Text("Count:", size=(12,1)), sg.Input(key=KEY_OBJECT_COUNT, size=(10,1), readonly=True)], # READONLY, no default
        [sg.Text("Weight:", size=(12,1)), sg.Input(key=KEY_OBJECT_WEIGHT, size=(10,1), default_text="1.0")],
        [sg.Text("Size:", size=(12,1)), sg.Input(key=KEY_OBJECT_SIZE, size=(10,1), default_text="1.0")],
        [sg.Text("Synonyms (csv):", size=(12,1)), sg.Input(key=KEY_OBJECT_SYNONYMS, size=(40,1))],
        [sg.Text("Description:")],
        [sg.Multiline(key=KEY_OBJECT_DESCRIPTION, size=(60, 5))],
    ])

    # State & Lock Frame
    state_lock_frame = sg.Frame("State and Locking", [
         [sg.Checkbox("Visible Initially", key=KEY_OBJECT_INITIAL_STATE, default=True)],
         [sg.Checkbox("Is Locked", key=KEY_OBJECT_IS_LOCKED, default=False)],
         [sg.Text("Power State:", size=(10,1)), sg.Combo(['', 'offline', 'emergency', 'main_power', 'torch_light'], key=KEY_OBJECT_POWER_STATE, size=(20,1), default_value='')],
         [sg.Text("Lock Type:", size=(10,1)), sg.Combo(['', 'key', 'code', 'biometric'], key=KEY_OBJECT_LOCK_TYPE, size=(20,1), default_value='')],
         [sg.Text("Lock Code:", size=(10,1)), sg.Input(key=KEY_OBJECT_LOCK_CODE, size=(20,1))],
         [sg.Text("Lock Key ID:", size=(10,1)), sg.Input(key=KEY_OBJECT_LOCK_KEY_ID, size=(30,1))],
    ])

    # --- Properties Frame (Expanded) ---
    # Arrange properties into columns for better spacing
    prop_col1 = [
        [sg.Checkbox("Takeable", key=KEY_PROP_IS_TAKEABLE, default=False)],
        [sg.Checkbox("Interactive", key=KEY_PROP_IS_INTERACTIVE, default=True)],
        [sg.Checkbox("Dangerous", key=KEY_PROP_IS_DANGEROUS, default=False)],
        [sg.Checkbox("Destroyable", key=KEY_PROP_IS_DESTROYABLE, default=False)],
        [sg.Checkbox("Is Storage", key=KEY_PROP_IS_STORAGE, default=False)],
        [sg.Checkbox("Operational", key=KEY_PROP_IS_OPERATIONAL, default=False)],
        [sg.Checkbox("Edible", key=KEY_PROP_IS_EDIBLE, default=False)],
        [sg.Checkbox("Is Weapon", key=KEY_PROP_IS_WEAPON, default=False)],
        [sg.Checkbox("Movable", key=KEY_PROP_IS_MOVABLE, default=False)],
        [sg.Checkbox("Wearable", key=KEY_PROP_IS_WEARABLE, default=False)],
    ]
    prop_col2 = [
        [sg.Checkbox("Flammable", key=KEY_PROP_IS_FLAMMABLE, default=False)],
        [sg.Checkbox("Toxic", key=KEY_PROP_IS_TOXIC, default=False)],
        [sg.Checkbox("Is Food", key=KEY_PROP_IS_FOOD, default=False)],
        [sg.Checkbox("Cookable", key=KEY_PROP_IS_COOKABLE, default=False)],
        [sg.Checkbox("Consumable", key=KEY_PROP_IS_CONSUMABLE, default=False)],
        [sg.Checkbox("Has Durability", key=KEY_PROP_HAS_DURABILITY, default=False)],
        [sg.Checkbox("Hackable", key=KEY_PROP_IS_HACKABLE, default=False)],
        [sg.Checkbox("Hidden", key=KEY_PROP_IS_HIDDEN, default=False)],
        [sg.Checkbox("Rechargeable", key=KEY_PROP_IS_RECHARGEABLE, default=False)],
        [sg.Checkbox("Fuel Source", key=KEY_PROP_IS_FUEL_SOURCE, default=False)],
    ]
    prop_col3 = [
        [sg.Checkbox("Regenerates", key=KEY_PROP_REGENERATES, default=False)],
        [sg.Checkbox("Modular", key=KEY_PROP_IS_MODULAR, default=False)],
        [sg.Checkbox("Is Stored", key=KEY_PROP_IS_STORED, default=False)], # Digital context
        [sg.Checkbox("Transferable", key=KEY_PROP_IS_TRANSFERABLE, default=False)], # Digital context
        [sg.Checkbox("Activatable", key=KEY_PROP_IS_ACTIVATABLE, default=False)],
        [sg.Checkbox("Networked", key=KEY_PROP_IS_NETWORKED, default=False)],
        [sg.Checkbox("Requires Power", key=KEY_PROP_REQUIRES_POWER, default=False)],
        [sg.Checkbox("Requires Item", key=KEY_PROP_REQUIRES_ITEM, default=False)],
        [sg.Checkbox("Has Security", key=KEY_PROP_HAS_SECURITY, default=False)],
        [sg.Checkbox("Sensitive", key=KEY_PROP_IS_SENSITIVE, default=False)],
    ]
    prop_col4 = [
        [sg.Checkbox("Fragile", key=KEY_PROP_IS_FRAGILE, default=False)],
        [sg.Checkbox("Secret", key=KEY_PROP_IS_SECRET, default=False)],
        [sg.Text("_"*15)], # Visual separator
        [sg.Text("Storage Specific:", font=("Any", 10, "bold"))],
        [sg.Text("Capacity:", size=(8,1)), sg.Input(key=KEY_PROP_STORAGE_CAPACITY, size=(10,1))],
        [sg.Checkbox("Stores Liquids", key=KEY_PROP_CAN_STORE_LIQUIDS, default=False)],
        [sg.Text("_"*15)], # Visual separator
        [sg.Text("Weapon Specific:", font=("Any", 10, "bold"))],
        [sg.Text("Damage:", size=(8,1)), sg.Input(key=KEY_PROP_DAMAGE, size=(10,1))],
        [sg.Text("Durability:", size=(8,1)), sg.Input(key=KEY_PROP_DURABILITY, size=(10,1))], # Weapon/Item durability
        [sg.Text("Range:", size=(8,1)), sg.Input(key=KEY_PROP_RANGE, size=(10,1))],
    ]

    properties_frame = sg.Frame("Properties", [
        [sg.Column(prop_col1), sg.VSeparator(),
         sg.Column(prop_col2), sg.VSeparator(),
         sg.Column(prop_col3), sg.VSeparator(),
         sg.Column(prop_col4)]
    ])

    # --- Interaction Frame (Expanded) ---
    # Using Multiline for lists, assuming comma-separated values for now
    interaction_frame = sg.Frame("Interaction", [
         [sg.Text("Required State (csv):", size=(20,1)), sg.Input(key=KEY_INTERACTION_REQUIRED_STATE, size=(40,1))],
         [sg.Text("Required Items (IDs, csv):", size=(20,1)), sg.Input(key=KEY_INTERACTION_REQUIRED_ITEMS, size=(40,1))],
         [sg.Text("Primary Actions (csv):", size=(20,1)), sg.Input(key=KEY_INTERACTION_PRIMARY_ACTIONS, size=(40,1))],
         [sg.Text("Effects (csv):", size=(20,1)), sg.Input(key=KEY_INTERACTION_EFFECTS, size=(40,1))],
         [sg.HSeparator()],
         [sg.Text("Success Message:", size=(20,1)), sg.Input(key=KEY_INTERACTION_SUCCESS, size=(50,1))],
         [sg.Text("Failure Message:", size=(20,1)), sg.Input(key=KEY_INTERACTION_FAILURE, size=(50,1))],
    ])

    # Other Frame
    other_frame = sg.Frame("Other Details", [
        [sg.Text("Storage Contents (IDs, csv):", size=(25,1)), sg.Input(key=KEY_OBJECT_STORAGE_CONTENTS, size=(40,1))],
        [sg.Text("State Descriptions (state:desc, one per line):")],
        [sg.Multiline(key=KEY_OBJECT_STATE_DESCRIPTIONS, size=(60, 4))],
    ])

    # --- Define YAML Preview Frame Separately ---
    yaml_preview_frame = sg.Frame("YAML Preview", [
        [sg.Multiline(key=KEY_YAML_PREVIEW, size=(65, 8), disabled=True, autoscroll=True)] # Adjusted size
    ])

    # --- Wearability Frame definition ---
    wear_area_values = [''] + [area.value for area in WearArea]
    wear_layer_values = [''] + ['1', '2', '3', '4', '5'] # Add blank option
    wearability_frame = sg.Frame("Wearability", [
        [sg.Text("Area:", size=(6,1)), sg.Combo(wear_area_values, key=KEY_WEAR_AREA, size=(15, 1), readonly=True, tooltip="Body area where item is worn (blank for none)")], # Updated tooltip
        [sg.Text("Layer:", size=(6,1)), sg.Combo(wear_layer_values, key=KEY_WEAR_LAYER, size=(5, 1), readonly=True, tooltip="Layer order (blank for none)")] # Updated tooltip
    ], vertical_alignment='top')

    # --- RE-ADD Bottom Controls Definition ---
    bottom_controls = [
        [ # Row for buttons
            sg.Button("Update Preview / Validate", key=KEY_VALIDATE_BUTTON),
            sg.Text("", key=KEY_VALIDATE_INDICATOR, size=(2,1)),
            sg.Push(),
            sg.Button("Save Changes", key=KEY_SAVE_BUTTON),
            sg.Button("Delete Selected Object", key=KEY_DELETE_BUTTON, button_color=('white', 'red')),
            sg.Button("Close", key=KEY_CLOSE_BUTTON) # Use explicit key
        ],
        [sg.StatusBar("", size=(80, 1), key=KEY_STATUS_BAR)]
    ]

    # --- Assemble Main Layout ---
    left_col = sg.Column([
        [basic_info_frame],
        [properties_frame],
    ], vertical_alignment='top')

    # Right Column Layout
    right_col = sg.Column([
        [sg.Column([[state_lock_frame]], pad=(0,0), expand_x=False),
         sg.Column([[wearability_frame]], pad=(0,0), expand_x=False)],
        [interaction_frame],
        [other_frame],
        [yaml_preview_frame]
    ], vertical_alignment='top')

    # Main layout using the defined columns and bottom controls
    layout = [
        top_controls,
        [sg.HSeparator()],
        [left_col, sg.VSeparator(), right_col],
        [sg.HSeparator()],
        bottom_controls # Use the re-added definition here
    ]

    # --- Create Window ---
    window = sg.Window("Starship Adventure 2 - Object Editor", layout, resizable=True, finalize=True)

    # --- Event Loop ---
    current_object_id = None # Track which object is loaded
    current_object_data = None # Store the full data of the loaded object

    while True:
        event, values = window.read()

        # Add explicit check for Close button OR window closed event
        if event == sg.WIN_CLOSED or event == KEY_CLOSE_BUTTON:
            break

        window[KEY_STATUS_BAR].update("")

        if event == KEY_OBJECT_DROPDOWN or event == KEY_LOAD_BUTTON:
            selected_id = values[KEY_OBJECT_DROPDOWN]
            if selected_id:
                logging.info(f"Load requested for: {selected_id}")
                window[KEY_STATUS_BAR].update(f"Loading data for {selected_id}...")
                window.refresh() # Show status update immediately

                loaded_data = manager.get_object_by_id(selected_id)
                if loaded_data:
                    current_object_id = selected_id
                    current_object_data = loaded_data # Store loaded data
                    populate_fields(window, current_object_data, manager)
                    update_yaml_preview(window, current_object_data, manager)
                    window[KEY_STATUS_BAR].update(f"Loaded: {selected_id}")
                else:
                    logging.error(f"Failed to retrieve data for selected ID: {selected_id}")
                    sg.popup_error(f"Could not load data for object '{selected_id}'. Check data files.", title="Load Error")
                    current_object_id = None
                    current_object_data = None
                    clear_fields(window) # Clear fields on error
                    window[KEY_STATUS_BAR].update(f"Error loading {selected_id}.")

            else:
                 window[KEY_STATUS_BAR].update("Select an object ID to load.")

        elif event == KEY_OBJECT_LOCATION: # Room selection changed
            selected_room_id = values[KEY_OBJECT_LOCATION]
            logging.info(f"Room selection changed to: {selected_room_id}")
            area_ids = []
            if selected_room_id:
                area_ids = manager.get_area_ids_for_room(selected_room_id)
            # Workaround: Ensure list is not empty
            display_area_ids = area_ids if area_ids else ['']
            # Explicitly set readonly and size during update
            window[KEY_OBJECT_AREA_LOCATION].update(values=display_area_ids, value=None, readonly=True, size=(30,1))

        elif event == KEY_NEW_BUTTON:
            logging.info("New Object button clicked.")
            window[KEY_STATUS_BAR].update("Enter details for new object. ID cannot be changed after saving.")
            current_object_id = None
            current_object_data = None
            clear_fields(window) # Use the helper function
            update_yaml_preview(window, None, manager) # Clear preview
            window[KEY_OBJECT_AREA_LOCATION].update(values=[], value=None) # Clear area dropdown

        elif event == KEY_VALIDATE_BUTTON:
            logging.info("Validate button clicked.")
            # Unpack all 3 return values
            gathered_data, selected_room_id, selected_area_id = gather_data_from_fields(window, manager)

            # Check if gather_data failed (returned None for data)
            if gathered_data is None:
                window[KEY_VALIDATE_INDICATOR].update('❌', text_color='red')
                window[KEY_STATUS_BAR].update("Validation Error: Failed to gather data from fields. Check logs.")
                update_yaml_preview(window, None, manager) # Clear preview on error
                continue # Stop processing this event

            # Check if we are editing an existing object or creating a new one
            is_new_object = not window[KEY_OBJECT_ID].Disabled

            validation_errors = validate_object_data(gathered_data, is_new_object, manager)

            if not validation_errors:
                window[KEY_VALIDATE_INDICATOR].update('✔️', text_color='green')
                window[KEY_STATUS_BAR].update("Validation successful.")
                update_yaml_preview(window, gathered_data, manager) # Update preview with validated data
            else:
                window[KEY_VALIDATE_INDICATOR].update('❌', text_color='red')
                error_message = "Validation Failed: " + "; ".join(validation_errors)
                window[KEY_STATUS_BAR].update(error_message)
                logging.warning(error_message)
                update_yaml_preview(window, gathered_data, manager)

        elif event == KEY_SAVE_BUTTON:
            logging.info("Save Changes button clicked.")
            window[KEY_STATUS_BAR].update("Saving...")
            window.refresh()

            # Unpack all 3 return values
            gathered_data, selected_room_id, selected_area_id = gather_data_from_fields(window, manager)
            
            # Check if gather_data failed
            if gathered_data is None:
                sg.popup_error("Cannot save: Error gathering data from form. Check logs.", title="Save Error")
                window[KEY_STATUS_BAR].update("Save failed: Invalid data.")
                continue

            # Location is now checked within gather_data, but re-check here for clarity?
            # selected_room_id is now returned by gather_data
            if not selected_room_id:
                 sg.popup_error("Cannot save: Please select a Room Location.", title="Save Error")
                 window[KEY_STATUS_BAR].update("Save failed: Room Location required.")
                 continue

            is_new_object = not window[KEY_OBJECT_ID].Disabled
            validation_errors = validate_object_data(gathered_data, is_new_object, manager)

            if validation_errors:
                 error_message = "Cannot save: Validation Failed!\n - " + "\n - ".join(validation_errors)
                 sg.popup_error(error_message, title="Save Error")
                 window[KEY_STATUS_BAR].update("Save failed: Validation errors.")
                 continue

            # Confirmation popup
            if sg.popup_yes_no("Are you sure you want to save these changes?", title="Confirm Save") == 'Yes':
                save_successful = False
                object_id_to_save = gathered_data['id']

                if is_new_object:
                    # Add new object to manager's list first
                    if manager.add_object(gathered_data):
                         # Then save location and write files
                         save_successful = manager.save_object_and_location(object_id_to_save, selected_room_id, selected_area_id)
                    else:
                        sg.popup_error(f"Failed to add object '{object_id_to_save}' internally (maybe duplicate ID?).", title="Save Error")
                else: # Updating existing object
                     # Update object data in manager's list first
                     if manager.update_object(current_object_id, gathered_data): # Use current_object_id being edited
                          # Then save location and write files
                          save_successful = manager.save_object_and_location(object_id_to_save, selected_room_id, selected_area_id)
                     else:
                          sg.popup_error(f"Failed to update object '{current_object_id}' internally.", title="Save Error")

                # Handle outcome
                if save_successful:
                    window[KEY_STATUS_BAR].update("Changes saved successfully!")
                    # Refresh object list dropdown
                    new_object_ids = manager.get_object_ids()
                    new_total_count = manager.get_object_count() # Get updated count
                    window[KEY_OBJECT_DROPDOWN].update(values=new_object_ids)
                    window[KEY_TOTAL_OBJECT_COUNT].update(f"Total Objects: {new_total_count}") # Update display
                    # Optionally clear fields or reload the saved object? Reload might be best.
                    window[KEY_OBJECT_DROPDOWN].update(value=object_id_to_save) # Select the saved object
                    # Re-populate fields with the saved data (in case manager modified it slightly)
                    current_object_data = manager.get_object_by_id(object_id_to_save)
                    if current_object_data:
                        populate_fields(window, current_object_data, manager)
                        update_yaml_preview(window, current_object_data, manager)
                    else: # Should not happen if save was successful
                         clear_fields(window)
                         update_yaml_preview(window, None, manager)

                else:
                    window[KEY_STATUS_BAR].update("Save failed! Check logs.")
                    sg.popup_error("Failed to save changes to YAML files. Check logs for details.", title="Save Error")
            else:
                window[KEY_STATUS_BAR].update("Save cancelled.")

        elif event == KEY_DELETE_BUTTON:
            selected_id_to_delete = values[KEY_OBJECT_DROPDOWN]
            logging.info(f"Delete button clicked for: {selected_id_to_delete}")
            if not selected_id_to_delete:
                 window[KEY_STATUS_BAR].update("Select an object from the dropdown to delete.")
                 continue

            if sg.popup_yes_no(f"Are you sure you want to permanently delete object '{selected_id_to_delete}'?", title="Confirm Delete", button_color=('white','red')) == 'Yes':
                 window[KEY_STATUS_BAR].update(f"Deleting {selected_id_to_delete}...")
                 window.refresh()
                 if manager.delete_object(selected_id_to_delete):
                     window[KEY_STATUS_BAR].update(f"Object '{selected_id_to_delete}' deleted successfully.")
                     current_object_id = None
                     current_object_data = None
                     clear_fields(window)
                     update_yaml_preview(window, None, manager)
                     # Refresh dropdown AND total count
                     new_object_ids = manager.get_object_ids()
                     new_total_count = manager.get_object_count()
                     window[KEY_OBJECT_DROPDOWN].update(values=new_object_ids, value='')
                     window[KEY_TOTAL_OBJECT_COUNT].update(f"Total Objects: {new_total_count}") # Update display
                 else:
                     window[KEY_STATUS_BAR].update(f"Delete failed for '{selected_id_to_delete}'. Check logs.")
                     sg.popup_error(f"Failed to delete object '{selected_id_to_delete}'. Check logs for details.", title="Delete Error")
            else:
                 window[KEY_STATUS_BAR].update("Delete cancelled.")

    window.close()

if __name__ == '__main__':
    main() 