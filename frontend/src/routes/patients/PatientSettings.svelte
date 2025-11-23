<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import {
    getPatientProfile,
    updatePatientProfile,
    type PatientProfile,
    type PatientProfileUpdatePayload
  } from '../../lib/api-patient';

  export let profile: PatientProfile | null = null;

  const dispatch = createEventDispatcher();

  let loading = true;
  let submitting = false;
  let error: string | null = null;
  let success: string | null = null;
  let initialised = false;

  let lastProfileTimestamp: string | null = null;

  let form: PatientProfileUpdatePayload = {
    first_name: '',
    last_name: '',
    phone: '',
    gender: '',
    date_of_birth: '',
    address_line1: '',
    address_line2: '',
    city: '',
    postal_code: '',
    country: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: ''
  };

  onMount(() => {
    void ensureProfile();
  });

  const ensureProfile = async () => {
    if (profile) {
      populateForm(profile);
      loading = false;
      return;
    }
    try {
      const fetched = await getPatientProfile();
      profile = fetched;
      populateForm(fetched);
    } catch (err) {
      console.error('Erreur lors du chargement du profil patient:', err);
      error = 'Impossible de charger vos informations';
    } finally {
      loading = false;
    }
  };

  const populateForm = (data: PatientProfile, force = false) => {
    if (initialised && !force) return;
    form = {
      first_name: data.first_name ?? '',
      last_name: data.last_name ?? '',
      phone: data.phone ?? '',
      gender: data.gender ?? '',
      date_of_birth: data.date_of_birth ?? '',
      address_line1: data.address_line1 ?? '',
      address_line2: data.address_line2 ?? '',
      city: data.city ?? '',
      postal_code: data.postal_code ?? '',
      country: data.country ?? '',
      emergency_contact_name: data.emergency_contact_name ?? '',
      emergency_contact_phone: data.emergency_contact_phone ?? '',
      emergency_contact_relationship: data.emergency_contact_relationship ?? ''
    };
    initialised = true;
    lastProfileTimestamp = data.updated_at ?? data.created_at;
  };

  $: if (profile && lastProfileTimestamp && (profile.updated_at ?? profile.created_at) !== lastProfileTimestamp) {
    populateForm(profile, true);
  }

  const handleSubmit = async () => {
    submitting = true;
    error = null;
    success = null;
    try {
      const payload: PatientProfileUpdatePayload = {
        ...form,
        first_name: form.first_name?.trim() || undefined,
        last_name: form.last_name?.trim() || undefined,
        phone: form.phone?.trim() || undefined,
        gender: form.gender || undefined,
        date_of_birth: form.date_of_birth || undefined,
        address_line1: form.address_line1?.trim() || undefined,
        address_line2: form.address_line2?.trim() || undefined,
        city: form.city?.trim() || undefined,
        postal_code: form.postal_code?.trim() || undefined,
        country: form.country?.trim() || undefined,
        emergency_contact_name: form.emergency_contact_name?.trim() || undefined,
        emergency_contact_phone: form.emergency_contact_phone?.trim() || undefined,
        emergency_contact_relationship: form.emergency_contact_relationship?.trim() || undefined
      };

      const updated = await updatePatientProfile(payload);
      profile = updated;
      success = 'Votre profil a été mis à jour.';
      dispatch('refresh');
    } catch (err: any) {
      console.error('Erreur lors de la mise à jour du profil patient:', err);
      error = err?.response?.data?.detail ?? 'Impossible de sauvegarder vos modifications';
    } finally {
      submitting = false;
    }
  };
</script>

<div class="space-y-6">
  <!-- Professional Header -->
  <div class="relative overflow-hidden rounded-2xl bg-gradient-to-r from-purple-600 via-pink-600 to-purple-700 p-6 shadow-lg">
    <div class="relative z-10">
      <div class="flex items-center gap-4">
        <div class="w-14 h-14 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <div>
          <h2 class="text-2xl font-bold text-white">Paramètres du patient</h2>
          <p class="text-sm text-purple-100">Mettez à jour vos informations personnelles</p>
        </div>
      </div>
    </div>
  </div>

  <div class="bg-white border border-gray-200 rounded-xl sm:rounded-2xl shadow-md p-4 sm:p-6 md:p-8">
    {#if loading}
      <div class="py-16 flex items-center justify-center">
        <div class="text-center">
          <div class="w-16 h-16 border-4 border-purple-200 border-t-purple-600 rounded-full animate-spin mx-auto mb-4"></div>
          <p class="text-lg font-semibold text-gray-900">Chargement...</p>
        </div>
      </div>
    {:else}
      <form class="space-y-8" on:submit|preventDefault={handleSubmit}>
        {#if error}
          <div class="bg-red-50 border-l-4 border-red-500 text-red-700 px-5 py-4 rounded-xl shadow-sm">{error}</div>
        {/if}
        {#if success}
          <div class="bg-emerald-50 border-l-4 border-emerald-500 text-emerald-800 px-5 py-4 rounded-xl shadow-sm flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            {success}
          </div>
        {/if}

        <div>
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
            Informations personnelles
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
          <div>
            <label for="patient-first-name" class="block text-sm font-semibold text-gray-700 mb-2">Prénom</label>
            <input
              id="patient-first-name"
              type="text"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.first_name}
              autocomplete="given-name"
            />
          </div>
          <div>
            <label for="patient-last-name" class="block text-sm font-semibold text-gray-700 mb-2">Nom</label>
            <input
              id="patient-last-name"
              type="text"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.last_name}
              autocomplete="family-name"
            />
          </div>
          <div>
            <label for="patient-phone" class="block text-sm font-semibold text-gray-700 mb-2">Téléphone</label>
            <input
              id="patient-phone"
              type="tel"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.phone}
              autocomplete="tel"
            />
          </div>
          <div>
            <label for="patient-gender" class="block text-sm font-semibold text-gray-700 mb-2">Genre</label>
            <select
              id="patient-gender"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all bg-white"
              bind:value={form.gender}
            >
              <option value="">Non précisé</option>
              <option value="female">Femme</option>
              <option value="male">Homme</option>
              <option value="non_binary">Non binaire</option>
              <option value="other">Autre</option>
            </select>
          </div>
          <div>
            <label for="patient-dob" class="block text-sm font-semibold text-gray-700 mb-2">Date de naissance</label>
            <input
              id="patient-dob"
              type="date"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.date_of_birth}
              autocomplete="bday"
            />
          </div>
        </div>
        </div>

        <div class="space-y-4 pt-4 border-t border-gray-200">
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Adresse
          </h3>
          <div>
            <label for="patient-address-line1" class="block text-sm font-semibold text-gray-700 mb-2">Adresse</label>
            <input
              id="patient-address-line1"
              type="text"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.address_line1}
              autocomplete="address-line1"
            />
          </div>
          <div>
            <label for="patient-address-line2" class="block text-sm font-semibold text-gray-700 mb-2">Complément d'adresse</label>
            <input
              id="patient-address-line2"
              type="text"
              class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
              bind:value={form.address_line2}
              autocomplete="address-line2"
            />
          </div>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label for="patient-city" class="block text-sm font-semibold text-gray-700 mb-2">Ville</label>
              <input
                id="patient-city"
                type="text"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.city}
                autocomplete="address-level2"
              />
            </div>
            <div>
              <label for="patient-postal-code" class="block text-sm font-semibold text-gray-700 mb-2">Code postal</label>
              <input
                id="patient-postal-code"
                type="text"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.postal_code}
                autocomplete="postal-code"
              />
            </div>
            <div>
              <label for="patient-country" class="block text-sm font-semibold text-gray-700 mb-2">Pays</label>
              <input
                id="patient-country"
                type="text"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.country}
                autocomplete="country-name"
              />
            </div>
          </div>
        </div>

        <div class="pt-6 border-t border-gray-200">
          <h3 class="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            Contact d'urgence
          </h3>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-5">
            <div>
              <label for="emergency-name" class="block text-sm font-semibold text-gray-700 mb-2">Nom</label>
              <input
                id="emergency-name"
                type="text"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.emergency_contact_name}
                placeholder="Nom du contact"
              />
            </div>
            <div>
              <label for="emergency-phone" class="block text-sm font-semibold text-gray-700 mb-2">Téléphone</label>
              <input
                id="emergency-phone"
                type="tel"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.emergency_contact_phone}
                placeholder="+33 6 XX XX XX XX"
              />
            </div>
            <div>
              <label for="emergency-relationship" class="block text-sm font-semibold text-gray-700 mb-2">Lien</label>
              <input
                id="emergency-relationship"
                type="text"
                class="w-full px-4 py-3 border-2 border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                bind:value={form.emergency_contact_relationship}
                placeholder="Conjoint, parent, ami..."
              />
            </div>
          </div>
        </div>

        <div class="flex justify-end pt-4">
          <button
            type="submit"
            class="px-8 py-3.5 bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-xl hover:from-purple-700 hover:to-pink-700 transition-all disabled:opacity-50 font-semibold shadow-lg hover:shadow-xl flex items-center gap-2"
            disabled={submitting}
          >
            {#if submitting}
              <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Sauvegarde...
            {:else}
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              Enregistrer les modifications
            {/if}
          </button>
        </div>
      </form>
    {/if}
  </div>
</div>
