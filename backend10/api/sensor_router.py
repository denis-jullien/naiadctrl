from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json
from pydantic import BaseModel as PydanticBaseModel

from models.base import Sensor, Measurement, MeasurementType
from sensors.base import SensorRegistry
from database import engine

router = APIRouter(
    prefix="/sensors",
    tags=["sensors"],
    responses={404: {"description": "Not found"}},
)

# Simplified model for sensor creation
class SensorCreate(PydanticBaseModel):
    name: str
    driver: str
    description: Optional[str] = None
    update_interval: Optional[int] = 60
    config: Optional[Dict[str, Any]] = {}
    calibration_data: Optional[Dict[str, Any]] = {}
    enabled: Optional[bool] = True

# Dependency to get the database session
def get_session():
    with Session(engine) as session:
        yield session

@router.get("/", response_model=List[Sensor])
async def get_sensors(session: Session = Depends(get_session)):
    """Get all sensors"""
    sensors = session.exec(select(Sensor)).all()
    return sensors

# @router.get("/types", response_model=List[str])
# async def get_sensor_types():
#     """Get all available sensor types"""
#     return [t.value for t in SensorType]

@router.get("/available-drivers", response_model=List[str])
async def get_available_drivers():
    """Get all available sensor drivers"""
    return SensorRegistry.get_available_drivers()

@router.get("/{sensor_id}", response_model=Sensor)
async def get_sensor(sensor_id: int, session: Session = Depends(get_session)):
    """Get a specific sensor by ID"""
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return sensor

@router.post("/", response_model=Sensor)
async def create_sensor(sensor_data: SensorCreate, session: Session = Depends(get_session)):
    """Create a new sensor with simplified input"""
    # Validate driver
    if sensor_data.driver not in SensorRegistry.get_available_drivers():
        raise HTTPException(status_code=400, detail=f"Invalid driver: {sensor_data.driver}")
    
    # Create a new Sensor instance with the provided data
    sensor = Sensor(
        name=sensor_data.name,
        driver=sensor_data.driver,
        description=sensor_data.description,
        update_interval=sensor_data.update_interval,
        enabled=sensor_data.enabled,
        config=json.dumps(sensor_data.config),
        calibration_data=json.dumps(sensor_data.calibration_data)
    )
    
    session.add(sensor)
    session.commit()
    session.refresh(sensor)
    return sensor

@router.put("/{sensor_id}", response_model=Sensor)
async def update_sensor(sensor_id: int, sensor_update: Sensor, session: Session = Depends(get_session)):
    """Update a sensor"""
    db_sensor = session.get(Sensor, sensor_id)
    if not db_sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Update sensor attributes
    sensor_data = sensor_update.dict(exclude_unset=True)
    
    # Handle JSON fields
    if 'config' in sensor_data and isinstance(sensor_data['config'], dict):
        sensor_data['config'] = json.dumps(sensor_data['config'])
    if 'calibration_data' in sensor_data and isinstance(sensor_data['calibration_data'], dict):
        sensor_data['calibration_data'] = json.dumps(sensor_data['calibration_data'])
    
    for key, value in sensor_data.items():
        setattr(db_sensor, key, value)
    
    session.add(db_sensor)
    session.commit()
    session.refresh(db_sensor)
    return db_sensor

@router.delete("/{sensor_id}", response_model=dict)
async def delete_sensor(sensor_id: int, session: Session = Depends(get_session)):
    """Delete a sensor"""
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    session.delete(sensor)
    session.commit()
    return {"message": f"Sensor {sensor_id} deleted"}

@router.get("/{sensor_id}/measurements", response_model=List[Measurement])
async def get_sensor_measurements(
    sensor_id: int, 
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    session: Session = Depends(get_session)
):
    """Get measurements for a specific sensor"""
    # Verify sensor exists
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Build query
    query = select(Measurement).where(Measurement.sensor_id == sensor_id)
    
    # Add time filters if provided
    if start_time:
        query = query.where(Measurement.timestamp >= start_time)
    if end_time:
        query = query.where(Measurement.timestamp <= end_time)
    
    # Add ordering and pagination
    query = query.order_by(Measurement.timestamp.desc()).offset(offset).limit(limit)
    
    # Execute query
    measurements = session.exec(query).all()
    return measurements