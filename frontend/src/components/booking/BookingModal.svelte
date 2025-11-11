<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  import { slide } from 'svelte/transition';
  import type { DoctorSearchResult } from '../../lib/api-patient';
  import type { SlotSuggestionGroup, SlotSuggestion } from '../../lib/utils/slots';
  import type { ConsultationType } from '../../lib/api-doctor';
  import BookingDoctorCard from './BookingDoctorCard.svelte';
  import BookingSlotPicker from './BookingSlotPicker.svelte';
  import { CONSULTATION_LABELS } from '../../lib/utils/formatting';

  export let show: boolean;
  export let selectedDoctor: DoctorSearchResult | null;
  export let visibleSlotGroups: SlotSuggestionGroup[];
  export let canShowMoreSlots: boolean;
  export let showAllSlots: boolean;
  export let availabilityLoading: boolean;
  export let availabilityError: string | null;
  export let bookingPayload: {
    doctor_id: number;
    appointment_date: string;
    consultation_type: ConsultationType;
    reason: string;
    patient_notes: string;
    schedule_entry_id: number | undefined;
  };
  export let bookingSubmitting: boolean;
  export let onClose: () => void;
  export let onSlotSelect: (slot: SlotSuggestion) => void;
  export let onRefreshSlots: () => void;
  export let onSubmit: () => void;
  export let onToggleShowAllSlots: () => void;
  export let consultationTypeOptions: (doctor: DoctorSearchResult | null) => { value: ConsultationType; label: string }[];

  let showNotes = false;
</script>

{#if show && selectedDoctor}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-3xl max-w-4xl w-full shadow-2xl max-h-[95vh] flex flex-col overflow-hidden border-2 border-gray-100" transition:fly={{ y: 30, duration: 300, easing: elasticOut }}>
      
      <!-- Header -->
      <div class="flex items-center justify-between p-6 border-b border-gray-200 bg-white">
        <h3 class="text-xl font-bold text-gray-900">Nouveau Rendez-vous</h3>
        <button 
          on:click={onClose} 
          class="w-8 h-8 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors"
          title="Fermer"
        >
          <svg class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Content -->
      <div class="p-6 flex flex-col gap-6 overflow-y-auto flex-1">
        <!-- Doctor Card -->
        <BookingDoctorCard doctor={selectedDoctor} />

        <!-- Slots Picker -->
        <BookingSlotPicker 
          {visibleSlotGroups}
          {canShowMoreSlots}
          {showAllSlots}
          {availabilityLoading}
          {availabilityError}
          selectedDate={bookingPayload.appointment_date}
          selectedScheduleEntryId={bookingPayload.schedule_entry_id}
          onSlotSelect={onSlotSelect}
          onRefresh={onRefreshSlots}
          onToggleShowMore={onToggleShowAllSlots}
        />

        <!-- Form Fields -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div class="space-y-2 md:col-span-2">
            <label for="booking-type" class="text-sm font-semibold text-gray-700">
              Type de consultation
            </label>
            <select
              id="booking-type"
              bind:value={bookingPayload.consultation_type}
              on:change={() => bookingPayload.schedule_entry_id = undefined}
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all bg-white"
            >
              {#each consultationTypeOptions(selectedDoctor) as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
          </div>

          <div class="space-y-2 md:col-span-2">
            <label for="booking-reason" class="text-sm font-semibold text-gray-700">
              Motif de consultation
            </label>
            <input
              id="booking-reason"
              type="text"
              bind:value={bookingPayload.reason}
              class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all bg-white"
              placeholder="Ex: Consultation de suivi, urgence..."
            />
          </div>

          <!-- Notes accordion -->
          <div class="space-y-2 md:col-span-2">
            <button
              type="button"
              on:click={() => showNotes = !showNotes}
              class="flex items-center gap-2 text-sm font-semibold text-gray-700 hover:text-violet-600 transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 transition-transform {showNotes ? 'rotate-90' : ''}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
              Notes supplémentaires (optionnel)
            </button>
            {#if showNotes}
              <div transition:slide={{ duration: 200 }}>
                <textarea
                  id="booking-notes"
                  bind:value={bookingPayload.patient_notes}
                  rows="3"
                  class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all bg-white resize-none"
                  placeholder="Informations complémentaires pour le praticien..."
                ></textarea>
              </div>
            {/if}
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="p-4 bg-gray-50 border-t border-gray-200 flex gap-3 justify-end">
        <button
          on:click={onClose}
          class="px-5 py-2 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-100 transition-all"
          disabled={bookingSubmitting}
        >
          Annuler
        </button>
        <button
          on:click={onSubmit}
          class="px-5 py-2 bg-violet-600 text-white rounded-lg font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          disabled={bookingSubmitting || !bookingPayload.appointment_date}
        >
          {#if bookingSubmitting}
            <span class="flex items-center gap-2">
              <svg class="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Confirmation...
            </span>
          {:else}
            Confirmer
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}
