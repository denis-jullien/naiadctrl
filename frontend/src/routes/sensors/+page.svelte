<script>
  import { onMount, onDestroy } from 'svelte';
  import { sensorData, fetchSensorData } from '$lib/stores';
  
  // Update interval (in ms)
  const UPDATE_INTERVAL = 5000; // 5 seconds
  
  // Interval ID for cleanup
  let intervalId;
  
  onMount(async () => {
    // Initial data fetch
    await fetchSensorData();
    
    // Set up interval for regular updates
    intervalId = setInterval(fetchSensorData, UPDATE_INTERVAL);
  });
  
  onDestroy(() => {
    // Clean up interval
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

<h2>Sensor Readings</h2>

<div class="row">
  <!-- pH Sensor -->
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">pH Sensor</h5>
      </div>
      <div class="card-body">
        <div class="d-flex align-items-center">
          <div class="display-1 me-3">{$sensorData.ph ? $sensorData.ph.toFixed(2) : 'N/A'}</div>
          <div>
            <div class="progress" style="height: 30px; width: 200px;">
              {#if $sensorData.ph}
                <div 
                  class="progress-bar {$sensorData.ph < 6 ? 'bg-danger' : $sensorData.ph > 8 ? 'bg-warning' : 'bg-success'}" 
                  role="progressbar" 
                  style="width: {($sensorData.ph / 14) * 100}%"
                >
                  pH {$sensorData.ph.toFixed(2)}
                </div>
              {:else}
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              {/if}
            </div>
            <div class="d-flex justify-content-between mt-1">
              <small>0</small>
              <small>7</small>
              <small>14</small>
            </div>
          </div>
        </div>
        
        <div class="mt-3">
          <h6>About pH:</h6>
          <p>pH measures how acidic or alkaline the water is. For most hydroponic plants, a slightly acidic pH between 5.5 and 6.5 is optimal.</p>
          <ul>
            <li><strong>Below 5.5:</strong> Too acidic, can damage roots and limit nutrient uptake</li>
            <li><strong>5.5 - 6.5:</strong> Optimal range for most plants</li>
            <li><strong>Above 6.5:</strong> Too alkaline, can cause nutrient deficiencies</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
  
  <!-- ORP Sensor -->
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">ORP Sensor</h5>
      </div>
      <div class="card-body">
        <div class="d-flex align-items-center">
          <div class="display-1 me-3">{$sensorData.orp ? $sensorData.orp.toFixed(0) : 'N/A'} <small>mV</small></div>
          <div>
            <div class="progress" style="height: 30px; width: 200px;">
              {#if $sensorData.orp}
                <div 
                  class="progress-bar {$sensorData.orp < 400 ? 'bg-danger' : $sensorData.orp > 800 ? 'bg-warning' : 'bg-success'}" 
                  role="progressbar" 
                  style="width: {($sensorData.orp / 1000) * 100}%"
                >
                  {$sensorData.orp.toFixed(0)} mV
                </div>
              {:else}
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              {/if}
            </div>
            <div class="d-flex justify-content-between mt-1">
              <small>0</small>
              <small>500</small>
              <small>1000</small>
            </div>
          </div>
        </div>
        
        <div class="mt-3">
          <h6>About ORP:</h6>
          <p>ORP (Oxidation-Reduction Potential) measures the ability of water to oxidize contaminants. Higher values indicate better sanitization.</p>
          <ul>
            <li><strong>Below 400 mV:</strong> Poor sanitization, potential for bacterial growth</li>
            <li><strong>400 - 800 mV:</strong> Good range for hydroponic systems</li>
            <li><strong>Above 800 mV:</strong> Very high oxidation, may stress plants</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
  
  <!-- EC Sensor -->
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">EC Sensor</h5>
      </div>
      <div class="card-body">
        <div class="d-flex align-items-center">
          <div class="display-1 me-3">{$sensorData.ec ? $sensorData.ec.toFixed(0) : 'N/A'} <small>μS/cm</small></div>
          <div>
            <div class="progress" style="height: 30px; width: 200px;">
              {#if $sensorData.ec}
                <div 
                  class="progress-bar {$sensorData.ec < 800 ? 'bg-warning' : $sensorData.ec > 2000 ? 'bg-danger' : 'bg-success'}" 
                  role="progressbar" 
                  style="width: {($sensorData.ec / 3000) * 100}%"
                >
                  {$sensorData.ec.toFixed(0)} μS/cm
                </div>
              {:else}
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              {/if}
            </div>
            <div class="d-flex justify-content-between mt-1">
              <small>0</small>
              <small>1500</small>
              <small>3000</small>
            </div>
          </div>
        </div>
        
        <div class="mt-3">
          <h6>About EC:</h6>
          <p>EC (Electrical Conductivity) measures the concentration of dissolved nutrients in the water.</p>
          <ul>
            <li><strong>Below 800 μS/cm:</strong> Low nutrient concentration, may cause deficiencies</li>
            <li><strong>800 - 2000 μS/cm:</strong> Good range for most plants</li>
            <li><strong>Above 2000 μS/cm:</strong> High concentration, may cause nutrient burn</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
  
  <!-- Temperature Sensors -->
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">Temperature & Humidity</h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-6">
            <h6>Water Temperature</h6>
            <div class="display-3">{$sensorData.water_temperature ? $sensorData.water_temperature.toFixed(1) : 'N/A'} <small>°C</small></div>
            <div class="progress mt-2" style="height: 20px;">
              {#if $sensorData.water_temperature}
                <div 
                  class="progress-bar {$sensorData.water_temperature < 18 ? 'bg-info' : $sensorData.water_temperature > 26 ? 'bg-danger' : 'bg-success'}" 
                  role="progressbar" 
                  style="width: {($sensorData.water_temperature / 40) * 100}%"
                >
                  {$sensorData.water_temperature.toFixed(1)}°C
                </div>
              {:else}
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              {/if}
            </div>
            <div class="d-flex justify-content-between">
              <small>0°C</small>
              <small>20°C</small>
              <small>40°C</small>
            </div>
          </div>
          
          <div class="col-md-6">
            <h6>Air Temperature</h6>
            <div class="display-3">{$sensorData.air_temperature ? $sensorData.air_temperature.toFixed(1) : 'N/A'} <small>°C</small></div>
            <div class="progress mt-2" style="height: 20px;">
              {#if $sensorData.air_temperature}
                <div 
                  class="progress-bar {$sensorData.air_temperature < 18 ? 'bg-info' : $sensorData.air_temperature > 30 ? 'bg-danger' : 'bg-success'}" 
                  role="progressbar" 
                  style="width: {($sensorData.air_temperature / 40) * 100}%"
                >
                  {$sensorData.air_temperature.toFixed(1)}°C
                </div>
              {:else}
                <div class="progress-bar" role="progressbar" style="width: 0%"></div>
              {/if}
            </div>
            <div class="d-flex justify-content-between">
              <small>0°C</small>
              <small>20°C</small>
              <small>40°C</small>
            </div>
          </div>
        </div>
        
        <div class="mt-4">
          <h6>Humidity</h6>
          <div class="display-3">{$sensorData.humidity ? $sensorData.humidity.toFixed(1) : 'N/A'} <small>%</small></div>
          <div class="progress mt-2" style="height: 20px;">
            {#if $sensorData.humidity}
              <div 
                class="progress-bar {$sensorData.humidity < 40 ? 'bg-warning' : $sensorData.humidity > 80 ? 'bg-info' : 'bg-success'}" 
                role="progressbar" 
                style="width: {$sensorData.humidity}%"
              >
                {$sensorData.humidity.toFixed(1)}%
              </div>
            {:else}
              <div class="progress-bar" role="progressbar" style="width: 0%"></div>
            {/if}
          </div>
          <div class="d-flex justify-content-between">
            <small>0%</small>
            <small>50%</small>
            <small>100%</small>
          </div>
        </div>
        
        <div class="mt-3">
          <h6>Optimal Ranges:</h6>
          <ul>
            <li><strong>Water Temperature:</strong> 18-26°C (65-78°F)</li>
            <li><strong>Air Temperature:</strong> 18-30°C (65-86°F)</li>
            <li><strong>Humidity:</strong> 40-80% (varies by plant type)</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>

<div class="text-muted mt-2">
  Last updated: {$sensorData.lastUpdated ? $sensorData.lastUpdated.toLocaleString() : 'Never'}
</div>