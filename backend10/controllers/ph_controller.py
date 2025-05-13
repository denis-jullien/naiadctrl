from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from models.base import MeasurementType, Measurement, Sensor
from controllers.base import BaseController, ControllerRegistry
from sqlmodel import Session, select
from database import engine

class PhController(BaseController):
    """Controller for managing pH levels by dosing pH- solution"""
    
    def __init__(self, controller_db):
        super().__init__(controller_db)
        # Configuration parameters with defaults
        self.target_ph = self.config.get('target_ph', 6.0)
        self.tolerance = self.config.get('tolerance', 0.2)
        self.dose_time = self.config.get('dose_time', 1.0)  # seconds
        self.min_dose_interval = self.config.get('min_dose_interval', 300)  # seconds
        self.output_pin = self.config.get('output_pin', None)
        
        # State variables
        self.last_dose_time = None
    
    def process(self) -> Optional[Dict[str, Any]]:
        """Process pH sensor data and control pH- dosing"""

        print("Processing pH controller...")
        
        # Get the latest pH measurement from the associated sensors
        latest_ph = self._get_latest_ph()
        
        if latest_ph is None:
            return None  # No pH data available

        print(f"Latest pH: {latest_ph}")
        
        # Check if pH is too high and needs adjustment
        if latest_ph > self.target_ph + self.tolerance:
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
                    'action_type': 'ph_dose',
                    'current_ph': latest_ph,
                    'target_ph': self.target_ph,
                    'dose_time': self.dose_time,
                    'timestamp': datetime.now().isoformat()
                }
        
        # pH is within acceptable range or too low
        return None
    
    def _get_latest_ph(self) -> Optional[float]:
        """Get the latest pH measurement from any associated sensors"""

        print("Getting latest pH measurement...")
        # Create a new session to query the database
        with Session(engine) as session:

            print("Querying database for latest pH measurement...")
            # Get the sensor IDs from the controller's sensors
            sensor_ids = [sensor.id for sensor in self.sensors]
            
            if not sensor_ids:
                print("No sensors associated with this controller")
                return None
            
            print(f"Looking for pH measurements from sensors: {sensor_ids}")
            
            # Query for the latest pH measurement from any of the associated sensors
            latest_measurement = session.exec(
                select(Measurement)
                .where(
                    Measurement.sensor_id.in_(sensor_ids),
                    Measurement.measurement_type == MeasurementType.PH
                )
                .order_by(Measurement.timestamp.desc())
                .limit(1)
            ).first()
        
            print(f"Latest measurement found: {latest_measurement}")
            
            if latest_measurement:
                return latest_measurement.value
            
            print("No pH measurements found, returning simulated value")
            # If no measurement found, return a random value for simulation
            import random
            return random.uniform(5.5, 7.5)

# Register the controller
ControllerRegistry.register('ph_controller', PhController)