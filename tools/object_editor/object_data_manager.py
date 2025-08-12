# Handles loading, saving, and managing object and room YAML data.
from loguru import logger
from pathlib import Path
from typing import Dict, List, Any, Optional
from ruamel.yaml import YAML
from ruamel.yaml.parser import ParserError
from ruamel.yaml.scanner import ScannerError

class ObjectDataManager:
    """Manages loading, accessing, and saving object and room data from YAML files."""

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initializes the manager and loads data.
        If data_dir is not provided, it defaults to the 'data' directory
        in the project root.
        """
        if data_dir is None:
            # Assumes the script is in tools/object_editor, so ../../data
            self.data_dir = Path(__file__).parent.parent.parent / "data"
        else:
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
            logger.warning(f"No objects found or loaded from {self.objects_file}. Check format (expected list under 'objects:' key).")
        if not self.rooms_data:
             logger.warning(f"No rooms found or loaded from {self.rooms_file}. Check format (expected list under 'rooms:' key).")

        logger.info(f"Loaded {len(self.objects_data)} objects and {len(self.rooms_data)} rooms.")

    def _load_yaml_file(self, file_path: Path) -> Optional[Any]:
        """Loads a single YAML file using ruamel.yaml."""
        try:
            if not file_path.is_file():
                logger.error(f"Data file not found: {file_path}")
                return None
            with open(file_path, 'r', encoding='utf-8') as f:
                data = self.yaml.load(f)
                logger.info(f"Successfully loaded YAML file: {file_path}")
                return data
        except (ParserError, ScannerError) as e:
            logger.error(f"Error parsing YAML file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred loading {file_path}: {e}")
            return None

    # --- Methods for accessing data will go here ---
    def get_object_count(self) -> int:
        """Returns the current number of loaded objects."""
        return len(self.objects_data)

    def get_object_ids(self) -> List[str]:
        """Returns a sorted list of all object IDs from the loaded list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logger.warning("get_object_ids: No objects_data list found.")
            return []
        ids = []
        for i, obj in enumerate(self.objects_data):
            if isinstance(obj, dict) and 'id' in obj:
                obj_id = obj.get('id', '')
                if obj_id:
                    ids.append(obj_id)
                else:
                    logger.warning(f"get_object_ids: Found empty ID in object at index {i}.")
            else:
                logger.warning(f"get_object_ids: Item at index {i} is not a dict or lacks 'id' key.")
        
        sorted_ids = sorted(ids)
        logger.info(f"get_object_ids: Returning IDs: {sorted_ids}") # DEBUG LOG
        return sorted_ids

    def get_room_ids(self) -> List[str]:
        """Returns a sorted list of all room IDs from the processed dictionary."""
        if not self.rooms_data or not isinstance(self.rooms_data, dict):
            return []
        # Now reads keys from the dictionary created in _load_data
        return sorted(list(self.rooms_data.keys()))

    def get_room_name(self, room_id: str) -> Optional[str]:
        """Returns the name of the room with the given ID."""
        if not self.rooms_data or room_id not in self.rooms_data:
            logger.warning(f"get_room_name: Room ID '{room_id}' not found in rooms_data.")
            return None
        room_data = self.rooms_data.get(room_id, {})
        return room_data.get('name') # Return the name or None if key missing

    def get_object_by_id(self, object_id: str) -> Optional[Dict[str, Any]]:
         """Retrieves the data for a specific object by its ID."""
         if not self.objects_data or not isinstance(self.objects_data, list): # Added type check
             logger.warning("get_object_by_id: objects_data is not a list or is empty.")
             return None
         if not object_id: # Prevent comparing against None/empty string
              logger.warning("get_object_by_id: received empty object_id to search for.")
              return None

         search_id = object_id.strip() # Strip whitespace from the ID we are searching for

         for i, obj in enumerate(self.objects_data):
             if isinstance(obj, dict):
                 obj_id_val = obj.get('id')
                 if isinstance(obj_id_val, str):
                     # --- Compare stripped versions ---
                     if obj_id_val.strip() == search_id:
                         logger.debug(f"get_object_by_id: Match found for '{search_id}' at index {i}.")
                         return obj
                 else:
                     logger.warning(f"get_object_by_id: Object at index {i} has non-string ID: {obj_id_val}")
             else:
                  logger.warning(f"get_object_by_id: Item at index {i} is not a dictionary.")

         logger.warning(f"get_object_by_id: No match found for '{search_id}'.")
         return None

    def get_key_object_ids(self) -> List[str]:
        """Returns a sorted list of object IDs for objects categorized as 'key'."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logger.warning("get_key_object_ids: No objects_data list found.")
            return []
        key_ids = []
        for obj in self.objects_data:
            if isinstance(obj, dict):
                obj_id = obj.get('id')
                category = obj.get('category')
                # Accept 'key_item' as a valid category
                if obj_id and category == 'key_item':
                    key_ids.append(str(obj_id)) # Ensure it's a string
        
        sorted_key_ids = sorted(key_ids)
        logger.debug(f"get_key_object_ids: Found key IDs: {sorted_key_ids}")
        return sorted_key_ids

    def get_area_ids_for_room(self, room_id: str) -> List[str]:
        """Returns a sorted list of area IDs for a given room ID."""
        if not self.rooms_data or room_id not in self.rooms_data:
            return []
        room_data = self.rooms_data.get(room_id, {})
        areas_list = room_data.get("areas", [])
        if not isinstance(areas_list, list):
            logger.warning(f"Areas data for room '{room_id}' is not a list.")
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
        logger.debug(f"find_object_location: Entered for object_id='{object_id}'. Checking self.rooms_data (len={len(self.rooms_data) if self.rooms_data else 0}). Is dict? {isinstance(self.rooms_data, dict)}")

        if not self.rooms_data or not object_id:
            logger.debug("find_object_location: Exiting early because self.rooms_data is empty or object_id is missing.") # Log the early exit
            return None, None

        search_id = object_id.strip()

        for room_id, room_data in self.rooms_data.items():
            if not isinstance(room_data, dict): continue

            # Check room-level objects_present
            room_objects = room_data.get("objects_present", [])
            if isinstance(room_objects, list):
                # --- Log the raw list content ---
                logger.debug(f"Room '{room_id}' room_objects: {room_objects}")
                for obj_dict in room_objects:
                    if isinstance(obj_dict, dict):
                         obj_id_val = obj_dict.get('id', '')
                         # --- Log extracted ID and comparison ---
                         logger.debug(f"  Checking room obj: ID='{obj_id_val}' (Type: {type(obj_id_val)}), Comparing '{obj_id_val.strip() if isinstance(obj_id_val, str) else obj_id_val}' == '{search_id}'")
                         if isinstance(obj_id_val, str) and obj_id_val.strip() == search_id:
                            logger.debug(f"Object '{search_id}' found directly in room '{room_id}'.")
                            return room_id, None
                    else:
                        # Log items that are not dictionaries
                        logger.debug(f"  Skipping non-dict room obj: {obj_dict} (Type: {type(obj_dict)}) ")


            # Check area-level objects_present
            areas_list = room_data.get("areas", [])
            if isinstance(areas_list, list):
                for area_data in areas_list:
                    if not isinstance(area_data, dict): continue
                    area_id = area_data.get("area_id")
                    area_objects = area_data.get("objects_present", [])
                    if isinstance(area_objects, list):
                         # --- Log the raw list content ---
                         logger.debug(f"Area '{area_id}' in room '{room_id}' area_objects: {area_objects}")
                         for obj_dict in area_objects:
                             if isinstance(obj_dict, dict):
                                 obj_id_val = obj_dict.get('id', '')
                                 # --- Log extracted ID and comparison ---
                                 logger.debug(f"    Checking area obj: ID='{obj_id_val}' (Type: {type(obj_id_val)}), Comparing '{obj_id_val.strip() if isinstance(obj_id_val, str) else obj_id_val}' == '{search_id}'")
                                 if isinstance(obj_id_val, str) and obj_id_val.strip() == search_id:
                                     logger.debug(f"Object '{search_id}' found in area '{area_id}' of room '{room_id}'.")
                                     return room_id, area_id
                             else:
                                 # Log items that are not dictionaries
                                 logger.debug(f"    Skipping non-dict area obj: {obj_dict} (Type: {type(obj_dict)}) ")

        logger.debug(f"Object '{search_id}' not found in any room or area 'objects_present' list.")
        return None, None

    # --- Methods for modifying and saving data will go here ---
    def _save_yaml_file(self, file_path: Path, data: Any) -> bool:
        """Saves data to a YAML file using ruamel.yaml, preserving formatting."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                self.yaml.dump(data, f)
            logger.info(f"Successfully saved YAML file: {file_path}")
            return True
        except Exception as e:
            logger.exception(f"An error occurred saving {file_path}")
            return False

    def add_object(self, new_object_data: dict) -> bool:
        """Adds a new object dictionary to the internal list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logger.error("Cannot add object: objects_data not loaded or not a list.")
            return False
        if not new_object_data or not isinstance(new_object_data, dict) or 'id' not in new_object_data:
            logger.error("Cannot add object: Invalid data provided.")
            return False
        
        new_id = new_object_data['id']
        if any(obj.get('id') == new_id for obj in self.objects_data if isinstance(obj, dict)):
            logger.error(f"Cannot add object: ID '{new_id}' already exists.")
            return False

        self.objects_data.append(new_object_data)
        logger.info(f"Added new object '{new_id}' to internal list.")
        return True

    def update_object(self, object_id: str, updated_object_data: dict) -> bool:
        """Updates an existing object's data in the internal list."""
        if not self.objects_data or not isinstance(self.objects_data, list):
            logger.error("Cannot update object: objects_data not loaded or not a list.")
            return False
        if not object_id:
            logger.error("Cannot update object: No object_id specified.")
            return False

        for i, obj in enumerate(self.objects_data):
            if isinstance(obj, dict) and obj.get('id') == object_id:
                self.objects_data[i] = updated_object_data
                # Ensure the ID in the updated data matches, if it was changed it's more complex
                if updated_object_data.get('id') != object_id:
                    logger.warning(f"Object ID in updated_object_data ('{updated_object_data.get('id')}') differs from original object_id ('{object_id}'). The list is updated, but this might be unintended.")
                logger.info(f"Updated object '{object_id}' in internal list.")
                return True
        logger.error(f"Cannot update object: ID '{object_id}' not found.")
        return False

    def _update_object_location_in_rooms(self, object_id: str, new_room_id: Optional[str], new_area_id: Optional[str]) -> bool:
        """
        Removes the object_id from its old location (if any) in rooms_data
        and adds it to its new location (if specified).
        This method directly manipulates self.rooms_data.
        """
        if not self.rooms_data or not isinstance(self.rooms_data, dict):
            logger.error("_update_object_location_in_rooms: rooms_data is not loaded or is not a dictionary.")
            return False

        object_id_to_move = object_id.strip()
        found_and_removed_from_old = False
        operation_successful = True # Assume success unless an error occurs

        # Phase 1: Remove from all previous locations
        for room_id, room_data in self.rooms_data.items():
            if not isinstance(room_data, dict): continue

            # Check and remove from room's direct objects_present
            room_objects = room_data.get("objects_present", [])
            if isinstance(room_objects, list):
                original_len = len(room_objects)
                room_data["objects_present"] = [
                    obj for obj in room_objects
                    if not (isinstance(obj, dict) and obj.get('id', '').strip() == object_id_to_move)
                ]
                if len(room_data["objects_present"]) < original_len:
                    logger.debug(f"Removed '{object_id_to_move}' from room '{room_id}' direct objects.")
                    found_and_removed_from_old = True


            # Check and remove from areas within the room
            areas_list = room_data.get("areas", [])
            if isinstance(areas_list, list):
                for area_data in areas_list:
                    if not isinstance(area_data, dict): continue
                    area_objects = area_data.get("objects_present", [])
                    if isinstance(area_objects, list):
                        original_len = len(area_objects)
                        area_data["objects_present"] = [
                            obj for obj in area_objects
                            if not (isinstance(obj, dict) and obj.get('id', '').strip() == object_id_to_move)
                        ]
                        if len(area_data["objects_present"]) < original_len:
                            logger.debug(f"Removed '{object_id_to_move}' from area '{area_data.get('area_id')}' in room '{room_id}'.")
                            found_and_removed_from_old = True
        
        if found_and_removed_from_old:
            logger.info(f"Successfully cleared old locations for object '{object_id_to_move}'.")

        # Phase 2: Add to new location (if specified)
        if new_room_id:
            new_room_id_stripped = new_room_id.strip()
            target_room_data = self.rooms_data.get(new_room_id_stripped)

            if target_room_data and isinstance(target_room_data, dict):
                object_ref_dict = {"id": object_id_to_move} # Store as a dict with an 'id' key

                if new_area_id:
                    new_area_id_stripped = new_area_id.strip()
                    areas_list = target_room_data.get("areas", [])
                    target_area_data = None
                    if isinstance(areas_list, list):
                        for area in areas_list:
                            if isinstance(area, dict) and area.get("area_id", "").strip() == new_area_id_stripped:
                                target_area_data = area
                                break
                    
                    if target_area_data and isinstance(target_area_data, dict):
                        area_objects = target_area_data.setdefault("objects_present", [])
                        if not isinstance(area_objects, list): # ensure it's a list
                            logger.warning(f"Area '{new_area_id_stripped}' objects_present was not a list, re-initializing for object '{object_id_to_move}'.")
                            area_objects = []
                            target_area_data["objects_present"] = area_objects
                        
                        # Add if not already present (idempotent add)
                        if not any(isinstance(obj, dict) and obj.get('id', '').strip() == object_id_to_move for obj in area_objects):
                            area_objects.append(object_ref_dict)
                            logger.info(f"Added object '{object_id_to_move}' to area '{new_area_id_stripped}' in room '{new_room_id_stripped}'.")
                        else:
                            logger.debug(f"Object '{object_id_to_move}' already present in area '{new_area_id_stripped}'.")
                    else:
                        logger.error(f"Could not add object '{object_id_to_move}' to area '{new_area_id_stripped}': Area not found in room '{new_room_id_stripped}'.")
                        operation_successful = False
                else: # Add to room's direct objects_present
                    room_objects = target_room_data.setdefault("objects_present", [])
                    if not isinstance(room_objects, list): # ensure it's a list
                        logger.warning(f"Room '{new_room_id_stripped}' objects_present was not a list, re-initializing for object '{object_id_to_move}'.")
                        room_objects = []
                        target_room_data["objects_present"] = room_objects

                    # Add if not already present (idempotent add)
                    if not any(isinstance(obj, dict) and obj.get('id', '').strip() == object_id_to_move for obj in room_objects):
                        room_objects.append(object_ref_dict)
                        logger.info(f"Added object '{object_id_to_move}' directly to room '{new_room_id_stripped}'.")
                    else:
                        logger.debug(f"Object '{object_id_to_move}' already present in room '{new_room_id_stripped}'.")
            else:
                logger.error(f"Could not add object '{object_id_to_move}' to room '{new_room_id_stripped}': Room ID not found.")
                operation_successful = False
        else: # No new_room_id means the object is being unplaced
            logger.info(f"Object '{object_id_to_move}' location cleared (not assigned to a new room/area).")

        return operation_successful

    def delete_object(self, object_id: str) -> bool:
        """Deletes an object by its ID from the internal list and attempts to remove it from rooms."""
        if not self.objects_data or not isinstance(self.objects_data, list) or not object_id:
            logger.error(f"Cannot delete object: Data not loaded or invalid object_id ('{object_id}').")
            return False

        original_len = len(self.objects_data)
        self.objects_data = [obj for obj in self.objects_data if not (isinstance(obj, dict) and obj.get('id') == object_id)]

        if len(self.objects_data) < original_len:
            logger.info(f"Removed object '{object_id}' from internal objects list.")
            # Attempt to remove from rooms as well
            if not self._update_object_location_in_rooms(object_id, None, None):
                # This method now returns bool, but a warning here is still useful
                logger.warning(f"Could not definitively remove '{object_id}' from room locations during delete (might not have been placed or error occurred). Check logs.")
            return True
        else:
            logger.error(f"Cannot delete object: ID '{object_id}' not found in objects list.")
            return False

    def save_all_changes(self) -> bool:
        """Saves the current state of objects_data and rooms_data to their respective YAML files."""
        objects_payload = {'objects': self.objects_data if self.objects_data else []}
        # For rooms, we need to convert our internal dictionary back to a list of room dicts
        rooms_list = list(self.rooms_data.values()) if self.rooms_data else []
        rooms_payload = {'rooms': rooms_list}

        obj_saved = self._save_yaml_file(self.objects_file, objects_payload)
        room_saved = self._save_yaml_file(self.rooms_file, rooms_payload)

        if obj_saved and room_saved:
            logger.info("All changes saved successfully to objects.yaml and rooms.yaml.")
            return True
        else:
            logger.error("Failed to save changes to one or both YAML files.")
            return False

    def save_object_and_location(self, object_id: str, new_room_id: Optional[str], new_area_id: Optional[str]) -> bool:
        """
        Specialized save: Updates object location in rooms_data, then saves both files.
        This is useful if the object's own data hasn't changed but its location has.
        Assumes the object itself (in objects_data) is already up-to-date if it needed changes.
        """
        if not object_id:
            logger.error("save_object_and_location: Missing object_id.")
            return False
        
        # if not new_room_id: # Objects MUST be in a room. Area is optional.
        # #      logger.error("save_object_and_location: Missing new_room_id. Cannot save object without assigning to a room.")
        # #      return False
        # Allow unplacing by passing None for new_room_id

        logger.info(f"Attempting to update location for object '{object_id}' to Room: '{new_room_id}', Area: '{new_area_id}'.")
        location_updated = self._update_object_location_in_rooms(object_id, new_room_id, new_area_id)

        if not location_updated:
            logger.error(f"Failed to update location for object '{object_id}' in rooms data. Aborting save.")
            # No, we should still try to save the objects file even if location update had issues
            # return False 
            # Let's proceed to save, but the error about location is logged.

        logger.info(f"Location update for object '{object_id}' handled (new location: Room='{new_room_id}', Area='{new_area_id}'). Proceeding to save.")
        return self.save_all_changes()


# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Adjust the path if running from a different directory
    # Assuming this script is in tools/object_editor, data is ../../data
    manager = ObjectDataManager(data_dir=Path(__file__).parent.parent.parent / "data")
    
    if manager.objects_data is not None and manager.rooms_data is not None:
        print("Data loaded successfully!")
        print("Object IDs:", manager.get_object_ids())
        print("Room IDs:", manager.get_room_ids())

        # Test get_object_by_id
        test_id = "flashlight" # Change to an ID you expect to find or not find
        obj_data = manager.get_object_by_id(test_id)
        if obj_data:
            print(f"\nData for '{test_id}':")
            # For pretty printing the dict:
            from ruamel.yaml import YAML
            yaml_out = YAML()
            yaml_out.dump(obj_data, Path("temp_object_output.yaml")) # Save to temp file
            print(f"(See temp_object_output.yaml for formatted details of {test_id})")

        else:
            print(f"\nObject with ID '{test_id}' not found.")
    else:
        print("Failed to load data.") 