import yaml
from engine.schemas import Room, LocationMode, DeckLevel

def load_and_validate_rooms(yaml_file):
    """Load rooms from YAML and validate them using the schema"""
    try:
        with open(yaml_file, 'r') as file:
            data = yaml.safe_load(file)
            
        # Validate each room in the YAML
        rooms = {}
        for room_id, room_data in data.items():
            try:
                # Create a Room instance to validate the data
                room = Room(**room_data)
                rooms[room_id] = room
                print(f"✓ Successfully validated room: {room.name}")
            except ValueError as e:
                print(f"✗ Error in room {room_id}: {e}")
        
        return rooms
    except Exception as e:
        print(f"Error loading YAML file: {e}")
        return None

def create_new_room():
    """Create a new room programmatically"""
    new_room_data = {
        "room_id": "engineering_bay",
        "name": "Engineering Bay",
        "room_count": 1,
        "location_mode": LocationMode.MAIN_SHIP,
        "deck_level": DeckLevel.ENGINEERING_DECK,
        "grid_reference": [2, 3],
        "grid_size": [6, 4],
        "windows_present": False,
        "backup_power": True,
        "emergency_exit": True,
        "requires_light_source": True,
        "first_visit_description": {
            "offline": "The engineering bay is completely dark.",
            "emergency": "Emergency lighting casts a dim red glow.",
            "main_power": "The engineering bay hums with power.",
            "torch_light": "Your torch illuminates the machinery."
        },
        "short_description": {
            "offline": "Dark and silent.",
            "emergency": "Dim red emergency lighting.",
            "main_power": "Fully operational.",
            "torch_light": "Lit by torchlight."
        },
        "exits": [
            {
                "direction": "north",
                "destination": "reactor_room"
            },
            {
                "direction": "east",
                "destination": "maintenance_bay"
            }
        ]
    }
    
    try:
        new_room = Room(**new_room_data)
        print("\nSuccessfully created new room:")
        print(f"Name: {new_room.name}")
        print(f"Location: {new_room.location_mode}")
        print(f"Deck: {new_room.deck_level}")
        print(f"Exits: {[exit.direction for exit in new_room.exits]}")
        return new_room
    except ValueError as e:
        print(f"Error creating new room: {e}")
        return None

if __name__ == "__main__":
    # Example 1: Validate existing rooms from YAML
    print("Validating rooms from YAML file...")
    rooms = load_and_validate_rooms("data/Starship_plan.yaml")
    
    # Example 2: Create a new room
    print("\nCreating a new room...")
    new_room = create_new_room() 