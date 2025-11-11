<script lang="ts">
  import type { DoctorSearchResult } from '../../lib/api-patient';
  import { formatSpecialty, CONSULTATION_LABELS } from '../../lib/utils/formatting';

  export let doctor: DoctorSearchResult;
</script>

<div class="bg-gray-50 border border-gray-200 rounded-lg p-4">
  <div class="flex items-center gap-3">
    <!-- Doctor Avatar -->
    <div class="w-12 h-12 bg-violet-600 rounded-lg flex items-center justify-center text-white text-lg font-bold flex-shrink-0">
      {doctor.first_name[0]}{doctor.last_name[0]}
    </div>
    
    <!-- Doctor Info -->
    <div class="flex-1 min-w-0">
      <h4 class="text-lg font-bold text-gray-900 truncate">Dr {doctor.first_name} {doctor.last_name}</h4>
      <p class="text-sm text-gray-600">{formatSpecialty(doctor.specialty)}</p>
      <p class="text-sm text-gray-500">{doctor.city ?? 'Ville non renseignée'} • {doctor.consultation_duration} min</p>
    </div>
  </div>
</div>
