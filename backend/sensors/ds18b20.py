import asyncio
import os
import glob

class DS18B20:
    """
    DS18B20 temperature sensor (1-Wire)
    """
    def __init__(self, sensor_id=None):
        """
        Initialize DS18B20 sensor
        
        Args:
            sensor_id: Specific sensor ID (if multiple sensors are connected)
        """
        self.base_dir = '/sys/bus/w1/devices/'
        self.sensor_id = sensor_id
        self.device_file = None
        
    async def initialize(self):
        """Initialize the sensor"""
        # Enable 1-Wire interface if not already enabled
        if not os.path.isdir(self.base_dir):
            os.system('modprobe w1-gpio')
            os.system('modprobe w1-therm')
            await asyncio.sleep(1)  # Wait for modules to load
            
        # Find sensor
        if self.sensor_id:
            self.device_file = f"{self.base_dir}{self.sensor_id}/w1_slave"
        else:
            # Find the first sensor
            device_folders = glob.glob(self.base_dir + '28-*')
            if device_folders:
                self.device_file = device_folders[0] + '/w1_slave'
            else:
                raise RuntimeError("No DS18B20 temperature sensors found")
                
    async def _read_temp_raw(self):
        """Read raw temperature data from the sensor"""
        with open(self.device_file, 'r') as f:
            lines = f.readlines()
        return lines
        
    async def read_temperature(self):
        """
        Read temperature from the sensor
        
        Returns:
            float: Temperature in °C
        """
        if not self.device_file:
            await self.initialize()
            
        lines = await self._read_temp_raw()
        
        # Retry if CRC check fails
        retries = 5
        while retries > 0 and lines[0].strip()[-3:] != 'YES':
            await asyncio.sleep(0.2)
            lines = await self._read_temp_raw()
            retries -= 1
            
        if lines[0].strip()[-3:] != 'YES':
            raise RuntimeError("CRC check failed for DS18B20 sensor")
            
        # Extract temperature
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return temp_c
            
        raise RuntimeError("Could not read temperature from DS18B20 sensor")