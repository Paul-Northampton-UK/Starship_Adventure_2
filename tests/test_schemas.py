import pytest
from engine.schemas import Room, RoomDescription, RoomExit, LocationMode, DeckLevel

def test_valid_room():
    """Test that a valid room passes validation"""
    room_data = {
        "room_id": "ship_bridge",
        "name": "Ship Bridge",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [3, 18],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "The bridge is shrouded in darkness.",
            "emergency": "Dim emergency lighting casts an eerie glow.",
            "main_power": "The bridge comes alive with brilliant lighting.",
            "torch_light": "The beam of your torch sweeps across the bridge."
        },
        "short_description": {
            "offline": "Total darkness.",
            "emergency": "Dim emergency lighting.",
            "main_power": "Fully operational.",
            "torch_light": "Flickering torchlight."
        },
        "exits": [
            {
                "direction": "up",
                "destination": "captains_door"
            }
        ]
    }
    
    room = Room(**room_data)
    assert room.room_id == "ship_bridge"
    assert room.name == "Ship Bridge"
    assert room.location_mode == LocationMode.MAIN_SHIP
    assert room.deck_level == DeckLevel.BRIDGE_DECK

def test_invalid_grid_coordinates():
    """Test that negative grid coordinates are rejected"""
    room_data = {
        "room_id": "test_room",
        "name": "Test Room",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [-1, 0],  # Invalid negative coordinate
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        }
    }
    
    with pytest.raises(ValueError):
        Room(**room_data)

def test_invalid_room_count():
    """Test that non-positive room count is rejected"""
    room_data = {
        "room_id": "test_room",
        "name": "Test Room",
        "room_count": 0,  # Invalid room count
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [0, 0],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        }
    }
    
    with pytest.raises(ValueError):
        Room(**room_data)

def test_invalid_room_id():
    """Test that invalid room IDs are rejected"""
    room_data = {
        "room_id": "Ship Bridge",  # Invalid: contains spaces and uppercase
        "name": "Test Room",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [0, 0],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        }
    }
    
    with pytest.raises(ValueError):
        Room(**room_data)

def test_invalid_exit_direction():
    """Test that invalid exit directions are rejected"""
    room_data = {
        "room_id": "test_room",
        "name": "Test Room",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [0, 0],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "exits": [
            {
                "direction": "invalid_direction",  # Invalid direction
                "destination": "test_destination"
            }
        ]
    }
    
    with pytest.raises(ValueError):
        Room(**room_data)

def test_duplicate_exit_directions():
    """Test that duplicate exit directions are rejected"""
    room_data = {
        "room_id": "test_room",
        "name": "Test Room",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [0, 0],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "exits": [
            {
                "direction": "north",
                "destination": "room1"
            },
            {
                "direction": "north",  # Duplicate direction
                "destination": "room2"
            }
        ]
    }
    
    with pytest.raises(ValueError):
        Room(**room_data)

def test_empty_room_name():
    """Test that empty room names are rejected"""
    room_data = {
        "room_id": "test_room",
        "name": "   ",  # Empty name with only whitespace
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.BRIDGE_DECK,
        "grid_reference": [0, 0],
        "grid_size": [5, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": False,
        "requires_light_source": False,
        "first_visit_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        },
        "short_description": {
            "offline": "Dark.",
            "emergency": "Dim.",
            "main_power": "Bright.",
            "torch_light": "Flickering."
        }
    }
    
    with pytest.raises(ValueError):
        Room(**room_data) 