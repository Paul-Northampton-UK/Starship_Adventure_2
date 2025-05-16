# GUI for creating, editing, and deleting game objects.

import FreeSimpleGUI as sg
import logging
import sys # Add sys import
import os  # Add os import
from pathlib import Path
from io import StringIO

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
KEY_PROP_IS_OPENABLE_CLOSABLE = "-PROP_IS_OPENABLE_CLOSABLE-" # <-- NEW KEY
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

# Help Button
KEY_HELP_BUTTON = "-HELP_BUTTON-"

# --- New Keys for Wearability Frame ---
KEY_WEAR_AREA = "-WEAR_AREA-"
KEY_WEAR_LAYER = "-WEAR_LAYER-"

# Wear layer options
WEAR_LAYER_OPTIONS = list(range(11)) # 0 through 10

# --- New Keys for Surface and Charger ---
KEY_PROP_IS_SURFACE = '-PROP_IS_SURFACE-'
KEY_PROP_IS_CHARGER = '-PROP_IS_CHARGER-'

# --- NEW: Key for Is Open state ---
KEY_OBJECT_IS_OPEN = "-OBJECT_IS_OPEN-"

# --- NEW: Weapon Tab Layout ---
weapons_frame_layout = [
    [sg.Checkbox("Is Weapon?", key=KEY_PROP_IS_WEAPON, enable_events=True, tooltip="Can this object be used as a weapon?")],
    [sg.Text("Damage:"), sg.Input(key=KEY_PROP_DAMAGE, tooltip="Damage dealt (if Weapon)", size=(8,1), disabled=True), sg.Text("Range:"), sg.Input(key=KEY_PROP_RANGE, tooltip="Effective range (if Weapon)", size=(8,1), disabled=True)],
]

# --- NEW Keys for Storage Management ---
KEY_STORAGE_ITEM_SELECT = "-STORAGE_ITEM_SELECT-"
KEY_STORAGE_ADD_BUTTON = "-STORAGE_ADD_BUTTON-"
KEY_STORAGE_DELETE_BUTTON = "-STORAGE_DELETE_BUTTON-"

digital_content_frame_layout = [
     [sg.Text("Digital Content (file_id: content, use --- separator:)"), sg.Multiline(key=KEY_OBJECT_DIGITAL_CONTENT, tooltip="For terminals, tablets: Define files/logs accessible (file_name:Text content)", size=(60, 10))],
]

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
    window[KEY_OBJECT_COUNT].update("(Auto)") # Indicate automatic count (remains disabled)

    # --- Clear Basic Info fields ---
    window[KEY_OBJECT_WEIGHT].update("")
    window[KEY_OBJECT_SIZE].update("")
    window[KEY_OBJECT_DESCRIPTION].update("")
    window[KEY_OBJECT_SYNONYMS].update("")


    # State & Lock
    window[KEY_OBJECT_INITIAL_STATE].update(True)
    window[KEY_OBJECT_IS_LOCKED].update(False)
    window[KEY_OBJECT_POWER_STATE].update("")
    window[KEY_OBJECT_LOCK_TYPE].update("")
    window[KEY_OBJECT_LOCK_CODE].update("")
    window[KEY_OBJECT_LOCK_KEY_ID].update("")
    window[KEY_OBJECT_IS_OPEN].update(False) # Reset new is_open field

    # Disable lock fields by default for new object
    window[KEY_OBJECT_LOCK_TYPE].update(disabled=True)
    window[KEY_OBJECT_LOCK_CODE].update(disabled=True)
    window[KEY_OBJECT_LOCK_KEY_ID].update(disabled=True)

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
    window[KEY_OBJECT_STORAGE_CONTENTS].update("", disabled=True) # Ensure disabled
    window[KEY_OBJECT_STATE_DESCRIPTIONS].update("")
    window[KEY_OBJECT_DIGITAL_CONTENT].update("")

    # Clear Wearability Frame (keep fields enabled/disabled based on is_wearable=False initially)
    window[KEY_WEAR_AREA].update(value='', disabled=True)
    window[KEY_WEAR_LAYER].update(value='', disabled=True) # Combo needs string value

    # Clear YAML Preview
    window[KEY_YAML_PREVIEW].update("")

    # Reset Validate button color to default
    window[KEY_VALIDATE_BUTTON].update(button_color=sg.theme_button_color())
    window[KEY_STATUS_BAR].update("Fields cleared for new object.")

    # Disable Save and Delete for a clean slate
    window[KEY_SAVE_BUTTON].update(disabled=True)
    window[KEY_DELETE_BUTTON].update(disabled=False)

    window[KEY_PROP_IS_DANGEROUS].update(False)
    window[KEY_PROP_IS_DESTROYABLE].update(False)
    window[KEY_PROP_IS_OPENABLE_CLOSABLE].update(False) # <-- CLEAR NEW FIELD
    # window[KEY_PROP_IS_LOCKABLE].update(False)
    window[KEY_PROP_IS_STORAGE].update(False)


def populate_fields(window, object_data: dict, manager: ObjectDataManager):
    """Populates the GUI fields with data from the loaded object."""
    logging.debug(f"Populating fields for object_id: {object_data.get('id')}")
    if not object_data:
        logging.warning("populate_fields called with empty object_data")
        return

    obj_id = object_data.get("id", "")
    # Disable Object ID field once loaded/created
    window[KEY_OBJECT_ID].update(obj_id, disabled=True)

    # --- Populate Basic Info ---
    window[KEY_OBJECT_NAME].update(object_data.get("name", ""))
    window[KEY_OBJECT_IS_PLURAL].update(object_data.get("is_plural", False))
    window[KEY_OBJECT_CATEGORY].update(object_data.get("category", ""))

    # Location - Find from rooms.yaml data using manager method (like old editor)
    found_room_id, found_area_id = manager.find_object_location(obj_id)
    logging.debug(f"  [Populate] Found Room: '{found_room_id}', Found Area: '{found_area_id}'")
    window[KEY_OBJECT_LOCATION].update(value=found_room_id or "") # Update room dropdown

    # Update Area dropdown based on found room
    area_ids = []
    if found_room_id and found_room_id != "inventory":
        area_ids = manager.get_area_ids_for_room(found_room_id) # Use correct method name
        logging.debug(f"  [Populate] Areas for room '{found_room_id}': {area_ids}")
        window[KEY_OBJECT_AREA_LOCATION].update(disabled=False, values=area_ids, value=found_area_id or "")
    else:
        logging.debug(f"  [Populate] Disabling area dropdown (Found Room: {found_room_id})")
        window[KEY_OBJECT_AREA_LOCATION].update(disabled=True, values=[], value="")


    # --- Object Count ---
    # Display the actual count, but keep the field disabled if it's not a new object
    count_val = object_data.get("count", 1) # Default to 1 if missing
    window[KEY_OBJECT_COUNT].update(count_val)

    # --- Populate other Basic Info fields ---
    window[KEY_OBJECT_WEIGHT].update(object_data.get("weight", ""))
    window[KEY_OBJECT_SIZE].update(object_data.get("size", ""))
    window[KEY_OBJECT_DESCRIPTION].update(object_data.get("description", ""))
    synonyms = object_data.get("synonyms", [])
    window[KEY_OBJECT_SYNONYMS].update(_parse_list_to_csv(synonyms))

    # --- Populate State & Lock (Now moved to other tabs) ---
    is_locked = object_data.get("is_locked", False) # Get lock state first
    window[KEY_OBJECT_IS_LOCKED].update(is_locked) # Update checkbox in Storage tab
    window[KEY_OBJECT_INITIAL_STATE].update(object_data.get("initial_state", True)) # Update checkbox in Properties tab
    window[KEY_OBJECT_POWER_STATE].update(object_data.get("power_state", "")) # Update input in Misc tab
    window[KEY_OBJECT_IS_OPEN].update(object_data.get("is_open", False)) # Populate is_open (default to False if not present)

    # Update and Enable/disable lock fields based on lock state (in Storage tab)
    window[KEY_OBJECT_LOCK_TYPE].update(object_data.get("lock_type", ""), disabled=not is_locked)
    window[KEY_OBJECT_LOCK_CODE].update(object_data.get("lock_code", ""), disabled=not is_locked)
    window[KEY_OBJECT_LOCK_KEY_ID].update(object_data.get("lock_key_id", ""), disabled=not is_locked) # Update dropdown value

    # --- Populate Properties ---
    props = object_data.get("properties", {})
    is_wearable = props.get("is_wearable", False) # Get the wearable flag (for Wearability tab)
    window[KEY_PROP_IS_WEARABLE].update(is_wearable)
    logging.debug(f"  [Populate] Is Wearable: {is_wearable}")
    # Wearability - Get directly from properties dict (like old editor)
    wear_area_val = props.get("wear_area", '')
    wear_layer_val = props.get("wear_layer", '') # Get value (might be None or number)
    logging.debug(f"  [Populate] Wear Area Value: {wear_area_val}")
    logging.debug(f"  [Populate] Wear Layer Value: {wear_layer_val}")

    # Populate and enable/disable wear fields based on the flag (Wearability tab)
    window[KEY_WEAR_AREA].update(wear_area_val, disabled=not is_wearable)
    # Convert layer to string for Combo field, handle None
    layer_str = str(wear_layer_val) if wear_layer_val is not None else ''
    window[KEY_WEAR_LAYER].update(layer_str, disabled=not is_wearable) # Update combo

    # Explicitly set storage field states on load (Storage tab)
    is_storage = props.get("is_storage", False)
    window[KEY_PROP_IS_STORAGE].update(is_storage)
    logging.debug(f"  [Populate] Is Storage: {is_storage}")

    # Explicitly set weapon field states on load (Weapon tab)
    is_weapon = props.get("is_weapon", False)
    window[KEY_PROP_IS_WEAPON].update(is_weapon)
    logging.debug(f"  [Populate] Is Weapon: {is_weapon}")

    # Get Has Durability flag
    has_durability = props.get("has_durability", False)
    window[KEY_PROP_HAS_DURABILITY].update(has_durability)
    logging.debug(f"  [Populate] Has Durability: {has_durability}")

    # Now iterate through general properties (Properties tab)
    for key, value in props.items():
        # Skip keys handled in other tabs or specific sections
        if key in ["wear_area", "wear_layer", "is_wearable", "is_storage",
                   "storage_capacity", "can_store_liquids", "is_weapon",
                   "damage", "range", "durability", "has_durability",
                   "is_openable_closable"]: # <-- Add to exclusion list if handled explicitly elsewhere
            continue

        # Convert property key (e.g., "is_takeable") to GUI key (e.g., "-PROP_IS_TAKEABLE-")
        gui_key = f"-PROP_{key.upper()}-"
        if gui_key in window.AllKeysDict:
            if isinstance(window[gui_key], sg.Checkbox):
                window[gui_key].update(bool(value))
            elif isinstance(window[gui_key], sg.Input):
                # Handle cases where value might be None or not a simple type
                window[gui_key].update(str(value) if value is not None else "")
            # Add other element types if needed (e.g., Spin, Combo)
        else:
            logging.warning(f"GUI key {gui_key} not found for property {key}")

    # Update specific input properties based on their flags (Storage, Weapon, and Durability in Properties)
    # Storage
    storage_cap = props.get("storage_capacity")
    window[KEY_PROP_STORAGE_CAPACITY].update(str(storage_cap) if storage_cap is not None else "", disabled=not is_storage)
    stores_liq = props.get("can_store_liquids", False)
    window[KEY_PROP_CAN_STORE_LIQUIDS].update(bool(stores_liq), disabled=not is_storage)
    # Weapon
    dmg = props.get("damage")
    window[KEY_PROP_DAMAGE].update(str(dmg) if dmg is not None else "", disabled=not is_weapon)
    rng = props.get("range")
    window[KEY_PROP_RANGE].update(str(rng) if rng is not None else "", disabled=not is_weapon)
    # Durability (based on has_durability flag)
    dura = props.get("durability")
    window[KEY_PROP_DURABILITY].update(str(dura) if dura is not None else "", disabled=not has_durability)

    # --- Populate Interaction (Interaction tab) ---
    interaction = object_data.get("interaction", {})
    window[KEY_INTERACTION_REQUIRED_STATE].update(interaction.get("required_state", ""))
    req_items = interaction.get("required_items", [])
    window[KEY_INTERACTION_REQUIRED_ITEMS].update(_parse_list_to_csv(req_items))
    prim_actions = interaction.get("primary_actions", [])
    window[KEY_INTERACTION_PRIMARY_ACTIONS].update(_parse_list_to_csv(prim_actions))
    effects = interaction.get("effects", {})
    window[KEY_INTERACTION_EFFECTS].update(_parse_dict_to_multiline(effects))
    window[KEY_INTERACTION_SUCCESS].update(interaction.get("success_message", ""))
    window[KEY_INTERACTION_FAILURE].update(interaction.get("failure_message", ""))


    # --- Populate Other (Storage, Misc, Digital tabs) ---
    storage = object_data.get("storage_contents", [])
    window[KEY_OBJECT_STORAGE_CONTENTS].update(_parse_list_to_csv(storage), disabled=True) # Ensure disabled
    state_desc = object_data.get("state_descriptions", {})
    window[KEY_OBJECT_STATE_DESCRIPTIONS].update(_parse_dict_to_multiline(state_desc))
    # Populate Digital Content
    digital_content = object_data.get("digital_content") # Allow None
    window[KEY_OBJECT_DIGITAL_CONTENT].update(_parse_digital_content_to_multiline(digital_content))


    # --- Update YAML Preview ---
    update_yaml_preview(window, object_data, manager)

    # Enable Save and Delete buttons after loading
    window[KEY_SAVE_BUTTON].update(disabled=False)
    window[KEY_DELETE_BUTTON].update(disabled=False)

    # Reset Validate button color to default on load
    window[KEY_VALIDATE_BUTTON].update(button_color=sg.theme_button_color())
    window[KEY_STATUS_BAR].update(f"Loaded object: {obj_id}")

    # Explicitly set openable_closable field state on load (Properties I tab)
    window[KEY_PROP_IS_OPENABLE_CLOSABLE].update(props.get("is_openable_closable", False))


def update_yaml_preview(window, object_data: Optional[dict], manager: ObjectDataManager):
    """Updates the YAML preview pane based on the current object data."""
    if not object_data:
        window[KEY_YAML_PREVIEW].update("No object loaded or created yet.")
        return

    try:
        # Use manager.yaml.dump with StringIO
        string_stream = StringIO()
        manager.yaml.dump([object_data], string_stream) # Dump as list containing the object dict
        yaml_string = string_stream.getvalue()
        # Optional: Remove the list indicator '- ' from the start for single object preview
        if yaml_string.startswith('- '):
            yaml_string = yaml_string[2:]

        window[KEY_YAML_PREVIEW].update(yaml_string)
    except Exception as e:
        logging.error(f"Error generating YAML preview: {e}")
        window[KEY_YAML_PREVIEW].update(f"Error generating preview: {e}")


def _parse_csv_to_list(csv_string: str) -> list:
    """Converts a comma-separated string (potentially with spaces) to a list of strings."""
    if not csv_string:
        return []
    return [item.strip() for item in csv_string.split(',') if item.strip()]

def _parse_multiline_to_dict(multiline_string: str) -> dict:
    """Converts key:value lines into a dictionary."""
    data_dict = {}
    if not multiline_string:
        return data_dict
    for line in multiline_string.splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            data_dict[key.strip()] = value.strip()
        else:
            logging.warning(f"Skipping malformed line in multiline input: {line}")
    return data_dict


def gather_data_from_fields(window: sg.Window, manager: ObjectDataManager) -> tuple[Optional[dict], Optional[str], Optional[str]]:
    """Gathers data from all GUI fields and compiles it into an object dictionary.
    Returns a tuple: (object_data_dict, object_id, original_object_id)
    object_id is the ID currently in the field (could be new or modified).
    original_object_id is the ID from the dropdown (used for saving/updating).
    Returns (None, None, None) if a critical error occurs (e.g., missing ID).
    """
    logging.debug("Gathering data from fields.")
    data = {}
    values = window.read(timeout=0)[1] # Get current values without blocking

    # Get ID (handle if disabled or new)
    object_id = values.get(KEY_OBJECT_ID)
    original_object_id = values.get(KEY_OBJECT_DROPDOWN) # ID used for loading

    if not object_id and not window[KEY_OBJECT_ID].Disabled: # If it's a new object, ID must be provided
         sg.popup_error("Object ID is required for new objects.")
         return None, None, None
    elif window[KEY_OBJECT_ID].Disabled: # If loaded, use the original ID for saving
        object_id = original_object_id # Ensure we use the loaded ID if field is disabled
    elif object_id != original_object_id and original_object_id: # ID changed after load
        # We might need logic here to handle renaming or creating a copy
        logging.warning(f"Object ID changed from '{original_object_id}' to '{object_id}'. Saving will update/create based on '{object_id}'.")


    if not object_id: # Final check if ID is somehow still missing
         sg.popup_error("Could not determine Object ID.")
         return None, None, None

    data["id"] = object_id.strip()


    # --- Basic Info ---
    data["name"] = values.get(KEY_OBJECT_NAME, "").strip()
    data["is_plural"] = bool(values.get(KEY_OBJECT_IS_PLURAL))
    data["category"] = values.get(KEY_OBJECT_CATEGORY, "")
    data["location"] = values.get(KEY_OBJECT_LOCATION, "") # Room ID
    data["area_location"] = values.get(KEY_OBJECT_AREA_LOCATION, "") # Optional Area

    # --- Object Count ---
    # Handle the "(Auto)" case for new objects explicitly
    count_str = values.get(KEY_OBJECT_COUNT, "1") # Default to '1' string
    if count_str == "(Auto)":
        # For new objects, we'll let the manager assign the count during saving if needed
        # Or default it to 1 here? Let's default to 1 for validation.
        data["count"] = 1
        logging.debug("Count field shows '(Auto)', setting data['count'] to 1 for now.")
    else:
        try:
            data["count"] = int(count_str)
        except (ValueError, TypeError):
             logging.warning(f"Invalid count value '{count_str}', defaulting to 1.")
             data["count"] = 1 # Default if conversion fails


    # --- Other Basic Info ---
    # Weight and Size - try converting to float, allow empty
    try:
        weight_str = values.get(KEY_OBJECT_WEIGHT, "")
        data["weight"] = float(weight_str) if weight_str else None
    except ValueError:
        logging.warning(f"Invalid weight value '{weight_str}', setting to None.")
        data["weight"] = None
    try:
        size_str = values.get(KEY_OBJECT_SIZE, "")
        data["size"] = float(size_str) if size_str else None
    except ValueError:
        logging.warning(f"Invalid size value '{size_str}', setting to None.")
        data["size"] = None

    data["description"] = values.get(KEY_OBJECT_DESCRIPTION, "").strip()
    data["synonyms"] = _parse_csv_to_list(values.get(KEY_OBJECT_SYNONYMS, ""))


    # --- State & Lock ---
    data["initial_state"] = bool(values.get(KEY_OBJECT_INITIAL_STATE))
    data["is_locked"] = bool(values.get(KEY_OBJECT_IS_LOCKED))
    data["power_state"] = values.get(KEY_OBJECT_POWER_STATE, "")
    data["lock_type"] = values.get(KEY_OBJECT_LOCK_TYPE, "")
    data["lock_code"] = values.get(KEY_OBJECT_LOCK_CODE, "")
    data["lock_key_id"] = values.get(KEY_OBJECT_LOCK_KEY_ID, "")
    data["is_open"] = bool(values.get(KEY_OBJECT_IS_OPEN, False)) # Gather is_open state

    # --- Properties --- (Gather from individual tabs)
    properties = {}
    all_keys = window.AllKeysDict
    for key in all_keys:
        # --- Add check for string type ---
        if isinstance(key, str):
            if key.startswith("-PROP_"):
                prop_name_full = key[len("-PROP_"):-1] # Remove prefix and suffix
                prop_name_lower = prop_name_full.lower()
                element = window[key]

                # Skip properties managed in specific tabs
                if prop_name_lower in ["is_storage", "storage_capacity", "can_store_liquids",
                                       "is_weapon", "damage", "range", "durability", "is_wearable",
                                       "is_openable_closable"]:
                    continue

                if isinstance(element, sg.Checkbox):
                    # Exclude initial_state as it's handled above
                    if key != KEY_OBJECT_INITIAL_STATE:
                        properties[prop_name_lower] = bool(values.get(key))
                elif isinstance(element, sg.Input):
                    input_val_str = values.get(key, "").strip()
                    # Store non-empty values as strings (numeric conversion was problematic)
                    if input_val_str:
                        properties[prop_name_lower] = input_val_str
                    # else: Omit empty optional properties
                # Add handling for other property types (Combo, Spin) if needed

    # Add properties from specific tabs / special handling
    # Has Durability (needed for the Durability input itself)
    has_durability = bool(values.get(KEY_PROP_HAS_DURABILITY))
    properties["has_durability"] = has_durability

    # Storage
    if values.get(KEY_PROP_IS_STORAGE):
        properties["is_storage"] = True
        capacity_str = values.get(KEY_PROP_STORAGE_CAPACITY, "").strip()
        if capacity_str:
            try:
                properties["storage_capacity"] = int(capacity_str)
            except ValueError:
                try:
                    properties["storage_capacity"] = float(capacity_str)
                except ValueError:
                    logging.warning(f"Invalid storage capacity '{capacity_str}', not saving.")
        if values.get(KEY_PROP_CAN_STORE_LIQUIDS):
            properties["can_store_liquids"] = True
    # Weapon
    if values.get(KEY_PROP_IS_WEAPON):
        properties["is_weapon"] = True
        damage_str = values.get(KEY_PROP_DAMAGE, "").strip()
        if damage_str:
            try:
                properties["damage"] = int(damage_str)
            except ValueError:
                try:
                    properties["damage"] = float(damage_str)
                except ValueError:
                     logging.warning(f"Invalid damage value '{damage_str}', not saving.")
        range_str = values.get(KEY_PROP_RANGE, "").strip()
        if range_str:
             try:
                 properties["range"] = int(range_str)
             except ValueError:
                 try:
                     properties["range"] = float(range_str)
                 except ValueError:
                     logging.warning(f"Invalid range value '{range_str}', not saving.")
        # Durability moved out
    # Durability (gather only if has_durability is checked)
    if has_durability:
        dura_str = values.get(KEY_PROP_DURABILITY, "").strip()
        if dura_str:
             try:
                 properties["durability"] = int(dura_str)
             except ValueError:
                 try:
                     properties["durability"] = float(dura_str)
                 except ValueError:
                     logging.warning(f"Invalid durability value '{dura_str}', not saving.")
    # Wearability
    if values.get(KEY_PROP_IS_WEARABLE):
        properties["is_wearable"] = True
        # Restore wear area/layer gathering
        wear_area = values.get(KEY_WEAR_AREA, '').strip()
        wear_layer_str = values.get(KEY_WEAR_LAYER, '')
        if wear_area:
            properties["wear_area"] = wear_area
        if wear_layer_str:
            try:
                properties["wear_layer"] = int(wear_layer_str)
            except (ValueError, TypeError):
                logging.warning(f"Invalid wear layer value '{wear_layer_str}', not saving.")

    # Add is_openable_closable to properties
    properties["is_openable_closable"] = bool(values.get(KEY_PROP_IS_OPENABLE_CLOSABLE)) # <-- GATHER FIELD

    # Only add properties dict if it's not empty
    if properties:
        data["properties"] = properties


    # --- Interaction ---
    interaction = {}
    req_state = values.get(KEY_INTERACTION_REQUIRED_STATE, "").strip()
    req_items = _parse_csv_to_list(values.get(KEY_INTERACTION_REQUIRED_ITEMS, ""))
    prim_actions = _parse_csv_to_list(values.get(KEY_INTERACTION_PRIMARY_ACTIONS, ""))
    effects = _parse_multiline_to_dict(values.get(KEY_INTERACTION_EFFECTS, ""))
    success_msg = values.get(KEY_INTERACTION_SUCCESS, "").strip()
    failure_msg = values.get(KEY_INTERACTION_FAILURE, "").strip()

    if req_state: interaction["required_state"] = req_state
    if req_items: interaction["required_items"] = req_items
    if prim_actions: interaction["primary_actions"] = prim_actions
    if effects: interaction["effects"] = effects
    if success_msg: interaction["success_message"] = success_msg
    if failure_msg: interaction["failure_message"] = failure_msg

    if interaction:
        data["interaction"] = interaction


    # --- Other (Gather from GUI) ---
    # Storage contents are now read from the disabled multiline, which is managed by Add/Delete buttons
    data["storage_contents"] = _parse_csv_to_list(values.get(KEY_OBJECT_STORAGE_CONTENTS, ""))
    # State descriptions (Misc Tab)
    data["state_descriptions"] = _parse_multiline_to_dict(values.get(KEY_OBJECT_STATE_DESCRIPTIONS, ""))
    # Digital Content (Digital Tab)
    digital_content_text = values.get(KEY_OBJECT_DIGITAL_CONTENT, "")
    data["digital_content"] = _parse_multiline_to_digital_content(digital_content_text)


    # --- Clean up empty/None optional fields ---
    # Remove keys with None values or empty lists/dicts where appropriate
    # This helps keep the YAML cleaner.
    keys_to_remove_if_empty = [
        "synonyms", "lock_type", "lock_code", "lock_key_id", "interaction",
        "storage_contents", "state_descriptions", "digital_content",
        "power_state", # Moved power_state here
        # "required_state", "required_items", "primary_actions", # Handled by interaction dict check
        # "effects", "success_message", "failure_message", # Handled by interaction dict check
        "area_location"
        # is_open will be included like is_locked, not removed if False
    ]
    keys_to_remove_if_none = ["weight", "size"] # Explicitly remove if None

    # Need to iterate safely as we are deleting
    for key in list(data.keys()): # Iterate over a copy of keys
        if key in keys_to_remove_if_empty and not data[key]:
             del data[key]
        elif key in keys_to_remove_if_none and data[key] is None:
             del data[key]

    # Remove empty properties dict if it exists and is empty
    if "properties" in data and not data["properties"]:
        del data["properties"]

    # Remove empty interaction dict (already checked if empty before adding)
    # if "interaction" in data and not data["interaction"]:
    #      del data["interaction"]

    logging.debug(f"Gathered data dict: {data}")
    return data, object_id, original_object_id


def validate_object_data(object_data: dict, is_new: bool, manager: ObjectDataManager) -> list[str]:
    """Validates the gathered object data against basic rules and schema.
    Returns a list of error messages. An empty list means validation passed.
    """
    errors = []
    if not object_data:
        return ["No object data provided."]

    obj_id = object_data.get("id")
    if not obj_id:
        errors.append("Object ID is missing.")
    elif not isinstance(obj_id, str) or not obj_id.strip():
         errors.append("Object ID cannot be empty.")
    elif is_new and (manager.get_object_by_id(obj_id) is not None):
        errors.append(f"Object ID '{obj_id}' already exists. Choose a different ID.")

    if not object_data.get("name"):
        errors.append("Object Name is required.")

    if not object_data.get("category"):
        errors.append("Object Category is required.")
    elif object_data["category"] not in get_object_categories():
         errors.append(f"Invalid Object Category: {object_data['category']}")

    # Location and Area Validation
    location_value = object_data.get("location") # String from Combo box, or "" if empty
    # 'initial_state' from data is True if "Initially Visible?" checkbox is checked.
    # So, is_marked_as_hidden_in_ui is True if the "Initially Visible?" checkbox is UNCHECKED.
    is_marked_as_hidden_in_ui = object_data.get("initial_state") is False

    location_is_truly_empty = not location_value # True if location_value is None or ""

    if location_is_truly_empty:
        # Location is empty. It's allowed if the object is marked as NOT initially visible in the UI.
        if not is_marked_as_hidden_in_ui:
            errors.append("Object Location (Room ID or 'inventory') is required if 'Initially Visible?' is checked.")
    else: # Location is provided, so validate it.
        if location_value != "inventory" and location_value not in manager.get_room_ids():
            errors.append(f"Selected Room ID '{location_value}' does not exist in loaded rooms data.")
        # Validate Area Location only if a valid room location is provided AND an area is specified.
        elif location_value != "inventory" and location_value in manager.get_room_ids():
            area_loc = object_data.get("area_location")
            if area_loc: # Only validate area if one is actually specified
                if area_loc not in manager.get_area_ids_for_room(location_value):
                    errors.append(f"Area '{area_loc}' does not exist in Room '{location_value}' according to loaded rooms data.")


    # --- Validate Numeric Fields (Weight, Size) ---
    # Weight: Non-negative number
    if "weight" in object_data and object_data["weight"] is not None:
        if not isinstance(object_data["weight"], (int, float)) or object_data["weight"] < 0:
            errors.append("Weight must be a non-negative number.")
    # Size: Positive number
    if "size" in object_data and object_data["size"] is not None:
        if not isinstance(object_data["size"], (int, float)) or object_data["size"] <= 0:
            errors.append("Size must be a positive number.")


    # --- Validate Lock properties ---
    is_locked = object_data.get("is_locked", False)
    lock_type = object_data.get("lock_type")
    lock_code = object_data.get("lock_code")
    lock_key_id = object_data.get("lock_key_id")
    if is_locked:
        if not lock_type:
            errors.append("If 'Is Locked' is checked, 'Lock Type' must be specified.")
        # Check if EITHER code OR key is provided
        if not lock_code and not lock_key_id:
            errors.append("If 'Is Locked' is checked, either 'Lock Code' or 'Key Object ID' must be provided.")
    # Add more lock validation if needed (e.g., code/key_id required for specific types)

    # --- Validate Open/Locked state consistency ---
    is_open = object_data.get("is_open", False)
    if is_locked and is_open:
        errors.append("Object cannot be both 'Is Locked' and 'Is Open' simultaneously. Please uncheck one.")

    # --- Validate Properties ---
    properties = object_data.get("properties", {})

    # --- NEW: Validate Openable/Closable, Is Open, and Is Locked consistency ---
    is_openable_closable_prop = properties.get("is_openable_closable", False)

    if not is_openable_closable_prop and is_open:
        errors.append("If 'Is Openable/Closable' property is unchecked, the object's 'Is Open' state (in States tab) must also be unchecked (i.e., it cannot start open).")

    if is_locked and not is_openable_closable_prop:
        errors.append("If object 'Is Locked' (in States tab), its 'Is Openable/Closable' property (in Properties I tab) must be checked.")
    # --- END NEW VALIDATION ---

    if properties.get("is_storage"):
        if "storage_capacity" not in properties or not isinstance(properties["storage_capacity"], (int, float)) or properties["storage_capacity"] <= 0:
            errors.append("If 'Is Storage' is checked, 'Storage Capacity' must be a positive number.")

    # --- Validate Weapon properties ---
    if properties.get("is_weapon"):
        # Damage: Required and positive
        if "damage" not in properties:
            errors.append("If 'Is Weapon' is checked, 'Damage' must be provided.")
        elif not isinstance(properties["damage"], (int, float)) or properties["damage"] <= 0:
            errors.append("Damage must be a positive number.")
        
        # Range: Optional, but non-negative if present
        if "range" in properties and properties["range"] is not None: # Check if key exists and value is not None
            if not isinstance(properties["range"], (int, float)) or properties["range"] < 0:
                errors.append("Range must be a non-negative number.")

        # Durability: Optional, but positive if present
        if "durability" in properties and properties["durability"] is not None: # Check if key exists and value is not None
            if not isinstance(properties["durability"], (int, float)) or properties["durability"] <= 0:
                errors.append("Durability must be a positive number.")

    # --- Validate Wearability (using properties directly) ---
    # wearable_props = object_data.get("wearable_properties") # No longer using this sub-dict
    is_wearable = properties.get("is_wearable", False)
    wear_area = properties.get("wear_area")
    layer = properties.get("wear_layer")

    if is_wearable:
         if not wear_area:
             errors.append("Wear Area is required for wearable items.")
         elif wear_area not in [wa.value for wa in WearArea]: # Check against enum
             errors.append(f"Invalid Wear Area: '{wear_area}'. Must be one of { [wa.value for wa in WearArea] }")
         if layer is not None: # Layer is optional, but validate if present
              # Layer is now validated as int >= 0 by gather_data handles combo conversion well, but safe to keep
              if not isinstance(layer, int) or layer < 0:
                   # This check might be redundant if gather_data handles combo conversion well, but safe to keep
                   errors.append("Wear Layer must be a non-negative integer (0-10).")
    # Check 2 from old editor: If area/layer is set, must be wearable
    elif (wear_area or layer is not None) and not is_wearable:
         errors.append("Wear Area/Layer is set, but 'Is Wearable' property is not checked.")


    # --- Add more specific validations as needed ---
    # ...

    logging.debug(f"Validation results for {obj_id}: {errors if errors else 'Passed'}")
    return errors


def main():
    sg.theme("DarkBlue") # Set a theme

    # --- Initialize ObjectDataManager ---
    # Determine the path relative to this script's location
    data_dir = project_root / "data"
    manager = ObjectDataManager(data_dir)
    all_object_ids = manager.get_object_ids()
    all_room_ids = manager.get_room_ids() # Corrected method name
    all_key_ids = manager.get_key_object_ids() # Get list of keys

    # --- Define Icon Path (set to None if no icon) ---
    ICON_PATH = None

    # --- GUI Layout Definition ---

    # --- Top Controls ---
    top_controls_layout = [[
        sg.Text("Select Object:"),
        sg.Combo(
            all_object_ids,
            key=KEY_OBJECT_DROPDOWN,
            enable_events=True, # Trigger event when selection changes
            tooltip="Select an existing object ID to load its data",
            size=(25, 1)
        ),
        sg.Button("Load", key=KEY_LOAD_BUTTON, tooltip="Load the selected object"),
        sg.Button("New", key=KEY_NEW_BUTTON, tooltip="Clear fields to create a new object"),
        sg.Button("Help", key=KEY_HELP_BUTTON, tooltip="Open editor help (Not implemented yet)"),
        sg.Push(),
        sg.Text("Total Objects:"),
        sg.Text("0", # Initial value, will be updated
                key=KEY_TOTAL_OBJECT_COUNT,
                size=(5,1),
                background_color='lightblue', # Highlight color
                text_color='black', # High-contrast text
                justification='center', # Center text within the background
                tooltip="Total number of objects defined in objects.yaml")
    ]]

    # --- Frame Definitions (Example - assuming these are defined earlier) ---
    # basic_info_frame = sg.Frame("Basic Info", [...])
    # properties_frame = sg.Frame("Properties", [...])
    # ... etc ...

    # --- Define layouts for each tab ---
    # (These should contain the FRAMES defined above)
    basic_info_tab_layout = [[sg.Text("Basic Info Content Placeholder")]] # Replace with actual frame layout
    properties_tab_layout = [[sg.Text("Properties Content Placeholder")]] # Replace with actual frame layout
    properties_tab_I_layout = [] # Define new layout
    properties_tab_II_layout = [] # Define new layout
    properties_tab_III_layout = [] # Define new layout for Properties III
    state_lock_tab_layout = [[sg.Text("State/Lock Content Placeholder")]] # Replace with actual frame layout
    interaction_tab_layout = [[sg.Text("Interaction Content Placeholder")]] # Replace with actual frame layout
    other_details_tab_layout = [[sg.Text("Other Details Placeholder")]] # Replace with actual frame layout
    wearability_tab_layout = [[sg.Text("Wearability Placeholder")]] # Replace with actual frame layout
    digital_content_tab_layout = [[sg.Text("Digital Content Placeholder")]] # Replace with actual frame layout

    # Rebuild these layouts using the actual content from the original file's frames
    # Example (replace placeholders above with these):
    basic_info_frame_layout = [
        # Add empty Text element for vertical spacing at the top
        [sg.Text('')],
        # Center the Object ID / Count row using Push()
        [sg.Push(), sg.Text("Object ID:"), sg.Input(key=KEY_OBJECT_ID, tooltip="Unique identifier for the object (cannot be changed after creation)", disabled=True, size=(30,1)), sg.Text("Count:"), sg.Input(key=KEY_OBJECT_COUNT, tooltip="Internal count, not editable", size=(8,1), disabled=True), sg.Push()],
        # Add empty Text element for vertical spacing below ID/Count
        [sg.Text('')],
        # Adjust Name row: Set label size, increase input size
        [sg.Text("Name:", size=(15, 1)), sg.Input(key=KEY_OBJECT_NAME, tooltip="Display name shown to the player", size=(60,1)), sg.Checkbox("Is Plural?", key=KEY_OBJECT_IS_PLURAL, tooltip="Check if the name refers to multiple items (e.g., 'boots')")],
        # Add Synonyms row here: Set label size (inc fix), match input size
        [sg.Text("Synonyms (CSV):", size=(15, 1)), sg.Input(key=KEY_OBJECT_SYNONYMS, tooltip="Comma-separated alternative names (e.g., torch, light)", size=(60,1))],
        [sg.Text("Category:", size=(15, 1)), sg.Combo(values=get_object_categories(), key=KEY_OBJECT_CATEGORY, tooltip="General classification for game logic", size=(20,1), readonly=True)],
        [sg.Text("Location:", size=(15, 1)), sg.Combo(values=manager.get_room_ids(), key=KEY_OBJECT_LOCATION, tooltip="Room ID where the object is initially located (or 'inventory')", size=(25,1), readonly=True, enable_events=True)], # Room dropdown
        [sg.Text("Area in Room:", size=(15, 1)), sg.Combo(values=[], key=KEY_OBJECT_AREA_LOCATION, tooltip="Specific area within the room (if applicable)", size=(25, 1), readonly=True, disabled=True)], # Area dropdown
        [sg.Text("Weight:", size=(15, 1)), sg.Input(key=KEY_OBJECT_WEIGHT, tooltip="Weight in kg (affects carrying/moving)", size=(8,1)), sg.Text("Size:"), sg.Input(key=KEY_OBJECT_SIZE, tooltip="Space taken in inventory (if takeable)", size=(8,1))],
        # Combine Description label and Multiline onto one row for alignment
        [sg.Text("Description:", size=(15, 1)), sg.Multiline(key=KEY_OBJECT_DESCRIPTION, tooltip="Detailed description shown when examining", size=(75, 7))],
    ]

    properties_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        [sg.Checkbox("Takeable", key=KEY_PROP_IS_TAKEABLE, tooltip="Can the player pick this up?"), sg.Checkbox("Interactive", key=KEY_PROP_IS_INTERACTIVE, default=True, tooltip="Does this object have specific actions?"), sg.Checkbox("Dangerous", key=KEY_PROP_IS_DANGEROUS, tooltip="Can this object harm the player?"), sg.Checkbox("Destroyable", key=KEY_PROP_IS_DESTROYABLE, tooltip="Can this object be destroyed?")],
        [sg.Checkbox("Operational", key=KEY_PROP_IS_OPERATIONAL, tooltip="Can this object be turned on/off or operated?"), sg.Checkbox("Edible", key=KEY_PROP_IS_EDIBLE, tooltip="Can the player eat this?")],
        [sg.Checkbox("Movable", key=KEY_PROP_IS_MOVABLE, tooltip="Can the player push/pull this (if not takeable)?"), sg.Checkbox("Flammable", key=KEY_PROP_IS_FLAMMABLE, tooltip="Can this object catch fire?"), sg.Checkbox("Toxic", key=KEY_PROP_IS_TOXIC, tooltip="Is this object poisonous?")],
        [sg.Checkbox("Food", key=KEY_PROP_IS_FOOD, tooltip="Is this specifically food (subset of edible)?"), sg.Checkbox("Cookable", key=KEY_PROP_IS_COOKABLE, tooltip="Can this object be cooked?"), sg.Checkbox("Consumable", key=KEY_PROP_IS_CONSUMABLE, tooltip="Is this used up when interacted with (e.g., medkit)?")],
        [sg.Checkbox("Has Durability", key=KEY_PROP_HAS_DURABILITY, enable_events=True, tooltip="Does this object have a durability value?"), sg.Checkbox("Hackable", key=KEY_PROP_IS_HACKABLE, tooltip="Can the player attempt to hack this?"), sg.Checkbox("Rechargeable", key=KEY_PROP_IS_RECHARGEABLE, tooltip="Can this object be recharged?")], # Removed KEY_PROP_IS_HIDDEN from this line
        [sg.Checkbox("Fuel Source", key=KEY_PROP_IS_FUEL_SOURCE, tooltip="Can this object be used as fuel?"), sg.Checkbox("Regenerates", key=KEY_PROP_REGENERATES, tooltip="Does this object replenish itself?"), sg.Checkbox("Modular", key=KEY_PROP_IS_MODULAR, tooltip="Can this object accept modules/upgrades?"), sg.Checkbox("Stored", key=KEY_PROP_IS_STORED, tooltip="Is this primarily digital data stored elsewhere?")], # is_stored?
        [sg.Checkbox("Transferable", key=KEY_PROP_IS_TRANSFERABLE, tooltip="Can this digital item be transferred?"), sg.Checkbox("Activatable", key=KEY_PROP_IS_ACTIVATABLE, tooltip="Does this require specific activation?"), sg.Checkbox("Networked", key=KEY_PROP_IS_NETWORKED, tooltip="Is this connected to a network?")],
        [sg.Checkbox("Requires Power", key=KEY_PROP_REQUIRES_POWER, tooltip="Does this need power to function?"), sg.Checkbox("Requires Item", key=KEY_PROP_REQUIRES_ITEM, tooltip="Does interaction require a specific item?"), sg.Checkbox("Has Security", key=KEY_PROP_HAS_SECURITY, tooltip="Is this protected by security systems?")],
        [sg.Checkbox("Sensitive", key=KEY_PROP_IS_SENSITIVE, tooltip="Does this react to environmental changes?"), sg.Checkbox("Fragile", key=KEY_PROP_IS_FRAGILE, tooltip="Is this easily broken?"), sg.Checkbox("Secret", key=KEY_PROP_IS_SECRET, tooltip="Does this contain a secret?")],
        [sg.Checkbox("Is Surface", key=KEY_PROP_IS_SURFACE, tooltip="Can items be placed on top of this?"), sg.Checkbox("Is Charger", key=KEY_PROP_IS_CHARGER, tooltip="Can this recharge other items?")], # NEW SURFACE/CHARGER
        [sg.Checkbox("Initially Visible?", key=KEY_OBJECT_INITIAL_STATE, default=True, tooltip="Is the object visible when the player enters the room?")],
        [sg.HorizontalSeparator()],
        # Add Durability input back
        [sg.Text("Durability:"), sg.Input(key=KEY_PROP_DURABILITY, tooltip="Object health/uses remaining (if Has Durability)", size=(8,1), disabled=True)],
        [sg.Checkbox("Openable/Closable", key=KEY_PROP_IS_OPENABLE_CLOSABLE, enable_events=True, tooltip="Can this object be opened and closed (e.g., doors, containers, books)?")],
    ]

    # Define the new "Properties I" tab layout with frames
    properties_tab_I_layout = [
        [sg.Text('')], # Add space at the top of the tab
        [sg.Frame(None, [ # Frame title set to None, using Text element below for bold title
            [sg.Text("Core Interaction & Visibility", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Initially Visible?", key=KEY_OBJECT_INITIAL_STATE, default=True, tooltip="Is the object visible when the player enters the room?", size=(25,None)),
             sg.Text("Visible on load; uncheck for event/search reveals.", expand_x=True)],
            [sg.Checkbox("Takeable", key=KEY_PROP_IS_TAKEABLE, tooltip="Can the player pick this up?", size=(25,None)),
             sg.Text("Player can pick up and add to inventory/hands.", expand_x=True)],
            [sg.Checkbox("Interactive", key=KEY_PROP_IS_INTERACTIVE, default=True, tooltip="Does this object have specific actions?", size=(25,None)),
             sg.Text("Object has unique commands beyond generic ones.", expand_x=True)],
            [sg.Checkbox("Movable", key=KEY_PROP_IS_MOVABLE, tooltip="Can the player push/pull this (if not takeable)?", size=(25,None)),
             sg.Text("If not takeable, player can push/pull object.", expand_x=True)]
        ], expand_x=True)],
        [sg.Text('')], # Add space between this frame and the next
        [sg.Frame(None, [ # Frame title set to None
            [sg.Text("Physical Attributes & Hazards", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Is Openable/Closable?", key=KEY_PROP_IS_OPENABLE_CLOSABLE, enable_events=True, tooltip="Can this object be opened and closed (e.g., doors, containers, books)?", size=(25,None)), # <-- NEW CHECKBOX
             sg.Text("Object can be opened and closed (doors, containers, books).", expand_x=True)], # <-- NEW TEXT
            [sg.Checkbox("Destroyable", key=KEY_PROP_IS_DESTROYABLE, tooltip="Can this object be destroyed?", size=(25,None)),
             sg.Text("Object can be damaged and ultimately destroyed.", expand_x=True)],
            [sg.Checkbox("Has Durability", key=KEY_PROP_HAS_DURABILITY, enable_events=True, tooltip="Does this object have a durability value?", size=(25,None)),
             sg.Text("Object has health/uses. Enables Durability field below.", expand_x=True)],
            [sg.Text("Durability:", size=(24,None)), sg.Input(key=KEY_PROP_DURABILITY, tooltip="Object health/uses remaining (if Has Durability)", size=(10,1), disabled=True)], # Aligned with checkbox text start
            [sg.Checkbox("Fragile", key=KEY_PROP_IS_FRAGILE, tooltip="Is this easily broken?", size=(25,None)),
             sg.Text("Object is easily broken or damaged.", expand_x=True)],
            [sg.Checkbox("Is Surface", key=KEY_PROP_IS_SURFACE, tooltip="Can items be placed on top of this?", size=(25,None)),
             sg.Text("Allows other items to be placed on this object.", expand_x=True)],
            [sg.Checkbox("Dangerous", key=KEY_PROP_IS_DANGEROUS, tooltip="Can this object harm the player?", size=(25,None)),
             sg.Text("Object can cause harm or negative effects to the player.", expand_x=True)],
            [sg.Checkbox("Flammable", key=KEY_PROP_IS_FLAMMABLE, tooltip="Can this object catch fire?", size=(25,None)),
             sg.Text("Object can be set on fire.", expand_x=True)],
            [sg.Checkbox("Toxic", key=KEY_PROP_IS_TOXIC, tooltip="Is this object poisonous?", size=(25,None)),
             sg.Text("Object is poisonous or emits harmful substances.", expand_x=True)]
        ], expand_x=True)]
        # Sustenance frame removed from here
    ]
    
    # Define the new "Properties II" tab layout with frames
    properties_tab_II_layout = [
        [sg.Text('')], # Add space at the top of the tab
        [sg.Frame(None, [ # Frame title set to None
            [sg.Text("Sustenance", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Edible", key=KEY_PROP_IS_EDIBLE, tooltip="Can the player eat this?", size=(25,None)),
             sg.Text("Player can consume this item.", expand_x=True)],
            [sg.Checkbox("Food", key=KEY_PROP_IS_FOOD, tooltip="Is this specifically food (subset of edible)?", size=(25,None)),
             sg.Text("Specifically designated as a food item (subset of Edible).", expand_x=True)],
            [sg.Checkbox("Cookable", key=KEY_PROP_IS_COOKABLE, tooltip="Can this object be cooked?", size=(25,None)),
             sg.Text("Item can be cooked, possibly changing its properties.", expand_x=True)],
            [sg.Checkbox("Consumable", key=KEY_PROP_IS_CONSUMABLE, tooltip="Is this used up when interacted with (e.g., medkit)?", size=(25,None)),
             sg.Text("Item is used up entirely upon interaction (e.g., medkit).", expand_x=True)]
        ], expand_x=True)],
        [sg.Text('')], # Space between this frame and the next
        [sg.Frame(None, [ # Frame title set to None
            [sg.Text("Operational & Power", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Operational", key=KEY_PROP_IS_OPERATIONAL, tooltip="Can this object be turned on/off or operated?", size=(25,None)),
             sg.Text("Object can be turned on/off or operated.", expand_x=True)],
            [sg.Checkbox("Requires Power", key=KEY_PROP_REQUIRES_POWER, tooltip="Does this need power to function?", size=(25,None)),
             sg.Text("Object needs a power source to function.", expand_x=True)],
            [sg.Checkbox("Rechargeable", key=KEY_PROP_IS_RECHARGEABLE, tooltip="Can this object be recharged?", size=(25,None)),
             sg.Text("Object's power can be replenished.", expand_x=True)],
            [sg.Checkbox("Is Charger", key=KEY_PROP_IS_CHARGER, tooltip="Can this recharge other items?", size=(25,None)),
             sg.Text("This object can recharge other rechargeable items.", expand_x=True)],
            [sg.Checkbox("Fuel Source", key=KEY_PROP_IS_FUEL_SOURCE, tooltip="Can this object be used as fuel?", size=(25,None)),
             sg.Text("Can be used as fuel for other devices/systems.", expand_x=True)]
        ], expand_x=True)]
        # Digital, Security & Environment and Advanced & Unique Mechanics frames removed from here
    ]

    # Define the new "Properties III" tab layout with frames
    properties_tab_III_layout = [
        [sg.Text('')], # Add space at the top of the tab
        [sg.Frame(None, [ # Frame title set to None
            [sg.Text("Digital, Security & Environment", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Hackable", key=KEY_PROP_IS_HACKABLE, tooltip="Can the player attempt to hack this?", size=(25,None)),
             sg.Text("Player can attempt to hack this object.", expand_x=True)],
            [sg.Checkbox("Stored", key=KEY_PROP_IS_STORED, tooltip="Is this primarily digital data stored elsewhere?", size=(25,None)),
             sg.Text("Primarily digital data (e.g., a file, log).", expand_x=True)],
            [sg.Checkbox("Transferable", key=KEY_PROP_IS_TRANSFERABLE, tooltip="Can this digital item be transferred?", size=(25,None)),
             sg.Text("Digital item can be moved/copied.", expand_x=True)],
            [sg.Checkbox("Networked", key=KEY_PROP_IS_NETWORKED, tooltip="Is this connected to a network?", size=(25,None)),
             sg.Text("Object is connected to some form of network.", expand_x=True)],
            [sg.Checkbox("Has Security", key=KEY_PROP_HAS_SECURITY, tooltip="Is this protected by security systems?", size=(25,None)),
             sg.Text("Protected by security measures (alarms, defenses).", expand_x=True)],
            [sg.Checkbox("Sensitive", key=KEY_PROP_IS_SENSITIVE, tooltip="Does this react to environmental changes?", size=(25,None)),
             sg.Text("Reacts to changes in the environment (temp, radiation).", expand_x=True)]
        ], expand_x=True)],
        [sg.Text('')], # Space between this frame and the next
        [sg.Frame(None, [ # Frame title set to None
            [sg.Text("Advanced & Unique Mechanics", font=("Helvetica", 11, "bold"))],
            [sg.HorizontalSeparator()],
            [sg.Checkbox("Activatable", key=KEY_PROP_IS_ACTIVATABLE, tooltip="Does this require specific activation?", size=(25,None)),
             sg.Text("Requires a specific activation sequence or condition.", expand_x=True)],
            [sg.Checkbox("Regenerates", key=KEY_PROP_REGENERATES, tooltip="Does this object replenish itself?", size=(25,None)),
             sg.Text("Object replenishes itself or its resources over time.", expand_x=True)],
            [sg.Checkbox("Modular", key=KEY_PROP_IS_MODULAR, tooltip="Can this object accept modules/upgrades?", size=(25,None)),
             sg.Text("Can accept modules, upgrades, or attachments.", expand_x=True)],
            [sg.Checkbox("Requires Item", key=KEY_PROP_REQUIRES_ITEM, tooltip="Does interaction require a specific item for this property flag to be true?", size=(25,None)),
             sg.Text("Interaction needs a specific item to be held/used.", expand_x=True)],
            [sg.Checkbox("Secret", key=KEY_PROP_IS_SECRET, tooltip="Does this contain a secret or hidden aspect beyond normal interaction?", size=(25,None)),
             sg.Text("Contains a hidden aspect or requires special discovery.", expand_x=True)]
        ], expand_x=True)]
    ]

    # State & Lock frame is now empty, controls moved elsewhere
    state_lock_frame_layout = []

    interaction_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        [sg.Text("Required State:"), sg.Input(key=KEY_INTERACTION_REQUIRED_STATE, tooltip="State the object must be in for interaction (e.g., 'powered_on')")],
        [sg.Text("Required Items (CSV:)"), sg.Input(key=KEY_INTERACTION_REQUIRED_ITEMS, tooltip="Comma-separated object IDs needed to interact")],
        [sg.Text("Primary Actions (CSV:)"), sg.Input(key=KEY_INTERACTION_PRIMARY_ACTIONS, tooltip="Comma-separated verbs player can use (e.g., use, operate)")],
        [sg.Text("Effects (key:value:)"), sg.Multiline(key=KEY_INTERACTION_EFFECTS, tooltip="Outcomes (one per line, e.g., state_change:powered_off)", size=(60, 4))], # Adjusted label and tooltip
        [sg.Text("Success Message:"), sg.Multiline(key=KEY_INTERACTION_SUCCESS, tooltip="Message shown on successful interaction", size=(60, 3))],
        [sg.Text("Failure Message:"), sg.Multiline(key=KEY_INTERACTION_FAILURE, tooltip="Message shown on failed interaction", size=(60, 3))],
    ]

    other_details_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        # Storage controls
        [sg.Checkbox("Is Storage?", key=KEY_PROP_IS_STORAGE, enable_events=True, tooltip="Can this object hold other objects?")],
        [sg.Text("Capacity:"), sg.Input(key=KEY_PROP_STORAGE_CAPACITY, tooltip="How many items/units it can hold (if Storage)", size=(8,1), disabled=True), sg.Checkbox("Stores Liquids?", key=KEY_PROP_CAN_STORE_LIQUIDS, tooltip="Can this container specifically hold liquids? (if Storage)", disabled=True)],
        [sg.HorizontalSeparator()],
        # Storage Contents - Changed label, disabled Multiline
        [sg.Text("Storage Contents:")],
        [sg.Multiline(key=KEY_OBJECT_STORAGE_CONTENTS, tooltip="Objects currently stored inside (managed below)", size=(60, 4), disabled=True)],
        # Add new controls for managing contents
        [sg.Text("Item:"),
         sg.Combo(values=manager.get_object_ids(), key=KEY_STORAGE_ITEM_SELECT, readonly=True, size=(30, 1), tooltip="Select an object ID to add or remove from contents"),
         sg.Button("Add", key=KEY_STORAGE_ADD_BUTTON, tooltip="Add selected item to contents"),
         sg.Button("Delete", key=KEY_STORAGE_DELETE_BUTTON, tooltip="Remove selected item from contents")]
        # Moved Lock Controls from here
    ]

    wearability_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        # Wearable checkbox
        [sg.Checkbox("Is Wearable?", key=KEY_PROP_IS_WEARABLE, enable_events=True, tooltip="Can the player wear this?")],
        [sg.Text("Wear Area:"), sg.Combo(values=[area.value for area in WearArea], key=KEY_WEAR_AREA, tooltip="Where on the body this is worn (if Wearable)", size=(20, 1), readonly=True, disabled=True)],
        [sg.Text("Wear Layer:"), sg.Combo(values=[str(i) for i in WEAR_LAYER_OPTIONS], key=KEY_WEAR_LAYER, tooltip="Clothing layer (0=base, higher=outer) (if Wearable)", size=(5, 1), readonly=True, disabled=True)]
    ]

    # Weapon Tab Layout - Remove Durability
    weapons_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        [sg.Checkbox("Is Weapon?", key=KEY_PROP_IS_WEAPON, enable_events=True, tooltip="Can this object be used as a weapon?")],
        [sg.Text("Damage:"), sg.Input(key=KEY_PROP_DAMAGE, tooltip="Damage dealt (if Weapon)", size=(8,1), disabled=True), sg.Text("Range:"), sg.Input(key=KEY_PROP_RANGE, tooltip="Effective range (if Weapon)", size=(8,1), disabled=True)]
    ]

    digital_content_frame_layout = [
         [sg.Text("Digital Content (file_id: content, use --- separator:)"), sg.Multiline(key=KEY_OBJECT_DIGITAL_CONTENT, tooltip="For terminals, tablets: Define files/logs accessible (file_name:Text content)", size=(60, 10))],
    ]

    # --- NEW: Misc Tab Layout ---
    misc_frame_layout = [
        # Add vertical spacing
        [sg.Text('')],
        [sg.Text("Power State:"), sg.Input(key=KEY_OBJECT_POWER_STATE, tooltip="Current power status (e.g., online, offline) - affects interactions", size=(20,1))],
        [sg.HorizontalSeparator()],
        [sg.Checkbox("Is Open?", key=KEY_OBJECT_IS_OPEN, default=False, tooltip="Is the object initially in an open state?")],
        [sg.Checkbox("Is Locked?", key=KEY_OBJECT_IS_LOCKED, enable_events=True, tooltip="Check if the object starts locked")],
        [sg.Text("Lock Type:"), sg.Input(key=KEY_OBJECT_LOCK_TYPE, tooltip="Mechanism: key, code, biometric (if Locked)", size=(20,1), disabled=True)],
        [sg.Text("Lock Code:"), sg.Input(key=KEY_OBJECT_LOCK_CODE, tooltip="Required code (if Lock Type is 'code' and Locked)", size=(20,1), disabled=True)],
        [sg.Text("Key Object ID:"), sg.Combo(all_key_ids, key=KEY_OBJECT_LOCK_KEY_ID, tooltip="Object ID of the key required (if Lock Type is 'key' and Locked)", size=(30,1), disabled=True)],
        [sg.HorizontalSeparator()],
        # Moved State Descriptions here
        [sg.Text("State Descriptions (state_name:description:)"), sg.Multiline(key=KEY_OBJECT_STATE_DESCRIPTIONS, tooltip="Descriptions for different object states (one per line, e.g., broken:It is shattered)", size=(60, 4))]
    ]

    # --- Define the Tab Group --- Remove State&Lock, Add Misc
    tab_group_layout = [
        [sg.TabGroup([
            [sg.Tab("Basic Info", basic_info_frame_layout, key='-TAB_BASIC-')],
            [sg.Tab("Properties I", properties_tab_I_layout, key='-TAB_PROPS_1-')], # New Properties I
            [sg.Tab("Properties II", properties_tab_II_layout, key='-TAB_PROPS_2-')], # New Properties II
            [sg.Tab("Properties III", properties_tab_III_layout, key='-TAB_PROPS_3-')], # New Properties III
            [sg.Tab("Storage", other_details_frame_layout, key='-TAB_OTHER-')],
            [sg.Tab("Weapons", weapons_frame_layout, key='-TAB_WEAPON-')],
            # Removed State & Lock tab
            [sg.Tab("Interactions", interaction_frame_layout, key='-TAB_INTERACT-')],
            [sg.Tab("Wearability", wearability_frame_layout, key='-TAB_WEAR-')],
            [sg.Tab("Digital Content", digital_content_frame_layout, key='-TAB_DIGITAL-')],
            [sg.Tab("States", misc_frame_layout, key='-TAB_STATES-')] # Renamed Misc tab to States
        ], key='-TAB_GROUP-', expand_y=True, expand_x=True) # Make tab group expand
        ]
    ]

    # --- Define the Right Column Layout (YAML Preview & Buttons) ---
    right_column_layout = [
        [sg.Text("YAML Preview:")],
        [sg.Multiline(key=KEY_YAML_PREVIEW, size=(80, 20), expand_x=True, expand_y=True)], # Make YAML preview expand
        [sg.HorizontalSeparator()],
        [
            sg.Button("Save", key=KEY_SAVE_BUTTON, tooltip="Save current object data to YAML files", button_color=('white', 'green')),
            sg.Button("Delete", key=KEY_DELETE_BUTTON, tooltip="Permanently delete the loaded object", button_color=('white', 'red')),
            sg.Button("Validate", key=KEY_VALIDATE_BUTTON, tooltip="Check current data for errors before saving"),
            sg.Push(), # Push buttons left
            sg.Button("Close", key=KEY_CLOSE_BUTTON, tooltip="Exit the object editor")
        ],
        [sg.StatusBar("Ready", size=(60, 1), key=KEY_STATUS_BAR)]
    ]

    # --- Main Window Layout Definition ---
    layout = [
        [top_controls_layout], # Top row for controls
        [sg.HorizontalSeparator()],
        [
            sg.Column(tab_group_layout, expand_x=True, expand_y=True), # Left column for tabs
            sg.VSeparator(), # Vertical separator
            sg.Column(right_column_layout, expand_x=True, expand_y=True) # Right column for YAML/buttons
        ]
    ]

    # --- Window Creation ---
    # Set resizable=True and finalize=True
    window = sg.Window("Starship Object Editor", layout, resizable=True, finalize=True, icon=ICON_PATH)

    # Update count initially (set value for the Text element)
    window[KEY_TOTAL_OBJECT_COUNT].update(str(manager.get_object_count()))

    # --- Main Event Loop ---
    selected_object_id = None
    current_object_data = None
    is_new_object = False

    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == KEY_CLOSE_BUTTON:
            logging.info("Close button clicked. Exiting editor.")
            break

        elif event == KEY_OBJECT_IS_LOCKED:
            is_locked = values[KEY_OBJECT_IS_LOCKED]
            window[KEY_OBJECT_LOCK_TYPE].update(disabled=not is_locked)
            window[KEY_OBJECT_LOCK_CODE].update(disabled=not is_locked)
            window[KEY_OBJECT_LOCK_KEY_ID].update(disabled=not is_locked)
            if not is_locked:
                window[KEY_OBJECT_LOCK_TYPE].update("")
                window[KEY_OBJECT_LOCK_CODE].update("")
                window[KEY_OBJECT_LOCK_KEY_ID].update("")


        elif event == KEY_OBJECT_DROPDOWN or event == KEY_LOAD_BUTTON:
            object_id = values[KEY_OBJECT_DROPDOWN]
            if object_id:
                logging.info(f"Loading object: {object_id}")
                data = manager.get_object_by_id(object_id)
                if data:
                    current_object_data = data # Store loaded data
                    populate_fields(window, data, manager)
                    window[KEY_OBJECT_ID].update(disabled=True)
                    # Re-enable top dropdown after successful load
                    window[KEY_OBJECT_DROPDOWN].update(disabled=False)
                    window[KEY_STATUS_BAR].update(f"Loaded object: {object_id}")
                    room_id = data.get("location", "")
                    if room_id and room_id != "inventory":
                         areas = manager.get_area_ids_for_room(room_id)
                         window[KEY_OBJECT_AREA_LOCATION].update(disabled=False, values=areas, value=None)
                    else:
                         window[KEY_OBJECT_AREA_LOCATION].update(disabled=True, values=[], value=None)
                else:
                    sg.popup_error(f"Could not load data for object: {object_id}")
                    window[KEY_STATUS_BAR].update(f"Error loading object: {object_id}", text_color="red")
                    current_object_data = None
                    window[KEY_SAVE_BUTTON].update(disabled=True)
                    window[KEY_DELETE_BUTTON].update(disabled=True)
                    window[KEY_OBJECT_AREA_LOCATION].update(disabled=True, values=[], value=None)
                    # Ensure top dropdown is enabled even on load failure?
                    window[KEY_OBJECT_DROPDOWN].update(disabled=False)
                    window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
            else:
                 window[KEY_STATUS_BAR].update("Select an object ID from the dropdown to load.")


        elif event == KEY_NEW_BUTTON:
            logging.info("New button clicked. Clearing fields.")
            clear_fields(window)
            current_object_data = None # Clear any loaded data
            # Fix 1: Clear the top dropdown value but keep it enabled
            window[KEY_OBJECT_DROPDOWN].update(value='', disabled=False) # Ensure enabled
            # ID field is enabled by clear_fields
            window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'lightblue'))
            window[KEY_STATUS_BAR].update("Enter details for the new object.")
            # Set focus to the newly enabled Object ID input field as the last UI step
            window[KEY_OBJECT_ID].set_focus()
            # Save/Delete button states are handled in clear_fields

        elif event == KEY_VALIDATE_BUTTON:
            logging.info("Validate button clicked.")
            window[KEY_STATUS_BAR].update("Validating current data...")
            gathered_data, obj_id, orig_id = gather_data_from_fields(window, manager)

            if gathered_data:
                 is_new = not window[KEY_OBJECT_ID].Disabled
                 validation_errors = validate_object_data(gathered_data, is_new, manager)
                 if not validation_errors:
                     current_object_data = gathered_data
                     update_yaml_preview(window, current_object_data, manager)
                     window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'green'))
                     window[KEY_STATUS_BAR].update(f"Validation successful for: {obj_id}")
                     window[KEY_SAVE_BUTTON].update(disabled=False)
                 else:
                     error_message = "Validation Failed:\n" + "\n".join(f"- {e}" for e in validation_errors)
                     sg.popup_error(error_message, title="Validation Errors")
                     window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                     window[KEY_STATUS_BAR].update("Validation failed. See popup for details.", text_color="red")
                     window[KEY_SAVE_BUTTON].update(disabled=True)
            else:
                 window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                 window[KEY_STATUS_BAR].update("Error gathering data for validation.", text_color="red")
                 window[KEY_SAVE_BUTTON].update(disabled=True)


        elif event == KEY_SAVE_BUTTON:
             logging.info("Save button clicked.")
             window[KEY_STATUS_BAR].update("Validating before saving...")
             gathered_data, obj_id, orig_id = gather_data_from_fields(window, manager)

             if gathered_data:
                 is_new = not window[KEY_OBJECT_ID].Disabled
                 validation_errors = validate_object_data(gathered_data, is_new, manager)
                 if not validation_errors:
                     # Prompt user before saving
                     if sg.popup_yes_no("Are you sure you want to save these changes?") != 'Yes':
                          window[KEY_STATUS_BAR].update("Save cancelled by user.")
                          continue # Stop if user cancels

                     # Proceed with saving
                     current_object_data = gathered_data # Update internal state for preview if needed
                     update_yaml_preview(window, current_object_data, manager) # Update preview

                     save_successful = False
                     action_successful = False
                     object_id_to_save = obj_id # Use the ID gathered from fields
                     original_id_to_check = orig_id # ID used for loading (for updates)

                     # Use correct save logic based on new/existing
                     try:
                          if is_new:
                              logging.debug(f"Attempting to add new object: {object_id_to_save}")
                              action_successful = manager.add_object(gathered_data)
                              if not action_successful:
                                   sg.popup_error(f"Failed to add object '{object_id_to_save}' internally (maybe duplicate ID?).")
                          else: # Existing object
                              logging.debug(f"Attempting to update object: {original_id_to_check} -> {object_id_to_save}")
                              # Note: If ID changed, gather_data uses the NEW ID.
                              # update_object needs the ORIGINAL ID to find it.
                              action_successful = manager.update_object(original_id_to_check, gathered_data)
                              if not action_successful:
                                   sg.popup_error(f"Failed to update object '{original_id_to_check}' internally.")

                          # If add/update was successful, save location and files
                          if action_successful:
                              logging.debug(f"Add/Update successful. Now saving location and files for {object_id_to_save}")
                              # Get location details directly from gathered data
                              final_room_id = gathered_data.get('location')
                              final_area_id = gathered_data.get('area_location')
                              save_successful = manager.save_object_and_location(object_id_to_save, final_room_id, final_area_id)

                     except Exception as e:
                          logging.exception(f"Error during save operation for {object_id_to_save}")
                          sg.popup_error(f"An unexpected error occurred during save.\nError: {e}")
                          save_successful = False # Ensure failure state

                     # Handle final outcome
                     if save_successful:
                         sg.popup(f"Object '{object_id_to_save}' saved successfully!")
                         window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'green'))
                         window[KEY_STATUS_BAR].update(f"Object '{object_id_to_save}' saved.")
                         # Refresh dropdown and total count
                         all_object_ids = manager.get_object_ids()
                         window[KEY_OBJECT_DROPDOWN].update(values=all_object_ids, value=object_id_to_save)
                         # Update Text field count
                         window[KEY_TOTAL_OBJECT_COUNT].update(str(len(all_object_ids)))
                         # Refresh Key Object ID dropdown as well
                         new_key_ids = manager.get_key_object_ids()
                         window[KEY_OBJECT_LOCK_KEY_ID].update(values=new_key_ids, value='') # Clear selection
                         # Refresh Storage Item Select dropdown as well
                         window[KEY_STORAGE_ITEM_SELECT].update(values=all_object_ids, value='') # Clear selection
                         window[KEY_OBJECT_ID].update(disabled=True) # Disable ID field after successful save
                         window[KEY_DELETE_BUTTON].update(disabled=False)
                     else:
                         # Error message already shown by add/update/save_object_and_location or exception block
                         window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                         window[KEY_STATUS_BAR].update(f"Save failed for '{object_id_to_save}'. Check logs.", text_color="red")
                 else:
                     # Validation failed just before save attempt
                     error_message = "Validation Failed (cannot save):\n" + "\n".join(f"- {e}" for e in validation_errors)
                     sg.popup_error(error_message, title="Validation Errors")
                     window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                     window[KEY_STATUS_BAR].update("Validation failed. Cannot save.", text_color="red")
             else:
                  # Error during data gathering
                  window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                  window[KEY_STATUS_BAR].update("Error gathering data. Cannot save.", text_color="red")


        elif event == KEY_DELETE_BUTTON:
             object_id = values.get(KEY_OBJECT_DROPDOWN)
             if object_id and not window[KEY_OBJECT_ID].Disabled:
                  logging.warning("Delete clicked, but ID field is enabled (seems like 'New' state).")
                  object_id = None

             if not object_id:
                  sg.popup_error("No object loaded to delete. Load an object first.")
                  continue

             confirm = sg.popup_yes_no(f"Are you sure you want to permanently delete object '{object_id}'?")
             if confirm == "Yes":
                 logging.info(f"Attempting to delete object: {object_id}")
                 if manager.delete_object(object_id):
                     sg.popup(f"Object '{object_id}' deleted successfully.")
                     clear_fields(window)
                     all_object_ids = manager.get_object_ids()
                     window[KEY_OBJECT_DROPDOWN].update(values=all_object_ids, value='')
                     # Update Text field count
                     window[KEY_TOTAL_OBJECT_COUNT].update(str(len(all_object_ids)))
                     current_object_data = None
                     window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'orange'))
                     window[KEY_STATUS_BAR].update(f"Object '{object_id}' deleted.")
                     window[KEY_SAVE_BUTTON].update(disabled=True)
                     window[KEY_DELETE_BUTTON].update(disabled=True)
                     window[KEY_OBJECT_AREA_LOCATION].update(disabled=True, values=[], value=None)
                 else:
                      sg.popup_error(f"Failed to delete object '{object_id}'. It might not exist or there was a file error.")
                      window[KEY_VALIDATE_BUTTON].update(button_color=('white', 'red'))
                      window[KEY_STATUS_BAR].update(f"Error deleting object '{object_id}'.", text_color="red")

        elif event == KEY_OBJECT_LOCATION:
            selected_room_id = values[KEY_OBJECT_LOCATION]
            logging.debug(f"Room selection changed to: {selected_room_id}")
            if selected_room_id and selected_room_id != "inventory":
                room_areas = manager.get_area_ids_for_room(selected_room_id)
                logging.debug(f"Areas for room {selected_room_id}: {room_areas}")
                window[KEY_OBJECT_AREA_LOCATION].update(disabled=False, values=room_areas, value=None)
            else:
                logging.debug(f"Disabling area dropdown for location: {selected_room_id}")
                window[KEY_OBJECT_AREA_LOCATION].update(disabled=True, values=[], value=None)

        elif event == KEY_PROP_IS_WEARABLE:
             is_wearable_checked = values[KEY_PROP_IS_WEARABLE]
             window[KEY_WEAR_AREA].update(disabled=not is_wearable_checked)
             window[KEY_WEAR_LAYER].update(disabled=not is_wearable_checked)
             if not is_wearable_checked:
                  window[KEY_WEAR_AREA].update("")
                  window[KEY_WEAR_LAYER].update("")

        elif event == KEY_PROP_IS_STORAGE:
             is_storage_checked = values[KEY_PROP_IS_STORAGE]
             window[KEY_PROP_STORAGE_CAPACITY].update(disabled=not is_storage_checked)
             window[KEY_PROP_CAN_STORE_LIQUIDS].update(disabled=not is_storage_checked)
             if not is_storage_checked:
                  window[KEY_PROP_STORAGE_CAPACITY].update("")
                  window[KEY_PROP_CAN_STORE_LIQUIDS].update(False)

        elif event == KEY_PROP_IS_WEAPON:
             is_weapon_checked = values[KEY_PROP_IS_WEAPON]
             window[KEY_PROP_DAMAGE].update(disabled=not is_weapon_checked)
             window[KEY_PROP_RANGE].update(disabled=not is_weapon_checked)
             if not is_weapon_checked:
                  window[KEY_PROP_DAMAGE].update("")
                  window[KEY_PROP_RANGE].update("")

        # --- Add event handler for HAS_DURABILITY ---
        elif event == KEY_PROP_HAS_DURABILITY:
            has_durability_checked = values[KEY_PROP_HAS_DURABILITY]
            window[KEY_PROP_DURABILITY].update(disabled=not has_durability_checked)
            if not has_durability_checked:
                window[KEY_PROP_DURABILITY].update("")

        # --- Storage Contents Add/Delete Logic ---
        elif event == KEY_STORAGE_ADD_BUTTON:
            selected_item = values[KEY_STORAGE_ITEM_SELECT]
            if not selected_item:
                sg.popup_error("Please select an item from the dropdown to add.", title="Add Error")
                continue

            current_contents_str = window[KEY_OBJECT_STORAGE_CONTENTS].get()
            current_list = _parse_csv_to_list(current_contents_str)

            if selected_item not in current_list:
                current_list.append(selected_item)
                new_contents_str = _parse_list_to_csv(current_list)
                window[KEY_OBJECT_STORAGE_CONTENTS].update(new_contents_str)
                window[KEY_STATUS_BAR].update(f"Added '{selected_item}' to contents.")
            else:
                window[KEY_STATUS_BAR].update(f"Item '{selected_item}' is already in contents.", text_color="orange")

        elif event == KEY_STORAGE_DELETE_BUTTON:
            selected_item = values[KEY_STORAGE_ITEM_SELECT]
            if not selected_item:
                sg.popup_error("Please select an item from the dropdown to delete.", title="Delete Error")
                continue

            current_contents_str = window[KEY_OBJECT_STORAGE_CONTENTS].get()
            current_list = _parse_csv_to_list(current_contents_str)

            if selected_item in current_list:
                current_list.remove(selected_item)
                new_contents_str = _parse_list_to_csv(current_list)
                window[KEY_OBJECT_STORAGE_CONTENTS].update(new_contents_str)
                window[KEY_STATUS_BAR].update(f"Removed '{selected_item}' from contents.")
            else:
                window[KEY_STATUS_BAR].update(f"Item '{selected_item}' not found in contents.", text_color="orange")

    window.close()
    logging.info("Object Editor closed.")

# --- Main Execution Guard ---
if __name__ == "__main__":
    main() 