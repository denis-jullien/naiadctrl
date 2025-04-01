<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    controller, 
    fetchControllerData, 
    updateControllerTarget,
    startController,
    stopController
  } from '$lib/state.svelte';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Button } from "$lib/components/ui/button";
  import { Badge } from "$lib/components/ui/badge";
  
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
  $: if (controller.ph) {
    phTarget = controller.ph.target_ph;
    phTolerance = controller.ph.tolerance;
  }
  
  $: if (controller.orp) {
    orpTarget = controller.orp.target_orp;
    orpTolerance = controller.orp.tolerance;
  }
  
  $: if (controller.ec) {
    ecTarget = controller.ec.target_ec;
    ecTolerance = controller.ec.tolerance;
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
    if (controller.ph.running) {
      await stopController('ph');
    } else {
      await startController('ph');
    }
  }
  
  async function toggleORPController() {
    if (controller.orp.running) {
      await stopController('orp');
    } else {
      await startController('orp');
    }
  }
  
  async function toggleECController() {
    if (controller.ec.running) {
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

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">Controllers</h2>
  </div>

  <div class="grid gap-6 md:grid-cols-3">
    <!-- pH Controller -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-xl font-bold">pH Controller</CardTitle>
        {#if controller.ph}
          <Button 
            variant={controller.ph.running ? "destructive" : "default"}
            size="sm"
            onclick={togglePHController}
          >
            {controller.ph.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if controller.ph}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current pH:</span>
              <span class="font-medium">{controller.ph.current_ph ? controller.ph.current_ph.toFixed(2) : 'N/A'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target pH:</span>
              <span class="font-medium">{controller.ph.target_ph.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{controller.ph.tolerance.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={controller.ph.running ? "success" : "secondary"}>
                {controller.ph.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if controller.ph.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date(controller.ph.last_dose_time * 1000).toLocaleString()}</span>
              </div>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handlePHSubmit} class="space-y-4">
            <div class="space-y-2">
              <Label for="phTarget">Target pH</Label>
              <Input id="phTarget" type="number" bind:value={phTarget} step="0.1" min="0" max="14" />
            </div>
            <div class="space-y-2">
              <Label for="phTolerance">Tolerance (±)</Label>
              <Input id="phTolerance" type="number" bind:value={phTolerance} step="0.1" min="0.1" max="1" />
            </div>
            <Button type="submit" class="w-full">Update</Button>
          </form>
        {:else}
          <div class="py-4 text-center text-muted-foreground">Loading pH controller data...</div>
        {/if}
      </CardContent>
    </Card>
    
    <!-- ORP Controller -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-xl font-bold">ORP Controller</CardTitle>
        {#if controller.orp}
          <Button 
            variant={controller.orp.running ? "destructive" : "default"}
            size="sm"
            on:click={toggleORPController}
          >
            {controller.orp.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if controller.orp}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current ORP:</span>
              <span class="font-medium">{controller.orp.current_orp ? controller.orp.current_orp.toFixed(0) : 'N/A'} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target ORP:</span>
              <span class="font-medium">{controller.orp.target_orp.toFixed(0)} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{controller.orp.tolerance.toFixed(0)} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={controller.orp.running ? "success" : "secondary"}>
                {controller.orp.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if controller.orp.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date(controller.orp.last_dose_time * 1000).toLocaleString()}</span>
              </div>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handleORPSubmit} class="space-y-4">
            <div class="space-y-2">
              <Label for="orpTarget">Target ORP (mV)</Label>
              <Input id="orpTarget" type="number" bind:value={orpTarget} step="10" min="0" max="1000" />
            </div>
            <div class="space-y-2">
              <Label for="orpTolerance">Tolerance (±mV)</Label>
              <Input id="orpTolerance" type="number" bind:value={orpTolerance} step="5" min="5" max="50" />
            </div>
            <Button type="submit" class="w-full">Update</Button>
          </form>
        {:else}
          <div class="py-4 text-center text-muted-foreground">Loading ORP controller data...</div>
        {/if}
      </CardContent>
    </Card>
    
    <!-- EC Controller -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-xl font-bold">EC Controller</CardTitle>
        {#if controller.ec}
          <Button 
            variant={controller.ec.running ? "destructive" : "default"}
            size="sm"
            onclick={toggleECController}
          >
            {controller.ec.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if controller.ec}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current EC:</span>
              <span class="font-medium">{controller.ec.current_ec ? controller.ec.current_ec.toFixed(0) : 'N/A'} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target EC:</span>
              <span class="font-medium">{controller.ec.target_ec.toFixed(0)} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{controller.ec.tolerance.toFixed(0)} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={controller.ec.running ? "success" : "secondary"}>
                {controller.ec.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if controller.ec.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date(controller.ec.last_dose_time * 1000).toLocaleString()}</span>
              </div>
            {/if}
          </div>
          
          <form on:submit|preventDefault={handleECSubmit} class="space-y-4">
            <div class="space-y-2">
              <Label for="ecTarget">Target EC (μS/cm)</Label>
              <Input id="ecTarget" type="number" bind:value={ecTarget} step="50" min="0" max="3000" />
            </div>
            <div class="space-y-2">
              <Label for="ecTolerance">Tolerance (±μS/cm)</Label>
              <Input id="ecTolerance" type="number" bind:value={ecTolerance} step="10" min="10" max="200" />
            </div>
            <Button type="submit" class="w-full">Update</Button>
          </form>
        {:else}
          <div class="py-4 text-center text-muted-foreground">Loading EC controller data...</div>
        {/if}
      </CardContent>
    </Card>
  </div>

  <div class="text-sm text-muted-foreground">
    Last updated: {controller.lastUpdated ? controller.lastUpdated.toLocaleString() : 'Never'}
  </div>
</div>