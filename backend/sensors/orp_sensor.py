from .cs1237 import CS1237


class ORPSensor:
    """
    ORP (Oxidation-Reduction Potential) sensor using CS1237 ADC
    """

    def __init__(self, sck_pin, data_read_pin, data_write_pin=None, offset=0):
        """
        Initialize ORP sensor

        Args:
            sck_pin: Clock pin for CS1237
            data_read_pin: Data read pin for CS1237
            data_write_pin: Data write pin for CS1237 (if separate from read pin)
            offset: Calibration offset in mV
        """
        self.adc = CS1237(sck_pin, data_read_pin, data_write_pin)
        self.offset = offset

    async def initialize(self):
        """Initialize the sensor"""
        await self.adc.initialize()
        self.adc.start()

    async def read_voltage(self):
        """Read raw voltage from the sensor"""
        return self.adc.get_averaged_data()

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
