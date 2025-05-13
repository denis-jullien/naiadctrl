<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { api, type Controller, type Sensor, type ControllerType } from "$lib/api";

  // State using Svelte 5 runes
  let controllers = $state<Controller[]>([]);
  let sensors = $state<Sensor[]>([]);
  let controllerTypes = $state<string[]>([]);
  let availableControllers = $state<string[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let showAddForm = $state(false);
  let editingController = $state<Controller | null>(null);
  let selectedControllerId = $state<number | null>(null);
  let controllerSensors = $state<Sensor[]>([]);

  // New controller form state
  let newController = $state<Partial<Controller>>({
    name: '',
    controller_type: undefined,
    description: '',
    update_interval: 60,
    enabled: true,
    config: '{}'
  });

  // Fetch data on component mount
  onMount(async () => {
    try {
      // Load controllers, sensors, and controller types in parallel
      const [controllersData, sensorsData, typesData, availableData] = await Promise.all([
        api.controllers.getAll(),
        api.sensors.getAll(),
        api.controllers.getTypes(),
        api.controllers.getAvailableControllers()
      ]);

      controllers = controllersData;
      sensors = sensorsData;
      controllerTypes = typesData;
      availableControllers = availableData;
    } catch (err) {
      console.error('Failed to load controllers data:', err);
      error = 'Failed to load controllers data. Please check your connection to the backend server.';
    } finally {
      loading = false;
    }
  });

  // Helper function to format date
  function formatDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  }

  // Toggle add form visibility
  function toggleAddForm() {
    showAddForm = !showAddForm;
    if (!showAddForm) {
      // Reset form when closing
      newController = {
        name: '',
        controller_type: undefined,
        description: '',
        update_interval: 60,
        enabled: true,
        config: '{}'
      };
    }
  }

  // Create new controller
  async function createController() {
    try {
      const created = await api.controllers.create(newController as Controller);
      controllers = [...controllers, created];
      toggleAddForm(); // Close form after successful creation
    } catch (err) {
      console.error('Failed to create controller:', err);
      error = 'Failed to create controller. Please try again.';
    }
  }

  // Edit controller
  function startEdit(controller: Controller) {
    editingController = { ...controller };
  }

  // Cancel edit
  function cancelEdit() {
    editingController = null;
  }

  // Save edited controller
  async function updateController() {
    if (!editingController || !editingController.id) return;
    
    try {
      const updated = await api.controllers.update(editingController.id, editingController);
      controllers = controllers.map(c => c.id === updated.id ? updated : c);
      editingController = null; // Close edit form
    } catch (err) {
      console.error('Failed to update controller:', err);
      error = 'Failed to update controller. Please try again.';
    }
  }

  // Delete controller
  async function deleteController(id: number) {
    if (!confirm('Are you sure you want to delete this controller?')) return;
    
    try {
      await api.controllers.delete(id);
      controllers = controllers.filter(c => c.id !== id);
      if (selectedControllerId === id) {
        selectedControllerId = null;
        controllerSensors = [];
      }
    } catch (err) {
      console.error('Failed to delete controller:', err);
      error = 'Failed to delete controller. Please try again.';
    }
  }

  // Toggle controller enabled state
  async function toggleControllerEnabled(controller: Controller) {
    if (!controller.id) return;
    
    try {
      const updated = await api.controllers.update(controller.id, {
        ...controller,
        enabled: !controller.enabled
      });
      controllers = controllers.map(c => c.id === updated.id ? updated : c);
    } catch (err) {
      console.error('Failed to update controller:', err);
      error = 'Failed to update controller. Please try again.';
    }
  }

  // Load controller sensors
  async function loadControllerSensors(controllerId: number) {
    selectedControllerId = controllerId;
    try {
      controllerSensors = await api.controllers.getSensors(controllerId);
    } catch (err) {
      console.error('Failed to load controller sensors:', err);
      error = 'Failed to load controller sensors. Please try again.';
    }
  }

  // Add sensor to controller
  async function addSensorToController(sensorId: number) {
    if (!selectedControllerId) return;
    
    try {
      await api.controllers.addSensor(selectedControllerId, sensorId);
      // Reload controller sensors
      controllerSensors = await api.controllers.getSensors(selectedControllerId);
    } catch (err) {
      console.error('Failed to add sensor to controller:', err);
      error = 'Failed to add sensor to controller. Please try again.';
    }
  }

  // Remove sensor from controller
  async function removeSensorFromController(sensorId: number) {
    if (!selectedControllerId) return;
    
    try {
      await api.controllers.removeSensor(selectedControllerId, sensorId);
      // Reload controller sensors
      controllerSensors = await api.controllers.getSensors(selectedControllerId);
    } catch (err) {
      console.error('Failed to remove sensor from controller:', err);
      error = 'Failed to remove sensor from controller. Please try again.';
    }
  }

  // Manually process controller
  async function processController(controllerId: number) {
    try {
      await api.controllers.process(controllerId);
      // Refresh controllers list to get updated last_run
      controllers = await api.controllers.getAll();
    } catch (err) {
      console.error('Failed to process controller:', err);
      error = 'Failed to process controller. Please try again.';
    }
  }

  // Get available sensors (not already assigned to selected controller)
  const availableSensors = $derived.by(() => {
    if (!selectedControllerId || !controllerSensors) return [];
    const controllerSensorIds = controllerSensors.map(s => s.id);
    return sensors.filter(s => !controllerSensorIds.includes(s.id));
  });
  
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">Controllers</h1>
    
    <Button onclick={toggleAddForm}>
      {showAddForm ? 'Cancel' : 'Add Controller'}
    </Button>
  </div>

  {#if error}
    <div class="bg-destructive/15 p-4 rounded-md">
      <p class="text-destructive">{error}</p>
      <Button variant="outline" class="mt-2" onclick={() => error = null}>Dismiss</Button>
    </div>
  {/if}

  {#if showAddForm}
    <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
      <h2 class="text-xl font-semibold mb-4">Add New Controller</h2>
      
      <div class="grid gap-4 md:grid-cols-2">
        <div class="space-y-2">
          <label class="text-sm font-medium" for="name">Name</label>
          <input 
            id="name"
            type="text" 
            bind:value={newController.name} 
            class="w-full p-2 border rounded-md"
            placeholder="pH Controller 1"
          />
        </div>
        
        <div class="space-y-2">
          <label class="text-sm font-medium" for="controller_type">Controller Type</label>
          <select 
            id="controller_type"
            bind:value={newController.controller_type} 
            class="w-full p-2 border rounded-md"
          >
            <option value="">Select a type</option>
            {#each controllerTypes as type}
              <option value={type}>{type}</option>
            {/each}
          </select>
        </div>
        
        <div class="space-y-2 md:col-span-2">
          <label class="text-sm font-medium" for="description">Description</label>
          <textarea 
            id="description"
            bind:value={newController.description} 
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
            bind:value={newController.update_interval} 
            class="w-full p-2 border rounded-md"
            min="1"
          />
        </div>
        
        <div class="space-y-2 flex items-center">
          <label class="inline-flex items-center">
            <input 
              type="checkbox" 
              bind:checked={newController.enabled} 
              class="mr-2"
            />
            <span class="text-sm font-medium">Enabled</span>
          </label>
        </div>
      </div>
      
      <div class="mt-6 flex justify-end space-x-2">
        <Button variant="outline" onclick={toggleAddForm}>Cancel</Button>
        <Button 
          onclick={createController}
          disabled={!newController.name || !newController.controller_type}
        >
          Create Controller
        </Button>
      </div>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <p class="text-lg">Loading controllers...</p>
    </div>
  {:else if controllers.length === 0}
    <div class="bg-muted p-6 rounded-lg text-center">
      <p class="text-muted-foreground">No controllers found. Add your first controller to get started.</p>
    </div>
  {:else}
    <div class="grid gap-6 md:grid-cols-2">
      <!-- Controllers List -->
      <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden">
        <div class="p-4 border-b">
          <h2 class="text-xl font-semibold">Controllers</h2>
        </div>
        <div class="overflow-y-auto max-h-[600px]">
          <div class="divide-y">
            {#each controllers as controller}
              {#if editingController && editingController.id === controller.id}
                <div class="p-4 bg-muted/50">
                  <div class="grid gap-4 md:grid-cols-2">
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Name</label>
                      <input 
                        type="text" 
                        bind:value={editingController.name} 
                        class="w-full p-2 border rounded-md"
                      />
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Controller Type</label>
                      <select 
                        bind:value={editingController.controller_type} 
                        class="w-full p-2 border rounded-md"
                      >
                        {#each controllerTypes as type}
                          <option value={type}>{type}</option>
                        {/each}
                      </select>
                    </div>
                    
                    <div class="space-y-2 md:col-span-2">
                      <label class="text-sm font-medium">Description</label>
                      <textarea 
                        bind:value={editingController.description} 
                        class="w-full p-2 border rounded-md"
                        rows="2"
                      ></textarea>
                    </div>
                    
                    <div class="space-y-2">
                      <label class="text-sm font-medium">Update Interval (seconds)</label>
                      <input 
                        type="number" 
                        bind:value={editingController.update_interval} 
                        class="w-full p-2 border rounded-md"
                        min="1"
                      />
                    </div>
                    
                    <div class="space-y-2 flex items-center">
                      <label class="inline-flex items-center">
                        <input 
                          type="checkbox" 
                          bind:checked={editingController.enabled} 
                          class="mr-2"
                        />
                        <span class="text-sm font-medium">Enabled</span>
                      </label>
                    </div>
                  </div>
                  
                  <div class="mt-4 flex justify-end space-x-2">
                    <Button variant="outline" onclick={cancelEdit}>Cancel</Button>
                    <Button onclick={updateController}>Save Changes</Button>
                  </div>
                </div>
              {:else}
                <div 
                  class="p-4 hover:bg-muted/50 cursor-pointer {selectedControllerId === controller.id ? 'bg-muted/50' : ''}"
                  onclick={() => loadControllerSensors(controller.id || 0)}
                >
                  <div class="flex justify-between items-start">
                    <div>
                      <h3 class="font-medium">{controller.name}</h3>
                      <p class="text-sm text-muted-foreground">{controller.controller_type}</p>
                      {#if controller.description}
                        <p class="text-sm mt-1">{controller.description}</p>
                      {/if}
                      <div class="mt-2 flex items-center space-x-2">
                        <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${controller.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                          {controller.enabled ? 'Active' : 'Disabled'}
                        </span>
                        <span class="text-xs text-muted-foreground">
                          Last run: {formatDate(controller.last_run)}
                        </span>
                      </div>
                    </div>
                    <div class="flex space-x-2">
                      <Button variant="outline" size="sm" onclick={(e) => { e.stopPropagation(); startEdit(controller); }}>Edit</Button>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onclick={(e) => { e.stopPropagation(); processController(controller.id || 0); }}
                      >
                        Run Now
                      </Button>
                      <Button 
                        variant={controller.enabled ? "destructive" : "default"} 
                        size="sm"
                        onclick={(e) => { e.stopPropagation(); toggleControllerEnabled(controller); }}
                      >
                        {controller.enabled ? 'Disable' : 'Enable'}
                      </Button>
                      <Button 
                        variant="destructive" 
                        size="sm" 
                        onclick={(e) => { e.stopPropagation(); deleteController(controller.id || 0); }}
                      >
                        Delete
                      </Button>
                    </div>
                  </div>
                </div>
              {/if}
            {/each}
          </div>
        </div>
      </div>

      <!-- Controller Sensors -->
      <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden">
        <div class="p-4 border-b">
          <h2 class="text-xl font-semibold">
            {selectedControllerId ? 
              `Sensors for ${controllers.find(c => c.id === selectedControllerId)?.name}` : 
              'Select a controller to manage sensors'}
          </h2>
        </div>
        
        {#if !selectedControllerId}
          <div class="p-6 text-center">
            <p class="text-muted-foreground">Click on a controller to manage its sensors</p>
          </div>
        {:else}
          <div class="p-4">
            <h3 class="font-medium mb-2">Assigned Sensors</h3>
            {#if controllerSensors.length === 0}
              <p class="text-sm text-muted-foreground mb-4">No sensors assigned to this controller</p>
            {:else}
              <div class="space-y-2 mb-4">
                {#each controllerSensors as sensor}
                  <div class="flex justify-between items-center p-2 border rounded-md">
                    <div>
                      <p class="font-medium">{sensor.name}</p>
                      <p class="text-xs text-muted-foreground">{sensor.driver}</p>
                    </div>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onclick={() => removeSensorFromController(sensor.id || 0)}
                    >
                      Remove
                    </Button>
                  </div>
                {/each}
              </div>
            {/if}

            <h3 class="font-medium mb-2 mt-6">Available Sensors</h3>
            {#if availableSensors.length === 0}
              <p class="text-sm text-muted-foreground">No available sensors to add</p>
            {:else}
              <div class="space-y-2">
                {#each availableSensors as sensor}
                  <div class="flex justify-between items-center p-2 border rounded-md">
                    <div>
                      <p class="font-medium">{sensor.name}</p>
                      <p class="text-xs text-muted-foreground">{sensor.driver}</p>
                    </div>
                    <Button 
                      size="sm"
                      onclick={() => addSensorToController(sensor.id || 0)}
                    >
                      Add
                    </Button>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>