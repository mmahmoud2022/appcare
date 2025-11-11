<script lang="ts">
  import { navigate } from '../../lib/router';
  import { registerPatient } from '../../lib/api';
  import type { PatientRegistrationData, RegistrationResponse } from '../../lib/api';
  import '../../styles/patient-register.css';

  let formData: PatientRegistrationData = {
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    phone: '',
    gender: '',
    date_of_birth: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    marketing_consent: false,
  };

  let confirmPassword = '';
  let error: string | null = null;
  let loading = false;
  let success = false;
  let registrationResult: RegistrationResponse | null = null;
  let currentStep = 1;
  let showPassword = false;
  let showConfirmPassword = false;

  // Password requirements tracking
  $: passwordReqs = {
    minLength: formData.password.length >= 8,
    hasUpper: /[A-Z]/.test(formData.password),
    hasLower: /[a-z]/.test(formData.password),
    hasNumber: /[0-9]/.test(formData.password),
  };

  $: allPasswordReqsMet = Object.values(passwordReqs).every(Boolean);
  $: passwordsMatch = confirmPassword === '' || formData.password === confirmPassword;

  const handleSubmit = async (e: Event) => {
    e.preventDefault();
    error = null;
    loading = true;

    if (!allPasswordReqsMet) {
      error = 'Le mot de passe ne respecte pas tous les critères requis';
      loading = false;
      return;
    }

    if (formData.password !== confirmPassword) {
      error = 'Les mots de passe ne correspondent pas';
      loading = false;
      return;
    }

    try {
      registrationResult = await registerPatient(formData);
      success = true;

      setTimeout(() => {
        navigate('/login');
      }, 5000);
    } catch (err: any) {
      console.error('Registration error:', err);
      if (err.response?.status === 400) {
        error = err.response.data?.detail || 'Données invalides';
      } else if (err.response?.status === 422) {
        const validationErrors = err.response?.data?.detail;
        if (Array.isArray(validationErrors) && validationErrors.length > 0) {
          // Extract the most relevant error message
          const firstError = validationErrors[0];
          error = firstError.msg || 'Erreur de validation des données';
        } else if (typeof validationErrors === 'string') {
          error = validationErrors;
        } else {
          error = 'Erreur de validation des données';
        }
      } else if (err.response?.status === 409) {
        error = 'Un compte existe déjà avec cet email';
      } else if (err.response?.status === 403) {
        error = err.response.data?.detail || 'Email bloqué ou suspendu';
      } else {
        error = 'Erreur lors de l\'inscription. Veuillez réessayer.';
      }
    } finally {
      loading = false;
    }
  };

  const nextStep = () => {
    if (currentStep < 3) currentStep++;
  };

  const prevStep = () => {
    if (currentStep > 1) currentStep--;
  };

  const validateStep1 = () => {
    if (!formData.first_name || !formData.last_name || !formData.email || 
        !formData.password || !confirmPassword) {
      error = 'Veuillez remplir tous les champs obligatoires';
      return false;
    }
    if (!allPasswordReqsMet) {
      error = 'Le mot de passe ne respecte pas tous les critères requis';
      return false;
    }
    if (formData.password !== confirmPassword) {
      error = 'Les mots de passe ne correspondent pas';
      return false;
    }
    error = null;
    return true;
  };

  const handleNextStep = () => {
    if (currentStep === 1 && !validateStep1()) {
      return;
    }
    nextStep();
  };
</script>

<div class="page-shell">
  <div class="max-w-4xl mx-auto space-y-12">
    <!-- Header -->
    <div class="text-center mb-10 animate-slide-down">
      <div class="inline-block mb-6 relative">
        <div class="w-20 h-20 rounded-3xl flex items-center justify-center mx-auto shadow-lg animate-bounce bg-gradient-to-br from-purple-500 via-indigo-500 to-purple-600">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
          </svg>
        </div>
      </div>
      <h1 class="text-4xl md:text-5xl font-bold mb-3 text-gray-900">Inscription Patient</h1>
      <p class="text-lg text-gray-700 font-medium">Créez votre compte pour accéder aux services médicaux</p>
    </div>

    {#if success && registrationResult}
      <!-- Success Message -->
      <div class="card-elevated animate-slide-down">
        <div class="alert alert-success">
          <div class="flex items-start gap-4">
            <div class="flex-shrink-0">
              <div class="w-16 h-16 rounded-2xl flex items-center justify-center shadow-lg bg-gradient-to-br from-success to-success-dark">
                <svg class="h-8 w-8 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <div class="flex-1">
              <h3 class="text-2xl font-bold mb-2 text-gray-900">{registrationResult.message}</h3>
              
              {#if registrationResult.next_steps.length > 0}
                <div class="mt-5 p-4 rounded-xl bg-green-50 border-2 border-green-200">
                  <p class="font-bold mb-3 text-gray-900">📋 Prochaines étapes :</p>
                  <ul class="space-y-2">
                    {#each registrationResult.next_steps as step, index}
                      <li class="flex items-start gap-3 animate-slide-down">
                        <span class="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold bg-gradient-to-br from-purple-600 to-purple-700 text-white shadow-md">{index + 1}</span>
                        <span class="text-gray-900 font-medium leading-relaxed">{step}</span>
                      </li>
                    {/each}
                  </ul>
                </div>
              {/if}

              <div class="mt-5 flex items-center gap-2 text-purple-700">
                <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <p class="font-semibold">Redirection vers la page de connexion...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    {:else}
      <!-- Registration Form -->
      <div class="card hover-lift">
        <!-- Step Indicator -->
        <div class="flex items-center justify-center gap-4 mb-10">
          <div class="flex flex-col items-center gap-2">
            <div class="flex items-center justify-center w-14 h-14 rounded-2xl font-bold text-lg transition-all duration-300 {currentStep === 1 ? 'bg-gradient-to-br from-primary-500 via-primary-600 to-primary-700 text-white shadow-xl scale-110 ring-4 ring-primary-200' : currentStep > 1 ? 'bg-gradient-to-br from-success to-success-dark text-white shadow-md' : 'bg-gray-200 text-gray-500'}">
              {#if currentStep > 1}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              {:else}
                1
              {/if}
            </div>
            <span class="text-xs font-bold {currentStep === 1 ? 'text-purple-700' : currentStep > 1 ? 'text-purple-600' : 'text-gray-500'}">Base</span>
          </div>
          
          <div class="w-20 h-1.5 rounded-full transition-all duration-500 {currentStep > 1 ? 'bg-gradient-to-r from-purple-500 to-purple-600 shadow-md' : 'bg-gray-300'}"></div>
          
          <div class="flex flex-col items-center gap-2">
            <div class="flex items-center justify-center w-14 h-14 rounded-2xl font-bold text-lg transition-all duration-300 {currentStep === 2 ? 'bg-gradient-to-br from-purple-500 via-purple-600 to-purple-700 text-white shadow-xl scale-110 ring-4 ring-purple-200' : currentStep > 2 ? 'bg-gradient-to-br from-purple-500 to-purple-600 text-white shadow-md' : 'bg-gray-300 text-gray-600'}">
              {#if currentStep > 2}
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M5 13l4 4L19 7" />
                </svg>
              {:else}
                2
              {/if}
            </div>
            <span class="text-xs font-bold {currentStep === 2 ? 'text-purple-700' : currentStep > 2 ? 'text-purple-600' : 'text-gray-500'}">Personnel</span>
          </div>
          
          <div class="w-20 h-1.5 rounded-full transition-all duration-500 {currentStep > 2 ? 'bg-gradient-to-r from-purple-500 to-purple-600 shadow-md' : 'bg-gray-300'}"></div>
          
          <div class="flex flex-col items-center gap-2">
            <div class="flex items-center justify-center w-14 h-14 rounded-2xl font-bold text-lg transition-all duration-300 {currentStep === 3 ? 'bg-gradient-to-br from-purple-500 via-purple-600 to-purple-700 text-white shadow-xl scale-110 ring-4 ring-purple-200' : 'bg-gray-300 text-gray-600'}">
              3
            </div>
            <span class="text-xs font-bold {currentStep === 3 ? 'text-purple-700' : 'text-gray-500'}">Urgence</span>
          </div>
        </div>

        <form on:submit={handleSubmit} class="space-y-6">
          <!-- Error Message -->
          {#if error}
            <div class="alert alert-error animate-scale-in animate-shake">
              <div class="flex items-start gap-3">
                <div class="flex-shrink-0">
                  <div class="w-10 h-10 rounded-full flex items-center justify-center bg-gradient-to-br from-error to-error-dark shadow-lg animate-error-pulse">
                    <svg class="h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                </div>
                <div class="flex-1 pt-1">
                  <h4 class="font-bold text-gray-900 mb-1">Erreur d'inscription</h4>
                  <p class="text-sm text-red-800 font-medium leading-relaxed">{error}</p>
                </div>
              </div>
            </div>
          {/if}

          {#if currentStep === 1}
            <!-- Step 1: Basic Information -->
            <div class="space-y-5 animate-fade-in">
              <div class="relative mb-6 p-5 rounded-2xl bg-gradient-to-r from-purple-50 via-indigo-50 to-purple-50 border-l-4 border-purple-600 shadow-sm">
                <div class="flex items-center gap-4">
                  <div class="w-16 h-16 rounded-xl flex items-center justify-center bg-gradient-to-br from-purple-500 to-purple-700 shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-2xl font-bold text-gray-900">Informations de base</h3>
                    <p class="text-sm text-purple-700 font-semibold mt-1">Créez votre identifiant et mot de passe</p>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label for="first_name" class="form-label">Prénom *</label>
                  <input
                    id="first_name"
                    type="text"
                    bind:value={formData.first_name}
                    class="input-field"
                    placeholder="Jean"
                    required
                    disabled={loading}
                  />
                </div>

                <div>
                  <label for="last_name" class="form-label">Nom *</label>
                  <input
                    id="last_name"
                    type="text"
                    bind:value={formData.last_name}
                    class="input-field"
                    placeholder="Dupont"
                    required
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label for="email" class="form-label">Email *</label>
                <input
                  id="email"
                  type="email"
                  bind:value={formData.email}
                  class="input-field"
                  placeholder="jean.dupont@example.com"
                  required
                  disabled={loading}
                />
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label for="password" class="form-label">Mot de passe *</label>
                  <div class="relative">
                    <input
                      id="password"
                      type={showPassword ? 'text' : 'password'}
                      bind:value={formData.password}
                      class="input-field pr-12"
                      placeholder="••••••••"
                      minlength="8"
                      required
                      disabled={loading}
                    />
                    <button
                      type="button"
                      class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-primary-600 transition-colors"
                      on:click={() => showPassword = !showPassword}
                      tabindex="-1"
                      aria-label="Toggle password visibility"
                    >
                      {#if showPassword}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                        </svg>
                      {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      {/if}
                    </button>
                  </div>
                  
                  <!-- Password requirements checklist -->
                  {#if formData.password.length > 0}
                    <div class="mt-3 space-y-1.5">
                      <div class="flex items-center gap-2 text-sm {passwordReqs.minLength ? 'text-primary-600' : 'text-gray-500'}">
                        <svg class="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="{passwordReqs.minLength ? 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' : 'M10 18a8 8 0 100-16 8 8 0 000 16z'}" clip-rule="evenodd" />
                        </svg>
                        <span class="{passwordReqs.minLength ? 'font-medium' : ''}">Au moins 8 caractères</span>
                      </div>
                      <div class="flex items-center gap-2 text-sm {passwordReqs.hasUpper ? 'text-primary-600' : 'text-gray-500'}">
                        <svg class="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="{passwordReqs.hasUpper ? 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' : 'M10 18a8 8 0 100-16 8 8 0 000 16z'}" clip-rule="evenodd" />
                        </svg>
                        <span class="{passwordReqs.hasUpper ? 'font-medium' : ''}">Une lettre majuscule</span>
                      </div>
                      <div class="flex items-center gap-2 text-sm {passwordReqs.hasLower ? 'text-primary-600' : 'text-gray-500'}">
                        <svg class="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="{passwordReqs.hasLower ? 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' : 'M10 18a8 8 0 100-16 8 8 0 000 16z'}" clip-rule="evenodd" />
                        </svg>
                        <span class="{passwordReqs.hasLower ? 'font-medium' : ''}">Une lettre minuscule</span>
                      </div>
                      <div class="flex items-center gap-2 text-sm {passwordReqs.hasNumber ? 'text-primary-600' : 'text-gray-500'}">
                        <svg class="h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="{passwordReqs.hasNumber ? 'M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' : 'M10 18a8 8 0 100-16 8 8 0 000 16z'}" clip-rule="evenodd" />
                        </svg>
                        <span class="{passwordReqs.hasNumber ? 'font-medium' : ''}">Un chiffre</span>
                      </div>
                    </div>
                  {/if}
                </div>

                <div>
                  <label for="confirm_password" class="form-label">Confirmer mot de passe *</label>
                  <div class="relative">
                    <input
                      id="confirm_password"
                      type={showConfirmPassword ? 'text' : 'password'}
                      bind:value={confirmPassword}
                      class="input-field pr-12 {!passwordsMatch && confirmPassword ? 'border-error focus:ring-error' : ''}"
                      placeholder="••••••••"
                      minlength="8"
                      required
                      disabled={loading}
                    />
                    <button
                      type="button"
                      class="absolute inset-y-0 right-0 pr-4 flex items-center text-gray-500 hover:text-primary-600 transition-colors"
                      on:click={() => showConfirmPassword = !showConfirmPassword}
                      tabindex="-1"
                      aria-label="Toggle confirm password visibility"
                    >
                      {#if showConfirmPassword}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                        </svg>
                      {:else}
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                      {/if}
                    </button>
                  </div>
                  {#if !passwordsMatch && confirmPassword}
                    <p class="mt-2 text-sm text-error flex items-center gap-1">
                      <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
                      </svg>
                      Les mots de passe ne correspondent pas
                    </p>
                  {:else if passwordsMatch && confirmPassword && formData.password}
                    <p class="mt-2 text-sm text-primary-600 flex items-center gap-1">
                      <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                      </svg>
                      Les mots de passe correspondent
                    </p>
                  {/if}
                </div>
              </div>
            </div>

            <div class="flex justify-center pt-4">
              <button 
                type="button" 
                on:click={handleNextStep} 
                class="group relative px-12 py-3 rounded-xl font-semibold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none animate-slide-in-right overflow-hidden" 
                disabled={loading}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600 opacity-90"></div>
                <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
                <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
                  <span class="text-lg font-bold">Suivant</span>
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </span>
              </button>
            </div>
          {/if}

          {#if currentStep === 2}
            <!-- Step 2: Personal Information -->
            <div class="space-y-5 animate-fade-in">
              <div class="relative mb-6 p-5 rounded-2xl bg-gradient-to-r from-indigo-50 via-purple-50 to-indigo-50 border-l-4 border-indigo-600 shadow-sm">
                <div class="flex items-center gap-4">
                  <div class="w-16 h-16 rounded-xl flex items-center justify-center bg-gradient-to-br from-indigo-500 to-indigo-700 shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-2xl font-bold text-gray-900">Informations personnelles</h3>
                    <p class="text-sm text-indigo-700 font-semibold mt-1">Partagez vos coordonnées</p>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label for="phone" class="form-label">Téléphone</label>
                  <input
                    id="phone"
                    type="tel"
                    bind:value={formData.phone}
                    class="input-field"
                    placeholder="+33 6 12 34 56 78"
                    disabled={loading}
                  />
                </div>

                <div>
                  <label for="date_of_birth" class="form-label">Date de naissance</label>
                  <input
                    id="date_of_birth"
                    type="date"
                    bind:value={formData.date_of_birth}
                    class="input-field"
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label for="gender" class="form-label">Genre</label>
                <select
                  id="gender"
                  bind:value={formData.gender}
                  class="input-field"
                  disabled={loading}
                >
                  <option value="">Sélectionner...</option>
                  <option value="male">Homme</option>
                  <option value="female">Femme</option>
                  <option value="other">Autre</option>
                </select>
              </div>
            </div>

            <div class="flex gap-4 pt-4">
              <button 
                type="button" 
                on:click={prevStep} 
                class="group relative flex-1 px-6 py-3 rounded-xl font-semibold shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none animate-slide-in-left overflow-hidden" 
                disabled={loading}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-gray-100 to-gray-200"></div>
                <div class="absolute inset-0 bg-white/40 backdrop-blur-sm"></div>
                <div class="absolute inset-0 border-2 border-purple-400/30 rounded-xl"></div>
                <div class="absolute inset-0 bg-gradient-to-br from-purple-100/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <span class="relative flex items-center justify-center gap-2 text-gray-700 group-hover:text-purple-700 transition-colors duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:-translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
                  </svg>
                  <span class="text-lg font-bold">Précédent</span>
                </span>
              </button>
              <button 
                type="button" 
                on:click={nextStep} 
                class="group relative flex-1 px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none animate-slide-in-right overflow-hidden" 
                disabled={loading}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600 opacity-90"></div>
                <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
                <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
                  <span class="text-lg font-bold">Suivant</span>
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 7l5 5m0 0l-5 5m5-5H6" />
                  </svg>
                </span>
              </button>
            </div>
          {/if}

          {#if currentStep === 3}
            <!-- Step 3: Emergency Contact -->
            <div class="space-y-5 animate-fade-in">
              <div class="relative mb-6 p-5 rounded-2xl bg-gradient-to-r from-rose-50 via-pink-50 to-rose-50 border-l-4 border-rose-600 shadow-sm">
                <div class="flex items-center gap-4">
                  <div class="w-16 h-16 rounded-xl flex items-center justify-center bg-gradient-to-br from-rose-500 to-rose-700 shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                    </svg>
                  </div>
                  <div>
                    <h3 class="text-2xl font-bold text-gray-900">Contact d'urgence</h3>
                    <p class="text-sm text-rose-700 font-semibold mt-1">Pour votre sécurité et tranquillité</p>
                  </div>
                </div>
              </div>

              <div class="p-4 rounded-xl bg-primary-50 border border-primary-200">
                <p class="text-sm text-primary-700 leading-relaxed">
                  ℹ️ Ces informations nous permettront de contacter un proche en cas d'urgence médicale.
                </p>
              </div>

              <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
                <div>
                  <label for="emergency_contact_name" class="form-label">Nom du contact</label>
                  <input
                    id="emergency_contact_name"
                    type="text"
                    bind:value={formData.emergency_contact_name}
                    class="input-field"
                    placeholder="Marie Dupont"
                    disabled={loading}
                  />
                </div>

                <div>
                  <label for="emergency_contact_phone" class="form-label">Téléphone du contact</label>
                  <input
                    id="emergency_contact_phone"
                    type="tel"
                    bind:value={formData.emergency_contact_phone}
                    class="input-field"
                    placeholder="+33 6 98 76 54 32"
                    disabled={loading}
                  />
                </div>
              </div>

              <div>
                <label for="emergency_contact_relationship" class="form-label">Lien de parenté</label>
                <input
                  id="emergency_contact_relationship"
                  type="text"
                  bind:value={formData.emergency_contact_relationship}
                  class="input-field"
                  placeholder="Conjoint(e), Parent, Ami(e), etc."
                  disabled={loading}
                />
              </div>

              <div class="flex items-start gap-3 p-4 rounded-xl bg-warm-gray-100 transition-all hover:bg-primary-50">
                <input
                  id="marketing_consent"
                  type="checkbox"
                  bind:checked={formData.marketing_consent}
                  class="w-5 h-5 mt-0.5 rounded cursor-pointer transition-all"
                  style="accent-color: var(--color-primary-500);"
                  disabled={loading}
                />
                <label for="marketing_consent" class="text-sm text-neutral cursor-pointer flex-1">
                  J'accepte de recevoir des informations et offres promotionnelles concernant les services de santé
                </label>
              </div>
            </div>

            <div class="flex gap-4 pt-4">
              <button 
                type="button" 
                on:click={prevStep} 
                class="group relative flex-1 px-6 py-3 rounded-xl font-semibold shadow-md hover:shadow-lg transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none animate-slide-in-left overflow-hidden" 
                disabled={loading}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-gray-100 to-gray-200"></div>
                <div class="absolute inset-0 bg-white/40 backdrop-blur-sm"></div>
                <div class="absolute inset-0 border-2 border-purple-400/30 rounded-xl"></div>
                <div class="absolute inset-0 bg-gradient-to-br from-purple-100/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                <span class="relative flex items-center justify-center gap-2 text-gray-700 group-hover:text-purple-700 transition-colors duration-300">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:-translate-x-1 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M11 17l-5-5m0 0l5-5m-5 5h12" />
                  </svg>
                  <span class="text-lg font-bold">Précédent</span>
                </span>
              </button>
              <button 
                type="submit" 
                class="group relative flex-1 px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-2xl transform hover:scale-105 transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none overflow-hidden {loading ? 'animate-pulse' : 'animate-slide-in-right'}" 
                disabled={loading}
              >
                <div class="absolute inset-0 bg-gradient-to-r from-purple-500 via-indigo-500 to-purple-600 opacity-90"></div>
                <div class="absolute inset-0 bg-white/20 backdrop-blur-sm"></div>
                <div class="absolute inset-0 bg-gradient-to-br from-white/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                {#if loading}
                  <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
                    <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="text-lg font-bold">Inscription en cours...</span>
                  </span>
                {:else}
                  <span class="relative flex items-center justify-center gap-2 text-white drop-shadow-lg">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 group-hover:scale-110 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M5 13l4 4L19 7" />
                    </svg>
                    <span class="text-lg font-bold">Créer mon compte</span>
                  </span>
                {/if}
              </button>
            </div>
          {/if}
        </form>

        <!-- Login Link -->
        <div class="divider"></div>
        <div class="text-center">
          <p class="text-gray-700 font-medium">
            Déjà inscrit ?
            <button type="button" on:click={() => navigate('/login')} class="font-bold text-purple-600 hover:text-purple-700 underline decoration-2 underline-offset-2 transition-colors">
              Se connecter →
            </button>
          </p>
        </div>
      </div>
    {/if}

    <!-- Back to Home -->
    <div class="text-center mt-8">
      <button 
        type="button" 
        on:click={() => navigate('/')} 
        class="inline-flex items-center gap-2 text-gray-800 hover:text-purple-700 font-semibold transition-all hover:gap-3"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Retour à l'accueil
      </button>
    </div>
  </div>
</div>