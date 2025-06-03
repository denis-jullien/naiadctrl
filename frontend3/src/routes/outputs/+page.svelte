<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { Button } from "$lib/components/ui/button";
  import { api } from "$lib/api";

  // State using Svelte 5 runes
  let outputs = $state<Record<string, boolean>>({});

  let loading = $state(true);
  let error = $state<string | null>(null);
  let refreshInterval = $state(5); // Refresh interval in seconds
  let refreshTimer: number | null = $state(null);
  let lastRefreshTime = $state<Date | null>(null);
  let pendingActions = $state<Set<number>>(new Set());

  // Fetch data on component mount
  onMount(async () => {
    await loadData();

    // Set up refresh timer
    startRefreshTimer();
  });

  // Clean up on component destroy
  onDestroy(() => {
    console.log('the component is being destroyed');
    stopRefreshTimer();
  });

  // Start the refresh timer
  function startRefreshTimer() {
    stopRefreshTimer(); // Clear any existing timer
    refreshTimer = window.setInterval(async () => {
      console.log('Refreshing outputs data...');
      await loadData(false); // Pass false to indicate this is a background refresh
    }, refreshInterval * 1000);
  }

  // Stop the refresh timer
  function stopRefreshTimer() {
    if (refreshTimer !== null) {
      window.clearInterval(refreshTimer);
      refreshTimer = null;
    }
  }

  // Load all data
  async function loadData(showLoadingState = true) {
    try {
      if (showLoadingState) {
        loading = true;
      }

      // Load all outputs
      outputs = await api.outputs.getAll();
      console.log(outputs)


      // Update last refresh time
      lastRefreshTime = new Date();
    } catch (err) {
      console.error('Failed to load outputs data:', err);
      if (showLoadingState) {
        error = 'Failed to load outputs data. Please check your connection to the backend server.';
      }
    } finally {
      if (showLoadingState) {
        loading = false;
      }
    }
  }

  // Toggle output pin state
  async function toggleOutput(pinNumber: number) {
    try {
      // Add to pending actions to show loading state
      pendingActions = new Set([...pendingActions, pinNumber]);

      const currentState = outputs[pinNumber] || false;
      const newState = !currentState;

      // Set the new state via API
      await api.outputs.set(pinNumber, newState);

      // Update local state immediately for better UX
      outputs[pinNumber] = newState;

      // Refresh data to ensure consistency
      await loadData(false);
    } catch (err) {
      console.error(`Failed to toggle output pin ${pinNumber}:`, err);
      error = `Failed to toggle output pin ${pinNumber}. Please try again.`;
    } finally {
      // Remove from pending actions
      const newPendingActions = new Set(pendingActions);
      newPendingActions.delete(pinNumber);
      pendingActions = newPendingActions;
    }
  }

  // Manual refresh function
  async function refreshData() {
    await loadData();
  }

  // // Get output name from the outputs object
  // function getOutputName(pinNumber: number): string {
  //   for (const [name, pin] of Object.entries(outputs)) {
  //     if (pin === pinNumber) {
  //       return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  //     }
  //   }
  //   return `Pin ${pinNumber}`;
  // }

  // Get sorted pin numbers for consistent display
  // const sortedPinNumbers = $derived(Object.values(outputs).sort((a, b) => a - b));
</script>

<div class="space-y-6">
  <div class="flex justify-between items-center">
    <h1 class="text-3xl font-bold tracking-tight">Output Pins</h1>

    <div class="flex space-x-2">
      <div class="flex items-center space-x-2">
        <span class="text-sm text-muted-foreground">
          {lastRefreshTime ? `Last updated: ${lastRefreshTime.toLocaleTimeString()}` : ''}
        </span>
        <Button variant="outline" size="sm" onclick={refreshData}>
          Refresh
        </Button>
      </div>
    </div>
  </div>

  {#if error}
    <div class="bg-destructive/15 p-4 rounded-md">
      <p class="text-destructive">{error}</p>
      <Button variant="outline" class="mt-2" onclick={() => error = null}>Dismiss</Button>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center h-64">
      <p class="text-lg">Loading output pins...</p>
    </div>
  {:else if Object.keys(outputs).length === 0}
    <div class="bg-muted p-6 rounded-lg text-center">
      <p class="text-muted-foreground">No output pins configured.</p>
    </div>
  {:else}
    <!-- Grid view for output pins -->
    <div class="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
      {#each Object.entries(outputs) as [pinNumber, value]}
        <div class="bg-card text-card-foreground rounded-lg shadow-sm p-6 border">
          <div class="flex flex-col items-center space-y-4">
            <div class="text-center">
              <h3 class="text-lg font-semibold">{pinNumber}</h3>
              <p class="text-sm text-muted-foreground">GPIO Pin {pinNumber}</p>
            </div>

            <div class="flex flex-col items-center space-y-2">
              <!-- Status indicator -->
              <div class={`w-12 h-12 rounded-full flex items-center justify-center ${
                value
                  ? 'bg-green-500 text-white'
                  : 'bg-gray-300 text-gray-600'
              }`}>
                {#if value}
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
                  </svg>
                {:else}
                  <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728L5.636 5.636m12.728 12.728L18.364 5.636M5.636 18.364l12.728-12.728"></path>
                  </svg>
                {/if}
              </div>

              <span class={`text-sm font-medium ${
                value ? 'text-green-600' : 'text-gray-500'
              }`}>
                {value ? 'ON' : 'OFF'}
              </span>
            </div>

            <Button
              variant={value ? "destructive" : "default"}
              size="sm"
              onclick={() => toggleOutput(pinNumber)}
              disabled={pendingActions.has(pinNumber)}
              class="w-full"
            >
              {#if pendingActions.has(pinNumber)}
                <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Setting...
              {:else}
                Turn {value ? 'OFF' : 'ON'}
              {/if}
            </Button>
          </div>
        </div>
      {/each}
    </div>

    <!-- Table view (alternative, you can choose one or both) -->
<!--    <div class="bg-card text-card-foreground rounded-lg shadow-sm overflow-hidden mt-8">-->
<!--      <div class="p-4 border-b">-->
<!--        <h2 class="text-lg font-semibold">Output Pin Details</h2>-->
<!--      </div>-->
<!--      <div class="overflow-x-auto">-->
<!--        <table class="w-full">-->
<!--          <thead>-->
<!--            <tr class="border-b">-->
<!--              <th class="text-left p-3 font-medium">Name</th>-->
<!--              <th class="text-left p-3 font-medium">GPIO Pin</th>-->
<!--              <th class="text-left p-3 font-medium">Status</th>-->
<!--              <th class="text-left p-3 font-medium">Actions</th>-->
<!--            </tr>-->
<!--          </thead>-->
<!--          <tbody>-->
<!--            {#each sortedPinNumbers as pinNumber}-->
<!--              <tr class="border-b hover:bg-muted/50">-->
<!--                <td class="p-3 font-medium">{getOutputName(pinNumber)}</td>-->
<!--                <td class="p-3">GPIO {pinNumber}</td>-->
<!--                <td class="p-3">-->
<!--                  <span class={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${-->
<!--                    outputStates[pinNumber]-->
<!--                      ? 'bg-green-100 text-green-800'-->
<!--                      : 'bg-gray-100 text-gray-800'-->
<!--                  }`}>-->
<!--                    {outputStates[pinNumber] ? 'ON' : 'OFF'}-->
<!--                  </span>-->
<!--                </td>-->
<!--                <td class="p-3">-->
<!--                  <Button-->
<!--                    variant={outputStates[pinNumber] ? "destructive" : "default"}-->
<!--                    size="sm"-->
<!--                    onclick={() => toggleOutput(pinNumber)}-->
<!--                    disabled={pendingActions.has(pinNumber)}-->
<!--                  >-->
<!--                    {#if pendingActions.has(pinNumber)}-->
<!--                      <svg class="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">-->
<!--                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>-->
<!--                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>-->
<!--                      </svg>-->
<!--                      Setting...-->
<!--                    {:else}-->
<!--                      Turn {outputStates[pinNumber] ? 'OFF' : 'ON'}-->
<!--                    {/if}-->
<!--                  </Button>-->
<!--                </td>-->
<!--              </tr>-->
<!--            {/each}-->
<!--          </tbody>-->
<!--        </table>-->
<!--      </div>-->
<!--    </div>-->
  {/if}
</div>