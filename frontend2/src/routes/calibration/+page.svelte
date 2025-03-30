<script>
  import { onMount } from 'svelte';
  import { sensorData, fetchSensorData, calibratePH, calibrateORP, calibrateEC } from '$lib/stores';
  
  // Form values
  let phVoltage = 0;
  let phValue = 7.0;
  let orpValue = 650;
  let ecValue = 1500;
  
  // Status messages
  let phStatus = '';
  let orpStatus = '';
  let ecStatus = '';
  
  // Handle form submissions
  async function handlePHCalibration() {
    phStatus = 'Calibrating...';
    const result = await calibratePH(parseFloat(phVoltage), parseFloat(phValue));
    if (result && result.success) {
      phStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      phStatus = 'Calibration failed. Please try again.';
    }
  }
  
  async function handleORPCalibration() {
    orpStatus = 'Calibrating...';
    const result = await calibrateORP(parseFloat(orpValue));
    if (result && result.success) {
      orpStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      orpStatus = 'Calibration failed. Please try again.';
    }
  }
  
  async function handleECCalibration() {
    ecStatus = 'Calibrating...';
    const result = await calibrateEC(parseFloat(ecValue));
    if (result && result.success) {
      ecStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      ecStatus = 'Calibration failed. Please try again.';
    }
  }
  
  onMount(async () => {
    // Initial data fetch
    await fetchSensorData();
  });
</script>

<h2>Sensor Calibration</h2>

<div class="row">
  <!-- pH Calibration -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">pH Calibration</h5>
      </div>
      <div class="card-body">
        <p>Current pH reading: <strong>{$sensorData.ph ? $sensorData.ph.toFixed(2) : 'N/A'}</strong></p>
        
        <form on:submit|preventDefault={handlePHCalibration}>
          <div class="mb-3">
            <label for="phVoltage" class="form-label">Voltage Reading (V)</label>
            <input type="number" class="form-control" id="phVoltage" bind:value={phVoltage} step="0.01" min="0" max="5">
            <div class="form-text">Enter the voltage reading from the pH probe</div>
          </div>
          <div class="mb-3">
            <label for="phValue" class="form-label">Known pH Value</label>
            <input type="number" class="form-control" id="phValue" bind:value={phValue} step="0.1" min="0" max="14">
            <div class="form-text">Enter the known pH value of your calibration solution</div>
          </div>
          <button type="submit" class="btn btn-primary">Calibrate</button>
          
          {#if phStatus}
            <div class="alert alert-info mt-3">{phStatus}</div>
          {/if}
        </form>
        
        <div class="mt-3">
          <h6>Calibration Instructions:</h6>
          <ol>
            <li>Place the pH probe in a calibration solution with a known pH value</li>
            <li>Enter the voltage reading from the sensor</li>
            <li>Enter the known pH value of the solution</li>
            <li>Click "Calibrate"</li>
            <li>Repeat with a different pH solution for better accuracy</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
  
  <!-- ORP Calibration -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">ORP Calibration</h5>
      </div>
      <div class="card-body">
        <p>Current ORP reading: <strong>{$sensorData.orp ? $sensorData.orp.toFixed(0) : 'N/A'} mV</strong></p>
        
        <form on:submit|preventDefault={handleORPCalibration}>
          <div class="mb-3">
            <label for="orpValue" class="form-label">Known ORP Value (mV)</label>
            <input type="number" class="form-control" id="orpValue" bind:value={orpValue} step="10" min="0" max="1000">
            <div class="form-text">Enter the known ORP value of your calibration solution</div>
          </div>
          <button type="submit" class="btn btn-primary">Calibrate</button>
          
          {#if orpStatus}
            <div class="alert alert-info mt-3">{orpStatus}</div>
          {/if}
        </form>
        
        <div class="mt-3">
          <h6>Calibration Instructions:</h6>
          <ol>
            <li>Place the ORP probe in a calibration solution with a known ORP value</li>
            <li>Enter the known ORP value of the solution in mV</li>
            <li>Click "Calibrate"</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
  
  <!-- EC Calibration -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header">
        <h5 class="mb-0">EC Calibration</h5>
      </div>
      <div class="card-body">
        <p>Current EC reading: <strong>{$sensorData.ec ? $sensorData.ec.toFixed(0) : 'N/A'} μS/cm</strong></p>
        
        <form on:submit|preventDefault={handleECCalibration}>
          <div class="mb-3">
            <label for="ecValue" class="form-label">Known EC Value (μS/cm)</label>
            <input type="number" class="form-control" id="ecValue" bind:value={ecValue} step="50" min="0" max="3000">
            <div class="form-text">Enter the known EC value of your calibration solution</div>
          </div>
          <button type="submit" class="btn btn-primary">Calibrate</button>
          
          {#if ecStatus}
            <div class="alert alert-info mt-3">{ecStatus}</div>
          {/if}
        </form>
        
        <div class="mt-3">
          <h6>Calibration Instructions:</h6>
          <ol>
            <li>Place the EC probe in a calibration solution with a known EC value</li>
            <li>Enter the known EC value of the solution in μS/cm</li>
            <li>Click "Calibrate"</li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</div>