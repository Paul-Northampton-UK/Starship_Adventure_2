# Starship Adventure 2

A generic, extensible text-adventure engine with a hub that can run multiple themed game packs. Includes tools to author packs (objects, rooms, dialogue) and a GUI prototype. One example pack is a sci‑fi adventure with a sarcastic AI narrator.

## Features

- Text-based adventure with GUI interface
- Natural language command parsing
- Sarcastic AI narrator (example pack)
- Environmental mechanics (oxygen, temperature, gravity)
- Inventory system
- Multiple puzzle types
- Save/Load system

## Current Status (August 2025)

**Implemented:**
- Core engine with modular command handlers via `engine/game_loop.py`
- NLP command parsing with spaCy + custom `EntityRuler` patterns; supports single and two-word directions
- YAML data loading and validation (`engine/yaml_loader.py`, `engine/schemas.py`)
- Game state tracking (`engine/game_state.py`): rooms, areas, visibility, inventory (held/worn), object state
- Command handlers implemented: Move, Look, Inventory, Quit, Take, Drop, Equip (wear/remove), Search, Put, Take From, Lock, Unlock, Open, Close
- Response variation system via `packs/responses.yaml`
- Room/Area description system with first-visit/short descriptions and dynamic object listing by state and placement (`location` / `area_location`)
- Logging via Loguru with rotating file logs
- Tools: CustomTkinter Object Editor under `tools/object_editor/`
- Hub groundwork for multi-pack workflow (see Game Packs & Hub). Current runtime still reads from `packs/` paths; pack loader is planned.
- Test suite exists under `tests/` (some tests predate the latest parser/engine changes)

**Planned / In Progress:**
- GUI prototype using Pygame (`main.py` shows a placeholder window); full GUI gameplay pending
- Container capacity checks (size/weight/count) and advanced inventory limits
- Environmental systems (oxygen, temperature, gravity, hazards)
- Narrator help/hint system and profanity filtering logic
- Save/Load subsystem
- Multi-pack loader: load `rooms.yaml`, `objects.yaml`, `responses.yaml` from a selected pack
- Central Hub app to manage multiple packs (create, edit, validate, test)
- Audio/visual polish and assets
- Refresh and expand automated tests

## Setup

1. Clone the repository:
```bash
git clone https://github.com/Paul-Northampton-UK/Starship_Adventure_2.git
cd Starship_Adventure_2
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Unix/MacOS
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download the spaCy English model (required for NLP):
```
python -m spacy download en_core_web_sm
```

5. Run the game (text loop in terminal):
```bash
python -m engine.game_loop

Alternatively, run the simple GUI placeholder window (not gameplay yet):
```
python -m engine.game_loop
```
```

## Project Structure

- `engine/` - Core game engine components
- `packs/` - Default game data and content (temporary runtime source until pack loader lands)
- `packs/` - Game packs library (planned runtime source). Each pack will contain its own `rooms.yaml`, `objects.yaml`, `responses.yaml`, etc.
- `logs/` - Game and system logs
- `saves/` - Save game files
- `docs/` - Documentation
- `tools/` - Editors and utilities (e.g., Object Editor, Hub at `tools/main_design_hub.py`, library under `tools/game_library/`)

## Game Packs & Hub

- Engine will support multiple game packs selectable from a central Hub.
- A pack will live under `packs/<pack_id>/` and minimally include:
  - `rooms.yaml` — world layout and descriptions
  - `objects.yaml` — items, containers, equipment, metadata
  - `responses.yaml` — narrator/system responses
  - `profanity_words.yaml` — optional
  - Optional pack-specific assets/config
- During the transition period, the runtime still reads from `packs/`. The Hub/tools will save to `packs/<pack_id>/`; a pack loader will copy/symlink/point the engine to the pack content.

## Development

- Python 3.12+
- spaCy for natural language processing
- fuzzywuzzy for typo tolerance (basic)
- YAML for game content (soon per-pack under `packs/<pack_id>/`)
- Loguru for logging
- Pygame (GUI prototype in `main.py`)

## License

This project is open source and available under the MIT License.

## Future Considerations

*   **Game Engine Framework:** If the project grows significantly in complexity, especially towards multiplayer features, consider investigating the [Evennia](https://www.evennia.com/) Python MUD/MUX/MU* framework as an alternative to the custom engine. It provides built-in networking, persistence, command parsing, and other features but comes with its own learning curve.
*   **Advanced NLP:** Explore more sophisticated NLP techniques for command parsing if needed (e.g., handling more complex sentence structures, coreference resolution).
*   **GUI:** Expand the current Pygame prototype into a full GUI experience.
*   **Detailed Exits:** Enhance the location descriptions to include more dynamic or flavorful text for exits based on visited status or other conditions (using potentially existing `rooms.yaml` structure or defining a new one). 