<script>
  import { buttonVariants } from "$lib/components/ui/button/index.js";
  import * as DropdownMenu from "$lib/components/ui/dropdown-menu/index.js"
  import { Moon, Sun } from "lucide-svelte";
  import { theme, toggleTheme } from "$lib/stores";
  
  function setTheme(newTheme) {
    theme.set(newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  }
</script>

<DropdownMenu.Root>
  <DropdownMenu.Trigger
  class={buttonVariants({ variant: "outline", size: "icon" })}
>
  <Sun
    class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0"
  />
  <Moon
    class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100"
  />
  <span class="sr-only">Toggle theme</span>
</DropdownMenu.Trigger>
  <DropdownMenu.Content align="end">
    <DropdownMenu.Item onclick={() => setTheme("light")}>
      Light
    </DropdownMenu.Item>
    <DropdownMenu.Item onclick={() => setTheme("dark")}>
      Dark
    </DropdownMenu.Item>
    <DropdownMenu.Item onclick={() => setTheme("system")}>
      System
    </DropdownMenu.Item>
  </DropdownMenu.Content>
</DropdownMenu.Root>
