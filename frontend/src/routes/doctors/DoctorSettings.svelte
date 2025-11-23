<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { 
    getCurrentDoctorProfile,
    updateDoctorProfile,
    getMySettings,
    updateMySettings,
    type DoctorProfile,
    type DoctorProfileUpdate,
    type Specialty,
    type DoctorSettings,
    type DoctorSettingsUpdate
  } from '../../lib/api-doctor';
  
  const dispatch = createEventDispatcher();
  
  let profile: DoctorProfile | null = null;
  let settings: DoctorSettings | null = null;
  let loading = true;
  let saving = false;
  let notificationsSaving = false;
  let preferencesSaving = false;
  let error: string | null = null;
  let successMessage: string | null = null;
  let activeSection: 'profile' | 'notifications' | 'preferences' | 'security' = 'profile';
  
  // Form data
  let formData: DoctorProfileUpdate = {};

  // Settings form state
  let settingsForm: DoctorSettingsUpdate = {
    email_notifications: true,
    sms_notifications: false,
    appointment_reminders: true,
    profile_visibility: 'public',
    show_phone: true,
    show_email: true,
    language: 'fr',
    timezone: 'Europe/Paris',
    payment_enabled: false,
    payment_methods: []
  };
  
  let paymentMethodsInput = '';

  const specialties: { value: Specialty; label: string }[] = [
    { value: 'general_practitioner', label: 'Médecin généraliste' },
    { value: 'cardiologist', label: 'Cardiologue' },
    { value: 'dermatologist', label: 'Dermatologue' },
    { value: 'pediatrician', label: 'Pédiatre' },
    { value: 'gynecologist', label: 'Gynécologue' },
    { value: 'psychiatrist', label: 'Psychiatre' },
    { value: 'orthopedist', label: 'Orthopédiste' },
    { value: 'ophthalmologist', label: 'Ophtalmologue' },
    { value: 'dentist', label: 'Dentiste' },
    { value: 'other', label: 'Autre' }
  ];

  onMount(async () => {
    await loadData();
  });

  const syncSettingsForm = (current: DoctorSettings) => {
    settings = current;
    settingsForm = {
      email_notifications: current.email_notifications,
      sms_notifications: current.sms_notifications,
      appointment_reminders: current.appointment_reminders,
      profile_visibility: current.profile_visibility,
      show_phone: current.show_phone,
      show_email: current.show_email,
      language: current.language,
      timezone: current.timezone,
      payment_enabled: current.payment_enabled,
      payment_methods: [...current.payment_methods]
    };
    paymentMethodsInput = current.payment_methods.join(', ');
  };

  const loadData = async () => {
    loading = true;
    error = null;
    try {
      profile = await getCurrentDoctorProfile();
      formData = {
        specialty: profile.specialty,
        rpps_number: profile.rpps_number,
        sub_specialty: profile.sub_specialty,
        office_address: profile.office_address,
        office_city: profile.office_city,
        office_postal_code: profile.office_postal_code,
        office_phone: profile.office_phone,
        biography: profile.biography,
        languages: profile.languages,
        education: profile.education,
        experience_years: profile.experience_years,
        consultation_types: profile.consultation_types,
        consultation_duration: profile.consultation_duration,
        consultation_price: profile.consultation_price,
        accepts_new_patients: profile.accepts_new_patients,
        is_public: profile.is_public
      };
    } catch (err: any) {
      console.error('Error loading profile:', err);
      error = 'Erreur lors du chargement du profil';
    }

    try {
      const loadedSettings = await getMySettings();
      syncSettingsForm(loadedSettings);
    } catch (err: any) {
      console.error('Error loading settings:', err);
      error = error ?? 'Erreur lors du chargement des paramètres';
    } finally {
      loading = false;
    }
  };

  const handleSaveProfile = async () => {
    saving = true;
    error = null;
    successMessage = null;
    try {
      await updateDoctorProfile(formData);
      successMessage = 'Profil mis à jour avec succès';
      await loadData();
      
      // Emit event to notify parent component (DoctorDashboard) to reload profile
      dispatch('profileUpdated');
    } catch (err: any) {
      console.error('Error updating profile:', err);
      error = 'Erreur lors de la mise à jour du profil';
    } finally {
      saving = false;
    }
  };

  const handleSaveNotifications = async () => {
    notificationsSaving = true;
    error = null;
    successMessage = null;
    try {
      const updated = await updateMySettings({
        email_notifications: settingsForm.email_notifications,
        sms_notifications: settingsForm.sms_notifications
      });
      syncSettingsForm(updated);
      successMessage = 'Préférences de notification mises à jour';
      setTimeout(() => successMessage = null, 3000);
    } catch (err: any) {
      console.error('Error saving notifications:', err);
      error = 'Erreur lors de la mise à jour des notifications';
    } finally {
      notificationsSaving = false;
    }
  };

  const handleSavePreferences = async () => {
    preferencesSaving = true;
    error = null;
    successMessage = null;
    try {
      const updated = await updateMySettings({
        appointment_reminders: settingsForm.appointment_reminders,
        profile_visibility: settingsForm.profile_visibility,
        show_phone: settingsForm.show_phone,
        show_email: settingsForm.show_email,
        language: settingsForm.language,
        timezone: settingsForm.timezone,
        payment_enabled: settingsForm.payment_enabled,
        payment_methods: paymentMethodsInput
          .split(',')
          .map(method => method.trim())
          .filter(Boolean)
      });
      syncSettingsForm(updated);
      successMessage = 'Préférences mises à jour avec succès';
      setTimeout(() => successMessage = null, 3000);
    } catch (err: any) {
      console.error('Error saving preferences:', err);
      error = 'Erreur lors de la mise à jour des préférences';
    } finally {
      preferencesSaving = false;
    }
  };
</script>

<div class="space-y-6">
  <!-- Header -->
  <div>
    <h2 class="text-2xl font-bold text-gray-900">Paramètres</h2>
    <p class="text-gray-600 mt-1">Gérez votre profil et vos préférences</p>
  </div>

  {#if successMessage}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4 animate-fade-in">
      <div class="flex items-center gap-2">
        <svg class="h-5 w-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
        </svg>
        <p class="text-green-800">{successMessage}</p>
      </div>
    </div>
  {/if}

  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{error}</p>
    </div>
  {/if}

  <div class="bg-white rounded-lg border border-gray-200 overflow-hidden">
    <!-- Tabs -->
    <div class="border-b border-gray-200 overflow-x-auto">
      <nav class="flex -mb-px min-w-max">
        <button
          on:click={() => activeSection = 'profile'}
          class="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap touch-target {activeSection === 'profile' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Profil professionnel
        </button>
        <button
          on:click={() => activeSection = 'notifications'}
          class="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap touch-target {activeSection === 'notifications' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Notifications
        </button>
        <button
          on:click={() => activeSection = 'preferences'}
          class="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap touch-target {activeSection === 'preferences' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Préférences
        </button>
        <button
          on:click={() => activeSection = 'security'}
          class="px-4 sm:px-6 py-3 sm:py-4 text-xs sm:text-sm font-medium border-b-2 transition-colors whitespace-nowrap touch-target {activeSection === 'security' ? 'border-emerald-500 text-emerald-600' : 'border-transparent text-gray-500 hover:text-gray-700'}"
        >
          Sécurité
        </button>
      </nav>
    </div>

    <!-- Content -->
    <div class="p-4 sm:p-6">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <svg class="animate-spin h-8 w-8 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        </div>
      {:else if activeSection === 'profile'}
        <!-- Profile Section -->
        <form on:submit|preventDefault={handleSaveProfile} class="space-y-6 max-w-2xl">
          <div>
            <label for="specialty" class="block text-sm font-medium text-gray-700 mb-2">Spécialité</label>
            <select
              id="specialty"
              bind:value={formData.specialty}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
            >
              {#each specialties as specialty}
                <option value={specialty.value}>{specialty.label}</option>
              {/each}
            </select>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label for="rpps-number" class="block text-sm font-medium text-gray-700 mb-2">
                Numéro RPPS
                <span class="text-xs text-gray-500">(11 chiffres)</span>
              </label>
              <input
                id="rpps-number"
                type="text"
                bind:value={formData.rpps_number}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="12345678901"
                maxlength="11"
                pattern="\d{11}"
              />
              <p class="mt-1 text-sm text-gray-500">Répertoire Partagé des Professionnels de Santé</p>
            </div>

            <div>
              <label for="sub-specialty" class="block text-sm font-medium text-gray-700 mb-2">Sous-spécialité</label>
              <input
                id="sub-specialty"
                type="text"
                bind:value={formData.sub_specialty}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="Ex: Cardiologie interventionnelle"
              />
            </div>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label for="experience-years" class="block text-sm font-medium text-gray-700 mb-2">Années d'expérience</label>
              <input
                id="experience-years"
                type="number"
                bind:value={formData.experience_years}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="10"
                min="0"
              />
            </div>

            <div>
              <label for="office-phone" class="block text-sm font-medium text-gray-700 mb-2">Téléphone du cabinet</label>
              <input
                id="office-phone"
                type="tel"
                bind:value={formData.office_phone}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="+33 1 23 45 67 89"
              />
            </div>
          </div>

          <div>
            <label for="consultation-price" class="block text-sm font-medium text-gray-700 mb-2">Tarif de consultation</label>
            <div class="relative">
              <input
                id="consultation-price"
                type="number"
                bind:value={formData.consultation_price}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 pr-12"
                placeholder="50"
                min="0"
                step="0.01"
              />
              <span class="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-500">
                FCFA
              </span>
            </div>
            <p class="mt-1 text-sm text-gray-500">💰 Tarif en Francs CFA (FCFA)</p>
          </div>

          <div>
            <label for="office-address" class="block text-sm font-medium text-gray-700 mb-2">Adresse du cabinet</label>
            <input
              id="office-address"
              type="text"
              bind:value={formData.office_address}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              placeholder="123 Rue de la Santé"
            />
          </div>

          <div>
            <label for="biography" class="block text-sm font-medium text-gray-700 mb-2">Biographie professionnelle</label>
            <textarea
              id="biography"
              bind:value={formData.biography}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
              rows="6"
              placeholder="Parlez-nous de votre parcours..."
            ></textarea>
          </div>

          <div class="flex justify-end">
            <button
              type="submit"
              class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
              disabled={saving}
            >
              {saving ? 'Enregistrement...' : 'Enregistrer les modifications'}
            </button>
          </div>
        </form>

      {:else if activeSection === 'notifications'}
        <!-- Notifications Section -->
        <div class="space-y-6 max-w-2xl">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Notifications par email</h3>
            <div class="space-y-3">
              <label class="flex items-center gap-3">
                <input
                  type="checkbox"
                  bind:checked={settingsForm.email_notifications}
                  class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  disabled={notificationsSaving}
                />
                <div>
                  <p class="font-medium text-gray-900">Nouveaux rendez-vous</p>
                  <p class="text-sm text-gray-500">Recevoir un email pour chaque nouveau rendez-vous</p>
                </div>
              </label>
              <label class="flex items-center gap-3">
                <input
                  type="checkbox"
                  bind:checked={settingsForm.sms_notifications}
                  class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  disabled={notificationsSaving}
                />
                <div>
                  <p class="font-medium text-gray-900">Notifications SMS</p>
                  <p class="text-sm text-gray-500">Recevoir un SMS pour les rendez-vous importants</p>
                </div>
              </label>
            </div>
          </div>

          <div class="flex justify-end">
            <button
              on:click={handleSaveNotifications}
              class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
              disabled={notificationsSaving}
            >
              {notificationsSaving ? 'Enregistrement...' : 'Enregistrer les préférences'}
            </button>
          </div>
        </div>

      {:else if activeSection === 'preferences'}
        <!-- Preferences Section -->
        <div class="space-y-6 max-w-2xl">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Gestion des rendez-vous</h3>
            <div class="space-y-4">
              <label class="flex items-center gap-3">
                <input
                  type="checkbox"
                  bind:checked={settingsForm.appointment_reminders}
                  class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  disabled={preferencesSaving}
                />
                <div>
                  <span class="font-medium text-gray-900">Rappels automatiques</span>
                  <p class="text-sm text-gray-500">Envoyer des rappels aux patients avant leurs rendez-vous</p>
                </div>
              </label>
            </div>
          </div>

          <div class="border-t border-gray-200 pt-6 space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">Visibilité du profil</h3>
            <div>
              <label for="profile-visibility" class="block text-sm font-medium text-gray-700 mb-2">Visibilité</label>
              <select
                id="profile-visibility"
                bind:value={settingsForm.profile_visibility}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                disabled={preferencesSaving}
              >
                <option value="public">Public</option>
                <option value="private">Privé</option>
                <option value="restricted">Restreint</option>
              </select>
            </div>
            <div class="space-y-3">
              <label class="flex items-center gap-3">
                <input
                  type="checkbox"
                  bind:checked={settingsForm.show_phone}
                  class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  disabled={preferencesSaving}
                />
                <span class="text-sm text-gray-700">Afficher le numéro de téléphone</span>
              </label>
              <label class="flex items-center gap-3">
                <input
                  type="checkbox"
                  bind:checked={settingsForm.show_email}
                  class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  disabled={preferencesSaving}
                />
                <span class="text-sm text-gray-700">Afficher l'email professionnel</span>
              </label>
            </div>
          </div>

          <div class="border-t border-gray-200 pt-6 space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">Langue et fuseau horaire</h3>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label for="settings-language" class="block text-sm font-medium text-gray-700 mb-2">Langue</label>
                <input
                  id="settings-language"
                  type="text"
                  bind:value={settingsForm.language}
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  disabled={preferencesSaving}
                  placeholder="fr"
                />
              </div>
              <div>
                <label for="settings-timezone" class="block text-sm font-medium text-gray-700 mb-2">Fuseau horaire</label>
                <input
                  id="settings-timezone"
                  type="text"
                  bind:value={settingsForm.timezone}
                  class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                  disabled={preferencesSaving}
                  placeholder="Europe/Paris"
                />
              </div>
            </div>
          </div>

          <div class="border-t border-gray-200 pt-6 space-y-4">
            <h3 class="text-lg font-semibold text-gray-900">Paiements</h3>
            <label class="flex items-center gap-3">
              <input
                type="checkbox"
                bind:checked={settingsForm.payment_enabled}
                class="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                disabled={preferencesSaving}
              />
              <span class="text-sm text-gray-700">Activer les paiements en ligne</span>
            </label>
            <div>
              <label for="payment-methods" class="block text-sm font-medium text-gray-700 mb-2">
                Méthodes de paiement acceptées
              </label>
              <input
                id="payment-methods"
                type="text"
                bind:value={paymentMethodsInput}
                class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
                disabled={preferencesSaving || !settingsForm.payment_enabled}
                placeholder="Carte bancaire, Virement..."
              />
              <p class="mt-1 text-sm text-gray-500">Séparez les méthodes par des virgules</p>
            </div>
          </div>

          <div class="flex justify-end">
            <button
              on:click={handleSavePreferences}
              class="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
              disabled={preferencesSaving}
            >
              {preferencesSaving ? 'Enregistrement...' : 'Enregistrer les préférences'}
            </button>
          </div>
        </div>

      {:else if activeSection === 'security'}
        <!-- Security Section -->
        <div class="space-y-6 max-w-2xl">
          <div>
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Mot de passe</h3>
            <p class="text-gray-600 mb-4">Pour changer votre mot de passe, contactez l'administrateur</p>
            <button
              class="px-6 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
            >
              Demander un changement de mot de passe
            </button>
          </div>

          <div class="border-t border-gray-200 pt-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Sessions actives</h3>
            <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
              <div class="flex items-center justify-between">
                <div>
                  <p class="font-medium text-gray-900">Session actuelle</p>
                  <p class="text-sm text-gray-500">Connecté depuis ce navigateur</p>
                </div>
                <span class="px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full">Active</span>
              </div>
            </div>
          </div>

          <div class="border-t border-gray-200 pt-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Supprimer le compte</h3>
            <p class="text-gray-600 mb-4">
              La suppression de votre compte est permanente et irréversible.
            </p>
            <button
              class="px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              Supprimer mon compte
            </button>
          </div>
        </div>
      {/if}
    </div>
  </div>
</div>
