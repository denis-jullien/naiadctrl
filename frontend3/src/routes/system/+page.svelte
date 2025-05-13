<script lang="ts">
  import { onMount } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { api } from "$lib/api";

  // State using Svelte 5 runes
  let systemStatus = $state<Record<string, any> | null>(null);
  let recentMeasurements = $state<any[]>([]);
  let recentActions = $state<any[]>([]);
  let loading = $state(true);
  let error = $state<string | null>(null);
  let timeRange = $state(24); // Default to 24 hours

  // Fetch data on component mount
  onMount(async () => {
    await loadData();
  });

  // Load all system data
  async function loadData() {
    try {
      loading = true;
      // Load all data in parallel
      const [statusData, measurementsData, actionsData] = await Promise.all([
        api.system.getStatus(),
        api.system.getRecentMeasurements(timeRange),
        api.system.getRecentActions(timeRange)
      ]);

      systemStatus = statusData;
      recentMeasurements = measurementsData;
      recentActions = actionsData;
    } catch (err) {
      console.error('Failed to load system data:', err);
      error = 'Failed to load system data. Please check your connection to the backend server.';
    } finally {
      loading = false;
    }
  }

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

  // Update time range and reload data
  async function updateTimeRange(hours: number) {
    timeRange = hours;
    await loadData();
  }
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">System Status</h1>
    
    {#if !loading && systemStatus}
      <Button 
        variant={systemStatus?.scheduler_running ? "destructive" : "default"}
        on:click={toggleScheduler}
      >
        {systemStatus?.scheduler_running ? "Stop Scheduler" : "Start Scheduler"}
      </Button>
    {/if}
  </div>

  {#if error}
    <div class="bg-destructive/15 p-4 rounded-md">
      <p class="text-destructive">{error}</p>
      <Button variant="outline" class="mt-2" on:click={() => error = null}>Dismiss</Button>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <p class="text-lg">Loading system data...</p>
    </div>
  {:else}
    <!-- System Status Card -->
    <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6">
      <h2 class="text-xl font-semibold mb-4">System Information</h2>
      
      <div class="grid gap-4 md:grid-cols-2">
        <div>
          <h3 class="font-medium">Scheduler Status</h3>
          <p class="text-2xl font-bold mt-1">
            {systemStatus?.scheduler_running ? "Running" : "Stopped"}
          </p>
        </div>
        
        <div>
          <h3 class="font-medium">Last Update</h3>
          <p class="text-2xl font-bold mt-1">
            {formatDate(systemStatus?.last_update || null)}
          </p>
        </div>
        
        {#if systemStatus?.uptime}
          <div>
            <h3 class="font-medium">System Uptime</h3>
            <p class="text-2xl font-bold mt-1">
              {systemStatus.uptime}
            </p>
          </div>
        {/if}
        
        {#if systemStatus?.version}
          <div>
            <h3 class="font-medium">System Version</h3>
            <p class="text-2xl font-bold mt-1">
              {systemStatus.version}
            </p>
          </div>
        {/if}
      </div>
    </div>

    <!-- Time Range Selector -->
    <div class="flex justify-end space-x-2 mt-6">
      <Button 
        variant={timeRange === 6 ? "default" : "outline"} 
        on:click={() => updateTimeRange(6)}
      >
        6 Hours
      </Button>
      <Button 
        variant={timeRange === 24 ? "default" : "outline"} 
        on:click={() => updateTimeRange(24)}
      >
        24 Hours
      </Button>
      <Button 
        variant={timeRange === 72 ? "default" : "outline"} 
        on:click={() => updateTimeRange(72)}
      >
        3 Days
      </Button>
    </div>

    <!-- Recent Measurements -->
    <div class="mt-2">
      <h2 class="text-xl font-semibold mb-4">Recent Measurements (Last {timeRange} hours)</h2>
      
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
                    <td class="p-3">{measurement.sensor_name || 'Unknown'}</td>
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

    <!-- Recent Controller Actions -->
    <div class="mt-6">
      <h2 class="text-xl font-semibold mb-4">Recent Controller Actions (Last {timeRange} hours)</h2>
      
      {#if recentActions.length === 0}
        <p class="text-muted-foreground">No recent controller actions available.</p>
      {:else}
        <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden">
          <div class="overflow-x-auto">
            <table class="w-full">
              <thead>
                <tr class="border-b">
                  <th class="text-left p-3 font-medium">Controller</th>
                  <th class="text-left p-3 font-medium">Action</th>
                  <th class="text-left p-3 font-medium">Details</th>
                  <th class="text-left p-3 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {#each recentActions.slice(0, 10) as action}
                  <tr class="border-b hover:bg-muted/50">
                    <td class="p-3">{action.controller_name || 'Unknown'}</td>
                    <td class="p-3">{action.action_type}</td>
                    <td class="p-3">{action.details || '-'}</td>
                    <td class="p-3">{formatDate(action.timestamp)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>