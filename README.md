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
- Central Game Loop (`engine/game_loop.py`) with basic command handling (Move, Look, Quit)
- Movement between rooms and areas
- Room/Area descriptions with `first_visit_description` and `short_description` logic

**Planned / In Progress:**
- Graphical User Interface (GUI) using Pygame (`ui/`)
- Detailed gameplay mechanics (inventory management (Take/Drop), object interaction (Use/Examine), environment, puzzles)
- Narrator logic and interaction
- Save/Load functionality
- Audio/Visual elements
- Expanded testing

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

4. Run the game (basic text loop):
```bash
python -m engine.game_loop
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

## Future Considerations

*   **Game Engine Framework:** If the project grows significantly in complexity, especially towards multiplayer features, consider investigating the [Evennia](https://www.evennia.com/) Python MUD/MUX/MU* framework as an alternative to the custom engine. It provides built-in networking, persistence, command parsing, and other features but comes with its own learning curve.
*   **Advanced NLP:** Explore more sophisticated NLP techniques for command parsing if needed (e.g., handling more complex sentence structures, coreference resolution).
*   **GUI:** Potentially add a graphical user interface (GUI) instead of the pure text interface.
*   **Detailed Exits:** Enhance the location descriptions to include more dynamic or flavorful text for exits based on visited status or other conditions (using potentially existing `rooms.yaml` structure or defining a new one). 