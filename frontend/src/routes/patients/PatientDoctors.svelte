<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { fade, fly, scale } from 'svelte/transition';
  import { searchDoctorsForPatient, type DoctorSearchResponse, type DoctorSearchResult } from '../../lib/api-patient';
  import type { ConsultationType, Specialty } from '../../lib/api-doctor';

  const dispatch = createEventDispatcher();

  let loading = false;
  let results: DoctorSearchResult[] = [];
  let total = 0;
  let page = 1;
  let error = '';
  let showFilters = false;
  let selectedDoctor: DoctorSearchResult | null = null;
  
  type DoctorFilters = {
    specialty: '' | Specialty;
    city: string;
    language: string;
    min_price: string;
    max_price: string;
    search: string;
  };

  let filters: DoctorFilters = {
    specialty: '',
    city: '',
    language: '',
    min_price: '',
    max_price: '',
    search: ''
  };

  const specialtyOptions: Array<{ value: '' | Specialty; label: string; icon: string; color: string }> = [
    { value: '', label: 'Toutes les spécialités', icon: '🏥', color: 'from-gray-500 to-gray-600' },
    { value: 'general_practitioner', label: 'Médecine générale', icon: '🩺', color: 'from-blue-500 to-blue-600' },
    { value: 'cardiologist', label: 'Cardiologie', icon: '❤️', color: 'from-red-500 to-pink-600' },
    { value: 'dermatologist', label: 'Dermatologie', icon: '🧴', color: 'from-purple-500 to-purple-600' },
    { value: 'pediatrician', label: 'Pédiatrie', icon: '👶', color: 'from-cyan-500 to-cyan-600' },
    { value: 'gynecologist', label: 'Gynécologie', icon: '🌸', color: 'from-pink-500 to-rose-600' },
    { value: 'psychiatrist', label: 'Psychiatrie', icon: '🧠', color: 'from-indigo-500 to-purple-600' },
    { value: 'ophthalmologist', label: 'Ophtalmologie', icon: '👁️', color: 'from-teal-500 to-cyan-600' },
    { value: 'dentist', label: 'Dentisterie', icon: '🦷', color: 'from-blue-400 to-cyan-500' },
    { value: 'orthopedist', label: 'Orthopédie', icon: '🦴', color: 'from-orange-500 to-amber-600' },
    { value: 'neurologist', label: 'Neurologie', icon: '🧬', color: 'from-violet-500 to-purple-600' },
    { value: 'radiologist', label: 'Radiologie', icon: '📡', color: 'from-emerald-500 to-teal-600' },
    { value: 'surgeon', label: 'Chirurgie', icon: '🔪', color: 'from-red-600 to-rose-700' },
    { value: 'other', label: 'Autres spécialités', icon: '⚕️', color: 'from-gray-500 to-slate-600' }
  ];

  onMount(() => {
    void runSearch();
  });

  const runSearch = async () => {
    loading = true;
    error = '';
    try {
      const response: DoctorSearchResponse = await searchDoctorsForPatient({
        page,
        page_size: 20,
        specialty: filters.specialty || undefined,
        city: filters.city.trim() || undefined,
        language: filters.language.trim() || undefined,
        min_price: filters.min_price ? Number(filters.min_price) : undefined,
        max_price: filters.max_price ? Number(filters.max_price) : undefined,
        search: filters.search.trim() || undefined
      });
      results = response.items;
      total = response.total;
    } catch (err) {
      console.error('Erreur lors de la recherche de praticiens:', err);
      error = err instanceof Error ? err.message : 'Une erreur est survenue lors de la recherche';
    } finally {
      loading = false;
    }
  };

  const consultationLabels: Record<ConsultationType, string> = {
    in_person: 'En cabinet',
    teleconsultation: 'Téléconsultation',
    both: 'Cabinet & Téléconsultation'
  };

  const consultationIcons: Record<ConsultationType, string> = {
    in_person: '🏥',
    teleconsultation: '💻',
    both: '🏥💻'
  };

  const handleBook = (doctor: DoctorSearchResult) => {
    dispatch('book', { doctor });
  };

  const getSpecialtyInfo = (specialty: string) => {
    const info = specialtyOptions.find(s => s.value === specialty);
    return info || { icon: '⚕️', color: 'from-blue-500 to-indigo-600', label: specialty };
  };

  const toggleFilters = () => {
    showFilters = !showFilters;
  };
</script>

<div class="space-y-6">
  <!-- Hero Header with Gradient -->
  <div class="relative overflow-hidden bg-gradient-to-br from-blue-500 via-indigo-600 to-purple-600 rounded-3xl shadow-2xl p-8 md:p-12">
    <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full -mr-32 -mt-32 blur-3xl"></div>
    <div class="absolute bottom-0 left-0 w-96 h-96 bg-white/5 rounded-full -ml-48 -mb-48 blur-3xl"></div>
    <div class="relative z-10">
      <div class="flex items-center gap-4 mb-4">
        <div class="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-xl animate-float">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div>
          <h2 class="text-3xl md:text-4xl font-bold text-white drop-shadow-lg">Trouvez votre praticien</h2>
          <p class="text-blue-100 text-sm md:text-base mt-1">Des milliers de professionnels de santé à votre écoute</p>
        </div>
      </div>
      
      <!-- Quick Search Bar -->
      <div class="mt-6 bg-white/95 backdrop-blur-sm rounded-2xl shadow-2xl p-2 flex items-center gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-gray-400 ml-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          bind:value={filters.search}
          on:keydown={(e) => e.key === 'Enter' && runSearch()}
          placeholder="Recherchez par nom, spécialité, ville..."
          class="flex-1 px-2 py-3 bg-transparent border-none focus:outline-none text-gray-900 placeholder-gray-500 font-medium"
        />
        <button
          on:click={runSearch}
          class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-semibold shadow-lg hover:shadow-xl hover:scale-105 flex items-center gap-2"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Rechercher
        </button>
      </div>
      
      <!-- Advanced Filters Toggle -->
      <div class="mt-4 flex justify-end">
        <button
          on:click={toggleFilters}
          class="px-4 py-2 bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white rounded-xl transition-all border border-white/20 flex items-center gap-2 font-medium"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
          </svg>
          {showFilters ? 'Masquer les filtres' : 'Filtres avancés'}
        </button>
      </div>
    </div>
  </div>

  <!-- Advanced Filters Panel -->
  {#if showFilters}
    <div transition:fly={{ y: -20, duration: 300 }} class="bg-white rounded-2xl shadow-xl border border-gray-200 overflow-hidden">
      <div class="bg-gradient-to-r from-gray-50 to-blue-50/30 px-6 py-4 border-b border-gray-200">
        <h3 class="font-bold text-gray-900 flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          Affinez votre recherche
        </h3>
      </div>
      <div class="p-6">
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          <div class="space-y-2">
            <label for="doctor-specialty-filter" class="block text-sm font-bold text-gray-700 flex items-center gap-2">
              <span class="text-lg">🎯</span>
              Spécialité
            </label>
            <select
              id="doctor-specialty-filter"
              bind:value={filters.specialty}
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all bg-white font-medium"
            >
              {#each specialtyOptions as option}
                <option value={option.value}>{option.icon} {option.label}</option>
              {/each}
            </select>
          </div>
          
          <div class="space-y-2">
            <label for="doctor-city-filter" class="block text-sm font-bold text-gray-700 flex items-center gap-2">
              <span class="text-lg">📍</span>
              Ville
            </label>
            <input
              id="doctor-city-filter"
              type="text"
              bind:value={filters.city}
              placeholder="Paris, Lyon, Marseille..."
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium placeholder-gray-400"
            />
          </div>
          
          <div class="space-y-2">
            <label for="doctor-language-filter" class="block text-sm font-bold text-gray-700 flex items-center gap-2">
              <span class="text-lg">🗣️</span>
              Langue
            </label>
            <input
              id="doctor-language-filter"
              type="text"
              bind:value={filters.language}
              placeholder="Français, Anglais, Arabe..."
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium placeholder-gray-400"
            />
          </div>
          
          <div class="space-y-2">
            <label for="doctor-min-price" class="block text-sm font-bold text-gray-700 flex items-center gap-2">
              <span class="text-lg">💰</span>
              Prix minimum (€)
            </label>
            <input
              id="doctor-min-price"
              type="number"
              min="0"
              bind:value={filters.min_price}
              placeholder="0"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium placeholder-gray-400"
            />
          </div>
          
          <div class="space-y-2">
            <label for="doctor-max-price" class="block text-sm font-bold text-gray-700 flex items-center gap-2">
              <span class="text-lg">💵</span>
              Prix maximum (€)
            </label>
            <input
              id="doctor-max-price"
              type="number"
              min="0"
              bind:value={filters.max_price}
              placeholder="200"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium placeholder-gray-400"
            />
          </div>
        </div>
        
        <div class="flex justify-end gap-3 mt-6 pt-6 border-t border-gray-200">
          <button
            on:click={() => {
              filters = { specialty: '', city: '', language: '', min_price: '', max_price: '', search: '' };
              page = 1;
              void runSearch();
            }}
            class="px-6 py-3 border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-gray-400 transition-all font-semibold"
          >
            Réinitialiser
          </button>
          <button
            on:click={() => {
              page = 1;
              void runSearch();
            }}
            class="px-8 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-bold shadow-lg hover:shadow-xl hover:scale-105"
          >
            Appliquer les filtres
          </button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Results Section -->
  {#if loading}
    <div class="text-center py-20" transition:fade={{ duration: 200 }}>
      <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full shadow-2xl animate-pulse">
        <div class="animate-spin rounded-full h-16 w-16 border-t-4 border-b-4 border-white"></div>
      </div>
      <p class="mt-6 text-gray-700 font-semibold text-lg">Recherche en cours...</p>
      <p class="mt-2 text-gray-500 text-sm">Nous trouvons les meilleurs praticiens pour vous</p>
    </div>
  
  {:else if error}
    <div transition:fly={{ y: 20, duration: 300 }} class="bg-gradient-to-r from-red-50 to-pink-50 border-2 border-red-300 rounded-2xl p-6 shadow-lg">
      <div class="flex items-start gap-4">
        <div class="flex-shrink-0">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 class="font-bold text-red-900 text-lg">Une erreur s'est produite</h3>
          <p class="text-red-700 mt-1">{error}</p>
          <button
            on:click={runSearch}
            class="mt-4 px-5 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all font-semibold shadow-md"
          >
            Réessayer
          </button>
        </div>
      </div>
    </div>
  
  {:else if results.length === 0}
    <div transition:fly={{ y: 20, duration: 300 }} class="text-center py-16 bg-gradient-to-br from-gray-50 to-blue-50/30 rounded-3xl border-2 border-dashed border-gray-300 shadow-inner">
      <div class="w-24 h-24 bg-gradient-to-br from-gray-400 to-gray-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      </div>
      <h3 class="text-2xl font-bold text-gray-900 mb-3">Aucun praticien trouvé</h3>
      <p class="text-gray-600 mb-2">Nous n'avons pas trouvé de médecin correspondant à vos critères.</p>
      <p class="text-sm text-gray-500 mb-6">Essayez de modifier vos filtres ou d'élargir votre recherche.</p>
      <button
        on:click={() => {
          filters = { specialty: '', city: '', language: '', min_price: '', max_price: '', search: '' };
          page = 1;
          void runSearch();
        }}
        class="px-6 py-3 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all font-bold shadow-lg hover:shadow-xl hover:scale-105"
      >
        Réinitialiser la recherche
      </button>
    </div>
  
  {:else}
    <div>
      <!-- Results Counter -->
      <div class="mb-6 flex items-center justify-between">
        <div>
          <p class="text-sm text-gray-600">
            <span class="font-bold text-gray-900 text-lg">{total}</span> praticien{total > 1 ? 's' : ''} trouvé{total > 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <!-- Doctor Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each results as doctor, i}
          <div 
            transition:fly={{ y: 30, duration: 400, delay: i * 50 }}
            class="group bg-white border-2 border-gray-200 rounded-2xl p-6 hover:shadow-2xl hover:border-blue-300 transition-all duration-300 hover:-translate-y-1"
          >
            <!-- Doctor Header -->
            <div class="flex items-start gap-4 mb-4">
              <div class="flex-shrink-0">
                <div class="w-16 h-16 bg-gradient-to-br {getSpecialtyInfo(doctor.specialty || '').color} rounded-2xl flex items-center justify-center text-white text-xl font-bold shadow-lg group-hover:scale-110 transition-transform duration-300">
                  {doctor.first_name?.[0]?.toUpperCase()}{doctor.last_name?.[0]?.toUpperCase()}
                </div>
              </div>
              <div class="flex-1 min-w-0">
                <h3 class="text-lg font-bold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
                  Dr. {doctor.first_name} {doctor.last_name}
                </h3>
                {#if doctor.specialty}
                  <div class="mt-1 inline-flex items-center gap-1.5 px-3 py-1 bg-gradient-to-r {getSpecialtyInfo(doctor.specialty).color} rounded-full shadow-sm">
                    <span class="text-sm">{getSpecialtyInfo(doctor.specialty).icon}</span>
                    <span class="text-xs font-semibold text-white">{doctor.specialty}</span>
                  </div>
                {/if}
              </div>
            </div>

            <!-- Accepts New Patients Badge -->
            <div class="mb-3">
              <span class={`inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-lg ${doctor.accepts_new_patients ? 'bg-gradient-to-r from-green-500 to-emerald-600 text-white shadow-md' : 'bg-gray-100 text-gray-600'}`}>
                {doctor.accepts_new_patients ? '✓ Accepte de nouveaux patients' : '⏳ Liste d\'attente'}
              </span>
            </div>

            <!-- Location -->
            {#if doctor.city}
              <div class="flex items-center gap-2 text-gray-600 mb-3">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span class="text-sm font-medium">{doctor.city}</span>
              </div>
            {/if}

            <!-- Consultation Info -->
            <div class="mb-3 flex items-center gap-2 text-sm text-gray-600">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="font-medium">{consultationIcons[doctor.consultation_types]} {consultationLabels[doctor.consultation_types]} · {doctor.consultation_duration} min</span>
            </div>

            <!-- Languages -->
            {#if doctor.languages && doctor.languages.length > 0}
              <div class="mb-4">
                <div class="flex flex-wrap gap-2">
                  {#each doctor.languages.slice(0, 3) as language}
                    <span class="px-3 py-1 bg-gradient-to-r from-blue-50 to-indigo-50 text-blue-700 text-xs font-semibold rounded-lg border border-blue-200">
                      🗣️ {language}
                    </span>
                  {/each}
                  {#if doctor.languages.length > 3}
                    <span class="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-semibold rounded-lg">
                      +{doctor.languages.length - 3}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}

            <!-- Divider -->
            <div class="border-t border-gray-200 my-4"></div>

            <!-- Price and Rating -->
            <div class="flex items-center justify-between mb-4">
              {#if doctor.consultation_price}
                <div class="flex items-center gap-2">
                  <div class="w-10 h-10 bg-gradient-to-br from-green-500 to-emerald-600 rounded-xl flex items-center justify-center shadow-md">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                    </svg>
                  </div>
                  <div>
                    <p class="text-xs text-gray-500 font-medium">Tarif</p>
                    <p class="text-lg font-bold text-gray-900">{doctor.consultation_price.toLocaleString('fr-FR')} XOF</p>
                  </div>
                </div>
              {/if}
              <div class="text-right">
                <div class="flex items-center gap-1">
                  <span class="text-2xl font-bold text-gray-900">
                    {doctor.average_rating ? doctor.average_rating.toFixed(1) : '0.0'}
                  </span>
                  <span class="text-2xl text-yellow-500">★</span>
                </div>
                <p class="text-xs text-gray-500">
                  {doctor.total_reviews || 0} {doctor.total_reviews === 1 ? 'avis' : 'avis'}
                </p>
              </div>
            </div>

            <!-- Action Button -->
            <button
              on:click={() => handleBook(doctor)}
              class="w-full px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all duration-300 font-bold shadow-lg hover:shadow-xl group-hover:scale-105 flex items-center justify-center gap-2"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              Réserver un rendez-vous
            </button>
          </div>
        {/each}
      </div>

      <!-- Pagination -->
      {#if total > 20}
        <div class="mt-10 flex items-center justify-center gap-2" transition:fade={{ delay: 300 }}>
          <button
            on:click={() => {
              if (page > 1) {
                page--;
                void runSearch();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }
            }}
            disabled={page === 1}
            class="px-4 py-2 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold flex items-center gap-2 shadow-md hover:shadow-lg"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
            </svg>
            Précédent
          </button>
          
          <div class="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-xl font-bold shadow-lg">
            <span>Page {page}</span>
            <span class="text-blue-200">sur</span>
            <span>{Math.ceil(total / 20)}</span>
          </div>
          
          <button
            on:click={() => {
              if (page < Math.ceil(total / 20)) {
                page++;
                void runSearch();
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }
            }}
            disabled={page >= Math.ceil(total / 20)}
            class="px-4 py-2 bg-white border-2 border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 hover:border-blue-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-semibold flex items-center gap-2 shadow-md hover:shadow-lg"
          >
            Suivant
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  @keyframes float {
    0%, 100% {
      transform: translateY(0px);
    }
    50% {
      transform: translateY(-10px);
    }
  }
  
  :global(.animate-float) {
    animation: float 3s ease-in-out infinite;
  }
</style>
