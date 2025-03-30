<script>
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
</script>

<svelte:head>
  <title>Hydroponic Control System</title>
  <meta name="description" content="Hydroponic Control System" />
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/css/bootstrap.min.css" />
</svelte:head>

<div class="container-fluid">
  <div class="row">
    <div class="col-md-2 d-none d-md-block bg-light sidebar">
      <div class="position-sticky pt-3">
        <ul class="nav flex-column">
          <li class="nav-item">
            <a class="nav-link" class:active={$page.url.pathname === '/'} href="/">
              Dashboard
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" class:active={$page.url.pathname === '/sensors'} href="/sensors">
              Sensors
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" class:active={$page.url.pathname === '/controllers'} href="/controllers">
              Controllers
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" class:active={$page.url.pathname === '/calibration'} href="/calibration">
              Calibration
            </a>
          </li>
          <li class="nav-item">
            <a class="nav-link" class:active={$page.url.pathname === '/settings'} href="/settings">
              Settings
            </a>
          </li>
        </ul>
      </div>
    </div>

    <main class="col-md-10 ms-sm-auto px-md-4">
      <div class="d-flex justify-content-between flex-wrap flex-md-nowrap align-items-center pt-3 pb-2 mb-3 border-bottom">
        <h1 class="h2">Hydroponic Control System</h1>
      </div>
      
      <slot />
    </main>
  </div>
</div>

<style>
  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 100;
    padding: 48px 0 0;
    box-shadow: inset -1px 0 0 rgba(0, 0, 0, 0.1);
  }
  
  .sidebar .nav-link {
    font-weight: 500;
    color: #333;
  }
  
  .sidebar .nav-link.active {
    color: #2470dc;
  }
</style>