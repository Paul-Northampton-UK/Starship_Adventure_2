# Game Pack Specification (v1)

A "pack" is a self-contained set of YAML files (plus optional assets) that the engine loads to run a themed game. Keep it minimal and readable.

Pack folder (example): packs/<pack_id>/
- Required files: game.yaml, rooms.yaml, objects.yaml, rules.yaml, lexicon.yaml, responses.yaml
- Optional: assets/ (images, audio, etc.)

## game.yaml
- Purpose: Pack metadata and startup defaults.
- Required fields:
  - id (string) - unique pack ID
  - name (string) - display name
  - version (string) - semantic version
  - engine_min_version (string) - minimum engine version
  - start_room_id (string) - initial room
  - start_power_state (string; offline|emergency|main_power)
- Optional: description, authors, created, tags, settings (misc toggles)
- Example:
```yaml
id: starship_adventure
name: Starship Adventure
version: 1.0.0
engine_min_version: 1.0.0
start_room_id: player_cabin
start_power_state: emergency
description: A sarcastic sci-fi text adventure.
```

## rooms.yaml
- Purpose: Defines rooms/areas and exits.
- Required fields:
  - rooms (list)
  - Each room: room_id, name, description
- Optional: first_visit_description, short_description, exits (dir: room_id), areas (list of area_id, name, description)
- Example:
```yaml
rooms:
  - room_id: player_cabin
    name: Player Cabin
    description: A compact cabin with emergency lighting.
    first_visit_description: You awake in a dim cabinâ€¦
    exits: { east: east_corridor, north: small_kitchen }
    areas:
      - area_id: bed_area
        name: Bed
        description: A sturdy bed with a footlocker.
```

## objects.yaml
- Purpose: Items, containers, doors, equipment.
- Required fields:
  - objects (list)
  - Each object: id, name, location (room_id)
- Optional: area_location, description, synonyms (list), weight, size,
  properties (booleans like is_takeable, is_storage, is_openable_closable, is_wearable),
  storage_contents (list of object IDs), state_descriptions (state: text), lock (type/key/code)
- Example:
```yaml
objects:
  - id: footlocker
    name: Footlocker
    location: player_cabin
    properties:
      is_storage: true
      is_openable_closable: true
    lock:
      type: key
      key_id: blue_keycard
  - id: blue_keycard
    name: Blue KeyCard
    location: player_cabin
    properties: { is_takeable: true }
```

## rules.yaml
- Purpose: Simple conditional logic and effects to augment handlers.
- Required: rules (list)
- Rule fields (minimal): when (event/key), target (id); optional requires (list), effects (list of actions)
- Optional: conditions (flags/states), messages (response keys)
- Example:
```yaml
rules:
  - when: unlock
    target: footlocker
    requires: [ blue_keycard ]
    effects:
      - set_flag: locker_unlocked
```

## lexicon.yaml
- Purpose: Vocabulary and synonyms to help the parser.
- Required: file exists
- Optional: synonyms (object_id: list), verbs (intent: list), nouns (extra object words)
- Example:
```yaml
synonyms:
  blue_keycard: [ keycard, blue card, access card ]
  footlocker: [ locker, chest ]
verbs:
  open: [ open, unseal ]
  take: [ take, pick up, grab ]
```

## responses.yaml
- Purpose: Message templates the engine formats and prints.
- Required: keys mapping to lists of strings
- Optional: placeholders in templates (e.g., {object_name})
- Example:
```yaml
open_success:
  - "The {object_name} opens with a soft click."
locked:
  - "It won't budge. The '{object_name}' seems to be locked."
move_success:
  - "[{room_name}]\n{room_description}"
```

## assets/ (optional)
- Purpose: Images/audio associated with the pack.
- Note: Referenced by future GUI; keep paths relative to the pack.

---
Implementation note: The current engine reads from packs/. Packs will live under packs/<pack_id>/. At runtime, the engine will use game.yaml (for start settings) and then load rooms.yaml, objects.yaml, and responses.yaml; rules.yaml and lexicon.yaml are for incremental features.

