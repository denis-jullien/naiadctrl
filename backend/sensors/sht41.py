import asyncio
import smbus2
import time

class SHT41:
    """
    SHT41 temperature and humidity sensor (I2C)
    """
    # SHT41 I2C address
    ADDRESS = 0x44
    
    # Commands
    CMD_MEASURE_HIGH_PRECISION = 0xFD
    CMD_MEASURE_MEDIUM_PRECISION = 0xF6
    CMD_MEASURE_LOW_PRECISION = 0xE0
    CMD_READ_SERIAL = 0x89
    CMD_SOFT_RESET = 0x94
    
    def __init__(self, bus_number=1):
        """
        Initialize SHT41 sensor
        
        Args:
            bus_number: I2C bus number
        """
        self.bus = smbus2.SMBus(bus_number)
        
    async def initialize(self):
        """Initialize the sensor"""
        # Soft reset
        self.bus.write_byte(self.ADDRESS, self.CMD_SOFT_RESET)
        await asyncio.sleep(0.01)  # 10ms delay
        
    async def read_measurement(self, precision="high"):
        """
        Read temperature and humidity
        
        Args:
            precision: Measurement precision ("high", "medium", "low")
            
        Returns:
            tuple: (temperature in °C, relative humidity in %)
        """
        # Select command based on precision
        if precision == "medium":
            cmd = self.CMD_MEASURE_MEDIUM_PRECISION
        elif precision == "low":
            cmd = self.CMD_MEASURE_LOW_PRECISION
        else:
            cmd = self.CMD_MEASURE_HIGH_PRECISION
            
        # Send measurement command
        self.bus.write_byte(self.ADDRESS, cmd)
        
        # Wait for measurement to complete
        if precision == "high":
            await asyncio.sleep(0.01)  # 10ms
        elif precision == "medium":
            await asyncio.sleep(0.005)  # 5ms
        else:
            await asyncio.sleep(0.002)  # 2ms
            
        # Read data (6 bytes: temp MSB, temp LSB, temp CRC, hum MSB, hum LSB, hum CRC)
        data = self.bus.read_i2c_block_data(self.ADDRESS, 0, 6)
        
        # Convert temperature
        temp_raw = (data[0] << 8) | data[1]
        temperature = -45 + 175 * temp_raw / 65535.0
        
        # Convert humidity
        hum_raw = (data[3] << 8) | data[4]
        humidity = 100 * hum_raw / 65535.0
        
        return temperature, humidity
        
    async def read_temperature(self):
        """
        Read temperature
        
        Returns:
            float: Temperature in °C
        """
        temp, _ = await self.read_measurement()
        return temp
        
    async def read_humidity(self):
        """
        Read humidity
        
        Returns:
            float: Relative humidity in %
        """
        _, humidity = await self.read_measurement()
        return humidity
        
    def close(self):
        """Clean up resources"""
        self.bus.close()