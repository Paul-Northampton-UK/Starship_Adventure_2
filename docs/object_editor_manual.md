## Object Editor Documentation (Draft 1)

This document details the fields available in the Starship Adventure 2 Object Editor GUI.

### 1. Top Controls

These controls manage the overall loading and creation process.

*   **Select Object (Dropdown):**
    *   **Purpose:** Displays a list of all existing object IDs currently loaded from `data/objects.yaml`. Allows you to choose an object to view or edit.
    *   **Behavior:** Selecting an ID from this list enables the "Load" button (or automatically triggers loading if we keep that event).
    *   **Data Type:** String (Object ID).
    *   **Notes:** This list is populated when the editor starts. It will be refreshed after saving changes or deleting an object.

*   **Load (Button):**
    *   **Purpose:** Loads the data for the object selected in the "Select Object" dropdown into all the editor fields below.
    *   **Behavior:** Fetches the object's data from the `ObjectDataManager` and calls the `populate_fields` function. Disables the "Object ID" field (as existing IDs shouldn't be changed). Updates the YAML preview.
    *   **Notes:** Currently triggers automatically when the dropdown selection changes. We can keep this or require an explicit button press.

*   **New Object (Button):**
    *   **Purpose:** Clears all editor fields to allow the creation of a brand new object.
    *   **Behavior:** Calls the `clear_fields` function, which resets all fields to their default state (empty strings, default numbers, default checkbox states). Crucially, it *enables* the "Object ID" field so you can define a unique ID for the new object. Clears the YAML preview.
    *   **Notes:** Creating a new object doesn't save anything until you click "Save Changes".

### 2. Basic Information (Frame)

This frame contains the most fundamental identifying details and physical properties of the object.

*   **Object ID (Input Text):**
    *   **Purpose:** The unique, internal identifier for this object. This is how the game engine and other data files (like `rooms.yaml`) will refer to this specific object.
    *   **Data Type:** String.
    *   **Rules/Importance:**
        *   **CRITICAL!** Must be unique across all objects. The editor checks for duplicates when validating a *new* object.
        *   Should only contain lowercase letters (`a-z`), numbers (`0-9`), and underscores (`_`). No spaces or other special characters.
        *   Cannot be changed after an object is first saved (field is disabled when loading existing objects). If you need to change an ID, you must delete the old object and create a new one.
        *   **Convention:** We discussed using `[room_prefix]_[noun]` (e.g., `cab_locker`, `nav_console`) but this is not enforced by the editor. Consistency is helpful.
    *   **Do:** Choose a clear, descriptive, and unique ID.
    *   **Don't:** Change this after creation; use invalid characters.

*   **Name (Input Text):**
    *   **Purpose:** The user-friendly name of the object as it will appear in game descriptions and messages (e.g., "Navigation Console", "Heavy Wrench", "Data Tablet").
    *   **Data Type:** String.
    *   **Rules/Importance:** Required field. Should be descriptive and capitalized appropriately for display.
    *   **Do:** Make it clear what the object is.
    *   **Don't:** Leave it empty.

*   **Category (Dropdown):**
    *   **Purpose:** A broad classification for the object, influencing default behaviors or how the game systems might treat it (e.g., distinguishing between a heavy piece of furniture and a small takeable item). This helps organize objects and can be used by game logic.
    *   **Data Type:** String (Dropdown Selection)
    *   **Default Value:** Usually the first item in the list, or empty if none selected.
    *   **Rules:** Select the category that best describes the object's primary nature or function.

Available categories include:
*   `container`
*   `weapon`
*   `tool`
*   `consumable`
*   `key_item`
*   `decorative`
*   `readable`
*   `clothing`
*   `equipment`
*   `furniture`
*   `device`
*   `lighting`
*   `fixture`
*   `structure`
*   `item`

*   **Room Location (Dropdown):**
    *   **Purpose:** Specifies the unique `room_id` of the room where this object is located.
    *   **Data Type:** String (selected from the list of `room_id`s loaded from `rooms.yaml`).
    *   **Rules/Importance:** Required for saving. An object must belong to a room (or an area within a room). When saving, the editor will ensure this object's ID is added to the `objects_present` list for this room (or its specified area).
    *   **Behavior:** Selecting a room here dynamically updates the "Area Location" dropdown below it.

*   **Area Location (Dropdown):**
    *   **Purpose:** Specifies the unique `area_id` *within the selected Room* where this object is located. If the object is in the room generally, but not tied to a specific area, leave this blank.
    *   **Data Type:** String (selected from the list of `area_id`s defined for the currently selected Room Location).
    *   **Rules/Importance:** Optional. Only relevant if the object should be associated with a specific sub-location (area) within a room. If an Area is selected, saving will place the object's ID in that Area's `objects_present` list, otherwise it goes in the Room's list.
    *   **Behavior:** This dropdown's choices are filtered based on the selection in "Room Location".

*   **Count (Input Text):**
    *   **Purpose:** How many instances of this object exist at this location with these exact properties. (Currently not used heavily by the engine, but planned).
    *   **Data Type:** Integer.
    *   **Rules/Importance:** Must be a whole number, 1 or greater. Defaults to 1.
    *   **Do:** Set to 1 unless you specifically intend for multiple identical objects (e.g., 3 medkits).

*   **Weight (Input Text):**
    *   **Purpose:** The object's weight in kilograms, used for future inventory capacity calculations.
    *   **Data Type:** Floating-point number (e.g., 0.5, 1.0, 25.3).
    *   **Rules/Importance:** Must be a number between 0.01 and 250.0 (inclusive). Objects >= 250 kg are intended to be immovable based on weight alone.
    *   **Do:** Enter a realistic weight.
    *   **Don't:** Enter text or values outside the range (validation will catch this).

*   **Size (Input Text):**
    *   **Purpose:** An abstract size rating (1-50) used for future inventory capacity and interaction logic (takeable/movable).
    *   **Data Type:** Integer.
    *   **Rules/Importance:** Must be a whole number between 1 and 50 (inclusive).
        *   `1-25`: Intended to be takeable (fits in inventory).
        *   `26-49`: Intended to be movable (push/slide) but not takeable.
        *   `50`: Intended to be fixed/immovable based on size alone.
    *   **Do:** Enter a whole number reflecting the object's relative size/bulk.
    *   **Don't:** Enter text, decimals, or values outside the range (validation will catch this).

*   **Synonyms (Input Text, comma-separated):**
    *   **Purpose:** A list of alternative words the player might use to refer to this object (e.g., for "Data Tablet", synonyms could be "tablet, pad, datapad, slate"). The command parser uses these.
    *   **Data Type:** List of strings (entered as a single string with commas separating the words).
    *   **Rules/Importance:** Optional. Helps make the parser more flexible.
    *   **Do:** Enter lowercase words, separated by commas. `tablet, pad, datapad`
    *   **Don't:** Forget commas between words.

*   **Description (Multiline Text):**
    *   **Purpose:** The detailed text shown to the player when they `examine` or `look at` this specific object.
    *   **Data Type:** String (can span multiple lines).
    *   **Rules/Importance:** Required field. This is the primary way the player learns about the object.
    *   **Do:** Write descriptive text. Include details about appearance, state, or function. You can use multiple lines. Use **markdown bold** (`**word**`) to highlight other potentially interactive objects mentioned *within* this description (though the editor doesn't enforce this, the game engine will use it).
    *   **Don't:** Leave it empty.

### 3. State and Locking (Frame)

This section defines the object's initial visibility, its locking mechanism (if any), and how its state might be affected by power conditions.

*   **Visible Initially (Checkbox):**
    *   **Purpose:** Determines if the object is immediately visible to the player when they first enter the room/area where it's located. Corresponds to the `initial_state` field in the schema.
    *   **Data Type:** Boolean (`True` / `False`).
    *   **Default:** `True` (Checked).
    *   **Rules/Importance:**
        *   If `Checked (True)`: The object is described as part of the location description or is immediately apparent.
        *   If `Unchecked (False)`: The object is initially hidden or requires some action (like searching or opening something) to be discovered. The game logic needs to handle how this object becomes visible.
    *   **Do:** Uncheck this for secret items, objects inside closed containers, or things that require searching to find.
    *   **Don't:** Forget to implement the game logic that reveals objects where this is `False`.

*   **Is Locked (Checkbox):**
    *   **Purpose:** Determines if the object is currently locked, preventing certain interactions (like opening a container, using a device, or sometimes even taking it).
    *   **Data Type:** Boolean (`True` / `False`).
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:**
        *   If `Checked (True)`: The object starts locked. The player will need to perform an `UNLOCK` action (or similar) using the correct method (defined by `Lock Type`).
        *   If `Unchecked (False)`: The object starts unlocked and can be interacted with according to its other properties.
    *   **Do:** Check this for doors, containers, or devices that should require unlocking first. Ensure you also configure the `Lock Type` and related fields below.
    *   **Don't:** Check this if the object should be immediately usable or accessible.

*   **Power State (Dropdown):**
    *   **Purpose:** Defines the object's operational state based on the current power condition in its location. This allows objects to behave differently when power is `offline`, on `emergency`, or `main_power`. (The `torch_light` option might be used if the player is providing local light in an `offline` room).
    *   **Data Type:** String (or `None` if left empty).
    *   **Default:** Empty (effectively `None`).
    *   **Options:** `''` (Empty/None), `offline`, `emergency`, `main_power`, `torch_light`.
    *   **Rules/Importance:**
        *   If set (e.g., to `offline`): This indicates the object *has* different states depending on power. The game logic (especially descriptions in `state_descriptions` or interaction checks) should look at the *room's* power state and compare it to see how this object behaves.
        *   If left Empty/None: The object's function is generally assumed to be independent of the room's power state (unless the `Requires Power` property is checked - see Properties frame).
    *   **Do:** Set this if the object's appearance or function changes significantly with power (e.g., a console screen). Use the `state_descriptions` field (in "Other Details") to define how it looks in each state.
    *   **Don't:** Confuse this with the `Requires Power` property. This field relates more to the object's *current status depiction*, while `Requires Power` determines if it *functions* at all without power. An object might be `offline` (this field) but still *require* power to be turned on.

*   **Lock Type (Dropdown):**
    *   **Purpose:** Specifies the *mechanism* used to unlock this object if `Is Locked` is checked.
    *   **Data Type:** String (or `None` if left empty).
    *   **Default:** Empty (effectively `None`).
    *   **Options:** `''` (Empty/None), `key`, `code`, `biometric`.
    *   **Rules/Importance:** Only relevant if `Is Locked` is `True`.
        *   `key`: Requires the player to `USE` a specific key item (whose ID is specified in `Lock Key ID`).
        *   `code`: Requires the player to `ENTER` or `TYPE` the correct code (specified in `Lock Code`).
        *   `biometric`: Might require a specific condition or item (less defined currently, could be a hand scanner needing power, etc.).
        *   Empty/None: If `Is Locked` is true but `Lock Type` is empty, it implies the object is locked by some other puzzle logic not defined directly here (e.g., needs power restored, a lever pulled elsewhere).
    *   **Do:** Select the appropriate type if the object has a standard lock. Ensure the corresponding field (`Lock Code` or `Lock Key ID`) is also filled.
    *   **Don't:** Select a type if `Is Locked` is `False`.

*   **Lock Code (Input Text):**
    *   **Purpose:** Specifies the exact code needed to unlock the object if `Lock Type` is set to `code`.
    *   **Data Type:** String.
    *   **Default:** Empty.
    *   **Rules/Importance:** Only used if `Lock Type` is `code`. The game's `ENTER CODE` logic will compare the player's input against this value.
    *   **Do:** Enter the required code (e.g., `1234`, `override_alpha`).
    *   **Don't:** Fill this in if the `Lock Type` is not `code`.

*   **Lock Key ID (Input Text):**
    *   **Purpose:** Specifies the unique `object_id` of the key item required to unlock this object if `Lock Type` is set to `key`.
    *   **Data Type:** String (should be a valid `object_id` of another object).
    *   **Default:** Empty.
    *   **Rules/Importance:** Only used if `Lock Type` is `key`. The game's `UNLOCK OBJECT WITH KEY` logic will check if the player possesses the item with this ID.
    *   **Do:** Enter the exact `object_id` of the required key item (e.g., `bridge_keycard`, `captains_key`).
    *   **Don't:** Fill this in if the `Lock Type` is not `key`.

### 4. Properties (Frame)

This large section contains numerous checkboxes and a few input fields that define the inherent capabilities and characteristics of the object. These properties are often checked by the game logic when the player attempts specific actions. *Note: These correspond to fields within the nested `properties:` dictionary in the YAML structure.*

#### 4.1 General Object Properties (Column 1 Mix)

*   **Takeable (`is_takeable`, Checkbox):**
    *   **Purpose:** Can the player pick up this object and add it to their inventory?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Fundamental property for inventory items. If `True`, the object's `Weight` and `Size` are used for inventory limits. An object's `Size` should ideally be within the takeable range (1-25) if this is checked.
    *   **Do:** Check for items meant to be carried (tools, keys, consumables, small devices).
    *   **Don't:** Check for large furniture, fixed consoles, structural elements.

*   **Interactive (`is_interactive`, Checkbox):**
    *   **Purpose:** Can the player generally interact with this object using commands beyond just `LOOK AT`? (e.g., `USE`, `OPEN`, `PUSH`, `EAT`). This acts as a master switch for many interactions.
    *   **Default:** `True` (Checked).
    *   **Rules/Importance:** Most objects should probably be interactive in some way, even if it's just getting a specific message. If `False`, the game might ignore attempts to use commands other than `LOOK AT` on this object.
    *   **Do:** Leave checked for most objects.
    *   **Don't:** Uncheck unless the object is purely environmental flavour text with no planned interaction potential at all (rare).

*   **Dangerous (`is_dangerous`, Checkbox):**
    *   **Purpose:** Does interacting with or being near this object pose a direct threat or potential harm to the player?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Used by game logic to trigger warnings, damage, status effects, or specific failure conditions.
    *   **Do:** Check for exposed wiring, radiation sources, unstable explosives, hostile creatures represented as objects.
    *   **Don't:** Check for standard safe objects.

*   **Destroyable (`is_destroyable`, Checkbox):**
    *   **Purpose:** Can this object be destroyed through player actions (e.g., using a weapon, a tool, or causing an explosion)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables specific game logic for destroying objects, potentially revealing items, clearing paths, or triggering consequences. Requires corresponding game logic to handle the destruction action.
    *   **Do:** Check for obstacles like flimsy crates, weak panels, certain types of locks, or quest-related destructible items.
    *   **Don't:** Check for critical structural elements or objects not intended to be breakable.

*   **Is Storage (`is_storage`, Checkbox):**
    *   **Purpose:** Does this object function as a container that can hold other objects?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables commands like `OPEN`, `CLOSE`, `PUT ITEM IN CONTAINER`, `LOOK IN CONTAINER`. Requires the `Storage Contents` field (in "Other Details") to be managed and potentially the `Storage Capacity` property below.
    *   **Do:** Check for lockers, backpacks, crates, drawers, pockets.
    *   **Don't:** Check for solid objects that cannot contain others.

*   **Operational (`is_operational`, Checkbox):**
    *   **Purpose:** Represents the general functional state of a device or tool. Is it currently working or broken/disabled? (Separate from power requirements).
    *   **Default:** `True` (Checked) - *Assumed default based on schema/common use.*
    *   **Rules/Importance:** Game logic can check this before allowing an action (e.g., can't `USE` a broken tool). The state might be changed by game events (damage, repair, power loss if `Requires Power` is also true).
    *   **Do:** Check if the device/tool is intended to be functional by default. Uncheck for items that start broken and need repair.
    *   **Don't:** Confuse with `is_interactive`. An object can be interactive (you can try to use it) but not operational (it fails because it's broken).

*   **Edible (`is_edible`, Checkbox):**
    *   **Purpose:** Can the player attempt to eat this object? (Does not guarantee it's beneficial!).
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables the `EAT` command for this object. Should typically be used alongside `Is Food` (for beneficial food) or potentially `Is Toxic` (for harmful things the player might mistakenly eat). Often implies `Is Consumable` is also true.
    *   **Do:** Check for food items, pills, maybe weird alien plants.
    *   **Don't:** Check for tools, furniture, etc.

*   **Is Weapon (`is_weapon`, Checkbox):**
    *   **Purpose:** Can this object be used offensively in combat or to destroy things?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables combat actions (`ATTACK WITH WEAPON`) or potentially destructive interactions (if `is_destroyable` is also relevant). Often used with `Damage`, `Durability`, and `Range` properties.
    *   **Do:** Check for knives, wrenches (as improvised), laser pistols, etc.
    *   **Don't:** Check for passive items.

*   **Movable (`is_movable`, Checkbox):**
    *   **Purpose:** Can the player push, pull, or slide this object around the location? (Distinct from picking it up).
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables commands like `PUSH`, `PULL`. Relevant for objects too large/heavy to take (`Size` 26-49) but not completely fixed (`Size` < 50, `Weight` < 250). Requires game logic support for changing object positions within a room/area.
    *   **Do:** Check for crates, heavy chairs, trolleys.
    *   **Don't:** Check for small takeable items or very large fixed items.

*   **Wearable (`is_wearable`, Checkbox):**
    *   **Purpose:** Can the player equip this object onto their person?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables commands like `WEAR`, `REMOVE`. Relevant for clothing, armor, helmets, boots, gloves. Often implies the object provides some status effect or protection when worn. Belongs to the `equipment` category typically.
    *   **Do:** Check for jumpsuits, boots, helmets, gloves, hazmat suits.
    *   **Don't:** Check for items not meant to be equipped.

#### 4.2 Physical & Hazard Properties (Column 2)

*   **Flammable (`is_flammable`, Checkbox):**
    *   **Purpose:** Can this object catch fire easily?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Used by game logic involving fire sources, spreading fire, or specific environmental hazards/puzzles. Destroyable flammable objects might be destroyed by fire.
    *   **Do:** Check for paper, cloth, fuel canisters, certain chemicals.
    *   **Don't:** Check for metal consoles, stone structures.

*   **Toxic (`is_toxic`, Checkbox):**
    *   **Purpose:** Is this object inherently poisonous or harmful if touched, ingested, or interacted with improperly?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Can trigger negative status effects (health loss, radiation) upon interaction or consumption. Often used with `Is Edible` for poisonous food/substances.
    *   **Do:** Check for hazardous chemicals, radioactive materials, poisonous plants/creatures.
    *   **Don't:** Check for safe items.

*   **Is Food (`is_food`, Checkbox):**
    *   **Purpose:** Specifically identifies the object as a beneficial food item.
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Used by the `EAT` command logic to provide positive effects (hunger reduction, potentially minor health/energy). Usually implies `Is Edible` and `Is Consumable` are also `True`.
    *   **Do:** Check for ration packs, nutrient paste, space carrots.
    *   **Don't:** Check for non-food items or harmful edible items (use `Is Edible` and `Is Toxic` for those).

*   **Cookable (`is_cookable`, Checkbox):**
    *   **Purpose:** Can this food item be cooked using a heat source/cooking device?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Modifies the `EAT` logic. Eating a raw cookable item might provide fewer benefits or even have negative effects compared to eating it cooked. Requires game logic for a `COOK` command/interaction. Usually applies only if `Is Food` is also `True`.
    *   **Do:** Check for raw ingredients that need cooking.
    *   **Don't:** Check for pre-packaged rations or non-food items.

*   **Consumable (`is_consumable`, Checkbox):**
    *   **Purpose:** Is this object used up entirely after one or more uses?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Triggers game logic to remove the object from inventory (or decrease its count) after use. Often associated with `Is Edible`, `Is Food`, but also applies to single-use items like repair kits, batteries, flares, medkits.
    *   **Do:** Check for anything that gets used up.
    *   **Don't:** Check for permanent tools, equipment, furniture.

*   **Has Durability (`has_durability`, Checkbox):**
    *   **Purpose:** Does this object degrade or have a limited number of uses before breaking or becoming ineffective?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Requires game logic to track the object's current durability state (often an integer value, possibly using the `Durability` property field). Use might decrease durability, and reaching zero could make it non-operational or destroy it.
    *   **Do:** Check for weapons that can break, tools that wear out, batteries that deplete (if not just `consumable`).
    *   **Don't:** Check for simple, non-degrading items.

*   **Hackable (`is_hackable`, Checkbox):**
    *   **Purpose:** Can the player attempt to hack this object (likely a device)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables `HACK` command attempts. Requires game logic for hacking minigames or skill checks. Success might bypass locks, change object state, or reveal information. Usually applies to `device` category objects.
    *   **Do:** Check for computer terminals, security panels, locked electronic doors.
    *   **Don't:** Check for non-electronic items.

*   **Rechargeable (`is_rechargeable`, Checkbox):**
    *   **Purpose:** Can this object (likely a battery or energy cell) have its energy store replenished?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables interactions with charging stations or other power sources. Requires game logic to track energy level (possibly using `Durability` or a custom state).
    *   **Do:** Check for power cells, tool batteries.
    *   **Don't:** Check for single-use consumables or non-powered items.

*   **Fuel Source (`is_fuel_source`, Checkbox):**
    *   **Purpose:** Can this object be used *as* fuel to power another device or system?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables using this object in interactions that require fuel (e.g., `USE POWER_CELL IN TORCH`). Often implies `Is Consumable`.
    *   **Do:** Check for batteries, plasma canisters, hydrogen cells.
    *   **Don't:** Check for devices that *use* fuel.

#### 4.3 Special & Digital Properties (Column 3)

*   **Regenerates (`regenerates`, Checkbox):**
    *   **Purpose:** Does this object replenish itself or its uses over time or after certain events? (Less common).
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Requires specific game logic to handle the regeneration trigger and effect. Could apply to a regenerating health pack, a slowly refilling water source object, etc.
    *   **Do:** Use sparingly for specific puzzle or resource mechanics.
    *   **Don't:** Use for standard items.

*   **Modular (`is_modular`, Checkbox):**
    *   **Purpose:** Is this object part of a larger construct, or can it be combined with other specific parts?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables crafting or assembly mechanics. Requires game logic to handle combining/attaching modular components.
    *   **Do:** Check for weapon parts, machinery components, puzzle pieces.
    *   **Don't:** Check for standalone items.

*   **Is Stored (`is_stored`, Checkbox):**
    *   **Purpose:** Primarily for digital items: Does this object exist only *within* another object (like a file on a computer)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Affects how the object is accessed. A stored object might only be listable/readable/transferable when interacting with its parent object (e.g., the computer). Might imply it's not `Takeable` on its own.
    *   **Do:** Check for data logs on a terminal, emails, program files.
    *   **Don't:** Check for physical objects.

*   **Transferable (`is_transferable`, Checkbox):**
    *   **Purpose:** Primarily for digital items: Can this object be copied or moved from one digital storage to another (e.g., download file from terminal to datapad)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables actions like `DOWNLOAD`, `COPY`, `TRANSFER`. Usually applies only if `Is Stored` is also `True`.
    *   **Do:** Check for files, data logs that can be moved.
    *   **Don't:** Check for physical objects or non-movable digital entries.

*   **Activatable (`is_activatable`, Checkbox):**
    *   **Purpose:** Can this object be explicitly turned on or off, or activated/deactivated?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Enables commands like `ACTIVATE`, `DEACTIVATE`, `TURN ON`, `TURN OFF`. The object might need power (`Requires Power`) to be activated. Its operational state might change.
    *   **Do:** Check for switches, consoles, machines, light sources, force fields.
    *   **Don't:** Check for passive objects.

*   **Networked (`is_networked`, Checkbox):**
    *   **Purpose:** Is this device connected to a wider ship system or network?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Can enable interactions that affect other parts of the ship network (e.g., hacking one terminal might unlock doors controlled by the network). Requires underlying game logic for network interactions.
    *   **Do:** Check for computer terminals, communication consoles, security cameras linked to a system.
    *   **Don't:** Check for standalone devices.

*   **Requires Power (`requires_power`, Checkbox):**
    *   **Purpose:** Does this object need external power (from the room's state or a connected fuel source) to function?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Critical check for most devices. If `True`, game logic will prevent activation or use if sufficient power isn't available.
    *   **Do:** Check for consoles, machines, powered doors, energy weapons.
    *   **Don't:** Check for simple tools, furniture, books, passive items.

*   **Requires Item (`requires_item`, Checkbox):**
    *   **Purpose:** Does using this object's primary function require another specific item to be present (either in inventory or perhaps inserted into it)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Used for interactions like inserting a keycard, loading fuel, or using a specific tool on a machine. The *specific* required item(s) should be defined in the "Interaction" section (`required_items` list). This checkbox acts as a quick flag.
    *   **Do:** Check if the object needs another item for its main function (e.g., a projector needing a data disk).
    *   **Don't:** Check if the object functions standalone.

*   **Has Security (`has_security`, Checkbox):**
    *   **Purpose:** Is interaction with this object monitored or restricted by some security measure (beyond just being locked)?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Can trigger alarms, log user actions, or require specific authorization levels (not fully implemented yet) for access/use, even if unlocked.
    *   **Do:** Check for sensitive computer terminals, security consoles, restricted area access panels.
    *   **Don't:** Check for common objects.

*   **Sensitive (`is_sensitive`, Checkbox):**
    *   **Purpose:** Will interacting with this object improperly (or sometimes, at all) trigger negative consequences or alarms?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Similar to `Has Security` but maybe broader. Could apply to triggering traps, alerting guards, or causing unstable equipment to malfunction if handled incorrectly.
    *   **Do:** Check for alarm panels, trapped containers, unstable experimental devices.
    *   **Don't:** Check for standard objects.

#### 4.4 Interaction & Specific Properties (Column 4)

*   **Fragile (`is_fragile`, Checkbox):**
    *   **Purpose:** Is this object easily broken if dropped, hit, or mishandled?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Game logic for dropping items or combat might check this. If `True`, the object might be destroyed or damaged under certain conditions. Often relevant for `glass` or `ceramic` items.
    *   **Do:** Check for glassware, delicate electronics, certain artifacts.
    *   **Don't:** Check for sturdy items.

*   **(Separator & Label: Storage Specific)** - Visual aid only.

*   **Capacity (`storage_capacity`, Input Text):**
    *   **Purpose:** If `Is Storage` is `True`, this defines the total `Size` units this container can hold.
    *   **Data Type:** Floating-point number (or `None` if empty).
    *   **Default:** Empty (`None`).
    *   **Rules/Importance:** Only relevant for containers. Game logic will check this when the player tries to put items into the container, comparing the item's `Size` against the remaining capacity. If empty/None, capacity might be considered unlimited or handled differently.
    *   **Do:** Enter a positive number representing the total size units the container holds (e.g., `50.0` for a backpack, `100.0` for a locker).
    *   **Don't:** Enter text or negative numbers. Leave empty if capacity is not relevant or unlimited.

*   **Stores Liquids (`can_store_liquids`, Checkbox):**
    *   **Purpose:** If `Is Storage` is `True`, can this container specifically hold liquids?
    *   **Default:** `False` (Unchecked).
    *   **Rules/Importance:** Used for game logic involving liquid collection, transfer, or storage. Prevents putting water in a backpack unless this is checked.
    *   **Do:** Check for bottles, canisters, tanks meant for liquids.
    *   **Don't:** Check for standard crates, bags, lockers not designed for liquids.

*   **(Separator & Label: Weapon Specific)** - Visual aid only.

*   **Damage (`damage`, Input Text):**
    *   **Purpose:** If `Is Weapon` is `True`, this indicates the amount of damage dealt per hit/use.
    *   **Data Type:** Floating-point number (or `None` if empty).
    *   **Default:** Empty (`None`).
    *   **Rules/Importance:** Only relevant for weapons. Used by combat logic.
    *   **Do:** Enter a positive number representing damage value.
    *   **Don't:** Enter text or negative numbers. Leave empty if not a weapon.

*   **Durability (`durability`, Input Text):**
    *   **Purpose:** If `Has Durability` is `True`, this represents the **Maximum Durability** - the total number of uses/hits the object can withstand before breaking or becoming useless.
    *   **Data Type:** Integer (or `None` if empty).
    *   **Default:** Empty (`None`).
    *   **Rules/Importance:** Relevant for weapons, tools, or rechargeable items. Game logic needs to track the *current* durability state separately (perhaps in `GameState.object_states`). When uses reach 0, the object breaks/depletes.
    *   **Do:** Enter a positive whole number representing the total uses/hits.
    *   **Don't:** Enter text, decimals, or negative numbers. Leave empty if durability doesn't apply.

*   **Range (`range`, Input Text):**
    *   **Purpose:** If `Is Weapon` is `True`, this might indicate the effective range (e.g., in abstract units or meters). (Currently not used by engine).
    *   **Data Type:** Floating-point number (or `None` if empty).
    *   **Default:** Empty (`None`).
    *   **Rules/Importance:** Optional, for potential future ranged combat logic.
    *   **Do:** Enter a positive number if relevant.
    *   **Don't:** Enter text or negative numbers.

### 5. Interaction (Frame)

This frame details the requirements, actions, and results associated with the object's primary intended use (often triggered by the `USE` command, but potentially others depending on game logic). *Note: These correspond to fields within the nested `interaction:` dictionary in the YAML structure.*

*   **Required State (Input Text, comma-separated):**
    *   **Purpose:** Specifies any game state flags or conditions that must be `True` for the interaction to be possible or succeed. This allows for puzzle dependencies.
    *   **Data Type:** List of strings (entered as comma-separated values). Each string should correspond to a flag name managed within `GameState.game_flags`.
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional. If list is not empty, the game logic handling the interaction should check if *all* listed flags are currently `True` in `GameState.game_flags` before allowing the interaction or determining its success.
    *   **Example:** `power_on, security_override` - Meaning the interaction only works if both the `power_on` flag AND the `security_override` flag are true in the game state.
    *   **Do:** List prerequisite game state flags needed for this interaction. Use commas to separate multiple flags.
    *   **Don't:** Include flags that aren't managed by the `GameState`.

*   **Required Items (Input Text, comma-separated IDs):**
    *   **Purpose:** Specifies the `object_id`(s) of other items the player must possess (usually in inventory, but could be equipped or even present in the room depending on game logic) for the interaction to succeed. Links with the `Requires Item` property checkbox.
    *   **Data Type:** List of strings (entered as comma-separated object IDs).
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional. If the `Requires Item` property is checked, this list should contain the ID(s) of the necessary item(s). The game logic handling the interaction verifies the player has these items.
    *   **Example:** `keycard_alpha, bypass_tool` - Meaning the player needs both the `keycard_alpha` and the `bypass_tool` items.
    *   **Do:** List the exact `object_id`s of required items, separated by commas.
    *   **Don't:** List item names; use the unique IDs.

*   **Primary Actions (Input Text, comma-separated):**
    *   **Purpose:** Defines the main verbs or actions typically associated with this object's primary function (often related to the `USE` command, but could inform other command interpretations).
    *   **Data Type:** List of strings (entered as comma-separated verbs/actions).
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional. Provides hints to the game logic (and potentially the parser) about what you can *do* with this object. Doesn't strictly enable/disable commands but defines intended use.
    *   **Example:** `insert, activate, operate, press` (for a button or console) or `read, view` (for a book or screen).
    *   **Do:** List the core actions associated with the object's function.
    *   **Don't:** List every possible command; focus on the main intended interactions.

*   **Effects (Input Text, comma-separated):**
    *   **Purpose:** Specifies the *outcomes* or changes that occur in the game state when the primary interaction is successfully performed. This is how objects trigger changes in the world or player status.
    *   **Data Type:** List of strings (entered as comma-separated effect descriptions). The format and interpretation of these strings depend entirely on the game logic that processes them.
    *   **Default:** Empty.
    *   **Rules/Importance:** Critical for making interactions meaningful. The game logic needs specific code to parse and execute these effects.
    *   **Examples (formats depend on implementation):**
        *   `set_flag:power_on` (Sets a game flag)
        *   `clear_flag:door_locked` (Clears a game flag)
        *   `change_state:other_object_id:activated` (Changes another object's state)
        *   `heal_player:25` (Affects player status)
        *   `teleport_player:other_room` (Moves the player)
        *   `reveal_object:secret_item` (Makes a hidden object visible)
        *   `add_inventory:item_id` (Gives player an item)
        *   `remove_inventory:item_id` (Takes an item - e.g. consumes required item)
    *   **Do:** Define the concrete effects using a consistent format that your game logic will understand. Separate multiple effects with commas.
    *   **Don't:** Write vague descriptions; use formats the engine can parse.

*   **Success Message (Input Text):**
    *   **Purpose:** The message displayed to the player when they successfully perform the primary interaction with this object (e.g., after using a keycard on a door, "The door clicks open.").
    *   **Data Type:** String.
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional but highly recommended for good feedback. If empty, the game might provide a generic success message (like "Done.") or no message other than the resulting description changes.
    *   **Do:** Write a clear message confirming the successful interaction.
    *   **Don't:** Rely solely on this; ensure the `Effects` field actually changes the game state appropriately.

*   **Failure Message (Input Text):**
    *   **Purpose:** The message displayed to the player when they attempt the primary interaction but fail because conditions aren't met (e.g., missing required items, wrong state, object is locked or broken).
    *   **Data Type:** String.
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional but highly recommended. Provides context for why an action failed. If empty, the game might give a generic failure message (like "You can't do that.") or rely on specific checks (like "It's locked.").
    *   **Do:** Write a helpful message explaining (or hinting at) why the interaction failed (e.g., "Nothing happens.", "It seems to require a keycard.", "The panel is unresponsive; perhaps it needs power?").
    *   **Don't:** Make it identical to the success message.

### 6. Other Details (Frame)

This frame holds miscellaneous but important details, particularly for containers and objects whose descriptions change based on their internal state.

*   **Storage Contents (Input Text, comma-separated IDs):**
    *   **Purpose:** If the object `Is Storage` (defined in Properties), this list specifies the `object_id`(s) of the items initially contained within this object when the game starts.
    *   **Data Type:** List of strings (entered as comma-separated object IDs).
    *   **Default:** Empty.
    *   **Rules/Importance:** Only relevant for container objects (`Is Storage` = `True`). When the player `OPEN`s or `LOOK IN` the container, the game logic uses this list (and any subsequent changes tracked in `GameState`) to determine what's inside. The total `Size` of the items listed here should ideally not exceed the container's `Storage Capacity` (if defined).
    *   **Do:** List the exact `object_id`s of items initially inside the container, separated by commas.
    *   **Don't:** Fill this in if the object is not a container. Don't list item names.

*   **State Descriptions (Multiline Text, `state_name:description` per line):**
    *   **Purpose:** Allows defining alternative descriptions for the object based on its *internal state*, which might be different from the general `Power State` of the room. This is useful for objects that can be turned on/off, opened/closed, broken/repaired, etc.
    *   **Data Type:** Dictionary mapping state names (strings) to description strings (entered as one `state_name:description` pair per line in the multiline box).
    *   **Default:** Empty.
    *   **Rules/Importance:** Optional. If provided, the game logic responsible for displaying the object's description (e.g., during `EXAMINE`) should first check the object's *current internal state* (which needs to be tracked, perhaps in `GameState.object_states`) and use the corresponding description from this dictionary if a match is found. If no match is found for the current state, or if this dictionary is empty, it falls back to the main `Description` field.
    *   **Example:**
        ```
        on:The console hums, displaying a star map.
        off:The console screen is dark and cold.
        broken:Sparks flicker from a cracked panel on the console.
        ```
    *   **Do:** Define state names consistently (e.g., `on`, `off`, `open`, `closed`, `broken`, `repaired`, `active`, `inactive`) and provide the description text for each state on a new line, separated by a colon (`:`).
    *   **Don't:** Forget the colon separator. Don't define states here unless your game logic actually tracks and uses these internal object states.

## Section 7: Notes on Output Formatting

This section details some aspects of the YAML files (`objects.yaml`, `rooms.yaml`) generated or modified by the Object Editor.

### 7.1 Object Separation in `objects.yaml`

*   **Current Behavior:** When saving, the editor uses the `ruamel.yaml` library to preserve comments and indentation. Objects in the main `objects:` list are output sequentially without an extra blank line between the end of one object and the `- id:` line of the next.
*   **Reasoning:** While a blank line might enhance visual separation slightly, achieving this reliably with `ruamel.yaml` without potentially breaking formatting or comments is complex. The standard YAML list indentation (the `-` at the start of each object ID) serves as the primary structural separator.
*   **TODO:** Investigate future `ruamel.yaml` updates or alternative safe methods to potentially introduce a single blank line between top-level object entries for improved manual readability, if feasible without compromising the library's formatting strengths.

### 7.2 Property Formatting (`properties:` Block)

*   **Current Behavior:** Object characteristics within the `properties:` block are saved using YAML's "block style" (one `key: value` pair per line).
    ```yaml
    properties:
      is_takeable: true
      is_interactive: true
      # ... etc
    ```
*   **Reasoning:** While YAML also supports a more compact "flow style" (`properties: {is_takeable: true, is_interactive: true, ...}`), the block style was chosen for significantly better readability and ease of manual editing, especially given the large number of boolean flags. Finding and changing a specific property is much easier with the block style.
*   **TODO:** (Low Priority) Re-evaluate the use of flow style only if the line count of `objects.yaml` becomes a critical issue, keeping in mind the negative impact it would likely have on readability and manual editing. 