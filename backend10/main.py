from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlmodel import SQLModel
from contextlib import asynccontextmanager

# Import database
from database import engine

# Import routers
from api.sensor_router import router as sensor_router
from api.controller_router import router as controller_router
from api.system_router import router as system_router
from api.output_router import router as output_router
from scheduler_instance import scheduler

from controllers.base import initialize_controllers
from sensors.base import initialize_sensors
from controllers.outputs import initialize_outputs

# Create tables on startup
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create DB tables and start scheduler
    create_db_and_tables()
    scheduler.start()
    yield
    # Shutdown: Stop scheduler
    scheduler.stop()

# Create FastAPI app
app = FastAPI(
    title="Hydro Control System",
    description="API for water environment monitoring and control system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sensor_router, prefix="/api", tags=["sensors"])
app.include_router(controller_router, prefix="/api", tags=["controllers"])
app.include_router(system_router, prefix="/api", tags=["system"])
app.include_router(output_router, prefix="/api", tags=["outputs"])

# Initialize controllers and sensors
initialize_controllers()
initialize_sensors()
initialize_outputs()

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)