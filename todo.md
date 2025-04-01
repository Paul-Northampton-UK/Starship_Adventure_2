# Starship Adventure 2 - Development Todo List

## 🧱 Core Engine Setup
- [x] Set up folder structure
  - [x] Create engine/ directory
  - [x] Create ui/ directory
  - [x] Create data/ directory
  - [x] Create logs/ directory
  - [x] Create assets/ directory
  - [x] Create saves/ directory
- [x] Create main.py entry point
- [x] Set up logging system with loguru
- [ ] Implement YAML loader
  - [ ] Create YAML schema for rooms
  - [ ] Create YAML schema for objects
  - [ ] Create YAML schema for settings
  - [ ] Implement YAML validation
- [ ] Design central game loop
  - [ ] Implement state machine
  - [ ] Add game state transitions
  - [ ] Handle game events
- [ ] Integrate spaCy for command parsing
  - [ ] Set up NLP model
  - [ ] Create command parser
  - [ ] Implement intent recognition
- [ ] Create command system
  - [ ] Implement alias/action translation
  - [ ] Add command handler modules
  - [ ] Create command vocabulary system

## 🖥️ GUI & Interface
- [x] Create basic game window
- [ ] Implement main UI components
  - [ ] Room name header
  - [ ] Room exits footer
  - [ ] Main scrollable output box
  - [ ] Narrator dialogue box
  - [ ] Visible objects box
  - [ ] Command input field
- [ ] Add interactive controls
  - [ ] Compass control (clickable directions)
  - [ ] Action buttons (Look, Take, Use, Inventory)
- [ ] Create side panels
  - [ ] Inventory panel with weight/size display
  - [ ] Player stats panel
  - [ ] Environmental panel
  - [ ] Fog-of-war map panel
- [ ] Add UI elements
  - [ ] Score display
  - [ ] Move counter
  - [ ] Save/Load buttons
- [ ] Implement UI theming system

## 🧠 Command & Interaction System
- [ ] Implement natural language processing
  - [ ] Add command variations support
  - [ ] Create command aliases
  - [ ] Add abbreviations support
- [ ] Create narrator interaction system
  - [ ] Add help command
  - [ ] Add insult command
  - [ ] Add ask command
  - [ ] Add hint command
- [ ] Implement error handling
  - [ ] Add gibberish detection
  - [ ] Create invalid input responses
  - [ ] Add profanity handling
- [ ] Create command vocabulary system
  - [ ] Make vocabulary YAML-based
  - [ ] Add vocabulary expansion support

## 🎮 Gameplay Mechanics
- [ ] Create object system
  - [ ] Define object structure
  - [ ] Add object properties (ID, name, description, size, weight)
  - [ ] Implement visibility system
- [ ] Build inventory system
  - [ ] Add carrying limits
  - [ ] Implement backpack system
  - [ ] Create object tracking
- [ ] Implement environmental mechanics
  - [ ] Add room-specific conditions
  - [ ] Create hazard system
  - [ ] Implement death scenarios
- [ ] Add object interaction
  - [ ] Create container logic
  - [ ] Add object activation
  - [ ] Implement assembly/disassembly

## 🧩 Puzzle & Story System
- [ ] Create puzzle framework
  - [ ] Implement difficulty tiers
  - [ ] Add puzzle types
    - [ ] Logic puzzles
    - [ ] Code entry terminals
    - [ ] Object combination puzzles
    - [ ] Environmental puzzles
- [ ] Build scoring system
  - [ ] Add difficulty-based scoring
  - [ ] Create progress tracking
- [ ] Implement story system
  - [ ] Add room descriptions
  - [ ] Create terminal entries
  - [ ] Add story progression

## 🤖 Narrator System
- [ ] Create narrator module
  - [ ] Add contextual responses
  - [ ] Implement sarcasm system
  - [ ] Create warning system
- [ ] Add interaction features
  - [ ] Create hint system
  - [ ] Add tutorial system
  - [ ] Implement response variations

## 💾 Save/Load System
- [ ] Create save system
  - [ ] Implement auto-save
  - [ ] Add manual save/load
  - [ ] Create profile system
- [ ] Add save data persistence
  - [ ] Save inventory state
  - [ ] Save room progress
  - [ ] Save player stats
  - [ ] Save puzzle progress
  - [ ] Save environmental state

## 🔊 Audio/Visual
- [ ] Add audio system
  - [ ] Create loading screen music
  - [ ] Implement ambient music
  - [ ] Add sound effects
- [ ] Implement visual elements
  - [ ] Add room artwork
  - [ ] Create cutscene system

## 📜 Logging System
- [x] Set up basic logging
- [ ] Create player log
  - [ ] Log player commands
  - [ ] Log system output
- [ ] Implement system log
  - [ ] Log function calls
  - [ ] Log errors
  - [ ] Log state changes

## 🧹 Code Quality
- [ ] Follow naming conventions
  - [ ] Use snake_case for variables/functions
  - [ ] Use PascalCase for classes
  - [ ] Add ID prefixes
- [ ] Add documentation
  - [ ] Write docstrings
  - [ ] Add inline comments
- [ ] Implement error handling
  - [ ] Add I/O error handling
  - [ ] Add YAML parsing error handling
- [ ] Maintain code organization
  - [ ] Keep modules focused
  - [ ] Create reusable components

## 🛸 Future Features
- [ ] Add multiplayer support
- [ ] Implement skill system
- [ ] Create achievements system
- [ ] Add text-to-speech
- [ ] Create modding tools
- [ ] Add surface missions 