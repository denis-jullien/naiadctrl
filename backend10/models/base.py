from typing import List, Optional, Dict, Any
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, JSON, String
from datetime import datetime
from enum import Enum, auto
import json

# Measurement types enum
class MeasurementType(str, Enum):
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PH = "ph"
    ORP = "orp"
    EC = "ec"
    PRESSURE = "pressure"
    WATER_LEVEL = "water_level"

# # Sensor types enum
# class SensorType(str, Enum):
#     SHT41 = "sht41"
#     DS18B20 = "ds18b20"
#     PH_SENSOR = "ph_sensor"
#     EC_SENSOR = "ec_sensor"
#     ORP_SENSOR = "orp_sensor"
#     PRESSURE_SENSOR = "pressure_sensor"
#     WATER_LEVEL_SENSOR = "water_level_sensor"

# Controller types enum
class ControllerType(str, Enum):
    PH_CONTROLLER = "ph_controller"
    EC_CONTROLLER = "ec_controller"
    PUMP_TIMER = "pump_timer"
    TEMP_PUMP_TIMER = "temp_pump_timer"

# Base model for all tables
class BaseModel(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    name: str = Field(index=True)
    description: Optional[str] = None
    enabled: bool = Field(default=True)

# Link table for Sensor to Controller relationship
class SensorControllerLink(SQLModel, table=True):
    sensor_id: Optional[int] = Field(
        default=None, foreign_key="sensor.id", primary_key=True
    )
    controller_id: Optional[int] = Field(
        default=None, foreign_key="controller.id", primary_key=True
    )

# Sensor model
class Sensor(BaseModel, table=True):
    # sensor_type: SensorType
    driver: str
    config: str = Field(default="{}", sa_column=Column(String, default="{}"))
    update_interval: int = Field(default=60)  # seconds
    last_measurement : Optional[datetime] = None
    calibration_data: str = Field(default="{}", sa_column=Column(String, default="{}"))
    
    # Relationships
    measurements: List["Measurement"] = Relationship(back_populates="sensor")
    controllers: List["Controller"] = Relationship(
        back_populates="sensors",
        link_model=SensorControllerLink,
    )

# Measurement model
class Measurement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    measurement_type: MeasurementType
    value: float
    unit: str
    raw_value: Optional[float] = None
    
    # Foreign keys
    sensor_id: Optional[int] = Field(default=None, foreign_key="sensor.id")
    
    # Relationships
    sensor: Optional[Sensor] = Relationship(back_populates="measurements")

# Controller Create model (for API requests)
class ControllerCreate(SQLModel):
    name: str
    description: Optional[str] = None
    controller_type: ControllerType
    config: Dict[str, Any] = Field(default={})
    update_interval: int = Field(default=60)  # seconds
    enabled: bool = Field(default=True)

# Controller model
class Controller(BaseModel, table=True):
    controller_type: ControllerType
    config: str = Field(default="{}", sa_column=Column(String, default="{}"))
    update_interval: int = Field(default=60)  # seconds
    last_run: Optional[datetime] = None
    
    # Relationships
    sensors: List[Sensor] = Relationship(
        back_populates="controllers",
        link_model=SensorControllerLink,
    )
    actions: List["ControlAction"] = Relationship(back_populates="controller")

# Control Action model (records of controller actions)
class ControlAction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    action_type: str
    details: str = Field(default="{}", sa_column=Column(String, default="{}"))
    
    # Foreign keys
    controller_id: Optional[int] = Field(default=None, foreign_key="controller.id")
    
    # Relationships
    controller: Optional[Controller] = Relationship(back_populates="actions")