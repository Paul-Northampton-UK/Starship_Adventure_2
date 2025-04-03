# Starship Adventure 2

A sci-fi text adventure game with a GUI interface, featuring a sarcastic AI narrator.

## Features

- Text-based adventure with GUI interface
- Natural language command parsing
- Sarcastic AI narrator
- Environmental mechanics (oxygen, temperature, gravity)
- Inventory system
- Multiple puzzle types
- Save/Load system

## Current Status (April 2024)

**Implemented:**
- Basic project structure and setup
- Core data loading from YAML files (`engine/yaml_loader.py`)
- Schema validation for YAML data (`engine/schemas.py`)
- Natural Language command parsing using spaCy (`engine/nlp_command_parser.py`)
- Basic game state tracking (`engine/game_state.py`)
- Logging setup using Loguru
- Initial testing framework for core components

**Planned / In Progress:**
- Central Game Loop (`engine/game_loop.py`)
- Graphical User Interface (GUI) using Pygame (`ui/`)
- Detailed gameplay mechanics (inventory, environment, puzzles)
- Narrator logic and interaction
- Save/Load functionality
- Audio/Visual elements

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

4. Run the game:
```bash
python main.py
```

## Project Structure

- `engine/` - Core game engine components
- `ui/` - GUI and interface code
- `data/` - Game data and content
- `logs/` - Game and system logs
- `assets/` - Images, sounds, and other resources
- `saves/` - Save game files
- `docs/` - Documentation

## Development

- Python 3.12+
- Uses pygame for GUI
- spaCy for natural language processing
- YAML for game content
- Loguru for logging

## License

This project is open source and available under the MIT License. 