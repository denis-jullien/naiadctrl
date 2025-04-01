from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any
import asyncio


class HydroFastAPI:
    """
    FastAPI implementation for the hydroponic system
    """

    def __init__(self, sensors, controllers, config, outputs):
        """
        Initialize API

        Args:
            sensors: Dictionary of sensor instances
            controllers: Dictionary of controller instances
            config: Config instance
        """
        self.app = FastAPI(title="Hydroponic System API")
        self.sensors = sensors
        self.controllers = controllers
        self.config = config
        self.outputs = outputs

        # Setup CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Allows all origins
            allow_credentials=True,
            allow_methods=["*"],  # Allows all methods
            allow_headers=["*"],  # Allows all headers
        )

        # Setup routes
        self.setup_routes()

    def setup_routes(self):
        """Setup API routes"""

        # Sensor routes
        @self.app.get("/api/sensors")
        async def get_all_sensors():
            try:
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
                    temp, humidity = await self.sensors[
                        "environment"
                    ].read_measurement()
                    data["air_temperature"] = temp
                    data["humidity"] = humidity

                return data

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/sensors/{sensor_id}")
        async def get_sensor(sensor_id: str):
            try:
                if sensor_id not in self.sensors:
                    raise HTTPException(
                        status_code=404, detail=f"Sensor {sensor_id} not found"
                    )

                if sensor_id == "ph":
                    value = await self.sensors["ph"].read_ph()
                elif sensor_id == "orp":
                    value = await self.sensors["orp"].read_orp()
                elif sensor_id == "ec":
                    value = await self.sensors["ec"].read_ec()
                elif sensor_id == "temperature":
                    value = await self.sensors["temperature"].read_temperature()
                elif sensor_id == "environment":
                    temp, humidity = await self.sensors[
                        "environment"
                    ].read_measurement()
                    value = {"temperature": temp, "humidity": humidity}
                else:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown sensor {sensor_id}"
                    )

                return {sensor_id: value}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        # Controller routes
        @self.app.get("/api/controllers")
        async def get_all_controllers():
            try:
                data = {}

                for controller_id, controller in self.controllers.items():
                    data[controller_id] = controller.get_status()

                return data

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/controllers/{controller_id}")
        async def get_controller(controller_id: str):
            try:
                if controller_id not in self.controllers:
                    raise HTTPException(
                        status_code=404, detail=f"Controller {controller_id} not found"
                    )

                status = self.controllers[controller_id].get_status()
                return {controller_id: status}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        class TargetValue(BaseModel):
            target: float

        @self.app.post("/api/controllers/{controller_id}/target")
        async def set_controller_target(controller_id: str, data: TargetValue):
            try:
                if controller_id not in self.controllers:
                    raise HTTPException(
                        status_code=404, detail=f"Controller {controller_id} not found"
                    )

                # Set target value
                controller = self.controllers[controller_id]

                if controller_id == "ph":
                    controller.set_target_ph(data.target)
                elif controller_id == "orp":
                    controller.set_target_orp(data.target)
                elif controller_id == "ec":
                    controller.set_target_ec(data.target)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown controller type {controller_id}",
                    )

                # Update configuration
                controller_config = self.config.get("controllers", {}).get(
                    controller_id, {}
                )
                controller_config["target"] = data.target
                self.config.set("controllers", controller_id, controller_config)

                return {"success": True}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/controllers/{controller_id}/start")
        async def start_controller(
            controller_id: str, background_tasks: BackgroundTasks
        ):
            try:
                if controller_id not in self.controllers:
                    raise HTTPException(
                        status_code=404, detail=f"Controller {controller_id} not found"
                    )

                # Start the controller task
                controller = self.controllers[controller_id]
                if not controller.running:
                    background_tasks.add_task(controller.run)

                # Update configuration
                controller_config = self.config.get("controllers", {}).get(
                    controller_id, {}
                )
                controller_config["enabled"] = True
                self.config.set("controllers", controller_id, controller_config)

                return {"success": True}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/controllers/{controller_id}/stop")
        async def stop_controller(controller_id: str):
            try:
                if controller_id not in self.controllers:
                    raise HTTPException(
                        status_code=404, detail=f"Controller {controller_id} not found"
                    )

                # Stop the controller
                controller = self.controllers[controller_id]
                controller.stop()

                # Update configuration
                controller_config = self.config.get("controllers", {}).get(
                    controller_id, {}
                )
                controller_config["enabled"] = False
                self.config.set("controllers", controller_id, controller_config)

                return {"success": True}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        # Configuration routes
        @self.app.get("/api/config")
        async def get_config():
            try:
                return self.config.get()

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        class ConfigUpdate(BaseModel):
            data: Dict[str, Any]

        @self.app.post("/api/config")
        async def update_config(data: Dict[str, Any]):
            try:
                # Update configuration sections
                for section, section_data in data.items():
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            self.config.set(section, key, value)

                return {"success": True}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # Calibration routes
        class PHCalibration(BaseModel):
            voltage_1: float
            ph_1: float
            voltage_2: float
            ph_2: float

        @self.app.post("/api/calibrate/ph")
        async def calibrate_ph(data: PHCalibration):
            try:
                # Update pH calibration in config
                ph_config = self.config.get("sensors", {}).get("ph", {})
                if not ph_config:
                    ph_config = {}

                if "calibration" not in ph_config:
                    ph_config["calibration"] = {}

                ph_config["calibration"]["voltage_1"] = data.voltage_1
                ph_config["calibration"]["ph_1"] = data.ph_1
                ph_config["calibration"]["voltage_2"] = data.voltage_2
                ph_config["calibration"]["ph_2"] = data.ph_2

                self.config.set("sensors", "ph", ph_config)

                # Update pH sensor calibration
                if "ph" in self.sensors:
                    self.sensors["ph"].set_calibration(
                        {data.voltage_1: data.ph_1, data.voltage_2: data.ph_2}
                    )

                return {"success": True}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        class ORPCalibration(BaseModel):
            offset: float

        @self.app.post("/api/calibrate/orp")
        async def calibrate_orp(data: ORPCalibration):
            try:
                # Update ORP calibration in config
                orp_config = self.config.get("sensors", {}).get("orp", {})
                if not orp_config:
                    orp_config = {}

                orp_config["offset"] = data.offset

                self.config.set("sensors", "orp", orp_config)

                # Update ORP sensor calibration
                if "orp" in self.sensors:
                    self.sensors["orp"].set_offset(data.offset)

                return {"success": True}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        class ECCalibration(BaseModel):
            factor: float

        @self.app.post("/api/calibrate/ec")
        async def calibrate_ec(data: ECCalibration):
            try:
                # Update EC calibration in config
                ec_config = self.config.get("sensors", {}).get("ec", {})
                if not ec_config:
                    ec_config = {}

                if "calibration" not in ec_config:
                    ec_config["calibration"] = {}

                ec_config["calibration"]["factor"] = data.factor

                self.config.set("sensors", "ec", ec_config)

                # Update EC sensor calibration
                if "ec" in self.sensors:
                    self.sensors["ec"].set_calibration_factor(data.factor)

                return {"success": True}

            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))

        # MOSFET test routes
        @self.app.post("/api/outputs/test")
        async def test_output(data: dict, background_tasks: BackgroundTasks):
            try:
                pin = data.get("pin")
                state = data.get("state", False)
                duration = data.get("duration", 1.0)  # Default 1 second

                if pin is None:
                    raise HTTPException(
                        status_code=400, detail="Pin number is required"
                    )

                if not self.outputs:
                    raise HTTPException(
                        status_code=500, detail="Output controller not initialized"
                    )

                # Set the output state
                self.outputs.set_output(pin, state)

                # If duration is provided, schedule turning it off after the duration
                if state and duration > 0:

                    async def turn_off_after_delay():
                        await asyncio.sleep(duration)
                        self.outputs.set_output(pin, False)

                    background_tasks.add_task(turn_off_after_delay)

                return {"success": True, "pin": pin, "state": state}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/api/outputs")
        async def get_outputs():
            # try:
            if not self.outputs:
                raise HTTPException(
                    status_code=500, detail="Output controller not initialized"
                )

            # Get the configured pins from config
            mosfet_pins = self.config.get("outputs", {}).get("mosfet_pins", [])

            # Get the current state of each pin
            output_states = {}
            for pin in mosfet_pins:
                output_states[pin] = self.outputs.get_state(pin)

            return {"pins": mosfet_pins, "states": output_states}

            # except Exception as e:
            #     if isinstance(e, HTTPException):
            #         raise e
            #     raise HTTPException(status_code=500, detail=str(e))

            # Add this to the existing HydroFastAPI class

        # History routes
        @self.app.get("/api/history")
        async def get_history(limit: int = None):
            try:
                if not hasattr(self, "history_storage"):
                    raise HTTPException(
                        status_code=500, detail="History storage not initialized"
                    )

                history_data = self.history_storage.get_history(limit)
                return history_data

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/api/history")
        async def clear_history():
            try:
                if not hasattr(self, "history_storage"):
                    raise HTTPException(
                        status_code=500, detail="History storage not initialized"
                    )

                # Clear all history data
                for key in self.history_storage.history:
                    self.history_storage.history[key].clear()

                # Save empty history
                self.history_storage.save()

                return {"success": True}

            except Exception as e:
                if isinstance(e, HTTPException):
                    raise e
                raise HTTPException(status_code=500, detail=str(e))
