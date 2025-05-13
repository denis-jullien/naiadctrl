<script lang="ts">
	import '../app.css';
	import { page } from '$app/stores';
	let { children } = $props();
</script>

<div class="min-h-screen bg-background">
  <div class="flex">
    <!-- Sidebar Navigation -->
    <aside class="w-64 bg-sidebar-background border-r border-border h-screen sticky top-0">
      <div class="p-6">
        <h2 class="text-2xl font-bold text-primary mb-6">Hydro Control</h2>
        <nav class="space-y-1">
          <a 
            href="/" 
            class="flex items-center px-3 py-2 rounded-md text-sm font-medium {$page.url.pathname === '/' ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
          >
            Dashboard
          </a>
          <a 
            href="/sensors" 
            class="flex items-center px-3 py-2 rounded-md text-sm font-medium {$page.url.pathname.startsWith('/sensors') ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
          >
            Sensors
          </a>
          <a 
            href="/controllers" 
            class="flex items-center px-3 py-2 rounded-md text-sm font-medium {$page.url.pathname.startsWith('/controllers') ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
          >
            Controllers
          </a>
          <a 
            href="/system" 
            class="flex items-center px-3 py-2 rounded-md text-sm font-medium {$page.url.pathname.startsWith('/system') ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground'}"
          >
            System
          </a>
        </nav>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 p-6">
      {@render children()}
    </main>
  </div>
</div>
