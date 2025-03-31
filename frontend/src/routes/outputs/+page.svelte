<script>
  import { onMount, onDestroy } from 'svelte';
  import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "$lib/components/ui/card";
  import { Button } from "$lib/components/ui/button";
  import { Input } from "$lib/components/ui/input";
  import { Label } from "$lib/components/ui/label";
  import { Slider } from "$lib/components/ui/slider";
  import { Switch } from "$lib/components/ui/switch";
  import { Alert, AlertDescription } from "$lib/components/ui/alert";
//   import { API_URL } from '$lib/stores';
  
  // Output pins and states
  let outputPins = [];
  let outputStates = {};
  let loading = true;
  let error = null;
  let statusMessage = '';

  let API_URL = "http://localhost:8000"
  
  // Test parameters
  let selectedPin = null;
  let testDuration = 1.0;
  
  // Fetch output pins
  async function fetchOutputs() {
    try {
      loading = true;
      error = null;
      
      const response = await fetch(`${API_URL}/api/outputs`);
      if (!response.ok) {
        throw new Error(`Error fetching outputs: ${response.statusText}`);
      }
      
      const data = await response.json();
      outputPins = data.pins || [];
      outputStates = data.states || {};
      
      if (outputPins.length > 0 && selectedPin === null) {
        selectedPin = outputPins[0];
      }
      
    } catch (err) {
      console.error('Error fetching outputs:', err);
      error = err.message;
    } finally {
      loading = false;
    }
  }
  
  // Test an output
  async function testOutput(pin, state, forceDuration = null) {
    try {
      statusMessage = `Setting pin ${pin} to ${state ? 'ON' : 'OFF'}...`;
      
      // Use forceDuration if provided, otherwise use testDuration for ON state
      const duration = forceDuration !== null ? forceDuration : (state ? testDuration : 0);
      const isPermanent = state && duration === 0;
      
      const response = await fetch(`${API_URL}/api/outputs/test`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          pin: pin,
          state: state,
          duration: duration
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `Error: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.success) {
        // Update local state
        outputStates[pin] = state;
        
        if (state) {
          if (isPermanent) {
            statusMessage = `Pin ${pin} turned ON permanently`;
          } else {
            statusMessage = `Pin ${pin} turned ON for ${testDuration} seconds`;
            
            // Schedule UI update after duration
            setTimeout(() => {
              outputStates[pin] = false;
              statusMessage = `Pin ${pin} turned OFF automatically after ${testDuration} seconds`;
            }, testDuration * 1000);
          }
        } else {
          statusMessage = `Pin ${pin} turned OFF`;
        }
      }
      
    } catch (err) {
      console.error('Error testing output:', err);
      statusMessage = `Error: ${err.message}`;
    }
  }
  
  // Initialize
  onMount(async () => {
    await fetchOutputs();
  });
</script>

<div class="space-y-6">
  <div class="flex items-center justify-between">
    <h2 class="text-3xl font-bold tracking-tight">MOSFET Outputs</h2>
    <Button variant="outline" onclick={fetchOutputs}>Refresh</Button>
  </div>
  
  {#if loading}
    <Card>
      <CardContent class="pt-6">
        <div class="flex items-center justify-center p-6">
          <p>Loading outputs...</p>
        </div>
      </CardContent>
    </Card>
  {:else if error}
    <Alert variant="destructive">
      <AlertDescription>{error}</AlertDescription>
    </Alert>
  {:else if outputPins.length === 0}
    <Card>
      <CardContent class="pt-6">
        <div class="flex items-center justify-center p-6">
          <p>No MOSFET outputs configured</p>
        </div>
      </CardContent>
    </Card>
  {:else}
    <Card>
      <CardHeader>
        <CardTitle>Test MOSFET Outputs</CardTitle>
        <CardDescription>
          Activate individual MOSFET outputs for testing purposes
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div class="space-y-6">
          <div class="space-y-2">
            <Label for="pin-select">Select Output Pin</Label>
            <div class="grid grid-cols-6 gap-2">
              {#each outputPins as pin}
                <Button 
                  variant={selectedPin === pin ? "default" : "outline"}
                  onclick={() => selectedPin = pin}
                >
                  Pin {pin}
                </Button>
              {/each}
            </div>
          </div>
          
          {#if selectedPin !== null}
            <div class="space-y-4">
              <div class="space-y-2">
                <Label for="duration">Test Duration (seconds)</Label>
                <div class="flex items-center gap-4">
                  <Slider 
                    id="duration" 
                    min={0.5} 
                    max={10} 
                    step={0.5} 
                    value={[testDuration]} 
                    onValueChange={(values) => testDuration = values[0]} 
                    class="flex-1"
                  />
                  <span class="w-12 text-right">{testDuration}s</span>
                </div>
              </div>
              
              <div class="flex items-center justify-between">
                <div>
                  <h3 class="text-lg font-medium">Pin {selectedPin}</h3>
                  <p class="text-sm text-muted-foreground">
                    Current state: 
                    <span class={outputStates[selectedPin] ? "text-green-500 font-medium" : "text-gray-500"}>
                      {outputStates[selectedPin] ? "ON" : "OFF"}
                    </span>
                  </p>
                </div>
                <div class="space-x-2">
                  <Button 
                    variant="destructive" 
                    onclick={() => testOutput(selectedPin, false)}
                    disabled={!outputStates[selectedPin]}
                  >
                    Turn OFF
                  </Button>
                  <Button 
                    variant="default" 
                    onclick={() => testOutput(selectedPin, true)}
                    disabled={outputStates[selectedPin]}
                  >
                    Turn ON for {testDuration}s
                  </Button>
                  <Button 
                    variant="secondary" 
                    onclick={() => testOutput(selectedPin, true, 0)}
                    disabled={outputStates[selectedPin]}
                  >
                    Turn ON Permanently
                  </Button>
                </div>
              </div>
            </div>
          {/if}
        </div>
      </CardContent>
    </Card>
    
    {#if statusMessage}
      <Alert>
        <AlertDescription>{statusMessage}</AlertDescription>
      </Alert>
    {/if}
  {/if}
</div>