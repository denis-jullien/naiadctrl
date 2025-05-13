<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { api, type Sensor, type SensorCreate, type Measurement } from "$lib/api";

  // State using Svelte 5 runes
  let sensors = $state<Sensor[]>([]);
  let availableDrivers = $state<string[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let showAddForm = $state(false);
  let editingSensor = $state<Sensor | null>(null);
  let latestMeasurements = $state<Record<number, Measurement | null>>({});
  let refreshInterval = $state(10); // Refresh interval in seconds
  let refreshTimer: number | null = $state(null);
  let lastRefreshTime = $state<Date | null>(null);

  // New sensor form state
  let newSensor = $state<SensorCreate>({
    name: '',
    driver: '',
    description: '',
    update_interval: 60,
    enabled: true,
    config: {},
    calibration_data: {}
  });

  // Fetch data on component mount
  onMount(async () => {
    await loadData();
    
    // Set up refresh timer
    startRefreshTimer();
  });
  
  // Clean up on component destroy
  onDestroy(() => {
    console.log('the component is being destroyed');
    stopRefreshTimer();
  });
  
  // Start the refresh timer
  function startRefreshTimer() {
    stopRefreshTimer(); // Clear any existing timer
    refreshTimer = window.setInterval(async () => {
      console.log('Refreshing data...');
      if (!editingSensor) { // Don't refresh while editing
        await loadData(false); // Pass false to indicate this is a background refresh
      }
    }, refreshInterval * 1000);
  }
  
  // Stop the refresh timer
  function stopRefreshTimer() {
    if (refreshTimer !== null) {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }
  
  // Load all data
  async function loadData(showLoadingState = true) {
    try {
      if (showLoadingState) {
        loading = true;
      }
      
      // Load sensors and available drivers in parallel
      const [sensorsData, driversData] = await Promise.all([
        api.sensors.getAll(),
        api.sensors.getAvailableDrivers()
      ]);

      sensors = sensorsData;
      availableDrivers = driversData;
      
      // Fetch latest measurement for each sensor
      await fetchLatestMeasurements();
      
      // Update last refresh time
      lastRefreshTime = new Date();
    } catch (err) {
      console.error('Failed to load sensors data:', err);
      if (showLoadingState) {
        error = 'Failed to load sensors data. Please check your connection to the backend server.';
      }
    } finally {
      if (showLoadingState) {
        loading = false;
      }
    }
  }

  // Fetch latest measurement for each sensor
  async function fetchLatestMeasurements() {
    for (const sensor of sensors) {
      if (sensor.id && sensor.last_measurement) {
        try {
          const measurements = await api.sensors.getMeasurements(sensor.id, 1);
          if (measurements && measurements.length > 0) {
            latestMeasurements[sensor.id] = measurements[0];
          }
        } catch (err) {
          console.error(`Failed to fetch measurements for sensor ${sensor.id}:`, err);
        }
      }
    }
  }

  // Helper function to format date
  function formatDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  }

  // Helper function to format measurement value with unit
  function formatMeasurement(sensorId: number | null): string {
    if (!sensorId || !latestMeasurements[sensorId]) return 'N/A';
    const measurement = latestMeasurements[sensorId];
    return `${measurement.value.toFixed(2)} ${measurement.unit}`;
  }

  // Toggle add form visibility
  function toggleAddForm() {
    showAddForm = !showAddForm;
    if (!showAddForm) {
      // Reset form when closing
      newSensor = {
        name: '',
        driver: '',
        description: '',
        update_interval: 60,
        enabled: true,
        config: {},
        calibration_data: {}
      };
    }
  }

  // Create new sensor
  async function createSensor() {
    try {
      const created = await api.sensors.create(newSensor);
      sensors = [...sensors, created];
      toggleAddForm(); // Close form after successful creation
      await loadData(); // Refresh data after creating a sensor
    } catch (err) {
      console.error('Failed to create sensor:', err);
      error = 'Failed to create sensor. Please try again.';
    }
  }

  // Edit sensor
  function startEdit(sensor: Sensor) {
    editingSensor = { ...sensor };
  }

  // Cancel edit
  function cancelEdit() {
    editingSensor = null;
  }

  // Save edited sensor
  async function updateSensor() {
    if (!editingSensor || !editingSensor.id) return;
    
    try {
      // Convert Sensor to SensorCreate for the API call
      const sensorUpdate: SensorCreate = {
        name: editingSensor.name,
        driver: editingSensor.driver,
        description: editingSensor.description,
        update_interval: editingSensor.update_interval,
        enabled: editingSensor.enabled,
        config: typeof editingSensor.config === 'string' 
          ? JSON.parse(editingSensor.config) 
          : editingSensor.config,
        calibration_data: typeof editingSensor.calibration_data === 'string'
          ? JSON.parse(editingSensor.calibration_data)
          : editingSensor.calibration_data
      };
      
      const updated = await api.sensors.update(editingSensor.id, sensorUpdate);
      sensors = sensors.map(s => s.id === updated.id ? updated : s);
      editingSensor = null; // Close edit form
      await loadData(); // Refresh data after updating a sensor
    } catch (err) {
      console.error('Failed to update sensor:', err);
      error = 'Failed to update sensor. Please try again.';
    }
  }

  // Delete sensor
  async function deleteSensor(id: number) {
    if (!confirm('Are you sure you want to delete this sensor?')) return;
    
    try {
      await api.sensors.delete(id);
      sensors = sensors.filter(s => s.id !== id);
      await loadData(); // Refresh data after deleting a sensor
    } catch (err) {
      console.error('Failed to delete sensor:', err);
      error = 'Failed to delete sensor. Please try again.';
    }
  }

  // Toggle sensor enabled state
  async function toggleSensorEnabled(sensor: Sensor) {
    if (!sensor.id) return;
    
    try {
      // Convert Sensor to SensorCreate for the API call
      const sensorUpdate: SensorCreate = {
        name: sensor.name,
        driver: sensor.driver,
        description: sensor.description,
        update_interval: sensor.update_interval,
        enabled: !sensor.enabled,  // Toggle the enabled state
        config: typeof sensor.config === 'string' 
          ? JSON.parse(sensor.config) 
          : sensor.config,
        calibration_data: typeof sensor.calibration_data === 'string'
          ? JSON.parse(sensor.calibration_data)
          : sensor.calibration_data
      };
      
      const updated = await api.sensors.update(sensor.id, sensorUpdate);
      sensors = sensors.map(s => s.id === updated.id ? updated : s);
    } catch (err) {
      console.error('Failed to update sensor:', err);
      error = 'Failed to update sensor. Please try again.';
    }
  }

  // Manual refresh function
  async function refreshData() {
    await loadData();
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">Sensors</h1>
    
    <div class="flex space-x-2">
      <div class="flex items-center space-x-2">
        <span class="text-sm text-muted-foreground">
          {lastRefreshTime ? `Last updated: ${lastRefreshTime.toLocaleTimeString()}` : ''}
        </span>
        <Button variant="outline" size="sm" onclick={refreshData}>
          Refresh
        </Button>
      </div>
      <Button onclick={toggleAddForm}>
        {showAddForm ? 'Cancel' : 'Add Sensor'}
      </Button>
    </div>
  </div>



  {#if error}
    <div class="bg-destructive/15 p-4 rounded-md">
      <p class="text-destructive">{error}</p>
      <Button variant="outline" class="mt-2" onclick={() => error = null}>Dismiss</Button>
    </div>
  {/if}

  {#if showAddForm}
    <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
      <h2 class="text-xl font-semibold mb-4">Add New Sensor</h2>
      
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <label class="text-sm font-medium" for="name">Name</label>
          <input 
            id="name"
            type="text" 
            bind:value={newSensor.name} 
            class="w-full p-2 border rounded-md"
            placeholder="Temperature Sensor 1"
          />
        </div>
        
        <div class="space-y-2">
          <label class="text-sm font-medium" for="driver">Driver</label>
          <select 
            id="driver"
            bind:value={newSensor.driver} 
            class="w-full p-2 border rounded-md"
          >
            <option value="">Select a driver</option>
            {#each availableDrivers as driver}
              <option value={driver}>{driver}</option>
            {/each}
          </select>
        </div>
        
        <div class="space-y-2 md:col-span-2">
          <label class="text-sm font-medium" for="description">Description</label>
          <textarea 
            id="description"
            bind:value={newSensor.description} 
            class="w-full p-2 border rounded-md"
            placeholder="Optional description"
            rows="2"
          ></textarea>
        </div>
        
        <div class="space-y-2">
          <label class="text-sm font-medium" for="update_interval">Update Interval (seconds)</label>
          <input 
            id="update_interval"
            type="number" 
            bind:value={newSensor.update_interval} 
            class="w-full p-2 border rounded-md"
            min="1"
          />
        </div>
        
        <div class="space-y-2 flex items-center">
          <label class="inline-flex items-center">
            <input 
              type="checkbox" 
              bind:checked={newSensor.enabled} 
              class="mr-2"
            />
            <span class="text-sm font-medium">Enabled</span>
          </label>
        </div>
      </div>
      
      <div class="mt-6 flex justify-end space-x-2">
        <Button variant="outline" onclick={toggleAddForm}>Cancel</Button>
        <Button 
          onclick={createSensor}
          disabled={!newSensor.name || !newSensor.driver}
        >
          Create Sensor
        </Button>
      </div>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <p class="text-lg">Loading sensors...</p>
    </div>
  {:else if sensors.length === 0}
    <div class="bg-muted p-6 rounded-lg text-center">
      <p class="text-muted-foreground">No sensors found. Add your first sensor to get started.</p>
    </div>
  {:else}
    <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden">
      <div class="overflow-x-auto">
        <table class="w-full">
          <thead>
            <tr class="border-b">
              <th class="text-left p-3 font-medium">Name</th>
              <th class="text-left p-3 font-medium">Driver</th>
              <th class="text-left p-3 font-medium">Status</th>
              <th class="text-left p-3 font-medium">Last Measurement</th>
              <th class="text-left p-3 font-medium">Latest Value</th>
              <th class="text-left p-3 font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {#each sensors as sensor}
              {#if editingSensor && editingSensor.id === sensor.id}
                <tr class="border-b bg-muted/50">
                  <td class="p-3" colspan="5">
                    <div class="grid gap-4 md:grid-cols-2">
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Name</label>
                        <input 
                          type="text" 
                          bind:value={editingSensor.name} 
                          class="w-full p-2 border rounded-md"
                        />
                      </div>
                      
                      <div class="space-y-2">
                        <label class="text-sm font-medium">Driver</label>
                        <select 
                          bind:value={editingSensor.driver} 
                          class="w-full p-2 border rounded-md"
                        >
                          {#each availableDrivers as driver}
                            <option value={driver}>{driver}</option>
                          {/each}
                        </select>
                      </div>
                      
                      <div class="space-y-2 md:col-span-2">
                        <label class="text-sm font-medium">Description</label>
                        <textarea 
                          bind:value={editingSensor.description} 
                          class="w-full p-2 border rounded-md"
                          rows="2"
                        ></textarea>
                      </div>
                      
                      <div class="space-y-2">
                        <label class="text-sm font-medium" for="edit_update_interval">Update Interval (seconds)</label>
                        <input 
                          type="number" 
                          bind:value={editingSensor.update_interval} 
                          class="w-full p-2 border rounded-md"
                          min="1"
                        />
                      </div>
                      
                      <div class="space-y-2 flex items-center">
                        <label class="inline-flex items-center">
                          <input 
                            type="checkbox" 
                            bind:checked={editingSensor.enabled} 
                            class="mr-2"
                          />
                          <span class="text-sm font-medium">Enabled</span>
                        </label>
                      </div>
                    </div>
                    
                    <div class="mt-4 flex justify-end space-x-2">
                      <Button variant="outline" onclick={cancelEdit}>Cancel</Button>
                      <Button onclick={updateSensor}>Save Changes</Button>
                    </div>
                  </td>
                </tr>
              {:else}
                <tr class="border-b hover:bg-muted/50">
                  <td class="p-3">{sensor.name}</td>
                  <td class="p-3">{sensor.driver}</td>
                  <td class="p-3">
                    <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${sensor.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {sensor.enabled ? 'Active' : 'Disabled'}
                    </span>
                  </td>
                  <td class="p-3">{formatDate(sensor.last_measurement)}</td>
                  <td class="p-3">{formatMeasurement(sensor.id)}</td>
                  <td class="p-3">
                    <div class="flex space-x-2">
                      <Button variant="outline" size="sm" onclick={() => startEdit(sensor)}>Edit</Button>
                      <Button 
                        variant={sensor.enabled ? "destructive" : "default"} 
                        size="sm"
                        onclick={() => toggleSensorEnabled(sensor)}
                      >
                        {sensor.enabled ? 'Disable' : 'Enable'}
                      </Button>
                      <Button variant="destructive" size="sm" onclick={() => deleteSensor(sensor.id || 0)}>Delete</Button>
                    </div>
                  </td>
                </tr>
              {/if}
            {/each}
          </tbody>
        </table>
      </div>
    </div>
  {/if}
</div>