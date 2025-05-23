import asyncio
import signal
import uvicorn

# Import configuration
from config import Config

# Import sensors
from sensors.ph_sensor import PHSensor
from sensors.orp_sensor import ORPSensor
from sensors.ec_sensor import ECSensor
from sensors.ds18b20 import DS18B20
from sensors.sht41 import SHT41
from sensors.generic_analog_sensor import GenericAnalogSensor

# Import controllers
from controllers.ph_controller import PHController
from controllers.orp_controller import ORPController
from controllers.ec_controller import ECController
from controllers.pump_timer_controller import PumpTimerController

# Import outputs
from outputs.mosfet_control import MOSFETControl

# Import API
from api.fastapi_routes import HydroFastAPI

# Add this import at the top with other imports
from history_storage import HistoryStorage
from mqtt_client import MQTTPublisher



# Add these imports at the top
import logging
from log_handler import MemoryLogHandler

class HydroponicSystem:
    # Add this after the class definition but before the initialize method
    # Create a memory log handler
    log_handler = MemoryLogHandler(capacity=1000)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),  # Console output
            log_handler  # Memory storage
        ]
    )

    # Get a logger for this module
    logger = logging.getLogger(__name__)

    def __init__(self, config_path="config.json"):
        """Initialize the hydroponic system"""
        self.config = Config(config_path)
        self.sensors = {}
        self.controllers = {}
        self.outputs = None
        self.api = None
        self.history_storage = None
        # Initialize tasks list
        self.tasks = []

        # Add MQTT client
        self.mqtt_client = None

        # In the __init__ method, add this line after self.mqtt_client = None
        # self.log_handler = memory_log_handler

    async def initialize(self):
        """Initialize all components"""
        print("Initializing hydroponic system...")

        # Initialize outputs
        mosfet_pins = self.config.get("outputs", {}).get("mosfet_pins", [])
        self.outputs = MOSFETControl(mosfet_pins)
        print(f"Initialized {len(mosfet_pins)} MOSFET outputs")

        # Initialize sensors
        await self._initialize_sensors()

        # Initialize controllers
        self._initialize_controllers()

        # Initialize history storage
        self.history_storage = HistoryStorage(self.config)
        self.logger.info("Initialized history storage")

        # Initialize API
        self.api = HydroFastAPI(
            self.sensors, self.controllers, self.config, self.outputs, self.log_handler
        )
        self.api.history_storage = self.history_storage

        # Initialize MQTT client
        await self._initialize_mqtt()

        self.logger.info("Hydroponic system initialized")

    # Add a method to update history with sensor data
    async def update_history(self):
        """Update history with current sensor data"""
        if not self.history_storage:
            return

        # Get current sensor readings
        data = {}

        # pH
        if "ph" in self.sensors:
            data["ph"] = await self.sensors["ph"].read_ph()

        # ORP
        if "orp" in self.sensors:
            data["orp"] = await self.sensors["orp"].read_orp()

        # EC
        if "ec" in self.sensors:
            data["ec"] = await self.sensors["ec"].read_ec()

        # Temperature (water)
        if "temperature" in self.sensors:
            data["water_temperature"] = await self.sensors[
                "temperature"
            ].read_temperature()

        # Environment (air temperature and humidity)
        if "environment" in self.sensors:
            temp, humidity = await self.sensors["environment"].read_measurement()
            data["air_temperature"] = temp
            data["humidity"] = humidity

        # Add data to history
        self.history_storage.add_data_point(data)

    async def start(self):
        """Start the hydroponic system"""
        self.logger.info("Starting hydroponic system...")

        # Start controllers
        for controller_id, controller in self.controllers.items():
            if not controller.running:
                asyncio.create_task(controller.run())
                self.logger.info(f"Started {controller_id} controller")

        # Start history update task
        history_update_interval = self.config.get("history", {}).get(
            "update_interval", 60
        )  # Default 60 seconds

        async def history_update_task():
            while True:
                await self.update_history()
                await asyncio.sleep(history_update_interval)

        asyncio.create_task(history_update_task())
        self.logger.info(f"Started history update task (interval: {history_update_interval}s)")

        # Start API server
        api_config = self.config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8000)

        # Create a config for uvicorn
        config = uvicorn.Config(self.api.app, host=host, port=port, log_level="info")

        # Create and start the server
        server = uvicorn.Server(config)
        await server.serve()

        self.logger.info(f"API server started at http://{host}:{port}")

    async def _initialize_mqtt(self):
        """Initialize MQTT client"""
        try:
            mqtt_config = self.config.get("mqtt", {})
            if mqtt_config and mqtt_config.get("enabled", False):
                host = mqtt_config.get("host", "localhost")
                port = mqtt_config.get("port", 1883)
                username = mqtt_config.get("username")
                password = mqtt_config.get("password")

                self.mqtt_client = MQTTPublisher(
                    host=host, port=port, username=username, password=password
                )

                # Start MQTT publisher task without waiting for connection
                # It will handle connection attempts internally
                mqtt_task = asyncio.create_task(self.mqtt_client.run(self))
                self.tasks.append(mqtt_task)
                self.logger.info(f"MQTT client initialized (will connect to {host}:{port})")
            else:
                self.logger.warning("MQTT client disabled in configuration")
        except Exception as e:
            self.logger.error(f"Error initializing MQTT client: {e}")

    def cleanup(self):
        """Clean up resources"""
        self.logger.info("Cleaning up resources...")
        
        # Cancel all running tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Stop controllers first
        for controller_id, controller in self.controllers.items():
            try:
                controller.stop()
            except Exception as e:
                self.logger.error(f"Error stopping {controller_id} controller: {e}")
    
        # Save history data
        if self.history_storage:
            self.history_storage.save()
    
        # Clean up sensors
        for sensor_id, sensor in self.sensors.items():
            # Check if the sensor has a close method before calling it
            if hasattr(sensor, "close"):
                try:
                    sensor.close()
                    self.logger.info(f"Closed {sensor_id} sensor")
                except Exception as e:
                    self.logger.error(f"Error closing {sensor_id} sensor: {e}")
    
        # Clean up outputs
        if self.outputs:
            try:
                self.outputs.close()
            except Exception as e:
                self.logger.error(f"Error closing outputs: {e}")
    
        # Stop MQTT client
        if self.mqtt_client:
            try:
                self.mqtt_client.stop()
            except Exception as e:
                self.logger.error(f"Error stopping MQTT client: {e}")
    
        self.logger.info("Cleanup complete")

    async def _initialize_sensors(self):
        """Initialize all sensors"""
        # pH sensor
        try:
            ph_config = self.config.get("sensors", {}).get("ph", {})
            if ph_config:
                sck_pin = ph_config.get("sck_pin")
                data_read_pin = ph_config.get("data_read_pin")
                data_write_pin = ph_config.get("data_write_pin")  # Get write pin

                # Extract calibration data from the new structure
                calibration = ph_config.get("calibration", {})
                if (
                    "voltage_1" in calibration
                    and "ph_1" in calibration
                    and "voltage_2" in calibration
                    and "ph_2" in calibration
                ):
                    # Create calibration dictionary with voltage-to-pH mapping
                    cal_dict = {
                        float(calibration["voltage_1"]): float(calibration["ph_1"]),
                        float(calibration["voltage_2"]): float(calibration["ph_2"]),
                    }
                else:
                    cal_dict = {}

                # Create pH sensor with separate read/write pins
                self.sensors["ph"] = PHSensor(
                    sck_pin, data_read_pin, data_write_pin, cal_dict
                )
                self.logger.info("Initializing pH sensor...")

                # Add timeout for sensor initialization
                try:
                    init_task = asyncio.create_task(self.sensors["ph"].initialize())
                    await asyncio.wait_for(init_task, timeout=2.0)  # 2 second timeout
                    self.logger.info("Initialized pH sensor")
                except asyncio.TimeoutError:
                    self.logger.error("Warning: pH sensor initialization timed out")
                except Exception as e:
                    self.logger.error(f"Error initializing pH sensor: {e}")
                    # Keep the sensor in the dictionary but mark it as not initialized
                    self.sensors["ph"].initialized = False
        except Exception as e:
            self.logger.error(f"Error setting up pH sensor: {e}")

        # ORP sensor
        try:
            orp_config = self.config.get("sensors", {}).get("orp", {})
            if orp_config:
                sck_pin = orp_config.get("sck_pin")
                data_read_pin = orp_config.get("data_read_pin")
                data_write_pin = orp_config.get("data_write_pin")  # Get write pin
                offset = orp_config.get("offset", 0)

                # Create ORP sensor with separate read/write pins
                self.sensors["orp"] = ORPSensor(
                    sck_pin, data_read_pin, data_write_pin, offset
                )
                self.logger.info("Initializing ORP sensor...")

                try:
                    init_task = asyncio.create_task(self.sensors["orp"].initialize())
                    await asyncio.wait_for(init_task, timeout=2.0)  # 2 second timeout
                    self.logger.info("Initialized ORP sensor")
                except asyncio.TimeoutError:
                    self.logger.error("Warning: ORP sensor initialization timed out")
                except Exception as e:
                    self.logger.error(f"Error initializing ORP sensor: {e}")
                    self.sensors["orp"].initialized = False
        except Exception as e:
            self.logger.error(f"Error setting up ORP sensor: {e}")

        # EC sensor
        try:
            ec_config = self.config.get("sensors", {}).get("ec", {})
            if ec_config:
                sck_pin = ec_config.get("sck_pin")
                data_read_pin = ec_config.get("data_read_pin")
                data_write_pin = ec_config.get("data_write_pin")
                pwm_pin = ec_config.get("pwm_pin")
                range_pin = ec_config.get("range_pin")
                calibration_pin = ec_config.get("calibration_pin")
                selection_pin = ec_config.get("selection_pin")
                k_value = ec_config.get("k_value", 1.0)

                # Get calibration factor
                calibration = ec_config.get("calibration", {})
                calibration_factor = calibration.get("factor", 1.0)

                # Create EC sensor with all required pins
                self.sensors["ec"] = ECSensor(
                    sck_pin,
                    data_read_pin,
                    data_write_pin,
                    pwm_pin,
                    range_pin,
                    calibration_pin,
                    selection_pin,
                    k_value=k_value,
                )
                self.logger.info("Initializing EC sensor...")

                # Set calibration factor
                self.sensors["ec"].set_calibration_factor(calibration_factor)

                try:
                    init_task = asyncio.create_task(self.sensors["ec"].initialize())
                    await asyncio.wait_for(init_task, timeout=2.0)  # 2 second timeout
                    self.logger.info("Initialized EC sensor")
                except asyncio.TimeoutError:
                    self.logger.error("Warning: EC sensor initialization timed out")
                except Exception as e:
                    self.logger.error(f"Error initializing EC sensor: {e}")
                    self.sensors["ec"].initialized = False
        except Exception as e:
            self.logger.error(f"Error setting up EC sensor: {e}")

        # Temperature sensor
        try:
            temp_config = self.config.get("sensors", {}).get("temperature", {})
            if temp_config:
                sensor_id = temp_config.get("ds18b20_id")

                self.sensors["temperature"] = DS18B20(sensor_id)
                self.logger.info("Initializing temperature sensor...")

                try:
                    init_task = asyncio.create_task(
                        self.sensors["temperature"].initialize()
                    )
                    await asyncio.wait_for(init_task, timeout=2.0)  # 2 second timeout
                    self.logger.info("Initialized temperature sensor")

                    # Set temperature for EC sensor
                    if (
                        "ec" in self.sensors
                        and hasattr(self.sensors["ec"], "initialized")
                        and self.sensors["ec"].initialized
                    ):
                        try:
                            temp = await self.sensors["temperature"].read_temperature()
                            if temp is not None:
                                self.sensors["ec"].set_temperature(temp)
                        except Exception as e:
                            self.logger.warning(f"Error reading temperature for EC sensor: {e}")
                except asyncio.TimeoutError:
                    self.logger.error("Warning: Temperature sensor initialization timed out")
                except Exception as e:
                    self.logger.error(f"Error initializing temperature sensor: {e}")
                    self.sensors["temperature"].initialized = False
        except Exception as e:
            self.logger.error(f"Error setting up temperature sensor: {e}")

        # Environment sensor
        try:
            env_config = self.config.get("sensors", {}).get("environment", {})
            if env_config:
                i2c_bus = env_config.get("i2c_bus", 1)

                self.sensors["environment"] = SHT41(i2c_bus)
                self.logger.info("Initializing environment sensor...")

                try:
                    init_task = asyncio.create_task(
                        self.sensors["environment"].initialize()
                    )
                    await asyncio.wait_for(init_task, timeout=2.0)  # 2 second timeout
                    self.logger.info("Initialized environment sensor")
                except asyncio.TimeoutError:
                    self.logger.error("Warning: Environment sensor initialization timed out")
                except Exception as e:
                    self.logger.error(f"Error initializing environment sensor: {e}")
                    self.sensors["environment"].initialized = False
        except Exception as e:
            self.logger.error(f"Error setting up environment sensor: {e}")

        # Generic analog sensors
        try:
            generic_sensors_config = self.config.get("sensors", {}).get("generic_analog", {})
            for sensor_id, sensor_config in generic_sensors_config.items():
                if not sensor_config.get("enabled", True):
                    continue
                    
                sck_pin = sensor_config.get("sck_pin")
                data_read_pin = sensor_config.get("data_read_pin")
                data_write_pin = sensor_config.get("data_write_pin")
                name = sensor_config.get("name", sensor_id)
                unit = sensor_config.get("unit", "")
                
                # Get PGA and speed settings if provided
                pga_setting = sensor_config.get("pga", 0)  # Default to PGA_1
                speed_setting = sensor_config.get("speed", 0)  # Default to 10Hz
                
                # Create the sensor
                self.sensors[sensor_id] = GenericAnalogSensor(
                    sck_pin=sck_pin, 
                    data_read_pin=data_read_pin, 
                    data_write_pin=data_write_pin,
                    name=name, 
                    unit=unit,
                    pga=pga_setting,
                    speed=speed_setting
                )
                
                # Set up calibration if provided
                calibration = sensor_config.get("calibration", {})
                if calibration:
                    # Convert string keys to int for calibration points
                    cal_points = {int(k): float(v) for k, v in calibration.items()}
                    self.sensors[sensor_id].set_calibration(cal_points)
                
                self.logger.info(f"Initializing generic analog sensor: {name}")
                
                try:
                    init_success = await self.sensors[sensor_id].initialize()
                    if init_success:
                        self.logger.info(f"Initialized generic analog sensor: {name}")
                    else:
                        self.logger.error(f"Failed to initialize generic analog sensor: {name}")
                except Exception as e:
                    self.logger.error(f"Error initializing {name} sensor: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error setting up generic analog sensors: {e}")

    def _initialize_controllers(self):
        """Initialize all controllers"""
        # pH controller
        ph_config = self.config.get("controllers", {}).get("ph", {})
        if ph_config and ph_config.get("enabled", False) and "ph" in self.sensors:
            target = ph_config.get("target", 6.0)
            tolerance = ph_config.get("tolerance", 0.2)
            check_interval = ph_config.get("check_interval", 60)
            acid_pump_pin = ph_config.get("acid_pump_pin")
            base_pump_pin = ph_config.get("base_pump_pin")

            self.controllers["ph"] = PHController(
                self.sensors["ph"],
                acid_pump_pin,
                base_pump_pin,
                self.outputs,
                target_ph=target,
                tolerance=tolerance,
                check_interval=check_interval,
            )
            self.logger.info("Initialized pH controller")

        # ORP controller
        orp_config = self.config.get("controllers", {}).get("orp", {})
        if orp_config and orp_config.get("enabled", False) and "orp" in self.sensors:
            target = orp_config.get("target", 650)
            tolerance = orp_config.get("tolerance", 20)
            check_interval = orp_config.get("check_interval", 60)
            increase_pump_pin = orp_config.get("increase_pump_pin")
            decrease_pump_pin = orp_config.get("decrease_pump_pin")

            self.controllers["orp"] = ORPController(
                self.sensors["orp"],
                increase_pump_pin,
                decrease_pump_pin,
                self.outputs,
                target_orp=target,
                tolerance=tolerance,
                check_interval=check_interval,
            )
            self.logger.info("Initialized ORP controller")

        # EC controller
        ec_config = self.config.get("controllers", {}).get("ec", {})
        if ec_config and ec_config.get("enabled", False) and "ec" in self.sensors:
            target = ec_config.get("target", 1500)
            tolerance = ec_config.get("tolerance", 100)
            check_interval = ec_config.get("check_interval", 60)
            nutrient_pump_pin = ec_config.get("nutrient_pump_pin")
            water_pump_pin = ec_config.get("water_pump_pin")

            self.controllers["ec"] = ECController(
                self.sensors["ec"],
                nutrient_pump_pin,
                water_pump_pin,
                self.outputs,
                target_ec=target,
                tolerance=tolerance,
                check_interval=check_interval,
            )
            self.logger.info("Initialized EC controller")

        # Add pump timer controller initialization
        try:
            pump_timer_config = self.config.get("controllers", {}).get("pump_timer", {})
            if pump_timer_config and pump_timer_config.get("enabled", False):
                if "temperature" in self.sensors:
                    pump_pin = pump_timer_config.get("pump_pin")
                    min_run_time = pump_timer_config.get("min_run_time", 15)
                    max_run_time = pump_timer_config.get("max_run_time", 120)
                    temp_check_delay = pump_timer_config.get("temp_check_delay", 5)
                    check_interval = pump_timer_config.get("check_interval", 60)
                    
                    # Convert string keys to integers for temperature thresholds
                    temp_thresholds = pump_timer_config.get("temp_thresholds", {})
                    temp_thresholds = {int(k): v for k, v in temp_thresholds.items()}
                    
                    start_hour = pump_timer_config.get("start_hour", 8)
                    end_hour = pump_timer_config.get("end_hour", 20)
                    
                    self.controllers["pump_timer"] = PumpTimerController(
                        self.sensors["temperature"],
                        pump_pin,
                        self.outputs,
                        min_run_time=min_run_time,
                        max_run_time=max_run_time,
                        temp_check_delay=temp_check_delay,
                        check_interval=check_interval,
                        temp_thresholds=temp_thresholds,
                        start_hour=start_hour,
                        end_hour=end_hour
                    )
                    self.logger.info("Initialized pump timer controller")
                else:
                    self.logger.warning("Cannot initialize pump timer controller: temperature sensor not found")
        except Exception as e:
            self.logger.error(f"Error initializing pump timer controller: {e}")

async def main():
    """Main entry point"""
    # Create hydroponic system
    system = HydroponicSystem()

    # Handle signals for graceful shutdown
    loop = asyncio.get_running_loop()
    
    def signal_handler():
        # First clean up resources
        system.cleanup()
        # Then stop the loop
        loop.stop()
        
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)

    try:
        # Initialize and start the system
        await system.initialize()
        await system.start()
    except Exception as e:
        print(f"Error: {e}")
        system.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
