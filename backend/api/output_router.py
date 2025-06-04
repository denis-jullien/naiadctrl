from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from controllers.outputs import set_pin_state, get_pin_state, ouput_pins

router = APIRouter(
    prefix="/outputs",
    tags=["outputs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=Dict[str, int])
async def get_output_pins():
    return {str(ixd) : get_pin_state(ixd) for ixd,k in enumerate(ouput_pins)}


@router.get("/{pin_number}", response_model=bool)
async def get_output_pin(pin_number: int):
    """Get a specific output pin by ID"""
    return get_pin_state(pin_number)



@router.post("/{pin_number}/set/{state}", response_model=Dict[str, Any])
async def direct_set_pin(pin_number: int, state: bool):
    """Set a GPIO pin directly """
    try:
        set_pin_state(pin_number, state)
        # Confirm the state was set
        actual_state = get_pin_state(pin_number)

        return {"pin": pin_number, "state": bool(actual_state), "gpio_available": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPIO error: {str(e)}")
