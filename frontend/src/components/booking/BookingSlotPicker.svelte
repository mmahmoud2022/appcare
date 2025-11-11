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
  export let onSlotSelect: (slot: SlotSuggestion) => void;
  export let onRefresh: () => void;
  export let onToggleShowMore: () => void;
</script>

<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <h4 class="text-base font-semibold text-gray-900">Créneaux disponibles</h4>
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
  {:else if visibleSlotGroups.length}
    <div class="space-y-3 max-h-[350px] overflow-y-auto pr-2">
      {#each visibleSlotGroups as group (group.key)}
        <div class="bg-white rounded-lg p-3 border border-gray-200" transition:fly={{ y: 12, duration: 180 }} animate:flip>
          <div class="flex items-center justify-between mb-2">
            <p class="text-sm font-semibold text-gray-900">{group.label}</p>
            <span class="px-2 py-0.5 bg-violet-100 rounded-full text-xs font-semibold text-violet-700">{group.slots.length}</span>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
            {#each group.slots as suggestion (suggestion.start.toISOString())}
              <button
                class={`rounded-lg border p-2.5 text-left transition-all ${
                  isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId) 
                    ? 'border-violet-600 bg-violet-600 text-white' 
                    : 'border-gray-300 bg-white hover:border-violet-400 hover:bg-violet-50 text-gray-900'
                }`}
                on:click={() => onSlotSelect(suggestion)}
              >
                <div class="flex items-center gap-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class={`h-4 w-4 flex-shrink-0 ${isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId) ? 'text-white' : 'text-violet-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div class="flex-1 min-w-0">
                    <p class={`text-sm font-semibold ${isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId) ? 'text-white' : 'text-gray-900'}`}>
                      {suggestion.start.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })} - {suggestion.end.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </p>
                    <p class={`text-xs truncate ${isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId) ? 'text-white/90' : 'text-gray-600'}`}>
                      {suggestion.entry.consultation_type === 'in_person' ? 'Cabinet' : suggestion.entry.consultation_type === 'teleconsultation' ? 'Téléconsultation' : 'Cabinet/Télé'}
                    </p>
                  </div>
                  {#if isSlotSelected(suggestion, selectedDate, selectedScheduleEntryId)}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
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
