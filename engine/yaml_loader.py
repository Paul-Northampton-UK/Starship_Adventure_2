"""
YAML loader module for Starship Adventure 2.
Handles loading and validation of game data from YAML files.
"""

import yaml
from pathlib import Path
from typing import Dict, Any
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
            bool: True if valid, False otherwise
        """
        required_fields = ['id', 'name', 'description', 'exits']
        
        try:
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in room data")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating room data: {e}")
            return False
    
    def validate_object_data(self, data: Dict[str, Any]) -> bool:
        """Validate object data structure.
        
        Args:
            data (Dict[str, Any]): Object data to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        required_fields = ['id', 'name', 'description']
        
        try:
            for field in required_fields:
                if field not in data:
                    logger.error(f"Missing required field '{field}' in object data")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error validating object data: {e}")
            return False 