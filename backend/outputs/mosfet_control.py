import asyncio
import RPi.GPIO as GPIO

class MOSFETControl:
    """
    Control for MOSFET outputs (pumps, relays, etc.)
    """
    def __init__(self, pins):
        """
        Initialize MOSFET control
        
        Args:
            pins: List of GPIO pins connected to MOSFETs
        """
        self.pins = pins
        self.states = {pin: False for pin in pins}
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        for pin in self.pins:
            GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)
            
    def set_output(self, pin, state):
        """
        Set the state of a MOSFET output
        
        Args:
            pin: GPIO pin number
            state: True for on, False for off
        """
        if pin not in self.pins:
            raise ValueError(f"Pin {pin} is not configured as a MOSFET output")
            
        GPIO.output(pin, GPIO.HIGH if state else GPIO.LOW)
        self.states[pin] = state
        
    def get_state(self, pin):
        """
        Get the current state of a MOSFET output
        
        Args:
            pin: GPIO pin number
            
        Returns:
            bool: True if on, False if off
        """
        if pin not in self.pins:
            raise ValueError(f"Pin {pin} is not configured as a MOSFET output")
            
        return self.states[pin]
        
    def get_all_states(self):
        """
        Get the states of all MOSFET outputs
        
        Returns:
            dict: Dictionary of {pin: state}
        """
        return self.states.copy()
        
    async def pulse(self, pin, duration):
        """
        Pulse a MOSFET output for a specified duration
        
        Args:
            pin: GPIO pin number
            duration: Pulse duration in seconds
        """
        if pin not in self.pins:
            raise ValueError(f"Pin {pin} is not configured as a MOSFET output")
            
        # Turn on
        self.set_output(pin, True)
        
        # Wait for duration
        await asyncio.sleep(duration)
        
        # Turn off
        self.set_output(pin, False)
        
    def close(self):
        """Clean up GPIO resources"""
        for pin in self.pins:
            GPIO.output(pin, GPIO.LOW)
        GPIO.cleanup(self.pins)