Starship Adventure Game - Product Requirements Document (PRD)

1. Project Overview

Title: Starship AdventureGenre: Sci-fi Text Adventure with GUI InterfacePlatform: Windows (standalone .exe installer)Audience: General audience, suitable for all agesGoal: Create a professional, interactive text adventure game with a custom GUI, logical puzzles, a central mystery, and a sarcastic AI narrator.

Initial State: The game begins according to settings defined in `game_config.yaml`, specifying the starting room (e.g., Player Cabin) and initial power state (e.g., Emergency Power).

2. Core Gameplay Features

Players awaken aboard an abandoned spaceship with no memory of events.

Exploration via compass directions (N, NE, NW, SE, SW, S, E, W, U, D) with room-by-room discovery.

Object interactions: examine, take, drop, use, combine, etc.

Sarcastic narrator provides humorous commentary and hints.

Player solves puzzles to unlock new areas and uncover the story.

Primary storyline: discover why the ship is abandoned and rescue the crew.

3. Game Structure & Flow

Semi-linear progression with interconnected puzzles.

Players explore the ship room by room. Some larger rooms (e.g., Bridge) are further divided into distinct Areas (e.g., Navigation Station, Helm) which function like sub-locations. Players can move between these Areas within a room, and interact with objects specific to an Area. Room exits are accessible from both the main room level and any Area within that room.

Multiple puzzle difficulty tiers:

Easy (local interaction)

Medium (multi-room or object-based)

Hard (complex, multi-stage puzzles)

Some puzzles must be solved to access key story areas.

Puzzle solutions are single-path, with hint support via narrator (point deduction).

4. GUI & Interface Design

Main game window (text output)

Header: Room name

Footer: Available exits

Narrator box: Sarcastic or humorous responses

Object list: Items visible in the current room

Command input box: Accepts typed commands

Optional click-based controls:

Compass buttons for movement

Action buttons (e.g. "Look", "Take", etc.)

Toggleable UI windows:

Inventory (with weight/size limits)

Player stats

Environmental conditions (oxygen, pressure, temperature, etc.)

Map (basic fog-of-war)

Load and Save buttons on GUI

Score and turn counter

Support for UI skinning/personalization (future optional)

5. Command & Interaction System

Primary input: typed commands

Support for natural language variations (e.g. "go north", "move n", "n", "north west") - Handled via NLP and custom patterns.

NLP engine: spaCy (installed and tested) with custom EntityRuler patterns for directions and game objects.

Expandable command vocabulary via YAML (objects, synonyms).

Alias and abbreviation support (partially handled via NLP verb/pattern matching).

Narrator responds to unknown commands, gibberish, or swearing - Handled via configurable responses in `responses.yaml`. (Profanity filter logic pending).

Response variations for actions and feedback managed via `responses.yaml`.

Handles plural items correctly in responses (e.g., "wear boots" vs "wear hat").

6. Gameplay Systems

Inventory system with:

Carrying limits by weight and size (Pending implementation)

Containers (e.g., backpack) to expand capacity (Pending implementation)

Basic item handling (take, drop, wear, remove) implemented.

Environmental mechanics:

(Pending implementation)

Object properties:

Weight, size, power requirements, visibility (based on light), wearability (area/layer), takeability, etc.

Includes `is_plural` flag for correct grammatical handling.

7. Puzzles & Lore

Mixture of logic, environmental, item-combo, hacking, and code puzzles

Scoring based on difficulty tier

Puzzles expand narrative and unlock access

No random/procedural generation; world defined in YAML

Logs, terminals, and discovered files build the story

8. Narrator System

Persistent sarcastic AI personality, driven by responses defined in `responses.yaml`.

Offers:

Commentary (via responses)

Reactions to events (via responses)

Insults, jokes, and breaking the fourth wall (via responses)

Optional hints/help with point deduction (Pending implementation)

Narrator tied into tutorial/help system (Pending implementation)

May reference past actions, choices, or item usage (Future enhancement)

9. Save & Load System

Auto-save on exit

Manual save/load via GUI

Multiple save slots per player

Tracks:

Rooms visited

Player inventory

Puzzle progress

Environmental states

Narrator history (optional)

10. Audio/Visual Elements

Intro loading screen with fade and intro music

Ambient in-game music

Contextual sound effects (item interaction, combat, environment)

Artwork displayed optionally in certain areas or cutscenes

11. Endgame & Progression

Single main ending: player uncovers ship mystery and restores crew

Optional: score tracking, puzzles solved, map discovered

Future: achievements/awards system (deferred)

12. Expandability

Game content stored in YAML files

New rooms, puzzles, items, and dialogue can be added without altering core code

Full support for modular expansion in future versions

13. Logging System

Player log:

Tracks all player commands and game responses

System log:

Internal tracking of engine modules, functions, and errors

Use Loguru for logging

Rotating log files with timestamps

14. Development Standards & Technical Preferences

Programming Language:

Python 3.12+

Code Structure:

Modular architecture with clearly defined folders (e.g. engine/, ui/, data/, saves/)

main.py as entry point

Naming Conventions:

snake_case for variables and functions

PascalCase for classes

Consistent prefixes (e.g., nav_, com_, etc.) for IDs

Documentation:

Docstrings for all functions and classes

Inline comments where appropriate

Consistent style across codebase

Error Handling:

Try/except for all file I/O and parsing logic

Descriptive error messages

Logging:

Use loguru

Log levels: DEBUG, INFO, ERROR

Output to console and file

Testing:

No formal testing required yet

Core engine modules should be easily testable

Third-party Libraries:

spaCy — natural language parsing

pygame — GUI and audio handling

PyYAML — game data and config files

loguru — logging

colorama, textwrap, pillow, etc. as needed

Standard Libraries:

os, sys, re, math, datetime, copy, glob, json, etc.

15. Future Enhancements (Optional)

Multiplayer/co-op exploration

Skill-based puzzles or character development

Achievements system

TTS narrator using ElevenLabs or equivalent

Mod support

Planet-side missions outside the ship

Status: Requirements approved by Paul (creator)Next step: Begin prototype build of the core engine and GUI system

15. Admin Interface

A comprehensive graphical interface for game development and management, restricted to admin users.

Main Interface Components:

1. Top Navigation Bar
   - User authentication/role display
   - Save/load game state
   - Quick search across all elements

2. Tab System
   - Objects Management
   - Rooms Management
   - Puzzles Management
   - Game Systems
   - Relationships
   - Testing

3. Object Management Tab
   - Object List Panel (Left)
     - Search/filter objects
     - Category filters
     - Quick view of object relationships
   - Object Editor Panel (Right)
     - Basic Info (ID, name, category)
     - Properties Editor
     - Description Editor
     - Location/Puzzle Assignment
     - Visual Preview
     - Relationship Manager
     - Test Panel

4. Room Management Tab
   - Room List Panel (Left)
     - Deck/level filters
     - Room type filters
     - Quick view of room contents
   - Room Editor Panel (Right)
     - Basic Info
     - Grid Editor for room layout
     - Object Placement Tool
     - Exit/Connection Manager
     - State Descriptions Editor
     - Visual Preview

5. Puzzle Management Tab
   - Puzzle List Panel (Left)
     - Difficulty filters
     - Type filters
     - Status indicators
   - Puzzle Editor Panel (Right)
     - Puzzle Description
     - Required Objects
     - Solution Steps
     - Hints Manager
     - Test Environment

6. Game Systems Tab
   - Theme Editor
     - Color schemes
     - Font settings
     - UI layout
   - Audio Manager
     - Sound effects
     - Background music
     - Volume controls
   - Loading Screen Editor
   - Game Settings
     - Difficulty levels
     - Save/load options
     - Debug settings

7. Relationships Tab
   - Visual graph of object/room/puzzle connections
   - Dependency checker
   - Path validation
   - Circular reference detector

8. Testing Tab
   - Game state simulator
   - Object interaction tester
   - Room transition tester
   - Puzzle solution validator
   - Performance metrics

Key Features:

1. Real-time Validation
   - Immediate feedback on invalid changes
   - Conflict detection
   - Missing dependency warnings

2. Visual Tools
   - Drag-and-drop interface
   - Visual room layout editor
   - Object placement grid
   - Relationship visualization

3. Data Management
   - Auto-save functionality
   - Version history
   - Backup/restore
   - Export/import

4. Development Aids
   - Template system
   - Bulk edit capabilities
   - Search and replace
   - Reference finder

Implementation Strategy:

1. Core Functionality (Phase 1)
   - Basic object editor
   - Simple room editor
   - Essential validation

2. Enhanced Features (Phase 2)
   - Visual tools
   - Advanced validation
   - Testing capabilities

3. Polish and Optimization (Phase 3)
   - UI/UX improvements
   - Performance optimization
   - Additional tools

