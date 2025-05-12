<script lang="ts">
    import { Button } from "$lib/components/ui/button/index.js";
    import { Label } from "$lib/components/ui/label/index.js";
    import { Switch } from "$lib/components/ui/switch/index.js";
  </script>
<Button>Hello</Button>
<h1>Welcome to SvelteKit</h1>
<p>Visit <a href="https://svelte.dev/docs/kit">svelte.dev/docs/kit</a> to read the documentation</p>
<div class="flex items-center space-x-2">
    <Switch id="airplane-mode" />
    <Label for="airplane-mode">Airplane Mode</Label>
  </div>