<script lang="ts">
  export let meetLink: string | null | undefined;
  export let appointmentDate: string;
  export let appointmentStatus: string;
  export let size: 'small' | 'medium' | 'large' = 'medium';

  // Vérifier si la téléconsultation est disponible
  $: canJoin = meetLink && (appointmentStatus === 'CONFIRMED' || appointmentStatus === 'confirmed');
  
  // Vérifier si c'est bientôt ou en cours
  $: appointmentTime = new Date(appointmentDate);
  $: now = new Date();
  $: minutesUntil = Math.floor((appointmentTime.getTime() - now.getTime()) / (1000 * 60));
  $: isNearby = minutesUntil <= 15 && minutesUntil >= -60; // 15 min avant à 60 min après
  $: isOngoing = minutesUntil <= 0 && minutesUntil >= -60; // En cours (pendant 60 min max)

  // Classes CSS selon la taille
  const sizeClasses = {
    small: 'px-3 py-1.5 text-xs',
    medium: 'px-4 py-2 text-sm',
    large: 'px-6 py-3 text-base'
  };

  function joinMeeting() {
    if (meetLink) {
      window.open(meetLink, '_blank', 'noopener,noreferrer');
    }
  }
</script>

{#if canJoin}
  <button
    on:click={joinMeeting}
    disabled={!isNearby}
    class="group relative font-bold rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 overflow-hidden {sizeClasses[size]} {isNearby ? 'hover:scale-105 cursor-pointer' : 'opacity-60 cursor-not-allowed'} z-10"
    title={isNearby ? 'Rejoindre la téléconsultation' : minutesUntil > 0 ? `Disponible ${minutesUntil} minutes avant le rendez-vous` : 'Téléconsultation terminée'}
  >
    <!-- Gradient background -->
    <div class="absolute inset-0 bg-gradient-to-r from-green-500 to-emerald-600 pointer-events-none"></div>
    
    <!-- Shimmer effect when active -->
    {#if isNearby}
      <div class="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000 pointer-events-none"></div>
    {/if}
    
    <!-- Content -->
    <span class="relative flex items-center gap-2 text-white drop-shadow-lg">
      <!-- Video icon -->
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 {isOngoing ? 'animate-pulse' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
      </svg>
      
      {#if isOngoing}
        <span class="font-extrabold">🔴 Rejoindre maintenant</span>
      {:else if minutesUntil > 0 && minutesUntil <= 15}
        <span>Rejoindre ({minutesUntil} min)</span>
      {:else if minutesUntil > 15}
        <span>Téléconsultation prévue</span>
      {:else}
        <span>Session expirée</span>
      {/if}
    </span>
  </button>

  <!-- Info message -->
  {#if !isNearby && minutesUntil > 0}
    <p class="text-xs text-gray-500 mt-1 italic">
      Le lien sera actif 15 minutes avant le rendez-vous
    </p>
  {/if}
{/if}

<style>
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }

  .animate-pulse {
    animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  }
</style>
