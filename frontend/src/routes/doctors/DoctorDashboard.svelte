<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../../lib/router';
  import { 
    getCurrentDoctorProfile,
    getDoctorStatistics, 
    getDoctorAppointments,
    type DoctorProfile,
    type DoctorStatistics,
    type Appointment
  } from '../../lib/api-doctor';
  import { getCurrentUser } from '../../lib/api';
  import DoctorAppointments from './DoctorAppointments.svelte';
  import DoctorAvailability from './DoctorAvailability.svelte';
  import DoctorPatients from './DoctorPatients.svelte';
  import DoctorReviews from './DoctorReviews.svelte';
  import DoctorMessages from './DoctorMessages.svelte';
  import DoctorPayments from './DoctorPayments.svelte';
  import DoctorSettings from './DoctorSettings.svelte';
  import DoctorDocuments from './DoctorDocuments.svelte';
  
  let profile: DoctorProfile | null = null;
  let currentUser: any = null;
  let statistics: DoctorStatistics | null = null;
  let upcomingAppointments: Appointment[] = [];
  let loading = true;
  let activeTab: 'overview' | 'appointments' | 'availability' | 'patients' | 'reviews' | 'messages' | 'documents' | 'payments' | 'settings' = 'overview';
  let totalPatients = 0;
  let completionRate = '0.0';
  let showBanner = true;

  onMount(async () => {
    try {
      currentUser = await getCurrentUser();
      if (currentUser.role !== 'doctor' && currentUser.role !== 'DOCTOR') {
        navigate('/');
        return;
      }

      await loadDashboardData();
    } catch (err: any) {
      console.error('Error loading dashboard:', err);
    } finally {
      loading = false;
    }
  });

  const loadDashboardData = async () => {
    try {
      profile = await getCurrentDoctorProfile();
    } catch (err: any) {
      console.warn('Profile not loaded, user can complete it later:', err);
    }

    try {
      statistics = await getDoctorStatistics();
    } catch (err: any) {
      console.error('Error loading statistics:', err);
    }

    try {
      const appointmentsData = await getDoctorAppointments(1, 5, 'pending');
      upcomingAppointments = appointmentsData.items || [];
    } catch (err: any) {
      console.error('Error loading appointments:', err);
    }
  };

  const handleProfileUpdated = async () => {
    console.log('Profile updated, reloading dashboard data...');
    await loadDashboardData();
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR', {
      style: 'currency',
      currency: 'EUR'
    }).format(amount / 100);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending': return 'badge-warning';
      case 'confirmed': return 'badge-info';
      case 'completed': return 'badge-success';
      case 'cancelled': return 'badge-error';
      case 'no_show': return 'badge-secondary';
      default: return 'badge-neutral';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'En attente';
      case 'confirmed': return 'Confirmé';
      case 'completed': return 'Terminé';
      case 'cancelled': return 'Annulé';
      case 'no_show': return 'Absent';
      default: return status;
    }
  };

  $: totalPatients = statistics
    ? statistics.new_patients_count + statistics.returning_patients_count
    : 0;

  $: completionRate = statistics && statistics.total_consultations > 0
    ? ((statistics.completed_consultations / statistics.total_consultations) * 100).toFixed(1)
    : '0.0';
</script>

<div class="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
  <!-- Header with gradient -->
  <header class="sticky top-0 z-50 backdrop-blur-xl bg-white/80 shadow-lg border-b border-white/20">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4 animate-fade-in">
          <div class="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-500/30 animate-float">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 bg-clip-text text-transparent">
              Dashboard Médecin
            </h1>
            {#if currentUser}
              <p class="text-sm text-slate-600 font-medium">
                Dr. {currentUser.first_name} {currentUser.last_name}
              </p>
            {/if}
          </div>
        </div>
        <button 
          on:click={() => navigate('/')}
          class="group px-5 py-2.5 rounded-xl font-medium text-slate-700 hover:text-white bg-white hover:bg-gradient-to-r hover:from-red-500 hover:to-pink-500 border border-slate-200 hover:border-transparent transition-all duration-300 shadow-sm hover:shadow-lg hover:shadow-red-500/25 hover:scale-105"
        >
          <span class="flex items-center gap-2">
            Déconnexion
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </span>
        </button>
      </div>
    </div>
  </header>

  {#if loading}
    <div class="flex items-center justify-center h-96">
      <div class="text-center animate-fade-in">
        <div class="relative w-16 h-16 mx-auto mb-6">
          <div class="absolute inset-0 rounded-full border-4 border-indigo-200"></div>
          <div class="absolute inset-0 rounded-full border-4 border-indigo-600 border-t-transparent animate-spin"></div>
        </div>
        <p class="text-slate-600 font-medium">Chargement du dashboard...</p>
      </div>
    </div>
  {:else}
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in">
      <!-- Profile completion banner -->
      {#if !profile && showBanner}
        <div class="mb-6 relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-600 p-1 shadow-xl shadow-indigo-500/30 animate-slide-down">
          <div class="bg-white/95 backdrop-blur-sm rounded-xl p-5">
            <div class="flex items-start gap-4">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0 animate-pulse-soft">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div class="flex-1">
                <h3 class="font-semibold text-slate-900 mb-1">Complétez votre profil</h3>
                <p class="text-sm text-slate-600">
                  Renseignez vos informations professionnelles pour améliorer votre visibilité auprès des patients.
                  <button 
                    on:click={() => activeTab = 'settings'}
                    class="ml-2 text-indigo-600 hover:text-indigo-700 underline decoration-2 underline-offset-2 font-semibold hover:scale-105 inline-block transition-all"
                  >
                    Aller aux paramètres →
                  </button>
                </p>
              </div>
              <button 
                on:click={() => showBanner = false}
                class="text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg p-2 transition-all hover:rotate-90"
                aria-label="Fermer"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      {/if}

      <!-- Statistics Cards -->
      {#if statistics}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Total Appointments -->
          <div class="group relative overflow-hidden bg-white rounded-2xl shadow-lg border border-slate-200/50 p-6 hover:shadow-2xl hover:shadow-blue-500/20 transition-all duration-300 hover:-translate-y-1 animate-scale-in" style="animation-delay: 0.1s">
            <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-indigo-500/10 rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-semibold text-slate-600">Rendez-vous totaux</h3>
                <div class="w-12 h-12 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
              <p class="text-4xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent mb-2">{statistics.total_consultations}</p>
              <p class="text-sm text-slate-500 font-medium">À venir: <span class="text-blue-600 font-semibold">{statistics.upcoming_appointments}</span></p>
            </div>
          </div>

          <!-- Total Patients -->
          <div class="group relative overflow-hidden bg-white rounded-2xl shadow-lg border border-slate-200/50 p-6 hover:shadow-2xl hover:shadow-emerald-500/20 transition-all duration-300 hover:-translate-y-1 animate-scale-in" style="animation-delay: 0.2s">
            <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-emerald-500/10 to-teal-500/10 rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-semibold text-slate-600">Patients</h3>
                <div class="w-12 h-12 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-500/30 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                  </svg>
                </div>
              </div>
              <p class="text-4xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent mb-2">{totalPatients}</p>
              <p class="text-sm text-slate-500 font-medium">Nouveaux: <span class="text-emerald-600 font-semibold">{statistics.new_patients_count}</span></p>
            </div>
          </div>

          <!-- Rating -->
          <div class="group relative overflow-hidden bg-white rounded-2xl shadow-lg border border-slate-200/50 p-6 hover:shadow-2xl hover:shadow-amber-500/20 transition-all duration-300 hover:-translate-y-1 animate-scale-in" style="animation-delay: 0.3s">
            <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-500/10 to-orange-500/10 rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-semibold text-slate-600">Note moyenne</h3>
                <div class="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-xl flex items-center justify-center shadow-lg shadow-amber-500/30 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/>
                  </svg>
                </div>
              </div>
              <p class="text-4xl font-bold bg-gradient-to-r from-amber-500 to-orange-500 bg-clip-text text-transparent mb-2">{statistics.average_rating.toFixed(1)}</p>
              <p class="text-sm text-slate-500 font-medium">{statistics.total_reviews} avis reçus</p>
            </div>
          </div>

          <!-- Revenue -->
          <div class="group relative overflow-hidden bg-white rounded-2xl shadow-lg border border-slate-200/50 p-6 hover:shadow-2xl hover:shadow-purple-500/20 transition-all duration-300 hover:-translate-y-1 animate-scale-in" style="animation-delay: 0.4s">
            <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-full -mr-16 -mt-16 group-hover:scale-150 transition-transform duration-500"></div>
            <div class="relative">
              <div class="flex items-center justify-between mb-3">
                <h3 class="text-sm font-semibold text-slate-600">Revenus</h3>
                <div class="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-600 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30 group-hover:scale-110 group-hover:rotate-6 transition-all duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <p class="text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent mb-2">{formatCurrency(statistics.total_revenue)}</p>
              <p class="text-sm text-slate-500 font-medium">En attente: <span class="text-purple-600 font-semibold">{formatCurrency(statistics.pending_revenue)}</span></p>
            </div>
          </div>
        </div>
      {/if}

      <!-- Navigation Tabs -->
      <div class="bg-white rounded-2xl shadow-xl border border-slate-200/50 mb-8 overflow-hidden animate-slide-up">
        <div class="border-b border-slate-200">
          <nav class="flex overflow-x-auto scrollbar-hide">
            <button
              on:click={() => activeTab = 'overview'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'overview' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Vue d'ensemble</span>
              {#if activeTab === 'overview'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'appointments'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'appointments' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Rendez-vous</span>
              {#if activeTab === 'appointments'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'availability'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'availability' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Disponibilités</span>
              {#if activeTab === 'availability'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'patients'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'patients' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Patients</span>
              {#if activeTab === 'patients'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'reviews'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'reviews' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Avis</span>
              {#if activeTab === 'reviews'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'messages'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'messages' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Messages</span>
              {#if activeTab === 'messages'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'documents'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'documents' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Documents</span>
              {#if activeTab === 'documents'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'payments'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'payments' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Paiements</span>
              {#if activeTab === 'payments'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'settings'}
              class="group px-6 py-4 text-sm font-semibold border-b-3 transition-all whitespace-nowrap relative {activeTab === 'settings' ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'}"
            >
              <span class="relative z-10">Paramètres</span>
              {#if activeTab === 'settings'}
                <div class="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500 rounded-t-full animate-slide-in"></div>
              {/if}
            </button>
          </nav>
        </div>

        <!-- Tab Content -->
        <div class="p-6">
          {#if activeTab === 'overview'}
            <!-- Overview Tab -->
            <div class="space-y-6">
              <div>
                <h2 class="text-xl font-bold text-slate-900 mb-5 flex items-center gap-2">
                  <span class="w-1 h-6 bg-gradient-to-b from-indigo-500 to-purple-500 rounded-full"></span>
                  Rendez-vous à venir
                </h2>
                {#if upcomingAppointments.length > 0}
                  <div class="space-y-4">
                    {#each upcomingAppointments as appointment, i}
                      <div class="group bg-gradient-to-br from-slate-50 to-blue-50/50 rounded-2xl p-5 border border-slate-200/50 hover:shadow-xl hover:shadow-blue-500/10 transition-all duration-300 hover:-translate-y-1 animate-slide-in" style="animation-delay: {i * 0.1}s">
                        <div class="flex items-center justify-between gap-4">
                          <div class="flex-1">
                            <div class="flex items-center gap-3 mb-3 flex-wrap">
                              <h3 class="font-semibold text-slate-900 text-lg">
                                {appointment.patient ? `${appointment.patient.first_name} ${appointment.patient.last_name}` : 'Patient inconnu'}
                              </h3>
                              <span class="badge {getStatusBadgeClass(appointment.status)} shadow-sm">
                                {getStatusLabel(appointment.status)}
                              </span>
                            </div>
                            <div class="space-y-2">
                              <p class="text-sm text-slate-600 flex items-center gap-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                </svg>
                                {formatDate(appointment.appointment_date)}
                              </p>
                              {#if appointment.reason}
                                <p class="text-sm text-slate-500 flex items-center gap-2">
                                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-purple-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                                  </svg>
                                  <span class="font-medium">Motif:</span> {appointment.reason}
                                </p>
                              {/if}
                            </div>
                          </div>
                          <button
                            on:click={() => navigate(`/doctors/appointments/${appointment.id}`)}
                            class="px-5 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-300 font-semibold shadow-lg shadow-indigo-500/30 hover:shadow-xl hover:shadow-indigo-500/40 hover:scale-105 flex items-center gap-2 group whitespace-nowrap"
                          >
                            Voir détails
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                            </svg>
                          </button>
                        </div>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <div class="text-center py-16 bg-gradient-to-br from-slate-50 to-indigo-50/30 rounded-2xl border-2 border-dashed border-slate-300">
                    <div class="w-16 h-16 bg-gradient-to-br from-slate-200 to-slate-300 rounded-2xl flex items-center justify-center mx-auto mb-4">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <p class="text-slate-500 font-medium">Aucun rendez-vous à venir</p>
                  </div>
                {/if}
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Profile Progress -->
                <div class="relative overflow-hidden bg-gradient-to-br from-emerald-500 via-teal-500 to-cyan-600 rounded-2xl p-6 shadow-xl shadow-emerald-500/30 animate-scale-in" style="animation-delay: 0.2s">
                  <div class="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -mr-20 -mt-20"></div>
                  <div class="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full -ml-16 -mb-16"></div>
                  <div class="relative">
                    <div class="flex items-center gap-3 mb-4">
                      <div class="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <h3 class="font-bold text-white text-lg">Profil complété</h3>
                    </div>
                    <div class="flex items-center gap-4 mb-4">
                      <div class="flex-1">
                        <div class="bg-white/30 backdrop-blur-sm rounded-full h-4 overflow-hidden shadow-inner">
                          <div class="bg-white h-full rounded-full transition-all duration-1000 ease-out shadow-lg" style="width: {profile ? '85' : '20'}%"></div>
                        </div>
                      </div>
                      <span class="text-3xl font-bold text-white drop-shadow-lg">{profile ? '85' : '20'}%</span>
                    </div>
                    <p class="text-white/90 text-sm font-medium">Complétez votre profil pour attirer plus de patients et augmenter votre visibilité</p>
                  </div>
                </div>

                <!-- Performance Card -->
                <div class="relative overflow-hidden bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 rounded-2xl p-6 shadow-xl shadow-blue-500/30 animate-scale-in" style="animation-delay: 0.3s">
                  <div class="absolute top-0 right-0 w-40 h-40 bg-white/10 rounded-full -mr-20 -mt-20"></div>
                  <div class="absolute bottom-0 left-0 w-32 h-32 bg-white/10 rounded-full -ml-16 -mb-16"></div>
                  <div class="relative">
                    <div class="flex items-center gap-3 mb-4">
                      <div class="w-12 h-12 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                        </svg>
                      </div>
                      <h3 class="font-bold text-white text-lg">Performance ce mois</h3>
                    </div>
                    {#if statistics}
                      <div class="space-y-3">
                        <div class="flex items-center justify-between p-3 bg-white/10 backdrop-blur-sm rounded-xl">
                          <span class="text-white/90 text-sm font-medium">Consultations terminées</span>
                          <span class="font-bold text-white text-lg">{statistics.completed_consultations}</span>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-white/10 backdrop-blur-sm rounded-xl">
                          <span class="text-white/90 text-sm font-medium">Annulations</span>
                          <span class="font-bold text-white text-lg">{statistics.cancelled_consultations}</span>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-white/10 backdrop-blur-sm rounded-xl">
                          <span class="text-white/90 text-sm font-medium">Absences</span>
                          <span class="font-bold text-white text-lg">{statistics.no_show_consultations}</span>
                        </div>
                        <div class="flex items-center justify-between p-3 bg-gradient-to-r from-white/20 to-white/10 backdrop-blur-sm rounded-xl border border-white/30">
                          <span class="text-white font-semibold">Taux de présence</span>
                          <span class="font-bold text-white text-xl">{completionRate}%</span>
                        </div>
                      </div>
                    {:else}
                      <p class="text-white/80 text-sm">Aucune donnée disponible</p>
                    {/if}
                  </div>
                </div>
              </div>
            </div>
          {:else if activeTab === 'settings'}
            <DoctorSettings on:profileUpdated={handleProfileUpdated} />
          {:else if !profile}
            <!-- Profile required message -->
            <div class="text-center py-16 animate-fade-in">
              <div class="max-w-md mx-auto">
                <div class="w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-3xl flex items-center justify-center mx-auto mb-6 shadow-2xl shadow-blue-500/40 animate-bounce-slow">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <h3 class="text-2xl font-bold text-slate-900 mb-3">Profil professionnel requis</h3>
                <p class="text-slate-600 mb-8 leading-relaxed">
                  Veuillez compléter votre profil professionnel pour accéder à cette section et commencer à gérer vos {activeTab === 'appointments' ? 'rendez-vous' : activeTab === 'availability' ? 'disponibilités' : activeTab === 'patients' ? 'patients' : activeTab === 'reviews' ? 'avis' : activeTab === 'messages' ? 'messages' : 'paiements'}.
                </p>
                <button 
                  on:click={() => activeTab = 'settings'}
                  class="group inline-flex items-center px-8 py-4 bg-gradient-to-r from-indigo-500 to-purple-600 text-white rounded-xl hover:from-indigo-600 hover:to-purple-700 transition-all duration-300 font-semibold shadow-xl shadow-indigo-500/40 hover:shadow-2xl hover:shadow-indigo-500/50 hover:scale-105"
                >
                  Compléter mon profil
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 ml-2 group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </button>
              </div>
            </div>
          {:else if activeTab === 'appointments'}
            <DoctorAppointments />
          {:else if activeTab === 'availability'}
            <DoctorAvailability />
          {:else if activeTab === 'patients'}
            <DoctorPatients />
          {:else if activeTab === 'reviews'}
            <DoctorReviews />
          {:else if activeTab === 'messages'}
            <DoctorMessages />
          {:else if activeTab === 'documents'}
            <DoctorDocuments />
          {:else if activeTab === 'payments'}
            <DoctorPayments />
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

<style lang="postcss">
  .badge {
    @apply inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold shadow-sm;
  }

  .badge-warning {
    @apply bg-gradient-to-r from-amber-400 to-orange-400 text-white;
  }

  .badge-info {
    @apply bg-gradient-to-r from-blue-400 to-indigo-400 text-white;
  }

  .badge-success {
    @apply bg-gradient-to-r from-emerald-400 to-teal-400 text-white;
  }

  .badge-error {
    @apply bg-gradient-to-r from-red-400 to-pink-400 text-white;
  }

  .badge-secondary {
    @apply bg-gradient-to-r from-slate-400 to-gray-400 text-white;
  }

  .badge-neutral {
    @apply bg-slate-200 text-slate-700;
  }

  .scrollbar-hide {
    -ms-overflow-style: none;
    scrollbar-width: none;
  }

  .scrollbar-hide::-webkit-scrollbar {
    display: none;
  }

  @keyframes fade-in {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes slide-down {
    from {
      opacity: 0;
      transform: translateY(-20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slide-up {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  @keyframes slide-in {
    from {
      opacity: 0;
      transform: translateX(-20px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  @keyframes scale-in {
    from {
      opacity: 0;
      transform: scale(0.9);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-5px);
    }
  }

  @keyframes pulse-soft {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.8;
    }
  }

  @keyframes bounce-slow {
    0%, 100% {
      transform: translateY(0);
    }
    50% {
      transform: translateY(-10px);
    }
  }

  .animate-fade-in {
    animation: fade-in 0.5s ease-out;
  }

  .animate-slide-down {
    animation: slide-down 0.5s ease-out;
  }

  .animate-slide-up {
    animation: slide-up 0.5s ease-out;
  }

  .animate-slide-in {
    animation: slide-in 0.5s ease-out;
  }

  .animate-scale-in {
    animation: scale-in 0.5s ease-out;
    animation-fill-mode: both;
  }

  .animate-float {
    animation: float 3s ease-in-out infinite;
  }

  .animate-pulse-soft {
    animation: pulse-soft 2s ease-in-out infinite;
  }

  .animate-bounce-slow {
    animation: bounce-slow 2s ease-in-out infinite;
  }
</style>