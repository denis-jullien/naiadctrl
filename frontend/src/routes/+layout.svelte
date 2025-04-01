<script>
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import '../app.css';
	import { Button } from '$lib/components/ui/button';
	import ModeToggle from '$lib/components/mode-toggle.svelte';

	// Navigation items
	const navItems = [
		{ href: '/', label: 'Dashboard' },
		{ href: '/sensors', label: 'Sensors' },
		{ href: '/outputs', label: 'Outputs' },
		{ href: '/controllers', label: 'Controllers' },
		{ href: '/calibration', label: 'Calibration' },
		{ href: '/settings', label: 'Settings' }
	];
</script>

<div class="min-h-screen bg-background">
	<div class="flex">
		<!-- Sidebar -->
		<aside class="fixed inset-y-0 left-0 z-10 hidden w-64 border-r bg-card md:block">
			<div class="flex h-16 items-center border-b px-6">
				<h2 class="text-lg font-semibold">Hydroponic System</h2>
			</div>
			<nav class="p-4">
				<ul class="space-y-2">
					{#each navItems as item}
						<li>
							<a
								href={item.href}
								class="flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors
                      {$page.url.pathname === item.href
									? 'bg-accent text-accent-foreground'
									: 'hover:bg-accent hover:text-accent-foreground'}"
							>
								{item.label}
							</a>
						</li>
					{/each}
				</ul>
			</nav>
		</aside>

		<!-- Main content -->
		<main class="flex-1 md:ml-64">
			<header class="sticky top-0 z-10 flex h-16 items-center gap-4 border-b bg-background px-6">
				<div class="flex-1">
					<h1 class="text-xl font-semibold">Hydroponic Control System</h1>
				</div>
				<ModeToggle />
			</header>

			<div class="p-6">
				<slot />
			</div>
		</main>
	</div>
</div>
