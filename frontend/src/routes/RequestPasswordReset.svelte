<script lang="ts">
  import { navigate } from '../lib/router';
  import { requestPasswordReset } from '../lib/api';

  let email = '';
  let loading = false;
  let success = false;
  let error = '';

  async function handleSubmit() {
    if (!email) {
      error = 'Veuillez entrer votre adresse email.';
      return;
    }

    loading = true;
    error = '';

    try {
      const response = await requestPasswordReset(email);
      success = true;
      error = '';
    } catch (err: any) {
      error = err.response?.data?.detail || 'Une erreur est survenue. Veuillez réessayer.';
      success = false;
    } finally {
      loading = false;
    }
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
        Mot de passe oublié
      </h1>
      <p class="text-lg text-gray-700 font-medium text-center mb-6">
        Entrez votre email pour recevoir un lien de réinitialisation
      </p>

      {#if success}
        <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-5 mb-6 shadow-lg animate-scale-in">
          <div class="flex items-start gap-3">
            <div class="flex-shrink-0">
              <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-md">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div>
              <p class="text-sm text-green-900 font-semibold">
                Un email de réinitialisation a été envoyé à <strong class="text-green-800">{email}</strong>.
              </p>
              <p class="text-sm text-green-800 font-medium mt-2">
                Vérifiez votre boîte de réception et suivez les instructions pour réinitialiser votre mot de passe.
              </p>
            </div>
          </div>
        </div>

        <button
          on:click={() => navigate('/login')}
          class="group relative w-full py-4 px-6 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 overflow-hidden"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-emerald-500 via-teal-500 to-emerald-600 opacity-90"></div>
          <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
          <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg text-lg">
            Retour à la connexion
          </span>
        </button>
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
            <label for="email" class="block text-sm font-bold text-gray-900 mb-2">
              Adresse email
            </label>
            <div class="relative">
              <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
                </svg>
              </div>
              <input
                type="email"
                id="email"
                bind:value={email}
                required
                class="w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
                placeholder="votre.email@exemple.com"
                disabled={loading}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
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
                <span class="text-lg">Envoi en cours...</span>
              </span>
            {:else}
              <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg text-lg">
                Envoyer le lien de réinitialisation
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
