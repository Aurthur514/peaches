"""
Configuration Manager for Finance Anomaly Radar
Handles loading and validation of system configuration.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path
from loguru import logger

class ConfigManager:
    """Manages configuration settings for the FAR system."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
        self._validate_config()
    
    def _find_config_file(self) -> str:
        """Find the configuration file in the project directory."""
        possible_paths = [
            "config.yaml",
            "config.yml",
            "../config.yaml",
            os.path.expanduser("~/.far/config.yaml")
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                return path
        
        # Create default config if none found
        return self._create_default_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return self._get_default_config()
    
    def _validate_config(self) -> None:
        """Validate configuration settings."""
        required_sections = ['app', 'ai_engines', 'database', 'api']
        
        for section in required_sections:
            if section not in self.config:
                logger.warning(f"Missing configuration section: {section}")
                self.config[section] = {}
    
    def _create_default_config(self) -> str:
        """Create default configuration file."""
        default_config = self._get_default_config()
        config_path = "config.yaml"
        
        with open(config_path, 'w', encoding='utf-8') as file:
            yaml.dump(default_config, file, default_flow_style=False)
        
        logger.info(f"Default configuration created at {config_path}")
        return config_path
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            'app': {
                'name': 'Finance Anomaly Radar',
                'version': '1.0.0',
                'debug': True,
                'log_level': 'INFO'
            },
            'ai_engines': {
                'nlp_detector': {
                    'model_name': 'distilbert-base-uncased',
                    'confidence_threshold': 0.75
                },
                'market_detector': {
                    'window_size': 100,
                    'anomaly_threshold': 2.5
                }
            },
            'database': {
                'main_db': {
                    'type': 'sqlite',
                    'path': 'data/far_db.sqlite'
                }
            },
            'api': {
                'host': '0.0.0.0',
                'port': 8000
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot notation key."""
        keys = key.split('.')
        value = self.config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value by dot notation key."""
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def save(self) -> None:
        """Save current configuration to file."""
        with open(self.config_path, 'w', encoding='utf-8') as file:
            yaml.dump(self.config, file, default_flow_style=False)
        
        logger.info(f"Configuration saved to {self.config_path}")
    
    def get_db_config(self) -> Dict[str, Any]:
        """Get database configuration."""
        return self.get('database', {})
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API configuration."""
        return self.get('api', {})
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI engines configuration."""
        return self.get('ai_engines', {})