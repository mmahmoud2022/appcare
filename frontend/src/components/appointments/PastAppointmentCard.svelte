<script lang="ts">
  import type { PatientAppointment } from '../../lib/api-patient';
  import { formatShortDate, formatTime } from '../../lib/utils/dates';
  import { CONSULTATION_LABELS } from '../../lib/utils/formatting';

  export let appointment: PatientAppointment;
</script>

<div class="relative pl-20">
  <!-- Timeline dot -->
  <div class="absolute left-0 top-6 w-16 h-16 flex items-center justify-center">
    <div class={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg ${
      appointment.status === 'completed' ? 'bg-gradient-to-br from-green-400 to-emerald-600' :
      appointment.status === 'cancelled' ? 'bg-gradient-to-br from-red-400 to-rose-600' :
      'bg-gradient-to-br from-yellow-400 to-orange-600'
    }`}>
      <span class="text-2xl">
        {appointment.status === 'completed' ? '✓' : appointment.status === 'cancelled' ? '✗' : '⊘'}
      </span>
    </div>
  </div>
  
  <!-- Card -->
  <div class="group relative">
    <!-- Glass effect -->
    <div class="absolute inset-0 bg-white/40 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl"></div>
    <div class="absolute inset-0 bg-gradient-to-br from-white/60 to-white/30 rounded-3xl"></div>
    
    <!-- Content -->
    <div class="relative bg-white/80 backdrop-blur-sm rounded-3xl p-6 border-2 border-gray-100 hover:border-gray-200 transition-all">
      <div class="flex items-start justify-between mb-4">
        <div class="flex-1">
          <!-- Doctor info -->
          <div class="flex items-center gap-3 mb-3">
            <div class="w-12 h-12 bg-gradient-to-br from-slate-400 to-gray-600 rounded-xl flex items-center justify-center text-white text-sm font-black shadow-md">
              {appointment.doctor_first_name?.[0]}{appointment.doctor_last_name?.[0]}
            </div>
            <div>
              <h4 class="text-lg font-black text-gray-900">
                Dr. {appointment.doctor_first_name} {appointment.doctor_last_name}
              </h4>
              <p class="text-sm text-gray-600 font-semibold capitalize flex items-center gap-1.5">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                </svg>
                {CONSULTATION_LABELS[appointment.consultation_type]}
              </p>
            </div>
          </div>
          
          <!-- Date and time -->
          <div class="flex items-center gap-4 text-sm text-gray-700 mb-3">
            <span class="flex items-center gap-1.5 font-bold">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              {formatShortDate(new Date(appointment.appointment_date))}
            </span>
            <span class="flex items-center gap-1.5 font-bold">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {formatTime(new Date(appointment.appointment_date))}
            </span>
          </div>
          
          {#if appointment.reason}
            <div class="bg-gradient-to-r from-gray-50 to-slate-50 px-4 py-2 rounded-xl border border-gray-200">
              <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Motif</p>
              <p class="text-sm text-gray-800 font-semibold">{appointment.reason}</p>
            </div>
          {/if}
        </div>
        
        <!-- Status badge -->
        <div class="relative">
          <div class={`px-4 py-2 rounded-full font-bold text-sm shadow-lg border-2 ${
            appointment.status === 'completed' 
              ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-300' 
              : appointment.status === 'cancelled'
              ? 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border-red-300'
              : 'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-700 border-yellow-300'
          }`}>
            {
              appointment.status === 'completed' ? '✓ Complété' :
              appointment.status === 'cancelled' ? '✗ Annulé' :
              '⊘ Non présenté'
            }
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
