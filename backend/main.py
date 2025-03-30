import asyncio
from aiohttp import web
import signal
import sys

# Import configuration
from config import Config

# Import sensors
from sensors.ph_sensor import PHSensor
from sensors.orp_sensor import ORPSensor
from sensors.ec_sensor import ECSensor
from sensors.ds18b20 import DS18B20
from sensors.sht41 import SHT41

# Import controllers
from controllers.ph_controller import PHController
from controllers.orp_controller import ORPController
from controllers.ec_controller import ECController

# Import outputs
from outputs.mosfet_control import MOSFETControl

# Import API
from api.routes import HydroAPI

class HydroponicSystem:
    """
    Main hydroponic system application
    """
    def __init__(self):
        """Initialize the hydroponic system"""
        self.config = Config()
        self.sensors = {}
        self.controllers = {}
        self.outputs = None
        self.app = web.Application()
        self.api = None
        
    async def initialize(self):
        """Initialize all components"""
        print("Initializing hydroponic system...")
        
        # Initialize outputs
        mosfet_pins = self.config.get('outputs', {}).get('mosfet_pins', [])
        self.outputs = MOSFETControl(mosfet_pins)
        print(f"Initialized {len(mosfet_pins)} MOSFET outputs")
        
        # Initialize sensors
        await self._initialize_sensors()
        
        # Initialize controllers
        self._initialize_controllers()
        
        # Initialize API
        self.api = HydroAPI(self.app, self.sensors, self.controllers, self.config)
        
        print("Hydroponic system initialized")
        
    async def _initialize_sensors(self):
        """Initialize all sensors"""
        # pH sensor
        ph_config = self.config.get('sensors', {}).get('ph', {})
        if ph_config:
            sck_pin = ph_config.get('sck_pin')
            data_pin = ph_config.get('data_pin')
            calibration = {float(k): float(v) for k, v in ph_config.get('calibration', {}).items()}
            
            self.sensors['ph'] = PHSensor(sck_pin, data_pin, calibration)
            await self.sensors['ph'].initialize()
            print("Initialized pH sensor")
            
        # ORP sensor
        orp_config = self.config.get('sensors', {}).get('orp', {})
        if orp_config:
            sck_pin = orp_config.get('sck_pin')
            data_pin = orp_config.get('data_pin')
            offset = orp_config.get('offset', 0)
            
            self.sensors['orp'] = ORPSensor(sck_pin, data_pin, offset)
            await self.sensors['orp'].initialize()
            print("Initialized ORP sensor")
            
        # EC sensor
        ec_config = self.config.get('sensors', {}).get('ec', {})
        if ec_config:
            sck_pin = ec_config.get('sck_pin')
            data_pin = ec_config.get('data_pin')
            pwm_pin = ec_config.get('pwm_pin')
            k_value = ec_config.get('k_value', 1.0)
            
            self.sensors['ec'] = ECSensor(sck_pin, data_pin, pwm_pin, k_value=k_value)
            await self.sensors['ec'].initialize()
            print("Initialized EC sensor")
            
        # Temperature sensor
        temp_config = self.config.get('sensors', {}).get('temperature', {})
        if temp_config:
            sensor_id = temp_config.get('ds18b20_id')
            
            self.sensors['temperature'] = DS18B20(sensor_id)
            await self.sensors['temperature'].initialize()
            print("Initialized temperature sensor")
            
            # Set temperature for EC sensor
            if 'ec' in self.sensors and 'temperature' in self.sensors:
                temp = await self.sensors['temperature'].read_temperature()
                self.sensors['ec'].set_temperature(temp)
                
        # Environment sensor
        env_config = self.config.get('sensors', {}).get('environment', {})
        if env_config:
            i2c_bus = env_config.get('i2c_bus', 1)
            
            self.sensors['environment'] = SHT41(i2c_bus)
            await self.sensors['environment'].initialize()
            print("Initialized environment sensor")
            
    def _initialize_controllers(self):
        """Initialize all controllers"""
        # pH controller
        ph_config = self.config.get('controllers', {}).get('ph', {})
        if ph_config and ph_config.get('enabled', False) and 'ph' in self.sensors:
            target = ph_config.get('target', 6.0)
            tolerance = ph_config.get('tolerance', 0.2)
            check_interval = ph_config.get('check_interval', 60)
            acid_pump_pin = ph_config.get('acid_pump_pin')
            base_pump_pin = ph_config.get('base_pump_pin')
            
            self.controllers['ph'] = PHController(
                self.sensors['ph'],
                acid_pump_pin,
                base_pump_pin,
                self.outputs,
                target_ph=target,
                tolerance=tolerance,
                check_interval=check_interval
            )
            print("Initialized pH controller")
            
        # ORP controller
        orp_config = self.config.get('controllers', {}).get('orp', {})
        if orp_config and orp_config.get('enabled', False) and 'orp' in self.sensors:
            target = orp_config.get('target', 650)
            tolerance = orp_config.get('tolerance', 20)
            check_interval = orp_config.get('check_interval', 60)
            increase_pump_pin = orp_config.get('increase_pump_pin')
            decrease_pump_pin = orp_config.get('decrease_pump_pin')
            
            self.controllers['orp'] = ORPController(
                self.sensors['orp'],
                increase_pump_pin,
                decrease_pump_pin,
                self.outputs,
                target_orp=target,
                tolerance=tolerance,
                check_interval=check_interval
            )
            print("Initialized ORP controller")
            
        # EC controller
        ec_config = self.config.get('controllers', {}).get('ec', {})
        if ec_config and ec_config.get('enabled', False) and 'ec' in self.sensors:
            target = ec_config.get('target', 1500)
            tolerance = ec_config.get('tolerance', 100)
            check_interval = ec_config.get('check_interval', 60)
            nutrient_pump_pin = ec_config.get('nutrient_pump_pin')
            water_pump_pin = ec_config.get('water_pump_pin')
            
            self.controllers['ec'] = ECController(
                self.sensors['ec'],
                nutrient_pump_pin,
                water_pump_pin,
                self.outputs,
                target_ec=target,
                tolerance=tolerance,
                check_interval=check_interval
            )
            print("Initialized EC controller")
            
    async def start(self):
        """Start the hydroponic system"""
        print("Starting hydroponic system...")
        
        # Start controllers
        for controller_id, controller in self.controllers.items():
            if not controller.running:
                self.app.loop.create_task(controller.run())
                print(f"Started {controller_id} controller")
                
        # Start API server
        api_config = self.config.get('api', {})
        host = api_config.get('host', '0.0.0.0')
        port = api_config.get('port', 8000)
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()
        
        print(f"API server started at http://{host}:{port}")
        
        # Keep the application running
        while True:
            await asyncio.sleep(1)
            
    def cleanup(self):
        """Clean up resources"""
        print("Cleaning up resources...")
        
        # Stop controllers
        for controller_id, controller in self.controllers.items():
            controller.stop()
            
        # Clean up sensors
        for sensor_id, sensor in self.sensors.items():
            sensor.close()
            
        # Clean up outputs
        if self.outputs:
            self.outputs.close()
            
        print("Cleanup complete")
        
async def main():
    """Main entry point"""
    # Create hydroponic system
    system = HydroponicSystem()
    
    # Handle signals for graceful shutdown
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        system.cleanup()
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