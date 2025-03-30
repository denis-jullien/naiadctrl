import asyncio
import time

class ORPController:
    """
    Controller for maintaining ORP level
    """
    def __init__(self, orp_sensor, increase_pump_pin, decrease_pump_pin, mosfet_control, 
                 target_orp=650, tolerance=20, check_interval=60):
        """
        Initialize ORP controller
        
        Args:
            orp_sensor: ORPSensor instance
            increase_pump_pin: GPIO pin for oxidizer dosing pump
            decrease_pump_pin: GPIO pin for reducer dosing pump
            mosfet_control: MOSFETControl instance
            target_orp: Target ORP value in mV
            tolerance: Acceptable deviation from target in mV
            check_interval: Time between checks in seconds
        """
        self.orp_sensor = orp_sensor
        self.increase_pump_pin = increase_pump_pin
        self.decrease_pump_pin = decrease_pump_pin
        self.mosfet_control = mosfet_control
        
        self.target_orp = target_orp
        self.tolerance = tolerance
        self.check_interval = check_interval
        
        # Dosing parameters
        self.dose_time = 1.0  # seconds
        self.min_dose_interval = 300  # seconds (5 minutes)
        
        # State variables
        self.running = False
        self.last_dose_time = 0
        self.last_orp = None
        
    def set_target(self, target_orp, tolerance=None):
        """
        Set target ORP and tolerance
        
        Args:
            target_orp: Target ORP value in mV
            tolerance: Acceptable deviation from target in mV
        """
        self.target_orp = target_orp
        if tolerance is not None:
            self.tolerance = tolerance
            
    async def check_and_adjust(self):
        """Check ORP level and adjust if needed"""
        try:
            current_orp = await self.orp_sensor.read_orp()
            self.last_orp = current_orp
            
            # Check if adjustment is needed
            if abs(current_orp - self.target_orp) > self.tolerance:
                # Check if enough time has passed since last dose
                current_time = time.time()
                if current_time - self.last_dose_time >= self.min_dose_interval:
                    if current_orp < self.target_orp:
                        # ORP is too low, add oxidizer
                        await self.mosfet_control.pulse(self.increase_pump_pin, self.dose_time)
                    else:
                        # ORP is too high, add reducer
                        await self.mosfet_control.pulse(self.decrease_pump_pin, self.dose_time)
                        
                    self.last_dose_time = current_time
                    
        except Exception as e:
            print(f"Error in ORP controller: {e}")
            
    async def run(self):
        """Run the ORP controller loop"""
        self.running = True
        while self.running:
            await self.check_and_adjust()
            await asyncio.sleep(self.check_interval)
            
    def stop(self):
        """Stop the ORP controller"""
        self.running = False
        
    def get_status(self):
        """
        Get controller status
        
        Returns:
            dict: Status information
        """
        return {
            "target_orp": self.target_orp,
            "tolerance": self.tolerance,
            "current_orp": self.last_orp,
            "running": self.running,
            "last_dose_time": self.last_dose_time
        }