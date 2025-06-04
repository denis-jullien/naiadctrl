# Hydroponic Control System

A complete hydroponic monitoring and control system built with Python and SvelteKit.

## Features

- Real-time monitoring of pH, ORP, EC, temperature, and humidity
- Automated control of nutrient dosing, pH adjustment, and ORP management
- Web-based dashboard with responsive design
- Sensor calibration interface
- Configuration management

## 🚀 **Quick start:**

**One-line install:**
```bash
curl -sSL https://raw.githubusercontent.com/denis-jullien/naiadctrl/main/install.sh | bash
```
Or download and run:
```bash
wget https://raw.githubusercontent.com/denis-jullien/naiadctrl/main/install.sh
chmod +x install.sh
./install.sh
```


## System Architecture

### Backend

- Python-based API server using aiohttp
- Sensor interfaces for pH, ORP, EC, temperature, and humidity sensors
- Controller modules for maintaining optimal water parameters
- GPIO control for pumps and other outputs

### Frontend

- SvelteKit-based web application

## Hardware Requirements

- Raspberry Pi 
- NaiadCtrl Hat
  - pH probe
  - ORP probe
  - EC probe
  - DS18B20 temperature sensor
  - SHT41 temperature and humidity sensor
  - MOSFETs (open drain) for controlling pumps or other equipements

## Installation

### Backend

1. Install required packages:
pip install aiohttp adafruit-circuitpython-sht4x RPi.GPIO

2. Configure your hardware pins in `config.json`

3. Run the backend server:
python backend/main.py

### Frontend

1. Install dependencies:
cd frontend
npm install

2. Run development server:
npm run dev

3. Build for production:
npm run build


## Usage

1. Access the web interface at `http://localhost:5173` (development) or `http://localhost:8000` (production)
2. Calibrate your sensors using the Calibration page
3. Configure target values for pH, ORP, and EC on the Controllers page
4. Monitor your system on the Dashboard

## License

MIT