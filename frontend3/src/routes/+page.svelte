<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button/index.js";
  import { api } from "$lib/api";

  import { Chart } from 'svelte-echarts'

  import { init } from 'echarts'
  import type { EChartsOption } from 'echarts'

  // State using Svelte 5 runes
  let systemStatus = $state<Record<string, any> | null>(null);
  let sensors = $state<any[]>([]);
  let controllers = $state<any[]>([]);
  let recentMeasurements = $state<any[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

    
  // Process measurements for chart display
  function processChartData() {
    if (!recentMeasurements || recentMeasurements.length === 0) 
      return {
        timestamps: [] as string[],
        values: {} as Record<string, number[]>
      };
    
    // Group measurements by type
    const measurementsByType: Record<string, any[]> = {};
    const timestamps: string[] = [];
    const timestampSet = new Set<string>();
    
    // First collect all unique timestamps and group measurements
    recentMeasurements.forEach(m => {
      if (!measurementsByType[m.measurement_type]) {
        measurementsByType[m.measurement_type] = [];
      }
      measurementsByType[m.measurement_type].push(m);
      
      // Format timestamp for display (just time part)
      const date = new Date(m.timestamp);
      const timeStr = date.toLocaleTimeString();
      timestampSet.add(timeStr);
    });
    
    // Convert to sorted array
    const sortedTimestamps = Array.from(timestampSet).sort((a, b) => {
      return new Date('1970/01/01 ' + a).getTime() - new Date('1970/01/01 ' + b).getTime();
    });
    
    // Prepare data for chart
    const values: Record<string, number[]> = {};
    
    // Initialize arrays for each measurement type
    Object.keys(measurementsByType).forEach(type => {
      values[type] = Array(sortedTimestamps.length).fill(null);
    });
    
    // Fill in values at corresponding timestamp positions
    Object.keys(measurementsByType).forEach(type => {
      measurementsByType[type].forEach(m => {
        const date = new Date(m.timestamp);
        const timeStr = date.toLocaleTimeString();
        const index = sortedTimestamps.indexOf(timeStr);
        if (index !== -1) {
          values[type][index] = m.value;
        }
      });
    });
    
    return {
      timestamps: sortedTimestamps,
      values: values
    };
  }

  // Chart data processing
  let chartData = $derived(processChartData());
  

  let options = $derived({
    // title: {
    //   text: 'ECharts Example',
    // },
    xAxis: {
      type: 'category',
      data: chartData.timestamps,
    },
    yAxis: [
      {
        name: 'Flow(m³/s)',
        type: 'value'
      },
      {
        name: 'Rainfall(mm)',
        // nameLocation: 'start',
        alignTicks: true,
        type: 'value',
        // inverse: true
      }
    ],
    dataZoom: [
    {
      type: 'slider',
      show: true,
      xAxisIndex: [0],
      // start: 1,
      // end: 35
    },
    {
      type: 'inside',
      xAxisIndex: [0],
      // start: 1,
      // end: 35
    },
  ],
    series: Object.keys(chartData.values).map((type, index) => {
      return {
        name: type,
        type: 'line',
        data: chartData.values[type],
        yAxisIndex: index % 2  // Alternate between left and right y-axis
      };
    })
  } as EChartsOption)

  // Fetch data on component mount
  onMount(async () => {
    // const interval = setInterval(updateData, 1000)
    try {
      // Load all data in parallel
      const [statusData, sensorsData, controllersData, measurementsData] = await Promise.all([
        api.system.getStatus(),
        api.sensors.getAll(),
        api.controllers.getAll(),
        api.system.getRecentMeasurements(24) // Last 24 hours
      ]);

      systemStatus = statusData;
      sensors = sensorsData;
      controllers = controllersData;
      recentMeasurements = measurementsData;
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      error = 'Failed to load dashboard data. Please check your connection to the backend server.';
    } finally {
      loading = false;
    }
  });

  // Helper function to format date
  function formatDate(dateString: string | null): string {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleString();
  }

</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">Hydroponic System Dashboard</h1>
    

  </div>

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <p class="text-lg">Loading dashboard data...</p>
    </div>
  {:else if error}
    <div class="bg-destructive/15 p-4 rounded-md">
      <p class="text-destructive">{error}</p>
    </div>
  {:else}
    <!-- System Status Card -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
        <h3 class="font-medium">System Status</h3>
        <div class="text-3xl font-bold mt-2">
          {systemStatus?.scheduler_status?.running  ? "Running" : "Stopped"}
        </div>
        <p class="text-muted-foreground text-sm mt-2">
          Last update: {formatDate(systemStatus?.timestamp || null)}
        </p>
      </div>

      <!-- Sensors Overview -->
      <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
        <h3 class="font-medium">Sensors</h3>
        <div class="text-3xl font-bold mt-2">{sensors.length}</div>
        <p class="text-muted-foreground text-sm mt-2">
          {sensors.filter(s => s.enabled).length} active
        </p>
      </div>

      <!-- Controllers Overview -->
      <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
        <h3 class="font-medium">Controllers</h3>
        <div class="text-3xl font-bold mt-2">{controllers.length}</div>
        <p class="text-muted-foreground text-sm mt-2">
          {controllers.filter(c => c.enabled).length} active
        </p>
      </div>

      <!-- Measurements Overview -->
      <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
        <h3 class="font-medium">Measurements (24h)</h3>
        <div class="text-3xl font-bold mt-2">{recentMeasurements.length}</div>
        <p class="text-muted-foreground text-sm mt-2">
          From {sensors.filter(s => s.last_measurement).length} sensors
        </p>
      </div>
    </div>

    <div class="h-[300px] rounded-lg shadow-sm">
      <Chart {init} {options} />
    </div>

    <!-- Recent Measurements -->
    <div class="mt-6">
      <h2 class="text-xl font-semibold mb-4">Recent Measurements</h2>
      
      {#if recentMeasurements.length === 0}
        <p class="text-muted-foreground">No recent measurements available.</p>
      {:else}
        <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b">
                  <th class="text-left p-3 font-medium">Sensor</th>
                  <th class="text-left p-3 font-medium">Type</th>
                  <th class="text-left p-3 font-medium">Value</th>
                  <th class="text-left p-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {#each recentMeasurements.slice(0, 10) as measurement}
                  <tr class="border-b hover:bg-muted/50">
                    <td class="p-3">{sensors.find(s => s.id === measurement.sensor_id)?.name || 'Unknown'}</td>
                    <td class="p-3">{measurement.measurement_type}</td>
                    <td class="p-3">{measurement.value} {measurement.unit}</td>
                    <td class="p-3">{formatDate(measurement.timestamp)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    </div>

    <!-- Quick Links -->
    <div class="grid gap-4 md:grid-cols-3 mt-6">
      <a href="/sensors" class="bg-card text-card-foreground rounded-lg shadow-sm p-6 hover:bg-accent/50 transition-colors">
        <h3 class="font-medium">Manage Sensors</h3>
        <p class="text-muted-foreground text-sm mt-2">View, add, and configure sensors</p>
      </a>
      
      <a href="/controllers" class="bg-card text-card-foreground rounded-lg shadow-sm p-6 hover:bg-accent/50 transition-colors">
        <h3 class="font-medium">Manage Controllers</h3>
        <p class="text-muted-foreground text-sm mt-2">Configure automation controllers</p>
      </a>
      
      <a href="/system" class="bg-card text-card-foreground rounded-lg shadow-sm p-6 hover:bg-accent/50 transition-colors">
        <h3 class="font-medium">System Settings</h3>
        <p class="text-muted-foreground text-sm mt-2">View system status and settings</p>
      </a>
    </div>
  {/if}
</div>