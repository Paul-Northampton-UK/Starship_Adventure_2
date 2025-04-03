import os
import sys
import pytest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from engine.nlp_command_parser import NLPCommandParser
from engine.command_defs import CommandIntent
from engine.game_state import GameState

class TestNLPCommandParser:
    @pytest.fixture
    def parser(self):
        """Create a parser instance for testing."""
        game_state = GameState(current_room_id="test_room")
        return NLPCommandParser(game_state)

    def generate_verb_documentation(self):
        """Generate documentation of all verb categories and their test cases."""
        parser = NLPCommandParser(GameState(current_room_id="test_room"))
        
        # Create a dictionary to store all test cases
        verb_categories = {
            "INVENTORY": {
                "verbs": ["i", "inventory", "inv", "items", "cargo", "loadout"],
                "description": "Commands for viewing inventory and equipment"
            },
            "QUIT": {
                "verbs": ["q", "quit", "exit", "bye", "logout", "disconnect"],
                "description": "Commands for exiting the game"
            },
            "HELP": {
                "verbs": ["h", "help", "?", "commands", "tutorial", "manual"],
                "description": "Commands for getting help and information"
            },
            "MOVE": {
                "verbs": ["go", "walk", "run", "move", "head", "float", "drift"],
                "directions": ["north", "south", "east", "west", "up", "down", "forward", "backward"],
                "locations": ["bridge", "engineering", "cargo bay", "airlock", "medbay", "quarters"],
                "description": "Commands for movement and navigation"
            },
            "LOOK": {
                "verbs": ["look", "l", "examine", "inspect", "check", "survey"],
                "objects": ["console", "panel", "terminal", "display", "hologram", "device", "equipment", "machinery"],
                "description": "Commands for looking at surroundings and objects"
            },
            "COMMUNICATE": {
                "verbs": ["talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast"],
                "targets": ["alien", "robot", "android", "ai", "computer", "crew", "captain", "officer"],
                "complex_commands": [
                    "hail the alien ship",
                    "contact engineering",
                    "transmit distress signal",
                    "broadcast message to all stations"
                ],
                "description": "Commands for communication and interaction"
            },
            "COMBAT": {
                "verbs": ["attack", "fight", "hit", "strike", "shoot", "fire", "blast", "discharge", "engage", "neutralize"],
                "targets": ["alien", "robot", "android", "drone", "hostile", "threat", "enemy", "creature"],
                "weapons": ["phaser", "blaster", "laser", "pulse", "beam", "torpedo", "missile"],
                "description": "Commands for combat and combat-related actions"
            },
            "SEARCH": {
                "verbs": ["search", "find", "locate", "seek", "probe", "detect", "discover", "track"],
                "targets": ["console", "panel", "terminal", "device", "data", "information", "signal", "lifeform", "artifact"],
                "description": "Commands for searching and finding objects"
            },
            "MANIPULATE": {
                "verbs": ["open", "close", "lock", "unlock", "push", "pull", "turn", "press", "activate", "deactivate", "engage", "disengage"],
                "objects": ["console", "panel", "terminal", "screen", "hatch", "airlock", "gate", "valve", "circuit", "system"],
                "description": "Commands for manipulating objects and devices"
            },
            "CLIMB": {
                "verbs": ["climb", "jump", "crawl", "swim", "hover", "fly", "launch", "land"],
                "objects": ["ladder", "wall", "rope", "gap", "fence", "pit", "tunnel", "vent", "pipe", "space"],
                "description": "Commands for climbing and movement in different environments"
            },
            "SOCIAL": {
                "verbs": ["give", "show", "trade", "follow", "greet", "salute", "wave", "gesture", "signal"],
                "objects": ["phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"],
                "description": "Commands for social interaction and gestures"
            },
            "ENVIRONMENT": {
                "verbs": ["dig", "cut", "burn", "pour", "light", "extinguish", "fill", "break", "smash", "destroy", "shatter"],
                "objects": ["circuit", "panel", "console", "terminal", "system", "device", "equipment", "machinery", "power", "energy", "shield"],
                "description": "Commands for environmental interaction and modification"
            },
            "GATHER_INFO": {
                "verbs": ["read", "listen", "smell", "touch", "taste", "study", "analyze", "scan", "monitor"],
                "objects": ["data", "information", "signal", "display", "screen", "terminal", "console", "hologram", "sensor", "scanner"],
                "description": "Commands for gathering information and analyzing objects"
            },
            "EQUIP": {
                "verbs": ["equip", "wear", "remove", "unequip", "wield", "hold", "power", "charge"],
                "objects": ["phaser", "blaster", "laser", "suit", "armor", "shield", "generator", "battery", "power pack", "jetpack"],
                "description": "Commands for equipment management and usage"
            },
            "TIME": {
                "verbs": ["wait", "rest", "sleep", "pause", "meditate", "nap", "stop", "delay", "hold", "standby"],
                "description": "Commands for time-related actions and waiting"
            },
            "COMPLEX": {
                "verbs": ["combine", "craft", "build", "create", "construct", "forge", "brew", "synthesize", "fabricate", "assemble"],
                "objects": ["device", "machine", "equipment", "circuit", "component", "module", "system", "artifact", "technology"],
                "description": "Commands for complex actions like crafting and building"
            },
            "TAKE": {
                "verbs": ["take", "grab", "pick", "get", "collect", "acquire", "obtain", "retrieve", "recover"],
                "objects": ["phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"],
                "description": "Commands for picking up and collecting items"
            }
        }
        
        # Generate the documentation file
        with open("verb_categories.txt", "w") as f:
            f.write("Verb Categories Documentation\n")
            f.write("===========================\n\n")
            
            for category, data in verb_categories.items():
                f.write(f"{category}\n")
                f.write("-" * len(category) + "\n")
                f.write(f"Description: {data['description']}\n\n")
                
                if "verbs" in data:
                    f.write("Verbs:\n")
                    for verb in data["verbs"]:
                        result = parser.parse_command(verb)
                        f.write(f"  - {verb}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                if "directions" in data:
                    f.write("Directions:\n")
                    for direction in data["directions"]:
                        result = parser.parse_command(direction)
                        f.write(f"  - {direction}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n")
                        f.write(f"    Direction: {result.direction}\n\n")
                
                if "locations" in data:
                    f.write("Locations:\n")
                    for location in data["locations"]:
                        result = parser.parse_command(f"go to {location}")
                        f.write(f"  - {location}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                if "targets" in data:
                    f.write("Targets:\n")
                    for target in data["targets"]:
                        result = parser.parse_command(f"{data['verbs'][0]} {target}")
                        f.write(f"  - {target}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                if "objects" in data:
                    f.write("Objects:\n")
                    for obj in data["objects"]:
                        result = parser.parse_command(f"{data['verbs'][0]} {obj}")
                        f.write(f"  - {obj}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                if "weapons" in data:
                    f.write("Weapons:\n")
                    for weapon in data["weapons"]:
                        result = parser.parse_command(f"attack alien with {weapon}")
                        f.write(f"  - {weapon}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                if "complex_commands" in data:
                    f.write("Complex Commands:\n")
                    for command in data["complex_commands"]:
                        result = parser.parse_command(command)
                        f.write(f"  - {command}\n")
                        f.write(f"    Action: {result.action}\n")
                        f.write(f"    Target: {result.target}\n")
                        f.write(f"    Intent: {result.intent}\n\n")
                
                f.write("\n")

    def test_generate_documentation(self):
        """Test the documentation generation."""
        self.generate_verb_documentation()
        assert os.path.exists("verb_categories.txt"), "Documentation file was not created"

    def test_single_letter_commands(self, parser):
        """Test single letter commands."""
        commands = ["i", "inventory", "inv", "items", "cargo", "loadout"]
        for command in commands:
            result = parser.parse_command(command)
            assert result.intent == CommandIntent.INVENTORY

        commands = ["q", "quit", "exit", "bye", "logout", "disconnect"]
        for command in commands:
            result = parser.parse_command(command)
            assert result.intent == CommandIntent.QUIT

        commands = ["h", "help", "?", "commands", "tutorial", "manual"]
        for command in commands:
            result = parser.parse_command(command)
            assert result.intent == CommandIntent.HELP

    def test_direction_commands(self, parser):
        """Test direction commands."""
        directions = ["north", "south", "east", "west", "up", "down", "forward", "backward"]
        for direction in directions:
            result = parser.parse_command(direction)
            assert result.intent == CommandIntent.MOVE
            assert result.direction == direction

        verbs = ["go", "walk", "run", "move", "head", "float", "drift"]
        for verb in verbs:
            result = parser.parse_command(f"{verb} north")
            assert result.intent == CommandIntent.MOVE
            assert result.direction == "north"

        locations = ["bridge", "engineering", "cargo bay", "airlock", "medbay", "quarters"]
        for location in locations:
            result = parser.parse_command(f"go to {location}")
            assert result.intent == CommandIntent.MOVE
            assert location in result.target

    def test_look_commands(self, parser):
        """Test look commands."""
        commands = ["look", "l", "examine", "inspect", "check", "survey"]
        for command in commands:
            result = parser.parse_command(command)
            assert result.intent == CommandIntent.LOOK

        objects = ["console", "panel", "terminal", "display", "hologram", "device", "equipment", "machinery"]
        for obj in objects:
            result = parser.parse_command(f"look at {obj}")
            assert result.intent == CommandIntent.LOOK
            assert obj in result.target

    def test_communication_commands(self, parser):
        """Test communication commands."""
        verbs = ["talk", "speak", "chat", "converse", "contact", "hail", "transmit", "broadcast"]
        targets = ["alien", "robot", "android", "ai", "computer", "crew", "captain", "officer"]
        
        for verb in verbs:
            for target in targets:
                result = parser.parse_command(f"{verb} to {target}")
                assert result.intent == CommandIntent.COMMUNICATE
                assert target in result.target

        commands = [
            "hail the alien ship",
            "contact engineering",
            "transmit distress signal",
            "broadcast message to all stations"
        ]
        for command in commands:
            result = parser.parse_command(command)
            assert result.intent == CommandIntent.COMMUNICATE

    def test_combat_commands(self, parser):
        """Test combat commands."""
        verbs = ["attack", "fight", "hit", "strike", "shoot", "fire", "blast", "discharge", "engage", "neutralize"]
        targets = ["alien", "robot", "android", "drone", "hostile", "threat", "enemy", "creature"]
        
        for verb in verbs:
            for target in targets:
                result = parser.parse_command(f"{verb} {target}")
                assert result.intent == CommandIntent.COMBAT
                assert target in result.target

        weapons = ["phaser", "blaster", "laser", "pulse", "beam", "torpedo", "missile"]
        for weapon in weapons:
            result = parser.parse_command(f"attack alien with {weapon}")
            assert result.intent == CommandIntent.COMBAT
            assert "alien" in result.target

    def test_search_commands(self, parser):
        """Test search commands."""
        verbs = ["search", "find", "locate", "seek", "probe", "detect", "discover", "track"]
        targets = ["console", "panel", "terminal", "device", "data", "information", "signal", "lifeform", "artifact"]
        
        for verb in verbs:
            for target in targets:
                result = parser.parse_command(f"{verb} for {target}")
                assert result.intent == CommandIntent.SEARCH
                assert target in result.target

    def test_manipulation_commands(self, parser):
        """Test manipulation commands."""
        verbs = ["open", "close", "lock", "unlock", "push", "pull", "turn", "press", "activate", "deactivate", "engage", "disengage"]
        objects = ["console", "panel", "terminal", "screen", "hatch", "airlock", "gate", "valve", "circuit", "system"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.MANIPULATE
                assert obj in result.target

    def test_climbing_commands(self, parser):
        """Test climbing commands."""
        verbs = ["climb", "jump", "crawl", "swim", "hover", "fly", "launch", "land"]
        objects = ["ladder", "wall", "rope", "gap", "fence", "pit", "tunnel", "vent", "pipe", "space"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.CLIMB
                assert obj in result.target

    def test_social_commands(self, parser):
        """Test social commands."""
        verbs = ["give", "show", "trade", "follow", "greet", "salute", "wave", "gesture", "signal"]
        objects = ["phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.SOCIAL
                assert obj in result.target

    def test_environment_commands(self, parser):
        """Test environment commands."""
        verbs = ["dig", "cut", "burn", "pour", "light", "extinguish", "fill", "break", "smash", "destroy", "shatter"]
        objects = ["circuit", "panel", "console", "terminal", "system", "device", "equipment", "machinery", "power", "energy", "shield"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.ENVIRONMENT
                assert obj in result.target

    def test_gather_info_commands(self, parser):
        """Test information gathering commands."""
        verbs = ["read", "listen", "smell", "touch", "taste", "study", "analyze", "scan", "monitor"]
        objects = ["data", "information", "signal", "display", "screen", "terminal", "console", "hologram", "sensor", "scanner"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.GATHER_INFO
                assert obj in result.target

    def test_equip_commands(self, parser):
        """Test equipment commands."""
        verbs = ["equip", "wear", "remove", "unequip", "wield", "hold", "power", "charge"]
        objects = ["phaser", "blaster", "laser", "suit", "armor", "shield", "generator", "battery", "power pack", "jetpack"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.EQUIP
                assert obj in result.target

    def test_time_commands(self, parser):
        """Test time commands."""
        verbs = ["wait", "rest", "sleep", "pause", "meditate", "nap", "stop", "delay", "hold", "standby"]
        for verb in verbs:
            result = parser.parse_command(verb)
            assert result.intent == CommandIntent.TIME

    def test_complex_commands(self, parser):
        """Test complex commands."""
        verbs = ["combine", "craft", "build", "create", "construct", "forge", "brew", "synthesize", "fabricate", "assemble"]
        objects = ["device", "machine", "equipment", "circuit", "component", "module", "system", "artifact", "technology"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.COMPLEX
                assert obj in result.target

    def test_take_commands(self, parser):
        """Test take commands."""
        verbs = ["take", "grab", "pick", "get", "collect", "acquire", "obtain", "retrieve", "recover"]
        objects = ["phaser", "blaster", "laser", "tool", "device", "data pad", "access card", "credits", "artifact"]
        
        for verb in verbs:
            for obj in objects:
                result = parser.parse_command(f"{verb} {obj}")
                assert result.intent == CommandIntent.TAKE
                assert obj in result.target

class TestInteractiveParser:
    """Test the interactive command parser with predefined commands."""
    
    def test_interactive_parser(self):
        """Test the command parser with a variety of predefined commands."""
        parser = NLPCommandParser(GameState(current_room_id="bridge"))
        
        # Test cases with expected results
        test_cases = [
            {
                "command": "look",
                "expected_intent": CommandIntent.LOOK,
                "expected_action": "look",
                "expected_target": "",
                "expected_direction": None
            },
            {
                "command": "go to engine room",
                "expected_intent": CommandIntent.MOVE,
                "expected_action": "go",
                "expected_target": "to engine room",
                "expected_direction": None
            },
            {
                "command": "take sword",
                "expected_intent": CommandIntent.TAKE,
                "expected_action": "take",
                "expected_target": "sword",
                "expected_direction": None
            },
            {
                "command": "talk to captain",
                "expected_intent": CommandIntent.COMMUNICATE,
                "expected_action": "talk",
                "expected_target": "captain",
                "expected_direction": None
            },
            {
                "command": "north",
                "expected_intent": CommandIntent.MOVE,
                "expected_action": "move",
                "expected_target": "",
                "expected_direction": "north"
            }
        ]
        
        # Run test cases
        for test_case in test_cases:
            result = parser.parse_command(test_case["command"])
            
            # Assert each part of the result matches expectations
            assert result.intent == test_case["expected_intent"], \
                f"Command '{test_case['command']}' - Expected intent {test_case['expected_intent']}, got {result.intent}"
            assert result.action == test_case["expected_action"], \
                f"Command '{test_case['command']}' - Expected action {test_case['expected_action']}, got {result.action}"
            assert result.target == test_case["expected_target"], \
                f"Command '{test_case['command']}' - Expected target {test_case['expected_target']}, got {result.target}"
            assert result.direction == test_case["expected_direction"], \
                f"Command '{test_case['command']}' - Expected direction {test_case['expected_direction']}, got {result.direction}"
            assert result.confidence > 0, \
                f"Command '{test_case['command']}' - Expected confidence > 0, got {result.confidence}"

if __name__ == "__main__":
    pytest.main([__file__]) 