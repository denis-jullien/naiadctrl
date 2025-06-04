<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { SimpleForm } from "@sjsf/form";
  import { resolver } from "@sjsf/form/resolvers/basic";
  import { translation } from "@sjsf/form/translations/en";
  import { api, type Controller, type Sensor, type ControllerType, type ControllerCreate } from "$lib/api";

  import { theme, setThemeContext } from '@sjsf/shadcn4-theme';
  import * as components from '@sjsf/shadcn4-theme/new-york';

  setThemeContext({ components })

  // State using Svelte 5 runes
  let controllers = $state<Controller[]>([]);
  let sensors = $state<Sensor[]>([]);
  let controllerTypes = $state<string[]>([]);
  let controllerSchemas = $state<Record<string, any>>({});
  let loading = $state(true);
  let error = $state<string | null>(null);
  let showAddForm = $state(false);
  let editingController = $state<Controller | null>(null);
  let selectedControllerId = $state<number | null>(null);
  let controllerSensors = $state<Sensor[]>([]);
  let selectedControllerType = $state<string>('');
  let loadingSchema = $state(false);

  // New controller form state
  let newControllerData = $state<any>({});
  let editControllerData = $state<any>({});

  // Fetch data on component mount
  onMount(async () => {
    try {
      // Load controllers, sensors, and controller types in parallel
      const [controllersData, sensorsData, typesData] = await Promise.all([
        api.controllers.getAll(),
        api.sensors.getAll(),
        api.controllers.getTypes()
      ]);

      controllers = controllersData;
      sensors = sensorsData;
      controllerTypes = typesData;

      // Pre-load all controller schemas
      await loadAllControllerSchemas();
    } catch (err) {
      console.error('Failed to load controllers data:', err);
      error = 'Failed to load controllers data. Please check your connection to the backend server.';
    } finally {
      loading = false;
    }
  });

  // Load all controller schemas
  async function loadAllControllerSchemas() {
    try {
      const schemas: Record<string, any> = {};
      for (const type of controllerTypes) {
        try {
          const response = await api.controllers.getSchema(type);
          console.log(`Loaded schema for ${type}:`, response);
          schemas[type] = response
        } catch (err) {
          console.warn(`Failed to load schema for ${type}:`, err);
        }
      }
      controllerSchemas = schemas;
    } catch (err) {
      console.error('Failed to load controller schemas:', err);
    }
  }

  // Helper function to format date
  function formatDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  }

  // Toggle add form visibility
  async function toggleAddForm() {
    showAddForm = !showAddForm;
    if (!showAddForm) {
      // Reset form when closing
      selectedControllerType = '';
      newControllerData = {};
    }
  }

  // Handle controller type selection for new controller
  async function onControllerTypeSelected(type: string) {
    selectedControllerType = type;
    newControllerData = {}; // Reset form data
  }

  // Create new controller
  async function createController(formData: any) {
    try {
      const controllerCreate: ControllerCreate = {
        name: formData.name || '',
        controller_type: selectedControllerType as ControllerType,
        description: formData.description || '',
        update_interval: formData.update_interval || 60,
        enabled: formData.enabled !== false,
        config: formData.config || {}
      };

      const created = await api.controllers.create(controllerCreate);
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
    // Parse config if it's a string
    const config = typeof controller.config === 'string' 
      ? JSON.parse(controller.config) 
      : controller.config;
    
    editControllerData = {
      name: controller.name,
      description: controller.description || '',
      update_interval: controller.update_interval,
      enabled: controller.enabled,
      config: config
    };
  }

  // Cancel edit
  function cancelEdit() {
    editingController = null;
    editControllerData = {};
  }

  // Save edited controller
  async function updateController(formData: any) {
    if (!editingController || !editingController.id) return;
    
    try {
      const controllerUpdate: ControllerCreate = {
        name: formData.name || editingController.name,
        controller_type: editingController.controller_type,
        description: formData.description || '',
        update_interval: formData.update_interval || 60,
        enabled: formData.enabled !== false,
        config: formData.config || {}
      };
      
      const updated = await api.controllers.update(editingController.id, controllerUpdate);
      controllers = controllers.map(c => c.id === updated.id ? updated : c);
      editingController = null; // Close edit form
      editControllerData = {};
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
      const controllerUpdate: ControllerCreate = {
        name: controller.name,
        controller_type: controller.controller_type,
        description: controller.description,
        update_interval: controller.update_interval,
        enabled: !controller.enabled,
        config: typeof controller.config === 'string' 
          ? JSON.parse(controller.config) 
          : controller.config
      };
      
      const updated = await api.controllers.update(controller.id, controllerUpdate);
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

  // Create base form schema for controller fields
  function getBaseControllerSchema() {
    return {
      type: "object",
      title: "Controller Configuration",
      properties: {
        name: {
          type: "string",
          title: "Controller Name",
          description: "A unique name for this controller"
        },
        description: {
          type: "string",
          title: "Description",
          description: "Optional description of what this controller does"
        },
        update_interval: {
          type: "integer",
          title: "Update Interval (seconds)",
          description: "How often the controller should run",
          minimum: 1,
          default: 60
        },
        enabled: {
          type: "boolean",
          title: "Enabled",
          description: "Whether this controller is active",
          default: true
        }
      },
      required: ["name"]
    };
  }

  // Merge base schema with controller-specific schema
  function getMergedSchema(controllerType: string) {
    const baseSchema = getBaseControllerSchema();
    const typeSchema = controllerSchemas[controllerType];
    
    if (!typeSchema) {
      return baseSchema;
    }

    // Merge the schemas
    return {
      ...baseSchema,
      properties: {
        ...baseSchema.properties,
        config: {
          type: "object",
          title: "Controller Configuration",
          description: "Type-specific configuration for this controller",
          ...typeSchema
        }
      }
    };
  }

  // Get initial form data for editing
  function getInitialEditData(controller: Controller) {
    const config = typeof controller.config === 'string' 
      ? JSON.parse(controller.config) 
      : controller.config;
    
    return {
      name: controller.name,
      description: controller.description || '',
      update_interval: controller.update_interval,
      enabled: controller.enabled,
      config: config
    };
  }
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
      
      {#if !selectedControllerType}
        <div class="space-y-4">
          <div class="space-y-2">
            <label class="text-sm font-medium">Select Controller Type</label>
            <select 
              bind:value={selectedControllerType} 
              onchange={() => onControllerTypeSelected(selectedControllerType)}
              class="w-full p-2 border rounded-md"
            >
              <option value="">Choose a controller type...</option>
              {#each controllerTypes as type}
                <option value={type}>{type}</option>
              {/each}
            </select>
          </div>
        </div>
      {:else}
        <div class="mb-4">
          <Button 
            variant="outline" 
            onclick={() => { selectedControllerType = ''; newControllerData = {}; }}
          >
            ← Change Controller Type
          </Button>
          <p class="text-sm text-muted-foreground mt-2">
            Creating: <strong>{selectedControllerType}</strong>
          </p>
        </div>

        {#if controllerSchemas[selectedControllerType]}
          <SimpleForm
            {theme}
            {translation}
            {resolver}
            schema={getMergedSchema(selectedControllerType)}
            validator={{ isValid: () => true }}
            value={newControllerData}
            onSubmit={createController}
            class="flex flex-col gap-4"
          />
        {:else}
          <div class="p-4 bg-muted rounded-md">
            <p class="text-muted-foreground">Loading schema for {selectedControllerType}...</p>
          </div>
        {/if}
      {/if}
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
                  <div class="mb-4">
                    <h3 class="font-medium">Editing: {controller.name}</h3>
                    <p class="text-sm text-muted-foreground">Type: {controller.controller_type}</p>
                  </div>

                  {#if controllerSchemas[controller.controller_type]}
                    <SimpleForm
                      {theme}
                      {translation}
                      {resolver}
                      schema={getMergedSchema(controller.controller_type)}
                      validator={{ isValid: () => true }}
                      value={getInitialEditData(controller)}
                      onSubmit={updateController}
                    />
                  {:else}
                    <div class="p-4 bg-muted rounded-md mb-4">
                      <p class="text-muted-foreground">Schema not available for {controller.controller_type}</p>
                    </div>
                  {/if}
                  
                  <div class="mt-4 flex justify-end">
                    <Button variant="outline" onclick={cancelEdit}>Cancel</Button>
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