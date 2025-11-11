<script lang="ts">
  import type { AxiosError } from 'axios';
  import { navigate } from '../lib/router';
  import { authStore } from '../lib/stores/auth';
  import { login } from '../lib/api';
  import type { LoginCredentials } from '../lib/api';
  import '../styles/login.css';

  let credentials: LoginCredentials = {
    email: '',
    password: '',
  };

  let error: string | null = null;
  let loading = false;
  let showPassword = false;
  let emailTouched = false;
  let passwordTouched = false;

  const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  interface ApiErrorData {
    detail?: string;
  }

  const clearError = () => {
    if (error) {
      error = null;
    }
  };

  // Map API error responses to contextual messages for the user.
  const getLoginErrorMessage = (err: unknown): string => {
    const apiError = err as AxiosError<ApiErrorData> | undefined;
    const status = apiError?.response?.status;
    const detailText = typeof apiError?.response?.data?.detail === 'string'
      ? apiError.response?.data?.detail
      : '';
    const detailLower = detailText.toLowerCase();

    if (status === 400) {
      if (detailLower.includes('email')) {
        return 'Email invalide. Veuillez vérifier votre adresse email.';
      }
      if (detailLower.includes('password')) {
        return 'Mot de passe requis.';
      }
      return 'Données invalides. Veuillez vérifier vos informations.';
    }

    if (status === 401) {
      if (detailLower.includes('not found') || detailLower.includes('does not exist')) {
        return 'Aucun compte trouvé avec cet email. Veuillez vérifier votre email ou créer un compte.';
      }
      if (detailLower.includes('password') || detailLower.includes('incorrect') || detailLower.includes('invalid credentials')) {
        return 'Mot de passe incorrect. Veuillez réessayer.';
      }
      if (detailLower.includes('not verified')) {
        return 'Votre email n\'est pas encore vérifié. Veuillez consulter votre boîte email.';
      }
      return 'Email ou mot de passe incorrect. Veuillez réessayer.';
    }

    if (status === 403) {
      if (detailLower.includes('suspend')) {
        return 'Votre compte a été suspendu. Veuillez contacter l\'administrateur.';
      }
      if (detailLower.includes('block') || detailLower.includes('blacklist')) {
        return 'Votre compte a été bloqué. Veuillez contacter le support.';
      }
      if (detailLower.includes('not approved') || detailLower.includes('pending')) {
        return 'Votre compte est en attente d\'approbation par un administrateur.';
      }
      return `Accès refusé. ${detailText || 'Veuillez contacter l\'administrateur.'}`;
    }

    if (status === 422) {
      return 'Données de connexion invalides. Vérifiez votre email et mot de passe.';
    }

    if (status === 429) {
      return 'Trop de tentatives de connexion. Veuillez réessayer dans quelques minutes.';
    }

    if (typeof status === 'number' && status >= 500) {
      return 'Erreur serveur. Veuillez réessayer plus tard.';
    }

    if (apiError?.code === 'ECONNABORTED' || apiError?.code === 'ERR_NETWORK') {
      return 'Erreur de connexion réseau. Vérifiez votre connexion internet.';
    }

    return detailText || 'Erreur de connexion. Veuillez réessayer.';
  };

  // Real-time validation
  $: trimmedEmail = credentials.email.trim();
  $: emailIsValid = EMAIL_REGEX.test(trimmedEmail);
  $: showEmailError = emailTouched && trimmedEmail.length > 0 && !emailIsValid;
  $: passwordIsBlank = credentials.password.trim().length === 0;
  $: showPasswordError = passwordTouched && passwordIsBlank;
  $: canSubmit = emailIsValid && !passwordIsBlank && !loading;

  const handleSubmit = async () => {
    if (loading) return;
    error = null;

    // Mark fields as touched
    emailTouched = true;
    passwordTouched = true;

    // Validation côté client
    if (!trimmedEmail) {
      error = 'Veuillez entrer votre adresse email.';
      return;
    }

    if (passwordIsBlank) {
      error = 'Veuillez entrer votre mot de passe.';
      return;
    }

    // Validation basique du format email
    if (!emailIsValid) {
      error = 'Format d\'email invalide. Exemple: utilisateur@exemple.com';
      return;
    }

    credentials = { ...credentials, email: trimmedEmail };
    loading = true;

    try {
      const response = await login(credentials);
      
      // Store tokens and user in auth store
      authStore.login(response.access_token, response.refresh_token, response.user);

      // Redirect based on role (case-insensitive comparison)
      const userRole = response.user.role.toUpperCase();
      if (userRole === 'ADMIN') {
        navigate('/admin/dashboard');
      } else if (userRole === 'DOCTOR') {
        if (response.user.admin_approved) {
          navigate('/doctors/dashboard');
        } else {
          // Doctor not yet approved
          navigate('/doctors/pending');
        }
      } else {
        navigate('/patients/dashboard');
      }
    } catch (err) {
      console.error('Login error:', err);
      error = getLoginErrorMessage(err);
    } finally {
      loading = false;
    }
  };
</script>

<div class="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-cyan-50 flex items-center justify-center px-4 py-12">
  <div class="max-w-md w-full space-y-8">
    <!-- Logo/Title -->
    <div class="text-center mb-8 animate-slide-down">
      <div class="inline-block mb-6 relative">
        <div class="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto shadow-xl animate-bounce bg-gradient-to-br from-emerald-500 to-teal-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
        <div class="absolute -top-1 -right-1 w-6 h-6 bg-gradient-to-br from-teal-400 to-emerald-500 rounded-full shadow-lg"></div>
      </div>
      <h1 class="text-5xl font-bold mb-3 bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">Connexion</h1>
      <p class="text-lg text-gray-700 font-medium">Accédez à votre compte</p>
    </div>

    <!-- Login Form -->
    <div class="relative bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl p-8 border-2 border-white/50 hover:shadow-emerald-200/50 transition-all duration-300">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-50/50 to-teal-50/50 rounded-3xl -z-10"></div>
      
      <form on:submit|preventDefault={handleSubmit} class="space-y-6" novalidate>
        <!-- Error Message -->
        {#if error}
          <div class="alert alert-error animate-scale-in animate-shake" role="alert" aria-live="assertive">
            <div class="flex items-start gap-3">
              <div class="flex-shrink-0">
                <div class="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-error to-error-dark shadow-lg">
                  <svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
              <div class="flex-1 pt-1">
                <h4 class="font-bold text-gray-900 mb-1">Erreur de connexion</h4>
                <p class="text-sm text-red-800 font-medium leading-relaxed">{error}</p>
              </div>
            </div>
          </div>
        {/if}

        <!-- Email Field -->
        <div>
          <label for="email" class="block text-sm font-bold text-gray-900 mb-2">Email</label>
          <div class="relative">
            <div class="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            </div>
            <input
              id="email"
              type="email"
              bind:value={credentials.email}
              on:blur={() => emailTouched = true}
              on:input={clearError}
              class="w-full pl-12 pr-12 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium {showEmailError ? 'border-red-400 focus:ring-red-500 focus:border-red-500' : ''}"
              placeholder="votre@email.com"
              required
              disabled={loading}
              autocomplete="email"
              aria-invalid={showEmailError}
              aria-describedby={showEmailError ? 'login-email-error' : undefined}
            />
            {#if credentials.email && emailIsValid}
              <div class="absolute inset-y-0 right-0 pr-4 flex items-center pointer-events-none">
                <svg class="h-6 w-6 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                </svg>
              </div>
            {/if}
          </div>
          {#if showEmailError}
            <p id="login-email-error" class="mt-2 text-sm text-red-700 font-semibold flex items-center gap-1">
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              Format d'email invalide
            </p>
          {/if}
        </div>

        <!-- Password Field -->
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
              on:blur={() => passwordTouched = true}
              on:input={() => error = null}
              class="w-full pl-12 pr-12 py-3.5 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium {showPasswordError ? 'border-red-400 focus:ring-red-500 focus:border-red-500' : ''}"
              placeholder="••••••••"
              required
              disabled={loading}
              autocomplete="current-password"
              aria-invalid={showPasswordError}
              aria-describedby={showPasswordError ? 'login-password-error' : undefined}
            />
            <button
              type="button"
              class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-emerald-600 transition-colors"
              on:click={() => showPassword = !showPassword}
              aria-label="Toggle password visibility"
              aria-pressed={showPassword}
              tabindex="-1"
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
          {#if showPasswordError}
            <p id="login-password-error" class="mt-2 text-sm text-red-700 font-semibold flex items-center gap-1">
              <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
              </svg>
              Le mot de passe est requis.
            </p>
          {/if}
        </div>

        <!-- Forgot Password Link -->
        <div class="text-right">
          <button type="button" on:click={() => navigate('/forgot-password')} class="text-sm text-emerald-600 hover:text-emerald-700 font-semibold underline decoration-2 underline-offset-2 transition-colors">
            Mot de passe oublié ?
          </button>
        </div>

        <!-- Submit Button -->
        <button
          type="submit"
          class="group relative w-full py-4 px-6 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none overflow-hidden {loading ? 'animate-pulse' : ''}"
          disabled={!canSubmit}
          aria-busy={loading}
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
              <span class="text-lg">Connexion en cours...</span>
            </span>
          {:else}
            <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
              </svg>
              <span class="text-lg">Se connecter</span>
            </span>
          {/if}
        </button>
      </form>

      <!-- Registration Links -->
      <div class="mt-8 pt-6 border-t-2 border-gray-100">
        <p class="text-center text-sm text-gray-700 font-semibold mb-4">Pas encore de compte ?</p>
        <div class="grid grid-cols-2 gap-3">
          <button 
            type="button" 
            on:click={() => navigate('/register/patient')} 
            class="group relative px-4 py-3 rounded-xl font-semibold shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-300 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-purple-100 to-indigo-100"></div>
            <div class="absolute inset-0 bg-white/40 backdrop-blur-sm"></div>
            <div class="absolute inset-0 border-2 border-purple-200 rounded-xl"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-purple-200/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span class="relative text-sm text-purple-700 group-hover:text-purple-800 font-bold transition-colors">
              Patient →
            </span>
          </button>
          
          <button 
            type="button" 
            on:click={() => navigate('/register/doctor')} 
            class="group relative px-4 py-3 rounded-xl font-semibold shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-300 overflow-hidden"
          >
            <div class="absolute inset-0 bg-gradient-to-r from-emerald-100 to-teal-100"></div>
            <div class="absolute inset-0 bg-white/40 backdrop-blur-sm"></div>
            <div class="absolute inset-0 border-2 border-emerald-200 rounded-xl"></div>
            <div class="absolute inset-0 bg-gradient-to-br from-emerald-200/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
            <span class="relative text-sm text-emerald-700 group-hover:text-emerald-800 font-bold transition-colors">
              Médecin →
            </span>
          </button>
        </div>
      </div>
    </div>

    <!-- Back to Home -->
    <div class="text-center mt-8">
      <button type="button" on:click={() => navigate('/')} class="inline-flex items-center gap-2 text-gray-800 hover:text-emerald-700 font-semibold transition-all hover:gap-3">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Retour à l'accueil
      </button>
    </div>
  </div>
</div>
