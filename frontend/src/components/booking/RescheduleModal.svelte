<script lang="ts">
  import { fade, fly } from 'svelte/transition';
  import { elasticOut } from 'svelte/easing';
  import type { PatientAppointment } from '../../lib/api-patient';
  import type { DoctorSearchResult } from '../../lib/api-patient';
  import type { DoctorScheduleEntry, ConsultationType } from '../../lib/api-doctor';
  import type { SlotSuggestionGroup, SlotSuggestion } from '../../lib/utils/slots';
  import { generateSlotSuggestions, groupSlotsByDay } from '../../lib/utils/slots';
  import { CONSULTATION_LABELS } from '../../lib/utils/formatting';
  import BookingSlotPicker from './BookingSlotPicker.svelte';

  export let show: boolean;
  export let appointment: PatientAppointment | null;
  export let doctorSchedule: DoctorScheduleEntry[]; // 🗑️ Obsolète
  export let slotsCache: SlotSuggestion[] = []; // 🆕 Créneaux absolus depuis l'API
  export let availabilityLoading: boolean;
  export let availabilityError: string | null;
  export let rescheduleNotes: string;
  export let submitting: boolean;
  export let showConfirm: boolean;
  export let doctorDetails: DoctorSearchResult | null = null;
  export let onClose: () => void;
  export let onLoadSchedule: (doctorId: number, consultationType: ConsultationType) => void;
  export let onSubmit: () => void;
  export let onConfirm: () => void;
  export let onBack: () => void;

  let selectedDate = '';
  let selectedScheduleEntryId: number | undefined;
  let showAllSlots = false;
  let selectedConsultationType: ConsultationType = 'in_person';

  // Initialiser le type de consultation
  $: if (appointment && show) {
    selectedConsultationType = appointment.consultation_type;
  }

  // 🆕 Reactive statements pour les créneaux - utiliser slotsCache au lieu de générer depuis doctorSchedule
  $: {
    console.log('📊 RescheduleModal - État des créneaux:', {
      slotsCacheLength: slotsCache.length,
      doctorScheduleLength: doctorSchedule.length,
      selectedConsultationType
    });
  }
  
  $: slotSuggestions = slotsCache.length > 0 
    ? slotsCache.filter(slot => {
        // Filtrer par type de consultation
        if (selectedConsultationType === 'both') return true;
        return slot.consultation_type === selectedConsultationType || slot.consultation_type === 'both';
      })
    : (appointment ? generateSlotSuggestions(doctorSchedule, selectedConsultationType, 20, 4) : []);
  
  $: {
    console.log('📊 RescheduleModal - Créneaux filtrés:', {
      slotSuggestionsLength: slotSuggestions.length,
      groupsLength: groupSlotsByDay(slotSuggestions).length
    });
  }
  
  $: slotSuggestionGroups = groupSlotsByDay(slotSuggestions);
  $: visibleSlotGroups = showAllSlots ? slotSuggestionGroups : slotSuggestionGroups.slice(0, 3);
  $: canShowMoreSlots = slotSuggestionGroups.length > 3;

  // Charger le planning quand on ouvre la modal ou change le type
  $: if (show && appointment && !availabilityLoading && slotsCache.length === 0 && doctorSchedule.length === 0) {
    onLoadSchedule(appointment.doctor_id, selectedConsultationType);
  }

  // Options de consultation disponibles
  $: consultationTypeOptions = (() => {
    if (!doctorDetails) {
      return [
        { value: 'in_person' as ConsultationType, label: 'En cabinet' },
        { value: 'teleconsultation' as ConsultationType, label: 'Téléconsultation' }
      ];
    }
    if (doctorDetails.consultation_types === 'both') {
      return [
        { value: 'in_person' as ConsultationType, label: 'En cabinet' },
        { value: 'teleconsultation' as ConsultationType, label: 'Téléconsultation' }
      ];
    }
    return [{ value: doctorDetails.consultation_types, label: CONSULTATION_LABELS[doctorDetails.consultation_types] }];
  })();

  // Recharger les créneaux quand on change le type de consultation
  const handleConsultationTypeChange = () => {
    if (appointment) {
      showAllSlots = false;
      selectedDate = '';
      selectedScheduleEntryId = undefined;
      onLoadSchedule(appointment.doctor_id, selectedConsultationType);
    }
  };

  const selectSlot = (slot: SlotSuggestion) => {
    const isoString = slot.start.toISOString();
    selectedDate = isoString.slice(0, 16); // Format pour datetime-local
    selectedScheduleEntryId = slot.entry.id;
  };

  const formatAppointmentLabel = (appt: PatientAppointment) => {
    const date = new Date(appt.appointment_date).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    const doctorName = [appt.doctor_first_name, appt.doctor_last_name].filter(Boolean).join(' ') || 'Médecin';
    return `${date} · ${doctorName}`;
  };

  const handleSubmit = () => {
    if (!selectedDate) return;
    // Mettre à jour l'objet appointment avec la nouvelle date et type de consultation
    if (appointment) {
      const newDate = new Date(selectedDate);
      appointment.appointment_date = newDate.toISOString();
      appointment.consultation_type = selectedConsultationType;
    }
    onSubmit();
  };

  // Réinitialiser quand on ferme
  $: if (!show) {
    selectedDate = '';
    selectedScheduleEntryId = undefined;
    showAllSlots = false;
    if (appointment) {
      selectedConsultationType = appointment.consultation_type;
    }
  }
</script>

{#if show && appointment}
  <div class="fixed inset-0 flex items-center justify-center z-50 p-2 sm:p-4" transition:fade={{ duration: 200 }}>
    <div class="absolute inset-0 bg-black/60 backdrop-blur-md pointer-events-none"></div>
    <div class="bg-white rounded-2xl sm:rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden border-2 border-gray-100 relative z-[1] isolate pointer-events-auto" transition:fly={{ y: 30, duration: 300, easing: elasticOut }}>
      
      {#if !showConfirm}
        <!-- Écran de sélection -->
        <!-- Enhanced Header -->
        <div class="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 p-4 sm:p-6 md:p-8">
          <div class="absolute inset-0 bg-grid-white/10"></div>
          <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <div class="relative flex items-center justify-between gap-2">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <div class="w-12 h-12 sm:w-14 sm:h-14 md:w-16 md:h-16 bg-white/20 backdrop-blur-sm rounded-xl sm:rounded-2xl flex items-center justify-center shadow-xl border-2 border-white/30 flex-shrink-0">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 sm:h-7 sm:w-7 md:h-8 md:w-8 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="min-w-0">
                <h3 class="text-lg sm:text-xl md:text-2xl font-black text-white drop-shadow-lg truncate"><span class="hide-mobile">Replanifier le rendez-vous</span><span class="show-mobile">Replanifier</span></h3>
                <p class="text-sm sm:text-base text-white/90 font-medium hide-mobile">Choisissez un nouveau créneau</p>
              </div>
            </div>
            <button 
              on:click={onClose} 
              class="w-10 h-10 sm:w-11 sm:h-11 md:w-12 md:h-12 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-lg sm:rounded-xl flex items-center justify-center transition-all border-2 border-white/30 hover:border-white/50 group flex-shrink-0 touch-target"
              title="Fermer"
            >
              <svg class="h-5 w-5 sm:h-6 sm:w-6 text-white group-hover:rotate-90 transition-transform duration-300 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
        
        <!-- Content -->
        <div class="p-4 sm:p-6 md:p-8 space-y-4 sm:space-y-6 max-h-[calc(95vh-280px)] overflow-y-auto">
          <!-- Current Appointment Info -->
          <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl sm:rounded-2xl p-4 sm:p-5 md:p-6 border-2 border-amber-200">
            <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-200/30 to-orange-200/30 rounded-full blur-2xl -mr-16 -mt-16"></div>
            <div class="relative">
              <div class="flex items-center gap-3 mb-3">
                <div class="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h4 class="text-lg font-black text-gray-900">Rendez-vous actuel</h4>
              </div>
              <p class="text-gray-700 font-semibold">{formatAppointmentLabel(appointment)}</p>
            </div>
          </div>

          <!-- Consultation Type Selector -->
          {#if consultationTypeOptions.length > 1}
            <div class="space-y-3">
              <div class="flex items-center gap-2 text-sm font-bold text-gray-900">
                <div class="w-6 h-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                </div>
                Type de consultation
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {#each consultationTypeOptions as option}
                  <button
                    type="button"
                    on:click={() => {
                      selectedConsultationType = option.value;
                      handleConsultationTypeChange();
                    }}
                    class={`group relative overflow-hidden px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-bold transition-all transform hover:scale-105 active:scale-95 touch-target ${
                      selectedConsultationType === option.value
                        ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-xl'
                        : 'bg-white border-2 border-gray-300 text-gray-700 hover:border-indigo-400 shadow-sm hover:shadow-md'
                    }`}
                  >
                    <div class="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                    <span class="relative flex items-center justify-center gap-2">
                      {#if option.value === 'in_person'}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                        </svg>
                      {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                        </svg>
                      {/if}
                      {option.label}
                    </span>
                    {#if selectedConsultationType === option.value}
                      <div class="absolute top-2 right-2 w-6 h-6 bg-white/30 rounded-full flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}

          <!-- Slot Picker (filtres masqués car gérés par les boutons au-dessus) -->
          <BookingSlotPicker 
            {visibleSlotGroups}
            {canShowMoreSlots}
            {showAllSlots}
            {availabilityLoading}
            {availabilityError}
            {selectedDate}
            {selectedScheduleEntryId}
            selectedConsultationType={selectedConsultationType}
            hideFilters={true}
            onSlotSelect={selectSlot}
            onRefresh={() => onLoadSchedule(appointment.doctor_id, selectedConsultationType)}
            onToggleShowMore={() => showAllSlots = !showAllSlots}
          />
          
          <!-- Notes Input -->
          <div class="space-y-2">
            <label for="reschedule-notes" class="flex items-center gap-2 text-sm font-bold text-gray-900">
              <div class="w-6 h-6 bg-gradient-to-br from-purple-500 to-fuchsia-600 rounded-lg flex items-center justify-center">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </div>
              Notes pour le praticien
              <span class="text-gray-500 font-normal text-xs ml-auto">(optionnel)</span>
            </label>
            <textarea
              id="reschedule-notes"
              rows="4"
              bind:value={rescheduleNotes}
              class="w-full px-4 py-3.5 border-2 border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium resize-none bg-white hover:border-blue-400 shadow-sm placeholder-gray-400"
              placeholder="Raison du changement, nouvelles informations..."
            ></textarea>
          </div>
        </div>
        
        <!-- Footer -->
        <div class="px-4 sm:px-6 md:px-8 py-4 sm:py-5 md:py-6 border-t-2 border-gray-200 flex flex-col sm:flex-row gap-3 sm:gap-4 bg-gradient-to-r from-blue-50/30 via-indigo-50/30 to-purple-50/30">
          <button
            on:click={onClose}
            class="w-full sm:flex-1 px-4 sm:px-6 py-3 sm:py-4 border-2 border-gray-300 text-gray-700 font-bold rounded-xl sm:rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md touch-target"
            disabled={submitting}
          >
            <span class="flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Annuler
            </span>
          </button>
          <button
            on:click={handleSubmit}
            class="group relative w-full sm:flex-[2] px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-black shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all overflow-hidden transform hover:scale-105 active:scale-95 touch-target"
            disabled={submitting || !selectedDate}
          >
            <div class="absolute inset-0 z-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 opacity-90"></div>
            <div class="absolute inset-0 z-0 bg-white/10"></div>
            <div class="absolute inset-0 z-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>

            <span class="relative z-10 flex items-center justify-center gap-3 text-white drop-shadow-lg">
              {#if submitting}
                <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Validation...
              {:else}
                <div class="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <span class="text-lg">Replanifier</span>
              {/if}
            </span>
          </button>
        </div>
      {:else}
        <!-- Écran de confirmation -->
        <!-- Enhanced Header -->
        <div class="relative overflow-hidden bg-gradient-to-br from-green-600 via-emerald-600 to-teal-700 p-8">
          <div class="absolute inset-0 bg-grid-white/10"></div>
          <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
          <div class="relative flex items-center gap-4">
            <div class="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center shadow-2xl border-4 border-white/30">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 class="text-2xl font-black text-white drop-shadow-lg">Confirmer la modification</h3>
              <p class="text-white/90 font-medium">Vérifiez les informations</p>
            </div>
          </div>
        </div>
        
        <!-- Content -->
        <div class="p-8 space-y-6">
          <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-blue-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <div class="flex-1">
                <h4 class="text-sm font-bold text-blue-700 uppercase tracking-wide mb-2">Rendez-vous actuel</h4>
                <p class="text-gray-700 font-semibold">{formatAppointmentLabel(appointment)}</p>
              </div>
            </div>
          </div>
          
          <div class="flex items-center justify-center">
            <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg animate-bounce">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
              </svg>
            </div>
          </div>
          
          <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-300">
            <div class="flex items-start gap-4">
              <div class="w-12 h-12 bg-green-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="flex-1">
                <h4 class="text-sm font-bold text-green-700 uppercase tracking-wide mb-2">Nouvelle date</h4>
                <p class="text-2xl font-black text-gray-900">{new Date(selectedDate).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
                <p class="text-xl font-bold text-green-600 mt-1">{new Date(selectedDate).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</p>
                
                <!-- Type de consultation badge -->
                <div class="mt-3 inline-flex items-center gap-2 px-4 py-2 bg-white rounded-xl border-2 border-green-300 shadow-sm">
                  {#if selectedConsultationType === 'in_person'}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                    </svg>
                  {:else}
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                    </svg>
                  {/if}
                  <span class="font-bold text-green-700">
                    {CONSULTATION_LABELS[selectedConsultationType]}
                  </span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-5 border-2 border-amber-200">
            <div class="flex items-start gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-sm text-amber-900 font-semibold">Le praticien sera notifié de ce changement par email</p>
            </div>
          </div>
          
          <p class="text-center text-gray-600 font-semibold">Confirmez-vous cette modification ?</p>
        </div>
        
        <!-- Footer -->
        <div class="px-4 sm:px-6 md:px-8 py-4 sm:py-5 md:py-6 border-t-2 border-gray-200 flex flex-col sm:flex-row gap-3 sm:gap-4 bg-gradient-to-r from-green-50/30 via-emerald-50/30 to-teal-50/30">
          <button
            class="w-full sm:flex-1 px-4 sm:px-6 py-3 sm:py-4 border-2 border-gray-300 text-gray-700 font-bold rounded-xl sm:rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md touch-target"
            on:click={onBack}
          >
            <span class="flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Retour
            </span>
          </button>
          <button
            class="group relative w-full sm:flex-[2] px-4 sm:px-6 py-3 sm:py-4 rounded-xl sm:rounded-2xl font-black shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all overflow-hidden transform hover:scale-105 active:scale-95 touch-target"
            on:click={onConfirm}
            disabled={submitting}
          >
            <div class="absolute inset-0 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-700 opacity-90"></div>
            <div class="absolute inset-0 bg-white/10"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
              {#if submitting}
                <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Modification...
              {:else}
                <div class="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <span class="text-lg">Confirmer la modification</span>
              {/if}
            </span>
          </button>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .bg-grid-white\/10 {
    background-image: linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px),
                      linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px);
    background-size: 20px 20px;
  }
</style>
