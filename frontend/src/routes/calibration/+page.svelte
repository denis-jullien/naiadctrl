<script>
	import { onMount } from 'svelte';
	import {
		sensor,
		fetchSensorData,
		calibratePH,
		calibrateORP,
		calibrateEC
	} from '$lib/state.svelte';
	import {
		Card,
		CardContent,
		CardDescription,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Button } from '$lib/components/ui/button';
	import { Alert, AlertDescription } from '$lib/components/ui/alert';
	import { Badge } from '$lib/components/ui/badge';

	// Form values
	let phVoltage = 0;
	let phValue = 7.0;
	let orpValue = 650;
	let ecValue = 1500;

	// Status messages
	let phStatus = '';
	let orpStatus = '';
	let ecStatus = '';
	let genericStatus = '';

	// Generic sensor calibration state
	let calibrationMode = false;
	let activeSensor = null;
	let calibrationPoints = {};
	let rawValue = null;
	let realValue = '';

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

	// Format timestamp function
	function formatTimestamp(timestamp) {
		if (!timestamp) return 'Never';
		return new Date(timestamp * 1000).toLocaleString();
	}

	// Start calibration for a generic sensor
	async function startCalibration(sensorId) {
		calibrationMode = true;
		activeSensor = sensorId;
		calibrationPoints = {};
		genericStatus = '';

		// Get current raw value
		try {
			const response = await fetch(`http://localhost:8000/api/sensors/${sensorId}/raw`);
			if (response.ok) {
				const data = await response.json();
				rawValue = data.value;
			}
		} catch (error) {
			console.error('Error fetching raw value:', error);
			genericStatus = 'Error fetching raw value';
		}
	}

	// Add calibration point
	function addCalibrationPoint() {
		if (rawValue !== null && realValue !== '') {
			calibrationPoints[rawValue] = parseFloat(realValue);
			realValue = '';
			genericStatus = 'Point added';
		}
	}

	// Save calibration
	async function saveCalibration() {
		if (Object.keys(calibrationPoints).length < 2) {
			genericStatus = 'At least 2 calibration points are required';
			return;
		}

		try {
			genericStatus = 'Saving calibration...';
			const response = await fetch(
				`http://localhost:8000/api/sensors/${activeSensor}/calibration`,
				{
					method: 'POST',
					headers: {
						'Content-Type': 'application/json'
					},
					body: JSON.stringify(calibrationPoints)
				}
			);

			if (response.ok) {
				genericStatus = 'Calibration successful!';
				setTimeout(() => {
					calibrationMode = false;
					activeSensor = null;
					genericStatus = '';
				}, 2000);
				// Refresh sensor data
				await fetchSensorData();
			} else {
				genericStatus = 'Failed to save calibration';
			}
		} catch (error) {
			console.error('Error saving calibration:', error);
			genericStatus = 'Error saving calibration';
		}
	}

	// Cancel calibration
	function cancelCalibration() {
		calibrationMode = false;
		activeSensor = null;
		calibrationPoints = {};
		genericStatus = '';
	}

	// Refresh raw value
	async function refreshRawValue() {
		if (!activeSensor) return;

		try {
			const response = await fetch(`http://localhost:8000/api/sensors/${activeSensor}/raw`);
			if (response.ok) {
				const data = await response.json();
				rawValue = data.value;
				genericStatus = 'Raw value refreshed';
			}
		} catch (error) {
			console.error('Error fetching raw value:', error);
			genericStatus = 'Error fetching raw value';
		}
	}

	 // Update unit
	 async function updateSensorUnit(sensorId, newUnit) {
        if (!newUnit) return;
        
        genericStatus = 'Updating unit...';
        
        try {
            const response = await fetch(`http://localhost:8000/api/sensors/${sensorId}/unit`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ unit: newUnit })
            });

            if (response.ok) {
                genericStatus = 'Unit updated successfully!';
                setTimeout(() => {
                    genericStatus = '';
                }, 2000);
                // Refresh sensor data
                await fetchSensorData();
            } else {
                genericStatus = 'Failed to update unit';
            }
        } catch (error) {
            console.error('Error updating unit:', error);
            genericStatus = 'Error updating unit';
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
					Current pH reading: <span class="font-medium"
						>{sensor.ph ? sensor.ph.toFixed(2) : 'N/A'}</span
					>
				</CardDescription>
			</CardHeader>
			<CardContent>
				<form onsubmit={handlePHCalibration} class="space-y-4">
					<div class="space-y-2">
						<Label for="phVoltage">Voltage Reading (V)</Label>
						<Input
							id="phVoltage"
							type="number"
							bind:value={phVoltage}
							step="0.01"
							min="0"
							max="5"
						/>
						<p class="text-sm text-muted-foreground">Enter the voltage reading from the pH probe</p>
					</div>
					<div class="space-y-2">
						<Label for="phValue">Known pH Value</Label>
						<Input id="phValue" type="number" bind:value={phValue} step="0.1" min="0" max="14" />
						<p class="text-sm text-muted-foreground">
							Enter the known pH value of your calibration solution
						</p>
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
					<ol class="list-inside list-decimal space-y-1 text-sm">
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
					Current ORP reading: <span class="font-medium"
						>{sensor.orp ? sensor.orp.toFixed(0) : 'N/A'} mV</span
					>
				</CardDescription>
			</CardHeader>
			<CardContent>
				<form onsubmit={handleORPCalibration} class="space-y-4">
					<div class="space-y-2">
						<Label for="orpValue">Known ORP Value (mV)</Label>
						<Input id="orpValue" type="number" bind:value={orpValue} step="10" min="0" max="1000" />
						<p class="text-sm text-muted-foreground">
							Enter the known ORP value of your calibration solution
						</p>
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
					<ol class="list-inside list-decimal space-y-1 text-sm">
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
					Current EC reading: <span class="font-medium"
						>{sensor.ec ? sensor.ec.toFixed(0) : 'N/A'} μS/cm</span
					>
				</CardDescription>
			</CardHeader>
			<CardContent>
				<form onsubmit={handleECCalibration} class="space-y-4">
					<div class="space-y-2">
						<Label for="ecValue">Known EC Value (μS/cm)</Label>
						<Input id="ecValue" type="number" bind:value={ecValue} step="50" min="0" max="3000" />
						<p class="text-sm text-muted-foreground">
							Enter the known EC value of your calibration solution
						</p>
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
					<ol class="list-inside list-decimal space-y-1 text-sm">
						<li>Place the EC probe in a calibration solution with a known EC value</li>
						<li>Enter the known EC value of the solution in μS/cm</li>
						<li>Click "Calibrate"</li>
					</ol>
				</div>
			</CardContent>
		</Card>
	</div>

	<!-- Update the generic sensors section to include unit change functionality -->
	<h3 class="text-xl font-bold tracking-tight mt-8">Generic Sensors Calibration</h3>
	<div class="grid gap-6 md:grid-cols-3">
	    {#each Object.entries(sensor) as [sensorId, sensorData]}
	        {#if sensorData && typeof sensorData === 'object' && sensorData.type === 'generic'}
	            <Card>
	                <CardHeader>
	                    <CardTitle>{sensorData.name || sensorId}</CardTitle>
	                    <CardDescription>
	                        Current reading: <span class="font-medium">
	                            {sensorData.value !== undefined && sensorData.value !== null
	                                ? typeof sensorData.value === 'number'
	                                    ? sensorData.value.toFixed(2)
	                                    : sensorData.value
	                                : 'N/A'}
	                            {#if sensorData.unit}
	                                {sensorData.unit}
	                            {/if}
	                        </span>
	                        {#if sensorData.has_calibration}
	                            <Badge variant="outline" class="ml-2">Calibrated</Badge>
	                        {/if}
	                    </CardDescription>
	                </CardHeader>
	                <CardContent>
	                    <div class="space-y-4">
	                        <div class="flex space-x-2">
	                            <Input
	                                placeholder="New unit"
	                                class="w-full"
	                                id={`unit-${sensorId}`}
	                                onkeydown={(e) => e.key === 'Enter' && updateSensorUnit(sensorId, e.target.value)}
	                            />
	                            <Button
	                                variant="outline"
	                                onclick={(e) => updateSensorUnit(sensorId, document.getElementById(`unit-${sensorId}`).value)}
	                            >
	                                Set Unit
	                            </Button>
	                        </div>
	                        <p class="text-sm text-muted-foreground">
	                            Calibrate this sensor by providing multiple reference points to map raw sensor values to real-world measurements.
	                        </p>
	                        <Button class="w-full" onclick={() => startCalibration(sensorId)}>
	                            Start Calibration
	                        </Button>
	                    </div>
	                </CardContent>
	            </Card>
	        {/if}
	    {/each}
	</div>
</div>

<!-- Generic Sensor Calibration Modal -->
{#if calibrationMode}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
		<div class="w-full max-w-2xl rounded-lg bg-white p-6 shadow-lg dark:bg-gray-800">
			<h2 class="mb-4 text-xl font-bold">
				Calibration: {sensor[activeSensor]?.name || activeSensor}
			</h2>

			<div class="space-y-4">
				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label>Current Raw Value</Label>
						<div class="flex space-x-2">
							<Input value={rawValue} readonly />
							<Button variant="outline" onclick={refreshRawValue}>Refresh</Button>
						</div>
					</div>
					<div class="space-y-2">
						<Label for="real-value">Real World Value</Label>
						<div class="flex space-x-2">
							<Input id="real-value" bind:value={realValue} type="number" step="0.01" />
							<Button onclick={addCalibrationPoint}>Add Point</Button>
						</div>
					</div>
				</div>

				{#if genericStatus}
					<Alert>
						<AlertDescription>{genericStatus}</AlertDescription>
					</Alert>
				{/if}

				<div class="space-y-2">
					<h3 class="font-medium">Calibration Points</h3>
					{#if Object.keys(calibrationPoints).length === 0}
						<p class="text-sm text-muted-foreground">No calibration points added yet</p>
					{:else}
						<div class="rounded-md border">
							<table class="w-full">
								<thead>
									<tr class="border-b">
										<th class="px-4 py-2 text-left">Raw Value</th>
										<th class="px-4 py-2 text-left">Real Value</th>
									</tr>
								</thead>
								<tbody>
									{#each Object.entries(calibrationPoints) as [raw, real]}
										<tr class="border-b">
											<td class="px-4 py-2">{raw}</td>
											<td class="px-4 py-2">{real}</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				</div>

				<div class="space-y-2">
					<h3 class="font-medium">Calibration Instructions:</h3>
					<ol class="list-inside list-decimal space-y-1 text-sm">
						<li>Click "Refresh" to get the current raw sensor value</li>
						<li>Enter the corresponding real-world value</li>
						<li>Click "Add Point" to add this calibration point</li>
						<li>Repeat steps 1-3 with different values (at least 2 points required)</li>
						<li>Click "Save Calibration" when done</li>
					</ol>
				</div>
			</div>

			<div class="mt-6 flex justify-end space-x-2">
				<Button variant="outline" onclick={cancelCalibration}>Cancel</Button>
				<Button onclick={saveCalibration} disabled={Object.keys(calibrationPoints).length < 2}>
					Save Calibration
				</Button>
			</div>
		</div>
	</div>
{/if}
