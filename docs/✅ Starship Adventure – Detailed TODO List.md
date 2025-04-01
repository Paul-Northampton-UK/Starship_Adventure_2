✅ Starship Adventure – Detailed TODO List


🧱 Core Engine

 Set up folder structure: engine/, ui/, data/, saves/, logs/, assets/

 Create main.py entry point

 Implement YAML loader (for rooms, objects, settings)

 Design central game loop and state machine

 Integrate spaCy for command parsing

 Create alias/action translation system (e.g. n, go north, walk north)

 Build modular command handler (actions, movement, examine, etc.)

 Integrate loguru for dev/system logging


🖥️ GUI & Interface

 Build main game window with pygame

 Add GUI components:

 Room name header

 Room exits footer

 Main scrollable game output box

 Narrator dialogue box

 Visible objects box

 Command input field (typed input)

 Add compass control (clickable directions)

 Add action buttons (Look, Take, Use, Inventory)

 Add toggleable side panels:

 Inventory (weight/size shown)

 Player stats (health, stamina, oxygen, etc.)

 Environmental panel (oxygen, gravity, temperature)

 Fog-of-war map panel

 Display score and move counter

 Save / Load buttons

 Implement UI theming/personalization options (future feature)


🧠 Command & Interaction System

 Support typed input with NLP variations

 Enable command aliases and abbreviations

 Add player-to-narrator interactions (e.g. help, insult, ask, hint)

 Handle invalid/gibberish commands with unique narrator responses

 Ensure command vocabulary is easily expandable via YAML


🎮 Gameplay Mechanics

 Define object structure (ID, name, description, size, weight, visibility, etc.)

 Build inventory management system

 Backpack system with size/weight constraints

 Carried object tracking

 Implement environmental mechanics:

 Room-specific oxygen, temperature, gravity, pressure

 Hazards (e.g. suffocation, overheating, radiation)

 Handle death scenarios and narrator warnings

 Object container logic (e.g. batteries inside torch, items inside locker)

 Enable object activation, assembly, disassembly


🧩 Puzzle & Story System

 Implement puzzle system with difficulty tiers (Easy, Medium, Hard)

 Add support for:

 Logic puzzles

 Code entry terminals

 Physical object combination puzzles

 Environmental / time-based puzzles

 Implement scoring system based on puzzle difficulty

 Track puzzle completion and tie it to story progress

 Embed core story across room descriptions, tablets, terminals


🤖 Narrator System

 Build narrator module:

 Contextual sarcasm and insults

 Humorous responses to player input

 Warnings before danger

 Custom reactions to swearing or nonsense input

 Narrator hint system with point penalty

 Narrator help system for tutorial commands


💾 Save/Load System

 Auto-save on game exit

 Manual save/load UI with multiple player profiles

 Save system must persist:

 Inventory

 Rooms visited

 Player stats

 Puzzle progress

 Environmental states


🔊 Audio/Visual

 Add loading screen splash with fade + intro music

 Implement ambient music engine (per area or event)

 Add basic sound effects (UI actions, interactions, alerts)

 Display optional static artwork per room or cutscene


📜 Logging

 Player log (all typed input + system output)

 System log (functions triggered, errors, game state changes)

 Use loguru with rotating log files and timestamps


🧩 Expandability

 Game world defined via external YAML

 All rooms, objects, puzzles, and dialogue must be extendable

 YAML validation and error catching

 Document expansion format (README or DevDocs)


🧹 Coding & Dev Standards

 Follow naming conventions:

snake_case for variables/functions

PascalCase for classes

ID prefixes (e.g., nav_, com_)

 Docstrings and inline comments throughout

 Error handling for all I/O and YAML parsing

 Clean modular codebase with reusable components


🛸 Future Features (Optional / Phase 2+)

 Multiplayer or co-op exploration mode

 Skill-based player progression (e.g. hacking, engineering)

 Achievements/trophies system

 Text-to-Speech narrator (e.g. ElevenLabs)

 Modding tools for community content

 Surface or planet-based missions

