"""
YAML loader module for Starship Adventure 2.
Handles loading and validation of game data from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Union
from loguru import logger

class YAMLLoader:
    """Handles loading and validation of YAML game data."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the YAML loader.
        
        Args:
            data_dir (str): Directory containing YAML data files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        logger.info(f"YAML loader initialized with data directory: {self.data_dir}")
    
    def load_file(self, filename: str) -> Dict[str, Any]:
        """Load and parse a YAML file.
        
        Args:
            filename (str): Name of the YAML file to load
            
        Returns:
            Dict[str, Any]: Parsed YAML data
            
        Raises:
            FileNotFoundError: If the file doesn't exist
            yaml.YAMLError: If the file contains invalid YAML
        """
        file_path = self.data_dir / filename
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                logger.info(f"Successfully loaded YAML file: {filename}")
                return data
        except FileNotFoundError:
            logger.error(f"YAML file not found: {filename}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {filename}: {e}")
            raise
    
    def validate_room_data(self, data: Dict[str, Any]) -> bool:
        """Validate room data structure.
        
        Args:
            data (Dict[str, Any]): Room data to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['room_id', 'name', 'first_visit_description', 'exits']
        required_power_states = ['offline', 'emergency', 'main_power', 'torch_light']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                msg = f"Missing required field '{field}' in room data"
                logger.error(msg)
                raise ValueError(msg)
        
        # Validate data types
        if not isinstance(data['room_id'], str):
            raise ValueError("Room id must be a string")
        if not isinstance(data['name'], str):
            raise ValueError("Room name must be a string")
        if not isinstance(data['first_visit_description'], dict):
            raise ValueError("First visit description must be a dictionary")
        if not isinstance(data['exits'], list):
            raise ValueError("Exits must be a list")
        
        # Validate power states
        for state in required_power_states:
            if state not in data['first_visit_description']:
                raise ValueError(f"Missing required power state '{state}' in first_visit_description")
        for state in data['first_visit_description']:
            if state not in required_power_states:
                raise ValueError(f"Invalid power state '{state}' in first_visit_description")
        
        # Validate areas if present
        if 'areas' in data:
            if not isinstance(data['areas'], list):
                raise ValueError("Areas must be a list")
            for area in data['areas']:
                self._validate_area(area)
        
        # Validate exits
        for exit_data in data['exits']:
            self._validate_exit(exit_data)
            
        return True
    
    def _validate_area(self, area: Dict[str, Any]) -> None:
        """Validate area data structure.
        
        Args:
            area (Dict[str, Any]): Area data to validate
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['area_id', 'name', 'command_aliases', 'area_count', 'first_visit_description']
        required_power_states = ['offline', 'emergency', 'main_power', 'torch_light']
        
        # Check required fields
        for field in required_fields:
            if field not in area:
                msg = f"Missing required field '{field}' in area data"
                logger.error(msg)
                raise ValueError(msg)
        
        # Validate data types
        if not isinstance(area['area_id'], str):
            raise ValueError("Area id must be a string")
        if not isinstance(area['name'], str):
            raise ValueError("Area name must be a string")
        if not isinstance(area['command_aliases'], list):
            raise ValueError("Area command aliases must be a list")
        if not isinstance(area['area_count'], int):
            raise ValueError("Area count must be an integer")
        if not isinstance(area['first_visit_description'], dict):
            raise ValueError("Area first visit description must be a dictionary")
        
        # Validate power states
        for state in required_power_states:
            if state not in area['first_visit_description']:
                raise ValueError(f"Missing required power state '{state}' in area first_visit_description")
        for state in area['first_visit_description']:
            if state not in required_power_states:
                raise ValueError(f"Invalid power state '{state}' in area first_visit_description")
    
    def _validate_exit(self, exit_data: Dict[str, Any]) -> None:
        """Validate exit data structure.
        
        Args:
            exit_data (Dict[str, Any]): Exit data to validate
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['direction', 'destination', 'dynamic_description']
        
        # Check required fields
        for field in required_fields:
            if field not in exit_data:
                msg = f"Missing required field '{field}' in exit data"
                logger.error(msg)
                raise ValueError(msg)
        
        # Validate data types
        if not isinstance(exit_data['direction'], str):
            raise ValueError("Exit direction must be a string")
        if not isinstance(exit_data['destination'], str):
            raise ValueError("Exit destination must be a string")
        if not isinstance(exit_data['dynamic_description'], dict):
            raise ValueError("Exit dynamic description must be a dictionary")
        
        # Validate dynamic description
        if 'unvisited' not in exit_data['dynamic_description']:
            raise ValueError("Exit dynamic description must contain 'unvisited' state")
        if 'visited' not in exit_data['dynamic_description']:
            raise ValueError("Exit dynamic description must contain 'visited' state")
    
    def validate_object_data(self, data: Dict[str, Any]) -> bool:
        """Validate object data structure.
        
        Args:
            data (Dict[str, Any]): Object data to validate
            
        Returns:
            bool: True if valid
            
        Raises:
            ValueError: If validation fails
        """
        required_fields = ['id', 'name', 'description', 'type']
        valid_types = ['furniture', 'device', 'item', 'structure', 'lighting']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                msg = f"Missing required field '{field}' in object data"
                logger.error(msg)
                raise ValueError(msg)
        
        # Validate data types
        if not isinstance(data['id'], str):
            raise ValueError("Object id must be a string")
        if not isinstance(data['name'], str):
            raise ValueError("Object name must be a string")
        if not isinstance(data['description'], str):
            raise ValueError("Object description must be a string")
        if not isinstance(data['type'], str):
            raise ValueError("Object type must be a string")
        if data['type'] not in valid_types:
            raise ValueError(f"Invalid object type. Must be one of: {', '.join(valid_types)}")
        
        # Validate optional fields if present
        if 'is_portable' in data and not isinstance(data['is_portable'], bool):
            raise ValueError("is_portable must be a boolean")
        if 'is_interactive' in data and not isinstance(data['is_interactive'], bool):
            raise ValueError("is_interactive must be a boolean")
        if 'weight' in data and not isinstance(data['weight'], (int, float)):
            raise ValueError("weight must be a number")
        if 'size' in data and not isinstance(data['size'], str):
            raise ValueError("size must be a string")
            
        return True 