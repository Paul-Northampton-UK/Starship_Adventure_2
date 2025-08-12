# tools/object_editor/ctk_object_editor.py
import customtkinter as ctk
from loguru import logger
import sys
from pathlib import Path
from enum import Enum
from tkinter import messagebox
from io import StringIO
import ruamel.yaml
from pydantic import ValidationError

# --- Custom Tooltip Class ---
class CustomToolTip:
    """
    Creates a tooltip for a given widget.
    This version ensures only one tooltip is visible at a time and adds a delay.
    """
    _active_tooltip = None
    _after_id = None

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.delay = 500  # 500ms delay
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)

    def on_enter(self, event=None):
        self.schedule_show()

    def on_leave(self, event=None):
        CustomToolTip.cancel_scheduled_show(self.widget)
        CustomToolTip.hide_tooltip()

    def schedule_show(self):
        CustomToolTip.cancel_scheduled_show(self.widget)
        CustomToolTip._after_id = self.widget.after(self.delay, self.show_tooltip)

    def show_tooltip(self):
        CustomToolTip.hide_tooltip()
        if not self.text or not self.widget.winfo_exists():
            return

        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25

        tooltip_window = ctk.CTkToplevel(self.widget)
        tooltip_window.wm_overrideredirect(True)
        tooltip_window.wm_geometry(f"+{x}+{y}")
        label = ctk.CTkLabel(tooltip_window, text=self.text, justify='left',
                             fg_color="gray20", corner_radius=5,
                             wraplength=250)
        label.pack(ipadx=5, ipady=5)
        CustomToolTip._active_tooltip = tooltip_window

    @classmethod
    def hide_tooltip(cls):
        if cls._active_tooltip:
            cls._active_tooltip.destroy()
            cls._active_tooltip = None

    @classmethod
    def cancel_scheduled_show(cls, widget):
        """Cancels any pending tooltip show events."""
        if cls._after_id:
            widget.after_cancel(cls._after_id)
            cls._after_id = None

# --- Add project root to Python path ---
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from tools.object_editor.object_data_manager import ObjectDataManager
from engine.schemas import ObjectCategory, ObjectProperties, Object as ObjectSchema, WearArea

# --- Help Texts ---
HELP_TEXTS = {
    "id": (
        "**Object ID (Unique Identifier)**\n\n"
        "A unique, machine-readable name for the object. This is the primary key for the object and cannot be changed after creation.\n\n"
        "**Best Practices:**\n"
        "- Use snake_case (e.g., 'player_cabin_door').\n"
        "- Be descriptive and include the location if relevant (e.g., 'nav_console', 'medbay_scanner').\n"
        "- Do not use spaces or special characters other than underscore.\n\n"
        "**Example:** `bridge_torch`"
    ),
    "name": (
        "**Object Name (In-Game)**\n\n"
        "The human-readable name for the object that the player will see in the game.\n\n"
        "**Best Practices:**\n"
        "- Use standard capitalization (e.g., 'A rusty keycard').\n"
        "- This name will be used in descriptions and messages, so make it clear and concise.\n\n"
        "**Example:** `A strange-looking torch`"
    ),
    "is_plural": (
        "**Is Plural?**\n\n"
        "Check this box if the object's name is grammatically plural.\n\n"
        "**Why?**\n"
        "This helps the game engine construct grammatically correct sentences. For example, the game will know to say 'There **are** boots here' instead of 'There **is** boots here'.\n\n"
        "**Examples of plural objects:** `boots`, `slippers`, `goggles`, `a pair of scissors`"
    ),
    "description": (
        "**Description**\n\n"
        "The detailed text a player sees when they use the 'examine' or 'look at' command on this object. This is your chance to add flavor, lore, or clues.\n\n"
        "**Best Practices:**\n"
        "- Be descriptive and engaging.\n"
        "- Mention any important details or features the player should notice.\n"
        "- You can hint at the object's purpose or how it might be used.\n\n"
        "**Example:** `The torch is made of a strange, dark metal that feels warm to the touch. A small, almost invisible seam runs along its side.`"
    ),
    "synonyms": (
        "**Synonyms (Comma-Separated)**\n\n"
        "A list of other words the player might use to refer to this object. The game's parser will recognize these as aliases for the object.\n\n"
        "**Do's and Don'ts:**\n"
        "- **DO:** Include common variations (e.g., 'light', 'lamp', 'flashlight' for a torch).\n"
        "- **DON'T:** Include verbs or actions (e.g., 'pick up').\n"
        "- **DO:** Separate each word with a comma.\n\n"
        "**Example:** `light, lamp, flashlight, torch`"
    ),
    "category": (
        "**Object Category**\n\n"
        "The general category this object belongs to. This can affect default behaviors and how the game engine treats the object.\n\n"
        "**Key Categories:**\n"
        "- **key_item:** Used to unlock things. Will appear in the 'Key Object ID' dropdown for lockable objects.\n"
        "- **container:** Can hold other objects.\n"
        "- **wearable:** Can be worn by the player.\n"
        "- **device:** Can be powered on/off or operated in some way.\n"
        "- **document:** Can be read.\n"
        "Select the most appropriate category."
    ),
    "location": (
        "**Location (Room ID)**\n\n"
        "The Room ID where this object is currently located. This determines where the object appears in the game world.\n\n"
        "**Important:**\n"
        "- If an object is held by the player (in their inventory, worn, or in hand), this should be left **blank**.\n"
        "- Select a valid Room ID from the dropdown list.\n"
        "- Changing this value will move the object in the game data."
    ),
    "area_in_room": (
        "**Area in Room (Area ID)**\n\n"
        "The specific Area ID within the selected Room where the object is located. This allows you to place objects in sub-locations within a room (e.g., 'on the desk', 'inside the crate').\n\n"
        "**Requirements:**\n"
        "- A 'Location (Room ID)' must be selected first.\n"
        "- The selected room must have defined areas."
    ),
    "weight": (
        "**Weight**\n\n"
        "The weight of the object, as a numerical value (can be a decimal).\n\n"
        "**Game Mechanics:**\n"
        "- This value is used to calculate the total weight of the player's inventory.\n"
        "- A player may have a maximum carrying capacity, so weight is an important balancing factor.\n\n"
        "**Range:** Typically 0 to 100. A value of 0 means it has negligible weight."
    ),
    "size": (
        "**Size**\n\n"
        "The size of the object, as a numerical value (can be a decimal).\n\n"
        "**Game Mechanics:**\n"
        "- This value is used to determine if an object can fit inside a container.\n"
        "- Containers will have a maximum size capacity.\n\n"
        "**Range:** Typically 1 to 100. A small item like a key might be 1, while a large crate might be 100."
    ),
    "properties": (
        "**Object Properties**\n\n"
        "Select the boolean properties that apply to this object. These act as simple flags that the game engine can check to determine how an object behaves.\n\n"
        "**Hover over each property in the editor to see a detailed explanation of what it does.**"
    ),
    "power_state": (
        "**Required Power State**\n\n"
        "The power state the *room* or *ship* must be in for this object to function or be interacted with in certain ways.\n\n"
        "**Options:**\n"
        "- **(Blank):** The object is not affected by power status.\n"
        "- **offline:** The object only works when all power is off.\n"
        "- **emergency:** Works during emergency power.\n"
        "- **main_power:** Requires main ship power to be active."
    ),
    "is_locked": (
        "**Is Locked?**\n\n"
        "Check this box if the object is currently in a locked state.\n\n"
        "**Functionality:**\n"
        "- If checked, you must define the lock details below (Lock Type, etc.).\n"
        "- The game will prevent actions like 'open' or 'use' until the object is unlocked."
    ),
    "lock_type": (
        "**Lock Type**\n\n"
        "The mechanism used to unlock this object.\n\n"
        "**Options:**\n"
        "- **(Blank):** No lock type.\n"
        "- **key:** Requires a specific key object (defined below).\n"
        "- **code:** Requires the player to enter a numeric or alphanumeric code.\n"
        "- **biometric:** Might require a specific player state or item (e.g., 'handprint')."
    ),
    "lock_code": (
        "**Lock Code**\n\n"
        "The specific code required to unlock the object if its 'Lock Type' is set to 'code'.\n\n"
        "**Format:** Can be numbers, letters, or a combination.\n\n"
        "**Example:** `481516` or `AE-35`"
    ),
    "key_object_id": (
        "**Key Object ID**\n\n"
        "The Object ID of the specific item that unlocks this object if its 'Lock Type' is set to 'key'.\n\n"
        "**Instructions:**\n"
        "- Select a valid key from the dropdown list.\n"
        "- The list is automatically populated with all objects in the game that have the category 'key_item'."
    ),
    "required_state": (
        "**Interaction: Required State (CSV)**\n\n"
        "A comma-separated list of states the object itself must be in for its primary interaction to work.\n\n"
        "**Example:**\n"
        "A computer terminal might require the state `powered_on`. So you would enter `powered_on` here. An interaction might need a door to be both `open` and `powered_on`. You would enter `open, powered_on`.\n\n"
        "These states are typically set by other interactions (the 'Effects' field)."
    ),
    "required_items": (
        "**Interaction: Required Items (CSV)**\n\n"
        "A comma-separated list of Object IDs that the player must have in their inventory to perform the primary interaction.\n\n"
        "**Example:**\n"
        "To operate a diagnostic machine, the player might need a `power_cell` and a `data_scanner`. You would enter: `power_cell, data_scanner`"
    ),
    "primary_actions": (
        "**Interaction: Primary Actions (CSV)**\n\n"
        "A comma-separated list of verbs that will trigger this object's special interaction.\n\n"
        "**Example:**\n"
        "For a computer console, the actions might be `use, operate, access`. When the player types 'use console', this interaction is triggered.\n"
        "**Do not** include basic commands like 'take' or 'examine' here."
    ),
    "effects": (
        "**Interaction: Effects (key:value)**\n\n"
        "The changes that occur when the primary interaction is successful. This is the core of puzzle logic.\n\n"
        "**Format:**\n"
        "Enter one effect per line, in `key: value` format.\n\n"
        "**Common Keys:**\n"
        "- `state`: Changes a state on this object (e.g., `state: powered_on`).\n"
        "- `description`: Changes the object's description.\n"
        "- `message`: Displays a custom message.\n"
        "- `add_object`: Adds a new object to the player's inventory.\n"
        "- `remove_item`: Removes the required item from inventory.\n"
        "- `unlock`: Unlocks a different object (e.g., `unlock: player_cabin_door`).\n\n"
        "**Example:**\n"
        "state: activated\n"
        "description: The console now hums with power.\n"
        "unlock: secret_passage"
    ),
    "success_message": (
        "**Interaction: Success Message**\n\n"
        "The message displayed to the player after a successful interaction.\n\n"
        "**Best Practice:**\n"
        "Make this message descriptive and rewarding. Let the player know what happened as a result of their action.\n\n"
        "**Example:** `You insert the keycard and the terminal whirs to life, displaying the ship's emergency logs.`"
    ),
    "failure_message": (
        "**Interaction: Failure Message**\n\n"
        "The message displayed to the player if they try to perform the primary action but do not meet the requirements (e.g., don't have the required items or the object is not in the required state).\n\n"
        "**Example:** `You press the button, but nothing happens. It seems to be missing a power source.`"
    ),
}

# --- Property Tooltip Texts ---
PROPERTY_TOOLTIPS = {
    # Core Behaviours
    "is_takeable": "Can the player pick this up and put it in their inventory?\n\nExample: Keys, tools, datapads.",
    "is_openable_closable": "Can this object be opened and closed?\n\nExample: Doors, lockers, crates.",
    "is_lockable": "Can this object be locked and unlocked?\nRequires 'is_openable_closable' to be useful.\n\nExample: A footlocker, a secure door.",
    "is_interactive": "Is this a general interactive object?\nFor things players can 'use' or interact with beyond basic actions.\n\nExample: A control panel, a computer terminal.",
    "is_movable": "Can the player push or pull this object around the room?\n(Note: This is different from taking it).\n\nExample: A large crate, a trolley.",
    "is_storage": "Is this a container that can hold other items?\n\nExample: A backpack, a locker, a box.",
    "is_weapon": "Can this object be used as a weapon?\nEnables the 'Weapon Stats' fields below.\n\nExample: A phaser, a knife.",

    # Physical & Material Attributes
    "is_flammable": "Can this object be set on fire?\n\nExample: Paper, cloth, fuel.",
    "is_fragile": "Can this object be broken or shattered?\n\nExample: A glass vial, an old ceramic pot.",
    "is_destroyable": "Can this object be destroyed by force (e.g., with a weapon)?\n\nExample: A locked but flimsy door, a security camera.",
    "is_toxic": "Is this object hazardous or poisonous to the player?\n\nExample: A leaking barrel of chemicals, a strange alien plant.",
    "is_dangerous": "Does this object pose a direct threat to the player?\n\nExample: A live power conduit, a malfunctioning robot.",
    "is_hidden": "Is this object hidden from view by default?\nIt may require searching the room or an area to be found.\n\nExample: A loose floor panel, a key hidden under a bed.",
    "is_secret": "Is this a secret object or passage?\nSimilar to 'hidden' but often implies a more significant discovery.\n\nExample: A hidden door behind a bookshelf.",
    "is_buoyant": "Does this object float in water?\n\nExample: A life-vest, an empty barrel.",
    "is_conductive": "Does this object conduct electricity?\n\nExample: A metal pole, a pool of water.",
    "is_magnetic": "Can this object be affected by magnets or magnetic fields?\n\nExample: An iron key, a steel plate.",

    # Consumable, Wearable & Durability
    "is_wearable": "Can the player wear this item on their body?\nEnables the 'Wearability Details' fields below.\n\nExample: A jumpsuit, boots, a helmet.",
    "is_edible": "Can the player eat this item?\n\nExample: An apple, a nutrition bar.",
    "is_food": "Is this item considered food?\n(Can be edible but not 'food', e.g., medicine).\n\nExample: A ration pack.",
    "is_cookable": "Can this item be cooked to change its state?\n\nExample: Raw alien meat.",
    "is_consumable": "Can this item be used up? A general category for single-use items.\n\nExample: A one-use medical hypo, a power cell.",
    "has_durability": "Does this object have a durability that wears down with use?\nRequires defining 'durability' value.\n\nExample: A tool, a weapon, a space suit.",
    "is_repairable": "Can this object be repaired if it has durability and is damaged?\n\nExample: A damaged engine part, a worn-out weapon.",

    # Device & Tech Properties
    "is_operational": "Is this a device that can be operated?\n\nExample: A ship's console, a diagnostic machine.",
    "is_activatable": "Can this object be activated or deactivated?\nOften used for switches, buttons, or devices.\n\nExample: A light switch, a force field emitter.",
    "requires_power": "Does this object need power to function?\n\nExample: A computer terminal, an automatic door.",
    "is_hackable": "Can the player use hacking skills or tools on this object?\n\nExample: A security terminal, an electronic lock.",
    "is_rechargeable": "Can this object's power be refilled?\n\nExample: A flashlight, a phaser.",
    "is_fuel_source": "Can this object be used as fuel for another device?\n\nExample: A power cell, a canister of plasma.",
    "is_networked": "Is this device connected to a larger network?\nInteracting with it might have effects elsewhere.\n\nExample: A comms panel, a central computer core.",
    "has_security": "Is this object protected by some form of security?\nThis could mean it's alarmed, or requires a keycard, etc.\n\nExample: A captain's safe, a secure data terminal.",
    "is_sensitive": "Is this object sensitive to damage or environmental changes?\n\nExample: A delicate scientific instrument.",
    "is_electronic": "Is this object electronic?\nThis can make it susceptible to EMPs or water damage.\n\nExample: A datapad, a remote control.",

    # Fantasy & Magic
    "is_magical": "Does this object have supernatural properties?\n\nExample: A glowing sword, a talking skull.",
    "is_cursed": "Does the object carry a negative enchantment that affects the holder?\n\nExample: A ring that slowly drains health.",
    "is_enchanted": "Does the object have a beneficial magical effect?\n\nExample: A shield that deflects fire, boots of speed.",
    "requires_attunement": "Must the player perform a ritual or wait to use this object's magic?\n\nExample: A holy symbol that must be blessed.",
    "is_quest_item": "Is this object critical for advancing a specific narrative quest?\n\nExample: The 'Amulet of Kings', a specific character's diary.",

    # Crafting & Social
    "is_crafting_material": "Can this be used as a component to create something else?\n\nExample: Scrap metal, herbs, a vial of liquid.",
    "can_be_disassembled": "Can this item be broken down into crafting materials?\n\nExample: Breaking down a radio for electronics.",
    "has_blueprint": "Is this a recipe or schematic that teaches a crafting recipe?\n\nExample: A weapons schematic, a potion recipe.",
    "is_owned": "Does this object belong to an NPC? Taking it might be stealing.\n\nExample: A shopkeeper's inventory, a guard's key.",
    "is_illegal": "Is possession of this item a crime within the game's world?\n\nExample: Contraband, an illegal weapon modification.",
    "is_evidence": "Is this a narrative object that can be used to prove something in dialogue?\n\nExample: A blood-stained knife, a signed confession.",

    # Other / Miscellaneous
    "is_modular": "Can this object be combined with other objects or upgraded?\n\nExample: A weapon with attachment slots.",
    "regenerates": "Does this object regenerate or replenish over time?\n\nExample: A self-healing alien plant, a slowly refilling water dispenser.",
    "is_stored": "Is this object currently stored inside another object?\n(Usually managed by the game engine, but can be set for initial state).\n\nExample: A key inside a box.",
    "is_transferable": "Can this object's data or contents be transferred?\n\nExample: A datapad, a storage drive.",
    "can_store_liquids": "Can this container hold liquids?\n\nExample: A bottle, a canteen.",
}


class ObjectEditorFrame(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # --- Layout ---
        self.grid_columnconfigure(0, weight=3) # Main editor area
        self.grid_columnconfigure(1, weight=1) # Help panel
        self.grid_rowconfigure(1, weight=1)

        # --- Top Controls ---
        self.top_frame = ctk.CTkFrame(self)
        self.top_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        
        self.manager = ObjectDataManager(project_root / "data")
        all_object_ids = self.manager.get_object_ids()

        self.object_dropdown_label = ctk.CTkLabel(self.top_frame, text="Select Object:")
        self.object_dropdown_label.pack(side="left", padx=(10, 5))
        self.object_dropdown = ctk.CTkComboBox(self.top_frame, values=[""] + all_object_ids, command=self.on_dropdown_select)
        self.object_dropdown.pack(side="left", padx=5)
        self.object_dropdown.set("")

        self.new_button = ctk.CTkButton(self.top_frame, text="New Object", command=self.clear_fields)
        self.new_button.pack(side="left", padx=5)
        
        self.validate_button = ctk.CTkButton(self.top_frame, text="Validate", command=lambda: self.validate_data(show_success=True))
        self.validate_button.pack(side="left", padx=5)

        self.save_button = ctk.CTkButton(self.top_frame, text="Save Changes", command=self.save_object)
        self.save_button.pack(side="right", padx=5)

        self.delete_button = ctk.CTkButton(self.top_frame, text="Delete Object", fg_color="red", hover_color="darkred", command=self.delete_object)
        self.delete_button.pack(side="right", padx=5)

        # --- Main Content Area ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # --- Help Panel ---
        self.help_frame = ctk.CTkFrame(self)
        self.help_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        self.help_frame.grid_rowconfigure(1, weight=1)
        self.help_frame.grid_columnconfigure(0, weight=1)
        
        self.help_title = ctk.CTkLabel(self.help_frame, text="Contextual Help", font=ctk.CTkFont(size=16, weight="bold"))
        self.help_title.grid(row=0, column=0, padx=10, pady=(10, 5))
        
        self.help_textbox = ctk.CTkTextbox(self.help_frame, wrap="word", state="disabled")
        self.help_textbox.grid(row=1, column=0, padx=10, pady=(5, 10), sticky="nsew")
        
        self.default_help_text = "Welcome to the Object Editor!\n\nSelect an object from the dropdown to edit it, or click 'New Object' to start fresh. Hover over any field to see detailed help here."

        self.tab_view.add("Basic Info")
        self.tab_view.add("Properties")
        self.tab_view.add("State & Lock")
        self.tab_view.add("Storage")
        self.tab_view.add("Interaction")
        self.tab_view.add("YAML Preview")

        self.create_basic_info_widgets(self.tab_view.tab("Basic Info"))
        self.create_properties_widgets(self.tab_view.tab("Properties"))
        self.create_state_lock_widgets(self.tab_view.tab("State & Lock"))
        self.create_storage_widgets(self.tab_view.tab("Storage"))
        self.create_interaction_widgets(self.tab_view.tab("Interaction"))
        self.create_yaml_preview_widgets(self.tab_view.tab("YAML Preview"))

        self.bind_live_update_events()
        
        self.clear_fields()
        self.update_help_text(self.default_help_text)

    def update_help_text(self, text):
        self.help_textbox.configure(state="normal")
        self.help_textbox.delete("1.0", "end")
        self.help_textbox.insert("1.0", text)
        self.help_textbox.configure(state="disabled")

    def bind_widget_help(self, widget, help_key):
        text = HELP_TEXTS.get(help_key, "No help available for this field.")
        widget.bind("<Enter>", lambda e, t=text: self.update_help_text(t))
        widget.bind("<Leave>", lambda e: self.update_help_text(self.default_help_text))

    def bind_live_update_events(self):
        for widget in [self.id_entry, self.name_entry, self.synonyms_entry, self.weight_entry, self.size_entry, self.lock_code_entry, self.req_state_entry, self.req_items_entry, self.actions_entry, self.wear_layer_entry, self.damage_entry, self.range_entry]:
            widget.bind("<KeyRelease>", self.update_preview_event)
        
        for widget in [self.is_plural_check, *self.prop_checks.values()]:
            # Some checkboxes have specific commands, we handle those separately
            if widget not in [self.prop_checks.get("is_wearable"), self.prop_checks.get("is_weapon")]:
                widget.configure(command=self.update_preview_event)
            
        for dropdown in [self.category_dropdown, self.location_dropdown, self.area_dropdown, self.power_state_dropdown, self.lock_type_dropdown, self.lock_key_id_dropdown, self.wear_area_dropdown]:
            original_command = dropdown.cget("command")
            def new_command(value, cmd=original_command):
                if cmd:
                    cmd(value)
                self.update_preview_event()
            dropdown.configure(command=lambda v, oc=original_command: self.update_preview_event(event=None, original_cmd=oc, value=v))

        for textbox in [self.desc_textbox, self.effects_textbox, self.success_msg_textbox, self.failure_msg_textbox]:
            textbox.bind("<<Modified>>", self.update_preview_event)

    def update_preview_event(self, event=None, original_cmd=None, value=None):
        if original_cmd:
            original_cmd(value)
            
        data = self.gather_data_from_fields()
        try:
            validated_obj = ObjectSchema.model_validate(data, strict=False)
            clean_data = validated_obj.model_dump(by_alias=True, exclude_unset=True, exclude_defaults=True)
            self.update_yaml_preview(clean_data)
        except ValidationError:
            self.update_yaml_preview(data)
        
    def gather_data_from_fields(self):
        data = {
            "id": self.id_entry.get() or None,
            "name": self.name_entry.get() or None,
            "is_plural": self.is_plural_check.get() == 1,
            "description": self.desc_textbox.get("1.0", "end-1c").strip() or None,
            "synonyms": self._parse_csv_to_list(self.synonyms_entry.get()),
            "category": self.category_dropdown.get() or None,
            "weight": self.weight_entry.get() or None,
            "size": self.size_entry.get() or None,
            "power_state": self.power_state_dropdown.get() or None,
            "is_locked": self.is_locked_check.get() == 1,
            "lock_type": self.lock_type_dropdown.get() or None,
            "lock_code": self.lock_code_entry.get() or None,
            "lock_key_id": self.lock_key_id_dropdown.get() or None,
            "properties": {prop: (checkbox.get() == 1) for prop, checkbox in self.prop_checks.items()},
            "interaction": {
                "required_state": self._parse_csv_to_list(self.req_state_entry.get()),
                "required_items": self._parse_csv_to_list(self.req_items_entry.get()),
                "primary_actions": self._parse_csv_to_list(self.actions_entry.get()),
                "effects": self._parse_multiline_to_dict(self.effects_textbox.get("1.0", "end-1c")),
                "success_message": self.success_msg_textbox.get("1.0", "end-1c").strip() or None,
                "failure_message": self.failure_msg_textbox.get("1.0", "end-1c").strip() or None,
            }
        }
        
        if data["properties"].get("is_wearable"):
            data["properties"]["wear_area"] = self.wear_area_dropdown.get() or None
            wear_layer_val = self.wear_layer_entry.get()
            data["properties"]["wear_layer"] = int(wear_layer_val) if wear_layer_val else None
        if data["properties"].get("is_weapon"):
            damage_val = self.damage_entry.get()
            range_val = self.range_entry.get()
            data["properties"]["damage"] = float(damage_val) if damage_val else None
            data["properties"]["range"] = float(range_val) if range_val else None

        if data["properties"].get("is_storage"):
            capacity_val = self.storage_capacity_entry.get()
            data["properties"]["storage_capacity"] = float(capacity_val) if capacity_val else None
            data["properties"]["can_store_liquids"] = self.can_store_liquids_check.get() == 1
        
        data["storage_contents"] = self.storage_contents_list.get("1.0", "end-1c").strip().splitlines()
        
        self._current_location = {"room": self.location_dropdown.get(), "area": self.area_dropdown.get()}
        return data
        
    def validate_data(self, show_success=False) -> list:
        errors = []
        raw_data = self.gather_data_from_fields()
        
        try:
            ObjectSchema.model_validate(raw_data, strict=False)
        except ValidationError as e:
            for error in e.errors():
                field = " -> ".join(map(str, error['loc']))
                errors.append(f"- {field.replace('_', ' ').title()}: {error['msg']}")

        if not raw_data.get("id"): errors.append("- Basic Info: 'Object ID' cannot be empty.")
        if not raw_data.get("name"): errors.append("- Basic Info: 'Name' cannot be empty.")
        if raw_data.get("is_locked"):
            if not raw_data.get("lock_type"): errors.append("- Is Locked: 'Lock Type' must be selected.")
            elif raw_data.get("lock_type") == "key" and not raw_data.get("lock_key_id"): errors.append("- Lock Type (Key): 'Key Object ID' must be selected.")
            elif raw_data.get("lock_type") == "code" and not raw_data.get("lock_code"): errors.append("- Lock Type (Code): 'Lock Code' must be provided.")
        
        if errors:
            messagebox.showerror("Validation Errors", "Validation failed:\n" + "\n".join(errors))
        elif show_success:
            messagebox.showinfo("Validation Successful", "The object data is valid.")
            
        return errors

    def on_dropdown_select(self, choice): 
        logger.info(f"Object selected: {choice}")
        if choice: self.load_object(choice)
        else: self.clear_fields()

    def get_enum_values(self, enum_class: Enum): return [item.value for item in enum_class]
    
    def create_basic_info_widgets(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Object ID:").grid(row=0, column=0, padx=10, pady=(20,5), sticky="w")
        self.id_entry = ctk.CTkEntry(tab); self.id_entry.grid(row=0, column=1, padx=10, pady=(20,5), sticky="ew")
        ctk.CTkLabel(tab, text="Name:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(tab); self.name_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.is_plural_check = ctk.CTkCheckBox(tab, text="Is Plural"); self.is_plural_check.grid(row=1, column=2, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(tab, text="Description:").grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.desc_textbox = ctk.CTkTextbox(tab, height=200); self.desc_textbox.grid(row=2, column=1, columnspan=3, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Synonyms (CSV):").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.synonyms_entry = ctk.CTkEntry(tab); self.synonyms_entry.grid(row=3, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Category:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.category_dropdown = ctk.CTkComboBox(tab, values=self.get_enum_values(ObjectCategory)); self.category_dropdown.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        all_room_ids = [""] + self.manager.get_room_ids()
        ctk.CTkLabel(tab, text="Location:").grid(row=5, column=0, padx=10, pady=5, sticky="w")
        self.location_dropdown = ctk.CTkComboBox(tab, values=all_room_ids, command=self.on_room_select); self.location_dropdown.grid(row=5, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Area in Room:").grid(row=6, column=0, padx=10, pady=5, sticky="w")
        self.area_dropdown = ctk.CTkComboBox(tab, values=[""], state="disabled"); self.area_dropdown.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Weight:").grid(row=7, column=0, padx=10, pady=5, sticky="w")
        self.weight_entry = ctk.CTkEntry(tab); self.weight_entry.grid(row=7, column=1, padx=(10,5), pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Size:").grid(row=7, column=2, padx=(10,0), pady=5, sticky="w")
        self.size_entry = ctk.CTkEntry(tab); self.size_entry.grid(row=7, column=3, padx=(0,10), pady=5, sticky="ew")
        tab.grid_columnconfigure(3, weight=1)

    def create_properties_widgets(self, tab):
        tab.grid_rowconfigure(0, weight=1)
        tab.grid_columnconfigure(0, weight=1)
        
        scrollable_frame = ctk.CTkScrollableFrame(tab)
        scrollable_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
        
        self.prop_checks = {}
        
        property_groups = {
            "Core Behaviours": ["is_takeable", "is_openable_closable", "is_lockable", "is_interactive", "is_movable", "is_storage", "is_weapon"],
            "Physical & Material": ["is_flammable", "is_fragile", "is_destroyable", "is_toxic", "is_dangerous", "is_hidden", "is_secret", "is_buoyant", "is_conductive", "is_magnetic"],
            "Consumable, Wearable & Durability": ["is_wearable", "is_edible", "is_food", "is_cookable", "is_consumable", "has_durability", "is_repairable", "can_store_liquids"],
            "Device & Tech": ["is_operational", "is_activatable", "requires_power", "is_hackable", "is_rechargeable", "is_fuel_source", "is_networked", "has_security", "is_sensitive", "is_electronic"],
            "Fantasy & Magic": ["is_magical", "is_cursed", "is_enchanted", "requires_attunement", "is_quest_item"],
            "Crafting & Social": ["is_crafting_material", "can_be_disassembled", "has_blueprint", "is_owned", "is_illegal", "is_evidence"],
            "Miscellaneous": ["is_modular", "regenerates", "is_stored", "is_transferable"]
        }

        all_schema_props = {name for name, field in ObjectProperties.model_fields.items() if field.annotation is bool}
        
        current_row = 0
        for group_name, props in property_groups.items():
            if not props: continue
            group_label = ctk.CTkLabel(scrollable_frame, text=group_name, font=ctk.CTkFont(size=14, weight="bold"))
            group_label.grid(row=current_row, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w")
            current_row += 1
            col = 0
            for prop_name in sorted(props):
                if prop_name not in all_schema_props: continue
                checkbox = ctk.CTkCheckBox(scrollable_frame, text=prop_name.replace("_", " ").title())
                checkbox.grid(row=current_row, column=col, padx=10, pady=5, sticky="w")
                tooltip_text = PROPERTY_TOOLTIPS.get(prop_name, f"No tooltip available for '{prop_name}'.")
                CustomToolTip(checkbox, text=tooltip_text)
                self.prop_checks[prop_name] = checkbox
                col += 1
                if col >= 4:
                    col = 0
                    current_row += 1
            if col != 0: current_row += 1
        
        separator = ctk.CTkFrame(scrollable_frame, height=2, fg_color="gray50")
        separator.grid(row=current_row, column=0, columnspan=4, pady=10, sticky="ew")
        current_row += 1

        wear_label = ctk.CTkLabel(scrollable_frame, text="Wearability Details", font=ctk.CTkFont(size=14, weight="bold"))
        wear_label.grid(row=current_row, column=0, columnspan=4, padx=10, pady=(5, 5), sticky="w")
        current_row += 1

        ctk.CTkLabel(scrollable_frame, text="Wear Area:").grid(row=current_row, column=0, padx=10, pady=5, sticky="w")
        self.wear_area_dropdown = ctk.CTkComboBox(scrollable_frame, values=[""] + self.get_enum_values(WearArea), state="disabled")
        self.wear_area_dropdown.grid(row=current_row, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(scrollable_frame, text="Wear Layer:").grid(row=current_row, column=2, padx=10, pady=5, sticky="w")
        self.wear_layer_entry = ctk.CTkEntry(scrollable_frame, state="disabled")
        self.wear_layer_entry.grid(row=current_row, column=3, padx=10, pady=5, sticky="ew")
        current_row += 1

        weapon_label = ctk.CTkLabel(scrollable_frame, text="Weapon Stats", font=ctk.CTkFont(size=14, weight="bold"))
        weapon_label.grid(row=current_row, column=0, columnspan=4, padx=10, pady=(10, 5), sticky="w")
        current_row += 1
        
        ctk.CTkLabel(scrollable_frame, text="Damage:").grid(row=current_row, column=0, padx=10, pady=5, sticky="w")
        self.damage_entry = ctk.CTkEntry(scrollable_frame, state="disabled")
        self.damage_entry.grid(row=current_row, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(scrollable_frame, text="Range:").grid(row=current_row, column=2, padx=10, pady=5, sticky="w")
        self.range_entry = ctk.CTkEntry(scrollable_frame, state="disabled")
        self.range_entry.grid(row=current_row, column=3, padx=10, pady=5, sticky="ew")
        
        if "is_wearable" in self.prop_checks:
            self.prop_checks["is_wearable"].configure(command=self.toggle_wearability_fields)
        if "is_weapon" in self.prop_checks:
            self.prop_checks["is_weapon"].configure(command=self.toggle_weapon_fields)
    
    def toggle_wearability_fields(self):
        is_wearable = self.prop_checks.get("is_wearable").get() == 1
        state = "normal" if is_wearable else "disabled"
        self.wear_area_dropdown.configure(state=state)
        self.wear_layer_entry.configure(state=state)
        if not is_wearable:
            self.wear_area_dropdown.set("")
            self.wear_layer_entry.delete(0, "end")
        self.update_preview_event()

    def toggle_weapon_fields(self):
        is_weapon = self.prop_checks.get("is_weapon").get() == 1
        state = "normal" if is_weapon else "disabled"
        self.damage_entry.configure(state=state)
        self.range_entry.configure(state=state)
        if not is_weapon:
            self.damage_entry.delete(0, "end")
            self.range_entry.delete(0, "end")
        self.update_preview_event()

    def create_state_lock_widgets(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Power State:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.power_state_dropdown = ctk.CTkComboBox(tab, values=["", "offline", "emergency", "main_power"]); self.power_state_dropdown.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.is_locked_check = ctk.CTkCheckBox(tab, text="Is Locked"); self.is_locked_check.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkLabel(tab, text="Lock Type:").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.lock_type_dropdown = ctk.CTkComboBox(tab, values=["", "key", "code", "biometric"]); self.lock_type_dropdown.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Lock Code:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.lock_code_entry = ctk.CTkEntry(tab); self.lock_code_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        all_key_ids = [""] + self.manager.get_key_object_ids()
        ctk.CTkLabel(tab, text="Key Object ID:").grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.lock_key_id_dropdown = ctk.CTkComboBox(tab, values=all_key_ids); self.lock_key_id_dropdown.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

    def create_storage_widgets(self, tab):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        # --- Top controls for capacity ---
        top_frame = ctk.CTkFrame(tab)
        top_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(top_frame, text="Storage Capacity:").pack(side="left", padx=(10,5))
        self.storage_capacity_entry = ctk.CTkEntry(top_frame, placeholder_text="e.g., 100.0")
        self.storage_capacity_entry.pack(side="left", padx=5)

        self.can_store_liquids_check = ctk.CTkCheckBox(top_frame, text="Can Store Liquids")
        self.can_store_liquids_check.pack(side="left", padx=20)
        
        # --- Contents display ---
        ctk.CTkLabel(tab, text="Storage Contents:", font=ctk.CTkFont(weight="bold")).grid(row=1, column=0, padx=10, pady=(10,0), sticky="w")
        self.storage_contents_list = ctk.CTkTextbox(tab, height=150)
        self.storage_contents_list.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")

        # --- Controls to add/remove items ---
        add_remove_frame = ctk.CTkFrame(tab)
        add_remove_frame.grid(row=3, column=0, padx=10, pady=5, sticky="ew")
        add_remove_frame.grid_columnconfigure(0, weight=1)

        all_object_ids = [""] + self.manager.get_object_ids()
        self.storage_item_select = ctk.CTkComboBox(add_remove_frame, values=all_object_ids)
        self.storage_item_select.grid(row=0, column=0, padx=(10,5), pady=5, sticky="ew")

        self.storage_add_button = ctk.CTkButton(add_remove_frame, text="Add Item", command=self.add_storage_item)
        self.storage_add_button.grid(row=0, column=1, padx=5, pady=5)

        self.storage_remove_button = ctk.CTkButton(add_remove_frame, text="Remove Item", command=self.remove_storage_item)
        self.storage_remove_button.grid(row=0, column=2, padx=5, pady=5)

    def add_storage_item(self):
        selected_item = self.storage_item_select.get()
        if not selected_item:
            messagebox.showwarning("Add Error", "Please select an item from the dropdown to add.")
            return

        current_contents = self.storage_contents_list.get("1.0", "end-1c").strip()
        current_list = current_contents.splitlines() if current_contents else []

        if selected_item not in current_list:
            current_list.append(selected_item)
            new_contents = "\n".join(current_list)
            self.storage_contents_list.delete("1.0", "end")
            self.storage_contents_list.insert("1.0", new_contents)
            self.update_preview_event()
        else:
            messagebox.showinfo("Info", f"Item '{selected_item}' is already in the container.")

    def remove_storage_item(self):
        selected_item = self.storage_item_select.get()
        if not selected_item:
            messagebox.showwarning("Remove Error", "Please select an item from the dropdown to remove.")
            return

        current_contents = self.storage_contents_list.get("1.0", "end-1c").strip()
        current_list = current_contents.splitlines() if current_contents else []

        if selected_item in current_list:
            current_list.remove(selected_item)
            new_contents = "\n".join(current_list)
            self.storage_contents_list.delete("1.0", "end")
            self.storage_contents_list.insert("1.0", new_contents)
            self.update_preview_event()
        else:
            messagebox.showwarning("Not Found", f"Item '{selected_item}' not found in the container.")

    def create_interaction_widgets(self, tab):
        tab.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(tab, text="Required State (CSV):").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.req_state_entry = ctk.CTkEntry(tab); self.req_state_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Required Items (CSV):").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.req_items_entry = ctk.CTkEntry(tab); self.req_items_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Primary Actions (CSV):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.actions_entry = ctk.CTkEntry(tab); self.actions_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Effects (key:value):").grid(row=3, column=0, padx=10, pady=5, sticky="nw")
        self.effects_textbox = ctk.CTkTextbox(tab, height=100); self.effects_textbox.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Success Message:").grid(row=4, column=0, padx=10, pady=5, sticky="nw")
        self.success_msg_textbox = ctk.CTkTextbox(tab, height=60); self.success_msg_textbox.grid(row=4, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(tab, text="Failure Message:").grid(row=5, column=0, padx=10, pady=5, sticky="nw")
        self.failure_msg_textbox = ctk.CTkTextbox(tab, height=60); self.failure_msg_textbox.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

    def create_yaml_preview_widgets(self, tab):
        tab.grid_rowconfigure(0, weight=1); tab.grid_columnconfigure(0, weight=1)
        self.yaml_preview_textbox = ctk.CTkTextbox(tab, state="disabled", font=("Courier New", 10)); self.yaml_preview_textbox.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")

    def on_room_select(self, room_id):
        if room_id:
            self.area_dropdown.configure(values=[""] + self.manager.get_area_ids_for_room(room_id), state="normal"); self.area_dropdown.set("")
        else:
            self.area_dropdown.configure(values=[""], state="disabled"); self.area_dropdown.set("")
            
    def _parse_csv_to_list(self, csv_string: str) -> list:
        return [item.strip() for item in csv_string.split(',') if item.strip()]

    def _parse_list_to_csv(self, data_list: list) -> str: 
        return ", ".join(map(str, data_list)) if data_list else ""
    
    def _parse_multiline_to_dict(self, multiline_string: str) -> dict:
        return {k.strip(): v.strip() for line in multiline_string.splitlines() if ':' in line for k, v in [line.split(':', 1)]}
    
    def _parse_dict_to_multiline(self, data_dict: dict) -> str: 
        return "\n".join(f"{k}:{v}" for k, v in data_dict.items()) if data_dict else ""

    def load_object(self, object_id: str):
        if not object_id: messagebox.showinfo("Info", "Please select an object to load."); return
        self._original_id = object_id
        object_data = self.manager.get_object_by_id(object_id)
        if object_data: self.populate_fields(object_data)
        else: messagebox.showerror("Error", f"Could not find data for object: {object_id}")
    
    def save_object(self):
        if self.validate_data(): return
        raw_data = self.gather_data_from_fields()
        validated_obj = ObjectSchema.model_validate(raw_data, strict=False)
        clean_data = validated_obj.model_dump(by_alias=True, exclude_unset=True)
        object_id = clean_data.get("id")
        if not object_id: messagebox.showerror("Error", "Object ID cannot be empty."); return
        is_new_object = self._original_id is None
        if is_new_object:
            if self.manager.get_object_by_id(object_id): messagebox.showerror("Error", f"An object with the ID '{object_id}' already exists."); return
            success = self.manager.add_object(clean_data)
        else:
            success = self.manager.update_object(self._original_id, clean_data)
        if not success: messagebox.showerror("Error", f"Failed to save object data for '{object_id}'."); return
        location_info = self._current_location
        original_id_for_loc_update = self._original_id if self._original_id != object_id else object_id
        location_success = self.manager.save_object_and_location(original_id_for_loc_update, object_id, location_info.get("room"), location_info.get("area"))
        if location_success:
            messagebox.showinfo("Success", f"Object '{object_id}' saved successfully.")
            self._original_id = object_id
            all_object_ids = self.manager.get_object_ids()
            self.object_dropdown.configure(values=[""] + all_object_ids)
            self.object_dropdown.set(object_id)
        else:
            messagebox.showerror("Error", "Object data saved, but failed to update location.")

    def delete_object(self):
        object_id = self.id_entry.get()
        if not object_id: messagebox.showerror("Error", "No object ID specified to delete."); return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to permanently delete the object '{object_id}'?"): return
        if self.manager.delete_object(object_id):
            messagebox.showinfo("Success", f"Object '{object_id}' has been deleted.")
            all_object_ids = self.manager.get_object_ids()
            self.object_dropdown.configure(values=[""] + all_object_ids)
            self.clear_fields()
        else:
            messagebox.showerror("Error", f"Failed to delete object '{object_id}'.")

    def clear_fields(self):
        self._original_id = None
        self.object_dropdown.set("")
        self.id_entry.delete(0, "end"); self.id_entry.configure(placeholder_text="unique_object_id")
        self.name_entry.delete(0, "end"); self.name_entry.configure(placeholder_text="In-Game Object Name")
        self.is_plural_check.deselect()
        self.desc_textbox.delete("1.0", "end"); self.desc_textbox.insert("1.0", "A detailed description.")
        self.synonyms_entry.delete(0, "end"); self.synonyms_entry.configure(placeholder_text="alias, nickname, other_name")
        self.category_dropdown.set("")
        self.location_dropdown.set("")
        self.area_dropdown.set(""); self.area_dropdown.configure(state="disabled")
        self.weight_entry.delete(0, "end"); self.weight_entry.configure(placeholder_text="0.0")
        self.size_entry.delete(0, "end"); self.size_entry.configure(placeholder_text="1.0")
        for checkbox in self.prop_checks.values(): checkbox.deselect()
        self.power_state_dropdown.set("")
        self.is_locked_check.deselect()
        self.lock_type_dropdown.set("")
        self.lock_code_entry.delete(0, "end"); self.lock_code_entry.configure(placeholder_text="e.g., 481516")
        self.lock_key_id_dropdown.set("")
        self.req_state_entry.delete(0, "end"); self.req_state_entry.configure(placeholder_text="e.g., powered_on, open")
        self.req_items_entry.delete(0, "end"); self.req_items_entry.configure(placeholder_text="e.g., keycard, power_cell")
        self.actions_entry.delete(0, "end"); self.actions_entry.configure(placeholder_text="e.g., use, operate")
        self.effects_textbox.delete("1.0", "end"); self.effects_textbox.insert("1.0", "state: powered_on\ndescription: It's now glowing.")
        self.success_msg_textbox.delete("1.0", "end"); self.success_msg_textbox.insert("1.0", "You successfully used the object.")
        self.failure_msg_textbox.delete("1.0", "end"); self.failure_msg_textbox.insert("1.0", "Nothing seems to happen.")
        
        self.storage_capacity_entry.delete(0, "end"); self.storage_capacity_entry.configure(placeholder_text="e.g., 100.0")
        self.can_store_liquids_check.deselect()
        self.storage_contents_list.delete("1.0", "end")

        self.toggle_wearability_fields()
        self.toggle_weapon_fields()
        self.update_preview_event()
        self.id_entry.focus()
        logger.info("Cleared all fields for new object entry.")

    def shutdown(self):
        """Prepares the frame for closing."""
        logger.info("Shutting down ObjectEditorFrame.")
        # Pass a widget to the class method to cancel any scheduled events
        CustomToolTip.cancel_scheduled_show(self)

    def populate_fields(self, data: dict):
        self.id_entry.delete(0, "end"); self.id_entry.insert(0, data.get("id", ""))
        self.name_entry.delete(0, "end"); self.name_entry.insert(0, data.get("name", ""))
        self.is_plural_check.select() if data.get("is_plural") else self.is_plural_check.deselect()
        self.desc_textbox.delete("1.0", "end"); self.desc_textbox.insert("1.0", data.get("description") or "")
        self.synonyms_entry.delete(0, "end"); self.synonyms_entry.insert(0, self._parse_list_to_csv(data.get("synonyms", [])))
        self.category_dropdown.set(data.get("category", ""))
        found_room, found_area = self.manager.find_object_location(data.get("id", ""))
        self.location_dropdown.set(found_room or ""); self.on_room_select(found_room)
        if found_area: self.area_dropdown.set(found_area)
        self.weight_entry.delete(0, "end"); self.weight_entry.insert(0, str(data.get("weight", "")))
        self.size_entry.delete(0, "end"); self.size_entry.insert(0, str(data.get("size", "")))
        
        properties = data.get("properties", {})
        for prop, checkbox in self.prop_checks.items():
            checkbox.select() if properties.get(prop) else checkbox.deselect()

        self.power_state_dropdown.set(data.get("power_state", ""))
        self.is_locked_check.select() if data.get("is_locked") else self.is_locked_check.deselect()
        self.lock_type_dropdown.set(data.get("lock_type", ""))
        self.lock_code_entry.delete(0, "end"); self.lock_code_entry.insert(0, data.get("lock_code", ""))
        self.lock_key_id_dropdown.set(data.get("key_object_id", ""))

        interaction = data.get("interaction", {})
        self.req_state_entry.delete(0, "end"); self.req_state_entry.insert(0, self._parse_list_to_csv(interaction.get("required_state", [])))
        self.req_items_entry.delete(0, "end"); self.req_items_entry.insert(0, self._parse_list_to_csv(interaction.get("required_items", [])))
        self.actions_entry.delete(0, "end"); self.actions_entry.insert(0, self._parse_list_to_csv(interaction.get("primary_actions", [])))
        self.effects_textbox.delete("1.0", "end"); self.effects_textbox.insert("1.0", self._parse_dict_to_multiline(interaction.get("effects", {})))
        self.success_msg_textbox.delete(0, "end"); self.success_msg_textbox.insert(0, interaction.get("success_message") or "")
        self.failure_msg_textbox.delete(0, "end"); self.failure_msg_textbox.insert(0, interaction.get("failure_message") or "")
        
        self.wear_area_dropdown.set(properties.get("wear_area", ""))
        self.wear_layer_entry.delete(0, "end"); self.wear_layer_entry.insert(0, str(properties.get("wear_layer", "")))
        self.damage_entry.delete(0, "end"); self.damage_entry.insert(0, str(properties.get("damage", "")))
        self.range_entry.delete(0, "end"); self.range_entry.insert(0, str(properties.get("range", "")))

        self.storage_capacity_entry.delete(0, "end"); self.storage_capacity_entry.insert(0, str(properties.get("storage_capacity", "")))
        self.can_store_liquids_check.select() if properties.get("can_store_liquids") else self.can_store_liquids_check.deselect()
        
        storage_contents = data.get("storage_contents", [])
        self.storage_contents_list.delete("1.0", "end")
        self.storage_contents_list.insert("1.0", "\n".join(storage_contents))

        self.toggle_wearability_fields()
        self.toggle_weapon_fields()

        self.update_preview_event()

    def update_yaml_preview(self, data):
        self.yaml_preview_textbox.configure(state="normal")
        self.yaml_preview_textbox.delete("1.0", "end")
        
        if not data or not data.get("id"): 
            self.yaml_preview_textbox.insert("1.0", "# YAML preview will appear here.")
            self.yaml_preview_textbox.configure(state="disabled")
            return

        if isinstance(data.get('category'), Enum): data['category'] = data['category'].value
        if data.get('properties') and isinstance(data['properties'].get('wear_area'), Enum): data['properties']['wear_area'] = data['properties']['wear_area'].value

        string_stream = StringIO()
        yaml = ruamel.yaml.YAML()
        yaml.indent(mapping=2, sequence=4, offset=2)
        
        yaml.dump({'objects': [data]}, string_stream)
        yaml_string = string_stream.getvalue()
        
        self.yaml_preview_textbox.insert("1.0", yaml_string)
        self.yaml_preview_textbox.configure(state="disabled")
