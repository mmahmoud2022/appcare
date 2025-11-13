<script lang="ts">
  /**
   * Composant Loading State moderne
   * 
   * Usage:
   * <LoadingState message="Chargement de vos données..." />
   */
  
  import { fade } from 'svelte/transition';
  
  export let message = 'Chargement...';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  
  $: sizeClass = {
    sm: 'h-8 w-8',
    md: 'h-16 w-16',
    lg: 'h-24 w-24'
  }[size];
  
  $: textSize = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg'
  }[size];
</script>

<div class="flex flex-col items-center justify-center py-12" transition:fade={{ duration: 300 }}>
  <div class="relative {sizeClass}">
    <!-- Spinner principal -->
    <div class="absolute inset-0 border-8 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
    <!-- Spinner secondaire -->
    <div class="absolute inset-0 border-8 border-fuchsia-200 border-t-fuchsia-600 rounded-full animate-spin" style="animation-direction: reverse; animation-delay: 150ms;"></div>
    <!-- Icône centrale -->
    <div class="absolute inset-0 flex items-center justify-center">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-1/2 w-1/2 text-violet-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    </div>
  </div>
  
  {#if message}
    <p class="{textSize} text-gray-600 font-medium mt-6 animate-pulse">{message}</p>
  {/if}
</div>
