<script lang="ts">
  /**
   * Composant Carte Moderne
   * 
   * Usage:
   * <Card variant="default" hover={true}>
   *   <div slot="header">Titre</div>
   *   Contenu principal
   *   <div slot="footer">Actions</div>
   * </Card>
   */
  
  import { fade } from 'svelte/transition';
  
  export let variant: 'default' | 'flat' | 'elevated' | 'glass' = 'default';
  export let hover = true;
  export let padding: 'none' | 'sm' | 'md' | 'lg' = 'md';
  export let borderAccent: 'none' | 'primary' | 'success' | 'warning' | 'error' = 'none';
  
  $: variantClass = {
    default: 'card',
    flat: 'card-flat',
    elevated: 'card-elevated',
    glass: 'glass-card'
  }[variant];
  
  $: paddingClass = {
    none: 'p-0',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8'
  }[padding];
  
  $: hoverClass = hover ? 'hover:-translate-y-1 hover:shadow-xl' : '';
  
  $: borderClass = borderAccent !== 'none' ? `border-l-4 border-${borderAccent}` : '';
</script>

<div 
  class="{variantClass} {paddingClass} {hoverClass} {borderClass} transition-all"
  transition:fade={{ duration: 300 }}
  role="article"
>
  {#if $$slots.header}
    <header class="mb-4 pb-4 border-b border-gray-200">
      <slot name="header" />
    </header>
  {/if}
  
  <div class="card-content">
    <slot />
  </div>
  
  {#if $$slots.footer}
    <footer class="mt-6 pt-4 border-t border-gray-200">
      <slot name="footer" />
    </footer>
  {/if}
</div>

<style>
  .glass-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(136, 180, 164, 0.2);
    box-shadow: var(--shadow-lg);
  }
  
  .border-primary {
    border-color: var(--color-primary-500);
  }
  
  .border-success {
    border-color: var(--color-success);
  }
  
  .border-warning {
    border-color: var(--color-warning);
  }
  
  .border-error {
    border-color: var(--color-error);
  }
</style>
