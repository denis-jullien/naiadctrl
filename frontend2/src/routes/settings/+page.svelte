<script>
  import { onMount } from 'svelte';
  import { configData, fetchConfig } from '$lib/stores';
  
  // Form values
  let config = null;
  let statusMessage = '';
  
  // Update configuration
  async function updateConfig() {
    try {
      statusMessage = 'Updating configuration...';
      
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (result.success) {
        statusMessage = 'Configuration updated successfully!';
        await fetchConfig();
      } else {
        statusMessage = 'Failed to update configuration: ' + (result.error || 'Unknown error');
      }
    } catch (error) {
      statusMessage = 'Error: ' + error.message;
    }
  }
  
  onMount(async () => {
    // Initial data fetch
    await fetchConfig();
    config = JSON.parse(JSON.stringify($configData));
  });
  
  // Update local config when store changes
  $: if ($configData && !config) {
    config = JSON.parse(JSON.stringify($configData));
  }
  
</script>

<h2>System Settings</h2>

{#if config}
  <div class="row">
    <div class="col-md-12 mb-4">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">Configuration</h5>
        </div>
        <div class="card-body">
          <ul class="nav nav-tabs" id="configTabs" role="tablist">
            <li class="nav-item" role="presentation">
              <button class="nav-link active" id="sensors-tab" data-bs-toggle="tab" data-bs-target="#sensors" type="button" role="tab">
                Sensors
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" id="controllers-tab" data-bs-toggle="tab" data-bs-target="#controllers" type="button" role="tab">
                Controllers
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" id="outputs-tab" data-bs-toggle="tab" data-bs-target="#outputs" type="button" role="tab">
                Outputs
              </button>
            </li>
            <li class="nav-item" role="presentation">
              <button class="nav-link" id="api-tab" data-bs-toggle="tab" data-bs-target="#api" type="button" role="tab">
                API
              </button>
            </li>
          </ul>
          
          <div class="tab-content p-3" id="configTabsContent">
            <!-- Sensors Tab -->
            <div class="tab-pane fade show active" id="sensors" role="tabpanel">
              <h5>pH Sensor</h5>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">SCK Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ph.sck_pin}>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Data Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ph.data_pin}>
                </div>
              </div>
              
              <h5>ORP Sensor</h5>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">SCK Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.orp.sck_pin}>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Data Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.orp.data_pin}>
                </div>
              </div>
              
              <h5>EC Sensor</h5>
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label">SCK Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ec.sck_pin}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Data Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ec.data_pin}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">PWM Pin</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ec.pwm_pin}>
                </div>
              </div>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">K Value</label>
                  <input type="number" class="form-control" bind:value={config.sensors.ec.k_value} step="0.1">
                </div>
              </div>
              
              <h5>Environment Sensor</h5>
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">I2C Bus</label>
                  <input type="number" class="form-control" bind:value={config.sensors.environment.i2c_bus}>
                </div>
              </div>
            </div>
            
            <!-- Controllers Tab -->
            <div class="tab-pane fade" id="controllers" role="tabpanel">
              <h5>pH Controller</h5>
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label">Check Interval (seconds)</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ph.check_interval}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Acid Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ph.acid_pump_pin}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Base Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ph.base_pump_pin}>
                </div>
              </div>
              
              <h5>ORP Controller</h5>
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label">Check Interval (seconds)</label>
                  <input type="number" class="form-control" bind:value={config.controllers.orp.check_interval}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Increase Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.orp.increase_pump_pin}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Decrease Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.orp.decrease_pump_pin}>
                </div>
              </div>
              
              <h5>EC Controller</h5>
              <div class="row mb-3">
                <div class="col-md-4">
                  <label class="form-label">Check Interval (seconds)</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ec.check_interval}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Nutrient Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ec.nutrient_pump_pin}>
                </div>
                <div class="col-md-4">
                  <label class="form-label">Water Pump Pin</label>
                  <input type="number" class="form-control" bind:value={config.controllers.ec.water_pump_pin}>
                </div>
              </div>
            </div>
            
            <!-- Outputs Tab -->
            <div class="tab-pane fade" id="outputs" role="tabpanel">
              <h5>MOSFET Pins</h5>
              <div class="mb-3">
                <label class="form-label">GPIO Pins (comma-separated)</label>
                <input 
                  type="text" 
                  class="form-control" 
                  value={config.outputs.mosfet_pins.join(', ')}
                  on:input={(e) => {
                    const pins = e.target.value.split(',').map(pin => parseInt(pin.trim())).filter(pin => !isNaN(pin));
                    config.outputs.mosfet_pins = pins;
                  }}
                >
              </div>
            </div>
            
            <!-- API Tab -->
            <div class="tab-pane fade" id="api" role="tabpanel">
              <div class="row mb-3">
                <div class="col-md-6">
                  <label class="form-label">Host</label>
                  <input type="text" class="form-control" bind:value={config.api.host}>
                </div>
                <div class="col-md-6">
                  <label class="form-label">Port</label>
                  <input type="number" class="form-control" bind:value={config.api.port}>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-3">
            <button class="btn btn-primary" on:click={updateConfig}>Save Configuration</button>
            
            {#if statusMessage}
              <div class="alert alert-info mt-3">{statusMessage}</div>
            {/if}
          </div>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="alert alert-info">Loading configuration...</div>
{/if}

