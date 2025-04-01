You are an expert in Python.

Project Style & Philosophy
- Use classes for core entities: Game, Player, Room, Object, Narrator, etc.
- Use functions for utility tasks: command parsing, string formatting, file management.
- Mix OOP and functional styles as needed for clarity and modularity.
- Favor iteration and reusable modules over copy/paste or bloated logic.
- Use clear, descriptive variable names — e.g. is_active, has_power, can_enter.

Project Structure & Naming
- Use snake_case for file and folder names (ui/main_window.py)
- Use snake_case for variables and functions
- Use PascalCase for class names
- Use prefixes to identify categories of objects (e.g., nav_, com_, sci_)
- Organize code into folders: engine/, ui/, data/, logs/, assets/, saves/

Dependencies

  Standard Libraries:
  - os, sys, re, copy, math, glob, datetime, textwrap, json

  Third-Party:
  - pygame – core GUI and event loop
  - pygame_gui (optional) – for cleaner UI components
  - PyYAML – game data from YAML
  - spaCy – natural language command parsing
  - en_core_web_sm – English model for spaCy
  - loguru – smart, clean logging system
  - colorama – colored text in debug/console output
  - pillow (PIL) – display or process images if needed

Command System
- All player commands should support multiple forms (e.g., n, go north, move north)
- Use NLP (via spaCy) to parse flexible input
- Support command aliases and easily expandable actions
- Catch and respond to gibberish, invalid inputs, or profanity with narrator sarcasm

Error Handling & Code Hygiene
- Handle edge cases and invalid input early in functions using guard clauses
- Avoid nested if/else blocks where possible — prefer early return
- Use try/except around all file I/O and YAML parsing
- Log all major actions and errors using loguru
- Keep logs user-readable, timestamped, and rotated for length

Documentation & Maintainability
- Add docstrings to all classes and functions
- Use inline comments to explain logic where needed
- Keep functions short and focused — one purpose per function
- Split complex logic into separate modules (inventory.py, navigation.py, etc.)

Expandability & Mod Support
- All game content (rooms, objects, logic) should be defined in YAML files
- Game engine must load and interpret YAML without needing code changes
- Allow future expansion by you or others with minimal effort

Future Considerations
- You may add FastAPI later for:
  High score boards
  Multiplayer
  Remote save sync

If so, then async def, Pydantic, and middleware will become relevant — but not now.