<script>
	import { onMount, onDestroy } from 'svelte';
	import {
		controller,
		fetchControllerData,
		updateControllerTarget,
		startController,
		stopController
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
	import { Badge } from '$lib/components/ui/badge';

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

	// ... existing imports and variables ...

	// Add new form values for pump timer
	let pumpMinRunTime = 15;
	let pumpMaxRunTime = 120;
	let pumpTempCheckDelay = 5;
	let pumpStartHour = 8;
	let pumpEndHour = 20;
	let pumpTempThresholds = {};

	// Handle pump timer controller form submission
	async function handlePumpTimerSubmit() {
		try {
			const response = await fetch('http://localhost:8000/api/controllers/pump_timer', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					min_run_time: pumpMinRunTime,
					max_run_time: pumpMaxRunTime,
					temp_check_delay: pumpTempCheckDelay,
					start_hour: pumpStartHour,
					end_hour: pumpEndHour,
					temp_thresholds: pumpTempThresholds
				})
			});

			const result = await response.json();

			if (result.success) {
				await fetchControllerData();
			}
		} catch (error) {
			console.error('Error updating pump timer controller:', error);
		}
	}

	// Toggle pump timer controller
	async function togglePumpTimerController() {
		if (controller.pump_timer?.running) {
			await stopController('pump_timer');
		} else {
			await startController('pump_timer');
		}
	}

	// Initialize form values when controller data is loaded
	$: if (controller.pump_timer) {
		pumpMinRunTime = controller.pump_timer.min_run_time || 15;
		pumpMaxRunTime = controller.pump_timer.max_run_time || 120;
		pumpTempCheckDelay = controller.pump_timer.temp_check_delay || 5;
		pumpStartHour = controller.pump_timer.start_hour || 8;
		pumpEndHour = controller.pump_timer.end_hour || 20;
		pumpTempThresholds = controller.pump_timer.temp_thresholds || {};
	}
</script>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<h2 class="text-3xl font-bold tracking-tight">Controllers</h2>
	</div>

	<div class="grid gap-6 md:grid-cols-2">
		<!-- pH Controller -->
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-xl font-bold">pH Controller</CardTitle>
				{#if controller.ph}
					<Button
						variant={controller.ph.running ? 'destructive' : 'default'}
						size="sm"
						onclick={togglePHController}
					>
						{controller.ph.running ? 'Stop' : 'Start'}
					</Button>
				{/if}
			</CardHeader>
			<CardContent>
				{#if controller.ph}
					<div class="mb-4 space-y-2">
						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Current pH:</span>
							<span class="font-medium"
								>{controller.ph.current_ph ? controller.ph.current_ph.toFixed(2) : 'N/A'}</span
							>
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
							<Badge variant={controller.ph.running ? 'success' : 'secondary'}>
								{controller.ph.running ? 'Running' : 'Stopped'}
							</Badge>
						</div>
						{#if controller.ph.last_dose_time > 0}
							<div class="flex justify-between">
								<span class="text-sm text-muted-foreground">Last dose:</span>
								<span class="text-sm"
									>{new Date(controller.ph.last_dose_time * 1000).toLocaleString()}</span
								>
							</div>
						{/if}
					</div>

					<form on:submit|preventDefault={handlePHSubmit} class="space-y-4">
						<div class="space-y-2">
							<Label for="phTarget">Target pH</Label>
							<Input
								id="phTarget"
								type="number"
								bind:value={phTarget}
								step="0.1"
								min="0"
								max="14"
							/>
						</div>
						<div class="space-y-2">
							<Label for="phTolerance">Tolerance (±)</Label>
							<Input
								id="phTolerance"
								type="number"
								bind:value={phTolerance}
								step="0.1"
								min="0.1"
								max="1"
							/>
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
						variant={controller.orp.running ? 'destructive' : 'default'}
						size="sm"
						on:click={toggleORPController}
					>
						{controller.orp.running ? 'Stop' : 'Start'}
					</Button>
				{/if}
			</CardHeader>
			<CardContent>
				{#if controller.orp}
					<div class="mb-4 space-y-2">
						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Current ORP:</span>
							<span class="font-medium"
								>{controller.orp.current_orp ? controller.orp.current_orp.toFixed(0) : 'N/A'} mV</span
							>
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
							<Badge variant={controller.orp.running ? 'success' : 'secondary'}>
								{controller.orp.running ? 'Running' : 'Stopped'}
							</Badge>
						</div>
						{#if controller.orp.last_dose_time > 0}
							<div class="flex justify-between">
								<span class="text-sm text-muted-foreground">Last dose:</span>
								<span class="text-sm"
									>{new Date(controller.orp.last_dose_time * 1000).toLocaleString()}</span
								>
							</div>
						{/if}
					</div>

					<form on:submit|preventDefault={handleORPSubmit} class="space-y-4">
						<div class="space-y-2">
							<Label for="orpTarget">Target ORP (mV)</Label>
							<Input
								id="orpTarget"
								type="number"
								bind:value={orpTarget}
								step="10"
								min="0"
								max="1000"
							/>
						</div>
						<div class="space-y-2">
							<Label for="orpTolerance">Tolerance (±mV)</Label>
							<Input
								id="orpTolerance"
								type="number"
								bind:value={orpTolerance}
								step="5"
								min="5"
								max="50"
							/>
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
						variant={controller.ec.running ? 'destructive' : 'default'}
						size="sm"
						onclick={toggleECController}
					>
						{controller.ec.running ? 'Stop' : 'Start'}
					</Button>
				{/if}
			</CardHeader>
			<CardContent>
				{#if controller.ec}
					<div class="mb-4 space-y-2">
						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Current EC:</span>
							<span class="font-medium"
								>{controller.ec.current_ec ? controller.ec.current_ec.toFixed(0) : 'N/A'} μS/cm</span
							>
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
							<Badge variant={controller.ec.running ? 'success' : 'secondary'}>
								{controller.ec.running ? 'Running' : 'Stopped'}
							</Badge>
						</div>
						{#if controller.ec.last_dose_time > 0}
							<div class="flex justify-between">
								<span class="text-sm text-muted-foreground">Last dose:</span>
								<span class="text-sm"
									>{new Date(controller.ec.last_dose_time * 1000).toLocaleString()}</span
								>
							</div>
						{/if}
					</div>

					<form on:submit|preventDefault={handleECSubmit} class="space-y-4">
						<div class="space-y-2">
							<Label for="ecTarget">Target EC (μS/cm)</Label>
							<Input
								id="ecTarget"
								type="number"
								bind:value={ecTarget}
								step="50"
								min="0"
								max="3000"
							/>
						</div>
						<div class="space-y-2">
							<Label for="ecTolerance">Tolerance (±μS/cm)</Label>
							<Input
								id="ecTolerance"
								type="number"
								bind:value={ecTolerance}
								step="10"
								min="10"
								max="200"
							/>
						</div>
						<Button type="submit" class="w-full">Update</Button>
					</form>
				{:else}
					<div class="py-4 text-center text-muted-foreground">Loading EC controller data...</div>
				{/if}
			</CardContent>
		</Card>

		<!-- Pump Timer Controller -->
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle class="text-xl font-bold">Pool Pump Timer</CardTitle>
				{#if controller.pump_timer}
					<Button
						variant={controller.pump_timer.running ? 'destructive' : 'default'}
						size="sm"
						on:click={togglePumpTimerController}
					>
						{controller.pump_timer.running ? 'Stop' : 'Start'}
					</Button>
				{/if}
			</CardHeader>
			<CardContent>
				{#if controller.pump_timer}
					<div class="mb-4 space-y-2">
						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Status:</span>
							<Badge variant={controller.pump_timer.pump_running ? 'success' : 'secondary'}>
								{controller.pump_timer.pump_running ? 'Running' : 'Idle'}
							</Badge>
						</div>

						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Last Temperature:</span>
							<span class="font-medium">
								{controller.pump_timer.last_temperature
									? controller.pump_timer.last_temperature.toFixed(1) + '°C'
									: 'N/A'}
							</span>
						</div>

						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Current Run Time:</span>
							<span class="font-medium">
								{controller.pump_timer.current_run_time} minutes
							</span>
						</div>

						{#if controller.pump_timer.last_run_start > 0}
							<div class="flex justify-between">
								<span class="text-sm text-muted-foreground">Last Run:</span>
								<span class="text-sm">
									{new Date(controller.pump_timer.last_run_start * 1000).toLocaleString()}
								</span>
							</div>

							<div class="flex justify-between">
								<span class="text-sm text-muted-foreground">Run Duration:</span>
								<span class="text-sm">
									{controller.pump_timer.last_run_duration.toFixed(1)} minutes
								</span>
							</div>
						{/if}

						<div class="flex justify-between">
							<span class="text-sm text-muted-foreground">Schedule:</span>
							<span class="font-medium">
								{controller.pump_timer.start_hour}:00 - {controller.pump_timer.end_hour}:00
							</span>
						</div>
					</div>

					<form on:submit|preventDefault={handlePumpTimerSubmit} class="space-y-4">
						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<Label for="pumpMinRunTime">Min Run Time (min)</Label>
								<Input
									id="pumpMinRunTime"
									type="number"
									bind:value={pumpMinRunTime}
									step="5"
									min="5"
									max="60"
								/>
							</div>

							<div class="space-y-2">
								<Label for="pumpMaxRunTime">Max Run Time (min)</Label>
								<Input
									id="pumpMaxRunTime"
									type="number"
									bind:value={pumpMaxRunTime}
									step="10"
									min="30"
									max="240"
								/>
							</div>
						</div>

						<div class="space-y-2">
							<Label for="pumpTempCheckDelay">Temperature Check Delay (min)</Label>
							<Input
								id="pumpTempCheckDelay"
								type="number"
								bind:value={pumpTempCheckDelay}
								step="1"
								min="1"
								max="30"
							/>
						</div>

						<div class="grid grid-cols-2 gap-4">
							<div class="space-y-2">
								<Label for="pumpStartHour">Start Hour (24h)</Label>
								<Input
									id="pumpStartHour"
									type="number"
									bind:value={pumpStartHour}
									step="1"
									min="0"
									max="23"
								/>
							</div>

							<div class="space-y-2">
								<Label for="pumpEndHour">End Hour (24h)</Label>
								<Input
									id="pumpEndHour"
									type="number"
									bind:value={pumpEndHour}
									step="1"
									min="0"
									max="23"
								/>
							</div>
						</div>

						<div class="space-y-2">
							<Label>Temperature Thresholds</Label>
							<div class="grid grid-cols-2 gap-2 rounded-md border p-2">
								<div class="text-sm font-medium">Temperature (°C)</div>
								<div class="text-sm font-medium">Run Time (min)</div>

								{#each Object.entries(controller.pump_timer.temp_thresholds).sort((a, b) => parseInt(a[0]) - parseInt(b[0])) as [temp, duration]}
									<div class="text-sm">{temp}°C</div>
									<div class="text-sm">{duration} min</div>
								{/each}
							</div>
							<p class="text-xs text-muted-foreground">
								Note: Temperature thresholds can be configured in the settings page
							</p>
						</div>

						<Button type="submit" class="w-full">Update</Button>
					</form>
				{:else}
					<div class="py-4 text-center text-muted-foreground">Loading pump timer data...</div>
				{/if}
			</CardContent>
		</Card>
	</div>

	<div class="text-sm text-muted-foreground">
		Last updated: {controller.lastUpdated ? controller.lastUpdated.toLocaleString() : 'Never'}
	</div>
</div>
