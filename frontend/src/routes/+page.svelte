<script>
	import { onMount, onDestroy } from 'svelte';
	import {
		sensor,
		controller,
		history,
		fetchSensorData,
		fetchControllerData,
		fetchSensorHistory
	} from '$lib/state.svelte';
	import {
		Card,
		CardContent,
		CardDescription,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { Button } from '$lib/components/ui/button';

	import UplotSvelte from '$lib/components/uplot-svelte.svelte';
	import uPlot from 'uplot';
	import 'uplot/dist/uPlot.min.css';

	// Update interval (in ms)
	const UPDATE_INTERVAL = 5000; // 10 seconds

	// Interval ID for cleanup
	let intervalId;
	
	// Add function to force pump run
	async function forcePumpRun() {
		try {
			const response = await fetch('http://localhost:8000/api/controllers/pump_timer/force_run', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				}
			});
			
			const result = await response.json();
			if (result.success) {
				// Refresh controller data to update UI
				await fetchControllerData();
			}
		} catch (error) {
			console.error('Error forcing pump run:', error);
		}
	}

	let makeFmt = (suffix) => (u, v, sidx, didx) => {
		if (didx == null) {
			let d = u.data[sidx];
			v = d[d.length - 1];
		}

		return v == null ? null : v.toFixed(1) + suffix;
	};

	// Fetch data
	async function updateData() {
		await Promise.all([fetchSensorData(), fetchControllerData()]);
	}

	onMount(async () => {
		// Initial data fetch
		await Promise.all([updateData(), fetchSensorHistory()]);

		// Set up interval for regular updates
		intervalId = setInterval(updateData, UPDATE_INTERVAL);
	});

	onDestroy(() => {
		// Clean up interval
		if (intervalId) {
			clearInterval(intervalId);
		}
	});
</script>

<div class="space-y-8">
	<div class="flex items-center justify-between">
		<h2 class="text-3xl font-bold tracking-tight">Dashboard</h2>
		<div class="space-x-2">
			<Button variant="outline" onclick={updateData}>Refresh Data</Button>
			<Button variant="outline" onclick={fetchSensorHistory}>Refresh History</Button>
		</div>
	</div>
	<div class="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
		<!-- pH Card -->
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium">pH</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">{sensor.ph ? sensor.ph.toFixed(2) : 'N/A'}</div>
				<p class="text-xs text-muted-foreground">
					Target: {controller.ph ? controller.ph.target_ph.toFixed(2) : 'N/A'}
					{#if controller.ph}
						<Badge variant={controller.ph.running ? 'success' : 'secondary'} class="ml-2">
							{controller.ph.running ? 'Running' : 'Stopped'}
						</Badge>
					{/if}
				</p>
			</CardContent>
		</Card>

		<!-- ORP Card -->
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium">ORP</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">{sensor.orp ? sensor.orp.toFixed(0) : 'N/A'} mV</div>
				<p class="text-xs text-muted-foreground">
					Target: {controller.orp ? controller.orp.target_orp.toFixed(0) : 'N/A'} mV
					{#if controller.orp}
						<Badge variant={controller.orp.running ? 'success' : 'secondary'} class="ml-2">
							{controller.orp.running ? 'Running' : 'Stopped'}
						</Badge>
					{/if}
				</p>
			</CardContent>
		</Card>

		<!-- EC Card -->
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium">EC</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">{sensor.ec ? sensor.ec.toFixed(0) : 'N/A'} μS/cm</div>
				<p class="text-xs text-muted-foreground">
					Target: {controller.ec ? controller.ec.target_ec.toFixed(0) : 'N/A'} μS/cm
					{#if controller.ec}
						<Badge variant={controller.ec.running ? 'success' : 'secondary'} class="ml-2">
							{controller.ec.running ? 'Running' : 'Stopped'}
						</Badge>
					{/if}
				</p>
			</CardContent>
		</Card>

		<!-- Temperature Card -->
		<Card>
			<CardHeader class="pb-2">
				<CardTitle class="text-sm font-medium">Temperature</CardTitle>
			</CardHeader>
			<CardContent>
				<div class="text-2xl font-bold">
					{sensor.water_temperature ? sensor.water_temperature.toFixed(1) : 'N/A'} °C
				</div>
				<p class="text-xs text-muted-foreground">
					Air: {sensor.air_temperature ? sensor.air_temperature.toFixed(1) : 'N/A'} °C Humidity: {sensor.humidity
						? sensor.humidity.toFixed(1)
						: 'N/A'} %
				</p>
			</CardContent>
		</Card>
	</div>
	
	<!-- Add Pool Pump Card -->
	{#if controller.pump_timer}
		<Card>
			<CardHeader class="flex flex-row items-center justify-between space-y-0 pb-2">
				<CardTitle>Pool Pump Control</CardTitle>
				<Badge variant={controller.pump_timer.pump_running ? 'success' : 'secondary'}>
					{controller.pump_timer.pump_running ? 'Running' : 'Idle'}
				</Badge>
			</CardHeader>
			<CardContent>
				<div class="space-y-4">
					<div class="grid grid-cols-2 gap-4">
						<div>
							<p class="text-sm font-medium">Last Temperature</p>
							<p class="text-2xl font-bold">
								{controller.pump_timer.last_temperature ? 
									controller.pump_timer.last_temperature.toFixed(1) + '°C' : 'N/A'}
							</p>
						</div>
						<div>
							<p class="text-sm font-medium">Current Run Time</p>
							<p class="text-2xl font-bold">
								{controller.pump_timer.current_run_time || 0} min
							</p>
						</div>
					</div>
					
					<div class="grid grid-cols-2 gap-4">
						<div>
							<p class="text-sm font-medium">Schedule</p>
							<p class="text-lg">
								{controller.pump_timer.start_hour}:00 - {controller.pump_timer.end_hour}:00
							</p>
						</div>
						<div>
							<p class="text-sm font-medium">Controller Status</p>
							<Badge variant={controller.pump_timer.enabled ? 'success' : 'secondary'}>
								{controller.pump_timer.enabled ? 'Enabled' : 'Disabled'}
							</Badge>
						</div>
					</div>
					
					<Button 
						variant="default" 
						class="w-full" 
						onclick={forcePumpRun}
						disabled={!controller.pump_timer.enabled}
					>
						Force Pump Run Until Next Cycle
					</Button>
				</div>
			</CardContent>
		</Card>
	{/if}

	<div class="grid gap-4 lg:grid-cols-2">
		<!-- Charts remain unchanged -->
		<!-- pH Chart -->
		<Card>
			<CardHeader>
				<CardTitle>pH History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte
					data={[history.timestamps, history.ph]}
					options={{
						width: 700,
						height: 300,
						scales: { x: { time: false } },
						series: [{ label: 'time' }, { label: 'EC', stroke: 'green' }]
					}}
				/>
			</CardContent>
		</Card>

		<!-- ORP Chart -->
		<Card>
			<CardHeader>
				<CardTitle>ORP History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte
					data={[history.timestamps, history.orp]}
					options={{
						width: 700,
						height: 300,
						scales: { x: { time: false } },
						series: [{ label: 'time' }, { label: 'EC', stroke: 'red', value: makeFmt('mV') }]
					}}
				/>
			</CardContent>
		</Card>

		<!-- EC Chart -->
		<Card>
			<CardHeader>
				<CardTitle>EC History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte
					data={[history.timestamps, history.ec]}
					options={{
						width: 700,
						height: 300,
						scales: { x: { time: false } },
						series: [{ label: 'time' }, { label: 'EC', stroke: 'red', value: makeFmt('μS/cm') }]
					}}
				/>
			</CardContent>
		</Card>

		<!-- Temperature Chart -->
		<Card>
			<CardHeader>
				<CardTitle>Temperature History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte
					data={[
						history.timestamps,
						history.air_temperature,
						history.water_temperature,
						history.humidity
					]}
					options={{
						width: 700,
						height: 300,
						scales: { x: { time: false } },
						series: [
							{ label: 'time' },
							{ label: 'tAir', stroke: 'red', value: makeFmt('°C'), scale: 'celsius' },
							{ label: 'tWater', stroke: 'blue', value: makeFmt('°C'), scale: 'celsius' },
							{ label: 'Humidity', stroke: 'green', value: makeFmt('%'), scale: '%' }
						],
						axes: [
							{},
							{
								scale: 'celsius',
								values: (u, vals, space) => vals.map((v) => +v.toFixed(2) + '°C')
							},
							{
								side: 1,
								scale: '%',
								values: (u, vals, space) => vals.map((v) => +v.toFixed(1) + '%'),
								grid: { show: false }
							}
						]
					}}
				/>
			</CardContent>
		</Card>
	</div>

	<div class="text-xs text-muted-foreground">
		Last updated: {sensor.lastUpdated ? sensor.lastUpdated.toLocaleString() : 'Never'}
	</div>
</div>
