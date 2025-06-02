from fastapi import APIRouter, Depends, HTTPException, Query

from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from models.base import Controller
from database import engine

# Import GPIO if on Linux (likely Raspberry Pi)
import platform
RPI_AVAILABLE = False
if platform.system() == "Linux":
    try:
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        RPI_AVAILABLE = True
        print("GPIO initialized in BCM mode")
    except ImportError:
        print("RPi.GPIO not available, running in simulation mode")
else:
    print("Not running on Linux, GPIO simulation mode active")

router = APIRouter(
    prefix="/outputs",
    tags=["outputs"],
    responses={404: {"description": "Not found"}},
)

# Helper function to set GPIO pin state
def set_gpio_pin(pin_number: int, state: bool) -> bool:
    """Set GPIO pin state directly"""
    try:
        if RPI_AVAILABLE:
            # Make sure the pin is set up for output
            GPIO.setup(pin_number, GPIO.OUT)
            # Set the pin state
            GPIO.output(pin_number, state)
            return True
        else:
            print(f"SIMULATION: Setting GPIO pin {pin_number} to {'HIGH' if state else 'LOW'}")
            return True
    except Exception as e:
        print(f"Error setting GPIO pin {pin_number}: {str(e)}")
        return False

# Helper function to read GPIO pin state
def read_gpio_pin(pin_number: int) -> Optional[bool]:
    """Read the current state of a GPIO pin"""
    try:
        if RPI_AVAILABLE:
            # For output pins, we can read the current state
            return bool(GPIO.input(pin_number))
        else:
            print(f"SIMULATION: Reading GPIO pin {pin_number}")
            return False
    except Exception as e:
        print(f"Error reading GPIO pin {pin_number}: {str(e)}")
        return None

@router.get("/", response_model=Dict[str, int])
async def get_output_pins():
    list = [5, 6]

    return {str(k) : GPIO.input(k) for k in list}


@router.get("/{pin_number}", response_model=bool)
async def get_output_pin(pin_number: int):
    """Get a specific output pin by ID"""
    return GPIO.input(pin_number)



@router.post("/{pin_number}/set/{state}", response_model=Dict[str, Any])
async def direct_set_pin(pin_number: int, state: bool):
    """Set a GPIO pin directly without using the database"""
    if not RPI_AVAILABLE:
        return {"pin": pin_number, "state": state, "gpio_available": False, "message": "Simulated mode"}

    try:
        # Make sure the pin is set up as an output
        GPIO.setup(pin_number, GPIO.OUT)
        # Set the pin
        GPIO.output(pin_number, state)
        # Confirm the state was set
        actual_state = GPIO.input(pin_number)

        return {"pin": pin_number, "state": bool(actual_state), "gpio_available": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPIO error: {str(e)}")
