<script lang="ts">
  /**
   * Badge moderne pour statuts et tags
   * 
   * Usage:
   * <Badge variant="success">Confirmé</Badge>
   * <Badge variant="warning" size="lg" icon={true}>En attente</Badge>
   */
  
  export let variant: 'primary' | 'success' | 'warning' | 'error' | 'neutral' | 'info' = 'neutral';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let icon = false;
  export let pulse = false;
  
  $: variantClass = {
    primary: 'badge-primary',
    success: 'badge-success',
    warning: 'badge-warning',
    error: 'badge-error',
    neutral: 'badge-neutral',
    info: 'bg-blue-100 text-blue-700'
  }[variant];
  
  $: sizeClass = {
    sm: 'text-xs px-2 py-1',
    md: 'text-sm px-3 py-1.5',
    lg: 'text-base px-4 py-2'
  }[size];
  
  $: pulseClass = pulse ? 'animate-pulse' : '';
  
  $: iconEmoji = {
    primary: '🔵',
    success: '✓',
    warning: '⚠️',
    error: '✗',
    neutral: '⊙',
    info: 'ℹ️'
  }[variant];
</script>

<span class="badge {variantClass} {sizeClass} {pulseClass}">
  {#if icon}
    <span class="mr-1">{iconEmoji}</span>
  {/if}
  <slot />
</span>

<style>
  .badge {
    display: inline-flex;
    align-items: center;
    font-weight: 600;
    border-radius: var(--radius-full);
    line-height: 1;
  }
</style>
