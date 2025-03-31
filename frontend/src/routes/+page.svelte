<script>
  import { onMount, onDestroy } from 'svelte';
  import { sensorData, controllerData, sensorHistory, fetchSensorData, fetchControllerData, fetchSensorHistory, getChartData } from '$lib/stores';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Badge } from "$lib/components/ui/badge";
  import { Button } from "$lib/components/ui/button";
  import { LineChart, AreaChart } from 'layerchart';
  import {
    Axis,
    Canvas,
    Chart,
    Highlight,
    Labels,
    Legend,
    LinearGradient,
    Spline,
    Svg,
    Text,
    Tooltip,
    pivotLonger,
  } from 'layerchart';
  import { scaleOrdinal, scaleSequential, scaleTime } from 'd3-scale';
  import { formatDate, PeriodType } from '@layerstack/utils';
  import { extent, flatGroup, group, ticks } from 'd3-array';
  
  // Update interval (in ms)
  const UPDATE_INTERVAL = 10000; // 10 seconds
  
  // Interval ID for cleanup
  let intervalId;

  const dateSeriesData = [
  {
    "date": new Date('2025-03-01T23:00:00.000Z'),
    "value": 60
  },
  {
    "date": new Date('2025-03-02T23:00:00.000Z'),
    "value": 96
  },
  {
    "date": new Date('2025-03-03T23:00:00.000Z'),
    "value": 65
  },
  {
    "date": new Date('2025-03-04T23:00:00.000Z'),
    "value": 75
  },
  {
    "date": new Date('2025-03-05T23:00:00.000Z'),
    "value": 78
  },
  {
    "date": new Date('2025-03-06T23:00:00.000Z'),
    "value": 50
  },
  {
    "date": new Date('2025-03-07T23:00:00.000Z'),
    "value": 83
  },
  {
    "date": new Date('2025-03-08T23:00:00.000Z'),
    "value": 70
  },
  {
    "date": new Date('2025-03-09T23:00:00.000Z'),
    "value": 57
  },
  {
    "date": new Date('2025-03-10T23:00:00.000Z'),
    "value": 55
  },
  {
    "date": new Date('2025-03-11T23:00:00.000Z'),
    "value": 86
  },
  {
    "date": new Date('2025-03-12T23:00:00.000Z'),
    "value": 73
  },
  {
    "date": new Date('2025-03-13T23:00:00.000Z'),
    "value": 58
  },
  {
    "date": new Date('2025-03-14T23:00:00.000Z'),
    "value": 85
  },
  {
    "date": new Date('2025-03-15T23:00:00.000Z'),
    "value": 85
  },
  {
    "date": new Date('2025-03-16T23:00:00.000Z'),
    "value": 57
  },
  {
    "date": new Date('2025-03-17T23:00:00.000Z'),
    "value": 93
  },
  {
    "date": new Date('2025-03-18T23:00:00.000Z'),
    "value": 89
  },
  {
    "date": new Date('2025-03-19T23:00:00.000Z'),
    "value": 59
  },
  {
    "date": new Date('2025-03-20T23:00:00.000Z'),
    "value": 57
  },
  {
    "date": new Date('2025-03-21T23:00:00.000Z'),
    "value": 61
  },
  {
    "date": new Date('2025-03-22T23:00:00.000Z'),
    "value": 78
  },
  {
    "date": new Date('2025-03-23T23:00:00.000Z'),
    "value": 71
  },
  {
    "date": new Date('2025-03-24T23:00:00.000Z'),
    "value": 92
  },
  {
    "date": new Date('2025-03-25T23:00:00.000Z'),
    "value": 87
  },
  {
    "date": new Date('2025-03-26T23:00:00.000Z'),
    "value": 87
  },
  {
    "date": new Date('2025-03-27T23:00:00.000Z'),
    "value": 83
  },
  {
    "date": new Date('2025-03-28T23:00:00.000Z'),
    "value": 83
  },
  {
    "date": new Date('2025-03-29T23:00:00.000Z'),
    "value": 70
  },
  {
    "date": new Date('2025-03-30T22:00:00.000Z'),
    "value": 94
  }
]
  let renderContext = 'svg';
  let debug = false;
  let dynamicData = ticks(-2, 2, 200).map(Math.sin);
  
  // Fetch data
  async function updateData() {
    await Promise.all([
      fetchSensorData(),
      fetchControllerData()
    ]);
  }
  
  onMount(async () => {
    // Initial data fetch
    await Promise.all([
      updateData(),
      fetchSensorHistory()
    ]);
    
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
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">Dashboard</h2>
    <div class="space-x-2">
      <Button variant="outline" onclick={updateData}>Refresh Data</Button>
      <Button variant="outline" onclick={fetchSensorHistory}>Refresh History</Button>
    </div>
  </div>
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
        <div class="h-[300px] ">
          <LineChart
          data={dynamicData.map((d, i) => ({ date: i, value: d }))}
          x="date"
          series={[{ key: "value", color: "hsl(var(--primary))" }]}
          props={{
            yAxis: { tweened: true },
            grid: { tweened: true },
          }}
        />
        </div>
        <!-- <div
          class="h-[300px]"
          on:mousemove={(e) => {
            const x = e.clientX;
            const y = e.clientY;
            dynamicData = dynamicData.slice(-200).concat(Math.atan2(x, y));
          }}
        >
        <LineChart
          data={dynamicData.map((d, i) => ({ x: i, y: d }))}
          x="x"
          series={[{ key: "y", color: "hsl(var(--primary))" }]}
          props={{
            yAxis: { tweened: true },
            grid: { tweened: true },
          }}
        />
      </div> -->
      </CardContent>
    </Card>
  </div>

 

  <div class="text-xs text-muted-foreground">
    Last updated: {$sensorData.lastUpdated ? $sensorData.lastUpdated.toLocaleString() : 'Never'}
  </div>
</div>