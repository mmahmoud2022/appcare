<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../lib/router';
  import { getStatistics } from '../lib/api';
  import type { StatisticsResponse } from '../lib/api';
  import '../styles/home.css';

  let statistics: StatisticsResponse | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      statistics = await getStatistics();
    } catch (err: any) {
      error = err.response?.data?.detail || 'Erreur lors du chargement des statistiques';
    } finally {
      loading = false;
    }
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50">
  <div class="space-y-24">
    <!-- HERO SECTION -->
    <header class="py-24 px-4 relative">
    <div class="max-w-6xl mx-auto text-center relative z-10">
      <div class="inline-block mb-6 animate-bounce">
        <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto shadow-lg bg-gradient-to-br from-emerald-500 to-teal-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </div>
      </div>
      <h1 class="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-emerald-600 via-teal-600 to-emerald-700 bg-clip-text text-transparent">
        Plateforme Médicale
      </h1>
      <p class="text-xl md:text-2xl mb-12 text-gray-700">
        Connectez-vous avec des professionnels de santé qualifiés et attentifs
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
        <button on:click={() => navigate('/register/patient')} class="px-8 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 text-white font-bold rounded-full hover:shadow-2xl hover:scale-105 transition-all duration-300">
          S'inscrire comme Patient
        </button>
        <button on:click={() => navigate('/register/doctor')} class="px-8 py-4 text-emerald-700 font-semibold rounded-full border-2 border-emerald-500 bg-white hover:bg-emerald-50 hover:shadow-lg transition-all duration-300">
          S'inscrire comme Médecin
        </button>
      </div>

      <div class="mt-6">
        <button on:click={() => navigate('/login')} class="px-6 py-2 text-teal-700 font-medium rounded-full hover:bg-teal-50 transition-all duration-200">
          Déjà inscrit ? Connexion →
        </button>
      </div>
    </div>
  </header>

  <!-- STATISTICS -->
  <section class="py-20 px-4">
    <div class="max-w-6xl mx-auto">
      <h2 class="text-4xl md:text-5xl font-bold text-center mb-4 text-teal-700">
        Notre Communauté
      </h2>
      <p class="text-center text-lg mb-12 text-gray-600">
        Rejoignez des milliers d'utilisateurs qui nous font confiance
      </p>

      {#if loading}
        <div class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-4 border-emerald-600"></div>
        </div>
      {:else if error}
        <div class="bg-red-50 border-2 border-red-300 rounded-2xl shadow-lg p-6 text-center">
          <p class="text-red-700 font-semibold">{error}</p>
        </div>
      {:else if statistics}
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div class="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100 hover:-translate-y-1 hover:shadow-xl hover:border-teal-200 transition-all duration-300">
            <svg class="h-10 w-10 mb-2 text-teal-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            <p class="text-3xl font-bold mb-2 text-gray-900">{statistics.total_users}</p>
            <p class="text-gray-600 font-medium">Utilisateurs Totaux</p>
          </div>

          <div class="bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-2xl shadow-lg p-6 text-white hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-2 border-emerald-400">
            <svg class="h-10 w-10 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
            <p class="text-4xl font-bold mb-2 drop-shadow-md">{statistics.total_doctors}</p>
            <p class="text-white font-semibold">Médecins Disponibles</p>
          </div>

          <div class="bg-gradient-to-br from-purple-500 to-purple-700 rounded-2xl shadow-lg p-6 text-white hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-2 border-purple-400">
            <svg class="h-10 w-10 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            <p class="text-4xl font-bold mb-2 drop-shadow-md">{statistics.total_patients}</p>
            <p class="text-white font-semibold">Patients Inscrits</p>
          </div>

          <div class="bg-gradient-to-br from-rose-500 to-rose-700 rounded-2xl shadow-lg p-6 text-white hover:-translate-y-1 hover:shadow-xl transition-all duration-300 border-2 border-rose-400">
            <svg class="h-10 w-10 mb-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
              stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-4xl font-bold mb-2 drop-shadow-md">{statistics.active_users}</p>
            <p class="text-white font-semibold">Utilisateurs Actifs</p>
          </div>
        </div>
      {/if}
    </div>
  </section>

  <!-- FEATURES -->
  <section class="py-20 px-4 bg-gradient-to-b from-emerald-50/30 to-teal-50/30">
    <div class="max-w-6xl mx-auto text-center">
      <h2 class="text-4xl md:text-5xl font-bold mb-4 text-teal-700">
        Pourquoi Nous Choisir ?
      </h2>
      <p class="text-lg mb-12 text-gray-600">
        Une plateforme moderne conçue pour votre bien-être
      </p>

      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-teal-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg bg-gradient-to-br from-teal-500 to-teal-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none"
              viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold mb-3 text-gray-900">Disponibilité 24/7</h3>
          <p class="text-gray-700">Accédez aux services médicaux à tout moment, où que vous soyez.</p>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-emerald-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg bg-gradient-to-br from-emerald-500 to-emerald-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none"
              viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold mb-3 text-gray-900">Sécurisé & Confidentiel</h3>
          <p class="text-gray-700">Vos données médicales sont protégées avec les normes les plus élevées.</p>
        </div>

        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-purple-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-6 shadow-lg bg-gradient-to-br from-purple-500 to-purple-600">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none"
              viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round"
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <h3 class="text-2xl font-bold mb-3 text-gray-900">Médecins Qualifiés</h3>
          <p class="text-gray-700">Tous nos médecins sont vérifiés et approuvés par notre équipe.</p>
        </div>
      </div>
    </div>
  </section>

  <!-- TESTIMONIALS -->
  <section class="py-20 px-4 bg-gradient-to-br from-emerald-50/50 to-teal-50/50">
    <div class="max-w-6xl mx-auto text-center">
      <h2 class="text-4xl md:text-5xl font-bold mb-12 text-gray-900">Témoignages</h2>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-teal-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <p class="italic text-gray-700 mb-4 text-lg">"Un service exceptionnel ! J'ai pu consulter un médecin en moins de 10 minutes."</p>
          <p class="font-bold text-emerald-700">— Sarah L.</p>
        </div>
        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-emerald-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <p class="italic text-gray-700 mb-4 text-lg">"Très rassurant, les médecins sont à l'écoute et bienveillants."</p>
          <p class="font-bold text-emerald-700">— Ahmed R.</p>
        </div>
        <div class="bg-white rounded-2xl shadow-lg p-8 border-2 border-gray-100 hover:border-purple-200 hover:-translate-y-2 hover:shadow-2xl transition-all duration-300">
          <p class="italic text-gray-700 mb-4 text-lg">"Une plateforme simple, fluide et sécurisée. Je recommande !"</p>
          <p class="font-bold text-emerald-700">— Julie M.</p>
        </div>
      </div>
    </div>
    </section>

    <!-- CTA FINALE -->
    <section class="mx-4 my-20 relative">
      <div class="max-w-4xl mx-auto bg-gradient-to-br from-emerald-500 to-teal-700 rounded-3xl p-12 md:p-16 text-center text-white relative overflow-hidden shadow-2xl">
        <div class="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent pointer-events-none"></div>
        <h2 class="text-3xl md:text-4xl font-bold mb-4 relative z-10">Prêt à prendre soin de votre santé ?</h2>
        <p class="mb-8 text-lg text-white/90 relative z-10">
          Rejoignez notre communauté et accédez à des soins personnalisés dès aujourd'hui.
        </p>
        <button on:click={() => navigate('/register/patient')} class="relative z-10 px-8 py-4 bg-white text-emerald-700 font-bold rounded-full hover:bg-emerald-50 hover:shadow-2xl hover:-translate-y-1 transition-all duration-300 inline-flex items-center gap-2">
          Commencer Maintenant
        </button>
      </div>
    </section>
  </div>
</div>
