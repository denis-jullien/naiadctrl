import asyncio
import time


class PHController:
    """
    Controller for maintaining pH level with proportional dosing
    """

    def __init__(
        self,
        ph_sensor,
        acid_pump_pin,
        base_pump_pin,
        mosfet_control,
        target_ph=6.0,
        tolerance=0.2,
        check_interval=60,
    ):
        """
        Initialize pH controller

        Args:
            ph_sensor: PHSensor instance
            acid_pump_pin: GPIO pin for acid dosing pump
            base_pump_pin: GPIO pin for base dosing pump
            mosfet_control: MOSFETControl instance
            target_ph: Target pH value
            tolerance: Acceptable deviation from target
            check_interval: Time between checks in seconds
        """
        self.ph_sensor = ph_sensor
        self.acid_pump_pin = acid_pump_pin
        self.base_pump_pin = base_pump_pin
        self.mosfet_control = mosfet_control

        self.target_ph = target_ph
        self.tolerance = tolerance
        self.check_interval = check_interval

        # Proportional dosing parameters
        self.max_proportional_value = 1.0  # pH difference for maximum dosing
        self.min_dose_time = 5.0  # minimum working time in seconds
        self.max_dose_time = 150.0  # maximum working time in seconds
        self.min_dose_interval = 300  # seconds (5 minutes) between dosing sessions

        # State variables
        self.running = False
        self.last_dose_time = 0
        self.last_ph = None
        self.dosing_in_progress = False

    def set_target(self, target_ph, tolerance=None):
        """
        Set target pH and tolerance

        Args:
            target_ph: Target pH value
            tolerance: Acceptable deviation from target
        """
        self.target_ph = target_ph
        if tolerance is not None:
            self.tolerance = tolerance

    def _calculate_dose_time(self, ph_difference):
        """
        Calculate dose time based on pH difference using proportional logic
        
        Args:
            ph_difference: Absolute difference between current pH and target pH
            
        Returns:
            tuple: (dose_time, pause_time) in seconds
        """
        # If within tolerance, no dosing needed
        if ph_difference <= self.tolerance:
            return 0, 0
            
        # Calculate proportion (0.0 to 1.0) based on difference
        proportion = min(ph_difference / self.max_proportional_value, 1.0)
        
        # Calculate dose time (minimum 5 seconds, scales up to max_dose_time)
        dose_time = max(self.min_dose_time, proportion * self.max_dose_time)
        
        # For full proportional dosing, pause time equals dose time when not at maximum
        # If at maximum proportion (1.0), continuous dosing (no pause)
        if proportion >= 1.0:
            pause_time = 0  # Continuous dosing
        else:
            pause_time = dose_time  # Equal pause and dose time
            
        return dose_time, pause_time

    async def _run_proportional_dosing(self, pump_pin, dose_time, pause_time):
        """
        Run a dosing cycle with proportional timing
        
        Args:
            pump_pin: GPIO pin for the pump
            dose_time: Time to run the pump in seconds
            pause_time: Pause time between doses in seconds
        """
        self.dosing_in_progress = True
        
        try:
            # If pause_time is 0, run continuously for dose_time
            if pause_time == 0:
                self.mosfet_control.set_output(pump_pin, True)
                await asyncio.sleep(dose_time)
                self.mosfet_control.set_output(pump_pin, False)
            else:
                # Run with alternating work-pause cycles
                cycles = int(self.check_interval / (dose_time + pause_time))
                cycles = max(1, cycles)  # At least one cycle
                
                for _ in range(cycles):
                    if not self.running or not self.dosing_in_progress:
                        break
                        
                    # Work cycle
                    self.mosfet_control.set_output(pump_pin, True)
                    await asyncio.sleep(dose_time)
                    
                    # Pause cycle
                    self.mosfet_control.set_output(pump_pin, False)
                    await asyncio.sleep(pause_time)
        finally:
            # Ensure pump is off
            self.mosfet_control.set_output(pump_pin, False)
            self.dosing_in_progress = False

    async def check_and_adjust(self):
        """Check pH level and adjust if needed using proportional dosing"""
        try:
            # Skip if already dosing
            if self.dosing_in_progress:
                return
                
            current_ph = await self.ph_sensor.read_ph()
            self.last_ph = current_ph
            
            # Calculate pH difference
            ph_difference = abs(current_ph - self.target_ph)

            # Check if adjustment is needed
            if ph_difference > self.tolerance:
                # Check if enough time has passed since last dosing session
                current_time = time.time()
                if current_time - self.last_dose_time >= self.min_dose_interval:
                    # Calculate dose and pause times
                    dose_time, pause_time = self._calculate_dose_time(ph_difference)
                    
                    if dose_time > 0:
                        if current_ph > self.target_ph:
                            # pH is too high, add acid
                            print(f"pH {current_ph} too high, dosing acid for {dose_time}s with {pause_time}s pauses")
                            await self._run_proportional_dosing(self.acid_pump_pin, dose_time, pause_time)
                        else:
                            # pH is too low, add base
                            print(f"pH {current_ph} too low, dosing base for {dose_time}s with {pause_time}s pauses")
                            await self._run_proportional_dosing(self.base_pump_pin, dose_time, pause_time)

                        self.last_dose_time = time.time()

        except Exception as e:
            print(f"Error in pH controller: {e}")
            # Ensure pumps are off in case of error
            try:
                self.mosfet_control.set_output(self.acid_pump_pin, False)
                self.mosfet_control.set_output(self.base_pump_pin, False)
            except:
                pass
            self.dosing_in_progress = False

    async def run(self):
        """Run the pH controller loop"""
        self.running = True
        while self.running:
            await self.check_and_adjust()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the pH controller"""
        self.running = False
        self.dosing_in_progress = False

    def get_status(self):
        """
        Get controller status

        Returns:
            dict: Status information
        """
        return {
            "target_ph": self.target_ph,
            "tolerance": self.tolerance,
            "current_ph": self.last_ph,
            "running": self.running,
            "last_dose_time": self.last_dose_time,
            "dosing_in_progress": self.dosing_in_progress,
            "max_proportional_value": self.max_proportional_value,
            "min_dose_time": self.min_dose_time,
            "max_dose_time": self.max_dose_time,
        }
