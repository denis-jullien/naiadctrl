import asyncio
import time


class PHController:
    """
    Controller for maintaining pH level
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

        # Dosing parameters
        self.dose_time = 1.0  # seconds
        self.min_dose_interval = 300  # seconds (5 minutes)

        # State variables
        self.running = False
        self.last_dose_time = 0
        self.last_ph = None

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

    async def check_and_adjust(self):
        """Check pH level and adjust if needed"""
        try:
            current_ph = await self.ph_sensor.read_ph()
            self.last_ph = current_ph

            # Check if adjustment is needed
            if abs(current_ph - self.target_ph) > self.tolerance:
                # Check if enough time has passed since last dose
                current_time = time.time()
                if current_time - self.last_dose_time >= self.min_dose_interval:
                    if current_ph > self.target_ph:
                        # pH is too high, add acid
                        await self.mosfet_control.pulse(
                            self.acid_pump_pin, self.dose_time
                        )
                    else:
                        # pH is too low, add base
                        await self.mosfet_control.pulse(
                            self.base_pump_pin, self.dose_time
                        )

                    self.last_dose_time = current_time

        except Exception as e:
            print(f"Error in pH controller: {e}")

    async def run(self):
        """Run the pH controller loop"""
        self.running = True
        while self.running:
            await self.check_and_adjust()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the pH controller"""
        self.running = False

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
        }
