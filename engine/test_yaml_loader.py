"""
Test module for the YAML loader.
"""

import pytest
from pathlib import Path
from .yaml_loader import YAMLLoader

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