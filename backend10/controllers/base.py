from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
import importlib
import os
import inspect
import json
from datetime import datetime
from models.base import Controller, ControlAction, Sensor

class BaseController(ABC):
    """Base class for all controller implementations"""
    
    def __init__(self, controller_db: Controller):
        """Initialize the controller with its database model"""
        self.controller_db = controller_db
        # Parse the config JSON string to a dictionary
        self.config = json.loads(controller_db.config) if controller_db.config else {}
        self.sensors = controller_db.sensors
    
    @abstractmethod
    def process(self) -> Optional[Dict[str, Any]]:
        """Process sensor data and determine control actions
        
        Returns:
            Dictionary with action details or None if no action needed
        """
        pass
    
    def record_action(self, action_type: str, details: Dict[str, Any]) -> ControlAction:
        """Record a control action in the database
        
        Args:
            action_type: Type of action performed
            details: Details of the action
            
        Returns:
            The created ControlAction object
        """
        # Convert dict to JSON string
        details_json = json.dumps(details) if isinstance(details, dict) else details
        
        action = ControlAction(
            timestamp=datetime.now(),
            action_type=action_type,
            details=details_json,
            controller_id=self.controller_db.id
        )
        # In a real implementation, we would save this to the database
        # For now, we just return the object
        return action


class ControllerRegistry:
    """Registry for controller implementations"""
    
    _controllers: Dict[str, Type[BaseController]] = {}
    
    @classmethod
    def register(cls, controller_name: str, controller_class: Type[BaseController]) -> None:
        """Register a controller implementation"""
        cls._controllers[controller_name] = controller_class
    
    @classmethod
    def get_controller(cls, controller_name: str) -> Optional[Type[BaseController]]:
        """Get a controller implementation by name"""
        return cls._controllers.get(controller_name)
    
    @classmethod
    def get_available_controllers(cls) -> List[str]:
        """Get a list of all available controllers"""
        return list(cls._controllers.keys())
    
    @classmethod
    def load_controllers(cls) -> None:
        """Load all controller implementations from the controllers directory"""
        controllers_dir = os.path.dirname(__file__)
        
        # Import all modules in the controllers directory
        for filename in os.listdir(controllers_dir):
            if filename.endswith('.py') and filename != '__init__.py' and filename != 'base.py':
                module_name = filename[:-3]  # Remove .py extension
                module = importlib.import_module(f'controllers.{module_name}')
                
                # Find all BaseController subclasses in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseController) and 
                        obj != BaseController):
                        # Register the controller with its class name
                        cls.register(obj.__name__, obj)


# Initialize the controller registry
def initialize_controllers():
    """Initialize the controller registry"""
    # Load all controllers
    ControllerRegistry.load_controllers()