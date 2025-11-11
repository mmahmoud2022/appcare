<script lang="ts">
  import { onMount, tick } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { getCurrentUser } from '../../lib/api';
  import { navigate } from '../../lib/router';
  import {
    getPatientDashboard,
    type PatientDashboardSummary,
    type PatientAppointment,
    type PatientDashboardNotification
  } from '../../lib/api-patient';
  import type { DoctorSearchResult } from '../../lib/api-patient';
  import PatientAppointments from './PatientAppointments.svelte';
  import PatientDoctors from './PatientDoctors.svelte';
  import PatientMedicalRecords from './PatientMedicalRecords.svelte';
  import PatientMessages from './PatientMessages.svelte';
  import PatientPayments from './PatientPayments.svelte';
  import PatientSettings from './PatientSettings.svelte';

  let dashboard: PatientDashboardSummary | null = null;
  let loading = true;
  let activeTab: 'overview' | 'appointments' | 'doctors' | 'medical' | 'messages' | 'payments' | 'settings' = 'overview';
  let appointmentsComponent: any;
  let currentUser: any = null;

  onMount(async () => {
    try {
      const user = await getCurrentUser();
      currentUser = user;
      if (user.role !== 'patient' && user.role !== 'PATIENT') {
        navigate('/login');
        return;
      }
      await loadDashboard();
    } catch (error) {
      console.error('Erreur lors du chargement du tableau de bord patient:', error);
      navigate('/login');
    } finally {
      loading = false;
    }
  });

  const loadDashboard = async () => {
    dashboard = await getPatientDashboard();
  };

  const handleRefresh = async () => {
    await loadDashboard();
  };

  const formatDate = (value: string) => {
    return new Date(value).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatNotificationLevel = (notification: PatientDashboardNotification) => {
    switch (notification.level) {
      case 'warning':
        return 'bg-amber-50 border-amber-200 text-amber-800';
      case 'success':
        return 'bg-emerald-50 border-emerald-200 text-emerald-800';
      case 'alert':
        return 'bg-red-50 border-red-200 text-red-800';
      default:
        return 'bg-blue-50 border-blue-200 text-blue-800';
    }
  };

  const getAppointmentDoctorName = (appointment: PatientAppointment) => {
    const parts = [appointment.doctor_first_name, appointment.doctor_last_name].filter(Boolean) as string[];
    return parts.length ? parts.join(' ') : 'Médecin';
  };

  const handleOpenDoctorSearch = () => {
    activeTab = 'doctors';
  };

  const handleDoctorBooking = async (event: CustomEvent<{ doctor: DoctorSearchResult }>) => {
    if (!event.detail?.doctor) {
      return;
    }
    activeTab = 'appointments';
    await tick();
    appointmentsComponent?.openBookingForDoctor(event.detail.doctor);
  };
</script>

<div class="min-h-screen bg-gradient-to-br from-gray-50 via-blue-50/20 to-indigo-50/10">
  <!-- Professional Header -->
  <header class="relative overflow-hidden bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 shadow-xl">
    <div class="absolute top-0 right-0 w-96 h-96 bg-white/5 rounded-full -mr-48 -mt-48 blur-3xl"></div>
    <div class="absolute bottom-0 left-0 w-96 h-96 bg-indigo-500/10 rounded-full -ml-48 -mb-48 blur-3xl"></div>
    
    <div class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="relative">
            <div class="w-16 h-16 rounded-2xl bg-white/15 backdrop-blur-lg flex items-center justify-center shadow-xl border border-white/20">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div class="absolute -bottom-1 -right-1 w-5 h-5 bg-emerald-400 rounded-full border-2 border-white shadow-lg"></div>
          </div>
          <div>
            <h1 class="text-2xl md:text-3xl font-bold text-white">Tableau de bord</h1>
            {#if currentUser}
              <p class="text-sm md:text-base text-blue-100 font-medium">
                {currentUser.first_name} {currentUser.last_name}
              </p>
            {/if}
          </div>
        </div>
        <button
          on:click={() => navigate('/')}
          class="px-5 py-2.5 bg-white/10 backdrop-blur-md text-white hover:bg-white/20 font-semibold rounded-xl transition-all duration-300 border border-white/20 shadow-lg hover:shadow-xl flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
          <span class="hidden sm:inline">Déconnexion</span>
        </button>
      </div>
    </div>
  </header>

  {#if loading}
    <div class="flex items-center justify-center h-96" transition:fade={{ duration: 300 }}>
      <div class="text-center">
        <div class="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full shadow-2xl animate-pulse mb-6">
          <div class="animate-spin rounded-full h-20 w-20 border-t-4 border-b-4 border-white"></div>
        </div>
        <p class="text-xl text-gray-700 font-semibold">Chargement de votre espace santé...</p>
        <p class="text-sm text-gray-500 mt-2">Préparation de vos informations</p>
      </div>
    </div>
  {:else if dashboard}
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Professional Stats Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
        <!-- Rendez-vous Card -->
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1 cursor-pointer relative overflow-hidden"
          on:click={() => activeTab = 'appointments'}
          transition:fly={{ y: 20, duration: 400, delay: 0 }}
        >
          <div class="absolute top-0 right-0 w-24 h-24 bg-blue-50 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-blue-50 rounded-xl group-hover:bg-blue-100 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">Rendez-vous</span>
            </div>
            <div class="mb-2">
              <span class="text-4xl font-semibold text-gray-900">{dashboard.upcoming_appointments.length}</span>
            </div>
            <p class="text-sm text-gray-600 font-medium">Consultations à venir</p>
          </div>
        </div>

        <!-- Messages Card -->
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1 cursor-pointer relative overflow-hidden"
          on:click={() => activeTab = 'messages'}
          transition:fly={{ y: 20, duration: 400, delay: 100 }}
        >
          <div class="absolute top-0 right-0 w-24 h-24 bg-indigo-50 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-indigo-50 rounded-xl group-hover:bg-indigo-100 transition-colors relative">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
                {#if dashboard.unread_messages > 0}
                  <div class="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center">
                    <span class="text-[10px] font-semibold text-white">{dashboard.unread_messages}</span>
                  </div>
                {/if}
              </div>
              <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">Messages</span>
            </div>
            <div class="mb-2">
              <span class="text-4xl font-semibold text-gray-900">{dashboard.unread_messages}</span>
            </div>
            <p class="text-sm text-gray-600 font-medium">Messages non lus</p>
          </div>
        </div>

        <!-- Documents Card -->
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1 cursor-pointer relative overflow-hidden"
          on:click={() => activeTab = 'medical'}
          transition:fly={{ y: 20, duration: 400, delay: 200 }}
        >
          <div class="absolute top-0 right-0 w-24 h-24 bg-emerald-50 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-emerald-50 rounded-xl group-hover:bg-emerald-100 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">Documents</span>
            </div>
            <div class="mb-2">
              <span class="text-4xl font-semibold text-gray-900">{dashboard.recent_documents.length}</span>
            </div>
            <p class="text-sm text-gray-600 font-medium">Dossier médical</p>
          </div>
        </div>

        <!-- Paiements Card -->
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="group bg-white rounded-2xl shadow-md hover:shadow-xl border border-gray-100 p-6 transition-all duration-300 hover:-translate-y-1 cursor-pointer relative overflow-hidden"
          on:click={() => activeTab = 'payments'}
          transition:fly={{ y: 20, duration: 400, delay: 300 }}
        >
          <div class="absolute top-0 right-0 w-24 h-24 bg-amber-50 rounded-full -mr-12 -mt-12 group-hover:scale-150 transition-transform duration-500"></div>
          <div class="relative">
            <div class="flex items-center justify-between mb-4">
              <div class="p-3 bg-amber-50 rounded-xl group-hover:bg-amber-100 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
              </div>
              <span class="text-xs font-medium text-gray-500 uppercase tracking-wide">Paiements</span>
            </div>
            <div class="mb-2">
              <span class="text-4xl font-semibold text-gray-900">{dashboard.pending_payments}</span>
            </div>
            <p class="text-sm text-gray-600 font-medium">En attente</p>
          </div>
        </div>
      </div>

      <!-- Clean Notifications -->
      {#if dashboard.notifications.length}
        <div class="mb-8" transition:fly={{ y: 20, duration: 400, delay: 400 }}>
          <div class="flex items-center gap-3 mb-4">
            <div class="p-2 bg-amber-50 rounded-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
            </div>
            <h2 class="text-xl font-bold text-gray-900">Notifications</h2>
            <span class="ml-auto px-3 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-bold">
              {dashboard.notifications.length}
            </span>
          </div>
          <div class="space-y-3">
            {#each dashboard.notifications as notification, i}
              <div 
                class={`bg-white border rounded-xl px-5 py-4 flex items-start gap-4 shadow-sm hover:shadow-md transition-all duration-300 ${
                  notification.level === 'alert' ? 'border-red-200 bg-red-50/30' :
                  notification.level === 'warning' ? 'border-amber-200 bg-amber-50/30' :
                  notification.level === 'success' ? 'border-emerald-200 bg-emerald-50/30' :
                  'border-blue-200 bg-blue-50/30'
                }`}
                transition:fly={{ x: -20, duration: 300, delay: i * 50 }}
              >
                <div class="flex-shrink-0">
                  {#if notification.level === 'alert'}
                    <div class="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                  {:else if notification.level === 'success'}
                    <div class="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  {:else if notification.level === 'warning'}
                    <div class="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                  {:else}
                    <div class="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                  {/if}
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-sm font-semibold text-gray-900 mb-1">{notification.message}</p>
                  <div class="flex items-center gap-2 text-xs text-gray-500">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    {formatDate(notification.created_at)}
                  </div>
                </div>
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Modern Clean Tab Navigation -->
      <div class="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden" transition:fly={{ y: 20, duration: 400, delay: 500 }}>
        <div class="border-b border-gray-200 bg-gray-50/50">
          <nav class="flex overflow-x-auto">
            <button
              on:click={() => activeTab = 'overview'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'overview' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4 5a1 1 0 011-1h4a1 1 0 011 1v7a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM14 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 16a1 1 0 011-1h4a1 1 0 011 1v3a1 1 0 01-1 1H5a1 1 0 01-1-1v-3zM14 13a1 1 0 011-1h4a1 1 0 011 1v6a1 1 0 01-1 1h-4a1 1 0 01-1-1v-6z" />
              </svg>
              Vue d'ensemble
            </button>
            <button
              on:click={() => activeTab = 'appointments'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'appointments' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Rendez-vous
            </button>
            <button
              on:click={() => activeTab = 'doctors'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'doctors' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              Praticiens
            </button>
            <button
              on:click={() => activeTab = 'medical'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'medical' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Dossier médical
            </button>
            <button
              on:click={() => activeTab = 'messages'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap relative ${activeTab === 'messages' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              Messagerie
              {#if dashboard.unread_messages > 0}
                <span class="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full"></span>
              {/if}
            </button>
            <button
              on:click={() => activeTab = 'payments'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'payments' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
              </svg>
              Paiements
            </button>
            <button
              on:click={() => activeTab = 'settings'}
              class={`flex items-center gap-2 px-6 py-4 text-sm font-semibold border-b-2 transition-all duration-200 whitespace-nowrap ${activeTab === 'settings' ? 'border-blue-600 text-blue-600 bg-white' : 'border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-50'}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              Paramètres
            </button>
          </nav>
        </div>

        <div class="p-6">
          {#if activeTab === 'overview'}
            <div class="space-y-6">
              <!-- Prochains RDV -->
              <div>
                <div class="flex items-center gap-2 mb-4">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <h2 class="text-lg font-bold text-gray-900">Prochains rendez-vous</h2>
                </div>
                {#if dashboard.upcoming_appointments.length}
                  <div class="space-y-3">
                    {#each dashboard.upcoming_appointments as appointment}
                      <div class="bg-gradient-to-r from-blue-50/50 to-white border border-blue-100 rounded-xl p-4 hover:shadow-md transition-shadow">
                        <div class="flex items-center justify-between">
                          <div class="flex-1">
                            <h3 class="font-semibold text-gray-900">{getAppointmentDoctorName(appointment)}</h3>
                            <p class="text-sm text-gray-600 mt-1 flex items-center gap-1.5">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {formatDate(appointment.appointment_date)}
                            </p>
                            {#if appointment.reason}
                              <p class="text-sm text-gray-500 mt-1.5">Motif: {appointment.reason}</p>
                            {/if}
                          </div>
                          <span class="px-3 py-1.5 text-xs font-semibold rounded-lg bg-blue-100 text-blue-700 whitespace-nowrap">
                            {appointment.consultation_type === 'teleconsultation' ? 'Télé' : 'Présentiel'}
                          </span>
                        </div>
                      </div>
                    {/each}
                  </div>
                {:else}
                  <div class="text-center py-12 bg-gray-50 rounded-xl border-2 border-dashed border-gray-200">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-gray-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <p class="text-gray-600 font-medium">Aucun rendez-vous à venir</p>
                    <p class="text-sm text-gray-500 mt-1">Prenez rendez-vous avec un praticien</p>
                  </div>
                {/if}
              </div>

              <!-- Action Cards -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div class="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white shadow-lg">
                  <h3 class="font-bold text-lg mb-2">🩺 Trouver un médecin</h3>
                  <p class="text-sm text-blue-100 mb-4">Recherchez un praticien près de chez vous</p>
                  <button
                    on:click={() => activeTab = 'doctors'}
                    class="inline-flex items-center gap-2 px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50 transition-colors font-semibold text-sm"
                  >
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    Rechercher
                  </button>
                </div>

                <div class="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-5 text-white shadow-lg">
                  <h3 class="font-bold text-lg mb-2">📹 Téléconsultation</h3>
                  <p class="text-sm text-emerald-100">Consultez un médecin à distance</p>
                </div>
              </div>
            </div>
          {:else if activeTab === 'appointments'}
            <PatientAppointments
              bind:this={appointmentsComponent}
              on:refresh={handleRefresh}
              on:openDoctorSearch={handleOpenDoctorSearch}
            />
          {:else if activeTab === 'doctors'}
            <PatientDoctors on:book={handleDoctorBooking} />
          {:else if activeTab === 'medical'}
            <PatientMedicalRecords />
          {:else if activeTab === 'messages'}
            <PatientMessages />
          {:else if activeTab === 'payments'}
            <PatientPayments />
          {:else if activeTab === 'settings'}
            <PatientSettings on:refresh={handleRefresh} profile={dashboard.profile} />
          {/if}
        </div>
      </div>
    </div>
  {:else}
    <div class="max-w-3xl mx-auto px-4 py-16 text-center">
      <h2 class="text-xl font-semibold text-gray-900">Impossible de charger votre tableau de bord</h2>
      <p class="text-gray-600 mt-2">Actualisez la page ou réessayez plus tard. Si le problème persiste, contactez le support.</p>
      <button
        on:click={handleRefresh}
        class="mt-6 inline-flex items-center px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >Réessayer</button>
    </div>
  {/if}
</div>

<style>
  /* Scrollbar styling for better UX */
  nav::-webkit-scrollbar {
    height: 4px;
  }
  
  nav::-webkit-scrollbar-thumb {
    background-color: rgb(191 219 254);
    border-radius: 2px;
  }
  
  nav::-webkit-scrollbar-track {
    background-color: rgb(243 244 246);
  }
</style>
