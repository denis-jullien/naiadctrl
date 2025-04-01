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

	let data = [
		[1, 2, 3, 4, 5],
		[1, 3, 2, 5, 4]
	];

	let options = {
		width: 800,
		height: 300,
		scales: { x: { time: false } },
		series: [{ label: 'x' }, { label: 'y', stroke: 'red' }]
	};

	let flag = true;
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

	<div class="grid gap-4 md:grid-cols-2">
		<!-- pH Chart -->
		<Card>
			<CardHeader>
				<CardTitle>pH History</CardTitle>
			</CardHeader>
			<CardContent></CardContent>
		</Card>

		<!-- ORP Chart -->
		<Card>
			<CardHeader>
				<CardTitle>ORP History</CardTitle>
			</CardHeader>
			<CardContent></CardContent>
		</Card>

		<!-- EC Chart -->
		<Card>
			<CardHeader>
				<CardTitle>EC History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte data={[history.timestamps, history.ec]} {options} />
			</CardContent>
		</Card>

		<!-- Temperature Chart -->
		<Card>
			<CardHeader>
				<CardTitle>Temperature History</CardTitle>
			</CardHeader>
			<CardContent>
				<UplotSvelte
					data={[history.timestamps, history.air_temperature, history.water_temperature]}
					options={{
						width: 800,
						height: 300,
						scales: { x: { time: false } },
						series: [{ label: 'x' }, { label: 'y', stroke: 'red' }]
					}}
				/>
			</CardContent>
		</Card>
	</div>

	<!-- sensorHistory{$sensorHistory["air_temperature"]} -->
	<!-- 
  {[history.timestamps, history.air_temperature]} -->

	<div class="text-xs text-muted-foreground">
		Last updated: {sensor.lastUpdated ? sensor.lastUpdated.toLocaleString() : 'Never'}
	</div>
</div>
