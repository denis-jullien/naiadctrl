from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

from models.base import Sensor, Controller, Measurement, ControlAction
from database import engine
from scheduler_instance import scheduler

router = APIRouter(
    prefix="/system",
    tags=["system"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the database session
def get_session():
    with Session(engine) as session:
        yield session

@router.get("/status", response_model=Dict[str, Any])
async def get_system_status(session: Session = Depends(get_session)):
    """Get the overall system status"""
    # Count sensors and controllers
    sensor_count = session.exec(select(Sensor)).count()
    controller_count = session.exec(select(Controller)).count()
    
    # Get the latest measurements
    latest_measurements_query = """
    SELECT m1.*
    FROM measurement m1
    JOIN (
        SELECT sensor_id, MAX(timestamp) as max_timestamp
        FROM measurement
        GROUP BY sensor_id
    ) m2 ON m1.sensor_id = m2.sensor_id AND m1.timestamp = m2.max_timestamp
    """
    latest_measurements = session.exec(latest_measurements_query).all()
    
    # Get the latest controller actions
    latest_actions_query = """
    SELECT a1.*
    FROM controlaction a1
    JOIN (
        SELECT controller_id, MAX(timestamp) as max_timestamp
        FROM controlaction
        GROUP BY controller_id
    ) a2 ON a1.controller_id = a2.controller_id AND a1.timestamp = a2.max_timestamp
    """
    latest_actions = session.exec(latest_actions_query).all()
    
    # Format the response
    return {
        "timestamp": datetime.now().isoformat(),
        "sensors": {
            "count": sensor_count,
            "enabled": session.exec(select(Sensor).where(Sensor.enabled == True)).count(),
        },
        "controllers": {
            "count": controller_count,
            "enabled": session.exec(select(Controller).where(Controller.enabled == True)).count(),
        },
        "latest_measurements": [
            {
                "sensor_id": m.sensor_id,
                "measurement_type": m.measurement_type,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat(),
            }
            for m in latest_measurements
        ],
        "latest_actions": [
            {
                "controller_id": a.controller_id,
                "action_type": a.action_type,
                "details": json.loads(a.details) if a.details else {},
                "timestamp": a.timestamp.isoformat(),
            }
            for a in latest_actions
        ],
        "scheduler_status": {
            "running": scheduler.running,
        },
    }

@router.post("/scheduler/start", response_model=Dict[str, Any])
async def start_scheduler():
    """Start the scheduler"""
    if scheduler.running:
        return {"message": "Scheduler is already running"}
    
    scheduler.start()
    return {"message": "Scheduler started"}

@router.post("/scheduler/stop", response_model=Dict[str, Any])
async def stop_scheduler():
    """Stop the scheduler"""
    if not scheduler.running:
        return {"message": "Scheduler is already stopped"}
    
    scheduler.stop()
    return {"message": "Scheduler stopped"}

@router.get("/measurements/recent", response_model=List[Dict[str, Any]])
async def get_recent_measurements(hours: int = 24, session: Session = Depends(get_session)):
    """Get recent measurements from all sensors"""
    # Calculate the start time
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Query for measurements after the start time
    query = select(Measurement).where(Measurement.timestamp >= start_time)
    measurements = session.exec(query).all()
    
    # Format the response
    return [
        {
            "sensor_id": m.sensor_id,
            "measurement_type": m.measurement_type,
            "value": m.value,
            "unit": m.unit,
            "timestamp": m.timestamp.isoformat(),
        }
        for m in measurements
    ]

@router.get("/actions/recent", response_model=List[Dict[str, Any]])
async def get_recent_actions(hours: int = 24, session: Session = Depends(get_session)):
    """Get recent controller actions"""
    # Calculate the start time
    start_time = datetime.now() - timedelta(hours=hours)
    
    # Query for actions after the start time
    query = select(ControlAction).where(ControlAction.timestamp >= start_time)
    actions = session.exec(query).all()
    
    # Format the response
    return [
        {
            "controller_id": a.controller_id,
            "action_type": a.action_type,
            "details": json.loads(a.details) if a.details else {},
            "timestamp": a.timestamp.isoformat(),
        }
        for a in actions
    ]