from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from models.controller_schemas import EcControllerConfig
from models.base import MeasurementType
from controllers.base import BaseController, ControllerRegistry

class EcController(BaseController):
    """Controller for managing EC (Electrical Conductivity) levels by dosing nutrient solution"""
    
    def __init__(self, controller_db):
        super().__init__(controller_db)
        # Configuration parameters with defaults
        # self.target_ec = self.config.get('target_ec', 1.5)  # mS/cm
        # self.tolerance = self.config.get('tolerance', 0.2)  # mS/cm
        # self.dose_time = self.config.get('dose_time', 1.0)  # seconds
        # self.min_dose_interval = self.config.get('min_dose_interval', 300)  # seconds
        # self.output_pin = self.config.get('output_pin', None)
        self.config_obj = EcControllerConfig(**self.config)
        
        # State variables
        self.last_dose_time = None
    
    def process(self) -> Optional[Dict[str, Any]]:
        """Process EC sensor data and control nutrient dosing"""
        # Get the latest EC measurement from the associated sensors
        latest_ec = self._get_latest_ec()
        
        if latest_ec is None:
            return None  # No EC data available
        
        # Check if EC is too low and needs adjustment
        if latest_ec < self.config_obj.target_ec - self.config_obj.tolerance:
            # Check if enough time has passed since the last dose
            if (self.last_dose_time is None or 
                datetime.now() - self.last_dose_time > timedelta(seconds=self.config_obj.min_dose_interval)):
                
                # Activate the output pin if configured
                if self.config_obj.output_pin is not None:
                    try:
                        import platform
                        if platform.system() == "Linux":
                            try:
                                import RPi.GPIO as GPIO
                                # Set up the pin as output
                                GPIO.setup(self.config_obj.output_pin, GPIO.OUT)
                                # Turn on the nutrient pump
                                GPIO.output(self.config_obj.output_pin, True)
                                # Import threading for non-blocking delay
                                import threading
                                import time

                                def turn_off_after_delay():
                                    time.sleep(self.config_obj.dose_time)
                                    GPIO.output(self.config_obj.output_pin, False)

                                # Start a thread to turn off the pin after the dose time
                                threading.Thread(target=turn_off_after_delay).start()
                            except ImportError:
                                print(f"GPIO library not available, simulating dosing")
                        else:
                            print(f"Not on Linux, simulating dosing with pin {self.config_obj.output_pin}")
                    except Exception as e:
                        print(f"Error controlling output pin: {e}")
                
                self.last_dose_time = datetime.now()
                
                return {
                    'action_type': 'ec_dose',
                    'current_ec': latest_ec,
                    'target_ec': self.config_obj.target_ec,
                    'dose_time': self.config_obj.dose_time,
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
            if sensor.driver == 'ec':
                # In a real implementation, we would query the database
                # For simulation, we'll return a random EC value
                import random
                return random.uniform(0.8, 2.2)  # mS/cm
        
        return None

# Register the controller
ControllerRegistry.register('ec_controller', EcController)