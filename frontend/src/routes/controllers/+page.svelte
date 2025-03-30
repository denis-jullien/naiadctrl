<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    controllerData, 
    fetchControllerData, 
    updateControllerTarget,
    startController,
    stopController
  } from '$lib/stores';
  
  // Form values
  let phTarget = 0;
  let phTolerance = 0;
  let orpTarget = 0;
  let orpTolerance = 0;
  let ecTarget = 0;
  let ecTolerance = 0;
  
  // Update interval (in ms)
  const UPDATE_INTERVAL = 5000; // 5 seconds
  
  // Interval ID for cleanup
  let intervalId;
  
  // Initialize form values from controller data
  $: if ($controllerData.ph) {
    phTarget = $controllerData.ph.target_ph;
    phTolerance = $controllerData.ph.tolerance;
  }
  
  $: if ($controllerData.orp) {
    orpTarget = $controllerData.orp.target_orp;
    orpTolerance = $controllerData.orp.tolerance;
  }
  
  $: if ($controllerData.ec) {
    ecTarget = $controllerData.ec.target_ec;
    ecTolerance = $controllerData.ec.tolerance;
  }
  
  // Handle form submissions
  async function handlePHSubmit() {
    await updateControllerTarget('ph', parseFloat(phTarget), parseFloat(phTolerance));
  }
  
  async function handleORPSubmit() {
    await updateControllerTarget('orp', parseFloat(orpTarget), parseFloat(orpTolerance));
  }
  
  async function handleECSubmit() {
    await updateControllerTarget('ec', parseFloat(ecTarget), parseFloat(ecTolerance));
  }
  
  // Handle controller start/stop
  async function togglePHController() {
    if ($controllerData.ph.running) {
      await stopController('ph');
    } else {
      await startController('ph');
    }
  }
  
  async function toggleORPController() {
    if ($controllerData.orp.running) {
      await stopController('orp');
    } else {
      await startController('orp');
    }
  }
  
  async function toggleECController() {
    if ($controllerData.ec.running) {
      await stopController('ec');
    } else {
      await startController('ec');
    }
  }
  
  onMount(async () => {
    // Initial data fetch
    await fetchControllerData();
    
    // Set up interval for regular updates
    intervalId = setInterval(fetchControllerData, UPDATE_INTERVAL);
  });
  
  onDestroy(() => {
    // Clean up interval
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

<h2>Controllers</h2>

<div class="row">
  <!-- pH Controller -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">pH Controller</h5>
        {#if $controllerData.ph}
          <button 
            class="btn btn-sm {$controllerData.ph.running ? 'btn-danger' : 'btn-success'}"
            on:click={togglePHController}
          >
            {$controllerData.ph.running ? 'Stop' : 'Start'}
          </button>
        {/if}
      </div>
      <div class="card-body">
        {#if $controllerData.ph}
          <div class="mb-3">
            <p>Current pH: <strong>{$controllerData.ph.current_ph ? $controllerData.ph.current_ph.toFixed(2) : 'N/A'}</strong></p>
            <p>Target pH: <strong>{$controllerData.ph.target_ph.toFixed(2)}</strong></p>
            <p>Tolerance: <strong>±{$controllerData.ph.tolerance.toFixed(2)}</strong></p>
            <p>Status: 
              <span class="badge {$controllerData.ph.running ? 'bg-success' : 'bg-secondary'}">
                {$controllerData.ph.running ? 'Running' : 'Stopped'}
              </span>
            </p>
            {#if $controllerData.ph.last_dose_time > 0}
              <p>Last dose: {new Date($controllerData.ph.last_dose_time * 1000).toLocaleString()}</p>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handlePHSubmit}>
            <div class="mb-3">
              <label for="phTarget" class="form-label">Target pH</label>
              <input type="number" class="form-control" id="phTarget" bind:value={phTarget} step="0.1" min="0" max="14">
            </div>
            <div class="mb-3">
              <label for="phTolerance" class="form-label">Tolerance (±)</label>
              <input type="number" class="form-control" id="phTolerance" bind:value={phTolerance} step="0.1" min="0.1" max="1">
            </div>
            <button type="submit" class="btn btn-primary">Update</button>
          </form>
        {:else}
          <p>Loading pH controller data...</p>
        {/if}
      </div>
    </div>
  </div>
  
  <!-- ORP Controller -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">ORP Controller</h5>
        {#if $controllerData.orp}
          <button 
            class="btn btn-sm {$controllerData.orp.running ? 'btn-danger' : 'btn-success'}"
            on:click={toggleORPController}
          >
            {$controllerData.orp.running ? 'Stop' : 'Start'}
          </button>
        {/if}
      </div>
      <div class="card-body">
        {#if $controllerData.orp}
          <div class="mb-3">
            <p>Current ORP: <strong>{$controllerData.orp.current_orp ? $controllerData.orp.current_orp.toFixed(0) : 'N/A'} mV</strong></p>
            <p>Target ORP: <strong>{$controllerData.orp.target_orp.toFixed(0)} mV</strong></p>
            <p>Tolerance: <strong>±{$controllerData.orp.tolerance.toFixed(0)} mV</strong></p>
            <p>Status: 
              <span class="badge {$controllerData.orp.running ? 'bg-success' : 'bg-secondary'}">
                {$controllerData.orp.running ? 'Running' : 'Stopped'}
              </span>
            </p>
            {#if $controllerData.orp.last_dose_time > 0}
              <p>Last dose: {new Date($controllerData.orp.last_dose_time * 1000).toLocaleString()}</p>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handleORPSubmit}>
            <div class="mb-3">
              <label for="orpTarget" class="form-label">Target ORP (mV)</label>
              <input type="number" class="form-control" id="orpTarget" bind:value={orpTarget} step="10" min="0" max="1000">
            </div>
            <div class="mb-3">
              <label for="orpTolerance" class="form-label">Tolerance (±mV)</label>
              <input type="number" class="form-control" id="orpTolerance" bind:value={orpTolerance} step="5" min="5" max="50">
            </div>
            <button type="submit" class="btn btn-primary">Update</button>
          </form>
        {:else}
          <p>Loading ORP controller data...</p>
        {/if}
      </div>
    </div>
  </div>
  
  <!-- EC Controller -->
  <div class="col-md-4 mb-4">
    <div class="card">
      <div class="card-header d-flex justify-content-between align-items-center">
        <h5 class="mb-0">EC Controller</h5>
        {#if $controllerData.ec}
          <button 
            class="btn btn-sm {$controllerData.ec.running ? 'btn-danger' : 'btn-success'}"
            on:click={toggleECController}
          >
            {$controllerData.ec.running ? 'Stop' : 'Start'}
          </button>
        {/if}
      </div>
      <div class="card-body">
        {#if $controllerData.ec}
          <div class="mb-3">
            <p>Current EC: <strong>{$controllerData.ec.current_ec ? $controllerData.ec.current_ec.toFixed(0) : 'N/A'} μS/cm</strong></p>
            <p>Target EC: <strong>{$controllerData.ec.target_ec.toFixed(0)} μS/cm</strong></p>
            <p>Tolerance: <strong>±{$controllerData.ec.tolerance.toFixed(0)} μS/cm</strong></p>
            <p>Status: 
              <span class="badge {$controllerData.ec.running ? 'bg-success' : 'bg-secondary'}">
                {$controllerData.ec.running ? 'Running' : 'Stopped'}
              </span>
            </p>
            {#if $controllerData.ec.last_dose_time > 0}
              <p>Last dose: {new Date($controllerData.ec.last_dose_time * 1000).toLocaleString()}</p>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handleECSubmit}>
            <div class="mb-3">
              <label for="ecTarget" class="form-label">Target EC (μS/cm)</label>
              <input type="number" class="form-control" id="ecTarget" bind:value={ecTarget} step="50" min="0" max="3000">
            </div>
            <div class="mb-3">
              <label for="ecTolerance" class="form-label">Tolerance (±μS/cm)</label>
              <input type="number" class="form-control" id="ecTolerance" bind:value={ecTolerance} step="10" min="10" max="200">
            </div>
            <button type="submit" class="btn btn-primary">Update</button>
          </form>
        {:else}
          <p>Loading EC controller data...</p>
        {/if}
      </div>
    </div>
  </div>
</div>

<div class="text-muted mt-2">
  Last updated: {$controllerData.lastUpdated ? $controllerData.lastUpdated.toLocaleString() : 'Never'}
</div>