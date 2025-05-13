// API service for hydroponic control system

const API_BASE_URL = 'http://hydroponie.local:8000';

// Helper function for API requests
async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }

  return await response.json();
}

// Types based on OpenAPI schema
export interface Sensor {
  id?: number | null;
  created_at: string;
  updated_at: string;
  name: string;
  description?: string | null;
  enabled: boolean;
  driver: string;
  config: string;
  update_interval: number;
  last_measurement?: string | null;
  calibration_data: string;
}

export interface SensorCreate {
  name: string;
  driver: string;
  description?: string | null;
  update_interval?: number | null;
  config?: Record<string, any> | null;
  calibration_data?: Record<string, any> | null;
  enabled?: boolean | null;
}

export interface Measurement {
  id?: number | null;
  timestamp: string;
  measurement_type: MeasurementType;
  value: number;
  unit: string;
  raw_value?: number | null;
  sensor_id?: number | null;
}

export type MeasurementType = 'temperature' | 'humidity' | 'ph' | 'orp' | 'ec' | 'pressure' | 'water_level';

export interface Controller {
  id?: number | null;
  created_at: string;
  updated_at: string;
  name: string;
  description?: string | null;
  enabled: boolean;
  controller_type: ControllerType;
  config: string;
  update_interval: number;
  last_run?: string | null;
}

export type ControllerType = 'ph_controller' | 'ec_controller' | 'pump_timer' | 'temp_pump_timer';

// API functions
export const api = {
  // Sensors
  sensors: {
    getAll: () => fetchApi<Sensor[]>('/api/sensors/'),
    get: (id: number) => fetchApi<Sensor>(`/api/sensors/${id}`),
    create: (sensor: SensorCreate) => fetchApi<Sensor>('/api/sensors/', {
      method: 'POST',
      body: JSON.stringify(sensor),
    }),
    update: (id: number, sensor: SensorCreate) => fetchApi<Sensor>(`/api/sensors/${id}`, {
      method: 'PUT',
      body: JSON.stringify(sensor),
    }),
    delete: (id: number) => fetchApi<any>(`/api/sensors/${id}`, {
      method: 'DELETE',
    }),
    getAvailableDrivers: () => fetchApi<string[]>('/api/sensors/available-drivers'),
    getMeasurements: (id: number, params?: {
      limit?: number;
      offset?: number;
      start_time?: string;
      end_time?: string;
    }) => {
      const queryParams = new URLSearchParams();
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      if (params?.offset) queryParams.append('offset', params.offset.toString());
      if (params?.start_time) queryParams.append('start_time', params.start_time);
      if (params?.end_time) queryParams.append('end_time', params.end_time);
      
      const query = queryParams.toString() ? `?${queryParams.toString()}` : '';
      return fetchApi<Measurement[]>(`/api/sensors/${id}/measurements${query}`);
    },
  },

  // Controllers
  controllers: {
    getAll: () => fetchApi<Controller[]>('/api/controllers/'),
    get: (id: number) => fetchApi<Controller>(`/api/controllers/${id}`),
    create: (controller: Controller) => fetchApi<Controller>('/api/controllers/', {
      method: 'POST',
      body: JSON.stringify(controller),
    }),
    update: (id: number, controller: Controller) => fetchApi<Controller>(`/api/controllers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(controller),
    }),
    delete: (id: number) => fetchApi<any>(`/api/controllers/${id}`, {
      method: 'DELETE',
    }),
    getTypes: () => fetchApi<string[]>('/api/controllers/types'),
    getAvailableControllers: () => fetchApi<string[]>('/api/controllers/available-controllers'),
    getSensors: (id: number) => fetchApi<Sensor[]>(`/api/controllers/${id}/sensors`),
    addSensor: (controllerId: number, sensorId: number) => fetchApi<any>(`/api/controllers/${controllerId}/sensors/${sensorId}`, {
      method: 'POST',
    }),
    removeSensor: (controllerId: number, sensorId: number) => fetchApi<any>(`/api/controllers/${controllerId}/sensors/${sensorId}`, {
      method: 'DELETE',
    }),
    process: (id: number) => fetchApi<any>(`/api/controllers/${id}/process`, {
      method: 'POST',
    }),
  },

  // System
  system: {
    getStatus: () => fetchApi<Record<string, any>>('/api/system/status'),
    startScheduler: () => fetchApi<Record<string, any>>('/api/system/scheduler/start', {
      method: 'POST',
    }),
    stopScheduler: () => fetchApi<Record<string, any>>('/api/system/scheduler/stop', {
      method: 'POST',
    }),
    getRecentMeasurements: (hours?: number) => {
      const query = hours ? `?hours=${hours}` : '';
      return fetchApi<Record<string, any>[]>(`/api/system/measurements/recent${query}`);
    },
    getRecentActions: (hours?: number) => {
      const query = hours ? `?hours=${hours}` : '';
      return fetchApi<Record<string, any>[]>(`/api/system/actions/recent${query}`);
    },
  },
};