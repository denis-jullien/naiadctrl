<script>
  import { onMount } from 'svelte';
  import { sensor, fetchSensorData, calibratePH, calibrateORP, calibrateEC } from '$lib/state.svelte';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Button } from "$lib/components/ui/button";
  import { Alert, AlertDescription } from "$lib/components/ui/alert";
  
  // Form values
  let phVoltage = 0;
  let phValue = 7.0;
  let orpValue = 650;
  let ecValue = 1500;
  
  // Status messages
  let phStatus = '';
  let orpStatus = '';
  let ecStatus = '';
  
  // Handle form submissions
  async function handlePHCalibration() {
    phStatus = 'Calibrating...';
    const result = await calibratePH(parseFloat(phVoltage), parseFloat(phValue));
    if (result && result.success) {
      phStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      phStatus = 'Calibration failed. Please try again.';
    }
  }
  
  async function handleORPCalibration() {
    orpStatus = 'Calibrating...';
    const result = await calibrateORP(parseFloat(orpValue));
    if (result && result.success) {
      orpStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      orpStatus = 'Calibration failed. Please try again.';
    }
  }
  
  async function handleECCalibration() {
    ecStatus = 'Calibrating...';
    const result = await calibrateEC(parseFloat(ecValue));
    if (result && result.success) {
      ecStatus = 'Calibration successful!';
      await fetchSensorData();
    } else {
      ecStatus = 'Calibration failed. Please try again.';
    }
  }
  
  onMount(async () => {
    // Initial data fetch
    await fetchSensorData();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">Sensor Calibration</h2>
  </div>

  <div class="grid gap-6 md:grid-cols-3">
    <!-- pH Calibration -->
    <Card>
      <CardHeader>
        <CardTitle>pH Calibration</CardTitle>
        <CardDescription>
          Current pH reading: <span class="font-medium">{sensor.ph ? sensor.ph.toFixed(2) : 'N/A'}</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form on:submit|preventDefault={handlePHCalibration} class="space-y-4">
          <div class="space-y-2">
            <Label for="phVoltage">Voltage Reading (V)</Label>
            <Input id="phVoltage" type="number" bind:value={phVoltage} step="0.01" min="0" max="5" />
            <p class="text-sm text-muted-foreground">Enter the voltage reading from the pH probe</p>
          </div>
          <div class="space-y-2">
            <Label for="phValue">Known pH Value</Label>
            <Input id="phValue" type="number" bind:value={phValue} step="0.1" min="0" max="14" />
            <p class="text-sm text-muted-foreground">Enter the known pH value of your calibration solution</p>
          </div>
          <Button type="submit" class="w-full">Calibrate</Button>
          
          {#if phStatus}
            <Alert>
              <AlertDescription>{phStatus}</AlertDescription>
            </Alert>
          {/if}
        </form>
        
        <div class="mt-6 space-y-2">
          <h3 class="font-medium">Calibration Instructions:</h3>
          <ol class="list-decimal list-inside space-y-1 text-sm">
            <li>Place the pH probe in a calibration solution with a known pH value</li>
            <li>Enter the voltage reading from the sensor</li>
            <li>Enter the known pH value of the solution</li>
            <li>Click "Calibrate"</li>
            <li>Repeat with a different pH solution for better accuracy</li>
          </ol>
        </div>
      </CardContent>
    </Card>
    
    <!-- ORP Calibration -->
    <Card>
      <CardHeader>
        <CardTitle>ORP Calibration</CardTitle>
        <CardDescription>
          Current ORP reading: <span class="font-medium">{sensor.orp ? sensor.orp.toFixed(0) : 'N/A'} mV</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form on:submit|preventDefault={handleORPCalibration} class="space-y-4">
          <div class="space-y-2">
            <Label for="orpValue">Known ORP Value (mV)</Label>
            <Input id="orpValue" type="number" bind:value={orpValue} step="10" min="0" max="1000" />
            <p class="text-sm text-muted-foreground">Enter the known ORP value of your calibration solution</p>
          </div>
          <Button type="submit" class="w-full">Calibrate</Button>
          
          {#if orpStatus}
            <Alert>
              <AlertDescription>{orpStatus}</AlertDescription>
            </Alert>
          {/if}
        </form>
        
        <div class="mt-6 space-y-2">
          <h3 class="font-medium">Calibration Instructions:</h3>
          <ol class="list-decimal list-inside space-y-1 text-sm">
            <li>Place the ORP probe in a calibration solution with a known ORP value</li>
            <li>Enter the known ORP value of the solution in mV</li>
            <li>Click "Calibrate"</li>
          </ol>
        </div>
      </CardContent>
    </Card>
    
    <!-- EC Calibration -->
    <Card>
      <CardHeader>
        <CardTitle>EC Calibration</CardTitle>
        <CardDescription>
          Current EC reading: <span class="font-medium">{sensor.ec ? sensor.ec.toFixed(0) : 'N/A'} μS/cm</span>
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form on:submit|preventDefault={handleECCalibration} class="space-y-4">
          <div class="space-y-2">
            <Label for="ecValue">Known EC Value (μS/cm)</Label>
            <Input id="ecValue" type="number" bind:value={ecValue} step="50" min="0" max="3000" />
            <p class="text-sm text-muted-foreground">Enter the known EC value of your calibration solution</p>
          </div>
          <Button type="submit" class="w-full">Calibrate</Button>
          
          {#if ecStatus}
            <Alert>
              <AlertDescription>{ecStatus}</AlertDescription>
            </Alert>
          {/if}
        </form>
        
        <div class="mt-6 space-y-2">
          <h3 class="font-medium">Calibration Instructions:</h3>
          <ol class="list-decimal list-inside space-y-1 text-sm">
            <li>Place the EC probe in a calibration solution with a known EC value</li>
            <li>Enter the known EC value of the solution in μS/cm</li>
            <li>Click "Calibrate"</li>
          </ol>
        </div>
      </CardContent>
    </Card>
  </div>
</div>