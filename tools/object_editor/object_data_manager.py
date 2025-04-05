# Handles loading, saving, and managing object and room YAML data.
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError

class ObjectDataManager:
    """Manages loading, accessing, and saving object and room data from YAML files."""

    def __init__(self, data_dir: Path = Path("../../data")): # Assume running from tools/object_editor
        """
        Initializes the manager and loads data.

        Args:
            data_dir: The path to the directory containing rooms.yaml and objects.yaml.
                      Defaults assuming the script runs from tools/object_editor.
        """
        self.data_dir = data_dir
        self.objects_file = self.data_dir / "objects.yaml"
        self.rooms_file = self.data_dir / "rooms.yaml"

        self.yaml = YAML()
        self.yaml.preserve_quotes = True # Keep formatting nice
        # self.yaml.indent(mapping=2, sequence=4, offset=2) # Optional: finer indent control

        self.objects_data: Optional[List[Dict[str, Any]]] = None
        self.rooms_data: Optional[Dict[str, Any]] = None # Rooms are usually dicts {id: data}

        self._load_data()

    def _load_data(self):
        """Loads both objects and rooms data, expecting lists under top keys."""
        raw_objects = self._load_yaml_file(self.objects_file)
        raw_rooms = self._load_yaml_file(self.rooms_file)

        # Expecting structure like {'objects': [{...}, {...}]} or {'rooms': [{...}, {...}]}
        self.objects_data = raw_objects.get('objects', []) if isinstance(raw_objects, dict) else raw_objects if isinstance(raw_objects, list) else []
        # Rooms are more complex, yaml has rooms as list but schema/code treats as dict
        # Let's convert the list from yaml into a dict for internal use, matching game_state
        rooms_list = raw_rooms.get('rooms', []) if isinstance(raw_rooms, dict) else raw_rooms if isinstance(raw_rooms, list) else []
        self.rooms_data = {room.get('room_id'): room for room in rooms_list if isinstance(room, dict) and 'room_id' in room}

        if not self.objects_data:
            logging.warning(f"No objects found or loaded from {self.objects_file}. Check format (expected list under 'objects:' key).")
        if not self.rooms_data:
             logging.warning(f"No rooms found or loaded from {self.rooms_file}. Check format (expected list under 'rooms:' key).")

        logging.info(f"Loaded {len(self.objects_data)} objects and {len(self.rooms_data)} rooms.")

    def _load_yaml_file(self, file_path: Path) -> Optional[Any]:
        """Loads a single YAML file using ruamel.yaml."""
        try:
            if not file_path.is_file():
                logging.error(f"Data file not found: {file_path}")
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                data = self.yaml.load(f)
                logging.info(f"Successfully loaded YAML file: {file_path}")
                return data
        except (ParserError, ScannerError) as e:
            logging.error(f"Error parsing YAML file {file_path}: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred loading {file_path}: {e}")
            return None

    # --- Methods for accessing data will go here ---
    def get_object_ids(self) -> List[str]:
        """Returns a sorted list of all object IDs from the loaded list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logging.warning("get_object_ids: No objects_data list found.")
            return []
        ids = []
        for i, obj in enumerate(self.objects_data):
            if isinstance(obj, dict) and 'id' in obj:
                obj_id = obj.get('id', '')
                if obj_id:
                    ids.append(obj_id)
                else:
                    logging.warning(f"get_object_ids: Found empty ID in object at index {i}.")
            else:
                logging.warning(f"get_object_ids: Item at index {i} is not a dict or lacks 'id' key.")
        
        sorted_ids = sorted(ids)
        logging.info(f"get_object_ids: Returning IDs: {sorted_ids}") # DEBUG LOG
        return sorted_ids

    def get_room_ids(self) -> List[str]:
        """Returns a sorted list of all room IDs from the processed dictionary."""
        if not self.rooms_data or not isinstance(self.rooms_data, dict):
            return []
        # Now reads keys from the dictionary created in _load_data
        return sorted(list(self.rooms_data.keys()))

    def get_object_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
         """Retrieves the data for a specific object by its ID."""
         if not self.objects_data or not isinstance(self.objects_data, list): # Added type check
             logging.warning("get_object_by_id: objects_data is not a list or is empty.")
             return None
         if not object_id: # Prevent comparing against None/empty string
              logging.warning("get_object_by_id: received empty object_id to search for.")
              return None

         search_id = object_id.strip() # Strip whitespace from the ID we are searching for

         for i, obj in enumerate(self.objects_data):
             if isinstance(obj, dict):
                 obj_id_val = obj.get('id')
                 if isinstance(obj_id_val, str):
                     # --- Compare stripped versions ---
                     if obj_id_val.strip() == search_id:
                         logging.debug(f"get_object_by_id: Match found for '{search_id}' at index {i}.")
                         return obj
                 else:
                     logging.warning(f"get_object_by_id: Object at index {i} has non-string ID: {obj_id_val}")
             else:
                  logging.warning(f"get_object_by_id: Item at index {i} is not a dictionary.")

         logging.warning(f"get_object_by_id: No match found for '{search_id}'.")
         return None

    def get_area_ids_for_room(self, room_id: str) -> List[str]:
        """Returns a sorted list of area IDs for a given room ID."""
        if not self.rooms_data or room_id not in self.rooms_data:
            return []
        room_data = self.rooms_data.get(room_id, {})
        areas_list = room_data.get("areas", [])
        if not isinstance(areas_list, list):
            logging.warning(f"Areas data for room '{room_id}' is not a list.")
            return []

        area_ids = [
            area.get("area_id", "")
            for area in areas_list
            if isinstance(area, dict) and "area_id" in area
        ]
        return sorted([aid for aid in area_ids if aid])

    def find_object_location(self, object_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        Finds the room_id and area_id where an object is located.

        Returns:
            A tuple (room_id, area_id). area_id is None if the object is in the room
            but not within a specific area, or if areas aren't defined properly.
            Both are None if the object is not found in any room's/area's objects_present list.
        """
        logging.debug(f"find_object_location: Entered for object_id='{object_id}'. Checking self.rooms_data (len={len(self.rooms_data) if self.rooms_data else 0}). Is dict? {isinstance(self.rooms_data, dict)}")

        if not self.rooms_data or not object_id:
            logging.debug("find_object_location: Exiting early because self.rooms_data is empty or object_id is missing.") # Log the early exit
            return None, None

        search_id = object_id.strip()

        for room_id, room_data in self.rooms_data.items():
            if not isinstance(room_data, dict): continue

            # Check room-level objects_present
            room_objects = room_data.get("objects_present", [])
            if isinstance(room_objects, list):
                # --- Log the raw list content ---
                logging.debug(f"Room '{room_id}' room_objects: {room_objects}")
                for obj_dict in room_objects:
                    if isinstance(obj_dict, dict):
                         obj_id_val = obj_dict.get('id', '')
                         # --- Log extracted ID and comparison ---
                         logging.debug(f"  Checking room obj: ID='{obj_id_val}' (Type: {type(obj_id_val)}), Comparing '{obj_id_val.strip() if isinstance(obj_id_val, str) else obj_id_val}' == '{search_id}'")
                         if isinstance(obj_id_val, str) and obj_id_val.strip() == search_id:
                            logging.debug(f"Object '{search_id}' found directly in room '{room_id}'.")
                            return room_id, None
                    else:
                        # Log items that are not dictionaries
                        logging.debug(f"  Skipping non-dict room obj: {obj_dict} (Type: {type(obj_dict)}) ")


            # Check area-level objects_present
            areas_list = room_data.get("areas", [])
            if isinstance(areas_list, list):
                for area_data in areas_list:
                    if not isinstance(area_data, dict): continue
                    area_id = area_data.get("area_id")
                    area_objects = area_data.get("objects_present", [])
                    if isinstance(area_objects, list):
                         # --- Log the raw list content ---
                         logging.debug(f"Area '{area_id}' in room '{room_id}' area_objects: {area_objects}")
                         for obj_dict in area_objects:
                             if isinstance(obj_dict, dict):
                                 obj_id_val = obj_dict.get('id', '')
                                 # --- Log extracted ID and comparison ---
                                 logging.debug(f"    Checking area obj: ID='{obj_id_val}' (Type: {type(obj_id_val)}), Comparing '{obj_id_val.strip() if isinstance(obj_id_val, str) else obj_id_val}' == '{search_id}'")
                                 if isinstance(obj_id_val, str) and obj_id_val.strip() == search_id:
                                     logging.debug(f"Object '{search_id}' found in area '{area_id}' of room '{room_id}'.")
                                     return room_id, area_id
                             else:
                                 # Log items that are not dictionaries
                                 logging.debug(f"    Skipping non-dict area obj: {obj_dict} (Type: {type(obj_dict)}) ")

        logging.debug(f"Object '{search_id}' not found in any room or area 'objects_present' list.")
        return None, None

    # --- Methods for modifying and saving data will go here ---
    def _save_yaml_file(self, file_path: Path, data: Any) -> bool:
        """Saves data to a YAML file using ruamel.yaml, preserving formatting."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)
            logging.info(f"Successfully saved YAML file: {file_path}")
            return True
        except Exception as e:
            logging.exception(f"An error occurred saving {file_path}")
            return False

    def add_object(self, new_object_data: dict) -> bool:
        """Adds a new object dictionary to the internal list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logging.error("Cannot add object: objects_data not loaded or not a list.")
            return False
        if not isinstance(new_object_data, dict) or 'id' not in new_object_data:
             logging.error("Cannot add object: Invalid data provided.")
             return False
        # Check for duplicate ID just in case
        if self.get_object_by_id(new_object_data['id']):
             logging.error(f"Cannot add object: ID '{new_object_data['id']}' already exists.")
             return False

        self.objects_data.append(new_object_data)
        logging.info(f"Added new object '{new_object_data['id']}' to internal list.")
        return True

    def update_object(self, object_id: str, updated_object_data: dict) -> bool:
        """Updates an existing object dictionary in the internal list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logging.error("Cannot update object: objects_data not loaded or not a list.")
            return False
        if not object_id:
             logging.error("Cannot update object: No object_id specified.")
             return False

        for i, obj in enumerate(self.objects_data):
            if isinstance(obj, dict) and obj.get('id', '').strip() == object_id.strip():
                # Replace the old dict with the new one, preserving list order
                self.objects_data[i] = updated_object_data
                # Ensure the ID in the new data matches (should already, but good practice)
                self.objects_data[i]['id'] = object_id.strip()
                logging.info(f"Updated object '{object_id}' in internal list.")
                return True

        logging.error(f"Cannot update object: ID '{object_id}' not found.")
        return False

    def _update_object_location_in_rooms(self, object_id: str, new_room_id: Optional[str], new_area_id: Optional[str]) -> bool:
        """Internal helper to remove object from old location and add to new location in rooms_data."""
        if not self.rooms_data: return False
        if not object_id: return False

        object_id_to_save = {'id': object_id} # Store as dict in rooms.yaml

        # 1. Find and remove from old location(s)
        for room_id, room_data in self.rooms_data.items():
            if not isinstance(room_data, dict): continue
            # Remove from room level
            if "objects_present" in room_data and isinstance(room_data["objects_present"], list):
                room_data["objects_present"][:] = [obj for obj in room_data["objects_present"] if not (isinstance(obj, dict) and obj.get('id') == object_id)]
            # Remove from area level
            if "areas" in room_data and isinstance(room_data["areas"], list):
                for area_data in room_data["areas"]:
                    if isinstance(area_data, dict) and "objects_present" in area_data and isinstance(area_data["objects_present"], list):
                         area_data["objects_present"][:] = [obj for obj in area_data["objects_present"] if not (isinstance(obj, dict) and obj.get('id') == object_id)]

        # 2. Add to new location
        if new_room_id and new_room_id in self.rooms_data:
            target_room_data = self.rooms_data[new_room_id]
            if new_area_id: # Add to specific area
                found_area = False
                if "areas" in target_room_data and isinstance(target_room_data["areas"], list):
                    for area_data in target_room_data["areas"]:
                        if isinstance(area_data, dict) and area_data.get("area_id") == new_area_id:
                             # Ensure objects_present list exists
                             if "objects_present" not in area_data or not isinstance(area_data["objects_present"], list):
                                 area_data["objects_present"] = []
                             # Add if not already present (shouldn't be, but safe check)
                             if object_id_to_save not in area_data["objects_present"]:
                                 area_data["objects_present"].append(object_id_to_save)
                                 logging.info(f"Added object '{object_id}' to area '{new_area_id}' in room '{new_room_id}'.")
                             found_area = True
                             break
                if not found_area:
                     logging.error(f"Could not add object '{object_id}' to area '{new_area_id}': Area not found in room '{new_room_id}'.")
                     return False
            else: # Add to room level
                 # Ensure objects_present list exists
                 if "objects_present" not in target_room_data or not isinstance(target_room_data["objects_present"], list):
                     target_room_data["objects_present"] = []
                 # Add if not already present
                 if object_id_to_save not in target_room_data["objects_present"]:
                     target_room_data["objects_present"].append(object_id_to_save)
                     logging.info(f"Added object '{object_id}' directly to room '{new_room_id}'.")
                 return True # Added to room level successfully

        elif new_room_id:
            logging.error(f"Could not add object '{object_id}' to room '{new_room_id}': Room ID not found.")
            return False
        else:
            # No new room specified, object just removed from old location (or was never placed)
            logging.info(f"Object '{object_id}' location cleared (not assigned to a new room/area).")
            return True # Successfully handled clearing location

        return True # Reached here if added to area successfully

    def delete_object(self, object_id: str) -> bool:
        """Deletes an object from internal lists and saves changes."""
        if not object_id: return False

        original_object_index = -1
        for i, obj in enumerate(self.objects_data):
             if isinstance(obj, dict) and obj.get('id', '').strip() == object_id.strip():
                 original_object_index = i
                 break

        if original_object_index == -1:
             logging.error(f"Cannot delete object: ID '{object_id}' not found in objects list.")
             return False

        # Remove from objects list
        deleted_obj_data = self.objects_data.pop(original_object_index)
        logging.info(f"Removed object '{object_id}' from internal objects list.")

        # Remove from room/area location
        if not self._update_object_location_in_rooms(object_id, None, None):
             logging.warning(f"Could not definitively remove '{object_id}' from room locations during delete (might not have been placed).")
             # Continue deletion from objects.yaml anyway

        # Save changes to both files
        return self.save_all_changes() # Use the new combined save method

    def save_all_changes(self) -> bool:
         """Saves the current state of objects_data and rooms_data to their files."""
         objects_to_save = {'objects': self.objects_data} # Structure for file
         # Convert rooms dict back to list structure for saving
         rooms_list_to_save = list(self.rooms_data.values())
         rooms_to_save = {'rooms': rooms_list_to_save} # Structure for file

         objects_saved = self._save_yaml_file(self.objects_file, objects_to_save)
         rooms_saved = self._save_yaml_file(self.rooms_file, rooms_to_save)

         if objects_saved and rooms_saved:
             logging.info("All changes saved successfully to objects.yaml and rooms.yaml.")
             return True
         else:
             logging.error("Failed to save changes to one or both YAML files.")
             # TODO: Consider rollback or backup mechanism?
             return False

    def save_object_and_location(self, object_id: str, new_room_id: Optional[str], new_area_id: Optional[str]) -> bool:
        """Updates the location lists in rooms_data and saves all changes."""
        if not object_id:
             logging.error("save_object_and_location: Missing object_id.")
             return False
        if not new_room_id:
             logging.error("save_object_and_location: Missing new_room_id. Cannot save object without assigning to a room.")
             return False

        # Update location in the rooms data structure
        location_updated = self._update_object_location_in_rooms(object_id, new_room_id, new_area_id)

        if not location_updated:
            logging.error(f"Failed to update location for object '{object_id}' in rooms data.")
            # Don't save if location update failed critically (e.g., target room/area invalid)
            return False

        # Save changes to both files
        return self.save_all_changes()

# Example Usage (for testing)
if __name__ == '__main__':
    # Adjust the path if running this file directly from its own directory
    manager = ObjectDataManager(data_dir=Path("..", "..", "data"))

    if manager.objects_data and manager.rooms_data:
        print("Data loaded successfully!")
        print("Object IDs:", manager.get_object_ids())
        print("Room IDs:", manager.get_room_ids())

        test_id = "cab_locker" # Example ID, change if needed
        obj = manager.get_object_by_id(test_id)
        if obj:
            print(f"\nData for '{test_id}':")
            # Print object data using yaml.dump to see formatting
            manager.yaml.dump([obj], Path.cwd() / "temp_object_output.yaml") # Dump to a temp file to view
            print(f"(See temp_object_output.yaml for formatted details of {test_id})")

        else:
            print(f"\nObject with ID '{test_id}' not found.")
    else:
        print("Failed to load data.") 