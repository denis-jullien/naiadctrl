from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type
import importlib
import os
import inspect
import json
from models.base import MeasurementType, Sensor, Measurement

class BaseSensor(ABC):
    """Base class for all sensor implementations"""
    
    def __init__(self, sensor_db: Sensor):
        """Initialize the sensor with its database model"""
        self.sensor_db = sensor_db
        # Parse JSON strings to dictionaries
        self.config = json.loads(sensor_db.config) if sensor_db.config else {}
        self.calibration_data = json.loads(sensor_db.calibration_data) if sensor_db.calibration_data else {}
    
    @abstractmethod
    def read(self) -> List[Dict[str, Any]]:
        """Read measurements from the sensor
        
        Returns:
            List of dictionaries with measurement data:
            [
                {
                    'type': MeasurementType,
                    'value': float,
                    'unit': str,
                    'raw_value': float (optional)
                },
                ...
            ]
        """
        pass
    
    def apply_calibration(self, measurement_type: MeasurementType, raw_value: float) -> float:
        """Apply calibration to a raw sensor value
        
        Args:
            measurement_type: Type of measurement being calibrated
            raw_value: Raw value from the sensor
            
        Returns:
            Calibrated value
        """
        if not self.calibration_data or measurement_type.value not in self.calibration_data:
            return raw_value
        
        cal_data = self.calibration_data[measurement_type.value]
        
        # Simple two-point calibration
        if 'points' in cal_data and len(cal_data['points']) >= 2:
            points = sorted(cal_data['points'], key=lambda p: p['raw'])
            
            # Find the two calibration points that bracket the raw value
            for i in range(len(points) - 1):
                low = points[i]
                high = points[i + 1]
                
                if low['raw'] <= raw_value <= high['raw']:
                    # Linear interpolation
                    raw_range = high['raw'] - low['raw']
                    if raw_range == 0:  # Avoid division by zero
                        return low['actual']
                    
                    actual_range = high['actual'] - low['actual']
                    ratio = (raw_value - low['raw']) / raw_range
                    return low['actual'] + (ratio * actual_range)
            
            # If outside the calibration range, use the closest point
            if raw_value < points[0]['raw']:
                return points[0]['actual']
            else:
                return points[-1]['actual']
        
        # Simple offset calibration
        if 'offset' in cal_data:
            return raw_value + cal_data['offset']
        
        # Simple scale calibration
        if 'scale' in cal_data:
            return raw_value * cal_data['scale']
        
        # No calibration data or unsupported format
        return raw_value


class SensorRegistry:
    """Registry for sensor drivers"""
    
    _drivers: Dict[str, Type[BaseSensor]] = {}
    
    @classmethod
    def register(cls, driver_name: str, driver_class: Type[BaseSensor]) -> None:
        """Register a sensor driver"""
        cls._drivers[driver_name] = driver_class
    
    @classmethod
    def get_driver(cls, driver_name: str) -> Optional[Type[BaseSensor]]:
        """Get a sensor driver by name"""
        return cls._drivers.get(driver_name)
    
    @classmethod
    def get_available_drivers(cls) -> List[str]:
        """Get a list of all available drivers"""
        return list(cls._drivers.keys())
    
    @classmethod
    def load_drivers(cls) -> None:
        """Load all sensor drivers from the drivers directory"""
        drivers_dir = os.path.join(os.path.dirname(__file__), 'drivers')
        if not os.path.exists(drivers_dir):
            os.makedirs(drivers_dir)
            
        # Create __init__.py if it doesn't exist
        init_file = os.path.join(drivers_dir, '__init__.py')
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# Sensor drivers package\n')
        
        # Import all modules in the drivers directory
        for filename in os.listdir(drivers_dir):
            if filename.endswith('.py') and filename != '__init__.py':
                print(f'Loading driver from {filename}')
                module_name = filename[:-3]  # Remove .py extension
                module = importlib.import_module(f'sensors.drivers.{module_name}')
                
                # # Find all BaseSensor subclasses in the module
                # for name, obj in inspect.getmembers(module):
                #     if (inspect.isclass(obj) and 
                #         issubclass(obj, BaseSensor) and 
                #         obj != BaseSensor):
                #         # Register the driver with its class name
                #         cls.register(obj.__name__, obj)


# Initialize the sensor registry
def initialize_sensors():
    """Initialize the sensor registry"""
    # Create the drivers directory if it doesn't exist
    drivers_dir = os.path.join(os.path.dirname(__file__), 'drivers')
    if not os.path.exists(drivers_dir):
        os.makedirs(drivers_dir)
        
    # Load all drivers
    SensorRegistry.load_drivers()