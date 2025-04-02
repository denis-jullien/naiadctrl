import asyncio
import RPi.GPIO as GPIO
from .cs1237 import CS1237


class ECSensor:
    """
    EC (Electrical Conductivity) sensor using CS1237 ADC and PWM
    """

    def __init__(
        self,
        sck_pin,
        data_read_pin,
        data_write_pin,
        pwm_pin,
        range_pin,
        calibration_pin,
        selection_pin,
        frequency=1000,
        k_value=1.0,
    ):
        """
        Initialize EC sensor

        Args:
            sck_pin: Clock pin for CS1237
            data_read_pin: Data read pin for CS1237
            data_write_pin: Data write pin for CS1237
            pwm_pin: PWM output pin
            range_pin: Output pin for amplification factor selection (1 low, 100 high)
            calibration_pin: Output pin for calibration mode (calibrate low, measure high)
            selection_pin: Output pin for mode selection (calibration/measurement modes)
            frequency: PWM frequency in Hz
            k_value: Cell constant (K value)
        """
        self.adc = CS1237(sck_pin, data_read_pin, data_write_pin)
        self.pwm_pin = pwm_pin
        self.range_pin = range_pin
        self.calibration_pin = calibration_pin
        self.selection_pin = selection_pin
        self.frequency = frequency
        self.k_value = k_value

        # Temperature compensation
        self.temperature = 25.0  # Default temperature in °C

        # Calibration parameters
        self.calibration_factor = 1.0
        self.high_amplification = False  # Default to low amplification (1x)
        self.calibration_mode = False  # Default to measurement mode

        # Setup GPIO
        GPIO.setmode(GPIO.BCM)

        # Setup PWM
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, self.frequency)
        self.pwm.start(0)  # Start with 0% duty cycle

        # Setup additional control pins
        GPIO.setup(self.range_pin, GPIO.OUT)
        GPIO.output(self.range_pin, GPIO.LOW)  # Default to low amplification

        GPIO.setup(self.calibration_pin, GPIO.OUT)
        GPIO.output(self.calibration_pin, GPIO.HIGH)  # Default to measure mode

        GPIO.setup(self.selection_pin, GPIO.OUT)
        GPIO.output(self.selection_pin, GPIO.HIGH)  # Default to EC measurement

    async def initialize(self):
        """Initialize the sensor"""
        await self.adc.initialize()
        self.adc.start()

    def set_amplification(self, high_amplification=False):
        """
        Set the amplification factor

        Args:
            high_amplification: True for high amplification (100x), False for low (1x)
        """
        self.high_amplification = high_amplification
        GPIO.output(self.range_pin, GPIO.HIGH if high_amplification else GPIO.LOW)

    def set_calibration_mode(self, calibration_mode=False):
        """
        Set calibration mode

        Args:
            calibration_mode: True for calibration mode, False for measurement mode
        """
        self.calibration_mode = calibration_mode
        GPIO.output(self.calibration_pin, GPIO.LOW if calibration_mode else GPIO.HIGH)

    def select_measurement(self, measure_ec=True):
        """
        Select what to measure in the current mode

        Args:
            measure_ec: In measurement mode: True for EC, False for temperature
                        In calibration mode: True for high resistor, False for low resistor
        """
        GPIO.output(self.selection_pin, GPIO.HIGH if measure_ec else GPIO.LOW)

    async def read_ec(self, duty_cycle=50, auto_range=True):
        """
        Read EC value from the sensor

        Args:
            duty_cycle: PWM duty cycle (0-100)
            auto_range: Automatically select amplification based on reading

        Returns:
            float: EC value in μS/cm
        """
        # Set to measurement mode
        self.set_calibration_mode(False)
        self.select_measurement(True)  # Measure EC

        # Set PWM duty cycle
        self.pwm.ChangeDutyCycle(duty_cycle)

        # Wait for the signal to stabilize
        await asyncio.sleep(0.1)

        # If auto-range is enabled, try with low amplification first
        if auto_range:
            # Try with low amplification first
            self.set_amplification(False)
            await asyncio.sleep(0.1)
            voltage_low = self.adc.get_averaged_data()

            # If voltage is too low, switch to high amplification
            if voltage_low < 0.1:  # Threshold for switching to high amplification
                self.set_amplification(True)
                await asyncio.sleep(0.1)
                voltage = self.adc.get_averaged_data()
                # Apply amplification factor in calculation
                amplification_factor = 100
            else:
                voltage = voltage_low
                amplification_factor = 1
        else:
            # Read with current amplification setting
            voltage = self.adc.get_averaged_data()
            amplification_factor = 100 if self.high_amplification else 1

        # Calculate EC (simplified model)
        # EC = voltage * k_value * calibration_factor / amplification_factor
        ec = (
            voltage
            * self.k_value
            * self.calibration_factor
            * 1000
            / amplification_factor
        )

        # Apply temperature compensation
        ec = ec * (1.0 + 0.02 * (self.temperature - 25.0))

        return ec

    async def read_temperature(self):
        """
        Read temperature from the sensor circuit

        Returns:
            float: Temperature in °C
        """
        # Set to measurement mode and select temperature
        self.set_calibration_mode(False)
        self.select_measurement(False)  # Measure temperature

        # Wait for the signal to stabilize
        await asyncio.sleep(0.1)

        # Read voltage
        voltage = self.adc.get_averaged_data()

        # Convert voltage to temperature (this depends on your specific hardware)
        # This is a placeholder - adjust the formula based on your temperature sensor
        temperature = voltage * 100.0  # Example: 10mV per °C

        # Update the stored temperature
        self.temperature = temperature

        return temperature

    def set_temperature(self, temperature):
        """
        Set the current temperature for compensation

        Args:
            temperature: Water temperature in °C
        """
        self.temperature = temperature

    async def calibrate(self, known_ec):
        """
        Calibrate the sensor with a known EC solution

        Args:
            known_ec: Known EC value in μS/cm
        """
        # Set to measurement mode for actual EC reading
        self.set_calibration_mode(False)
        measured_ec = await self.read_ec(auto_range=True)
        self.calibration_factor = known_ec / measured_ec

    async def calibrate_resistors(self):
        """
        Calibrate the sensor using internal resistor dividers
        """
        # Set to calibration mode
        self.set_calibration_mode(True)

        # Measure with low resistor
        self.select_measurement(False)
        await asyncio.sleep(0.2)
        low_reading = self.adc.get_averaged_data()

        # Measure with high resistor
        self.select_measurement(True)
        await asyncio.sleep(0.2)
        high_reading = self.adc.get_averaged_data()

        # Calculate calibration factor based on resistor ratio
        # This is a placeholder - adjust based on your specific hardware design
        resistor_ratio = 10.0  # Expected ratio between high and low resistors
        measured_ratio = high_reading / low_reading if low_reading > 0 else 1.0

        # Adjust calibration factor
        self.calibration_factor = resistor_ratio / measured_ratio

        # Return to measurement mode
        self.set_calibration_mode(False)

        return self.calibration_factor

    def set_calibration_factor(self, factor):
        """
        Directly set the calibration factor

        Args:
            factor: Calibration factor value
        """
        self.calibration_factor = factor

    def close(self):
        """Clean up resources"""
        self.pwm.stop()
        # Clean up all GPIO pins
        GPIO.cleanup(
            [self.pwm_pin, self.range_pin, self.calibration_pin, self.selection_pin]
        )
        self.adc.close()
