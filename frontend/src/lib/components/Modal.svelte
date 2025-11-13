<script lang="ts">
  /**
   * Modal moderne avec glassmorphism et animations
   * 
   * Usage:
   * <Modal bind:open={showModal} title="Mon Modal">
   *   Contenu du modal
   *   <div slot="footer">
   *     <Button>Fermer</Button>
   *   </div>
   * </Modal>
   */
  
  import { fade, scale } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  
  export let open = false;
  export let title = '';
  export let size: 'sm' | 'md' | 'lg' | 'xl' | 'full' = 'md';
  export let closable = true;
  export let closeOnBackdrop = true;
  
  $: sizeClass = {
    sm: 'max-w-md',
    md: 'max-w-lg',
    lg: 'max-w-2xl',
    xl: 'max-w-4xl',
    full: 'max-w-6xl'
  }[size];
  
  function handleBackdropClick() {
    if (closeOnBackdrop && closable) {
      open = false;
    }
  }
  
  function handleClose() {
    if (closable) {
      open = false;
    }
  }
  
  // Empêcher le scroll du body quand le modal est ouvert
  $: if (open) {
    document.body.style.overflow = 'hidden';
  } else {
    document.body.style.overflow = '';
  }
</script>

{#if open}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
    transition:fade={{ duration: 200 }}
    on:click={handleBackdropClick}
    on:keydown={(e) => e.key === 'Escape' && handleClose()}
    role="button"
    tabindex="0"
  >
    <!-- Modal Content -->
    <div
      class="bg-white rounded-3xl {sizeClass} w-full shadow-2xl max-h-[90vh] flex flex-col"
      transition:scale={{ duration: 400, easing: elasticOut }}
      on:click|stopPropagation
      on:keydown
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      tabindex="-1"
    >
      <!-- Header -->
      <header class="px-8 py-6 bg-gradient-to-r from-blue-600 to-indigo-600 rounded-t-3xl flex items-center justify-between">
        <h2 id="modal-title" class="text-2xl font-bold text-white">
          {title}
        </h2>
        {#if closable}
          <button
            on:click={handleClose}
            class="text-white/80 hover:text-white hover:bg-white/20 rounded-xl p-2 transition-all"
            aria-label="Fermer le modal"
          >
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        {/if}
      </header>
      
      <!-- Body -->
      <div class="px-8 py-6 flex-1 overflow-y-auto scrollbar-thin scrollbar-thumb-blue-300 scrollbar-track-blue-50">
        <slot />
      </div>
      
      <!-- Footer -->
      {#if $$slots.footer}
        <footer class="px-8 py-6 border-t-2 border-gray-200 bg-gradient-to-r from-gray-50 to-blue-50/30 rounded-b-3xl">
          <slot name="footer" />
        </footer>
      {/if}
    </div>
  </div>
{/if}

<style>
  /* Scrollbar personnalisée pour WebKit */
  :global(.scrollbar-thin::-webkit-scrollbar) {
    width: 6px;
  }
  
  :global(.scrollbar-thin::-webkit-scrollbar-track) {
    background: #eff6ff;
    border-radius: 10px;
  }
  
  :global(.scrollbar-thin::-webkit-scrollbar-thumb) {
    background: #93c5fd;
    border-radius: 10px;
  }
  
  :global(.scrollbar-thin::-webkit-scrollbar-thumb:hover) {
    background: #60a5fa;
  }
</style>
