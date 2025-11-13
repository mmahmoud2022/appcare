<script lang="ts">
  /**
   * Empty State moderne et engageant
   * 
   * Usage:
   * <EmptyState
   *   icon="calendar"
   *   title="Aucun rendez-vous"
   *   description="Prenez soin de votre santé"
   *   actionText="Prendre rendez-vous"
   *   on:action={handleAction}
   * />
   */
  
  import { scale } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  import { createEventDispatcher } from 'svelte';
  import Button from './Button.svelte';
  
  const dispatch = createEventDispatcher();
  
  export let icon: 'calendar' | 'user' | 'document' | 'heart' | 'star' = 'calendar';
  export let title = 'Aucune donnée disponible';
  export let description = '';
  export let actionText = '';
  export let gradient = 'from-gray-50 via-blue-50 to-purple-50';
  
  $: iconPath = {
    calendar: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z',
    user: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z',
    document: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
    heart: 'M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z',
    star: 'M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z'
  }[icon];
  
  function handleAction() {
    dispatch('action');
  }
</script>

<div 
  class="relative overflow-hidden bg-gradient-to-br {gradient} rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
  transition:scale={{ duration: 400, easing: elasticOut }}
>
  <!-- Blobs animés en arrière-plan -->
  <div class="absolute top-0 left-0 w-full h-full opacity-30 pointer-events-none">
    <div class="absolute top-10 left-10 w-20 h-20 bg-blue-400 rounded-full blur-xl animate-blob"></div>
    <div class="absolute top-20 right-10 w-32 h-32 bg-purple-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
    <div class="absolute bottom-10 left-1/2 w-24 h-24 bg-pink-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
  </div>
  
  <!-- Contenu -->
  <div class="relative z-10">
    <!-- Icône animée -->
    <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d={iconPath} />
      </svg>
    </div>
    
    <!-- Titre -->
    <h3 class="text-3xl font-black text-gray-900 mb-3">{title}</h3>
    
    <!-- Description -->
    {#if description}
      <p class="text-lg text-gray-600 mb-6 max-w-md mx-auto">{description}</p>
    {/if}
    
    <!-- Action -->
    {#if actionText}
      <Button variant="primary" size="lg" on:click={handleAction}>
        <svg slot="icon-left" xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        {actionText}
      </Button>
    {/if}
    
    <!-- Slot pour contenu personnalisé -->
    <slot />
  </div>
</div>

<style>
  @keyframes blob {
    0%, 100% {
      transform: translate(0, 0) scale(1);
    }
    33% {
      transform: translate(30px, -50px) scale(1.1);
    }
    66% {
      transform: translate(-20px, 20px) scale(0.9);
    }
  }
  
  .animate-blob {
    animation: blob 7s infinite;
  }
  
  .animation-delay-2000 {
    animation-delay: 2s;
  }
  
  .animation-delay-4000 {
    animation-delay: 4s;
  }
</style>
