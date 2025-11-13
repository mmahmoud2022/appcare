<script lang="ts">
  /**
   * Composant Bouton Moderne
   * 
   * Usage:
   * <Button variant="primary" size="md" on:click={handleClick}>
   *   Mon bouton
   * </Button>
   */
  
  export let variant: 'primary' | 'secondary' | 'outline' | 'success' | 'danger' = 'primary';
  export let size: 'sm' | 'md' | 'lg' = 'md';
  export let disabled = false;
  export let loading = false;
  export let fullWidth = false;
  export let icon: 'left' | 'right' | 'none' = 'none';
  export let type: 'button' | 'submit' | 'reset' = 'button';
  
  $: variantClass = {
    primary: 'btn-primary',
    secondary: 'btn-secondary',
    outline: 'btn-outline',
    success: 'btn-success',
    danger: 'btn-danger'
  }[variant];
  
  $: sizeClass = {
    sm: 'btn-sm',
    md: '',
    lg: 'btn-lg'
  }[size];
  
  $: widthClass = fullWidth ? 'w-full' : '';
</script>

<button
  {type}
  class="{variantClass} {sizeClass} {widthClass}"
  disabled={disabled || loading}
  on:click
  on:mouseenter
  on:mouseleave
  on:focus
  on:blur
>
  {#if loading}
    <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
  {/if}
  
  {#if icon === 'left' && !loading}
    <slot name="icon-left" />
  {/if}
  
  <slot />
  
  {#if icon === 'right' && !loading}
    <slot name="icon-right" />
  {/if}
</button>

<style>
  /* Styles supplémentaires si nécessaire */
  button {
    position: relative;
    overflow: hidden;
  }
  
  button:not(:disabled):active {
    transform: translateY(0) scale(0.98);
  }
</style>
