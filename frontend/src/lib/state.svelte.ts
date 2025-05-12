// API base URL
const API_BASE = 'http://192.168.10.50:8000/api';

// Maximum number of historical data points to keep
const MAX_HISTORY_POINTS = 100;

// Create shared state using Svelte 5 runes
export const sensor = $state({
	ph: null,
	orp: null,
	ec: null,
	water_temperature: null,
	air_temperature: null,
	humidity: null,
	lastUpdated: null
});

// Historical sensor data (for charts)
export const history = $state({
	ph: [],
	orp: [],
	ec: [],
	water_temperature: [],
	air_temperature: [],
	humidity: [],
	timestamps: []
});

// Controller data
export const controller = $state({
	ph: null,
	orp: null,
	ec: null,
	lastUpdated: null
});

// Configuration
export const config = $state({
	plop: {}
});

// Theme
export const theme = $state({
	color: 'light'
});

// Function to toggle theme
export function toggleTheme() {
	theme.color = theme.color === 'light' ? 'dark' : 'light';
}

// Function to fetch sensor data
export async function fetchSensorData() {
	try {
		const response = await fetch(`${API_BASE}/sensors`);
		const data = await response.json();

		console.log('Sensor Data:', data);

		// Update current sensor data
		Object.assign(sensor, {
			...data,
			lastUpdated: new Date()
		});

		// Add timestamp
		history.timestamps = [...history.timestamps, Date.now()];

		// Add sensor values
		Object.keys(data).forEach((key) => {
			if (key in history && key !== 'timestamps') {
				history[key] = [...history[key], data[key]];
			}
		});

		// Trim arrays if they exceed maximum length
		if (history.timestamps.length > MAX_HISTORY_POINTS) {
			Object.keys(history).forEach((key) => {
				if (Array.isArray(history[key])) {
					history[key] = history[key].slice(-MAX_HISTORY_POINTS);
				}
			});
		}

		return data;
	} catch (error) {
		console.error('Error fetching sensor data:', error);
		return null;
	}
}

// Function to fetch controller data
export async function fetchControllerData() {
	try {
		const response = await fetch(`${API_BASE}/controllers`);
		const data = await response.json();

		console.log('Controller Data:', data);

		Object.assign(controller, {
			...data,
			lastUpdated: new Date()
		});

		return data;
	} catch (error) {
		console.error('Error fetching controller data:', error);
		return null;
	}
}

// Function to fetch configuration
export async function fetchConfig() {
	try {
		const response = await fetch(`${API_BASE}/config`);
		const data = await response.json();

		config.plop = data;

		return data;
	} catch (error) {
		console.error('Error fetching configuration:', error);
		return null;
	}
}

// Function to update controller target
export async function updateControllerTarget(controllerId, target, tolerance = null) {
	try {
		const payload = { target };
		if (tolerance !== null) {
			payload.tolerance = tolerance;
		}

		const response = await fetch(`${API_BASE}/controllers/${controllerId}/target`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify(payload)
		});

		const data = await response.json();

		// Refresh controller data
		await fetchControllerData();

		return data;
	} catch (error) {
		console.error(`Error updating ${controllerId} target:`, error);
		return null;
	}
}

// Function to start controller
export async function startController(controllerId) {
	try {
		const response = await fetch(`${API_BASE}/controllers/${controllerId}/start`, {
			method: 'POST'
		});

		const data = await response.json();

		// Refresh controller data
		await fetchControllerData();

		return data;
	} catch (error) {
		console.error(`Error starting ${controllerId} controller:`, error);
		return null;
	}
}

// Function to stop controller
export async function stopController(controllerId) {
	try {
		const response = await fetch(`${API_BASE}/controllers/${controllerId}/stop`, {
			method: 'POST'
		});

		const data = await response.json();

		// Refresh controller data
		await fetchControllerData();

		return data;
	} catch (error) {
		console.error(`Error stopping ${controllerId} controller:`, error);
		return null;
	}
}

// Function to calibrate pH sensor
export async function calibratePH(voltage, ph) {
	try {
		const response = await fetch(`${API_BASE}/calibrate/ph`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ voltage, ph })
		});

		return await response.json();
	} catch (error) {
		console.error('Error calibrating pH sensor:', error);
		return null;
	}
}

// Function to calibrate ORP sensor
export async function calibrateORP(orp) {
	try {
		const response = await fetch(`${API_BASE}/calibrate/orp`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ orp })
		});

		return await response.json();
	} catch (error) {
		console.error('Error calibrating ORP sensor:', error);
		return null;
	}
}

// Function to calibrate EC sensor
export async function calibrateEC(ec) {
	try {
		const response = await fetch(`${API_BASE}/calibrate/ec`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ ec })
		});

		return await response.json();
	} catch (error) {
		console.error('Error calibrating EC sensor:', error);
		return null;
	}
}

// Function to fetch sensor history
export async function fetchSensorHistory() {
	try {
		const response = await fetch(`${API_BASE}/history`);
		const data = await response.json();

		// Update history store
		Object.assign(history, {
			ph: data.ph || [],
			orp: data.orp || [],
			ec: data.ec || [],
			water_temperature: data.water_temperature || [],
			air_temperature: data.air_temperature || [],
			humidity: data.humidity || [],
			timestamps: data.timestamps.map((date) => new Date(date).getTime()) || []
		});

		console.log('History Data:', data);

		return data;
	} catch (error) {
		console.error('Error fetching history data:', error);
		return null;
	}
}

// Function to get formatted data for charts
export function getChartData(sensorType) {
	if (!history || !history[sensorType] || !history.timestamps) {
		return [];
	}

	return history[sensorType].map((value, index) => ({
		x: history.timestamps[index],
		y: value
	}));
}
