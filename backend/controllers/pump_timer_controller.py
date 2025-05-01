import asyncio
import time
from datetime import datetime, timedelta


class PumpTimerController:
    """
    Controller for timing a pool pump based on temperature
    """

    def __init__(
        self,
        temperature_sensor,
        pump_pin,
        mosfet_control,
        min_run_time=15,  # minutes
        max_run_time=120,  # minutes
        temp_check_delay=5,  # minutes
        check_interval=60,  # seconds
        temp_thresholds=None,
        start_hour=8,
        end_hour=20,
    ):
        """
        Initialize pump timer controller

        Args:
            temperature_sensor: Temperature sensor instance
            pump_pin: GPIO pin for pump control
            mosfet_control: MOSFETControl instance
            min_run_time: Minimum run time in minutes
            max_run_time: Maximum run time in minutes
            temp_check_delay: Minutes to wait before checking temperature
            check_interval: Time between checks in seconds
            temp_thresholds: Dictionary mapping temperature thresholds to run times
                             e.g., {20: 30, 25: 60, 30: 90} means:
                             - Below 20°C: run for 30 minutes
                             - 20-25°C: run for 60 minutes
                             - 25-30°C: run for 90 minutes
                             - Above 30°C: run for max_run_time
            start_hour: Hour of day to start allowing pump runs (24h format)
            end_hour: Hour of day to stop allowing pump runs (24h format)
        """
        self.temperature_sensor = temperature_sensor
        self.pump_pin = pump_pin
        self.mosfet_control = mosfet_control

        self.min_run_time = min_run_time
        self.max_run_time = max_run_time
        self.temp_check_delay = temp_check_delay
        self.check_interval = check_interval
        
        # Default temperature thresholds if none provided
        self.temp_thresholds = temp_thresholds or {
            20: 30,  # Below 20°C: run for 30 minutes
            25: 60,  # 20-25°C: run for 60 minutes
            30: 90,  # 25-30°C: run for 90 minutes
            # Above 30°C: run for max_run_time
        }
        
        # Sort thresholds for easier processing
        self.sorted_thresholds = sorted(self.temp_thresholds.items())
        
        self.start_hour = start_hour
        self.end_hour = end_hour

        # State variables
        self.running = False
        self.pump_running = False
        self.last_run_start = 0
        self.last_run_duration = 0
        self.scheduled_end_time = 0
        self.last_temperature = None
        self.current_run_time = 0  # in minutes

    def set_thresholds(self, temp_thresholds):
        """
        Set temperature thresholds and corresponding run times

        Args:
            temp_thresholds: Dictionary mapping temperature thresholds to run times
        """
        self.temp_thresholds = temp_thresholds
        self.sorted_thresholds = sorted(self.temp_thresholds.items())

    def set_schedule(self, start_hour, end_hour):
        """
        Set daily schedule for pump operation

        Args:
            start_hour: Hour of day to start allowing pump runs (24h format)
            end_hour: Hour of day to stop allowing pump runs (24h format)
        """
        self.start_hour = start_hour
        self.end_hour = end_hour

    def get_status(self):
        """
        Get current controller status

        Returns:
            dict: Controller status
        """
        return {
            "enabled": self.running,
            "pump_running": self.pump_running,
            "last_run_start": self.last_run_start,
            "last_run_duration": self.last_run_duration,
            "scheduled_end_time": self.scheduled_end_time,
            "last_temperature": self.last_temperature,
            "current_run_time": self.current_run_time,
            "min_run_time": self.min_run_time,
            "max_run_time": self.max_run_time,
            "temp_check_delay": self.temp_check_delay,
            "temp_thresholds": self.temp_thresholds,
            "start_hour": self.start_hour,
            "end_hour": self.end_hour,
        }

    def _is_within_schedule(self):
        """Check if current time is within scheduled hours"""
        current_hour = datetime.now().hour
        if self.start_hour <= self.end_hour:
            return self.start_hour <= current_hour < self.end_hour
        else:  # Schedule crosses midnight
            return current_hour >= self.start_hour or current_hour < self.end_hour

    def _get_run_time_for_temperature(self, temperature):
        """
        Determine run time based on temperature

        Args:
            temperature: Current water temperature in °C

        Returns:
            int: Run time in minutes
        """
        # Default to max run time
        run_time = self.max_run_time
        
        # Find the appropriate threshold
        for threshold, minutes in self.sorted_thresholds:
            if temperature < threshold:
                run_time = minutes
                break
                
        return max(self.min_run_time, min(run_time, self.max_run_time))

    async def start_pump(self):
        """Start the pump and schedule its run time"""
        if not self.pump_running:
            # Turn on the pump
            self.mosfet_control.set_output(self.pump_pin, True)
            self.pump_running = True
            self.last_run_start = time.time()
            self.current_run_time = self.min_run_time  # Start with minimum run time
            
            # Schedule initial end time
            self.scheduled_end_time = self.last_run_start + (self.min_run_time * 60)
            
            print(f"Pump started, initial run time: {self.min_run_time} minutes")

    async def stop_pump(self):
        """Stop the pump"""
        if self.pump_running:
            self.mosfet_control.set_output(self.pump_pin, False)
            self.pump_running = False
            self.last_run_duration = (time.time() - self.last_run_start) / 60  # in minutes
            print(f"Pump stopped after {self.last_run_duration:.1f} minutes")

    async def run_continuously(self):
        """Run the pump continuously until manually stopped"""

        # Turn on the pump
        self.mosfet_control.set_output(self.pump_pin, True)
        self.pump_running = True
        self.last_run_start = time.time()
        self.current_run_time = 0  # This will increase as time passes
        
        # Set scheduled end time to a very large value (effectively infinite)
        self.scheduled_end_time = float('inf')
        
        print(f"Pump started in continuous mode")
        return True
        
        
    async def check_and_adjust(self):
        """Check conditions and adjust pump state"""
        try:
            current_time = time.time()
            
            # If pump is running, update current run time
            if self.pump_running:
                # Update current run time
                self.current_run_time = (current_time - self.last_run_start) / 60  # in minutes
                
                # If we've been running for temp_check_delay minutes, check temperature
                if (current_time - self.last_run_start) >= (self.temp_check_delay * 60) and \
                   (current_time - self.last_run_start) < (self.temp_check_delay * 60 + 60) and \
                   self.scheduled_end_time != float('inf'):  # Skip for continuous mode
                    
                    # Read temperature
                    temperature = await self.temperature_sensor.read_temperature()
                    self.last_temperature = temperature
                    
                    # Calculate new run time based on temperature
                    new_run_time = self._get_run_time_for_temperature(temperature)
                    self.current_run_time = new_run_time
                    
                    # Update scheduled end time
                    self.scheduled_end_time = self.last_run_start + (new_run_time * 60)
                    
                    print(f"Temperature: {temperature}°C, adjusted run time: {new_run_time} minutes")
                
                # Check if it's time to stop the pump (skip for continuous mode)
                if self.scheduled_end_time != float('inf') and current_time >= self.scheduled_end_time:
                    await self.stop_pump()
            
            # If pump is not running, check if it's time to start
            elif self._is_within_schedule():
                # Check if it's been at least 6 hours since last run
                if self.last_run_start == 0 or (current_time - self.last_run_start) >= 6 * 3600:
                    await self.start_pump()
            
        except Exception as e:
            print(f"Error in pump timer controller: {e}")

    async def run(self):
        """Run the controller loop"""
        self.running = True
        
        while self.running:
            await self.check_and_adjust()
            await asyncio.sleep(self.check_interval)

    def stop(self):
        """Stop the controller"""
        self.running = False

    async def force_run(self):
        """Force the pump to run until the next automatic cycle"""
        if not self.pump_running and self.running:
            await self.start_pump()
            # Set a flag to indicate this is a forced run
            self.forced_run = True
            return True
        return False