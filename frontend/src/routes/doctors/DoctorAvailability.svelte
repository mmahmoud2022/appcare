<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    getDoctorSchedule,
    getCurrentDoctorProfile,
    createScheduleEntry, 
    deleteScheduleEntry,
    updateScheduleEntry,
    getBlockedSlots,
    createBlockedSlot,
    deleteBlockedSlot,
    type DoctorScheduleEntry,
    type ScheduleEntryCreate,
    type ScheduleEntryUpdate,
    type ConsultationType,
    type BlockedSlot,
    type BlockedSlotCreate
  } from '../../lib/api-doctor';
  
  let scheduleEntries: DoctorScheduleEntry[] = [];
  let blockedSlots: BlockedSlot[] = [];
  let loading = true;
  let loadingBlocked = false;
  let error: string | null = null;
  let showCreateModal = false;
  let showBlockModal = false;
  let creating = false;
  let blocking = false;
  let updating = false;
  let doctorId: number | null = null;
  let showEditModal = false;
  let selectedEntry: DoctorScheduleEntry | null = null;
  let activeTab: 'recurring' | 'blocked' = 'recurring';
  let editEntry: ScheduleEntryUpdate = {
    day_of_week: 1,
    start_time: '09:00',
    end_time: '17:00',
    consultation_type: 'in_person',
    slot_duration: 30,
    break_duration: 0,
    location: ''
  };

  let newEntry: ScheduleEntryCreate = {
    day_of_week: 1,
    start_time: '09:00',
    end_time: '17:00',
    consultation_type: 'in_person',
    slot_duration: 30,
    break_duration: 0,
    location: ''
  };

  let newBlockedSlot: BlockedSlotCreate = {
    start_datetime: '',
    end_datetime: '',
    reason: ''
  };

  const daysOfWeek = [
    { value: 1, label: 'Lundi' },
    { value: 2, label: 'Mardi' },
    { value: 3, label: 'Mercredi' },
    { value: 4, label: 'Jeudi' },
    { value: 5, label: 'Vendredi' },
    { value: 6, label: 'Samedi' },
    { value: 0, label: 'Dimanche' }
  ];

  const consultationTypes: { value: ConsultationType; label: string }[] = [
    { value: 'in_person', label: 'En personne' },
    { value: 'teleconsultation', label: 'Téléconsultation' },
    { value: 'both', label: 'Les deux' }
  ];

  onMount(async () => {
    await loadScheduleEntries();
    await loadBlockedSlots();
  });

  const loadScheduleEntries = async () => {
    loading = true;
    error = null;
    try {
      // Get doctor ID first if not already loaded
      if (!doctorId) {
        const profile = await getCurrentDoctorProfile();
        doctorId = profile.id;
      }
      
      scheduleEntries = await getDoctorSchedule(doctorId);
      // Sort by day and time
      scheduleEntries.sort((a, b) => {
        if (a.day_of_week !== b.day_of_week) {
          return a.day_of_week - b.day_of_week;
        }
        return a.start_time.localeCompare(b.start_time);
      });
    } catch (err: any) {
      console.error('Error loading schedule entries:', err);
      error = 'Erreur lors du chargement des disponibilités';
    } finally {
      loading = false;
    }
  };

  const loadBlockedSlots = async () => {
    loadingBlocked = true;
    try {
      blockedSlots = await getBlockedSlots();
      // Sort by date
      blockedSlots.sort((a, b) => 
        new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime()
      );
    } catch (err: any) {
      console.error('Error loading blocked slots:', err);
    } finally {
      loadingBlocked = false;
    }
  };

  const getDayLabel = (day: number) => {
    return daysOfWeek.find(d => d.value === day)?.label || '';
  };

  const getConsultationTypeLabel = (type: string) => {
    return consultationTypes.find(t => t.value === type)?.label || type;
  };

  const getConsultationTypeIcon = (type: string) => {
    switch (type) {
      case 'in_person':
        return '🏥';
      case 'teleconsultation':
        return '💻';
      case 'both':
        return '🏥💻';
      default:
        return '📅';
    }
  };

  const handleCreate = async () => {
    creating = true;
    try {
      const payload = {
        ...newEntry,
        slot_duration: Number(newEntry.slot_duration),
        break_duration: Number(newEntry.break_duration ?? 0) || 0,
        location: newEntry.location?.trim() || undefined
      };
      await createScheduleEntry(payload);
      showCreateModal = false;
      resetForm();
      await loadScheduleEntries();
    } catch (err: any) {
      console.error('Error creating schedule entry:', err);
      // Surface backend validation / error details when available to help debugging
      const detail = err?.response?.data?.detail || err?.response?.data || err?.message;
      alert(detail || 'Erreur lors de la création de la disponibilité');
    } finally {
      creating = false;
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette disponibilité ?')) return;
    
    try {
      await deleteScheduleEntry(id);
      await loadScheduleEntries();
    } catch (err: any) {
      console.error('Error deleting schedule entry:', err);
      alert('Erreur lors de la suppression');
    }
  };

  const openEditModal = (entry: DoctorScheduleEntry) => {
    selectedEntry = entry;
    editEntry = {
      day_of_week: entry.day_of_week,
      start_time: entry.start_time.slice(0, 5),
      end_time: entry.end_time.slice(0, 5),
      consultation_type: entry.consultation_type,
      slot_duration: entry.slot_duration,
      break_duration: entry.break_duration,
      location: entry.location || ''
    };
    showEditModal = true;
  };

  const closeEditModal = () => {
    showEditModal = false;
    selectedEntry = null;
    resetEditForm();
  };

  const handleUpdate = async () => {
    if (!selectedEntry) return;
    updating = true;
    try {
      const payload = {
        ...editEntry,
        slot_duration: editEntry.slot_duration !== undefined ? Number(editEntry.slot_duration) : undefined,
        break_duration: editEntry.break_duration !== undefined ? Number(editEntry.break_duration) : undefined,
        location: editEntry.location?.trim() || undefined
      };
      await updateScheduleEntry(selectedEntry.id, payload);
      closeEditModal();
      await loadScheduleEntries();
    } catch (err: any) {
      console.error('Error updating schedule entry:', err);
      const detail = err?.response?.data?.detail || err?.response?.data || err?.message;
      alert(detail || 'Erreur lors de la mise à jour de la disponibilité');
    } finally {
      updating = false;
    }
  };

  const resetForm = () => {
    newEntry = {
      day_of_week: 1,
      start_time: '09:00',
      end_time: '17:00',
      consultation_type: 'in_person',
      slot_duration: 30,
      break_duration: 0,
      location: ''
    };
  };

  const resetEditForm = () => {
    editEntry = {
      day_of_week: 1,
      start_time: '09:00',
      end_time: '17:00',
      consultation_type: 'in_person',
      slot_duration: 30,
      break_duration: 0,
      location: ''
    };
  };

  const openCreateModal = () => {
    resetForm();
    showCreateModal = true;
  };

  const openBlockModal = () => {
    resetBlockForm();
    showBlockModal = true;
  };

  const resetBlockForm = () => {
    // Set default to tomorrow, 9 AM to 5 PM
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    const start = new Date(tomorrow);
    start.setHours(9, 0, 0, 0);
    const end = new Date(tomorrow);
    end.setHours(17, 0, 0, 0);
    
    newBlockedSlot = {
      start_datetime: start.toISOString().slice(0, 16),
      end_datetime: end.toISOString().slice(0, 16),
      reason: ''
    };
  };

  const handleCreateBlockedSlot = async () => {
    blocking = true;
    try {
      await createBlockedSlot(newBlockedSlot);
      showBlockModal = false;
      resetBlockForm();
      await loadBlockedSlots();
    } catch (err: any) {
      console.error('Error creating blocked slot:', err);
      alert(err.response?.data?.detail || 'Erreur lors du blocage du créneau');
    } finally {
      blocking = false;
    }
  };

  const handleDeleteBlockedSlot = async (id: number) => {
    if (!confirm('Êtes-vous sûr de vouloir débloquer ce créneau ?')) return;
    
    try {
      await deleteBlockedSlot(id);
      await loadBlockedSlots();
    } catch (err: any) {
      console.error('Error deleting blocked slot:', err);
      alert('Erreur lors de la suppression');
    }
  };

  const formatDateTime = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('fr-FR', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatDateTimeShort = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Regrouper les entrées de planning par jour
  $: scheduleByDay = scheduleEntries.reduce((acc, entry) => {
    if (!acc[entry.day_of_week]) {
      acc[entry.day_of_week] = [];
    }
    acc[entry.day_of_week].push(entry);
    return acc;
  }, {} as Record<number, DoctorScheduleEntry[]>);
</script>

<div class="space-y-6">
  <!-- Header avec onglets -->
  <div class="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
    <div class="border-b border-gray-200">
      <nav class="flex">
        <button
          on:click={() => activeTab = 'recurring'}
          class="flex-1 px-6 py-4 text-sm font-semibold border-b-2 transition-colors {activeTab === 'recurring' ? 'border-emerald-500 text-emerald-600 bg-emerald-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'}"
        >
          📅 Créneaux récurrents
        </button>
        <button
          on:click={() => activeTab = 'blocked'}
          class="flex-1 px-6 py-4 text-sm font-semibold border-b-2 transition-colors {activeTab === 'blocked' ? 'border-red-500 text-red-600 bg-red-50/50' : 'border-transparent text-gray-500 hover:text-gray-700 hover:bg-gray-50'}"
        >
          🚫 Créneaux bloqués
          {#if blockedSlots.length > 0}
            <span class="ml-2 px-2 py-0.5 text-xs bg-red-100 text-red-800 rounded-full">{blockedSlots.length}</span>
          {/if}
        </button>
      </nav>
    </div>

    <div class="p-6">
      <!-- Recurring Tab -->
      {#if activeTab === 'recurring'}
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold text-gray-900">Disponibilités hebdomadaires</h2>
            <button
              on:click={openCreateModal}
              class="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
              </svg>
              Ajouter un créneau
            </button>
          </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{error}</p>
    </div>
  {:else if scheduleEntries.length === 0}
    <div class="text-center py-12 bg-white rounded-lg border border-gray-200">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <p class="text-gray-600 mb-4">Aucune disponibilité configurée</p>
      <button
        on:click={openCreateModal}
        class="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
      >
        Ajouter votre première disponibilité
      </button>
    </div>
  {:else}
    <!-- Calendar View -->
    <div class="grid grid-cols-1 gap-6">
      {#each daysOfWeek as day}
        {#if scheduleByDay[day.value]}
          <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <div class="bg-gradient-to-r from-emerald-50 to-teal-50 px-6 py-4 border-b border-gray-200">
              <h3 class="text-lg font-semibold text-gray-900">{day.label}</h3>
            </div>
            <div class="p-6">
              <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {#each scheduleByDay[day.value] as entry}
                    <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                    <div class="flex items-start justify-between mb-3">
                      <div class="flex items-center gap-2">
                          <span class="text-2xl">{getConsultationTypeIcon(entry.consultation_type)}</span>
                        <div>
                          <p class="font-medium text-gray-900">
                              {entry.start_time.slice(0, 5)} - {entry.end_time.slice(0, 5)}
                          </p>
                          <p class="text-sm text-gray-600">
                              {getConsultationTypeLabel(entry.consultation_type)}
                          </p>
                        </div>
                      </div>
                    </div>
                      <div class="text-sm text-gray-500 space-y-1 mb-3">
                        <p>Créneau : {entry.slot_duration} min</p>
                        {#if entry.break_duration}
                          <p>Pause entre créneaux : {entry.break_duration} min</p>
                        {/if}
                        {#if entry.location}
                          <p>Lieu : {entry.location}</p>
                        {/if}
                      </div>
                    <div class="flex gap-2">
                      <button
                          on:click={() => openEditModal(entry)}
                        class="flex-1 px-3 py-2 text-sm text-emerald-600 border border-emerald-200 rounded-lg hover:bg-emerald-50 transition-colors"
                      >
                        Modifier
                      </button>
                      <button
                          on:click={() => handleDelete(entry.id)}
                        class="flex-1 px-3 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition-colors"
                      >
                        Supprimer
                      </button>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          </div>
        {/if}
      {/each}
    </div>
  {/if}
        </div>
      {:else}
        <!-- Blocked Slots Tab -->
        <div class="space-y-4">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-bold text-gray-900">Créneaux bloqués</h2>
            <button
              on:click={openBlockModal}
              class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors flex items-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
              </svg>
              Bloquer un créneau
            </button>
          </div>

          {#if loadingBlocked}
            <div class="flex items-center justify-center py-12">
              <svg class="animate-spin h-8 w-8 text-red-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          {:else if blockedSlots.length === 0}
            <div class="text-center py-12 bg-white rounded-lg border border-gray-200">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <p class="text-gray-600 mb-4">Aucun créneau bloqué</p>
              <button
                on:click={openBlockModal}
                class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
              >
                Bloquer votre premier créneau
              </button>
            </div>
          {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              {#each blockedSlots as slot}
                <div class="border-2 border-red-200 bg-red-50/50 rounded-lg p-5 hover:shadow-md transition-shadow">
                  <div class="flex items-start justify-between mb-3">
                    <div class="flex-1">
                      <p class="text-sm font-semibold text-red-900 mb-1">
                        📅 {formatDateTime(slot.start_datetime)}
                      </p>
                      <p class="text-sm text-red-700">
                        ⏱️ Jusqu'à: {formatDateTimeShort(slot.end_datetime)}
                      </p>
                      {#if slot.reason}
                        <p class="text-sm text-gray-600 mt-2 italic">
                          💬 {slot.reason}
                        </p>
                      {/if}
                    </div>
                    <button
                      on:click={() => handleDeleteBlockedSlot(slot.id)}
                      class="px-3 py-2 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-100 transition-colors"
                      title="Débloquer"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  </div>
</div>

<!-- Create Modal -->
{#if showCreateModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl max-w-lg w-full">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-bold text-gray-900">Ajouter une disponibilité</h3>
          <button on:click={() => showCreateModal = false} class="text-gray-400 hover:text-gray-600" title="Fermer">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span class="sr-only">Fermer</span>
          </button>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label for="day-select" class="block text-sm font-medium text-gray-700 mb-2">Jour de la semaine</label>
          <select
            id="day-select"
            bind:value={newEntry.day_of_week}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          >
            {#each daysOfWeek as day}
              <option value={day.value}>{day.label}</option>
            {/each}
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="start-time" class="block text-sm font-medium text-gray-700 mb-2">Heure de début</label>
            <input
              id="start-time"
              type="time"
              bind:value={newEntry.start_time}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label for="end-time" class="block text-sm font-medium text-gray-700 mb-2">Heure de fin</label>
            <input
              id="end-time"
              type="time"
              bind:value={newEntry.end_time}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="slot-duration" class="block text-sm font-medium text-gray-700 mb-2">Durée d'un créneau (minutes)</label>
            <input
              id="slot-duration"
              type="number"
              min="5"
              step="5"
              bind:value={newEntry.slot_duration}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label for="break-duration" class="block text-sm font-medium text-gray-700 mb-2">Pause entre créneaux (minutes)</label>
            <input
              id="break-duration"
              type="number"
              min="0"
              step="5"
              bind:value={newEntry.break_duration}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
        <div>
          <label for="consultation-type" class="block text-sm font-medium text-gray-700 mb-2">Type de consultation</label>
          <select
            id="consultation-type"
            bind:value={newEntry.consultation_type}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          >
            {#each consultationTypes as type}
              <option value={type.value}>{getConsultationTypeIcon(type.value)} {type.label}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for="location" class="block text-sm font-medium text-gray-700 mb-2">Lieu (optionnel)</label>
          <input
            id="location"
            type="text"
            bind:value={newEntry.location}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            placeholder="Cabinet, téléconsultation, etc."
          />
        </div>
      </div>
      <div class="p-6 border-t border-gray-200 flex gap-3">
        <button
          on:click={() => showCreateModal = false}
          class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          disabled={creating}
        >
          Annuler
        </button>
        <button
          on:click={handleCreate}
          class="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
          disabled={creating}
        >
          {creating ? 'Création...' : 'Créer'}
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showEditModal && selectedEntry}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl max-w-lg w-full">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-bold text-gray-900">Modifier la disponibilité</h3>
          <button on:click={closeEditModal} class="text-gray-400 hover:text-gray-600" title="Fermer">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span class="sr-only">Fermer</span>
          </button>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <div>
          <label for="edit-day-select" class="block text-sm font-medium text-gray-700 mb-2">Jour de la semaine</label>
          <select
            id="edit-day-select"
            bind:value={editEntry.day_of_week}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          >
            {#each daysOfWeek as day}
              <option value={day.value}>{day.label}</option>
            {/each}
          </select>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="edit-start-time" class="block text-sm font-medium text-gray-700 mb-2">Heure de début</label>
            <input
              id="edit-start-time"
              type="time"
              bind:value={editEntry.start_time}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label for="edit-end-time" class="block text-sm font-medium text-gray-700 mb-2">Heure de fin</label>
            <input
              id="edit-end-time"
              type="time"
              bind:value={editEntry.end_time}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="edit-slot-duration" class="block text-sm font-medium text-gray-700 mb-2">Durée d'un créneau (minutes)</label>
            <input
              id="edit-slot-duration"
              type="number"
              min="5"
              step="5"
              bind:value={editEntry.slot_duration}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
          <div>
            <label for="edit-break-duration" class="block text-sm font-medium text-gray-700 mb-2">Pause entre créneaux (minutes)</label>
            <input
              id="edit-break-duration"
              type="number"
              min="0"
              step="5"
              bind:value={editEntry.break_duration}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>
        <div>
          <label for="edit-consultation-type" class="block text-sm font-medium text-gray-700 mb-2">Type de consultation</label>
          <select
            id="edit-consultation-type"
            bind:value={editEntry.consultation_type}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          >
            {#each consultationTypes as type}
              <option value={type.value}>{getConsultationTypeIcon(type.value)} {type.label}</option>
            {/each}
          </select>
        </div>
        <div>
          <label for="edit-location" class="block text-sm font-medium text-gray-700 mb-2">Lieu (optionnel)</label>
          <input
            id="edit-location"
            type="text"
            bind:value={editEntry.location}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
          />
        </div>
      </div>
      <div class="p-6 border-t border-gray-200 flex gap-3">
        <button
          on:click={closeEditModal}
          class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          disabled={updating}
        >
          Annuler
        </button>
        <button
          on:click={handleUpdate}
          class="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
          disabled={updating}
        >
          {updating ? 'Enregistrement...' : 'Enregistrer'}
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Block Slot Modal -->
{#if showBlockModal}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl max-w-lg w-full">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <h3 class="text-xl font-bold text-gray-900">Bloquer un créneau</h3>
          <button on:click={() => showBlockModal = false} class="text-gray-400 hover:text-gray-600" title="Fermer">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      <div class="p-6 space-y-4">
        <div class="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <p class="text-sm text-amber-800">
            💡 Bloquez un créneau pour indiquer une indisponibilité ponctuelle (congés, formation, etc.). 
            Les patients ne pourront pas réserver pendant cette période.
          </p>
        </div>
        <div>
          <label for="block-start" class="block text-sm font-medium text-gray-700 mb-2">Date et heure de début</label>
          <input
            id="block-start"
            type="datetime-local"
            bind:value={newBlockedSlot.start_datetime}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
          />
        </div>
        <div>
          <label for="block-end" class="block text-sm font-medium text-gray-700 mb-2">Date et heure de fin</label>
          <input
            id="block-end"
            type="datetime-local"
            bind:value={newBlockedSlot.end_datetime}
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
          />
        </div>
        <div>
          <label for="block-reason" class="block text-sm font-medium text-gray-700 mb-2">Raison (optionnel)</label>
          <input
            id="block-reason"
            type="text"
            bind:value={newBlockedSlot.reason}
            placeholder="Ex: Congés, Formation, Rendez-vous personnel..."
            class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500"
          />
        </div>
      </div>
      <div class="p-6 border-t border-gray-200 flex gap-3">
        <button
          on:click={() => showBlockModal = false}
          class="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          disabled={blocking}
        >
          Annuler
        </button>
        <button
          on:click={handleCreateBlockedSlot}
          class="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
          disabled={blocking}
        >
          {blocking ? 'Blocage...' : 'Bloquer le créneau'}
        </button>
      </div>
    </div>
  </div>
{/if}
