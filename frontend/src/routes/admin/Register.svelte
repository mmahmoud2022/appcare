<script lang="ts">
  import { navigate } from '../../lib/router';
  import { registerAdmin } from '../../lib/api';
  import type { AdminRegistrationData } from '../../lib/api';
  import '../../styles/login.css';

  let formData: AdminRegistrationData = {
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    admin_secret: '',
  };

  let confirmPassword = '';
  let error: string | null = null;
  let success: string | null = null;
  let loading = false;
  let showPassword = false;
  let showConfirmPassword = false;
  let showAdminSecret = false;
  let passwordStrength = 0;

  // Password requirements tracking
  $: passwordReqs = {
    minLength: formData.password.length >= 8,
    hasUpper: /[A-Z]/.test(formData.password),
    hasLower: /[a-z]/.test(formData.password),
    hasNumber: /[0-9]/.test(formData.password),
  };

  $: allPasswordReqsMet = Object.values(passwordReqs).every(Boolean);

  const handlePasswordInput = () => {
    const value = formData.password;
    const score = [/.{8,}/, /[A-Z]/, /[a-z]/, /[0-9]/].reduce(
      (acc, regex) => acc + Number(regex.test(value)),
      0
    );
    passwordStrength = score;
  };

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    error = null;
    success = null;

    // Validate password requirements
    if (!allPasswordReqsMet) {
      error = 'Le mot de passe ne respecte pas tous les critères requis.';
      return;
    }

    if (formData.password !== confirmPassword) {
      error = 'Les mots de passe ne correspondent pas.';
      return;
    }
    if (!formData.admin_secret) {
      error = 'Le secret administrateur est requis.';
      return;
    }

    loading = true;
    try {
      await registerAdmin(formData);
      success = 'Compte administrateur créé avec succès ! Redirection...';
      setTimeout(() => navigate('/admin/login'), 2000);
    } catch (err: any) {
      if (err.response?.status === 403) error = 'Secret administrateur invalide.';
      else if (err.response?.status === 422) {
        // Better handling of validation errors
        const details = err.response?.data?.detail;
        if (Array.isArray(details) && details.length > 0) {
          error = details[0].msg || 'Erreur de validation du formulaire.';
        } else {
          error = 'Erreur de validation. Vérifiez tous les champs.';
        }
      }
      else if (err.response?.status === 400)
        error = err.response.data?.detail || 'Email déjà enregistré.';
      else error = 'Erreur lors de la création du compte.';
    } finally {
      loading = false;
    }
  };
</script>

<div class="min-h-screen bg-gradient-to-br from-orange-50 via-amber-50 to-yellow-50 flex items-center justify-center px-4 py-12">
  <div class="max-w-lg w-full">
    <div class="relative bg-white/80 backdrop-blur-lg rounded-3xl shadow-2xl border-2 border-white/50 p-8 hover:shadow-orange-200/50 transition-all duration-300">
      <div class="absolute inset-0 bg-gradient-to-br from-orange-50/50 to-amber-50/50 rounded-3xl -z-10"></div>
      
      <!-- Logo -->
      <div class="flex justify-center mb-4 sm:mb-6 animate-slide-down">
        <div class="relative">
          <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-3xl bg-gradient-to-br from-orange-500 to-amber-600 flex items-center justify-center shadow-xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 sm:h-10 sm:w-10 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div class="absolute -top-1 -right-1 w-5 h-5 sm:w-6 sm:h-6 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full shadow-lg"></div>
        </div>
      </div>

      <h1 class="text-2xl sm:text-3xl font-bold text-gray-900 text-center mb-2 px-2">Création d'un compte administrateur</h1>
      <p class="text-base sm:text-lg text-gray-700 font-medium text-center mb-4 sm:mb-6 px-4">Veuillez remplir les informations ci-dessous</p>

    {#if success}
      <div class="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-5 mb-6 shadow-lg animate-scale-in">
        <div class="flex items-start gap-3">
          <div class="flex-shrink-0">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <p class="text-sm text-green-900 font-semibold pt-1">{success}</p>
        </div>
      </div>
    {/if}

    {#if error}
      <div class="bg-red-50/80 backdrop-blur-sm border-2 border-red-200 rounded-xl p-4 mb-6 shadow-md">
        <div class="flex items-start gap-3">
          <svg class="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <p class="text-sm text-red-800 font-medium">{error}</p>
        </div>
      </div>
    {/if}

    <form on:submit={handleSubmit} class="space-y-6">
      <div class="grid grid-cols-2 gap-4">
        <div>
          <label for="first_name" class="block text-sm font-bold text-gray-900 mb-2">Prénom *</label>
          <input 
            id="first_name" 
            type="text" 
            bind:value={formData.first_name} 
            required 
            placeholder="Prénom"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
        </div>
        <div>
          <label for="last_name" class="block text-sm font-bold text-gray-900 mb-2">Nom *</label>
          <input 
            id="last_name" 
            type="text" 
            bind:value={formData.last_name} 
            required 
            placeholder="Nom"
            class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
        </div>
      </div>

      <div>
        <label for="email" class="block text-sm font-bold text-gray-900 mb-2">Email *</label>
        <input 
          id="email" 
          type="email" 
          bind:value={formData.email} 
          required 
          placeholder="admin@example.com"
          class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
        />
      </div>

      <div>
        <label for="phone" class="block text-sm font-bold text-gray-900 mb-2">Téléphone</label>
        <input 
          id="phone" 
          type="tel" 
          bind:value={formData.phone} 
          placeholder="+33 6 12 34 56 78"
          class="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
        />
      </div>

      <div>
        <label for="password" class="block text-sm font-bold text-gray-900 mb-2">Mot de passe *</label>
        <div class="relative">
          <input
            id="password"
            type={showPassword ? 'text' : 'password'}
            bind:value={formData.password}
            on:input={handlePasswordInput}
            placeholder="Entrez un mot de passe sécurisé"
            required
            class="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
          <button 
            type="button" 
            on:click={() => (showPassword = !showPassword)} 
            class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-orange-600 transition-colors" 
            aria-label="Afficher ou masquer le mot de passe"
          >
            {showPassword ? '🙈' : '👁️'}
          </button>
        </div>

        <!-- Password requirements checklist -->
        {#if formData.password.length > 0}
          <div class="mt-3 grid grid-cols-2 gap-2 text-sm">
            <div class="flex items-center gap-2 {passwordReqs.minLength ? 'text-green-700' : 'text-gray-500'}">
              <span class="font-bold">{passwordReqs.minLength ? '✓' : '○'}</span>
              <span class="font-medium">8+ caractères</span>
            </div>
            <div class="flex items-center gap-2 {passwordReqs.hasUpper ? 'text-green-700' : 'text-gray-500'}">
              <span class="font-bold">{passwordReqs.hasUpper ? '✓' : '○'}</span>
              <span class="font-medium">Majuscule</span>
            </div>
            <div class="flex items-center gap-2 {passwordReqs.hasLower ? 'text-green-700' : 'text-gray-500'}">
              <span class="font-bold">{passwordReqs.hasLower ? '✓' : '○'}</span>
              <span class="font-medium">Minuscule</span>
            </div>
            <div class="flex items-center gap-2 {passwordReqs.hasNumber ? 'text-green-700' : 'text-gray-500'}">
              <span class="font-bold">{passwordReqs.hasNumber ? '✓' : '○'}</span>
              <span class="font-medium">Chiffre</span>
            </div>
          </div>
        {/if}

        <!-- Strength bar -->
        <div class="mt-3 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            class="h-full transition-all duration-300 rounded-full {passwordStrength === 4 ? 'bg-gradient-to-r from-green-500 to-emerald-600' : 'bg-gradient-to-r from-red-500 via-orange-500 to-green-500'}" 
            style="width: {passwordStrength * 25}%;"
          ></div>
        </div>
      </div>

      <div>
        <label for="confirm_password" class="block text-sm font-bold text-gray-900 mb-2">Confirmer le mot de passe *</label>
        <div class="relative">
          <input
            id="confirm_password"
            type={showConfirmPassword ? 'text' : 'password'}
            bind:value={confirmPassword}
            placeholder="Répéter le mot de passe"
            required
            class="w-full px-4 py-3 pr-12 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white/50 backdrop-blur-sm font-medium"
          />
          <button 
            type="button" 
            on:click={() => (showConfirmPassword = !showConfirmPassword)} 
            class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-orange-600 transition-colors" 
            aria-label="Afficher ou masquer la confirmation du mot de passe"
          >
            {showConfirmPassword ? '🙈' : '👁️'}
          </button>
        </div>
        {#if confirmPassword && formData.password !== confirmPassword}
          <p class="mt-2 text-sm text-red-700 font-semibold flex items-center gap-1">
            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
            </svg>
            Les mots de passe ne correspondent pas
          </p>
        {/if}
      </div>

      <div class="bg-orange-50/50 border-2 border-orange-200 rounded-xl p-4">
        <label for="admin_secret" class="block text-sm font-bold text-gray-900 mb-2">Secret Administrateur *</label>
        <div class="relative">
          <input
            id="admin_secret"
            type={showAdminSecret ? 'text' : 'password'}
            bind:value={formData.admin_secret}
            placeholder="AdminSecret2025"
            required
            class="w-full px-4 py-3 pr-12 border-2 border-orange-300 rounded-xl focus:ring-2 focus:ring-orange-500 focus:border-orange-500 transition-all duration-200 bg-white font-medium"
          />
          <button 
            type="button" 
            on:click={() => (showAdminSecret = !showAdminSecret)} 
            class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-orange-600 transition-colors" 
            aria-label="Afficher ou masquer le secret administrateur"
          >
            {showAdminSecret ? '🙈' : '👁️'}
          </button>
        </div>
        <p class="mt-2 text-xs text-orange-800 font-semibold">
          ℹ️ Ce secret est défini côté serveur (fichier .env): ADMIN_SECRET
        </p>
      </div>

      <button 
        type="submit" 
        class="group relative w-full py-4 px-6 rounded-xl font-bold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-60 disabled:cursor-not-allowed disabled:transform-none overflow-hidden mt-2" 
        disabled={loading}
      >
        <div class="absolute inset-0 bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 opacity-90"></div>
        <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
        <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
        
        {#if loading}
          <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
            <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <span class="text-lg">Création en cours...</span>
          </span>
        {:else}
          <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg text-lg">
            🚀 Créer le compte
          </span>
        {/if}
      </button>
    </form>

    <div class="mt-6 text-center">
      <a 
        href="/admin/login" 
        on:click|preventDefault={() => navigate('/admin/login')}
        class="inline-flex items-center gap-2 text-gray-800 hover:text-orange-700 font-semibold transition-all hover:gap-3"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Retour à la connexion
      </a>
    </div>
  </div>
</div>
</div>

