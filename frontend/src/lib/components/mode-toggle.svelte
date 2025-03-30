<script>
  import { Button } from "$lib/components/ui/button";
  import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "$lib/components/ui/dropdown-menu";
  import { Moon, Sun } from "lucide-svelte";
  import { theme, toggleTheme } from "$lib/stores";
  
  function setTheme(newTheme) {
    theme.set(newTheme);
    document.documentElement.classList.toggle('dark', newTheme === 'dark');
  }
</script>

<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline" size="icon" class="rounded-full">
      <Sun class="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
      <Moon class="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
      <span class="sr-only">Toggle theme</span>
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onclick={() => setTheme("light")}>
      Light
    </DropdownMenuItem>
    <DropdownMenuItem onclick={() => setTheme("dark")}>
      Dark
    </DropdownMenuItem>
    <DropdownMenuItem onclick={() => setTheme("system")}>
      System
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>