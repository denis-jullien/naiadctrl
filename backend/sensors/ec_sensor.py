import asyncio
import RPi.GPIO as GPIO
from .cs1237 import CS1237

class ECSensor:
    """
    EC (Electrical Conductivity) sensor using CS1237 ADC and PWM
    """
    def __init__(self, sck_pin, data_read_pin, data_write_pin=None, pwm_pin=None, frequency=1000, k_value=1.0):
        """
        Initialize EC sensor
        
        Args:
            sck_pin: Clock pin for CS1237
            data_read_pin: Data read pin for CS1237
            data_write_pin: Data write pin for CS1237 (if separate from read pin)
            pwm_pin: PWM output pin
            frequency: PWM frequency in Hz
            k_value: Cell constant (K value)
        """
        self.adc = CS1237(sck_pin, data_read_pin, data_write_pin)
        self.pwm_pin = pwm_pin
        self.frequency = frequency
        self.k_value = k_value
        
        # Temperature compensation
        self.temperature = 25.0  # Default temperature in °C
        
        # Calibration parameters
        self.calibration_factor = 1.0
        
        # Setup PWM
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pwm_pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pwm_pin, self.frequency)
        self.pwm.start(0)  # Start with 0% duty cycle
        
    async def initialize(self):
        """Initialize the sensor"""
        await self.adc.initialize()
        self.adc.start()
        
    async def read_ec(self, duty_cycle=50):
        """
        Read EC value from the sensor
        
        Args:
            duty_cycle: PWM duty cycle (0-100)
            
        Returns:
            float: EC value in μS/cm
        """
        # Set PWM duty cycle
        self.pwm.ChangeDutyCycle(duty_cycle)
        
        # Wait for the signal to stabilize
        await asyncio.sleep(0.1)
        
        # Read voltage
        voltage = self.adc.get_averaged_data()
        
        # Calculate EC (simplified model)
        # EC = voltage * k_value * calibration_factor
        ec = voltage * self.k_value * self.calibration_factor * 1000  # Convert to μS/cm
        
        # Apply temperature compensation
        ec = ec * (1.0 + 0.02 * (self.temperature - 25.0))
        
        return ec
        
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
        measured_ec = await self.read_ec()
        self.calibration_factor = known_ec / measured_ec
        
    def close(self):
        """Clean up resources"""
        self.pwm.stop()
        GPIO.cleanup(self.pwm_pin)
        self.adc.close()