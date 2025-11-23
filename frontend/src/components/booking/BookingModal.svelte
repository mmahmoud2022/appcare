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
  export let wsConnected: boolean = false; // 🆕 État WebSocket
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
  export let onConsultationTypeChange: () => void = () => {}; // 🆕 Callback changement type
  export let consultationTypeOptions: (doctor: DoctorSearchResult | null) => { value: ConsultationType; label: string }[];

  let showNotes = false;
</script>

{#if show && selectedDoctor}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-2 sm:p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-2xl sm:rounded-3xl max-w-4xl w-full shadow-2xl max-h-[95vh] flex flex-col overflow-hidden border-2 border-gray-100" transition:fly={{ y: 30, duration: 300, easing: elasticOut }}>
      
      <!-- Header -->
      <div class="flex items-center justify-between p-4 sm:p-6 border-b border-gray-200 bg-white">
        <h3 class="text-lg sm:text-xl font-bold text-gray-900">Nouveau Rendez-vous</h3>
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
      <div class="p-4 sm:p-6 flex flex-col gap-4 sm:gap-6 overflow-y-auto flex-1">
        <!-- Doctor Card -->
        <BookingDoctorCard doctor={selectedDoctor} />

        <!-- Selected Slot Summary -->
        {#if bookingPayload.appointment_date}
          <div class="relative overflow-hidden bg-gradient-to-br from-violet-600 via-purple-600 to-fuchsia-600 rounded-xl sm:rounded-2xl p-4 sm:p-5 shadow-xl border-2 border-violet-400" transition:fly={{ y: -20, duration: 300 }}>
            <div class="absolute inset-0 bg-grid-white/10"></div>
            <div class="absolute top-0 right-0 w-24 h-24 sm:w-32 sm:h-32 bg-white/10 rounded-full blur-3xl -mr-12 sm:-mr-16 -mt-12 sm:-mt-16"></div>
            
            <div class="relative z-10">
              <div class="flex items-start gap-3 sm:gap-4">
                <!-- Success Icon -->
                <div class="w-10 h-10 sm:w-12 sm:h-12 bg-white/20 backdrop-blur-sm rounded-lg sm:rounded-xl flex items-center justify-center flex-shrink-0 animate-bounce">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 sm:h-6 sm:w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2 mb-1 sm:mb-2">
                    <h4 class="text-white font-bold text-base sm:text-lg">Créneau sélectionné</h4>
                    <div class="w-2 h-2 bg-green-400 rounded-full animate-pulse flex-shrink-0"></div>
                  </div>
                  
                  <div class="space-y-1 sm:space-y-2">
                    <!-- Date -->
                    <div class="flex items-center gap-2 text-white/95">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 text-white/80 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      <span class="font-semibold text-sm sm:text-base break-words">
                        {new Date(bookingPayload.appointment_date).toLocaleDateString('fr-FR', {
                          weekday: 'long',
                          day: 'numeric',
                          month: 'long',
                          year: 'numeric'
                        })}
                      </span>
                    </div>
                    
                    <!-- Time -->
                    <div class="flex items-center gap-2 text-white/95">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 text-white/80 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span class="font-bold text-xl">
                        {new Date(bookingPayload.appointment_date).toLocaleTimeString('fr-FR', {
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </span>
                    </div>
                    
                    <!-- Consultation Type -->
                    <div class="flex items-center gap-2">
                      {#if bookingPayload.consultation_type === 'teleconsultation'}
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-emerald-400/30 backdrop-blur-sm border border-emerald-300/50 text-white rounded-lg text-sm font-semibold">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          Téléconsultation
                        </span>
                      {:else}
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 bg-blue-400/30 backdrop-blur-sm border border-blue-300/50 text-white rounded-lg text-sm font-semibold">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                          </svg>
                          En cabinet
                        </span>
                      {/if}
                    </div>
                  </div>
                </div>
                
                <!-- Remove button -->
                <button
                  on:click={() => {
                    bookingPayload.appointment_date = '';
                    bookingPayload.schedule_entry_id = undefined;
                  }}
                  class="w-8 h-8 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg flex items-center justify-center transition-colors"
                  title="Changer de créneau"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        {/if}

        <!-- Slots Picker -->
        <BookingSlotPicker 
          {visibleSlotGroups}
          {canShowMoreSlots}
          {showAllSlots}
          {availabilityLoading}
          {availabilityError}
          {wsConnected}
          selectedConsultationType={bookingPayload.consultation_type}
          selectedDate={bookingPayload.appointment_date}
          selectedScheduleEntryId={bookingPayload.schedule_entry_id}
          onSlotSelect={onSlotSelect}
          onRefresh={onRefreshSlots}
          onToggleShowMore={onToggleShowAllSlots}
          onConsultationTypeFilterChange={(newType) => {
            bookingPayload.consultation_type = newType as any;
            bookingPayload.schedule_entry_id = undefined;
            onConsultationTypeChange();
          }}
        />

        <!-- Form Fields -->
        <div class="grid grid-cols-1 gap-4">
          <div class="space-y-2">
            <label for="booking-type" class="text-xs sm:text-sm font-semibold text-gray-700">
              Type de consultation
            </label>
            <select
              id="booking-type"
              bind:value={bookingPayload.consultation_type}
              on:change={() => {
                bookingPayload.schedule_entry_id = undefined;
                onConsultationTypeChange();
              }}
              class="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all bg-white text-sm sm:text-base"
            >
              {#each consultationTypeOptions(selectedDoctor) as option}
                <option value={option.value}>{option.label}</option>
              {/each}
            </select>
          </div>

          <div class="space-y-2">
            <label for="booking-reason" class="text-xs sm:text-sm font-semibold text-gray-700">
              Motif de consultation
            </label>
            <input
              id="booking-reason"
              type="text"
              bind:value={bookingPayload.reason}
              class="w-full px-3 sm:px-4 py-2.5 sm:py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-violet-500 focus:border-violet-500 transition-all bg-white text-sm sm:text-base"
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
      <div class="p-4 sm:p-5 bg-gray-50 border-t border-gray-200 flex flex-col sm:flex-row gap-3 justify-end">
        <button
          on:click={onClose}
          class="w-full sm:w-auto px-5 py-3 sm:py-2 border border-gray-300 text-gray-700 rounded-lg font-semibold hover:bg-gray-100 transition-all touch-target"
          disabled={bookingSubmitting}
        >
          Annuler
        </button>
        <button
          on:click={onSubmit}
          class="w-full sm:w-auto px-5 py-3 sm:py-2 bg-violet-600 text-white rounded-lg font-semibold hover:bg-violet-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed touch-target active:scale-95"
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
