<script>
	import { onMount, onDestroy } from 'svelte';
	import {
		Card,
		CardContent,
		CardDescription,
		CardFooter,
		CardHeader,
		CardTitle
	} from '$lib/components/ui/card';
	import { Button } from '$lib/components/ui/button';
	import { Input } from '$lib/components/ui/input';
	import { Label } from '$lib/components/ui/label';
	import { Select } from '$lib/components/ui/select';
	import { Badge } from '$lib/components/ui/badge';
	import { Progress } from '$lib/components/ui/progress';

	// Log data
	let logs = [];
	let loading = true;
	let error = null;
	let autoRefresh = true;
	let refreshInterval = 5000; // 5 seconds
	let intervalId;
	let logLimit = 100;
	let logLevel = '';
	let searchQuery = '';
	let filteredLogs = [];

	// Fetch logs
	async function fetchLogs() {
		try {
			loading = true;
			error = null;

			let url = `http://localhost:8000/api/logs?limit=${logLimit}`;
			if (logLevel) {
				url += `&level=${logLevel}`;
			}

			const response = await fetch(url);
			if (!response.ok) {
				throw new Error(`Error fetching logs: ${response.statusText}`);
			}

			const data = await response.json();
			logs = data.logs || [];

			// Apply search filter
			applySearchFilter();
		} catch (err) {
			console.error('Error fetching logs:', err);
			error = err.message;
		} finally {
			loading = false;
		}
	}

	// Apply search filter to logs
	function applySearchFilter() {
		if (!searchQuery) {
			filteredLogs = [...logs];
			return;
		}

		const query = searchQuery.toLowerCase();
		filteredLogs = logs.filter(
			(log) =>
				log.message.toLowerCase().includes(query) ||
				log.source.toLowerCase().includes(query) ||
				log.level.toLowerCase().includes(query)
		);
	}

	// Format timestamp
	function formatTimestamp(timestamp) {
		return new Date(timestamp * 1000).toLocaleString();
	}

	// Get badge color based on log level
	function getLevelBadgeVariant(level) {
		switch (level) {
			case 'ERROR':
				return 'destructive';
			case 'WARNING':
				return 'warning';
			case 'INFO':
				return 'default';
			case 'DEBUG':
				return 'secondary';
			default:
				return 'outline';
		}
	}

	// Toggle auto-refresh
	function toggleAutoRefresh() {
		autoRefresh = !autoRefresh;
		if (autoRefresh) {
			intervalId = setInterval(fetchLogs, refreshInterval);
		} else if (intervalId) {
			clearInterval(intervalId);
		}
	}

	// Watch for search query changes
	$: if (searchQuery !== undefined) {
		applySearchFilter();
	}

	onMount(async () => {
		// Initial data fetch
		await fetchLogs();

		// Set up interval for auto-refresh
		if (autoRefresh) {
			intervalId = setInterval(fetchLogs, refreshInterval);
		}
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
		<h2 class="text-3xl font-bold tracking-tight">System Logs</h2>
		<div class="space-x-2">
			<Button variant={autoRefresh ? 'default' : 'outline'} onclick={toggleAutoRefresh}>
				{autoRefresh ? 'Auto-Refresh On' : 'Auto-Refresh Off'}
			</Button>
			<Button variant="outline" onclick={fetchLogs}>Refresh Now</Button>
		</div>
	</div>

	<div class="grid gap-4 md:grid-cols-3">
		<div class="space-y-2">
			<Label for="logLimit">Max Logs</Label>
			<Input
				id="logLimit"
				type="number"
				bind:value={logLimit}
				min="10"
				max="1000"
				step="10"
				onchange={fetchLogs}
			/>
		</div>

		<div class="space-y-2">
			<Label for="logLevel">Log Level</Label>
			<select
				id="logLevel"
				class="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
				bind:value={logLevel}
				onchange={fetchLogs}
			>
				<option value="">All Levels</option>
				<option value="DEBUG">Debug</option>
				<option value="INFO">Info</option>
				<option value="WARNING">Warning</option>
				<option value="ERROR">Error</option>
			</select>
		</div>

		<div class="space-y-2">
			<Label for="searchQuery">Search</Label>
			<Input id="searchQuery" type="text" bind:value={searchQuery} placeholder="Filter logs..." />
		</div>
	</div>

	<Card>
		<CardHeader>
			<CardTitle>Log Entries</CardTitle>
			<CardDescription>
				Showing {filteredLogs.length} of {logs.length} log entries
			</CardDescription>
		</CardHeader>
		<CardContent>
			{#if loading && logs.length === 0}
				<div class="py-4 text-center">
					<Progress value={undefined} class="w-full" />
					<p class="mt-2 text-sm text-muted-foreground">Loading logs...</p>
				</div>
			{:else if error}
				<div class="rounded-md bg-destructive/15 p-4 text-destructive">
					<p>Error: {error}</p>
				</div>
			{:else if filteredLogs.length === 0}
				<div class="py-4 text-center text-muted-foreground">
					<p>No logs found</p>
				</div>
			{:else}
				<div class="space-y-2">
					{#each filteredLogs as log}
						<div class="rounded-md border p-3 text-sm">
							<div class="flex items-center justify-between">
								<!-- <span class="font-medium"> -->
								<span>
									<!-- {formatTimestamp(log.timestamp)} -->
									{log.message}
								</span>
								<Badge variant={getLevelBadgeVariant(log.level)}>{log.level}</Badge>
							</div>
							<!-- <div class="mt-1 text-xs text-muted-foreground">
                                Source: {log.source}
                            </div> -->
							<!-- <div class="mt-2 whitespace-pre-wrap font-mono text-xs">
                                {log.message}
                            </div> -->
						</div>
					{/each}
				</div>
			{/if}
		</CardContent>
	</Card>
</div>
