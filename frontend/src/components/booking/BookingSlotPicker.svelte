<script lang="ts">
  import { fly, fade } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import type { SlotSuggestionGroup } from '../../lib/utils/slots';
  import { isSlotSelected } from '../../lib/utils/slots';
  import type { SlotSuggestion } from '../../lib/utils/slots';

  export let visibleSlotGroups: SlotSuggestionGroup[];
  export let canShowMoreSlots: boolean;
  export let showAllSlots: boolean;
  export let availabilityLoading: boolean;
  export let availabilityError: string | null;
  export let selectedDate: string;
  export let selectedScheduleEntryId: number | undefined;
  export let wsConnected: boolean = false; // 🆕 État connexion WebSocket
  export let selectedConsultationType: string = 'in_person'; // 🆕 Type sélectionné dans le dropdown
  export let hideFilters: boolean = false; // 🆕 Masquer les filtres (pour RescheduleModal)
  export let onSlotSelect: (slot: SlotSuggestion) => void;
  export let onRefresh: () => void;
  export let onToggleShowMore: () => void;
  export let onConsultationTypeFilterChange: (newType: string) => void = () => {}; // 🆕 Callback changement filtre
  
  // 🆕 Filtre par type de consultation (synchronisé avec selectedConsultationType)
  type ConsultationFilter = 'all' | 'in_person' | 'teleconsultation';
  let consultationFilter: ConsultationFilter = 'all';
  
  // 🆕 Synchroniser le filtre quand le type de consultation change dans le dropdown
  $: {
    if (selectedConsultationType === 'both') {
      consultationFilter = 'all';
    } else if (selectedConsultationType === 'in_person' || selectedConsultationType === 'teleconsultation') {
      consultationFilter = selectedConsultationType as ConsultationFilter;
    }
  }
  
  // 🆕 Fonction pour changer le filtre et notifier le parent
  function changeFilter(newFilter: ConsultationFilter) {
    consultationFilter = newFilter;
    
    // Mettre à jour le type de consultation dans le parent
    if (newFilter === 'all') {
      // Si on sélectionne "Tous", passer en mode "both" si disponible
      onConsultationTypeFilterChange('both');
    } else {
      // Sinon, synchroniser avec le filtre sélectionné
      onConsultationTypeFilterChange(newFilter);
    }
  }
  
  // Filtrer les groupes selon le type de consultation
  $: filteredGroups = visibleSlotGroups.map(group => ({
    ...group,
    slots: group.slots.filter(slot => {
      if (consultationFilter === 'all') return true;
      return slot.consultation_type === consultationFilter || slot.entry.consultation_type === 'both';
    })
  })).filter(group => group.slots.length > 0);
  
  // Fonction helper pour déterminer le style du slot
  function getSlotStyle(suggestion: SlotSuggestion, isSelected: boolean) {
    const consultType = suggestion.entry.consultation_type || suggestion.consultation_type;
    const isAvailable = suggestion.is_available !== false; // Par défaut true si non défini
    
    // 🔴 Créneaux NON disponibles (bloqués par le docteur)
    if (!isAvailable) {
      return 'border-red-400 bg-red-50/80 text-gray-500 cursor-not-allowed opacity-60 relative overflow-hidden';
    }
    
    if (isSelected) {
      return 'border-violet-600 bg-gradient-to-br from-violet-600 via-purple-600 to-fuchsia-600 text-white shadow-xl scale-105 ring-4 ring-violet-300';
    }
    
    if (consultType === 'both') {
      return 'border-purple-300 bg-gradient-to-br from-blue-50 via-white to-emerald-50 hover:from-blue-100 hover:to-emerald-100 text-gray-900 hover:border-purple-400 hover:shadow-lg hover:scale-102';
    } else if (consultType === 'teleconsultation') {
      return 'border-emerald-300 bg-emerald-50 hover:bg-emerald-100 hover:border-emerald-500 text-gray-900 hover:shadow-lg hover:scale-102';
    } else {
      return 'border-blue-300 bg-blue-50 hover:bg-blue-100 hover:border-blue-500 text-gray-900 hover:shadow-lg hover:scale-102';
    }
  }
</script>


<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between flex-wrap gap-3">
    <div class="flex items-center gap-3">
      <h4 class="text-base font-semibold text-gray-900">Créneaux disponibles</h4>
      
      <!-- 🆕 Indicateur connexion WebSocket -->
      {#if wsConnected}
        <div class="flex items-center gap-1.5 px-2 py-1 bg-green-50 border border-green-200 rounded-full" transition:fade>
          <div class="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <span class="text-xs font-semibold text-green-700">Temps réel</span>
        </div>
      {/if}
    </div>
    
    <button
      class="px-3 py-1.5 bg-violet-100 hover:bg-violet-200 text-violet-700 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors"
      on:click={onRefresh}
      disabled={availabilityLoading}
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 {availabilityLoading ? 'animate-spin' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
      </svg>
      Actualiser
    </button>
  </div>
  
  <!-- 🆕 Filtres par type de consultation (masqués si hideFilters=true) -->
  {#if visibleSlotGroups.length > 0 && !hideFilters}
    <div class="space-y-3" transition:fade>
      <div class="flex gap-2 flex-wrap">
        <button
          class={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
            consultationFilter === 'all'
              ? 'bg-violet-600 text-white shadow-sm'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
          on:click={() => changeFilter('all')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 sm:h-4 sm:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
          </svg>
          <span class="hidden sm:inline">Tous</span>
          <span class="sm:hidden">Tous</span>
        </button>
        
        <button
          class={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
            consultationFilter === 'in_person'
              ? 'bg-blue-600 text-white shadow-sm'
              : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
          }`}
          on:click={() => changeFilter('in_person')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 sm:h-4 sm:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
          <span class="hidden sm:inline">Cabinet</span>
          <span class="sm:hidden">🏥</span>
        </button>
        
        <button
          class={`px-3 py-1.5 rounded-lg text-xs sm:text-sm font-semibold transition-all flex items-center gap-1.5 ${
            consultationFilter === 'teleconsultation'
              ? 'bg-emerald-600 text-white shadow-sm'
              : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200'
          }`}
          on:click={() => changeFilter('teleconsultation')}
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5 sm:h-4 sm:w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
          <span class="hidden sm:inline">Téléconsultation</span>
          <span class="sm:hidden">📹</span>
        </button>
      </div>
      
      <!-- 🆕 Message de synchronisation -->
      {#if selectedConsultationType !== 'both' && (selectedConsultationType === 'in_person' || selectedConsultationType === 'teleconsultation')}
        <div class="flex items-center gap-2 text-xs bg-violet-50 text-violet-700 rounded-lg px-3 py-2 border border-violet-200" transition:fade>
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
          <span class="font-medium">
            Filtre synchronisé avec le type de consultation sélectionné
          </span>
        </div>
      {/if}
      
      <!-- 🆕 Légende visuelle -->
      <div class="flex items-center gap-3 text-xs text-gray-600 bg-gray-50 rounded-lg px-3 py-2 border border-gray-200">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span class="flex-1">
          <span class="font-semibold text-blue-700">Bleu</span> = Cabinet • 
          <span class="font-semibold text-emerald-700">Vert</span> = Téléconsultation • 
          <span class="font-semibold text-purple-700">Mixte</span> = Au choix • 
          <span class="font-semibold text-red-700">Rouge rayé</span> = Indisponible
        </span>
      </div>
    </div>
  {/if}
  
  <!-- Content -->
  {#if availabilityLoading}
    <div class="flex flex-col items-center justify-center py-8 bg-gray-50 rounded-lg border border-gray-200">
      <div class="w-12 h-12 border-3 border-gray-200 border-t-violet-600 rounded-full animate-spin mb-3"></div>
      <p class="text-sm font-medium text-gray-600">Chargement des créneaux...</p>
    </div>
  {:else if availabilityError}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <div class="flex items-start gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <h5 class="font-semibold text-red-900 text-sm mb-1">Erreur de chargement</h5>
          <p class="text-red-700 text-sm">{availabilityError}</p>
        </div>
      </div>
    </div>
  {:else if filteredGroups.length}
    <div class="space-y-3 max-h-[350px] overflow-y-auto pr-2">
      {#each filteredGroups as group (group.key)}
        <div class="bg-white rounded-lg p-2 sm:p-3 border border-gray-200" transition:fly={{ y: 12, duration: 180 }} animate:flip>
          <div class="flex items-center justify-between mb-2">
            <p class="text-xs sm:text-sm font-semibold text-gray-900 truncate">{group.label}</p>
            <span class="px-2 py-0.5 bg-violet-100 rounded-full text-xs font-semibold text-violet-700 ml-2">{group.slots.length}</span>
          </div>
          
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
            {#each group.slots as suggestion (suggestion.start.toISOString())}
              {@const isSelected = isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId)}
              {@const consultType = suggestion.entry.consultation_type || suggestion.consultation_type}
              {@const isAvailable = suggestion.is_available !== false}
              
              <button
                class={`rounded-lg border-2 p-2 sm:p-2.5 text-left transition-all ${isAvailable ? 'active:scale-95' : ''} ${getSlotStyle(suggestion, isSelected)}`}
                on:click={() => isAvailable && onSlotSelect(suggestion)}
                disabled={!isAvailable}
              >
                <!-- 🔴 Barre de rayure diagonale pour les créneaux non disponibles -->
                {#if !isAvailable}
                  <div class="absolute inset-0 pointer-events-none">
                    <svg class="w-full h-full" xmlns="http://www.w3.org/2000/svg">
                      <line x1="0" y1="0" x2="100%" y2="100%" stroke="currentColor" stroke-width="2" class="text-red-500 opacity-40" />
                      <line x1="100%" y1="0" x2="0" y2="100%" stroke="currentColor" stroke-width="2" class="text-red-500 opacity-40" />
                    </svg>
                  </div>
                {/if}
                
                <div class="flex items-start gap-1.5 sm:gap-2 relative z-10">
                  <!-- Icône selon le type (cachée sur mobile, badge emoji suffit) -->
                  <div class="hidden sm:block">
                    {#if consultType === 'teleconsultation'}
                      <svg xmlns="http://www.w3.org/2000/svg" class={`h-5 w-5 flex-shrink-0 mt-0.5 ${isSelected ? 'text-white' : 'text-emerald-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                      </svg>
                    {:else if consultType === 'both'}
                      <svg xmlns="http://www.w3.org/2000/svg" class={`h-5 w-5 flex-shrink-0 mt-0.5 ${isSelected ? 'text-white' : 'text-purple-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                      </svg>
                    {:else}
                      <svg xmlns="http://www.w3.org/2000/svg" class={`h-5 w-5 flex-shrink-0 mt-0.5 ${isSelected ? 'text-white' : 'text-blue-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                      </svg>
                    {/if}
                  </div>
                  
                  <div class="flex-1 min-w-0">
                    <!-- Heure (rayée si non disponible) -->
                    <p class={`text-xs sm:text-sm font-bold mb-1 ${
                      !isAvailable ? 'line-through text-gray-400' : 
                      isSelected ? 'text-white' : 'text-gray-900'
                    }`}>
                      {suggestion.start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} - {suggestion.end.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    
                    <!-- Badge type consultation ou indisponible -->
                    {#if !isAvailable}
                      <span class="inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold bg-red-100 text-red-700 border border-red-300">
                        🚫 Indisponible
                      </span>
                    {:else if consultType === 'teleconsultation'}
                      <span class={`inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        📹 <span class="hidden sm:inline">Téléconsultation</span><span class="sm:hidden">Télé</span>
                      </span>
                    {:else if consultType === 'both'}
                      <span class={`inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-purple-100 text-purple-700'
                      }`}>
                        🎯 <span class="hidden sm:inline">Cabinet ou Télé</span><span class="sm:hidden">Mixte</span>
                      </span>
                    {:else}
                      <span class={`inline-flex items-center gap-1 px-1.5 sm:px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-semibold ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-blue-100 text-blue-700'
                      }`}>
                        🏥 Cabinet
                      </span>
                    {/if}
                  </div>
                  
                  <!-- Checkmark si sélectionné -->
                  {#if isSelected}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 text-white flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
        </div>
      {/each}
    </div>
    
    {#if canShowMoreSlots}
      <div class="flex justify-center">
        <button
          class="px-4 py-2 bg-violet-100 hover:bg-violet-200 text-violet-700 rounded-lg text-sm font-semibold flex items-center gap-2 transition-colors"
          on:click={onToggleShowMore}
        >
          {#if showAllSlots}
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
            </svg>
            Afficher moins
          {:else}
            Afficher plus
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
            </svg>
          {/if}
        </button>
      </div>
    {/if}
  {:else if visibleSlotGroups.length > 0 && filteredGroups.length === 0}
    <!-- Aucun créneau ne correspond au filtre -->
    <div class="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
      </svg>
      <h5 class="text-sm font-semibold text-gray-700 mb-1">Aucun créneau pour ce type</h5>
      <p class="text-sm text-gray-500">Essayez un autre filtre de consultation</p>
    </div>
  {:else}
    <div class="text-center py-8 bg-gray-50 rounded-lg border border-gray-200">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <h5 class="text-sm font-semibold text-gray-700 mb-1">Aucun créneau disponible</h5>
      <p class="text-sm text-gray-500">Aucun horaire n'est disponible pour l'instant</p>
    </div>
  {/if}
</div>