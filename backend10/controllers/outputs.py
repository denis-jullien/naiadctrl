
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

ouput_pins = [5,6,7,8,9,10]

def initialize_outputs():
    for pin in ouput_pins:
        GPIO.setup(pin, GPIO.OUT)

def set_pin_state(pin, state):
    if not RPI_AVAILABLE:
        print(f"GPIO simulation mode active for pin {pin} state: {state}")
        return
    GPIO.output(ouput_pins[pin], state)

def get_pin_state(pin):
    return GPIO.input(ouput_pins[pin])