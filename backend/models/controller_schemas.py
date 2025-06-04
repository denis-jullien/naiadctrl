from pydantic import BaseModel, Field, validator
from typing import Dict, Any, Optional, List, Union, Literal
from enum import Enum

# Base configuration model that all controller configs will inherit from
class BaseControllerConfig(BaseModel):
    """Base configuration for all controllers"""
    class Config:
        extra = "forbid"  # Prevent extra fields

# pH Controller configuration
class PhControllerConfig(BaseControllerConfig):
    """Configuration for pH controllers"""
    target_ph: float = Field(6.0, description="Target pH value", ge=0, le=14)
    tolerance: float = Field(0.2, description="Acceptable deviation from target", ge=0.01, le=2.0)
    dose_time: float = Field(1.0, description="Dose time in seconds", ge=0.1, le=10.0)
    min_dose_interval: int = Field(300, description="Minimum time between doses in seconds", ge=10)
    output_pin: Optional[int] = Field(None, description="GPIO pin for dosing pump")

    @validator('target_ph')
    def validate_ph(cls, v):
        if v < 0 or v > 14:
            raise ValueError('pH must be between 0 and 14')
        return v

# EC Controller configuration
class EcControllerConfig(BaseControllerConfig):
    """Configuration for EC (Electrical Conductivity) controllers"""
    target_ec: float = Field(1.5, description="Target EC value in mS/cm", ge=0, le=10.0)
    tolerance: float = Field(0.2, description="Acceptable deviation from target", ge=0.01, le=1.0)
    dose_time: float = Field(1.0, description="Dose time in seconds", ge=0.1, le=10.0)
    min_dose_interval: int = Field(300, description="Minimum time between doses in seconds", ge=10)
    output_pin: Optional[int] = Field(None, description="GPIO pin for nutrient pump")

# Pump Timer Controller configuration
class PumpTimerConfig(BaseControllerConfig):
    """Configuration for time-based pump controllers"""
    on_duration: int = Field(300, description="Duration pump is on in seconds", ge=1)
    off_duration: int = Field(1800, description="Duration pump is off in seconds", ge=1)
    output_pin: Optional[int] = Field(None, description="GPIO pin for pump")
    start_time: str = Field("08:00", description="Daily start time (HH:MM)")
    end_time: str = Field("20:00", description="Daily end time (HH:MM)")

    @validator('start_time', 'end_time')
    def validate_time_format(cls, v):
        try:
            hour, minute = map(int, v.split(':'))
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
        except:
            raise ValueError('Time must be in HH:MM format (00:00 to 23:59)')
        return v

# Temperature Pump Timer Controller configuration
class TempPumpTimerConfig(BaseControllerConfig):
    """Configuration for temperature-dependent pump controllers"""
    min_temp: float = Field(18.0, description="Minimum temperature in °C", ge=0, le=50)
    max_temp: float = Field(28.0, description="Maximum temperature in °C", ge=0, le=50)
    on_duration: int = Field(300, description="Duration pump is on in seconds", ge=1)
    off_duration: int = Field(1800, description="Duration pump is off in seconds", ge=1)
    output_pin: Optional[int] = Field(None, description="GPIO pin for pump")

    @validator('max_temp')
    def validate_max_temp(cls, v, values):
        if 'min_temp' in values and v <= values['min_temp']:
            raise ValueError('Maximum temperature must be greater than minimum temperature')
        return v

# Map controller types to their configuration models
CONTROLLER_CONFIG_MAP = {
    "ph_controller": PhControllerConfig,
    "ec_controller": EcControllerConfig,
    "pump_timer": PumpTimerConfig,
    "temp_pump_timer": TempPumpTimerConfig,
}

# Function to get the appropriate config model for a controller type
def get_config_model(controller_type: str):
    """Get the configuration model for a specific controller type"""
    return CONTROLLER_CONFIG_MAP.get(controller_type, BaseControllerConfig)

# Function to validate config against the appropriate model
def validate_controller_config(controller_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate controller configuration against its schema"""
    model = get_config_model(controller_type)
    return model(**config).dict()

# Function to get schema for a controller type
def get_controller_schema(controller_type: str) -> Dict[str, Any]:
    """Get JSON schema for a controller type"""
    model = get_config_model(controller_type)
    return model.schema()