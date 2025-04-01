import pytest
from engine.command_parser import CommandParser, CommandType, ParsedCommand
from engine.game_state import GameState

@pytest.fixture
def game_state():
    """Create a fresh GameState instance for each test."""
    return GameState(current_room_id="ship_bridge")

@pytest.fixture
def command_parser(game_state):
    """Create a fresh CommandParser instance for each test."""
    return CommandParser(game_state)

def test_empty_command(command_parser):
    """Test handling of empty commands."""
    parsed = command_parser.parse_command("")
    assert parsed.command_type == CommandType.UNKNOWN
    assert parsed.target is None
    assert parsed.preposition is None
    assert parsed.indirect_object is None
    assert parsed.raw_input == ""

def test_simple_commands(command_parser):
    """Test parsing of simple commands without targets."""
    # Test inventory command
    parsed = command_parser.parse_command("inventory")
    assert parsed.command_type == CommandType.INVENTORY
    assert parsed.target is None
    
    # Test help command
    parsed = command_parser.parse_command("help")
    assert parsed.command_type == CommandType.HELP
    assert parsed.target is None
    
    # Test quit command
    parsed = command_parser.parse_command("quit")
    assert parsed.command_type == CommandType.QUIT
    assert parsed.target is None

def test_command_aliases(command_parser):
    """Test that command aliases are properly recognized."""
    # Test look aliases
    assert command_parser.parse_command("look").command_type == CommandType.LOOK
    assert command_parser.parse_command("l").command_type == CommandType.LOOK
    assert command_parser.parse_command("examine").command_type == CommandType.LOOK
    assert command_parser.parse_command("x").command_type == CommandType.LOOK
    
    # Test movement aliases
    assert command_parser.parse_command("go").command_type == CommandType.GO
    assert command_parser.parse_command("move").command_type == CommandType.GO
    assert command_parser.parse_command("walk").command_type == CommandType.GO
    assert command_parser.parse_command("run").command_type == CommandType.GO
    
    # Test direction aliases
    assert command_parser.parse_command("north").command_type == CommandType.GO
    assert command_parser.parse_command("n").command_type == CommandType.GO
    assert command_parser.parse_command("south").command_type == CommandType.GO
    assert command_parser.parse_command("s").command_type == CommandType.GO

def test_commands_with_targets(command_parser):
    """Test parsing of commands with targets."""
    # Test look with target
    parsed = command_parser.parse_command("look at door")
    assert parsed.command_type == CommandType.LOOK
    assert parsed.target == "door"
    
    # Test take with target
    parsed = command_parser.parse_command("take key")
    assert parsed.command_type == CommandType.TAKE
    assert parsed.target == "key"
    
    # Test drop with target
    parsed = command_parser.parse_command("drop book")
    assert parsed.command_type == CommandType.DROP
    assert parsed.target == "book"

def test_commands_with_prepositions(command_parser):
    """Test parsing of commands with prepositions and indirect objects."""
    # Test use with preposition
    parsed = command_parser.parse_command("use key with door")
    assert parsed.command_type == CommandType.USE
    assert parsed.target == "key"
    assert parsed.preposition == "with"
    assert parsed.indirect_object == "door"
    
    # Test use with different preposition
    parsed = command_parser.parse_command("use key on door")
    assert parsed.command_type == CommandType.USE
    assert parsed.target == "key"
    assert parsed.preposition == "on"
    assert parsed.indirect_object == "door"

def test_unknown_commands(command_parser):
    """Test handling of unknown commands."""
    parsed = command_parser.parse_command("xyzzy")
    assert parsed.command_type == CommandType.UNKNOWN
    assert parsed.target is None
    assert parsed.preposition is None
    assert parsed.indirect_object is None
    assert parsed.raw_input == "xyzzy"

def test_command_processing(command_parser):
    """Test processing of various commands."""
    # Test look command
    result, continue_game = command_parser.process_command("look")
    assert "You are in the ship_bridge" in result
    assert continue_game is True
    
    # Test inventory command
    result, continue_game = command_parser.process_command("inventory")
    assert "Your inventory is empty" in result
    assert continue_game is True
    
    # Test quit command
    result, continue_game = command_parser.process_command("quit")
    assert "Goodbye" in result
    assert continue_game is False
    
    # Test unknown command
    result, continue_game = command_parser.process_command("xyzzy")
    assert "I don't understand that command" in result
    assert continue_game is True

def test_inventory_management(command_parser, game_state):
    """Test inventory-related commands with actual inventory changes."""
    # Add an item to inventory
    game_state.add_to_inventory("torch")
    
    # Test inventory command
    result, _ = command_parser.process_command("inventory")
    assert "torch" in result
    
    # Test take command
    result, _ = command_parser.process_command("take key")
    assert "try to take the key" in result
    
    # Test drop command
    result, _ = command_parser.process_command("drop torch")
    assert "try to drop the torch" in result 