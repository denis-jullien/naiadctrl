import { writable } from 'svelte/store';

// API base URL
const API_BASE = 'http://localhost:8000/api';

// Maximum number of historical data points to keep
const MAX_HISTORY_POINTS = 100;

// Store for sensor data
export const sensorData = writable({
  ph: null,
  orp: null,
  ec: null,
  water_temperature: null,
  air_temperature: null,
  humidity: null,
  lastUpdated: null
});

// Store for historical sensor data (for charts)
export const sensorHistory = writable({
  ph: [],
  orp: [],
  ec: [],
  water_temperature: [],
  air_temperature: [],
  humidity: [],
  timestamps: []
});

// Store for controller data
export const controllerData = writable({
  ph: null,
  orp: null,
  ec: null,
  lastUpdated: null
});

// Store for configuration
export const configData = writable(null);

// Theme store for shadcn
export const theme = writable('light');

// Function to toggle theme
export function toggleTheme() {
  theme.update(current => current === 'light' ? 'dark' : 'light');
}

// Function to fetch sensor data
export async function fetchSensorData() {
  try {
    const response = await fetch(`${API_BASE}/sensors`);
    const data = await response.json();

    console.log('Sensor Data:', data);
    
    // Update current sensor data
    sensorData.update(current => ({
      ...current,
      ...data,
      lastUpdated: new Date()
    }));
    
    // Update historical data
    const timestamp = new Date().toISOString();
    sensorHistory.update(history => {
      // Add new data points
      const newHistory = { ...history };
      
      // Add timestamp
      newHistory.timestamps = [...history.timestamps, timestamp];
      
      // Add sensor values
      Object.keys(data).forEach(key => {
        if (key in newHistory) {
          newHistory[key] = [...history[key], data[key]];
        }
      });
      
      // Trim arrays if they exceed maximum length
      if (newHistory.timestamps.length > MAX_HISTORY_POINTS) {
        newHistory.timestamps = newHistory.timestamps.slice(-MAX_HISTORY_POINTS);
        
        Object.keys(newHistory).forEach(key => {
          if (key !== 'timestamps' && Array.isArray(newHistory[key])) {
            newHistory[key] = newHistory[key].slice(-MAX_HISTORY_POINTS);
          }
        });
      }
      
      return newHistory;
    });
    
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
    
    controllerData.update(current => ({
      ...current,
      ...data,
      lastUpdated: new Date()
    }));
    
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
    
    configData.set(data);
    
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

// Function to get formatted data for LayerChart
// Add history fetching function
export async function fetchSensorHistory() {
  try {
    const response = await fetch(`${API_BASE}/history`);
    const data = await response.json();
    
    console.log('History Data:', data);
    
    // Update history store
    sensorHistory.set({
      ph: data.ph || [],
      orp: data.orp || [],
      ec: data.ec || [],
      water_temperature: data.water_temperature || [],
      air_temperature: data.air_temperature || [],
      humidity: data.humidity || [],
      timestamps: data.timestamps || []
    });
    
    return data;
  } catch (error) {
    console.error('Error fetching history data:', error);
    return null;
  }
}

// Update the getChartData function to handle the new data format
export function getChartData(sensorType) {
  let data = [];
  let $history;
  
  // Get the current value of the store
  sensorHistory.subscribe(value => {
    $history = value;
  })();
  
  if (!$history || !$history.timestamps || !$history[sensorType]) {
    return data;
  }
  
  // Format data for LayerChart
  for (let i = 0; i < $history.timestamps.length; i++) {
    if ($history[sensorType][i] !== null && $history[sensorType][i] !== undefined) {
      data.push({
        x: new Date($history.timestamps[i]),
        y: $history[sensorType][i]
      });
    }
  }
  
  return data;
}