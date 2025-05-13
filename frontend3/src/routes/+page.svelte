<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button/index.js";
  import { api } from "$lib/api";

  // State using Svelte 5 runes
  let systemStatus = $state<Record<string, any> | null>(null);
  let sensors = $state<any[]>([]);
  let controllers = $state<any[]>([]);
  let recentMeasurements = $state<any[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);

  // Fetch data on component mount
  onMount(async () => {
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

  // Toggle scheduler
  async function toggleScheduler() {
    try {
      if (systemStatus?.scheduler_running) {
        await api.system.stopScheduler();
      } else {
        await api.system.startScheduler();
      }
      // Refresh status
      systemStatus = await api.system.getStatus();
    } catch (err) {
      console.error('Failed to toggle scheduler:', err);
      error = 'Failed to toggle scheduler. Please try again.';
    }
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">Hydroponic System Dashboard</h1>
    
    {#if !loading && systemStatus}
      <Button 
        variant={systemStatus?.scheduler_running ? "destructive" : "default"}
        on:click={toggleScheduler}
      >
        {systemStatus?.scheduler_running ? "Stop Scheduler" : "Start Scheduler"}
      </Button>
    {/if}
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
          {systemStatus?.scheduler_running ? "Running" : "Stopped"}
        </div>
        <p class="text-muted-foreground text-sm mt-2">
          Last update: {formatDate(systemStatus?.last_update || null)}
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