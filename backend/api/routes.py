from aiohttp import web
import json

class HydroAPI:
    """
    API for the hydroponic system
    """
    def __init__(self, app, sensors, controllers, config):
        """
        Initialize API
        
        Args:
            app: aiohttp web application
            sensors: Dictionary of sensor instances
            controllers: Dictionary of controller instances
            config: Config instance
        """
        self.app = app
        self.sensors = sensors
        self.controllers = controllers
        self.config = config
        
        # Setup routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup API routes"""
        # Sensor routes
        self.app.router.add_get('/api/sensors', self.get_all_sensors)
        self.app.router.add_get('/api/sensors/{sensor_id}', self.get_sensor)
        
        # Controller routes
        self.app.router.add_get('/api/controllers', self.get_all_controllers)
        self.app.router.add_get('/api/controllers/{controller_id}', self.get_controller)
        self.app.router.add_post('/api/controllers/{controller_id}/target', self.set_controller_target)
        self.app.router.add_post('/api/controllers/{controller_id}/start', self.start_controller)
        self.app.router.add_post('/api/controllers/{controller_id}/stop', self.stop_controller)
        
        # Configuration routes
        self.app.router.add_get('/api/config', self.get_config)
        self.app.router.add_post('/api/config', self.update_config)
        
        # Calibration routes
        self.app.router.add_post('/api/calibrate/ph', self.calibrate_ph)
        self.app.router.add_post('/api/calibrate/orp', self.calibrate_orp)
        self.app.router.add_post('/api/calibrate/ec', self.calibrate_ec)
        
    async def get_all_sensors(self, request):
        """Get all sensor readings"""
        try:
            data = {}
            
            # pH
            if 'ph' in self.sensors:
                data['ph'] = await self.sensors['ph'].read_ph()
                
            # ORP
            if 'orp' in self.sensors:
                data['orp'] = await self.sensors['orp'].read_orp()
                
            # EC
            if 'ec' in self.sensors:
                data['ec'] = await self.sensors['ec'].read_ec()
                
            # Temperature (water)
            if 'temperature' in self.sensors:
                data['water_temperature'] = await self.sensors['temperature'].read_temperature()
                
            # Environment (air temperature and humidity)
            if 'environment' in self.sensors:
                temp, humidity = await self.sensors['environment'].read_measurement()
                data['air_temperature'] = temp
                data['humidity'] = humidity
                
            return web.json_response(data)
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_sensor(self, request):
        """Get specific sensor reading"""
        sensor_id = request.match_info['sensor_id']
        
        try:
            if sensor_id not in self.sensors:
                return web.json_response({'error': f'Sensor {sensor_id} not found'}, status=404)
                
            if sensor_id == 'ph':
                value = await self.sensors['ph'].read_ph()
            elif sensor_id == 'orp':
                value = await self.sensors['orp'].read_orp()
            elif sensor_id == 'ec':
                value = await self.sensors['ec'].read_ec()
            elif sensor_id == 'temperature':
                value = await self.sensors['temperature'].read_temperature()
            elif sensor_id == 'environment':
                temp, humidity = await self.sensors['environment'].read_measurement()
                value = {'temperature': temp, 'humidity': humidity}
            else:
                return web.json_response({'error': f'Unknown sensor {sensor_id}'}, status=400)
                
            return web.json_response({sensor_id: value})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_all_controllers(self, request):
        """Get all controller statuses"""
        try:
            data = {}
            
            for controller_id, controller in self.controllers.items():
                data[controller_id] = controller.get_status()
                
            return web.json_response(data)
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_controller(self, request):
        """Get specific controller status"""
        controller_id = request.match_info['controller_id']
        
        try:
            if controller_id not in self.controllers:
                return web.json_response({'error': f'Controller {controller_id} not found'}, status=404)
                
            status = self.controllers[controller_id].get_status()
            return web.json_response({controller_id: status})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def set_controller_target(self, request):
        """Set controller target value"""
        controller_id = request.match_info['controller_id']
        
        try:
            if controller_id not in self.controllers:
                return web.json_response({'error': f'Controller {controller_id} not found'}, status=404)
                
            data = await request.json()
            
            if 'target' not in data:
                return web.json_response({'error': 'Target value not provided'}, status=400)
                
            target = data['target']
            tolerance = data.get('tolerance')
            
            self.controllers[controller_id].set_target(target, tolerance)
            
            # Update configuration
            controller_config = self.config.get('controllers', {}).get(controller_id, {})
            controller_config['target'] = target
            if tolerance is not None:
                controller_config['tolerance'] = tolerance
            self.config.set('controllers', controller_id, controller_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def start_controller(self, request):
        """Start a controller"""
        controller_id = request.match_info['controller_id']
        
        try:
            if controller_id not in self.controllers:
                return web.json_response({'error': f'Controller {controller_id} not found'}, status=404)
                
            # Start the controller task
            controller = self.controllers[controller_id]
            if not controller.running:
                self.app.loop.create_task(controller.run())
                
            # Update configuration
            controller_config = self.config.get('controllers', {}).get(controller_id, {})
            controller_config['enabled'] = True
            self.config.set('controllers', controller_id, controller_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def stop_controller(self, request):
        """Stop a controller"""
        controller_id = request.match_info['controller_id']
        
        try:
            if controller_id not in self.controllers:
                return web.json_response({'error': f'Controller {controller_id} not found'}, status=404)
                
            # Stop the controller
            controller = self.controllers[controller_id]
            controller.stop()
            
            # Update configuration
            controller_config = self.config.get('controllers', {}).get(controller_id, {})
            controller_config['enabled'] = False
            self.config.set('controllers', controller_id, controller_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_config(self, request):
        """Get configuration"""
        try:
            return web.json_response(self.config.get())
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def update_config(self, request):
        """Update configuration"""
        try:
            data = await request.json()
            
            # Update configuration sections
            for section, section_data in data.items():
                if isinstance(section_data, dict):
                    for key, value in section_data.items():
                        self.config.set(section, key, value)
                        
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def calibrate_ph(self, request):
        """Calibrate pH sensor"""
        try:
            data = await request.json()
            
            if 'voltage' not in data or 'ph' not in data:
                return web.json_response({'error': 'Voltage and pH values required'}, status=400)
                
            voltage = float(data['voltage'])
            ph = float(data['ph'])
            
            # Calibrate sensor
            self.sensors['ph'].calibrate(voltage, ph)
            
            # Update configuration
            ph_config = self.config.get('sensors', {}).get('ph', {})
            calibration = ph_config.get('calibration', {})
            calibration[str(voltage)] = ph
            ph_config['calibration'] = calibration
            self.config.set('sensors', 'ph', ph_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def calibrate_orp(self, request):
        """Calibrate ORP sensor"""
        try:
            data = await request.json()
            
            if 'orp' not in data:
                return web.json_response({'error': 'ORP value required'}, status=400)
                
            orp = float(data['orp'])
            
            # Calibrate sensor
            self.sensors['orp'].calibrate(orp)
            
            # Update configuration
            orp_config = self.config.get('sensors', {}).get('orp', {})
            orp_config['offset'] = self.sensors['orp'].offset
            self.config.set('sensors', 'orp', orp_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)
            
    async def calibrate_ec(self, request):
        """Calibrate EC sensor"""
        try:
            data = await request.json()
            
            if 'ec' not in data:
                return web.json_response({'error': 'EC value required'}, status=400)
                
            ec = float(data['ec'])
            
            # Calibrate sensor
            self.sensors['ec'].calibrate(ec)
            
            # Update configuration
            ec_config = self.config.get('sensors', {}).get('ec', {})
            ec_config['calibration_factor'] = self.sensors['ec'].calibration_factor
            self.config.set('sensors', 'ec', ec_config)
            
            return web.json_response({'success': True})
            
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)