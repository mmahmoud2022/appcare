<script lang="ts">
  import { navigate } from '../../lib/router';
  import { authStore } from '../../lib/stores/auth';
  import { login } from '../../lib/api';
  import type { LoginCredentials } from '../../lib/api';

  let credentials: LoginCredentials = { email: '', password: '' };
  let error: string | null = null;
  let loading = false;
  let showPassword = false;

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    error = null;

    // Validation basique
    if (!credentials.email.trim()) {
      error = 'Veuillez entrer votre adresse email administrateur.';
      return;
    }
    if (!credentials.password.trim()) {
      error = 'Veuillez entrer votre mot de passe.';
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(credentials.email)) {
      error = 'Format d\'email invalide. Exemple : admin@exemple.com';
      return;
    }

    loading = true;
    try {
      const response = await login(credentials);
      if (response.user.role.toUpperCase() !== 'ADMIN') {
        error = 'Accès refusé : réservé aux administrateurs.';
        loading = false;
        return;
      }

      authStore.login(response.access_token, response.refresh_token, response.user);
      navigate('/admin/dashboard');
    } catch (err: any) {
      const status = err.response?.status;
      const detail = err.response?.data?.detail?.toLowerCase?.() || '';

      if (status === 401) {
        error = detail.includes('password')
          ? 'Mot de passe incorrect.'
          : 'Email ou mot de passe incorrect.';
      } else if (status === 403) {
        error = 'Votre compte administrateur est suspendu ou bloqué.';
      } else if (status === 422) {
        error = 'Données invalides. Vérifiez votre email et mot de passe.';
      } else if (status === 429) {
        error = 'Trop de tentatives. Réessayez dans quelques minutes.';
      } else if (status >= 500) {
        error = 'Erreur serveur. Veuillez réessayer plus tard.';
      } else {
        error = err.response?.data?.detail || 'Erreur de connexion. Veuillez vérifier vos informations.';
      }
      
      console.error('Login error:', err);
    } finally {
      loading = false;
    }
  };
</script>

<div class="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 flex items-center justify-center px-4 py-12">
  <div class="max-w-md w-full">
    <div class="relative bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl border-2 border-white/50 p-8 hover:shadow-orange-200/50 transition-all duration-300">
      <div class="absolute inset-0 bg-gradient-to-br from-orange-50/50 to-amber-50/50 rounded-3xl -z-10"></div>
      
      <!-- Logo -->
      <div class="flex justify-center mb-4 sm:mb-6 animate-slide-down">
        <div class="relative">
          <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 sm:h-10 sm:w-10 text-white" viewBox="0 0 24 24" stroke="currentColor" fill="none">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div class="absolute -top-1 -right-1 w-5 h-5 sm:w-6 sm:h-6 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-2 px-2">Connexion administrateur</h1>
      <p class="text-base sm:text-lg text-gray-700 font-medium text-center mb-4 sm:mb-6 px-4">Accès réservé au personnel autorisé</p>

    {#if error}
      <div class="bg-red-50/80 backdrop-blur-sm border-2 border-red-200 rounded-xl p-4 mb-6 shadow-md animate-shake">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
              </svg>
            </div>
          </div>
          <div class="flex-1 pt-1">
            <h4 class="font-bold text-gray-900 mb-1">Erreur de connexion</h4>
            <p class="text-sm text-red-800 font-medium">{error}</p>
          </div>
        </div>
      </div>
    {/if}

    <form on:submit={handleSubmit} class="space-y-6">
      <div>
        <label for="email" class="block text-sm font-bold text-gray-900 mb-2">Email</label>
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <input
            id="email"
            type="email"
            bind:value={credentials.email}
            placeholder="admin@exemple.com"
            disabled={loading}
            autocomplete="email"
            required
            class="w-full pl-12 pr-4 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
        </div>
      </div>

      <div>
        <label for="password" class="block text-sm font-bold text-gray-900 mb-2">Mot de passe</label>
        <div class="relative">
          <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            bind:value={credentials.password}
            placeholder="••••••••"
            disabled={loading}
            autocomplete="current-password"
            required
            class="w-full pl-12 pr-12 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
          <button
            type="button"
            on:click={() => (showPassword = !showPassword)}
            class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-orange-600 transition-colors"
            aria-label="Afficher ou masquer le mot de passe"
            disabled={loading}
          >
            {#if showPassword}
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            {:else}
              <svg class="h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            {/if}
          </button>
        </div>
      </div>

      <button
        type="submit"
        class="group relative w-full py-4 px-6 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none overflow-hidden"
        disabled={loading}
      >
        <div class="absolute inset-0 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 opacity-90"></div>
        <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
        <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        
        {#if loading}
          <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
            <svg class="animate-spin h-6 w-6 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="text-lg">Connexion en cours...</span>
          </span>
        {:else}
          <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:scale-110 transition-transform duration-300" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-lg">Se connecter</span>
          </span>
        {/if}
      </button>
    </form>

    <div class="mt-8 pt-6 border-t-2 border-gray-100 space-y-4">
      <p class="text-center text-sm text-gray-700 font-semibold">
        Pas encore de compte ? 
        <button type="button" on:click={() => navigate('/admin/register')} class="text-orange-600 hover:text-orange-700 font-bold underline decoration-2 underline-offset-2 transition-colors">
          Créer un compte administrateur
        </button>
      </p>
      <div class="text-center">
        <button type="button" on:click={() => navigate('/')} class="inline-flex items-center gap-2 text-gray-800 hover:text-orange-700 font-semibold transition-all hover:gap-3">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Retour à l'accueil
        </button>
      </div>
    </div>
  </div>
</div>
</div>

