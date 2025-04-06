import asyncio
import json
from aiomqtt import Client, MqttError
import time
import logging

class MQTTPublisher:
    """
    MQTT client for publishing hydroponic system data
    """

    # Get a logger for this module
    logger = logging.getLogger(__name__)

    def __init__(
        self, host="localhost", port=1883, client_id=None, username=None, password=None
    ):
        """
        Initialize MQTT publisher

        Args:
            host: MQTT broker hostname or IP
            port: MQTT broker port
            client_id: Client identifier (defaults to hydro_python_<timestamp>)
            username: Username for authentication (optional)
            password: Password for authentication (optional)
        """
        self.host = host
        self.port = port
        self.client_id = client_id or f"hydro_python_{int(time.time())}"
        self.username = username
        self.password = password

        self.client = None
        self.connected = False
        self.running = False
        self.publish_interval = 10  # seconds
        self.reconnect_interval = 30  # seconds

        # Base topic
        self.base_topic = "hydroponics"

    async def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = Client(
                hostname=self.host,
                port=self.port,
                identifier=self.client_id,
                username=self.username,
                password=self.password,
            )
            await self.client.__aenter__()
            self.connected = True
            self.logger.info(f"Connected to MQTT broker at {self.host}:{self.port}")
            return True
        except MqttError as e:
            self.logger.warning(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error connecting to MQTT broker: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                self.logger.warning("Disconnected from MQTT broker")
            except Exception as e:
                self.logger.error(f"Error disconnecting from MQTT broker: {e}")
        self.connected = False

    async def publish_message(self, topic, payload):
        """
        Publish a message to a topic

        Args:
            topic: Topic to publish to (will be prefixed with base_topic)
            payload: Message payload (will be converted to JSON)
        """
        if not self.connected or not self.client:
            self.logger.warning("Not connected to MQTT broker")
            return False

        full_topic = f"{self.base_topic}/{topic}"

        try:
            # Convert payload to JSON string
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)

            await self.client.publish(full_topic, payload)
            return True
        except Exception as e:
            self.logger.error(f"Error publishing to {full_topic}: {e}")
            self.connected = False  # Mark as disconnected to trigger reconnect
            return False

    async def publish_sensor_data(self, sensors):
        """
        Publish sensor data

        Args:
            sensors: Dictionary of sensor objects
        """
        sensor_data = {}

        # pH sensor
        if "ph" in sensors:
            try:
                ph = await sensors["ph"].read_ph()
                if ph is not None:
                    sensor_data["ph"] = round(ph, 2)
            except Exception as e:
                self.logger.error(f"Error reading pH: {e}")

        # ORP sensor
        if "orp" in sensors:
            try:
                orp = await sensors["orp"].read_orp()
                if orp is not None:
                    sensor_data["orp"] = round(orp, 1)
            except Exception as e:
                self.logger.error(f"Error reading ORP: {e}")

        # EC sensor
        if "ec" in sensors:
            try:
                ec = await sensors["ec"].read_ec()
                if ec is not None:
                    sensor_data["ec"] = round(ec, 1)
            except Exception as e:
                self.logger.error(f"Error reading EC: {e}")

        # Temperature sensor
        if "temperature" in sensors:
            try:
                temp = await sensors["temperature"].read_temperature()
                if temp is not None:
                    sensor_data["water_temperature"] = round(temp, 1)
            except Exception as e:
                self.logger.error(f"Error reading water temperature: {e}")

        # Environment sensor
        if "environment" in sensors:
            try:
                temp, humidity = await sensors["environment"].read_measurement()
                if temp is not None:
                    sensor_data["air_temperature"] = round(temp, 1)
                if humidity is not None:
                    sensor_data["humidity"] = round(humidity, 1)
            except Exception as e:
                self.logger.error(f"Error reading environment data: {e}")

        # Publish sensor data if we have any
        if sensor_data:
            await self.publish_message("sensors", sensor_data)

    async def publish_controller_data(self, controllers):
        """
        Publish controller data

        Args:
            controllers: Dictionary of controller objects
        """
        controller_data = {}

        for controller_id, controller in controllers.items():
            try:
                status = controller.get_status()
                controller_data[controller_id] = status
            except Exception as e:
                self.logger.error(f"Error getting status for {controller_id} controller: {e}")

        # Publish controller data if we have any
        if controller_data:
            await self.publish_message("controllers", controller_data)

    async def publish_output_status(self, outputs):
        """
        Publish output status

        Args:
            outputs: MOSFETControl object
        """
        try:
            output_states = outputs.get_all_states()
            await self.publish_message("outputs", output_states)
        except Exception as e:
            self.logger.error(f"Error publishing output status: {e}")

    async def run(self, system):
        """
        Run the MQTT publisher loop

        Args:
            system: HydroponicSystem instance
        """
        self.running = True

        while self.running:
            try:
                # Ensure we're connected
                if not self.connected:
                    connected = await self.connect()
                    if not connected:
                        # If connection failed, wait before retrying
                        self.logger.info(
                            f"Will retry connecting to MQTT broker in {self.reconnect_interval} seconds"
                        )
                        await asyncio.sleep(self.reconnect_interval)
                        continue

                # Publish sensor data
                await self.publish_sensor_data(system.sensors)

                # Publish controller data
                await self.publish_controller_data(system.controllers)

                # Publish output status
                await self.publish_output_status(system.outputs)

            except MqttError as e:
                self.logger.error(f"MQTT error: {e}")
                self.connected = False
                # Don't wait the full interval on connection error
                await asyncio.sleep(self.reconnect_interval)
                continue
            except Exception as e:
                self.logger.error(f"Error in MQTT publisher loop: {e}")
                # Try to reconnect on next iteration
                self.connected = False

            # Wait for next publish interval
            await asyncio.sleep(self.publish_interval)

    def stop(self):
        """Stop the MQTT publisher"""
        self.running = False
