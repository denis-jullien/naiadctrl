<script>
  import { onMount } from 'svelte';
  import { configData, fetchConfig } from '$lib/stores';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Tabs, TabsContent, TabsList, TabsTrigger } from "$lib/components/ui/tabs";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Button } from "$lib/components/ui/button";
  import { Alert, AlertDescription } from "$lib/components/ui/alert";
  
  // Form values
  let config = null;
  let statusMessage = '';
  let activeTab = "sensors";
  
  // Update configuration
  async function updateConfig() {
    try {
      statusMessage = 'Updating configuration...';
      
      const response = await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      
      const result = await response.json();
      
      if (result.success) {
        statusMessage = 'Configuration updated successfully!';
        await fetchConfig();
      } else {
        statusMessage = 'Failed to update configuration: ' + (result.error || 'Unknown error');
      }
    } catch (error) {
      statusMessage = 'Error: ' + error.message;
    }
  }
  
  onMount(async () => {
    // Initial data fetch
    await fetchConfig();
    config = JSON.parse(JSON.stringify($configData));
  });
  
  // Update local config when store changes
  $: if ($configData && !config) {
    config = JSON.parse(JSON.stringify($configData));
  }
  
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">System Settings</h2>
  </div>

  {#if config}
    <Card>
      <CardHeader>
        <CardTitle>Configuration</CardTitle>
        <CardDescription>Manage your system configuration settings</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(value) => activeTab = value} class="w-full">
          <TabsList class="grid w-full grid-cols-4">
            <TabsTrigger value="sensors">Sensors</TabsTrigger>
            <TabsTrigger value="controllers">Controllers</TabsTrigger>
            <TabsTrigger value="outputs">Outputs</TabsTrigger>
            <TabsTrigger value="api">API</TabsTrigger>
          </TabsList>
          
          <!-- Sensors Tab -->
          <TabsContent value="sensors" class="space-y-6">
            <div class="space-y-4">
              <div>
                <h3 class="text-lg font-medium">pH Sensor</h3>
                <div class="grid grid-cols-2 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="ph-sck-pin">SCK Pin</Label>
                    <Input id="ph-sck-pin" type="number" bind:value={config.sensors.ph.sck_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ph-data-pin">Data Pin</Label>
                    <Input id="ph-data-pin" type="number" bind:value={config.sensors.ph.data_pin} />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 class="text-lg font-medium">ORP Sensor</h3>
                <div class="grid grid-cols-2 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="orp-sck-pin">SCK Pin</Label>
                    <Input id="orp-sck-pin" type="number" bind:value={config.sensors.orp.sck_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="orp-data-pin">Data Pin</Label>
                    <Input id="orp-data-pin" type="number" bind:value={config.sensors.orp.data_pin} />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 class="text-lg font-medium">EC Sensor</h3>
                <div class="grid grid-cols-3 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="ec-sck-pin">SCK Pin</Label>
                    <Input id="ec-sck-pin" type="number" bind:value={config.sensors.ec.sck_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ec-data-pin">Data Pin</Label>
                    <Input id="ec-data-pin" type="number" bind:value={config.sensors.ec.data_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ec-pwm-pin">PWM Pin</Label>
                    <Input id="ec-pwm-pin" type="number" bind:value={config.sensors.ec.pwm_pin} />
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-4 mt-4">
                  <div class="space-y-2">
                    <Label for="ec-k-value">K Value</Label>
                    <Input id="ec-k-value" type="number" bind:value={config.sensors.ec.k_value} step="0.1" />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 class="text-lg font-medium">Environment Sensor</h3>
                <div class="grid grid-cols-2 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="env-i2c-bus">I2C Bus</Label>
                    <Input id="env-i2c-bus" type="number" bind:value={config.sensors.environment.i2c_bus} />
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <!-- Controllers Tab -->
          <TabsContent value="controllers" class="space-y-6">
            <div class="space-y-4">
              <div>
                <h3 class="text-lg font-medium">pH Controller</h3>
                <div class="grid grid-cols-3 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="ph-check-interval">Check Interval (seconds)</Label>
                    <Input id="ph-check-interval" type="number" bind:value={config.controllers.ph.check_interval} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ph-acid-pump-pin">Acid Pump Pin</Label>
                    <Input id="ph-acid-pump-pin" type="number" bind:value={config.controllers.ph.acid_pump_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ph-base-pump-pin">Base Pump Pin</Label>
                    <Input id="ph-base-pump-pin" type="number" bind:value={config.controllers.ph.base_pump_pin} />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 class="text-lg font-medium">ORP Controller</h3>
                <div class="grid grid-cols-3 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="orp-check-interval">Check Interval (seconds)</Label>
                    <Input id="orp-check-interval" type="number" bind:value={config.controllers.orp.check_interval} />
                  </div>
                  <div class="space-y-2">
                    <Label for="orp-increase-pump-pin">Increase Pump Pin</Label>
                    <Input id="orp-increase-pump-pin" type="number" bind:value={config.controllers.orp.increase_pump_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="orp-decrease-pump-pin">Decrease Pump Pin</Label>
                    <Input id="orp-decrease-pump-pin" type="number" bind:value={config.controllers.orp.decrease_pump_pin} />
                  </div>
                </div>
              </div>
              
              <div>
                <h3 class="text-lg font-medium">EC Controller</h3>
                <div class="grid grid-cols-3 gap-4 mt-2">
                  <div class="space-y-2">
                    <Label for="ec-check-interval">Check Interval (seconds)</Label>
                    <Input id="ec-check-interval" type="number" bind:value={config.controllers.ec.check_interval} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ec-nutrient-pump-pin">Nutrient Pump Pin</Label>
                    <Input id="ec-nutrient-pump-pin" type="number" bind:value={config.controllers.ec.nutrient_pump_pin} />
                  </div>
                  <div class="space-y-2">
                    <Label for="ec-water-pump-pin">Water Pump Pin</Label>
                    <Input id="ec-water-pump-pin" type="number" bind:value={config.controllers.ec.water_pump_pin} />
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
          
          <!-- Outputs Tab -->
          <TabsContent value="outputs" class="space-y-6">
            <div class="space-y-4">
              <div>
                <h3 class="text-lg font-medium">MOSFET Pins</h3>
                <div class="space-y-2 mt-2">
                  <Label for="mosfet-pins">GPIO Pins (comma-separated)</Label>
                  <Input 
                    id="mosfet-pins"
                    type="text" 
                    value={config.outputs.mosfet_pins.join(', ')}
                    on:input={(e) => {
                      const pins = e.target.value.split(',').map(pin => parseInt(pin.trim())).filter(pin => !isNaN(pin));
                      config.outputs.mosfet_pins = pins;
                    }}
                  />
                </div>
              </div>
            </div>
          </TabsContent>
          
          <!-- API Tab -->
          <TabsContent value="api" class="space-y-6">
            <div class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="space-y-2">
                  <Label for="api-host">Host</Label>
                  <Input id="api-host" type="text" bind:value={config.api.host} />
                </div>
                <div class="space-y-2">
                  <Label for="api-port">Port</Label>
                  <Input id="api-port" type="number" bind:value={config.api.port} />
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
      <CardFooter>
        <Button on:click={updateConfig}>Save Configuration</Button>
      </CardFooter>
    </Card>
    
    {#if statusMessage}
      <Alert>
        <AlertDescription>{statusMessage}</AlertDescription>
      </Alert>
    {/if}
  {:else}
    <Card>
      <CardContent class="pt-6">
        <div class="flex items-center justify-center p-6">
          <p>Loading configuration...</p>
        </div>
      </CardContent>
    </Card>
  {/if}
</div>

