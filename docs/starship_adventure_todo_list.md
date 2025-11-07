✅ Starship Adventure – Detailed TODO List

🧱 Core Engine

✅ Set up folder structure: engine/, ui/, data/, saves/, logs/, assets/
✅ Create main.py entry point
✅ Implement YAML loader (for rooms, objects, settings)
✅ Design central game loop and state machine (GameState now robustly manages current_room_id, current_area_id, object states, and visibility logic)
✅ Integrate spaCy for command parsing
✅ Create alias/action translation system (e.g. n, go north, walk north) - Handled by NLP parser
✅ Build modular command handler (actions, movement, examine, etc.) - Handlers created
✅ Integrate loguru for dev/system logging
✅ Implement loading of initial game state (start room, power state) from game_config.yaml (Basic loading done)

🎨 GUI & Interface

🔄 Build main game window with pygame
🔄 Add GUI components:
  - Room name header
  - Room exits footer
  - Main scrollable game output box
  - Narrator dialogue box
  - Visible objects box
  - Command input field (typed input)
  - Compass control (clickable directions)
  - Action buttons (Look, Take, Use, Inventory)
  - Toggleable side panels:
    - Inventory (weight/size shown)
    - Player stats (health, stamina, oxygen, etc.)
    - Environmental panel (oxygen, gravity, temperature)
    - Fog-of-war map panel
  - Score and move counter
  - Save / Load buttons
🔄 Implement UI theming/personalization options (future feature)

🧠 Command & Interaction System

✅ Support typed input with NLP variations (Basic NLP in place)
✅ Enable command aliases and abbreviations (Handled by NLP patterns/verbs)
✅ Refactor parser.py into smaller helper functions
🔄 Add player-to-narrator interactions (e.g. help, insult, ask, hint)
✅ Handle invalid/gibberish commands with unique narrator responses (Implemented via responses.yaml)
✅ Ensure command vocabulary is easily expandable via YAML (Objects/synonyms loaded)
✅ Improve target extraction (handle prepositions like "with", "on", and also recognizes AREA entities as targets) - Improved via entity ruler and parser logic
🔄 Refine command parsing logic (e.g., disambiguation, error handling)
🔄 Implement profanity filtering for player input (Data files created, logic pending)
🔸 Note: spaCy model `en_core_web_sm` must be installed as part of setup.
🔄 Implement fuzzy matching/typo tolerance (using fuzzywuzzy) - Potential future step
✅ Implement response variations (using responses.yaml)
✅ Handle plural items in responses
✅ Display location description automatically on move
✅ Parse two-word diagonal directions (e.g., "north west")
✅ Add specific response for self-insertion container attempts (e.g., put pack in pack)
   - TODO: Implement 'put_fail_incomplete' response/logic.
   - TODO: Implement 'take_from_fail_incomplete' response/logic.
   - TODO: Refine 'take_from_fail_ambiguous' logic/response.
   - TODO: Refine wear/remove responses for different item types (e.g., "slip on" vs "wear" vs "put on").

🎮 Gameplay Mechanics

✅ Define object structure (ID, name, description, size, weight, visibility, location, area_location, properties like is_takeable, is_openable_closable, etc.)
✅ Build inventory management system (Core implemented: take, drop, wear, remove, put, take_from, wear_from; take/drop logic now correctly handles object visibility in rooms/areas)
✅ Backpack system with size/weight constraints -> (Partially addressed by container logic, capacity check TODO)
✅ Carried object tracking (In hand slot / worn items)
🔄 Implement environmental mechanics:
  - Room-specific oxygen, temperature, gravity, pressure
  - Hazards (e.g. suffocation, overheating, radiation)
  - Handle death scenarios and narrator warnings
✅ Object container logic (Core implemented: put items in, take items out, wear items from held/worn containers)
   - TODO: Implement container capacity checks (size/weight/count).
   ✅ Implement container open/close states and check in commands (is_openable_closable property added, open/close handlers updated).
🔄 Enable object activation, assembly, disassembly
🔄 Implement HELP system (discuss approach: datapad vs command list)

🧩 Puzzle & Story System

🔄 Implement puzzle system with difficulty tiers (Easy, Medium, Hard)
🔄 Add support for:
  - Logic puzzles
  - Code entry terminals
  - Physical object combination puzzles
  - Environmental / time-based puzzles
🔄 Implement scoring system based on puzzle difficulty
🔄 Track puzzle completion and tie it to story progress
🔄 Embed core story across room descriptions, tablets, terminals

🤖 Narrator System

🔄 Build narrator module:
  ✅ Contextual sarcasm and insults (Via responses.yaml)
  ✅ Humorous responses to player input (Via responses.yaml)
  🔄 Warnings before danger
  ✅ Custom reactions to swearing or nonsense input (Via responses.yaml, profanity logic pending)
  🔄 Narrator hint system with point penalty
  🔄 Narrator help system for tutorial commands

💾 Save/Load System

🔄 Implement SAVE/LOAD functionality
🔄 Auto-save on game exit
🔄 Manual save/load UI with multiple player profiles
🔄 Save system must persist:
  - Inventory
  - Rooms visited
  - Player stats
  - Puzzle progress
  - Environmental states

🔊 Audio/Visual

🔄 Add loading screen splash with fade + intro music
🔄 Implement ambient music engine (per area or event)
🔄 Add basic sound effects (UI actions, interactions, alerts)
🔄 Display optional static artwork per room or cutscene

📜 Logging

✅ Player log (all typed input + system output) - Captured by terminal
✅ System log (functions triggered, errors, game state changes) - Implemented via logging module
✅ Use loguru with rotating log files and timestamps - Basic logging setup done

🧩 Expandability

✅ Game world defined via external YAML
✅ All rooms, objects, puzzles, and dialogue must be extendable
✅ YAML validation and error catching (Via Pydantic schemas)
🔄 Document expansion format (README or DevDocs)

📦 Game Packs & Hub

🔄 Define pack structure under `packs/<pack_id>/` (rooms.yaml, objects.yaml, responses.yaml, profanity_words.yaml)
🔄 Implement pack loader: select `active_pack` and load its files into the engine
🔄 Update tools to save/edit per-pack files rather than root `data/`
🔄 Hub app (`tools/main_design_hub.py`) to browse, create, validate, and launch packs

🧹 Coding & Dev Standards

✅ Follow naming conventions:
  - snake_case for variables/functions
  - PascalCase for classes
  - ID prefixes (e.g., nav_, com_)
✅ Docstrings and inline comments throughout
✅ Error handling for all I/O and YAML parsing (Basic handling implemented)
✅ Clean modular codebase with reusable components (Ongoing effort)
   - TODO: Review necessity/usage of general GameState.inventory list.

🛸 Future Features (Optional / Phase 2+)

🛠️ Admin Interface (Phase 1)

🔄 Core Setup:
- Create admin interface window structure
- Implement user authentication system
- Set up tab navigation system
- Design basic layout and styling

🔄 Object Management:
- Build object list panel with search/filter
- Create object editor panel
- Implement property editor with validation
- Add object relationship manager
- Build test panel for object interactions

🔄 Room Management:
- Create room list panel with filters
- Build room editor panel
- Implement grid-based room layout editor
- Add object placement tool
- Create exit/connection manager

🔄 Data Management:
- Implement auto-save system
- Add version history tracking
- Create backup/restore functionality
- Build export/import tools

🛠️ Admin Interface (Phase 2)

🔄 Puzzle Management:
  - Create puzzle list panel
  - Build puzzle editor interface
  - Implement solution step editor
  - Add hints management system
  - Create puzzle test environment

- Game Systems:
  - Build theme editor
  - Create audio management system
  - Implement loading screen editor
  - Add game settings manager

- Visual Tools:
  - Implement drag-and-drop interface
  - Create visual room layout editor
  - Build object placement grid
  - Add relationship visualization

🛠️ Admin Interface (Phase 3)

🔄 Testing Tools:
  - Create game state simulator
  - Build object interaction tester
  - Implement room transition tester
  - Add puzzle solution validator
  - Create performance metrics display

- Polish & Optimization:
  - Enhance UI/UX design
  - Optimize performance
  - Add advanced validation
  - Implement bulk edit tools
  - Create template system

