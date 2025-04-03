# engine/game_loop.py

import logging
from .game_state import GameState
from .nlp_command_parser import NLPCommandParser

class GameLoop:
    """Manages the main game loop and orchestrates game flow."""

    def __init__(self):
        """Initializes the Game Loop."""
        logging.info("Initializing Game Loop...")
        
        # Initialize game state (assuming 'bridge' as starting room for now)
        # TODO: Load actual starting room from game data later
        self.game_state = GameState(current_room_id="bridge")
        logging.info(f"GameState initialized. Starting room: {self.game_state.current_room_id}")

        # Initialize command parser, passing the game state
        self.command_parser = NLPCommandParser(self.game_state)
        logging.info("NLPCommandParser initialized.")
        
        self.is_running = False
        logging.info("Game Loop initialized.")

    def run(self):
        """Starts and runs the main game loop."""
        self.is_running = True
        logging.info("Starting game loop...")

        print("Welcome to Starship Adventure 2!") # Basic welcome message

        while self.is_running:
            # TODO: Implement core loop:
            # 1. Get player input
            # 2. Parse command (Current Step)
            # 3. Process command (update game state)
            # 4. Display output/result
            # 5. Check for quit condition
            
            # 1. Get player input
            command_input = input("> ").strip()
            if not command_input:
                continue # Ask for input again if empty

            # 5. Check for quit condition (early check)
            if command_input.lower() == "quit":
                 self.is_running = False
                 continue # Skip parsing/processing if quitting

            # 2. Parse command
            try:
                parsed_intent = self.command_parser.parse_command(command_input)
                # For now, just print the parsed intent to see the result
                print(f"Parsed: {parsed_intent}") 
            except Exception as e:
                logging.error(f"Error parsing command '{command_input}': {e}", exc_info=True)
                print("An error occurred while parsing your command.")

            # TODO: 3. Process command using parsed_intent
            # TODO: 4. Display output/result from processing
                
        logging.info("Game loop stopped.")
        print("Goodbye!")

# Example of how it might be run (likely from main.py later)
if __name__ == '__main__':
    # Setup basic logging for testing this module directly
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    game_loop = GameLoop()
    # In a real scenario, we'd load game data and initialize game_state/parser properly here
    # game_loop.setup_game()
    game_loop.run() 