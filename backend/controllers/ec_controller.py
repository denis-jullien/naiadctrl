import asyncio
import time

class ECController:
    """
    Controller for maintaining EC (Electrical Conductivity) level
    """
    def __init__(self, ec_sensor, nutrient_pump_pin, water_pump_pin, mosfet_control, 
                 target_ec=1500, tolerance=100, check_interval=60):
        """
        Initialize EC controller
        
        Args:
            ec_sensor: ECSensor instance
            nutrient_pump_pin: GPIO pin for nutrient dosing pump
            water_pump_pin: GPIO pin for water dosing pump
            mosfet_control: MOSFETControl instance
            target_ec: Target EC value in μS/cm
            tolerance: Acceptable deviation from target in μS/cm
            check_interval: Time between checks in seconds
        """
        self.ec_sensor = ec_sensor
        self.nutrient_pump_pin = nutrient_pump_pin
        self.water_pump_pin = water_pump_pin
        self.mosfet_control = mosfet_control
        
        self.target_ec = target_ec
        self.tolerance = tolerance
        self.check_interval = check_interval
        
        # Dosing parameters
        self.dose_time = 1.0  # seconds
        self.min_dose_interval = 300  # seconds (5 minutes)
        
        # State variables
        self.running = False
        self.last_dose_time = 0
        self.last_ec = None
        
    def set_target(self, target_ec, tolerance=None):
        """
        Set target EC and tolerance
        
        Args:
            target_ec: Target EC value in μS/cm
            tolerance: Acceptable deviation from target in μS/cm
        """
        self.target_ec = target_ec
        if tolerance is not None:
            self.tolerance = tolerance
            
    async def check_and_adjust(self):
        """Check EC level and adjust if needed"""
        try:
            current_ec = await self.ec_sensor.read_ec()
            self.last_ec = current_ec
            
            # Check if adjustment is needed
            if abs(current_ec - self.target_ec) > self.tolerance:
                # Check if enough time has passed since last dose
                current_time = time.time()
                if current_time - self.last_dose_time >= self.min_dose_interval:
                    if current_ec < self.target_ec:
                        # EC is too low, add nutrients
                        await self.mosfet_control.pulse(self.nutrient_pump_pin, self.dose_time)
                    else:
                        # EC is too high, add water
                        await self.mosfet_control.pulse(self.water_pump_pin, self.dose_time)
                        
                    self.last_dose_time = current_time
                    
        except Exception as e:
            print(f"Error in EC controller: {e}")
            
    async def run(self):
        """Run the EC controller loop"""
        self.running = True
        while self.running:
            await self.check_and_adjust()
            await asyncio.sleep(self.check_interval)
            
    def stop(self):
        """Stop the EC controller"""
        self.running = False
        
    def get_status(self):
        """
        Get controller status
        
        Returns:
            dict: Status information
        """
        return {
            "target_ec": self.target_ec,
            "tolerance": self.tolerance,
            "current_ec": self.last_ec,
            "running": self.running,
            "last_dose_time": self.last_dose_time
        }