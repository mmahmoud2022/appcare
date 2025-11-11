<script lang="ts">
  import type { PatientAppointment } from '../../lib/api-patient';
  import { formatAppointmentDate, formatShortDate, formatTime } from '../../lib/utils/dates';
  import { CONSULTATION_LABELS } from '../../lib/utils/formatting';
  import { createEventDispatcher } from 'svelte';

  export let appointment: PatientAppointment;
  export let hoveredId: number | null = null;

  const dispatch = createEventDispatcher<{
    reschedule: PatientAppointment;
    cancel: PatientAppointment;
  }>();

  $: isHovered = hoveredId === appointment.id;
</script>

<div
  class="group relative perspective-1000"
  role="article"
  on:mouseenter={() => hoveredId = appointment.id}
  on:mouseleave={() => hoveredId = null}
>
  <!-- 3D Card Effect -->
  <div class={`relative transform transition-all duration-500 preserve-3d ${isHovered ? 'rotate-y-5 scale-105' : ''}`}>
    <!-- Glow effect -->
    <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl blur opacity-25 group-hover:opacity-75 transition-opacity duration-500"></div>
    
    <!-- Main Card -->
    <div class="relative bg-white rounded-3xl p-8 shadow-2xl border-2 border-gray-100 overflow-hidden">
      <!-- Animated background pattern -->
      <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 group-hover:scale-150 transition-transform duration-1000"></div>
      
      <!-- Status badge -->
      <div class="absolute top-6 right-6">
        <div class={`relative px-4 py-2 rounded-full font-bold text-sm shadow-lg transform transition-transform duration-300 ${
          appointment.status === 'confirmed' 
            ? 'bg-gradient-to-r from-green-400 to-emerald-600 text-white group-hover:scale-110' 
            : 'bg-gradient-to-r from-blue-400 to-indigo-600 text-white group-hover:scale-110'
        }`}>
          <div class="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
          <span class="relative">
            {appointment.status === 'confirmed' ? '✓ Confirmé' : '⏱ En attente'}
          </span>
        </div>
      </div>
      
      <div class="relative z-10">
        <!-- Doctor info -->
        <div class="flex items-start gap-4 mb-6">
          <div class="w-16 h-16 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-xl font-black shadow-xl transform group-hover:rotate-12 transition-transform duration-500">
            {appointment.doctor_first_name?.[0]}{appointment.doctor_last_name?.[0]}
          </div>
          <div class="flex-1">
            <h4 class="text-xl font-black text-gray-900 group-hover:text-violet-600 transition-colors">
              Dr. {appointment.doctor_first_name} {appointment.doctor_last_name}
            </h4>
            <div class="flex items-center gap-2 mt-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-lg font-bold text-gray-900">
                {new Date(appointment.appointment_date).toLocaleDateString('fr-FR', { 
                  weekday: 'long', 
                  day: 'numeric', 
                  month: 'long',
                  year: 'numeric'
                })}
              </span>
            </div>
            <div class="flex items-center gap-2 mt-1">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-fuchsia-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-2xl font-black bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
                {formatTime(new Date(appointment.appointment_date))}
              </span>
            </div>
          </div>
        </div>

        <!-- Consultation type -->
        <div class="mb-6">
          <div class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border-2 border-indigo-200">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span class="font-bold text-indigo-700">
              {CONSULTATION_LABELS[appointment.consultation_type]}
            </span>
          </div>
        </div>

        {#if appointment.reason}
          <div class="mb-6 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border-2 border-amber-200">
            <div class="flex items-start gap-3">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <div>
                <p class="text-xs font-bold text-amber-700 uppercase tracking-wide">Motif</p>
                <p class="text-sm text-amber-900 font-semibold mt-1">{appointment.reason}</p>
              </div>
            </div>
          </div>
        {/if}

        <!-- Action buttons -->
        <div class="flex gap-3">
          <button
            on:click={() => dispatch('reschedule', appointment)}
            class="group/btn flex-1 relative overflow-hidden px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all transform hover:scale-105 active:scale-95"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-700 opacity-0 group-hover/btn:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Replanifier
            </span>
          </button>
          <button
            on:click={() => dispatch('cancel', appointment)}
            class="group/btn flex-1 relative overflow-hidden px-6 py-4 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all transform hover:scale-105 active:scale-95"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-red-600 to-pink-700 opacity-0 group-hover/btn:opacity-100 transition-opacity"></div>
            <span class="relative flex items-center justify-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
              Annuler
            </span>
          </button>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .perspective-1000 {
    perspective: 1000px;
  }
  
  .preserve-3d {
    transform-style: preserve-3d;
  }
  
  .rotate-y-5 {
    transform: rotateY(5deg);
  }
</style>
