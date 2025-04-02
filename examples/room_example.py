from engine.schemas import Room, LocationMode, DeckLevel

# Example room data
bridge_data = {
    "room_id": "bridge",  # Must be lowercase with no spaces
    "name": "Bridge",     # Display name can have spaces
    "room_count": 1,      # Must be at least 1
    "location_mode": LocationMode.MAIN_SHIP,
    "deck_level": DeckLevel.BRIDGE_DECK,
    "grid_reference": [0, 0],  # Must be non-negative
    "grid_size": [5, 4],      # Must be non-negative
    "windows_present": True,
    "backup_power": True,
    "emergency_exit": True,
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
            "direction": "north",  # Must be a valid direction
            "destination": "captains_quarters"  # Must be a valid room_id
        }
    ]
}

# Create a Room instance
try:
    bridge = Room(**bridge_data)
    print("Room created successfully!")
    print(f"Room ID: {bridge.room_id}")
    print(f"Name: {bridge.name}")
    print(f"Location: {bridge.location_mode}")
    print(f"Deck: {bridge.deck_level}")
    print(f"Has windows: {bridge.windows_present}")
    print(f"Exits: {[exit.direction for exit in bridge.exits]}")
except ValueError as e:
    print(f"Error creating room: {e}") 