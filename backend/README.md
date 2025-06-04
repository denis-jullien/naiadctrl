# Hydro Control System

A modular Python system for water environment monitoring and control using FastAPI and SQLModel.

## Features

- Configurable sensor system with support for multiple sensor types (SHT41, DS18B20, etc.)
- Sensor calibration support
- Modular controller system for managing outputs based on sensor readings
- Scheduler for coordinating periodic sensor readings and control actions
- REST API for configuration, settings, and data retrieval
- Extensible architecture for easily adding new sensors and controllers

## Installation

```bash
sudo apt update 
sudo apt install python3-dev python3-pip git
git clone https://github.com/denis-jullien/naiadctrl.git
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## PI Configuration

1. Add this to config.txt: 
sudo nano /boot/firmware/config.txt
```
# Temperature sensor 1-Wire
dtoverlay=w1-gpio,gpiopin=17
# SHT41 on i2c
dtparam=i2c_arm=on
#dtoverlay=i2c-sensor,sht4x
```

2. Ensure that /etc/modules contains the following line:
```
i2c-dev
```	

## Running the Application

```bash
python main.py
```

The API will be available at http://localhost:8000

## API Documentation

Once the application is running, you can access the API documentation at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

- `api/`: API routers and endpoints
- `models/`: SQLModel database models
- `sensors/`: Sensor drivers and base classes
- `controllers/`: Controller implementations
- `scheduler/`: Scheduling system for periodic tasks

## Adding New Components

### Adding a New Sensor

Create a new sensor driver in the `sensors/drivers/` directory that inherits from the `BaseSensor` class.

### Adding a New Controller

Create a new controller in the `controllers/` directory that inherits from the `BaseController` class.