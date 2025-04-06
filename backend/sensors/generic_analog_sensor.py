import asyncio
import time
import logging
from .cs1237 import CS1237, CS1237_PGA_1, CS1237_SPEED_10HZ, CS1237_CHANNEL_A, CS1237_REFO_DISABLE

class GenericAnalogSensor:
    """
    Generic analog sensor using CS1237 ADC with configurable calibration and unit
    """
    
    def __init__(self, sck_pin, data_read_pin, data_write_pin, name="Generic", unit="", 
                 calibration_points=None, pga=CS1237_PGA_1, speed=CS1237_SPEED_10HZ):
        """
        Initialize the generic analog sensor
        
        Args:
            sck_pin: Clock pin for CS1237
            data_read_pin: Data read pin for CS1237
            data_write_pin: Data write pin for CS1237
            name: Sensor name
            unit: Unit of measurement (e.g., "°C", "ppm", etc.)
            calibration_points: Dictionary mapping raw ADC values to real-world values
            pga: Programmable Gain Amplifier setting
            speed: Sampling speed
        """
        self.name = name
        self.unit = unit
        self.calibration_points = calibration_points or {}
        self.initialized = False
        self.logger = logging.getLogger(f"sensor.{name.lower().replace(' ', '_')}")
        
        # Create CS1237 ADC instance
        self.adc = CS1237(
            sck_pin=sck_pin,
            data_read_pin=data_read_pin,
            data_write_pin=data_write_pin,
            pga=pga,
            speed=speed
        )
        
        # Last reading
        self.last_reading = None
        self.last_reading_time = 0
        
    async def initialize(self):
        """Initialize the sensor"""
        try:
            result = await self.adc.initialize()
            if result:
                self.adc.start()
                self.initialized = True
                self.logger.info(f"{self.name} sensor initialized")
                return True
            else:
                self.logger.error(f"Failed to initialize {self.name} sensor")
                return False
        except Exception as e:
            self.logger.error(f"Error initializing {self.name} sensor: {e}")
            return False
    
    def _interpolate(self, raw_value):
        """
        Interpolate between calibration points
        
        Args:
            raw_value: Raw ADC value
            
        Returns:
            float: Interpolated real-world value
        """
        if not self.calibration_points:
            # If no calibration points, return voltage
            return self.adc.get_data()
            
        # Convert calibration points to sorted lists
        raw_values = sorted(self.calibration_points.keys())
        real_values = [self.calibration_points[raw] for raw in raw_values]
        
        # If raw_value is outside the calibration range, use the closest point
        if raw_value <= raw_values[0]:
            return real_values[0]
        if raw_value >= raw_values[-1]:
            return real_values[-1]
        
        # Find the two closest calibration points
        for i in range(len(raw_values) - 1):
            if raw_values[i] <= raw_value <= raw_values[i + 1]:
                # Linear interpolation
                raw_range = raw_values[i + 1] - raw_values[i]
                real_range = real_values[i + 1] - real_values[i]
                ratio = (raw_value - raw_values[i]) / raw_range
                return real_values[i] + ratio * real_range
                
        # Fallback (should not reach here)
        return self.adc.get_data()
    
    async def read_raw(self):
        """
        Read raw ADC value
        
        Returns:
            int: Raw ADC value
        """
        if not self.initialized:
            self.logger.warning(f"{self.name} sensor not initialized")
            return None
            
        return self.adc.get_raw_data()
    
    async def read_voltage(self):
        """
        Read voltage from ADC
        
        Returns:
            float: Voltage reading
        """
        if not self.initialized:
            self.logger.warning(f"{self.name} sensor not initialized")
            return None
            
        return self.adc.get_data()
    
    async def read_value(self):
        """
        Read and convert sensor value using calibration
        
        Returns:
            float: Converted sensor value
        """
        if not self.initialized:
            self.logger.warning(f"{self.name} sensor not initialized")
            return None
            
        try:
            # Get raw value
            raw_value = self.adc.get_raw_data()
            
            # Apply calibration
            if self.calibration_points:
                value = self._interpolate(raw_value)
            else:
                # If no calibration, return voltage
                value = self.adc.get_data()
                
            # Update last reading
            self.last_reading = value
            self.last_reading_time = time.time()
            
            return value
        except Exception as e:
            self.logger.error(f"Error reading {self.name} value: {e}")
            return None
    
    def set_calibration(self, calibration_points):
        """
        Set calibration points
        
        Args:
            calibration_points: Dictionary mapping raw ADC values to real-world values
        """
        self.calibration_points = calibration_points
        self.logger.info(f"Updated {self.name} calibration: {calibration_points}")
    
    def set_unit(self, unit):
        """
        Set unit of measurement
        
        Args:
            unit: Unit string (e.g., "°C", "ppm", etc.)
        """
        self.unit = unit
        self.logger.info(f"Updated {self.name} unit to {unit}")
    
    def get_status(self):
        """
        Get sensor status
        
        Returns:
            dict: Sensor status information
        """
        return {
            "name": self.name,
            "unit": self.unit,
            "initialized": self.initialized,
            "last_reading": self.last_reading,
            "last_reading_time": self.last_reading_time,
            "has_calibration": bool(self.calibration_points)
        }
    
    def close(self):
        """Clean up resources"""
        if self.initialized:
            try:
                self.adc.stop()
                self.adc.close()
                self.logger.info(f"Closed {self.name} sensor")
            except Exception as e:
                self.logger.error(f"Error closing {self.name} sensor: {e}")
            finally:
                self.initialized = False