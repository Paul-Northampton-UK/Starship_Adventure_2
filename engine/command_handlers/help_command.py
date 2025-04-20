from engine.game_state import GameState
from engine.nlg import generate_response
from engine.nlp.types import ParsedIntent

def handle_help(intent: ParsedIntent, game_state: GameState) -> str:
    """
    Handles the HELP command, providing players with information about available commands.
    """
    # TODO: Implement logic to list all commands or provide help for a specific command.
    return generate_response("help_placeholder", game_state.config) 