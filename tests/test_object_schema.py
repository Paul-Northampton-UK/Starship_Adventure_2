import pytest
import yaml
from engine.schemas import Object, ObjectCategory, ObjectProperties, ObjectInteraction

def test_valid_container():
    """Test creating a valid container object"""
    container_data = {
        "object_id": "storage_box",
        "name": "Storage Box",
        "category": ObjectCategory.CONTAINER,
        "count": 1,
        "weight": 2.0,
        "size": 1.0,
        "description": "A sturdy storage box.",
        "properties": {
            "storage_capacity": 10.0,
            "can_store_liquids": False
        },
        "interaction": {
            "primary_actions": ["open", "close", "store", "retrieve"]
        }
    }
    
    container = Object(**container_data)
    assert container.object_id == "storage_box"
    assert container.category == ObjectCategory.CONTAINER
    assert container.properties.storage_capacity == 10.0
    assert "open" in container.interaction.primary_actions

def test_valid_weapon():
    """Test creating a valid weapon object"""
    weapon_data = {
        "object_id": "laser_pistol",
        "name": "Laser Pistol",
        "category": ObjectCategory.WEAPON,
        "count": 1,
        "weight": 1.5,
        "size": 0.5,
        "description": "A standard issue laser pistol.",
        "properties": {
            "damage": 25.0,
            "durability": 100,
            "range": 20.0
        },
        "interaction": {
            "primary_actions": ["fire", "reload", "inspect"]
        }
    }
    
    weapon = Object(**weapon_data)
    assert weapon.object_id == "laser_pistol"
    assert weapon.category == ObjectCategory.WEAPON
    assert weapon.properties.damage == 25.0
    assert "fire" in weapon.interaction.primary_actions

def test_valid_consumable():
    """Test creating a valid consumable object"""
    food_data = {
        "object_id": "ration_pack",
        "name": "Ration Pack",
        "category": ObjectCategory.CONSUMABLE,
        "count": 1,
        "weight": 0.5,
        "size": 0.2,
        "description": "A standard ration pack.",
        "properties": {
            "is_consumable": True,
            "is_edible": True,
            "is_food": True
        },
        "interaction": {
            "primary_actions": ["eat", "inspect"],
            "effects": ["restore_health", "satisfy_hunger"]
        }
    }
    
    food = Object(**food_data)
    assert food.object_id == "ration_pack"
    assert food.category == ObjectCategory.CONSUMABLE
    assert food.properties.is_edible
    assert "eat" in food.interaction.primary_actions

def test_invalid_object_id():
    """Test that invalid object IDs are rejected"""
    with pytest.raises(ValueError):
        Object(
            object_id="Invalid ID!",  # Contains spaces and special characters
            name="Test Object",
            category=ObjectCategory.DECORATIVE,
            count=1,
            weight=1.0,
            size=1.0,
            description="Test description"
        )

def test_invalid_properties():
    """Test that invalid properties are rejected"""
    with pytest.raises(ValueError):
        Object(
            object_id="test_object",
            name="Test Object",
            category=ObjectCategory.WEAPON,
            count=1,
            weight=1.0,
            size=1.0,
            description="Test description",
            properties=ObjectProperties(
                damage=-10.0,  # Negative damage
                storage_capacity=-5.0  # Negative capacity
            )
        )

def test_empty_name():
    """Test that empty names are rejected"""
    with pytest.raises(ValueError):
        Object(
            object_id="test_object",
            name="",  # Empty name
            category=ObjectCategory.DECORATIVE,
            count=1,
            weight=1.0,
            size=1.0,
            description="Test description"
        )

def test_load_from_yaml():
    """Test loading objects from YAML file"""
    with open("data/objects.yaml", 'r') as file:
        data = yaml.safe_load(file)
    
    # Skip the defaults section
    objects_data = data.get('objects', [])
    
    for obj_data in objects_data:
        # Convert YAML data to our schema format
        object_data = {
            "object_id": obj_data['id'],
            "name": obj_data['name'],
            "category": ObjectCategory(obj_data.get('type', 'DECORATIVE')),
            "count": 1,  # Default count
            "weight": float(obj_data.get('weight', 1.0)),
            "size": float(1.0 if obj_data.get('size') == 'small' else 
                         2.0 if obj_data.get('size') == 'medium' else 
                         3.0),  # Convert size strings to numbers
            "description": obj_data['description'],
            "power_state": obj_data.get('power_state'),
            "is_locked": obj_data.get('is_locked', False),
            "lock_type": obj_data.get('lock_type'),
            "lock_code": obj_data.get('lock_code'),
            "lock_key_id": obj_data.get('lock_key_id'),
            "storage_contents": obj_data.get('storage_contents', []),
            "synonyms": obj_data.get('synonyms', []),
            "properties": {
                "is_interactive": obj_data.get('is_interactive', True),
                "is_takeable": obj_data.get('is_portable', False),
                "is_operational": obj_data.get('is_operational', False),
                "is_storage": obj_data.get('is_storage', False),
                "is_hackable": obj_data.get('is_hackable', False),
                "is_hidden": obj_data.get('is_hidden', False),
                "is_activatable": obj_data.get('is_activatable', False),
                "is_networked": obj_data.get('is_networked', False),
                "requires_power": obj_data.get('requires_power', False),
                "is_stored": obj_data.get('is_stored', False),
                "is_transferable": obj_data.get('is_transferable', False)
            },
            "interaction": {
                "primary_actions": obj_data.get('commands', [])
            }
        }
        
        # Create object and verify it's valid
        obj = Object(**object_data)
        assert obj.object_id == obj_data['id']
        assert obj.name == obj_data['name']
        assert obj.description == obj_data['description'] 