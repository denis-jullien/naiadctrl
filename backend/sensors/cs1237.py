import asyncio
import RPi.GPIO as GPIO

class CS1237:
    """
    Interface for the CS1237 24-bit ADC
    """
    def __init__(self, sck_pin, data_pin, gain=1, rate=10):
        """
        Initialize CS1237 ADC
        
        Args:
            sck_pin: Clock pin
            data_pin: Data pin
            gain: Gain setting (1, 2, 64, 128)
            rate: Sample rate (10, 40, 640, 1280 Hz)
        """
        self.sck_pin = sck_pin
        self.data_pin = data_pin
        
        # Configure gain and rate
        gain_values = {1: 0, 2: 1, 64: 2, 128: 3}
        rate_values = {10: 0, 40: 1, 640: 2, 1280: 3}
        
        self.gain = gain_values.get(gain, 0)
        self.rate = rate_values.get(rate, 0)
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.sck_pin, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        self._initialized = False
        
    async def initialize(self):
        """Initialize the ADC"""
        if self._initialized:
            return
            
        try:
            # Wake up the ADC
            GPIO.output(self.sck_pin, GPIO.HIGH)
            await asyncio.sleep(0.001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            
            # Wait for the device to be ready with timeout
            timeout = 0.5  # 500ms timeout
            start_time = asyncio.get_event_loop().time()
            
            while GPIO.input(self.data_pin) == GPIO.HIGH:
                await asyncio.sleep(0.001)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print(f"Warning: CS1237 on pins SCK={self.sck_pin}, DATA={self.data_pin} timed out during initialization")
                    return False
                    
            self._initialized = True
            
            # Configure the device
            await self._configure()
            return True
            
        except Exception as e:
            print(f"Error initializing CS1237 on pins SCK={self.sck_pin}, DATA={self.data_pin}: {e}")
            return False
            
    async def read_raw(self):
        """
        Read raw 24-bit value from the ADC
        
        Returns:
            int: Raw 24-bit ADC value or None if error
        """
        if not self._initialized:
            success = await self.initialize()
            if not success:
                return None
                
        try:
            # Wait for the device to be ready with timeout
            timeout = 0.5  # 500ms timeout
            start_time = asyncio.get_event_loop().time()
            
            while GPIO.input(self.data_pin) == GPIO.HIGH:
                await asyncio.sleep(0.001)
                if asyncio.get_event_loop().time() - start_time > timeout:
                    print(f"Warning: CS1237 on pins SCK={self.sck_pin}, DATA={self.data_pin} timed out during reading")
                    return None
                    
            # Read 24 bits
            value = 0
            for i in range(24):
                GPIO.output(self.sck_pin, GPIO.HIGH)
                await asyncio.sleep(0.000001)  # 1µs delay
                
                value = (value << 1) | GPIO.input(self.data_pin)
                
                GPIO.output(self.sck_pin, GPIO.LOW)
                await asyncio.sleep(0.000001)  # 1µs delay
                
            # Additional clock pulse to complete the reading
            GPIO.output(self.sck_pin, GPIO.HIGH)
            await asyncio.sleep(0.000001)
            GPIO.output(self.sck_pin, GPIO.LOW)
            
            # Convert to signed value
            if value & 0x800000:
                value = value - 0x1000000
                
            return value
            
        except Exception as e:
            print(f"Error reading from CS1237 on pins SCK={self.sck_pin}, DATA={self.data_pin}: {e}")
            return None
            
    async def read_voltage(self, vref=5.0):
        """
        Read voltage from the ADC
        
        Args:
            vref: Reference voltage (default 5.0V)
            
        Returns:
            float: Voltage reading or None if error
        """
        raw = await self.read_raw()
        if raw is None:
            return None
            
        voltage = (raw / 0x7FFFFF) * vref
        return voltage
        
    def close(self):
        """Clean up GPIO resources"""
        GPIO.cleanup([self.sck_pin, self.data_pin])