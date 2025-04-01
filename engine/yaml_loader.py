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
        required_fields = ['id', 'name', 'description', 'exits']
        
        # Check required fields
        for field in required_fields:
            if field not in data:
                msg = f"Missing required field '{field}' in room data"
                logger.error(msg)
                raise ValueError(msg)
        
        # Validate data types
        if not isinstance(data['id'], str):
            raise ValueError("Room id must be a string")
        if not isinstance(data['name'], str):
            raise ValueError("Room name must be a string")
        if not isinstance(data['description'], str):
            raise ValueError("Room description must be a string")
        if not isinstance(data['exits'], dict):
            raise ValueError("Exits must be a dictionary")
        if 'objects' in data and not isinstance(data['objects'], list):
            raise ValueError("Objects must be a list")
        if 'accessible' in data and not isinstance(data['accessible'], bool):
            raise ValueError("Accessible must be a boolean")
            
        return True
    
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