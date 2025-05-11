import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models.base import Sensor, Controller, Measurement
from sensors.base import BaseSensor, SensorRegistry
from controllers.base import BaseController, ControllerRegistry

class Scheduler:
    """Scheduler for periodic sensor readings and controller actions"""
    
    def __init__(self):
        """Initialize the scheduler"""
        self.running = False
        self.thread = None
        self.sensor_instances: Dict[int, BaseSensor] = {}
        self.controller_instances: Dict[int, BaseController] = {}
        self.engine = None  # Will be set when the scheduler starts
    
    def set_engine(self, engine):
        """Set the database engine"""
        self.engine = engine
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5.0)
            self.thread = None
    
    def _run(self):
        """Main scheduler loop"""
        from main import engine  # Import here to avoid circular imports
        self.engine = engine
        
        while self.running:
            try:
                # Get the next sensor or controller to run
                next_item, is_sensor = self._get_next_item()
                
                if next_item:
                    # Run the sensor or controller
                    if is_sensor:
                        self._run_sensor(next_item)
                    else:
                        self._run_controller(next_item)
                else:
                    # No items to run, sleep for a short time
                    time.sleep(1.0)
            except Exception as e:
                # Log the error and continue
                print(f"Error in scheduler: {e}")
                time.sleep(1.0)
    
    def _get_next_item(self) -> tuple[Optional[Any], bool]:
        """Get the next sensor or controller to run
        
        Returns:
            Tuple of (item, is_sensor) where item is the sensor or controller to run
            and is_sensor is True if the item is a sensor, False if it's a controller
        """
        with Session(self.engine) as session:
            # Get all enabled sensors
            sensors_stmt = select(Sensor).where(Sensor.enabled == True)
            sensors = session.exec(sensors_stmt).all()
            
            # Get all enabled controllers
            controllers_stmt = select(Controller).where(Controller.enabled == True)
            controllers = session.exec(controllers_stmt).all()
            
            # Find the next sensor to run
            next_sensor = None
            next_sensor_time = None
            
            for sensor in sensors:
                # Get the last measurement for this sensor
                last_measurement_stmt = select(Measurement).where(
                    Measurement.sensor_id == sensor.id
                ).order_by(Measurement.timestamp.desc()).limit(1)
                
                last_measurement = session.exec(last_measurement_stmt).first()
                
                if last_measurement:
                    # Calculate the next run time
                    next_run = last_measurement.timestamp + timedelta(seconds=sensor.update_interval)
                else:
                    # No previous measurement, run immediately
                    next_run = datetime.now() - timedelta(seconds=1)
                
                # Check if this sensor should run next
                if next_sensor_time is None or next_run < next_sensor_time:
                    next_sensor = sensor
                    next_sensor_time = next_run
            
            # Find the next controller to run
            next_controller = None
            next_controller_time = None
            
            for controller in controllers:
                if controller.last_run:
                    # Calculate the next run time
                    next_run = controller.last_run + timedelta(seconds=controller.update_interval)
                else:
                    # No previous run, run immediately
                    next_run = datetime.now() - timedelta(seconds=1)
                
                # Check if this controller should run next
                if next_controller_time is None or next_run < next_controller_time:
                    next_controller = controller
                    next_controller_time = next_run
            
            # Determine whether to run a sensor or controller next
            if next_sensor_time and next_controller_time:
                if next_sensor_time <= next_controller_time:
                    return next_sensor, True
                else:
                    return next_controller, False
            elif next_sensor_time:
                return next_sensor, True
            elif next_controller_time:
                return next_controller, False
            else:
                return None, False
    
    def _run_sensor(self, sensor):
        """Run a sensor and record its measurements"""
        try:
            with Session(self.engine) as session:
                # Get the sensor instance or create it if it doesn't exist
                if sensor.id not in self.sensor_instances:
                    # Get the sensor driver class
                    driver_class = SensorRegistry.get_driver(sensor.driver)
                    if not driver_class:
                        print(f"Error: Driver {sensor.driver} not found for sensor {sensor.id}")
                        return
                    
                    # Create the sensor instance
                    self.sensor_instances[sensor.id] = driver_class(sensor)
                
                # Get the sensor instance
                sensor_instance = self.sensor_instances[sensor.id]
                
                # Read the sensor
                readings = sensor_instance.read()
                
                # Record the measurements
                for reading in readings:
                    measurement = Measurement(
                        timestamp=datetime.now(),
                        measurement_type=reading['type'],
                        value=reading['value'],
                        unit=reading['unit'],
                        raw_value=reading.get('raw_value'),
                        sensor_id=sensor.id
                    )
                    session.add(measurement)
                
                session.commit()
                print(f"Recorded {len(readings)} measurements from sensor {sensor.id}")
        except Exception as e:
            print(f"Error running sensor {sensor.id}: {e}")
    
    def _run_controller(self, controller):
        """Run a controller and record its actions"""
        try:
            with Session(self.engine) as session:
                # Get the controller from the database to ensure we have the latest data
                db_controller = session.get(Controller, controller.id)
                if not db_controller:
                    print(f"Error: Controller {controller.id} not found in database")
                    return
                
                # Get the controller instance or create it if it doesn't exist
                if controller.id not in self.controller_instances:
                    # Get the controller class
                    controller_class = ControllerRegistry.get_controller(controller.controller_type.value)
                    if not controller_class:
                        print(f"Error: Controller type {controller.controller_type} not found for controller {controller.id}")
                        return
                    
                    # Create the controller instance
                    self.controller_instances[controller.id] = controller_class(db_controller)
                
                # Get the controller instance
                controller_instance = self.controller_instances[controller.id]
                
                # Process the controller
                result = controller_instance.process()
                
                # Record the action if there was one
                if result:
                    action = controller_instance.record_action(
                        action_type=result.get('action_type', 'unknown'),
                        details=result
                    )
                    session.add(action)
                
                # Update the last run time
                db_controller.last_run = datetime.now()
                session.add(db_controller)
                
                session.commit()
                if result:
                    print(f"Recorded action from controller {controller.id}: {result.get('action_type', 'unknown')}")
                else:
                    print(f"No action taken by controller {controller.id}")
        except Exception as e:
            print(f"Error running controller {controller.id}: {e}")