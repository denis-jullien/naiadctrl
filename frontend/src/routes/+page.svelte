<script>
  import { onMount, onDestroy } from 'svelte';
  import { sensorData, controllerData, sensorHistory, fetchSensorData, fetchControllerData, getChartData } from '$lib/stores';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { LineChart, AreaChart } from 'layerchart';
  
  // Update interval (in ms)
  const UPDATE_INTERVAL = 10000; // 10 seconds
  
  // Interval ID for cleanup
  let intervalId;
  
  // Fetch data
  async function updateData() {
    await Promise.all([
      fetchSensorData(),
      fetchControllerData()
    ]);
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
  
  // Chart options
  const chartOptions = {
    grid: {
      x: {
        show: true
      },
      y: {
        show: true
      }
    },
    tooltip: {
      show: true
    },
    height: 250
  };
</script>

<div class="space-y-8">
  <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
    <!-- pH Card -->
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium">pH</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{$sensorData.ph ? $sensorData.ph.toFixed(2) : 'N/A'}</div>
        <p class="text-xs text-muted-foreground">
          Target: {$controllerData.ph ? $controllerData.ph.target_ph.toFixed(2) : 'N/A'}
          {#if $controllerData.ph}
            <Badge variant={$controllerData.ph.running ? "success" : "secondary"} class="ml-2">
              {$controllerData.ph.running ? 'Running' : 'Stopped'}
            </Badge>
          {/if}
        </p>
      </CardContent>
    </Card>

    <!-- ORP Card -->
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium">ORP</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{$sensorData.orp ? $sensorData.orp.toFixed(0) : 'N/A'} mV</div>
        <p class="text-xs text-muted-foreground">
          Target: {$controllerData.orp ? $controllerData.orp.target_orp.toFixed(0) : 'N/A'} mV
          {#if $controllerData.orp}
            <Badge variant={$controllerData.orp.running ? "success" : "secondary"} class="ml-2">
              {$controllerData.orp.running ? 'Running' : 'Stopped'}
            </Badge>
          {/if}
        </p>
      </CardContent>
    </Card>

    <!-- EC Card -->
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium">EC</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{$sensorData.ec ? $sensorData.ec.toFixed(0) : 'N/A'} μS/cm</div>
        <p class="text-xs text-muted-foreground">
          Target: {$controllerData.ec ? $controllerData.ec.target_ec.toFixed(0) : 'N/A'} μS/cm
          {#if $controllerData.ec}
            <Badge variant={$controllerData.ec.running ? "success" : "secondary"} class="ml-2">
              {$controllerData.ec.running ? 'Running' : 'Stopped'}
            </Badge>
          {/if}
        </p>
      </CardContent>
    </Card>

    <!-- Temperature Card -->
    <Card>
      <CardHeader class="pb-2">
        <CardTitle class="text-sm font-medium">Temperature</CardTitle>
      </CardHeader>
      <CardContent>
        <div class="text-2xl font-bold">{$sensorData.water_temperature ? $sensorData.water_temperature.toFixed(1) : 'N/A'} °C</div>
        <p class="text-xs text-muted-foreground">
          Air: {$sensorData.air_temperature ? $sensorData.air_temperature.toFixed(1) : 'N/A'} °C
          Humidity: {$sensorData.humidity ? $sensorData.humidity.toFixed(1) : 'N/A'} %
        </p>
      </CardContent>
    </Card>
  </div>

  <div class="grid gap-4 md:grid-cols-2">
    <!-- pH Chart -->
    <Card>
      <CardHeader>
        <CardTitle>pH History</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart
          data={getChartData('ph')}
          xKey="x"
          yKey="y"
          options={chartOptions}
          color="#10b981"
        />
      </CardContent>
    </Card>

    <!-- ORP Chart -->
    <Card>
      <CardHeader>
        <CardTitle>ORP History</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart
          data={getChartData('orp')}
          xKey="x"
          yKey="y"
          options={chartOptions}
          color="#6366f1"
        />
      </CardContent>
    </Card>

    <!-- EC Chart -->
    <Card>
      <CardHeader>
        <CardTitle>EC History</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart
          data={getChartData('ec')}
          xKey="x"
          yKey="y"
          options={chartOptions}
          color="#f59e0b"
        />
      </CardContent>
    </Card>

    <!-- Temperature Chart -->
    <Card>
      <CardHeader>
        <CardTitle>Temperature History</CardTitle>
      </CardHeader>
      <CardContent>
        <LineChart
          data={getChartData('water_temperature')}
          xKey="x"
          yKey="y"
          options={chartOptions}
          color="#ef4444"
        />
      </CardContent>
    </Card>
  </div>

  <div class="text-xs text-muted-foreground">
    Last updated: {$sensorData.lastUpdated ? $sensorData.lastUpdated.toLocaleString() : 'Never'}
  </div>
</div>