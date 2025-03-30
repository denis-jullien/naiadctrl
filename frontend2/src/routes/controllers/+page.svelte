<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    controllerData, 
    fetchControllerData, 
    updateControllerTarget,
    startController,
    stopController
  } from '$lib/stores';
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

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">Controllers</h2>
  </div>

  <div class="grid gap-6 md:grid-cols-3">
    <!-- pH Controller -->
    <Card>
      <CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle class="text-xl font-bold">pH Controller</CardTitle>
        {#if $controllerData.ph}
          <Button 
            variant={$controllerData.ph.running ? "destructive" : "default"}
            size="sm"
            on:click={togglePHController}
          >
            {$controllerData.ph.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if $controllerData.ph}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current pH:</span>
              <span class="font-medium">{$controllerData.ph.current_ph ? $controllerData.ph.current_ph.toFixed(2) : 'N/A'}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target pH:</span>
              <span class="font-medium">{$controllerData.ph.target_ph.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{$controllerData.ph.tolerance.toFixed(2)}</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={$controllerData.ph.running ? "success" : "secondary"}>
                {$controllerData.ph.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if $controllerData.ph.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date($controllerData.ph.last_dose_time * 1000).toLocaleString()}</span>
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
        {#if $controllerData.orp}
          <Button 
            variant={$controllerData.orp.running ? "destructive" : "default"}
            size="sm"
            on:click={toggleORPController}
          >
            {$controllerData.orp.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if $controllerData.orp}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current ORP:</span>
              <span class="font-medium">{$controllerData.orp.current_orp ? $controllerData.orp.current_orp.toFixed(0) : 'N/A'} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target ORP:</span>
              <span class="font-medium">{$controllerData.orp.target_orp.toFixed(0)} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{$controllerData.orp.tolerance.toFixed(0)} mV</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={$controllerData.orp.running ? "success" : "secondary"}>
                {$controllerData.orp.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if $controllerData.orp.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date($controllerData.orp.last_dose_time * 1000).toLocaleString()}</span>
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
        {#if $controllerData.ec}
          <Button 
            variant={$controllerData.ec.running ? "destructive" : "default"}
            size="sm"
            on:click={toggleECController}
          >
            {$controllerData.ec.running ? 'Stop' : 'Start'}
          </Button>
        {/if}
      </CardHeader>
      <CardContent>
        {#if $controllerData.ec}
          <div class="space-y-2 mb-4">
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Current EC:</span>
              <span class="font-medium">{$controllerData.ec.current_ec ? $controllerData.ec.current_ec.toFixed(0) : 'N/A'} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Target EC:</span>
              <span class="font-medium">{$controllerData.ec.target_ec.toFixed(0)} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Tolerance:</span>
              <span class="font-medium">±{$controllerData.ec.tolerance.toFixed(0)} μS/cm</span>
            </div>
            <div class="flex justify-between">
              <span class="text-sm text-muted-foreground">Status:</span>
              <Badge variant={$controllerData.ec.running ? "success" : "secondary"}>
                {$controllerData.ec.running ? 'Running' : 'Stopped'}
              </Badge>
            </div>
            {#if $controllerData.ec.last_dose_time > 0}
              <div class="flex justify-between">
                <span class="text-sm text-muted-foreground">Last dose:</span>
                <span class="text-sm">{new Date($controllerData.ec.last_dose_time * 1000).toLocaleString()}</span>
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
    Last updated: {$controllerData.lastUpdated ? $controllerData.lastUpdated.toLocaleString() : 'Never'}
  </div>
</div>