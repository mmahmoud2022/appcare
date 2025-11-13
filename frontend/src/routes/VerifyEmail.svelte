<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../lib/router';
  import { verifyEmail } from '../lib/api';

  let loading = true;
  let success = false;
  let error = '';
  let message = '';

  onMount(async () => {
    // Get token from URL query parameter
    const params = new URLSearchParams(window.location.search);
    const token = params.get('token');

    if (!token) {
      error = 'Token de vérification manquant. Veuillez utiliser le lien fourni dans votre email.';
      loading = false;
      return;
    }

    try {
      const response = await verifyEmail(token);
      success = true;
      message = response.message || 'Votre email a été vérifié avec succès !';
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      error = err.response?.data?.detail || 'Une erreur est survenue lors de la vérification de votre email.';
      success = false;
    } finally {
      loading = false;
    }
  });
</script>

<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex items-center justify-center px-4 py-12">
  <div class="max-w-md w-full">
    <div class="relative bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl border-2 border-white/50 p-8 hover:shadow-emerald-200/50 transition-all duration-300">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-50/50 to-teal-50/50 rounded-3xl -z-10"></div>
      
      <!-- Logo -->
      <div class="flex justify-center mb-6 animate-slide-down">
        <div class="relative">
          <div class="w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div class="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      <h1 class="text-3xl font-bold text-gray-900 text-center mb-2">
        Vérification Email
      </h1>

      {#if loading}
        <div class="text-center py-8">
          <svg class="animate-spin h-16 w-16 text-emerald-600 mx-auto mb-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          <p class="text-lg text-gray-700 font-medium">Vérification en cours...</p>
        </div>
      {:else if success}
        <div class="text-center py-8">
          <div class="mb-6 animate-scale-in">
            <div class="inline-block p-4 bg-gradient-to-br from-green-100 to-emerald-100 rounded-3xl shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p class="text-2xl text-gray-900 font-bold mb-3">Email vérifié !</p>
          <p class="text-lg text-gray-700 font-medium">{message}</p>
          <div class="mt-6 inline-flex items-center gap-2 text-emerald-600">
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-sm font-semibold">Redirection vers la page de connexion...</p>
          </div>
        </div>
      {:else if error}
        <div class="text-center py-8">
          <div class="mb-6 animate-scale-in">
            <div class="inline-block p-4 bg-gradient-to-br from-red-100 to-rose-100 rounded-3xl shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p class="text-2xl text-gray-900 font-bold mb-3">Échec de la vérification</p>
          <p class="text-gray-700 font-medium mb-8">{error}</p>
          <div class="flex items-center justify-center gap-4">
            <button
              on:click={() => navigate('/login')}
              class="group relative inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
            >
              <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 opacity-90"></div>
              <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
              <span class="relative text-white drop-shadow-lg">Aller à la connexion</span>
            </button>

            <button
              on:click={() => navigate('/resend-verification')}
              class="group relative inline-flex items-center gap-2 px-6 py-3.5 rounded-xl font-bold bg-white border border-gray-200 shadow hover:shadow-md transform hover:scale-102 transition-all duration-300 overflow-hidden"
            >
              <span class="relative text-gray-800">Renvoyer l'email de vérification</span>
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>
