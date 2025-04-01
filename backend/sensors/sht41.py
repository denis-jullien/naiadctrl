import board
import adafruit_sht4x


class SHT41:
    """
    SHT41 temperature and humidity sensor using Adafruit CircuitPython library
    """

    def __init__(self, bus_number=1):
        """
        Initialize SHT41 sensor

        Args:
            bus_number: I2C bus number (used to select the appropriate board I2C)
        """
        self.bus_number = bus_number
        self.sensor = None
        self.initialized = False

    async def initialize(self):
        """Initialize the sensor"""
        try:
            # Create I2C interface based on bus number
            if self.bus_number == 1:
                i2c = board.I2C()  # uses board.SCL and board.SDA
            else:
                # For custom I2C pins, you would need to specify them
                # This is just a placeholder for other bus numbers
                i2c = board.I2C()

            # Create sensor object
            self.sensor = adafruit_sht4x.SHT4x(i2c)

            # Set to high precision mode by default
            self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

            # Check if sensor is responding by reading serial number
            serial = self.sensor.serial_number
            print(f"SHT4X sensor initialized. Serial number: {serial}")

            self.initialized = True
            return True

        except Exception as e:
            print(f"Error initializing SHT4X sensor: {e}")
            self.initialized = False
            return False

    async def read_measurement(self, precision="high"):
        """
        Read temperature and humidity

        Args:
            precision: Measurement precision ("high", "medium", "low")

        Returns:
            tuple: (temperature in °C, relative humidity in %)
        """
        if not self.initialized or self.sensor is None:
            print("SHT4X sensor not initialized")
            return None, None

        try:
            # Set precision mode
            if precision == "medium":
                self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_MEDIUMPRECISION
            elif precision == "low":
                self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_LOWPRECISION
            else:
                self.sensor.mode = adafruit_sht4x.Mode.NOHEAT_HIGHPRECISION

            # Read measurement
            temperature, humidity = self.sensor.measurements

            return temperature, humidity

        except Exception as e:
            print(f"Error reading from SHT4X sensor: {e}")
            return None, None

    async def read_temperature(self):
        """
        Read temperature

        Returns:
            float: Temperature in °C or None if error
        """
        temp, _ = await self.read_measurement()
        return temp

    async def read_humidity(self):
        """
        Read humidity

        Returns:
            float: Relative humidity in % or None if error
        """
        _, humidity = await self.read_measurement()
        return humidity

    def close(self):
        """Clean up resources"""
        # No explicit cleanup needed for the Adafruit library
        self.sensor = None
        self.initialized = False
