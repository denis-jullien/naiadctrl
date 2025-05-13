from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

from models.base import Controller, ControllerType, Sensor, SensorControllerLink, ControllerCreate
from controllers.base import ControllerRegistry
from database import engine

router = APIRouter(
    prefix="/controllers",
    tags=["controllers"],
    responses={404: {"description": "Not found"}},
)

# Dependency to get the database session
def get_session():
    with Session(engine) as session:
        yield session

@router.get("/", response_model=List[Controller])
async def get_controllers(session: Session = Depends(get_session)):
    """Get all controllers"""
    controllers = session.exec(select(Controller)).all()
    return controllers

@router.get("/types", response_model=List[str])
async def get_controller_types():
    """Get all available controller types"""
    return [t.value for t in ControllerType]

@router.get("/available-controllers", response_model=List[str])
async def get_available_controllers():
    """Get all available controller implementations"""
    return ControllerRegistry.get_available_controllers()

@router.get("/{controller_id}", response_model=Controller)
async def get_controller(controller_id: int, session: Session = Depends(get_session)):
    """Get a specific controller by ID"""
    controller = session.get(Controller, controller_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    return controller

@router.post("/", response_model=Controller)
async def create_controller(controller_create: ControllerCreate, session: Session = Depends(get_session)):
    """Create a new controller"""
    # Validate controller type
    if controller_create.controller_type not in ControllerType:
        raise HTTPException(status_code=400, detail=f"Invalid controller type: {controller_create.controller_type}")
    
    # Validate that the controller type is available in the registry
    if controller_create.controller_type.value not in ControllerRegistry.get_available_controllers():
        raise HTTPException(
            status_code=400, 
            detail=f"Controller implementation not available: {controller_create.controller_type}"
        )
    
    # Create a new Controller instance from the ControllerCreate data
    controller = Controller(
        name=controller_create.name,
        description=controller_create.description,
        controller_type=controller_create.controller_type,
        config=json.dumps(controller_create.config),
        update_interval=controller_create.update_interval,
        enabled=controller_create.enabled
    )
    
    session.add(controller)
    session.commit()
    session.refresh(controller)
    return controller

@router.put("/{controller_id}", response_model=Controller)
async def update_controller(
    controller_id: int, 
    controller_update: ControllerCreate, 
    session: Session = Depends(get_session)
):
    """Update a controller"""
    db_controller = session.get(Controller, controller_id)
    if not db_controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    # Update controller attributes
    db_controller.name = controller_update.name
    db_controller.description = controller_update.description
    db_controller.controller_type = controller_update.controller_type
    db_controller.config = json.dumps(controller_update.config)
    db_controller.update_interval = controller_update.update_interval
    db_controller.enabled = controller_update.enabled
    db_controller.updated_at = datetime.now()
    
    session.add(db_controller)
    session.commit()
    session.refresh(db_controller)
    return db_controller

@router.delete("/{controller_id}", response_model=dict)
async def delete_controller(controller_id: int, session: Session = Depends(get_session)):
    """Delete a controller"""
    controller = session.get(Controller, controller_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    session.delete(controller)
    session.commit()
    return {"message": f"Controller {controller_id} deleted"}

@router.get("/{controller_id}/sensors", response_model=List[Sensor])
async def get_controller_sensors(controller_id: int, session: Session = Depends(get_session)):
    """Get all sensors associated with a controller"""
    controller = session.get(Controller, controller_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    return controller.sensors

@router.post("/{controller_id}/sensors/{sensor_id}", response_model=dict)
async def add_sensor_to_controller(
    controller_id: int, 
    sensor_id: int, 
    session: Session = Depends(get_session)
):
    """Associate a sensor with a controller"""
    controller = session.get(Controller, controller_id)
    if not controller:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    sensor = session.get(Sensor, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    # Check if the association already exists
    link = session.exec(
        select(SensorControllerLink).where(
            SensorControllerLink.sensor_id == sensor_id,
            SensorControllerLink.controller_id == controller_id
        )
    ).first()
    
    if link:
        return {"message": "Sensor already associated with controller"}
    
    # Create the association
    link = SensorControllerLink(sensor_id=sensor_id, controller_id=controller_id)
    session.add(link)
    session.commit()
    
    return {"message": f"Sensor {sensor_id} added to controller {controller_id}"}

@router.delete("/{controller_id}/sensors/{sensor_id}", response_model=dict)
async def remove_sensor_from_controller(
    controller_id: int, 
    sensor_id: int, 
    session: Session = Depends(get_session)
):
    """Remove a sensor from a controller"""
    # Check if the association exists
    link = session.exec(
        select(SensorControllerLink).where(
            SensorControllerLink.sensor_id == sensor_id,
            SensorControllerLink.controller_id == controller_id
        )
    ).first()
    
    if not link:
        raise HTTPException(status_code=404, detail="Sensor not associated with controller")
    
    # Remove the association
    session.delete(link)
    session.commit()
    
    return {"message": f"Sensor {sensor_id} removed from controller {controller_id}"}

@router.post("/{controller_id}/process", response_model=Dict[str, Any])
async def process_controller(controller_id: int, session: Session = Depends(get_session)):
    """Manually trigger a controller to process its inputs"""
    controller_db = session.get(Controller, controller_id)
    if not controller_db:
        raise HTTPException(status_code=404, detail="Controller not found")
    
    # Get the controller implementation
    controller_class = ControllerRegistry.get_controller(controller_db.controller_type.value)
    if not controller_class:
        raise HTTPException(
            status_code=400, 
            detail=f"Controller implementation not available: {controller_db.controller_type}"
        )
    
    # Create an instance of the controller
    controller = controller_class(controller_db)
    
    # Process the controller
    result = controller.process()
    
    # Update the last_run timestamp
    controller_db.last_run = datetime.now()
    session.add(controller_db)
    session.commit()
    
    if result:
        return result
    else:
        return {"message": "No action taken"}