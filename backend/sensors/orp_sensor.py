import asyncio
from .cs1237 import CS1237

class ORPSensor:
    """
    ORP (Oxidation-Reduction Potential) sensor using CS1237 ADC
    """
    def __init__(self, sck_pin, data_pin, offset=0):
        """
        Initialize ORP sensor
        
        Args:
            sck_pin: Clock pin for CS1237
            data_pin: Data pin for CS1237
            offset: Calibration offset in mV
        """
        self.adc = CS1237(sck_pin, data_pin)
        self.offset = offset
        
    async def initialize(self):
        """Initialize the sensor"""
        await self.adc.initialize()
        
    async def read_voltage(self):
        """Read raw voltage from the sensor"""
        return await self.adc.read_voltage()
        
    async def read_orp(self):
        """
        Read ORP value from the sensor
        
        Returns:
            float: ORP value in mV
        """
        voltage = await self.read_voltage()
        # Convert voltage to mV and apply offset
        orp_mv = voltage * 1000 + self.offset
        return orp_mv
        
    async def calibrate(self, known_orp):
        """
        Calibrate the sensor with a known ORP solution
        
        Args:
            known_orp: Known ORP value in mV
        """
        voltage = await self.read_voltage()
        measured_orp = voltage * 1000
        self.offset = known_orp - measured_orp
        
    def close(self):
        """Clean up resources"""
        self.adc.close()