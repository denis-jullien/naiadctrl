from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from controllers.base import BaseController, ControllerRegistry

class PumpTimerController(BaseController):
    """Controller for managing water pumps based on time schedules"""
    
    def __init__(self, controller_db):
        super().__init__(controller_db)
        # Configuration parameters with defaults
        self.on_duration = self.config.get('on_duration', 300)  # seconds
        self.off_duration = self.config.get('off_duration', 1800)  # seconds
        self.output_pin = self.config.get('output_pin', None)
        self.start_time = self.config.get('start_time', '08:00')  # HH:MM format
        self.end_time = self.config.get('end_time', '20:00')  # HH:MM format
        
        # State variables
        self.last_state_change = None
        self.current_state = False  # False = OFF, True = ON
    
    def process(self) -> Optional[Dict[str, Any]]:
        """Process time-based pump control"""
        current_time = datetime.now()
        
        # Check if we're within the active hours
        if not self._is_within_active_hours(current_time):
            if self.current_state:  # If pump is ON but outside active hours
                self.current_state = False
                return self._create_action('pump_off', 'Outside active hours')
            return None
        
        # Initialize state if this is the first run
        if self.last_state_change is None:
            self.last_state_change = current_time
            self.current_state = True
            return self._create_action('pump_on', 'Initial start')
        
        # Calculate time since last state change
        time_since_change = (current_time - self.last_state_change).total_seconds()
        
        # Check if it's time to change state
        if self.current_state:  # Currently ON
            if time_since_change >= self.on_duration:
                self.current_state = False
                self.last_state_change = current_time
                return self._create_action('pump_off', 'On duration completed')
        else:  # Currently OFF
            if time_since_change >= self.off_duration:
                self.current_state = True
                self.last_state_change = current_time
                return self._create_action('pump_on', 'Off duration completed')
        
        # No state change needed
        return None
    
    def _is_within_active_hours(self, current_time: datetime) -> bool:
        """Check if the current time is within the active hours"""
        # Parse start and end times
        start_hour, start_minute = map(int, self.start_time.split(':'))
        end_hour, end_minute = map(int, self.end_time.split(':'))
        
        # Create datetime objects for today's start and end times
        start_datetime = current_time.replace(
            hour=start_hour, minute=start_minute, second=0, microsecond=0)
        end_datetime = current_time.replace(
            hour=end_hour, minute=end_minute, second=0, microsecond=0)
        
        # Check if current time is within range
        return start_datetime <= current_time <= end_datetime
    
    def _create_action(self, action_type: str, reason: str) -> Dict[str, Any]:
        """Create an action dictionary"""
        # In a real implementation, we would activate the output pin
        # For example:
        # import RPi.GPIO as GPIO
        # GPIO.output(self.output_pin, GPIO.HIGH if action_type == 'pump_on' else GPIO.LOW)
        
        return {
            'action_type': action_type,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }

# Register the controller
ControllerRegistry.register('pump_timer', PumpTimerController)


class TempPumpTimerController(BaseController):
    """Controller for managing temperature-dependent water pumps"""
    
    def __init__(self, controller_db):
        super().__init__(controller_db)
        # Configuration parameters with defaults
        self.min_temp = self.config.get('min_temp', 18.0)  # °C
        self.max_temp = self.config.get('max_temp', 28.0)  # °C
        self.on_duration = self.config.get('on_duration', 300)  # seconds
        self.off_duration = self.config.get('off_duration', 1800)  # seconds
        self.output_pin = self.config.get('output_pin', None)
        
        # State variables
        self.last_state_change = None
        self.current_state = False  # False = OFF, True = ON
    
    def process(self) -> Optional[Dict[str, Any]]:
        """Process temperature-based pump control"""
        current_time = datetime.now()
        latest_temp = self._get_latest_temperature()
        
        if latest_temp is None:
            return None  # No temperature data available
        
        # Check if temperature is outside acceptable range
        temp_too_high = latest_temp > self.max_temp
        
        # Initialize state if this is the first run
        if self.last_state_change is None:
            self.last_state_change = current_time
            self.current_state = temp_too_high  # Turn on if temp is too high
            if self.current_state:
                return self._create_action('pump_on', f'Initial start - Temperature {latest_temp}°C above max {self.max_temp}°C')
            return None
        
        # Calculate time since last state change
        time_since_change = (current_time - self.last_state_change).total_seconds()
        
        # Check if it's time to change state based on temperature and timing
        if self.current_state:  # Currently ON
            if not temp_too_high or time_since_change >= self.on_duration:
                self.current_state = False
                self.last_state_change = current_time
                return self._create_action('pump_off', f'Temperature {latest_temp}°C normal or on duration completed')
        else:  # Currently OFF
            if temp_too_high and time_since_change >= self.off_duration:
                self.current_state = True
                self.last_state_change = current_time
                return self._create_action('pump_on', f'Temperature {latest_temp}°C above max {self.max_temp}°C')
        
        # No state change needed
        return None
    
    def _get_latest_temperature(self) -> Optional[float]:
        """Get the latest temperature measurement from the associated sensors"""
        for sensor in self.sensors:
            # Check if this sensor measures temperature
            if sensor.sensor_type.value in ['sht41', 'ds18b20']:
                # In a real implementation, we would query the database
                # For simulation, we'll return a random temperature value
                import random
                return random.uniform(15.0, 30.0)  # °C
        
        return None
    
    def _create_action(self, action_type: str, reason: str) -> Dict[str, Any]:
        """Create an action dictionary"""
        # In a real implementation, we would activate the output pin
        # For example:
        # import RPi.GPIO as GPIO
        # GPIO.output(self.output_pin, GPIO.HIGH if action_type == 'pump_on' else GPIO.LOW)
        
        return {
            'action_type': action_type,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }

# Register the controller
ControllerRegistry.register('temp_pump_timer', TempPumpTimerController)