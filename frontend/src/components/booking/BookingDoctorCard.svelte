<script lang="ts">
  import type { DoctorSearchResult } from '../../lib/api-patient';
  import { formatSpecialty, CONSULTATION_LABELS } from '../../lib/utils/formatting';

  export let doctor: DoctorSearchResult;
</script>

<div class="bg-gray-50 border border-gray-200 rounded-lg p-3 sm:p-4">
  <div class="flex items-center gap-2 sm:gap-3">
    <!-- Doctor Avatar -->
    <div class="w-10 h-10 sm:w-12 sm:h-12 bg-violet-600 rounded-lg flex items-center justify-center text-white text-base sm:text-lg font-bold flex-shrink-0">
      {doctor.first_name[0]}{doctor.last_name[0]}
    </div>
    
    <!-- Doctor Info -->
    <div class="flex-1 min-w-0">
      <div class="flex items-center justify-between gap-2 mb-1">
        <h4 class="text-base sm:text-lg font-bold text-gray-900 truncate">Dr {doctor.first_name} {doctor.last_name}</h4>
        
        <!-- Rating Badge -->
        <div class="flex items-center gap-1 px-1.5 sm:px-2 py-0.5 sm:py-1 bg-yellow-50 rounded-lg border border-yellow-200 flex-shrink-0">
          <span class="text-base sm:text-lg text-yellow-500">★</span>
          <span class="text-xs sm:text-sm font-bold text-gray-900">
            {doctor.average_rating ? doctor.average_rating.toFixed(1) : '0.0'}
          </span>
          <span class="text-xs text-gray-500">
            ({doctor.total_reviews || 0})
          </span>
        </div>
      </div>
      <p class="text-xs sm:text-sm text-gray-600 truncate">{formatSpecialty(doctor.specialty)}</p>
      <div class="flex items-center flex-wrap gap-1 sm:gap-2 text-xs sm:text-sm text-gray-500 mt-1">
        <span class="truncate max-w-[120px] sm:max-w-none">{doctor.city ?? 'Ville non renseignée'}</span>
        <span class="hidden sm:inline">•</span>
        <span>{doctor.consultation_duration} min</span>
        {#if doctor.consultation_price}
          <span class="hidden sm:inline">•</span>
          <span class="font-semibold text-green-600">{doctor.consultation_price.toLocaleString('fr-FR')} XOF</span>
        {/if}
      </div>
    </div>
  </div>
</div>
