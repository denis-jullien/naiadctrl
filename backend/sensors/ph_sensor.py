import asyncio
from .cs1237 import CS1237

class PHSensor:
    """
    pH sensor using CS1237 ADC
    """
    def __init__(self, sck_pin, data_read_pin, data_write_pin=None, calibration_points=None):
        """
        Initialize pH sensor
        
        Args:
            sck_pin: Clock pin for CS1237
            data_read_pin: Data read pin for CS1237
            data_write_pin: Data write pin for CS1237 (if separate from read pin)
            calibration_points: Dictionary of {voltage: pH} calibration points
        """
        self.adc = CS1237(sck_pin, data_read_pin, data_write_pin)
        
        # Default calibration (pH 7 = 2.5V, pH 4 = 3.0V)
        self.calibration_points = calibration_points or {
            0.5: 7.0,
            3.0: 4.0
        }
        
        # Calculate slope and intercept from calibration points
        self._calculate_calibration()
        
    def _calculate_calibration(self):
        """Calculate calibration parameters from calibration points"""
        if len(self.calibration_points) < 2:
            raise ValueError("At least two calibration points are required")
            
        # Get two points for calibration
        voltages = list(self.calibration_points.keys())
        phs = list(self.calibration_points.values())
        
        v1, v2 = voltages[0], voltages[1]
        ph1, ph2 = phs[0], phs[1]
        
        # Calculate slope and intercept (pH = slope * voltage + intercept)
        self.slope = (ph2 - ph1) / (v2 - v1)
        self.intercept = ph1 - self.slope * v1
        
    async def initialize(self):
        """Initialize the sensor"""
        await self.adc.initialize()
        self.adc.start()
        
    async def read_voltage(self):
        """Read raw voltage from the sensor"""
        return self.adc.get_averaged_data()
        
    async def read_ph(self):
        """
        Read pH value from the sensor
        
        Returns:
            float: pH value
        """
        voltage = await self.read_voltage()
        ph = self.slope * voltage + self.intercept
        return ph
        
    def calibrate(self, voltage, ph):
        """
        Add a calibration point
        
        Args:
            voltage: Measured voltage
            ph: Known pH value
        """
        self.calibration_points[voltage] = ph
        self._calculate_calibration()
        
    def close(self):
        """Clean up resources"""
        self.adc.close()