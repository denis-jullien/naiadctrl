from typing import Dict, List, Any
from models.base import MeasurementType
from sensors.base import BaseSensor, SensorRegistry

class SHT41Sensor(BaseSensor):
    """Driver for SHT41 temperature and humidity sensor"""
    
    def __init__(self, sensor_db):
        super().__init__(sensor_db)
        # In a real implementation, we would initialize the hardware here
        # For example, using Adafruit's CircuitPython library
        self.i2c_address = self.config.get('i2c_address', 0x44)
        self.i2c_bus = self.config.get('i2c_bus', 1)
        
        # In a real implementation:
        import board
        import adafruit_sht4x
        i2c = board.I2C()
        self.sensor = adafruit_sht4x.SHT4x(i2c, address=self.i2c_address)
        # Set to high precision mode by default
        self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION
        
        # # For simulation purposes
        # self._simulated_temp = 25.0
        # self._simulated_humidity = 50.0
    
    def read(self) -> List[Dict[str, Any]]:
        """Read temperature and humidity from the SHT41 sensor"""
        try:
            # In a real implementation:
            temperature, humidity = self.sensor.measurements
            
            # # For simulation purposes
            # temperature = self._simulated_temp
            # humidity = self._simulated_humidity
            
            # # Simulate some variation
            # import random
            # temperature += random.uniform(-0.5, 0.5)
            # humidity += random.uniform(-2, 2)
            
            # Apply calibration
            calibrated_temp = self.apply_calibration(MeasurementType.TEMPERATURE, temperature)
            calibrated_humidity = self.apply_calibration(MeasurementType.HUMIDITY, humidity)
            
            return [
                {
                    'type': MeasurementType.TEMPERATURE,
                    'value': calibrated_temp,
                    'unit': '°C',
                    'raw_value': temperature
                },
                {
                    'type': MeasurementType.HUMIDITY,
                    'value': calibrated_humidity,
                    'unit': '%',
                    'raw_value': humidity
                }
            ]
        except Exception as e:
            # Log the error
            print(f"Error reading SHT41 sensor: {e}")
            return []

# Register the driver
SensorRegistry.register('sht41', SHT41Sensor)