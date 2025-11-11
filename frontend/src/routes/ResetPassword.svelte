<script lang="ts">
  import { onMount } from 'svelte';
  import { navigate } from '../lib/router';
  import { resetPassword } from '../lib/api';

  let token = '';
  let newPassword = '';
  let confirmPassword = '';
  let loading = false;
  let success = false;
  let error = '';

  onMount(() => {
    // Get token from URL query parameter
    const params = new URLSearchParams(window.location.search);
    const urlToken = params.get('token');
    
    if (!urlToken) {
      error = 'Token de réinitialisation manquant. Veuillez utiliser le lien fourni dans votre email.';
    } else {
      token = urlToken;
    }
  });

  async function handleSubmit() {
    error = '';

    if (!token) {
      error = 'Token de réinitialisation manquant.';
      return;
    }

    if (!validatePassword(newPassword)) {
      error = 'Le mot de passe doit contenir au moins 8 caractères.';
      return;
    }

    if (newPassword !== confirmPassword) {
      error = 'Les mots de passe ne correspondent pas.';
      return;
    }

    loading = true;

    try {
      const response = await resetPassword(token, newPassword);
      success = true;
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (err: any) {
      error = err.response?.data?.detail || 'Une erreur est survenue lors de la réinitialisation du mot de passe.';
      success = false;
    } finally {
      loading = false;
    }
  }

  function validatePassword(password: string): boolean {
    return password.length >= 8;
  }
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
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
          </div>
          <div class="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      <h1 class="text-3xl font-bold text-gray-900 text-center mb-2">
        Réinitialiser le mot de passe
      </h1>
      <p class="text-lg text-gray-700 font-medium text-center mb-6">
        Choisissez un nouveau mot de passe sécurisé
      </p>

      {#if success}
        <div class="text-center py-8">
          <div class="mb-6 animate-scale-in">
            <div class="inline-block p-4 bg-gradient-to-br from-green-100 to-emerald-100 rounded-3xl shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <p class="text-2xl text-gray-900 font-bold mb-3">Mot de passe réinitialisé !</p>
          <p class="text-lg text-gray-700 font-medium">Votre mot de passe a été modifié avec succès.</p>
          <div class="mt-6 inline-flex items-center gap-2 text-emerald-600">
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <p class="text-sm font-semibold">Redirection vers la page de connexion...</p>
          </div>
        </div>
      {:else}
        <form on:submit|preventDefault={handleSubmit} class="space-y-6">
          {#if error}
            <div class="bg-red-50/80 backdrop-blur-sm border-2 border-red-200 rounded-xl p-4 shadow-md">
              <div class="flex items-start gap-3">
                <svg class="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                </svg>
                <p class="text-sm text-red-800 font-medium">{error}</p>
              </div>
            </div>
          {/if}

          <div>
            <label for="newPassword" class="block text-sm font-bold text-gray-900 mb-2">
              Nouveau mot de passe
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <input
                type="password"
                id="newPassword"
                bind:value={newPassword}
                required
                minlength="8"
                class="w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
                placeholder="••••••••"
                disabled={loading || !token}
              />
            </div>
            <p class="text-xs text-gray-600 font-medium mt-2 ml-1">Minimum 8 caractères</p>
          </div>

          <div>
            <label for="confirmPassword" class="block text-sm font-bold text-gray-900 mb-2">
              Confirmer le mot de passe
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <input
                type="password"
                id="confirmPassword"
                bind:value={confirmPassword}
                required
                minlength="8"
                class="w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
                placeholder="••••••••"
                disabled={loading || !token}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || !token}
            class="group relative w-full py-4 px-6 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 opacity-90"></div>
            <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            
            {#if loading}
              <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
                <svg class="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span class="text-lg">Réinitialisation...</span>
              </span>
            {:else}
              <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg text-lg">
                Réinitialiser le mot de passe
              </span>
            {/if}
          </button>
        </form>

        <div class="mt-6 text-center">
          <button
            on:click={() => navigate('/login')}
            class="inline-flex items-center gap-2 text-gray-800 hover:text-emerald-700 font-semibold transition-all hover:gap-3"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Retour à la connexion
          </button>
        </div>
      {/if}
    </div>
  </div>
</div>
