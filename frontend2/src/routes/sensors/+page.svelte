<script>
  import { onMount, onDestroy } from 'svelte';
  import { sensorData, fetchSensorData } from '$lib/stores';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Progress } from "$lib/components/ui/progress";
  
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
  
  // Helper function to get progress color based on value
  function getPhColor(value) {
    if (!value) return "bg-gray-200";
    return value < 6 ? "bg-destructive" : value > 8 ? "bg-warning" : "bg-success";
  }
  
  function getOrpColor(value) {
    if (!value) return "bg-gray-200";
    return value < 400 ? "bg-destructive" : value > 800 ? "bg-warning" : "bg-success";
  }
  
  function getEcColor(value) {
    if (!value) return "bg-gray-200";
    return value < 800 ? "bg-warning" : value > 2000 ? "bg-destructive" : "bg-success";
  }
  
  function getTempColor(value) {
    if (!value) return "bg-gray-200";
    return value < 18 ? "bg-blue-500" : value > 26 ? "bg-destructive" : "bg-success";
  }
  
  function getAirTempColor(value) {
    if (!value) return "bg-gray-200";
    return value < 18 ? "bg-blue-500" : value > 30 ? "bg-destructive" : "bg-success";
  }
  
  function getHumidityColor(value) {
    if (!value) return "bg-gray-200";
    return value < 40 ? "bg-warning" : value > 80 ? "bg-blue-500" : "bg-success";
  }
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">Sensor Readings</h2>
  </div>

  <div class="grid gap-6 md:grid-cols-2">
    <!-- pH Sensor -->
    <Card>
      <CardHeader>
        <CardTitle>pH Sensor</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center gap-4 mb-4">
          <div class="text-5xl font-bold">{$sensorData.ph ? $sensorData.ph.toFixed(2) : 'N/A'}</div>
          <div class="w-full max-w-md">
            <div class="h-8 w-full bg-secondary rounded-md overflow-hidden">
              {#if $sensorData.ph}
                <div 
                  class="h-full {getPhColor($sensorData.ph)} flex items-center justify-center text-white font-medium"
                  style="width: {($sensorData.ph / 14) * 100}%"
                >
                  pH {$sensorData.ph.toFixed(2)}
                </div>
              {/if}
            </div>
            <div class="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>0</span>
              <span>7</span>
              <span>14</span>
            </div>
          </div>
        </div>
        
        <div class="space-y-2">
          <h3 class="font-medium">About pH:</h3>
          <p class="text-sm text-muted-foreground">pH measures how acidic or alkaline the water is. For most hydroponic plants, a slightly acidic pH between 5.5 and 6.5 is optimal.</p>
          <ul class="text-sm space-y-1">
            <li><span class="font-medium">Below 5.5:</span> Too acidic, can damage roots and limit nutrient uptake</li>
            <li><span class="font-medium">5.5 - 6.5:</span> Optimal range for most plants</li>
            <li><span class="font-medium">Above 6.5:</span> Too alkaline, can cause nutrient deficiencies</li>
          </ul>
        </div>
      </CardContent>
    </Card>
    
    <!-- ORP Sensor -->
    <Card>
      <CardHeader>
        <CardTitle>ORP Sensor</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center gap-4 mb-4">
          <div class="text-5xl font-bold">{$sensorData.orp ? $sensorData.orp.toFixed(0) : 'N/A'} <span class="text-lg font-normal">mV</span></div>
          <div class="w-full max-w-md">
            <div class="h-8 w-full bg-secondary rounded-md overflow-hidden">
              {#if $sensorData.orp}
                <div 
                  class="h-full {getOrpColor($sensorData.orp)} flex items-center justify-center text-white font-medium"
                  style="width: {($sensorData.orp / 1000) * 100}%"
                >
                  {$sensorData.orp.toFixed(0)} mV
                </div>
              {/if}
            </div>
            <div class="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>0</span>
              <span>500</span>
              <span>1000</span>
            </div>
          </div>
        </div>
        
        <div class="space-y-2">
          <h3 class="font-medium">About ORP:</h3>
          <p class="text-sm text-muted-foreground">ORP (Oxidation-Reduction Potential) measures the ability of water to oxidize contaminants. Higher values indicate better sanitization.</p>
          <ul class="text-sm space-y-1">
            <li><span class="font-medium">Below 400 mV:</span> Poor sanitization, potential for bacterial growth</li>
            <li><span class="font-medium">400 - 800 mV:</span> Good range for hydroponic systems</li>
            <li><span class="font-medium">Above 800 mV:</span> Very high oxidation, may stress plants</li>
          </ul>
        </div>
      </CardContent>
    </Card>
    
    <!-- EC Sensor -->
    <Card>
      <CardHeader>
        <CardTitle>EC Sensor</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="flex items-center gap-4 mb-4">
          <div class="text-5xl font-bold">{$sensorData.ec ? $sensorData.ec.toFixed(0) : 'N/A'} <span class="text-lg font-normal">μS/cm</span></div>
          <div class="w-full max-w-md">
            <div class="h-8 w-full bg-secondary rounded-md overflow-hidden">
              {#if $sensorData.ec}
                <div 
                  class="h-full {getEcColor($sensorData.ec)} flex items-center justify-center text-white font-medium"
                  style="width: {($sensorData.ec / 3000) * 100}%"
                >
                  {$sensorData.ec.toFixed(0)} μS/cm
                </div>
              {/if}
            </div>
            <div class="flex justify-between mt-1 text-xs text-muted-foreground">
              <span>0</span>
              <span>1500</span>
              <span>3000</span>
            </div>
          </div>
        </div>
        
        <div class="space-y-2">
          <h3 class="font-medium">About EC:</h3>
          <p class="text-sm text-muted-foreground">EC (Electrical Conductivity) measures the concentration of dissolved nutrients in the water.</p>
          <ul class="text-sm space-y-1">
            <li><span class="font-medium">Below 800 μS/cm:</span> Low nutrient concentration, may cause deficiencies</li>
            <li><span class="font-medium">800 - 2000 μS/cm:</span> Good range for most plants</li>
            <li><span class="font-medium">Above 2000 μS/cm:</span> High concentration, may cause nutrient burn</li>
          </ul>
        </div>
      </CardContent>
    </Card>
    
    <!-- Temperature & Humidity -->
    <Card>
      <CardHeader>
        <CardTitle>Temperature & Humidity</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div class="space-y-2">
            <h3 class="font-medium">Water Temperature</h3>
            <div class="text-3xl font-bold">{$sensorData.water_temperature ? $sensorData.water_temperature.toFixed(1) : 'N/A'} <span class="text-sm font-normal">°C</span></div>
            <div class="h-6 w-full bg-secondary rounded-md overflow-hidden">
              {#if $sensorData.water_temperature}
                <div 
                  class="h-full {getTempColor($sensorData.water_temperature)} flex items-center justify-center text-white text-xs font-medium"
                  style="width: {($sensorData.water_temperature / 40) * 100}%"
                >
                  {$sensorData.water_temperature.toFixed(1)}°C
                </div>
              {/if}
            </div>
            <div class="flex justify-between text-xs text-muted-foreground">
              <span>0°C</span>
              <span>20°C</span>
              <span>40°C</span>
            </div>
          </div>
          
          <div class="space-y-2">
            <h3 class="font-medium">Air Temperature</h3>
            <div class="text-3xl font-bold">{$sensorData.air_temperature ? $sensorData.air_temperature.toFixed(1) : 'N/A'} <span class="text-sm font-normal">°C</span></div>
            <div class="h-6 w-full bg-secondary rounded-md overflow-hidden">
              {#if $sensorData.air_temperature}
                <div 
                  class="h-full {getAirTempColor($sensorData.air_temperature)} flex items-center justify-center text-white text-xs font-medium"
                  style="width: {($sensorData.air_temperature / 40) * 100}%"
                >
                  {$sensorData.air_temperature.toFixed(1)}°C
                </div>
              {/if}
            </div>
            <div class="flex justify-between text-xs text-muted-foreground">
              <span>0°C</span>
              <span>20°C</span>
              <span>40°C</span>
            </div>
          </div>
        </div>
        
        <div class="space-y-2 mt-4">
          <h3 class="font-medium">Humidity</h3>
          <div class="text-3xl font-bold">{$sensorData.humidity ? $sensorData.humidity.toFixed(1) : 'N/A'} <span class="text-sm font-normal">%</span></div>
          <div class="h-6 w-full bg-secondary rounded-md overflow-hidden">
            {#if $sensorData.humidity}
              <div 
                class="h-full {getHumidityColor($sensorData.humidity)} flex items-center justify-center text-white text-xs font-medium"
                style="width: {$sensorData.humidity}%"
              >
                {$sensorData.humidity.toFixed(1)}%
              </div>
            {/if}
          </div>
          <div class="flex justify-between text-xs text-muted-foreground">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
        </div>
        
        <div class="mt-4 space-y-2">
          <h3 class="font-medium">Optimal Ranges:</h3>
          <ul class="text-sm space-y-1">
            <li><span class="font-medium">Water Temperature:</span> 18-26°C (65-78°F)</li>
            <li><span class="font-medium">Air Temperature:</span> 18-30°C (65-86°F)</li>
            <li><span class="font-medium">Humidity:</span> 40-80% (varies by plant type)</li>
          </ul>
        </div>
      </CardContent>
    </Card>
  </div>

  <div class="text-sm text-muted-foreground">
    Last updated: {$sensorData.lastUpdated ? $sensorData.lastUpdated.toLocaleString() : 'Never'}
  </div>
</div>