import pytest
from engine.nlp_command_parser import NLPCommandParser, CommandIntent, ParsedIntent
from engine.game_state import GameState

@pytest.fixture
def game_state():
    """Create a fresh GameState instance for each test."""
    return GameState(current_room_id="ship_bridge")

@pytest.fixture
def nlp_parser(game_state):
    """Create a fresh NLPCommandParser instance for each test."""
    return NLPCommandParser(game_state)

def test_empty_command(nlp_parser):
    """Test handling of empty commands."""
    parsed = nlp_parser.parse_command("")
    assert parsed.intent == CommandIntent.UNKNOWN
    assert parsed.action is None
    assert parsed.target is None
    assert parsed.direction is None
    assert parsed.confidence == 0.0

def test_look_commands(nlp_parser):
    """Test various forms of look commands."""
    # Simple look
    parsed = nlp_parser.parse_command("look")
    assert parsed.intent == CommandIntent.LOOK
    assert parsed.confidence > 0.5
    
    # Look with target
    parsed = nlp_parser.parse_command("look at the door")
    assert parsed.intent == CommandIntent.LOOK
    assert parsed.target == "door"
    assert parsed.confidence > 0.5
    
    # Natural language look
    parsed = nlp_parser.parse_command("examine the control panel carefully")
    assert parsed.intent == CommandIntent.LOOK
    assert "panel" in parsed.target
    assert parsed.confidence > 0.5

def test_movement_commands(nlp_parser):
    """Test various forms of movement commands."""
    # Simple direction
    parsed = nlp_parser.parse_command("north")
    assert parsed.intent == CommandIntent.MOVE
    assert parsed.direction == "north"
    
    # Go with direction
    parsed = nlp_parser.parse_command("go north")
    assert parsed.intent == CommandIntent.MOVE
    assert parsed.direction == "north"
    
    # Natural language movement
    parsed = nlp_parser.parse_command("walk towards the northern door")
    assert parsed.intent == CommandIntent.MOVE
    assert "north" in parsed.direction

def test_inventory_commands(nlp_parser):
    """Test various forms of inventory commands."""
    # Simple inventory
    parsed = nlp_parser.parse_command("inventory")
    assert parsed.intent == CommandIntent.INVENTORY
    
    # Natural language inventory
    parsed = nlp_parser.parse_command("check what I'm carrying")
    assert parsed.intent == CommandIntent.INVENTORY
    
    # Abbreviated inventory
    parsed = nlp_parser.parse_command("i")
    assert parsed.intent == CommandIntent.INVENTORY

def test_take_commands(nlp_parser):
    """Test various forms of take commands."""
    # Simple take
    parsed = nlp_parser.parse_command("take key")
    assert parsed.intent == CommandIntent.TAKE
    assert parsed.target == "key"
    
    # Natural language take
    parsed = nlp_parser.parse_command("pick up the red key from the table")
    assert parsed.intent == CommandIntent.TAKE
    assert "key" in parsed.target

def test_use_commands(nlp_parser):
    """Test various forms of use commands."""
    # Simple use
    parsed = nlp_parser.parse_command("use key")
    assert parsed.intent == CommandIntent.USE
    assert parsed.target == "key"
    
    # Use with target
    parsed = nlp_parser.parse_command("use key on door")
    assert parsed.intent == CommandIntent.USE
    assert parsed.target == "key"

def test_system_commands(nlp_parser):
    """Test system commands."""
    # Save
    parsed = nlp_parser.parse_command("save")
    assert parsed.intent == CommandIntent.SAVE
    
    # Load
    parsed = nlp_parser.parse_command("load")
    assert parsed.intent == CommandIntent.LOAD
    
    # Quit
    parsed = nlp_parser.parse_command("quit")
    assert parsed.intent == CommandIntent.QUIT
    
    # Help
    parsed = nlp_parser.parse_command("help")
    assert parsed.intent == CommandIntent.HELP

def test_unknown_commands(nlp_parser):
    """Test handling of unknown or invalid commands."""
    parsed = nlp_parser.parse_command("xyzzy")
    assert parsed.intent == CommandIntent.UNKNOWN
    assert parsed.confidence == 0.0
    
    parsed = nlp_parser.parse_command("dance with the stars")
    assert parsed.intent == CommandIntent.UNKNOWN
    assert parsed.confidence == 0.0

def test_command_processing(nlp_parser):
    """Test processing of various commands."""
    # Test look command
    result, continue_game = nlp_parser.process_command("look")
    assert "You are in the ship_bridge" in result
    assert continue_game is True
    
    # Test inventory command
    result, continue_game = nlp_parser.process_command("check inventory")
    assert "Your inventory is empty" in result
    assert continue_game is True
    
    # Test quit command
    result, continue_game = nlp_parser.process_command("quit")
    assert "Goodbye" in result
    assert continue_game is False
    
    # Test unknown command
    result, continue_game = nlp_parser.process_command("xyzzy")
    assert "Try rephrasing that" in result
    assert continue_game is True

def test_natural_language_processing(nlp_parser):
    """Test more complex natural language commands."""
    # Complex look command
    parsed = nlp_parser.parse_command("take a careful look at the broken console")
    assert parsed.intent == CommandIntent.LOOK
    assert "console" in parsed.target
    
    # Complex movement command
    parsed = nlp_parser.parse_command("let's head towards the northern corridor")
    assert parsed.intent == CommandIntent.MOVE
    assert "north" in parsed.direction
    
    # Complex inventory command
    parsed = nlp_parser.parse_command("show me what items I have")
    assert parsed.intent == CommandIntent.INVENTORY
    
    # Complex interaction command
    parsed = nlp_parser.parse_command("try to use the red key to unlock the door")
    assert parsed.intent == CommandIntent.USE
    assert "key" in parsed.target 