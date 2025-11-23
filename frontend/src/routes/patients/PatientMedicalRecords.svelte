<script lang="ts">
  import { onMount } from 'svelte';
  import { fade, fly, scale, blur } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { elasticOut, cubicOut } from 'svelte/easing';
  import { getPatientMedicalRecords, type PatientMedicalRecord, type PatientAppointment } from '../../lib/api-patient';

  let loading = true;
  let error: string | null = null;
  let record: PatientMedicalRecord | null = null;
  let activeTab: 'appointments' | 'documents' | 'prescriptions' = 'appointments';
  let hoveredAppointment: number | null = null;

  onMount(async () => {
    await loadRecord();
  });

  const loadRecord = async () => {
    loading = true;
    error = null;
    try {
      record = await getPatientMedicalRecords();
    } catch (err: any) {
      console.error('Erreur lors du chargement du dossier médical:', err);
      error = "Impossible de charger votre dossier médical";
    } finally {
      loading = false;
    }
  };

  const formatDate = (value: string) => {
    return new Date(value).toLocaleString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const doctorName = (appointment: PatientAppointment) => {
    const parts = [appointment.doctor_first_name, appointment.doctor_last_name].filter(Boolean);
    return parts.length ? `Dr ${parts.join(' ')}` : 'Médecin';
  };

  const downloadDocument = async (documentId: number, fileName: string) => {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        alert('Session expirée. Veuillez vous reconnecter.');
        return;
      }

      const response = await fetch(`/api/v1/patients/documents/${documentId}/download`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        if (response.status === 401) {
          alert('Session expirée. Veuillez vous reconnecter.');
          return;
        }
        throw new Error('Erreur lors du téléchargement');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Erreur téléchargement:', err);
      alert('Impossible de télécharger le document');
    }
  };
</script>

<div class="space-y-8 relative">
  <!-- Ultra Modern Header -->
  <div class="relative overflow-hidden bg-gradient-to-br from-teal-600 via-cyan-600 to-blue-600 rounded-[2rem] shadow-2xl p-1">
    <div class="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]"></div>
    <div class="absolute top-0 left-0 w-72 h-72 bg-white/20 rounded-full blur-3xl -ml-36 -mt-36 animate-blob"></div>
    <div class="absolute bottom-0 right-0 w-72 h-72 bg-emerald-300/20 rounded-full blur-3xl -mr-36 -mb-36 animate-blob animation-delay-2000"></div>
    
    <div class="relative bg-white/10 backdrop-blur-2xl rounded-2xl sm:rounded-[1.75rem] p-4 sm:p-6 md:p-8 border border-white/20">
      <div class="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div class="flex items-center gap-3 sm:gap-6">
          <div class="relative flex-shrink-0">
            <div class="w-14 h-14 sm:w-20 sm:h-20 bg-gradient-to-br from-white/40 to-white/20 rounded-2xl sm:rounded-3xl flex items-center justify-center backdrop-blur-sm border-2 border-white/30 shadow-2xl transform hover:rotate-12 transition-transform duration-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 sm:h-10 sm:w-10 text-white drop-shadow-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
          </div>
          <div class="min-w-0">
            <h2 class="text-2xl sm:text-3xl md:text-4xl font-black text-white drop-shadow-lg mb-1 sm:mb-2 tracking-tight">Dossier Médical</h2>
            <p class="text-sm sm:text-base md:text-lg text-white/90 font-medium hide-mobile">Vos archives de santé centralisées</p>
          </div>
        </div>
        <button
          on:click={loadRecord}
          class="group relative w-full sm:w-auto px-4 sm:px-6 py-2.5 sm:py-3 bg-white text-teal-600 rounded-xl sm:rounded-2xl hover:bg-white/90 transition-all shadow-2xl hover:shadow-3xl font-bold text-sm sm:text-base overflow-hidden transform active:scale-95 sm:hover:scale-105 touch-target"
          disabled={loading}
        >
          <div class="absolute inset-0 bg-gradient-to-r from-teal-600/20 to-cyan-600/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="{loading ? 'animate-spin' : ''} h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Actualiser
          </div>
        </button>
      </div>
    </div>
  </div>

  <!-- Modern Tabs -->
  <div class="bg-white/80 backdrop-blur-xl rounded-2xl sm:rounded-3xl shadow-xl border-2 border-gray-100 p-1 sm:p-2 overflow-x-auto">
    <div class="flex gap-1 sm:gap-2 min-w-max">
      <button
        on:click={() => activeTab = 'appointments'}
        class={`flex-1 min-w-[120px] px-3 sm:px-4 md:px-6 py-2.5 sm:py-3 md:py-4 rounded-xl sm:rounded-2xl font-bold text-xs sm:text-sm md:text-base transition-all duration-300 touch-target ${
          activeTab === 'appointments' 
            ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg transform sm:scale-105' 
            : 'text-gray-600 hover:bg-gray-50'
        }`}
      >
        <div class="flex items-center justify-center gap-1.5 sm:gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 sm:h-5 sm:w-5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span class="whitespace-nowrap">Rendez-vous</span>
        </div>
      </button>
      <button
        on:click={() => activeTab = 'documents'}
        class={`flex-1 px-6 py-4 rounded-2xl font-bold text-base transition-all duration-300 ${
          activeTab === 'documents' 
            ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg transform scale-105' 
            : 'text-gray-600 hover:bg-gray-50'
        }`}
      >
        <div class="flex items-center justify-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          Documents
        </div>
      </button>
      <button
        on:click={() => activeTab = 'prescriptions'}
        class={`flex-1 px-6 py-4 rounded-2xl font-bold text-base transition-all duration-300 ${
          activeTab === 'prescriptions' 
            ? 'bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg transform scale-105' 
            : 'text-gray-600 hover:bg-gray-50'
        }`}
      >
        <div class="flex items-center justify-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          Ordonnances
        </div>
      </button>
    </div>
  </div>

  <!-- Content Area with Timeline Design -->
  <div class="min-h-[500px]">
    {#if loading}
      <div class="flex items-center justify-center py-24" transition:fade={{ duration: 300 }}>
        <div class="relative">
          <div class="w-32 h-32 border-8 border-teal-200 border-t-teal-600 rounded-full animate-spin"></div>
          <div class="absolute inset-0 w-32 h-32 border-8 border-cyan-200 border-t-cyan-600 rounded-full animate-spin animation-delay-150" style="animation-direction: reverse;"></div>
          <div class="absolute inset-0 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-teal-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
        </div>
      </div>
    {:else if error}
      <div 
        class="bg-gradient-to-br from-red-50 to-pink-50 border-l-4 border-red-500 rounded-2xl p-6 shadow-xl"
        transition:fly={{ x: -20, duration: 400 }}
      >
        <div class="flex items-start gap-4">
          <div class="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 class="font-bold text-red-900 text-lg">Erreur de chargement</h3>
            <p class="text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    {:else if record}
      {#if activeTab === 'appointments'}
        {#if record.appointments.length}
          <!-- Timeline Layout with 3D Cards -->
          <div class="relative">
            <!-- Timeline line -->
            <div class="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-teal-400 via-cyan-400 to-blue-400 rounded-full shadow-lg"></div>
            
            <div class="space-y-8">
              {#each record.appointments as appointment, i (appointment.id)}
                <div
                  class="relative pl-20"
                  transition:fly={{ x: -30, duration: 500, delay: i * 100 }}
                  animate:flip={{ duration: 400 }}
                  on:mouseenter={() => hoveredAppointment = appointment.id}
                  on:mouseleave={() => hoveredAppointment = null}
                  role="article"
                >
                  <!-- Timeline dot -->
                  <div class="absolute left-0 top-8 w-16 h-16 flex items-center justify-center">
                    <div class={`w-14 h-14 rounded-full flex items-center justify-center shadow-xl transform transition-all duration-500 ${
                      appointment.status === 'completed' ? 'bg-gradient-to-br from-green-400 to-emerald-600 scale-100' :
                      appointment.status === 'pending' ? 'bg-gradient-to-br from-blue-400 to-indigo-600 scale-100' :
                      appointment.status === 'cancelled' ? 'bg-gradient-to-br from-red-400 to-rose-600 scale-90' :
                      'bg-gradient-to-br from-yellow-400 to-orange-600 scale-95'
                    } ${hoveredAppointment === appointment.id ? 'scale-110 rotate-12' : ''}`}>
                      <span class="text-2xl">
                        {appointment.status === 'completed' ? '✓' : 
                         appointment.status === 'pending' ? '⏱' :
                         appointment.status === 'cancelled' ? '✗' : '📅'}
                      </span>
                    </div>
                    <!-- Pulse effect for pending -->
                    {#if appointment.status === 'pending'}
                      <div class="absolute inset-0 w-14 h-14 rounded-full bg-blue-400 animate-ping opacity-30"></div>
                    {/if}
                  </div>
                  
                  <!-- 3D Card -->
                  <div class="group perspective-1000">
                    <div class={`relative transform transition-all duration-500 ${
                      hoveredAppointment === appointment.id ? 'scale-105 -translate-y-2' : ''
                    }`}>
                      <!-- Glow effect -->
                      <div class="absolute -inset-1 bg-gradient-to-r from-teal-600 via-cyan-600 to-blue-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
                      
                      <!-- Main card -->
                      <div class="relative bg-white rounded-3xl p-6 shadow-xl border-2 border-gray-100 overflow-hidden">
                        <!-- Animated background pattern -->
                        <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-teal-50 to-cyan-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 group-hover:scale-150 transition-transform duration-1000"></div>
                        
                        <!-- Content -->
                        <div class="relative z-10">
                          <div class="flex items-start justify-between mb-4">
                            <div class="flex-1">
                              <!-- Doctor info -->
                              <div class="flex items-center gap-4 mb-3">
                                <div class="w-16 h-16 bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl flex items-center justify-center text-white text-xl font-black shadow-lg transform group-hover:rotate-6 transition-transform duration-500">
                                  {appointment.doctor_first_name?.[0]}{appointment.doctor_last_name?.[0]}
                                </div>
                                <div>
                                  <h3 class="text-xl font-black text-gray-900 group-hover:text-teal-600 transition-colors">
                                    {doctorName(appointment)}
                                  </h3>
                                  <div class="flex items-center gap-2 mt-1 text-sm text-gray-600">
                                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                    </svg>
                                    <span class="font-medium">{formatDate(appointment.appointment_date)}</span>
                                  </div>
                                </div>
                              </div>
                              
                              <!-- Consultation type badge -->
                              <div class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border-2 border-indigo-200 mb-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                <span class="font-semibold text-indigo-700 text-sm">
                                  {appointment.consultation_type === 'teleconsultation' ? 'Téléconsultation' : 'Consultation en cabinet'}
                                </span>
                              </div>
                            </div>
                            
                            <!-- Status badge -->
                            <div class={`px-4 py-2 rounded-full font-semibold text-sm shadow-lg border-2 uppercase tracking-wide ${
                              appointment.status === 'completed' 
                                ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-300' 
                                : appointment.status === 'pending'
                                ? 'bg-gradient-to-r from-blue-100 to-indigo-100 text-blue-700 border-blue-300'
                                : appointment.status === 'cancelled'
                                ? 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border-red-300'
                                : 'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-700 border-yellow-300'
                            }`}>
                              {appointment.status}
                            </div>
                          </div>
                          
                          <!-- Notes sections -->
                          {#if appointment.doctor_notes}
                            <div class="mb-4 p-4 bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl border-2 border-green-200">
                              <div class="flex items-start gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <div class="flex-1">
                                  <p class="text-xs font-medium text-green-700 uppercase tracking-wide mb-1">Notes du praticien</p>
                                  <p class="text-sm text-green-900 font-medium">{appointment.doctor_notes}</p>
                                </div>
                              </div>
                            </div>
                          {/if}
                          
                          {#if appointment.patient_notes}
                            <div class="p-4 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border-2 border-blue-200">
                              <div class="flex items-start gap-3">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                                </svg>
                                <div class="flex-1">
                                  <p class="text-xs font-medium text-blue-700 uppercase tracking-wide mb-1">Vos notes</p>
                                  <p class="text-sm text-blue-900 font-medium">{appointment.patient_notes}</p>
                                </div>
                              </div>
                            </div>
                          {/if}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div 
            class="relative overflow-hidden bg-gradient-to-br from-gray-50 via-teal-50 to-cyan-50 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
            transition:scale={{ duration: 400, easing: elasticOut }}
          >
            <div class="absolute top-0 left-0 w-full h-full opacity-30">
              <div class="absolute top-10 left-10 w-20 h-20 bg-teal-400 rounded-full blur-xl animate-blob"></div>
              <div class="absolute top-20 right-10 w-32 h-32 bg-cyan-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
              <div class="absolute bottom-10 left-1/2 w-24 h-24 bg-blue-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
            </div>
            <div class="relative z-10">
              <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 class="text-2xl sm:text-3xl font-black text-gray-900 mb-3">Aucun rendez-vous enregistré</h3>
              <p class="text-lg text-gray-600">Vos consultations futures et passées apparaîtront ici</p>
            </div>
          </div>
        {/if}
      {:else if activeTab === 'documents'}
        {#if record.documents.length}
          <!-- Document Cards Grid with Flip Effect -->
          <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {#each record.documents as document, i (document.id)}
              <div
                class="group perspective-1000"
                transition:fly={{ y: 20, duration: 400, delay: i * 80 }}
                animate:flip={{ duration: 400 }}
              >
                <div class="relative transform transition-all duration-500 hover:scale-105">
                  <!-- Glow effect -->
                  <div class="absolute -inset-1 bg-gradient-to-r from-purple-600 via-pink-600 to-red-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
                  
                  <!-- Document Card -->
                  <div class="relative bg-white rounded-3xl p-6 shadow-xl border-2 border-gray-100 overflow-hidden min-h-[200px] flex flex-col">
                    <!-- Background pattern -->
                    <div class="absolute top-0 right-0 w-48 h-48 bg-gradient-to-br from-purple-50 to-pink-50 rounded-full blur-3xl -mr-24 -mt-24 opacity-50 group-hover:scale-150 transition-transform duration-1000"></div>
                    
                    <!-- Content -->
                    <div class="relative z-10 flex-1 flex flex-col">
                      <!-- Icon -->
                      <div class="mb-4">
                        <div class="w-16 h-16 bg-gradient-to-br from-purple-500 to-pink-600 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:rotate-12 transition-transform duration-500">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                          </svg>
                        </div>
                      </div>
                      
                      <!-- Title -->
                      <h3 class="text-lg font-black text-gray-900 mb-2 group-hover:text-purple-600 transition-colors line-clamp-2">
                        {document.title}
                      </h3>
                      
                      <!-- Type badge -->
                      <div class="inline-flex items-center gap-2 px-3 py-1.5 bg-gradient-to-r from-purple-100 to-pink-100 rounded-lg border border-purple-200 mb-3 self-start">
                        <span class="font-bold text-purple-700 text-xs uppercase tracking-wide">
                          {document.document_type ?? 'Document'}
                        </span>
                      </div>
                      
                      <!-- Description -->
                      {#if document.description}
                        <p class="text-sm text-gray-600 mb-4 line-clamp-2 flex-1">{document.description}</p>
                      {:else}
                        <div class="flex-1"></div>
                      {/if}
                      
                      <!-- Footer -->
                      <div class="flex items-center justify-between pt-4 border-t border-gray-100">
                        <div class="text-xs text-gray-500">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                          {new Date(document.created_at || document.uploaded_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', year: 'numeric' })}
                        </div>
                        <div class="flex items-center gap-2">
                          <div class="text-xs font-medium text-gray-700 bg-gray-100 px-3 py-1.5 rounded-lg">
                            {Math.round((document.file_size ?? 0) / 1024)} KB
                          </div>
                          <button
                            on:click={() => downloadDocument(document.id, document.file_name)}
                            class="group/btn relative px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all shadow-lg hover:shadow-xl font-bold overflow-hidden transform hover:scale-105 active:scale-95"
                          >
                            <div class="absolute inset-0 bg-gradient-to-r from-white/20 to-white/0 opacity-0 group-hover/btn:opacity-100 transition-opacity"></div>
                            <div class="relative flex items-center gap-2">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                              </svg>
                              <span class="text-xs">Télécharger</span>
                            </div>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div 
            class="relative overflow-hidden bg-gradient-to-br from-gray-50 via-purple-50 to-pink-50 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
            transition:scale={{ duration: 400, easing: elasticOut }}
          >
            <div class="absolute top-0 left-0 w-full h-full opacity-30">
              <div class="absolute top-10 left-10 w-20 h-20 bg-purple-400 rounded-full blur-xl animate-blob"></div>
              <div class="absolute top-20 right-10 w-32 h-32 bg-pink-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
              <div class="absolute bottom-10 left-1/2 w-24 h-24 bg-red-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
            </div>
            <div class="relative z-10">
              <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 class="text-2xl sm:text-3xl font-black text-gray-900 mb-3">Aucun document disponible</h3>
              <p class="text-lg text-gray-600">Vos documents médicaux seront stockés ici de manière sécurisée</p>
            </div>
          </div>
        {/if}
      {:else if activeTab === 'prescriptions'}
        {#if record.prescriptions.length}
          <!-- Prescription Cards -->
          <div class="space-y-6">
            {#each record.prescriptions as prescription, i (prescription.id)}
              <div
                class="group"
                transition:fly={{ y: 20, duration: 400, delay: i * 100 }}
                animate:flip={{ duration: 400 }}
              >
                <div class="relative">
                  <!-- Glow effect -->
                  <div class="absolute -inset-1 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 rounded-3xl blur opacity-20 group-hover:opacity-40 transition-opacity duration-500"></div>
                  
                  <!-- Prescription Card -->
                  <div class="relative bg-white rounded-3xl p-8 shadow-xl border-2 border-gray-100 overflow-hidden">
                    <!-- Background pattern -->
                    <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-green-50 to-emerald-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 group-hover:scale-150 transition-transform duration-1000"></div>
                    
                    <!-- Content -->
                    <div class="relative z-10">
                      <!-- Header -->
                      <div class="flex items-start justify-between mb-6">
                        <div class="flex items-center gap-4">
                          <div class="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-2xl flex items-center justify-center shadow-lg transform group-hover:rotate-6 transition-transform duration-500">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                          </div>
                          <div>
                            <h3 class="text-2xl font-black text-gray-900 group-hover:text-green-600 transition-colors">
                              Ordonnance #{prescription.prescription_number}
                            </h3>
                            <div class="flex items-center gap-2 mt-2 text-sm text-gray-600">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              <span class="font-semibold">Émise le {new Date(prescription.issued_at || prescription.prescription_date).toLocaleDateString('fr-FR', { day: 'numeric', month: 'long', year: 'numeric' })}</span>
                            </div>
                          </div>
                        </div>
                        
                        <!-- Status badge -->
                        <div class={`px-5 py-2.5 rounded-full font-semibold text-sm shadow-lg border-2 uppercase tracking-wide ${
                          prescription.status === 'issued' 
                            ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-300' 
                            : 'bg-gradient-to-r from-gray-100 to-slate-100 text-gray-700 border-gray-300'
                        }`}>
                          {prescription.status === 'issued' ? '✓ Émise' : prescription.status}
                        </div>
                      </div>
                      
                      <!-- Medications list -->
                      <div class="space-y-4 mb-6">
                        <h4 class="text-lg font-semibold text-gray-900 flex items-center gap-2">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                          </svg>
                          Médicaments prescrits ({prescription.medications.length})
                        </h4>
                        
                        {#each prescription.medications as medication, index}
                          <div class="relative">
                            <!-- Medication card -->
                            <div class="bg-gradient-to-br from-gray-50 to-green-50/30 border-2 border-green-200 rounded-2xl p-5 hover:shadow-lg transition-shadow">
                              <div class="flex items-start gap-4">
                                <!-- Number badge -->
                                <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center flex-shrink-0 shadow-md">
                                  <span class="text-white text-lg font-black">{index + 1}</span>
                                </div>
                                
                                <!-- Medication details -->
                                <div class="flex-1">
                                  <h5 class="text-lg font-black text-gray-900 mb-3">{medication.name}</h5>
                                  
                                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                                    {#if medication.dosage}
                                      <div class="flex items-start gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                                        </svg>
                                        <div>
                                          <p class="text-xs font-medium text-green-700 uppercase tracking-wide">Posologie</p>
                                          <p class="text-sm text-gray-900 font-medium">{medication.dosage}</p>
                                        </div>
                                      </div>
                                    {/if}
                                    
                                    {#if medication.frequency}
                                      <div class="flex items-start gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                        </svg>
                                        <div>
                                          <p class="text-xs font-medium text-green-700 uppercase tracking-wide">Fréquence</p>
                                          <p class="text-sm text-gray-900 font-medium">{medication.frequency}</p>
                                        </div>
                                      </div>
                                    {/if}
                                    
                                    {#if medication.duration}
                                      <div class="flex items-start gap-2">
                                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-green-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                        </svg>
                                        <div>
                                          <p class="text-xs font-medium text-green-700 uppercase tracking-wide">Durée</p>
                                          <p class="text-sm text-gray-900 font-medium">{medication.duration}</p>
                                        </div>
                                      </div>
                                    {/if}
                                  </div>
                                  
                                  {#if medication.notes}
                                    <div class="mt-3 p-3 bg-amber-50 border border-amber-200 rounded-xl">
                                      <p class="text-xs font-medium text-amber-700 uppercase tracking-wide mb-1">Notes importantes</p>
                                      <p class="text-sm text-amber-900 font-medium">{medication.notes}</p>
                                    </div>
                                  {/if}
                                </div>
                              </div>
                            </div>
                          </div>
                        {/each}
                      </div>
                      
                      <!-- Instructions -->
                      {#if prescription.instructions}
                        <div class="p-5 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl border-2 border-blue-200">
                          <div class="flex items-start gap-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <div class="flex-1">
                              <p class="text-sm font-medium text-blue-700 uppercase tracking-wide mb-2">Instructions du médecin</p>
                              <p class="text-base text-blue-900 font-medium leading-relaxed">{prescription.instructions}</p>
                            </div>
                          </div>
                        </div>
                      {/if}
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div 
            class="relative overflow-hidden bg-gradient-to-br from-gray-50 via-green-50 to-emerald-50 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
            transition:scale={{ duration: 400, easing: elasticOut }}
          >
            <div class="absolute top-0 left-0 w-full h-full opacity-30">
              <div class="absolute top-10 left-10 w-20 h-20 bg-green-400 rounded-full blur-xl animate-blob"></div>
              <div class="absolute top-20 right-10 w-32 h-32 bg-emerald-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
              <div class="absolute bottom-10 left-1/2 w-24 h-24 bg-teal-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
            </div>
            <div class="relative z-10">
              <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 class="text-2xl sm:text-3xl font-black text-gray-900 mb-3">Aucune ordonnance disponible</h3>
              <p class="text-lg text-gray-600">Vos prescriptions médicales seront accessibles ici</p>
            </div>
          </div>
        {/if}
      {/if}
    {:else}
      <div 
        class="relative overflow-hidden bg-gradient-to-br from-gray-50 to-gray-100 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
        transition:scale={{ duration: 400 }}
      >
        <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 class="text-2xl sm:text-3xl font-black text-gray-700 mb-3">Aucune donnée disponible</h3>
        <p class="text-lg text-gray-600">Votre dossier médical sera accessible ici</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .perspective-1000 {
    perspective: 1000px;
  }
  
  @keyframes blob {
    0%, 100% {
      transform: translate(0, 0) scale(1);
    }
    33% {
      transform: translate(30px, -50px) scale(1.1);
    }
    66% {
      transform: translate(-20px, 20px) scale(0.9);
    }
  }
  
  .animate-blob {
    animation: blob 7s infinite;
  }
  
  .animation-delay-2000 {
    animation-delay: 2s;
  }
  
  .animation-delay-4000 {
    animation-delay: 4s;
  }
  
  .animation-delay-150 {
    animation-delay: 150ms;
  }
  
  .line-clamp-2 {
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
</style>
