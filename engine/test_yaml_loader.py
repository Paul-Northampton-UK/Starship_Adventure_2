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
    assert bridge["id"] == "bridge"
    assert bridge["name"] == "Bridge"
    assert "description" in bridge
    assert "exits" in bridge
    assert "objects" in bridge
    
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
        "name": "Invalid Room"  # Missing id and other required fields
    }
    with pytest.raises(ValueError, match="Missing required field"):
        loader.validate_room_data(invalid_room)
    
    # Invalid exit format
    invalid_room = {
        "id": "test_room",
        "name": "Test Room",
        "description": "A test room",
        "exits": "not_a_dict",  # Should be a dictionary
        "objects": [],
        "accessible": True
    }
    with pytest.raises(ValueError, match="Exits must be a dictionary"):
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
        "id": 123,  # Should be string
        "name": ["Not", "A", "String"],  # Should be string
        "description": "Valid description",
        "exits": {},
        "objects": "not_a_list",  # Should be list
        "accessible": "not_a_boolean"  # Should be boolean
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