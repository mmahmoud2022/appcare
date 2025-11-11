<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../../lib/router';
  import { authStore } from '../../lib/stores/auth';
  import {
    getAllUsers,
    getPendingDoctors,
    approveDoctor,
    rejectDoctor,
    suspendUser,
    activateUser,
    deleteUser,
    getStatistics,
    logout,
  } from '../../lib/api';
  import type { User, AdminActionResponse, StatisticsResponse } from '../../lib/api';

  let currentUser: User | null = null;
  let allUsers: User[] = [];
  let pendingDoctors: User[] = [];
  let statistics: StatisticsResponse | null = null;
  let loading = true;
  let activeTab: 'pending' | 'all-users' | 'patients' | 'doctors' = 'pending';
  let searchQuery = '';
  let showModal = false;
  let modalAction: 'suspend' | 'delete' | 'approve' | 'reject' | null = null;
  let selectedUser: User | null = null;
  let actionReason = '';
  let actionLoading = false;
  let successMessage = '';
  let errorMessage = '';
  let patientsExpanded = false;
  let doctorsExpanded = false;

  // Subscribe to auth store
  authStore.subscribe((state) => {
    currentUser = state.user;
  });

  onMount(async () => {
    // Check if user is admin (case-insensitive comparison)
    if (!currentUser || currentUser.role.toUpperCase() !== 'ADMIN') {
      navigate('/login');
      return;
    }

    await loadData();
  });

  async function loadData() {
    loading = true;
    errorMessage = '';
    try {
      const [stats, users, pending] = await Promise.all([
        getStatistics(),
        getAllUsers(),
        getPendingDoctors(),
      ]);
      statistics = stats;
      allUsers = users;
      // Filter to ensure only doctors (not admins) are in pending list
      pendingDoctors = pending.filter((u) => u.role.toUpperCase() === 'DOCTOR');
    } catch (error: any) {
      errorMessage = error.response?.data?.detail || 'Erreur lors du chargement des données';
      console.error('Error loading admin data:', error);
    } finally {
      loading = false;
    }
  }

  function openModal(action: typeof modalAction, user: User) {
    modalAction = action;
    selectedUser = user;
    actionReason = '';
    showModal = true;
  }

  function closeModal() {
    showModal = false;
    modalAction = null;
    selectedUser = null;
    actionReason = '';
  }

  async function confirmAction() {
    if (!selectedUser || !modalAction) return;

    actionLoading = true;
    errorMessage = '';
    successMessage = '';

    try {
      let response: AdminActionResponse;

      switch (modalAction) {
        case 'approve':
          response = await approveDoctor(selectedUser.id);
          break;
        case 'reject':
          response = await rejectDoctor(selectedUser.id, actionReason || 'Rejected by admin');
          break;
        case 'suspend':
          response = await suspendUser(selectedUser.id, actionReason || 'Suspended by admin');
          break;
        case 'delete':
          response = await deleteUser(selectedUser.id);
          break;
      }

      successMessage = response!.message;
      closeModal();
      await loadData();

      // Clear success message after 5 seconds
      setTimeout(() => {
        successMessage = '';
      }, 5000);
    } catch (error: any) {
      errorMessage = error.response?.data?.detail || 'Une erreur est survenue';
    } finally {
      actionLoading = false;
    }
  }

  async function handleActivateUser(user: User) {
    actionLoading = true;
    errorMessage = '';
    successMessage = '';

    try {
      const response = await activateUser(user.id);
      successMessage = response.message;
      await loadData();

      setTimeout(() => {
        successMessage = '';
      }, 5000);
    } catch (error: any) {
      errorMessage = error.response?.data?.detail || 'Une erreur est survenue';
    } finally {
      actionLoading = false;
    }
  }

  async function handleLogout() {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout error:', error);
      navigate('/login');
    }
  }

  // Filter users based on active tab and search query
  $: filteredUsers = (() => {
    let users: User[] = [];

    switch (activeTab) {
      case 'pending':
        users = pendingDoctors;
        break;
      case 'all-users':
        users = allUsers;
        break;
      case 'patients':
        users = allUsers.filter((u) => u.role.toUpperCase() === 'PATIENT');
        break;
      case 'doctors':
        users = allUsers.filter((u) => u.role.toUpperCase() === 'DOCTOR');
        break;
    }

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      users = users.filter(
        (u) =>
          u.email.toLowerCase().includes(query) ||
          `${u.first_name} ${u.last_name}`.toLowerCase().includes(query)
      );
    }

    return users;
  })();
</script>

<div class="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50">
  <!-- Header -->
  <header class="bg-white/80 backdrop-blur-lg border-b-2 border-orange-100 shadow-md sticky top-0 z-10">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h1 class="text-2xl font-bold text-gray-900">Tableau de bord Admin</h1>
            <p class="text-sm text-gray-600 font-medium">
              Bienvenue, {currentUser ? `${currentUser.first_name} ${currentUser.last_name}` : 'Admin'}
            </p>
          </div>
        </div>
        <div class="flex items-center gap-3">
          <button 
            on:click={() => navigate('/dashboard')}
            class="px-4 py-2 rounded-xl border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all duration-200"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard
          </button>
          <button 
            on:click={handleLogout}
            class="group relative px-4 py-2 rounded-xl font-bold shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-red-500 to-rose-600 opacity-90"></div>
            <div class="absolute inset-0 bg-white/20"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span class="relative flex items-center gap-2 text-white drop-shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              Déconnexion
            </span>
          </button>
        </div>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Success/Error Messages -->
    {#if successMessage}
      <div class="mb-6 bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-5 shadow-lg animate-scale-in">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <div class="flex-1 pt-1">
            <h4 class="font-bold text-gray-900 mb-1">Succès</h4>
            <p class="text-sm text-green-900 font-medium">{successMessage}</p>
          </div>
        </div>
      </div>
    {/if}

    {#if errorMessage}
      <div class="mb-6 bg-red-50/80 backdrop-blur-sm border-2 border-red-200 rounded-xl p-4 shadow-md animate-shake">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
          </div>
          <div class="flex-1 pt-1">
            <h4 class="font-bold text-gray-900 mb-1">Erreur</h4>
            <p class="text-sm text-red-800 font-medium">{errorMessage}</p>
          </div>
        </div>
      </div>
    {/if}

    <!-- Statistics Cards -->
    {#if statistics}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <!-- Total Users -->
        <div class="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all duration-300 overflow-hidden group">
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-400/20 to-purple-500/20 rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
          <div class="relative flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Total Utilisateurs</p>
              <p class="text-4xl font-bold text-gray-900">{statistics.total_users}</p>
            </div>
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Doctors -->
        <div class="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all duration-300 overflow-hidden group">
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-emerald-400/20 to-teal-500/20 rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
          <div class="relative flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Médecins</p>
              <p class="text-4xl font-bold text-gray-900">{statistics.total_doctors}</p>
            </div>
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Patients -->
        <div class="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all duration-300 overflow-hidden group">
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-cyan-400/20 to-blue-500/20 rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
          <div class="relative flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">Patients</p>
              <p class="text-4xl font-bold text-gray-900">{statistics.total_patients}</p>
            </div>
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </div>
        </div>

        <!-- Pending -->
        <div class="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 p-6 hover:shadow-xl transition-all duration-300 overflow-hidden group">
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-orange-400/20 to-amber-500/20 rounded-full -mr-16 -mt-16 group-hover:scale-125 transition-transform duration-500"></div>
          <div class="relative flex items-center justify-between">
            <div>
              <p class="text-sm font-semibold text-gray-600 uppercase tracking-wide mb-1">En Attente</p>
              <p class="text-4xl font-bold text-gray-900">{statistics.pending_doctors}</p>
            </div>
            <div class="w-16 h-16 rounded-2xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Detailed Statistics Sections -->
    {#if statistics}
      <!-- Patient Statistics Section -->
      <div class="mb-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="px-6 py-5 border-b-2 border-gray-100 bg-gradient-to-r from-cyan-50 to-blue-50 cursor-pointer hover:bg-gradient-to-r hover:from-cyan-100 hover:to-blue-100 transition-colors duration-200"
          on:click={() => patientsExpanded = !patientsExpanded}
        >
          <div class="flex items-center justify-between">
            <h3 class="text-xl font-bold text-gray-900 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-cyan-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
              Statistiques des Patients
              <span class="ml-2 px-2.5 py-1 bg-cyan-100 text-cyan-700 text-sm font-bold rounded-full">
                {statistics.patients.length}
              </span>
            </h3>
            <button class="p-2 hover:bg-cyan-200 rounded-lg transition-colors duration-200" title="{patientsExpanded ? 'Réduire' : 'Développer'} la liste des patients" aria-label="{patientsExpanded ? 'Réduire' : 'Développer'} la liste des patients">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-6 w-6 text-cyan-700 transition-transform duration-300 {patientsExpanded ? 'rotate-180' : ''}" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
        {#if patientsExpanded}
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Patient</th>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Email</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">En attente</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-green-700 uppercase tracking-wider">Confirmés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-blue-700 uppercase tracking-wider">Terminés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-red-700 uppercase tracking-wider">Annulés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-orange-700 uppercase tracking-wider">Absents</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-purple-700 uppercase tracking-wider">Total</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each statistics.patients as patient}
                <tr class="hover:bg-blue-50 transition-colors duration-150">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-semibold text-gray-900">{patient.patient_name}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm text-gray-600">{patient.patient_email}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-gray-100 text-gray-800">
                      {patient.pending_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-green-100 text-green-800">
                      {patient.confirmed_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-blue-100 text-blue-800">
                      {patient.completed_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-red-100 text-red-800">
                      {patient.cancelled_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-orange-100 text-orange-800">
                      {patient.no_show_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-purple-100 text-purple-800">
                      {patient.total_appointments}
                    </span>
                  </td>
                </tr>
              {:else}
                <tr>
                  <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    Aucun patient trouvé
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        {/if}
      </div>

      <!-- Doctor Statistics Section -->
      <div class="mb-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
        <!-- svelte-ignore a11y-click-events-have-key-events -->
        <!-- svelte-ignore a11y-no-static-element-interactions -->
        <div 
          class="px-6 py-5 border-b-2 border-gray-100 bg-gradient-to-r from-emerald-50 to-teal-50 cursor-pointer hover:bg-gradient-to-r hover:from-emerald-100 hover:to-teal-100 transition-colors duration-200"
          on:click={() => doctorsExpanded = !doctorsExpanded}
        >
          <div class="flex items-center justify-between">
            <h3 class="text-xl font-bold text-gray-900 flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Statistiques des Médecins
              <span class="ml-2 px-2.5 py-1 bg-emerald-100 text-emerald-700 text-sm font-bold rounded-full">
                {statistics.doctors.length}
              </span>
            </h3>
            <button class="p-2 hover:bg-emerald-200 rounded-lg transition-colors duration-200" title="{doctorsExpanded ? 'Réduire' : 'Développer'} la liste des médecins" aria-label="{doctorsExpanded ? 'Réduire' : 'Développer'} la liste des médecins">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-6 w-6 text-emerald-700 transition-transform duration-300 {doctorsExpanded ? 'rotate-180' : ''}" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>
          </div>
        </div>
        {#if doctorsExpanded}
        <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Médecin</th>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Spécialisation</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-gray-600 uppercase tracking-wider">En attente</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-green-700 uppercase tracking-wider">Confirmés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-blue-700 uppercase tracking-wider">Terminés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-red-700 uppercase tracking-wider">Annulés</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-orange-700 uppercase tracking-wider">Absents</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-purple-700 uppercase tracking-wider">Total</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-yellow-700 uppercase tracking-wider">Note</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              {#each statistics.doctors as doctor}
                <tr class="hover:bg-emerald-50 transition-colors duration-150">
                  <td class="px-6 py-4 whitespace-nowrap">
                    <div class="text-sm font-semibold text-gray-900">{doctor.doctor_name}</div>
                    <div class="text-xs text-gray-500">{doctor.doctor_email}</div>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800">
                      {doctor.specialization}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-gray-100 text-gray-800">
                      {doctor.pending_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-green-100 text-green-800">
                      {doctor.confirmed_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-blue-100 text-blue-800">
                      {doctor.completed_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-red-100 text-red-800">
                      {doctor.cancelled_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-orange-100 text-orange-800">
                      {doctor.no_show_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-sm font-bold bg-purple-100 text-purple-800">
                      {doctor.total_appointments}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center">
                    <div class="flex items-center justify-center gap-1">
                      {#if doctor.average_rating > 0}
                        <span class="text-yellow-500 font-bold">{doctor.average_rating.toFixed(1)}</span>
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      {:else}
                        <span class="text-gray-400 text-sm">Pas de note</span>
                      {/if}
                    </div>
                  </td>
                </tr>
              {:else}
                <tr>
                  <td colspan="9" class="px-6 py-8 text-center text-gray-500">
                    Aucun médecin trouvé
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
        {/if}
      </div>
    {/if}

    <!-- Tabs -->
    <div class="flex flex-wrap gap-3 mb-6">
      <button
        class="px-6 py-3 rounded-xl font-bold transition-all duration-200 {activeTab === 'pending' ? 'bg-gradient-to-r from-orange-500 to-amber-600 text-white shadow-lg scale-105' : 'bg-white/70 text-gray-700 border-2 border-gray-200 hover:bg-white hover:border-orange-300'}"
        on:click={() => (activeTab = 'pending')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Médecins en attente ({pendingDoctors.length})
      </button>
      <button
        class="px-6 py-3 rounded-xl font-bold transition-all duration-200 {activeTab === 'all-users' ? 'bg-gradient-to-r from-orange-500 to-amber-600 text-white shadow-lg scale-105' : 'bg-white/70 text-gray-700 border-2 border-gray-200 hover:bg-white hover:border-orange-300'}"
        on:click={() => (activeTab = 'all-users')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
        Tous ({allUsers.length})
      </button>
      <button
        class="px-6 py-3 rounded-xl font-bold transition-all duration-200 {activeTab === 'patients' ? 'bg-gradient-to-r from-orange-500 to-amber-600 text-white shadow-lg scale-105' : 'bg-white/70 text-gray-700 border-2 border-gray-200 hover:bg-white hover:border-orange-300'}"
        on:click={() => (activeTab = 'patients')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
        </svg>
        Patients ({allUsers.filter((u) => u.role.toUpperCase() === 'PATIENT').length})
      </button>
      <button
        class="px-6 py-3 rounded-xl font-bold transition-all duration-200 {activeTab === 'doctors' ? 'bg-gradient-to-r from-orange-500 to-amber-600 text-white shadow-lg scale-105' : 'bg-white/70 text-gray-700 border-2 border-gray-200 hover:bg-white hover:border-orange-300'}"
        on:click={() => (activeTab = 'doctors')}
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 inline-block mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Médecins ({allUsers.filter((u) => u.role.toUpperCase() === 'DOCTOR').length})
      </button>
    </div>

    <!-- Users Table -->
    <div class="relative bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border-2 border-gray-100 overflow-hidden">
      <div class="px-6 py-5 border-b-2 border-gray-100 flex items-center justify-between">
        <h2 class="text-xl font-bold text-gray-900">
          {#if activeTab === 'pending'}
            Médecins en attente d'approbation
          {:else if activeTab === 'all-users'}
            Tous les utilisateurs
          {:else if activeTab === 'patients'}
            Patients
          {:else}
            Médecins
          {/if}
        </h2>
        <div class="flex items-center gap-3">
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <input
              type="text"
              class="pl-10 pr-4 py-2 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/70 font-medium w-64"
              placeholder="Rechercher..."
              bind:value={searchQuery}
            />
          </div>
          <button 
            class="group relative px-4 py-2 rounded-xl font-bold shadow-md hover:shadow-lg transition-all duration-300 overflow-hidden"
            on:click={loadData}
          >
            <div class="absolute inset-0 bg-gradient-to-r from-orange-500 to-amber-600 opacity-90"></div>
            <div class="absolute inset-0 bg-white/20"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span class="relative flex items-center gap-2 text-white drop-shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 group-hover:rotate-180 transition-transform duration-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
              Actualiser
            </span>
          </button>
        </div>
      </div>

      <div class="overflow-x-auto">
        {#if loading}
          <div class="flex items-center justify-center py-16">
            <div class="relative">
              <div class="w-16 h-16 rounded-full border-4 border-orange-200 border-t-orange-600 animate-spin"></div>
              <div class="absolute inset-0 flex items-center justify-center">
                <div class="w-8 h-8 rounded-full bg-gradient-to-br from-orange-500 to-amber-600"></div>
              </div>
            </div>
          </div>
        {:else if filteredUsers.length === 0}
          <div class="text-center py-16">
            <div class="inline-block p-6 bg-gradient-to-br from-gray-100 to-gray-200 rounded-full mb-4">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <h3 class="text-xl font-bold text-gray-900 mb-2">Aucun utilisateur trouvé</h3>
            <p class="text-gray-600 font-medium">
              {searchQuery
                ? 'Aucun résultat pour votre recherche'
                : 'Aucun utilisateur dans cette catégorie'}
            </p>
          </div>
        {:else}
          <table class="w-full">
            <thead class="bg-gradient-to-r from-gray-50 to-gray-100 border-b-2 border-gray-200">
              <tr>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">ID</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Nom</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Email</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Rôle</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Statut</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Vérifié</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Créé le</th>
                <th class="px-6 py-4 text-left text-xs font-bold text-gray-700 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-100">
              {#each filteredUsers as user (user.id)}
                <tr class="hover:bg-orange-50/50 transition-colors duration-150">
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-semibold text-gray-900">#{user.id}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{user.first_name} {user.last_name}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{user.email}</td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold {user.role.toLowerCase() === 'admin' ? 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-800 border border-orange-300' : user.role.toLowerCase() === 'doctor' ? 'bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-800 border border-emerald-300' : 'bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-800 border border-purple-300'}">
                      {user.role}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold {user.is_active ? 'bg-green-100 text-green-800 border border-green-300' : 'bg-red-100 text-red-800 border border-red-300'}">
                      {user.is_active ? '✓ Actif' : '✕ Suspendu'}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap">
                    <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold {user.email_verified ? 'bg-blue-100 text-blue-800 border border-blue-300' : 'bg-yellow-100 text-yellow-800 border border-yellow-300'}">
                      {user.email_verified ? '✓ Oui' : '⏳ Non'}
                    </span>
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-600 font-medium">{new Date(user.created_at).toLocaleDateString('fr-FR')}</td>
                  <td class="px-6 py-4 whitespace-nowrap text-sm">
                    <div class="flex items-center gap-2">
                      {#if activeTab === 'pending' && user.role.toUpperCase() === 'DOCTOR' && !user.admin_approved}
                        <button
                          class="px-3 py-1.5 rounded-lg bg-green-100 hover:bg-green-200 text-green-800 font-semibold text-xs border border-green-300 transition-colors duration-200"
                          on:click={() => openModal('approve', user)}
                        >
                          ✓ Approuver
                        </button>
                        <button
                          class="px-3 py-1.5 rounded-lg bg-red-100 hover:bg-red-200 text-red-800 font-semibold text-xs border border-red-300 transition-colors duration-200"
                          on:click={() => openModal('reject', user)}
                        >
                          ✕ Rejeter
                        </button>
                      {:else}
                        {#if user.is_active && user.role.toUpperCase() !== 'ADMIN'}
                          <button
                            class="px-3 py-1.5 rounded-lg bg-yellow-100 hover:bg-yellow-200 text-yellow-800 font-semibold text-xs border border-yellow-300 transition-colors duration-200"
                            on:click={() => openModal('suspend', user)}
                          >
                            ⏸ Suspendre
                          </button>
                        {/if}
                        {#if !user.is_active}
                          <button
                            class="px-3 py-1.5 rounded-lg bg-green-100 hover:bg-green-200 text-green-800 font-semibold text-xs border border-green-300 transition-colors duration-200"
                            on:click={() => handleActivateUser(user)}
                            disabled={actionLoading}
                          >
                            ▶ Activer
                          </button>
                        {/if}
                        {#if user.role.toUpperCase() !== 'ADMIN'}
                          <button
                            class="px-3 py-1.5 rounded-lg bg-red-100 hover:bg-red-200 text-red-800 font-semibold text-xs border border-red-300 transition-colors duration-200"
                            on:click={() => openModal('delete', user)}
                          >
                            🗑 Supprimer
                          </button>
                        {/if}
                      {/if}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    </div>
  </main>
</div>

<!-- Modal -->
{#if showModal && selectedUser}
  <!-- svelte-ignore a11y-click-events-have-key-events -->
  <!-- svelte-ignore a11y-no-static-element-interactions -->
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" on:click={closeModal} role="dialog" aria-modal="true" tabindex="-1">
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="relative bg-white/90 backdrop-blur-lg rounded-3xl shadow-2xl border-2 border-white/50 max-w-lg w-full p-8 animate-scale-in" on:click|stopPropagation>
      <div class="absolute inset-0 bg-gradient-to-br from-orange-50/50 to-amber-50/50 rounded-3xl -z-10"></div>
      
      <div class="mb-6">
        <h3 class="text-2xl font-bold text-gray-900">
          {#if modalAction === 'approve'}
            Approuver le médecin
          {:else if modalAction === 'reject'}
            Rejeter le médecin
          {:else if modalAction === 'suspend'}
            Suspendre l'utilisateur
          {:else if modalAction === 'delete'}
            Supprimer l'utilisateur
          {/if}
        </h3>
      </div>

      <div class="space-y-4 mb-6">
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
          <span class="text-sm font-bold text-gray-600">Nom:</span>
          <span class="text-sm font-semibold text-gray-900">{selectedUser.first_name} {selectedUser.last_name}</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
          <span class="text-sm font-bold text-gray-600">Email:</span>
          <span class="text-sm font-semibold text-gray-900">{selectedUser.email}</span>
        </div>
        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-xl">
          <span class="text-sm font-bold text-gray-600">Rôle:</span>
          <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold {selectedUser.role.toLowerCase() === 'admin' ? 'bg-gradient-to-r from-orange-100 to-amber-100 text-orange-800' : selectedUser.role.toLowerCase() === 'doctor' ? 'bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-800' : 'bg-gradient-to-r from-purple-100 to-indigo-100 text-purple-800'}">
            {selectedUser.role}
          </span>
        </div>

        {#if modalAction === 'reject' || modalAction === 'suspend'}
          <div class="mt-4">
            <label class="block text-sm font-bold text-gray-900 mb-2" for="actionReason">
              {modalAction === 'reject' ? 'Raison du rejet' : 'Raison de la suspension'}
              {modalAction === 'suspend' ? '(requis)' : '(optionnel)'}
            </label>
            <textarea
              id="actionReason"
              class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium resize-none"
              rows="3"
              bind:value={actionReason}
              placeholder="Entrez la raison..."
            ></textarea>
          </div>
        {/if}

        {#if modalAction === 'approve'}
          <div class="mt-4 p-4 bg-green-50 border-2 border-green-200 rounded-xl">
            <p class="text-sm text-green-800 font-semibold flex items-center gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Ce médecin sera approuvé et pourra se connecter à la plateforme.
            </p>
          </div>
        {:else if modalAction === 'delete'}
          <div class="mt-4 p-4 bg-red-50 border-2 border-red-200 rounded-xl">
            <p class="text-sm text-red-800 font-bold flex items-start gap-2">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Attention : Cette action est irréversible. L'utilisateur sera définitivement supprimé de la base de données.
            </p>
          </div>
        {/if}

        {#if errorMessage}
          <div class="mt-4 bg-red-50/80 backdrop-blur-sm border-2 border-red-200 rounded-xl p-4 shadow-md">
            <div class="flex items-start gap-3">
              <svg class="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              <p class="text-sm text-red-800 font-medium">{errorMessage}</p>
            </div>
          </div>
        {/if}
      </div>

      <div class="flex items-center gap-3">
        <button 
          class="flex-1 px-4 py-3 rounded-xl border-2 border-gray-300 text-gray-700 font-semibold hover:bg-gray-50 hover:border-gray-400 transition-all duration-200" 
          on:click={closeModal} 
          disabled={actionLoading}
        >
          Annuler
        </button>
        <button
          class="group relative flex-1 px-4 py-3 rounded-xl font-bold shadow-md hover:shadow-lg transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed overflow-hidden"
          on:click={confirmAction}
          disabled={actionLoading || (modalAction === 'suspend' && !actionReason)}
        >
          <div class="absolute inset-0 bg-gradient-to-r {modalAction === 'approve' ? 'from-green-500 to-emerald-600' : 'from-red-500 to-rose-600'} opacity-90"></div>
          <div class="absolute inset-0 bg-white/20"></div>
          <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <span class="relative text-white drop-shadow-lg">
            {#if actionLoading}
              Traitement...
            {:else if modalAction === 'approve'}
              Approuver
            {:else if modalAction === 'reject'}
              Rejeter
            {:else if modalAction === 'suspend'}
              Suspendre
            {:else if modalAction === 'delete'}
              Supprimer
            {/if}
          </span>
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  @keyframes scale-in {
    from { opacity: 0; transform: scale(0.95); }
    to { opacity: 1; transform: scale(1); }
  }

  .animate-scale-in {
    animation: scale-in 0.3s ease;
  }

  @keyframes shake {
    0%, 100% { transform: translateX(0); }
    25% { transform: translateX(-6px); }
    75% { transform: translateX(6px); }
  }

  .animate-shake {
    animation: shake 0.35s ease;
  }
</style>
