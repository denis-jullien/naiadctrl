from typing import Dict, List, Any
from models.base import MeasurementType
from sensors.base import BaseSensor, SensorRegistry
from ._cs1237 import CS1237

class PHSensor(BaseSensor):
    """Driver for SHT41 temperature and humidity sensor"""
    
    def __init__(self, sensor_db):
        super().__init__(sensor_db)

        
        sck_pin = self.config.get('sck_pin', 11)
        data_read_pin = self.config.get('data_read_pin', 18)
        data_write_pin = self.config.get('data_write_pin', 13)

        # Initialize the sensor
        self.adc = CS1237(sck_pin, data_read_pin, data_write_pin)

        self.adc.initialize()
        self.adc.start()
    
    def read(self) -> List[Dict[str, Any]]:
        """Read temperature and humidity from the SHT41 sensor"""
        try:
            
            voltage = self.adc.get_averaged_data()
            
            # Apply calibration
            calibrated_ph = self.apply_calibration(MeasurementType.PH, voltage)

            return [
                {
                    'type': MeasurementType.PH,
                    'value': calibrated_ph,
                    'unit': '',
                    'raw_value': voltage
                }
            ]
        except Exception as e:
            # Log the error
            print(f"Error reading SHT41 sensor: {e}")
            return []

# Register the driver
SensorRegistry.register('ph', PHSensor)