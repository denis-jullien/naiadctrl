<script>
  import { onMount, onDestroy } from 'svelte';
  import { sensorData, controllerData, fetchSensorData, fetchControllerData } from '$lib/stores';
  import { Line } from 'svelte-chartjs';
  import { 
    Chart as ChartJS,
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale
  } from 'chart.js';
  
  // Register ChartJS components
  ChartJS.register(
    Title,
    Tooltip,
    Legend,
    LineElement,
    LinearScale,
    PointElement,
    CategoryScale
  );
  
  // Historical data for charts
  let phHistory = [];
  let orpHistory = [];
  let ecHistory = [];
  let tempHistory = [];
  
  // Time labels for charts
  let timeLabels = [];
  
  // Maximum number of data points to keep
  const MAX_HISTORY = 20;
  
  // Update interval (in ms)
  const UPDATE_INTERVAL = 10000; // 10 seconds
  
  // Interval ID for cleanup
  let intervalId;
  
  // Format time for display
  function formatTime(date) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  // Update historical data
  function updateHistory() {
    const now = new Date();
    const timeLabel = formatTime(now);
    
    // Add new time label
    timeLabels.push(timeLabel);
    if (timeLabels.length > MAX_HISTORY) {
      timeLabels.shift();
    }
    
    // Add new data points
    phHistory.push($sensorData.ph);
    if (phHistory.length > MAX_HISTORY) {
      phHistory.shift();
    }
    
    orpHistory.push($sensorData.orp);
    if (orpHistory.length > MAX_HISTORY) {
      orpHistory.shift();
    }
    
    ecHistory.push($sensorData.ec);
    if (ecHistory.length > MAX_HISTORY) {
      ecHistory.shift();
    }
    
    tempHistory.push($sensorData.water_temperature);
    if (tempHistory.length > MAX_HISTORY) {
      tempHistory.shift();
    }
    
    // Force update
    phHistory = [...phHistory];
    orpHistory = [...orpHistory];
    ecHistory = [...ecHistory];
    tempHistory = [...tempHistory];
    timeLabels = [...timeLabels];
  }
  
  // Chart data
  $: phChartData = {
    labels: timeLabels,
    datasets: [
      {
        label: 'pH',
        data: phHistory,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1
      }
    ]
  };
  
  $: orpChartData = {
    labels: timeLabels,
    datasets: [
      {
        label: 'ORP (mV)',
        data: orpHistory,
        borderColor: 'rgb(153, 102, 255)',
        tension: 0.1
      }
    ]
  };
  
  $: ecChartData = {
    labels: timeLabels,
    datasets: [
      {
        label: 'EC (μS/cm)',
        data: ecHistory,
        borderColor: 'rgb(255, 159, 64)',
        tension: 0.1
      }
    ]
  };
  
  $: tempChartData = {
    labels: timeLabels,
    datasets: [
      {
        label: 'Water Temperature (°C)',
        data: tempHistory,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1
      }
    ]
  };
  
  // Chart options
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: {
        beginAtZero: false
      }
    }
  };
  
  // Fetch data and update history
  async function updateData() {
    await Promise.all([
      fetchSensorData(),
      fetchControllerData()
    ]);
    
    updateHistory();
  }
  
  onMount(async () => {
    // Initial data fetch
    await updateData();
    
    // Set up interval for regular updates
    intervalId = setInterval(updateData, UPDATE_INTERVAL);
  });
  
  onDestroy(() => {
    // Clean up interval
    if (intervalId) {
      clearInterval(intervalId);
    }
  });
</script>

<div class="row mb-4">
  <div class="col-md-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">pH</h5>
        <h2 class="card-text">{$sensorData.ph ? $sensorData.ph.toFixed(2) : 'N/A'}</h2>
        <p class="card-text">
          Target: {$controllerData.ph ? $controllerData.ph.target_ph.toFixed(2) : 'N/A'}
          {#if $controllerData.ph}
            <span class="badge {$controllerData.ph.running ? 'bg-success' : 'bg-secondary'}">
              {$controllerData.ph.running ? 'Running' : 'Stopped'}
            </span>
          {/if}
        </p>
      </div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">ORP</h5>
        <h2 class="card-text">{$sensorData.orp ? $sensorData.orp.toFixed(0) : 'N/A'} mV</h2>
        <p class="card-text">
          Target: {$controllerData.orp ? $controllerData.orp.target_orp.toFixed(0) : 'N/A'} mV
          {#if $controllerData.orp}
            <span class="badge {$controllerData.orp.running ? 'bg-success' : 'bg-secondary'}">
              {$controllerData.orp.running ? 'Running' : 'Stopped'}
            </span>
          {/if}
        </p>
      </div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">EC</h5>
        <h2 class="card-text">{$sensorData.ec ? $sensorData.ec.toFixed(0) : 'N/A'} μS/cm</h2>
        <p class="card-text">
          Target: {$controllerData.ec ? $controllerData.ec.target_ec.toFixed(0) : 'N/A'} μS/cm
          {#if $controllerData.ec}
            <span class="badge {$controllerData.ec.running ? 'bg-success' : 'bg-secondary'}">
              {$controllerData.ec.running ? 'Running' : 'Stopped'}
            </span>
          {/if}
        </p>
      </div>
    </div>
  </div>
  
  <div class="col-md-3">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Temperature</h5>
        <h2 class="card-text">{$sensorData.water_temperature ? $sensorData.water_temperature.toFixed(1) : 'N/A'} °C</h2>
        <p class="card-text">
          Air: {$sensorData.air_temperature ? $sensorData.air_temperature.toFixed(1) : 'N/A'} °C
          Humidity: {$sensorData.humidity ? $sensorData.humidity.toFixed(1) : 'N/A'} %
        </p>
      </div>
    </div>
  </div>
</div>

<div class="row">
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">pH History</h5>
        <div style="height: 300px;">
          <Line data={phChartData} options={chartOptions} />
        </div>
      </div>
    </div>
  </div>
  
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">ORP History</h5>
        <div style="height: 300px;">
          <Line data={orpChartData} options={chartOptions} />
        </div>
      </div>
    </div>
  </div>
  
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">EC History</h5>
        <div style="height: 300px;">
          <Line data={ecChartData} options={chartOptions} />
        </div>
      </div>
    </div>
  </div>
  
  <div class="col-md-6 mb-4">
    <div class="card">
      <div class="card-body">
        <h5 class="card-title">Temperature History</h5>
        <div style="height: 300px;">
          <Line data={tempChartData} options={chartOptions} />
        </div>
      </div>
    </div>
  </div>
</div>

<div class="text-muted mt-2">
  Last updated: {$sensorData.lastUpdated ? $sensorData.lastUpdated.toLocaleString() : 'Never'}
</div>