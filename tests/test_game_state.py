import pytest
from engine.game_state import GameState, PowerState
import json
import os
from datetime import datetime, timedelta

@pytest.fixture
def game_state():
    """Create a fresh GameState instance for each test."""
    return GameState(current_room_id="ship_bridge")

def test_initial_state(game_state):
    """Test the initial state of a new game."""
    assert game_state.current_room_id == "ship_bridge"
    assert game_state.current_area_id is None
    assert game_state.power_state == PowerState.OFFLINE
    assert len(game_state.inventory) == 0
    assert len(game_state.visited_rooms) == 0
    assert len(game_state.visited_areas) == 0
    assert len(game_state.game_flags) == 0

def test_visit_room(game_state):
    """Test visiting a room."""
    game_state.visit_room("corridor")
    assert game_state.has_visited_room("corridor")
    assert not game_state.has_visited_room("other_room")

def test_visit_area(game_state):
    """Test visiting an area."""
    game_state.visit_area("navigation_station")
    assert game_state.has_visited_area("navigation_station")
    assert not game_state.has_visited_area("other_area")

def test_inventory_management(game_state):
    """Test adding and removing items from inventory."""
    # Add item
    game_state.add_to_inventory("torch")
    assert game_state.has_object("torch")
    assert len(game_state.inventory) == 1
    
    # Try to add same item again
    game_state.add_to_inventory("torch")
    assert len(game_state.inventory) == 1
    
    # Remove item
    game_state.remove_from_inventory("torch")
    assert not game_state.has_object("torch")
    assert len(game_state.inventory) == 0

def test_power_state_management(game_state):
    """Test changing power states."""
    assert game_state.power_state == PowerState.OFFLINE
    
    game_state.set_power_state(PowerState.EMERGENCY)
    assert game_state.power_state == PowerState.EMERGENCY
    
    game_state.set_power_state(PowerState.MAIN_POWER)
    assert game_state.power_state == PowerState.MAIN_POWER

def test_game_flags(game_state):
    """Test setting and getting game flags."""
    # Set flag
    game_state.set_game_flag("puzzle_solved")
    assert game_state.get_game_flag("puzzle_solved")
    
    # Get non-existent flag
    assert not game_state.get_game_flag("non_existent_flag")
    
    # Set flag to False
    game_state.set_game_flag("puzzle_solved", False)
    assert not game_state.get_game_flag("puzzle_solved")

def test_movement(game_state):
    """Test moving between rooms and areas."""
    # Move to new room
    game_state.move_to_room("corridor")
    assert game_state.current_room_id == "corridor"
    assert game_state.current_area_id is None
    assert game_state.has_visited_room("corridor")
    
    # Move to area in current room
    game_state.move_to_area("navigation_station")
    assert game_state.current_area_id == "navigation_station"
    assert game_state.has_visited_area("navigation_station")
    
    # Move to another room (should clear current area)
    game_state.move_to_room("ship_bridge")
    assert game_state.current_room_id == "ship_bridge"
    assert game_state.current_area_id is None

def test_get_current_location(game_state):
    """Test getting current location."""
    room_id, area_id = game_state.get_current_location()
    assert room_id == "ship_bridge"
    assert area_id is None
    
    game_state.move_to_area("navigation_station")
    room_id, area_id = game_state.get_current_location()
    assert room_id == "ship_bridge"
    assert area_id == "navigation_station"

def test_player_status_management(game_state):
    """Test player status updates and limits."""
    # Test initial status
    status = game_state.get_player_status()
    assert status['health'] == 100
    assert status['energy'] == 100
    assert status['oxygen'] == 100
    assert status['radiation'] == 0
    
    # Test status updates
    game_state.update_player_status(health_change=-20, energy_change=-30)
    status = game_state.get_player_status()
    assert status['health'] == 80
    assert status['energy'] == 70
    
    # Test status limits
    game_state.update_player_status(health_change=50)  # Try to exceed max
    status = game_state.get_player_status()
    assert status['health'] == 100  # Should be capped at max
    
    game_state.update_player_status(health_change=-150)  # Try to go below 0
    status = game_state.get_player_status()
    assert status['health'] == 0  # Should be capped at 0

def test_game_time_management(game_state):
    """Test game time advancement and its effects."""
    initial_time = game_state.game_time
    
    # Test time advancement
    game_state.advance_game_time(60)  # Advance 1 hour
    assert game_state.game_time == initial_time + timedelta(minutes=60)
    
    # Test status changes from time
    initial_energy = game_state.player_status.energy
    initial_oxygen = game_state.player_status.oxygen
    
    game_state.advance_game_time(120)  # Advance 2 hours
    assert game_state.player_status.energy < initial_energy  # Should lose energy
    assert game_state.player_status.oxygen < initial_oxygen  # Should lose oxygen

def test_object_state_management(game_state):
    """Test object state tracking."""
    # Test setting object state
    game_state.set_object_state("door_1", {"locked": True, "position": "closed"})
    assert game_state.is_object_interacted_with("door_1")
    
    # Test getting object state
    state = game_state.get_object_state("door_1")
    assert state["locked"] is True
    assert state["position"] == "closed"
    
    # Test non-existent object
    assert game_state.get_object_state("non_existent") is None
    assert not game_state.is_object_interacted_with("non_existent")

def test_save_and_load_game(game_state, tmp_path):
    """Test saving and loading game state."""
    # Set up some game state
    game_state.move_to_room("corridor")
    game_state.add_to_inventory("torch")
    game_state.set_game_flag("puzzle_solved")
    game_state.update_player_status(health_change=-20)
    game_state.set_object_state("door_1", {"locked": True})
    
    # Save game
    save_file = tmp_path / "test_save.json"
    game_state.save_game(str(save_file))
    
    # Load game
    loaded_state = GameState.load_game(str(save_file))
    
    # Verify loaded state matches original
    assert loaded_state.current_room_id == "corridor"
    assert "torch" in loaded_state.inventory
    assert loaded_state.get_game_flag("puzzle_solved")
    assert loaded_state.player_status.health == 80
    assert loaded_state.get_object_state("door_1")["locked"] is True

def test_player_alive_status(game_state):
    """Test player alive status checks."""
    assert game_state.is_player_alive()  # Should be alive initially
    
    # Test death conditions
    game_state.update_player_status(health_change=-100)  # Health to 0
    assert not game_state.is_player_alive()
    
    game_state.update_player_status(health_change=100)  # Restore health
    game_state.update_player_status(oxygen_change=-100)  # Oxygen to 0
    assert not game_state.is_player_alive()
    
    game_state.update_player_status(oxygen_change=100)  # Restore oxygen
    game_state.update_player_status(radiation_change=100)  # Max radiation
    assert not game_state.is_player_alive() 