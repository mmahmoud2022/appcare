<script lang="ts">
  /**
   * Alerte moderne avec animations
   * 
   * Usage:
   * <Alert variant="success" dismissible={true} on:dismiss={handleDismiss}>
   *   Votre rendez-vous a été confirmé !
   * </Alert>
   */
  
  import { fade, slide } from 'svelte/transition';
  import { createEventDispatcher } from 'svelte';
  
  const dispatch = createEventDispatcher();
  
  export let variant: 'success' | 'error' | 'warning' | 'info' = 'info';
  export let dismissible = false;
  export let title = '';
  export let icon = true;
  
  let visible = true;
  
  $: variantClass = {
    success: 'alert-success',
    error: 'alert-error',
    warning: 'alert-warning',
    info: 'alert-info'
  }[variant];
  
  $: iconSvg = {
    success: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />`,
    error: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`,
    warning: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />`,
    info: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />`
  }[variant];
  
  function handleDismiss() {
    visible = false;
    dispatch('dismiss');
  }
</script>

{#if visible}
  <div
    class="alert {variantClass}"
    transition:slide={{ duration: 300 }}
    role="alert"
  >
    {#if icon}
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        {@html iconSvg}
      </svg>
    {/if}
    
    <div class="flex-1">
      {#if title}
        <h3 class="font-bold mb-1">{title}</h3>
      {/if}
      <slot />
    </div>
    
    {#if dismissible}
      <button
        on:click={handleDismiss}
        class="ml-4 hover:opacity-70 transition-opacity"
        aria-label="Fermer l'alerte"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    {/if}
  </div>
{/if}
