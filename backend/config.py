import json
import os

class Config:
    """
    Configuration manager for the hydroponic system
    """
    def __init__(self, config_file="config.json"):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = config_file
        self.config = self._load_default_config()
        
        # Load configuration from file if it exists
        if os.path.exists(config_file):
            self.load()
        else:
            # Save default configuration
            self.save()
            
    def _load_default_config(self):
        """Load default configuration"""
        return {
            "sensors": {
                "ph": {
                    "sck_pin": 11,
                    "data_read_pin": 18,
                    "data_write_pin": 13,  # Added separate write pin
                    "calibration": {
                        "voltage_1": 2.5,
                        "ph_1": 7.0,
                        "voltage_2": 3.0,
                        "ph_2": 4.0
                    }
                },
                "orp": {
                    "sck_pin": 16,
                    "data_read_pin": 19,
                    "data_write_pin": 20,  # Added separate write pin
                    "offset": 0
                },
                "ec": {
                    "sck_pin": 23,
                    "data_read_pin": 24,
                    "data_write_pin": 25,   # Added separate write pin
                    "pwm_pin": 18,
                    "k_value": 1.0,
                    "calibration": {
                        "factor": 1.0
                    }
                },
                "temperature": {
                    "ds18b20_id": None  # Auto-detect
                },
                "environment": {
                    "i2c_bus": 1
                }
            },
            "outputs": {
                "mosfet_pins": [5, 6, 7, 8, 9, 10]
            },
            "controllers": {
                "ph": {
                    "enabled": True,
                    "target": 6.0,
                    "tolerance": 0.2,
                    "check_interval": 60,
                    "acid_pump_pin": 5,
                    "base_pump_pin": 6
                },
                "orp": {
                    "enabled": True,
                    "target": 650,
                    "tolerance": 20,
                    "check_interval": 60,
                    "increase_pump_pin": 13,
                    "decrease_pump_pin": 19
                },
                "ec": {
                    "enabled": True,
                    "target": 1500,
                    "tolerance": 100,
                    "check_interval": 60,
                    "nutrient_pump_pin": 26,
                    "water_pump_pin": 16
                }
            },
            "api": {
                "host": "0.0.0.0",
                "port": 8000
            }
        }
        
    def load(self):
        """Load configuration from file"""
        try:
            with open(self.config_file, 'r') as f:
                loaded_config = json.load(f)
                
            # Update configuration (preserving default values for missing keys)
            self._update_dict(self.config, loaded_config)
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            
    def _update_dict(self, target, source):
        """
        Recursively update dictionary
        
        Args:
            target: Target dictionary to update
            source: Source dictionary with new values
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._update_dict(target[key], value)
            else:
                target[key] = value
                
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                
        except Exception as e:
            print(f"Error saving configuration: {e}")
            
    def get(self, section=None, key=None):
        """
        Get configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            
        Returns:
            Configuration value or section
        """
        if section is None:
            return self.config
            
        return self.config.get(section, key)
        
        
    def set(self, section, key, value):
        """
        Set configuration value
        
        Args:
            section: Configuration section
            key: Configuration key
            value: Configuration value
        """
        if section not in self.config:
            self.config[section] = {}
            
        self.config[section][key] = value
        self.save()