from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from models.base import MeasurementType
from controllers.base import BaseController, ControllerRegistry

class EcController(BaseController):
    """Controller for managing EC (Electrical Conductivity) levels by dosing nutrient solution"""
    
    def __init__(self, controller_db):
        super().__init__(controller_db)
        # Configuration parameters with defaults
        self.target_ec = self.config.get('target_ec', 1.5)  # mS/cm
        self.tolerance = self.config.get('tolerance', 0.2)  # mS/cm
        self.dose_time = self.config.get('dose_time', 1.0)  # seconds
        self.min_dose_interval = self.config.get('min_dose_interval', 300)  # seconds
        self.output_pin = self.config.get('output_pin', None)
        
        # State variables
        self.last_dose_time = None
    
    def process(self) -> Optional[Dict[str, Any]]:
        """Process EC sensor data and control nutrient dosing"""
        # Get the latest EC measurement from the associated sensors
        latest_ec = self._get_latest_ec()
        
        if latest_ec is None:
            return None  # No EC data available
        
        # Check if EC is too low and needs adjustment
        if latest_ec < self.target_ec - self.tolerance:
            # Check if enough time has passed since the last dose
            if (self.last_dose_time is None or 
                datetime.now() - self.last_dose_time > timedelta(seconds=self.min_dose_interval)):
                
                # In a real implementation, we would activate the output pin
                # For example:
                # import RPi.GPIO as GPIO
                # GPIO.output(self.output_pin, GPIO.HIGH)
                # time.sleep(self.dose_time)
                # GPIO.output(self.output_pin, GPIO.LOW)
                
                self.last_dose_time = datetime.now()
                
                return {
                    'action_type': 'ec_dose',
                    'current_ec': latest_ec,
                    'target_ec': self.target_ec,
                    'dose_time': self.dose_time,
                    'timestamp': datetime.now().isoformat()
                }
        
        # EC is within acceptable range or too high
        return None
    
    def _get_latest_ec(self) -> Optional[float]:
        """Get the latest EC measurement from the associated sensors"""
        # In a real implementation, we would query the database for the latest measurement
        # For now, we'll simulate this by checking if any of our sensors measure EC
        
        for sensor in self.sensors:
            # Check if this sensor measures EC
            if sensor.sensor_type.value == 'ec_sensor':
                # In a real implementation, we would query the database
                # For simulation, we'll return a random EC value
                import random
                return random.uniform(0.8, 2.2)  # mS/cm
        
        return None

# Register the controller
ControllerRegistry.register('ec_controller', EcController)