"""
Test module for the YAML loader.
"""

import pytest
from pathlib import Path
from engine.yaml_loader import YAMLLoader

def test_yaml_loader_initialization():
    """Test YAML loader initialization."""
    loader = YAMLLoader()
    assert loader.data_dir == Path("data")
    assert loader.data_dir.exists()

def test_load_rooms():
    """Test loading room data."""
    loader = YAMLLoader()
    data = loader.load_file("rooms.yaml")
    
    # Check basic structure
    assert "rooms" in data
    assert len(data["rooms"]) > 0
    
    # Check first room
    bridge = data["rooms"][0]
    assert bridge["room_id"] == "ship_bridge"
    assert bridge["name"] == "Ship Bridge"
    assert "first_visit_description" in bridge
    assert "exits" in bridge
    assert "areas" in bridge
    
    # Validate room data
    assert loader.validate_room_data(bridge)

def test_load_objects():
    """Test loading object data."""
    loader = YAMLLoader()
    data = loader.load_file("objects.yaml")
    
    # Check basic structure
    assert "objects" in data
    assert len(data["objects"]) > 0
    
    # Check first object
    chair = data["objects"][0]
    assert chair["id"] == "captain_chair"
    assert chair["name"] == "Captain's Chair"
    assert "description" in chair
    assert "type" in chair
    
    # Validate object data
    assert loader.validate_object_data(chair)

def test_invalid_file():
    """Test handling of invalid files."""
    loader = YAMLLoader()
    
    # Test non-existent file
    with pytest.raises(FileNotFoundError):
        loader.load_file("nonexistent.yaml")
    
    # Test invalid YAML
    invalid_yaml = Path("data/invalid.yaml")
    invalid_yaml.write_text("invalid: yaml: content: -")
    
    with pytest.raises(Exception):
        loader.load_file("invalid.yaml")
    
    invalid_yaml.unlink()  # Clean up test file 

def test_room_validation_failures():
    """Test room validation with invalid data."""
    loader = YAMLLoader()
    
    # Missing required fields
    invalid_room = {
        "name": "Invalid Room"  # Missing room_id and other required fields
    }
    with pytest.raises(ValueError, match="Missing required field"):
        loader.validate_room_data(invalid_room)
    
    # Invalid exit format
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "A test room in offline state",
            "emergency": "A test room in emergency state",
            "main_power": "A test room in main power state",
            "torch_light": "A test room in torch light state"
        },
        "exits": "not_a_list",  # Should be a list
        "areas": []
    }
    with pytest.raises(ValueError, match="Exits must be a list"):
        loader.validate_room_data(invalid_room)

def test_object_validation_failures():
    """Test object validation with invalid data."""
    loader = YAMLLoader()
    
    # Missing required fields
    invalid_object = {
        "name": "Invalid Object"  # Missing id and other required fields
    }
    with pytest.raises(ValueError, match="Missing required field"):
        loader.validate_object_data(invalid_object)
    
    # Invalid type values
    invalid_object = {
        "id": "test_obj",
        "name": "Test Object",
        "description": "A test object",
        "type": "invalid_type",  # Should be one of the valid types
        "is_portable": "not_a_boolean",  # Should be boolean
        "is_interactive": True,
        "weight": "not_a_number",  # Should be number
        "size": "medium"
    }
    with pytest.raises(ValueError):
        loader.validate_object_data(invalid_object)

def test_nested_structures():
    """Test loading and validation of nested room/object structures."""
    loader = YAMLLoader()
    
    # Create a test YAML file with nested structures
    test_yaml = Path("data/test_nested.yaml")
    test_yaml.write_text("""
rooms:
  - id: nested_room
    name: Nested Room
    description: A room with nested objects
    exits:
      north:
        room_id: corridor
        requires_key: true
        key_id: master_key
    objects:
      - id: nested_obj
        name: Nested Object
        description: An object with nested properties
        properties:
          power_level: 100
          status: active
    accessible: true
""")
    
    try:
        data = loader.load_file("test_nested.yaml")
        room = data["rooms"][0]
        
        # Verify nested structures
        assert "exits" in room
        assert "north" in room["exits"]
        assert room["exits"]["north"]["room_id"] == "corridor"
        assert room["exits"]["north"]["requires_key"]
        assert room["exits"]["north"]["key_id"] == "master_key"
        
        assert "objects" in room
        assert len(room["objects"]) > 0
        assert "properties" in room["objects"][0]
        assert room["objects"][0]["properties"]["power_level"] == 100
        assert room["objects"][0]["properties"]["status"] == "active"
    finally:
        test_yaml.unlink()  # Clean up test file

def test_data_type_validation():
    """Test validation of data types in room and object fields."""
    loader = YAMLLoader()
    
    # Test room with invalid data types
    invalid_room = {
        "room_id": 123,  # Should be string
        "name": ["Not", "A", "String"],  # Should be string
        "first_visit_description": "not_a_dict",  # Should be a dictionary
        "exits": {},  # Should be a list
        "areas": "not_a_list"  # Should be list
    }
    with pytest.raises(ValueError, match="Room id must be a string"):
        loader.validate_room_data(invalid_room)
    
    # Test object with invalid data types
    invalid_object = {
        "id": "valid_id",
        "name": "Valid Name",
        "description": 42,  # Should be string
        "type": ["not", "a", "string"],  # Should be string
        "is_portable": 1,  # Should be boolean
        "is_interactive": "not_a_boolean",  # Should be boolean
        "weight": "not_a_number",  # Should be number
        "size": 42  # Should be string
    }
    with pytest.raises(ValueError, match="Object description must be a string"):
        loader.validate_object_data(invalid_object)

def test_power_state_validation():
    """Test validation of power states in room descriptions."""
    loader = YAMLLoader()
    
    # Missing power states
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power"
            # Missing main_power and torch_light
        },
        "exits": [],
        "areas": []
    }
    with pytest.raises(ValueError, match="Missing required power state"):
        loader.validate_room_data(invalid_room)
    
    # Invalid power state
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power",
            "main_power": "Room has main power",
            "torch_light": "Room in torch light",
            "invalid_state": "Invalid power state"  # Extra invalid state
        },
        "exits": [],
        "areas": []
    }
    with pytest.raises(ValueError, match="Invalid power state"):
        loader.validate_room_data(invalid_room)

def test_area_validation():
    """Test validation of areas within rooms."""
    loader = YAMLLoader()
    
    # Invalid area structure
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power",
            "main_power": "Room has main power",
            "torch_light": "Room in torch light"
        },
        "exits": [],
        "areas": [
            {
                # Missing required area fields
                "name": "Test Area"
            }
        ]
    }
    with pytest.raises(ValueError, match="Missing required field 'area_id' in area data"):
        loader.validate_room_data(invalid_room)
    
    # Invalid area command aliases
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power",
            "main_power": "Room has main power",
            "torch_light": "Room in torch light"
        },
        "exits": [],
        "areas": [
            {
                "area_id": "test_area",
                "name": "Test Area",
                "command_aliases": "not_a_list",  # Should be a list
                "area_count": 1,
                "first_visit_description": {
                    "offline": "Area is offline",
                    "emergency": "Area is in emergency power",
                    "main_power": "Area has main power",
                    "torch_light": "Area in torch light"
                }
            }
        ]
    }
    with pytest.raises(ValueError, match="Area command aliases must be a list"):
        loader.validate_room_data(invalid_room)

def test_exit_validation():
    """Test validation of room exits."""
    loader = YAMLLoader()
    
    # Invalid exit structure
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power",
            "main_power": "Room has main power",
            "torch_light": "Room in torch light"
        },
        "exits": [
            {
                # Missing required exit fields
                "direction": "north"
            }
        ],
        "areas": []
    }
    with pytest.raises(ValueError, match="Missing required field 'destination' in exit data"):
        loader.validate_room_data(invalid_room)
    
    # Invalid dynamic description
    invalid_room = {
        "room_id": "test_room",
        "name": "Test Room",
        "first_visit_description": {
            "offline": "Room is offline",
            "emergency": "Room is in emergency power",
            "main_power": "Room has main power",
            "torch_light": "Room in torch light"
        },
        "exits": [
            {
                "direction": "north",
                "destination": "corridor",
                "dynamic_description": "not_a_dict"  # Should be a dictionary
            }
        ],
        "areas": []
    }
    with pytest.raises(ValueError, match="Exit dynamic description must be a dictionary"):
        loader.validate_room_data(invalid_room) 