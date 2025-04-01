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