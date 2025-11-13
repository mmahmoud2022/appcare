<script lang="ts">
  import { onMount } from 'svelte';
  import {
    getMyPatients,
    uploadPatientDocument,
    issueElectronicPrescription,
    getDoctorPrescriptions,
    type PatientBasicInfo,
    type ElectronicPrescription,
    type PrescriptionMedication,
  } from '../../lib/api-doctor';

  let activeTab: 'upload' | 'prescription' = 'upload';
  let patients: PatientBasicInfo[] = [];
  let prescriptions: ElectronicPrescription[] = [];
  let loading = false;
  let error: string | null = null;
  let successMessage: string | null = null;

  // Upload Document Form
  let uploadForm = {
    patient_id: 0,
    title: '',
    description: '',
    document_type: 'medical_report',
    file: null as File | null,
  };
  let uploadingDocument = false;

  // Electronic Prescription Form
  let prescriptionForm = {
    patient_id: 0,
    medications: [
      {
        name: '',
        dosage: '',
        frequency: '',
        duration: '',
        notes: '',
      },
    ] as PrescriptionMedication[],
    instructions: '',
    expires_at: '',
  };
  let issuingPrescription = false;

  // View Prescriptions
  let viewingPrescriptions = false;
  let selectedPatientId: number | undefined;

  onMount(async () => {
    await loadPatients();
  });

  const loadPatients = async () => {
    loading = true;
    error = null;
    try {
      const response = await getMyPatients(1, 100);
      patients = response.items || [];
    } catch (err: any) {
      console.error('Error loading patients:', err);
      error = 'Erreur lors du chargement des patients';
    } finally {
      loading = false;
    }
  };

  const loadPrescriptions = async (patientId?: number) => {
    viewingPrescriptions = true;
    error = null;
    try {
      const response = await getDoctorPrescriptions(1, 50, patientId);
      prescriptions = response.items || [];
    } catch (err: any) {
      console.error('Error loading prescriptions:', err);
      error = 'Erreur lors du chargement des prescriptions';
    } finally {
      viewingPrescriptions = false;
    }
  };

  const handleFileChange = (event: Event) => {
    const target = event.target as HTMLInputElement;
    if (target.files && target.files.length > 0) {
      uploadForm.file = target.files[0];
    }
  };

  const handleUploadDocument = async () => {
    if (!uploadForm.file) {
      error = 'Veuillez sélectionner un fichier';
      return;
    }

    if (!uploadForm.patient_id) {
      error = 'Veuillez sélectionner un patient';
      return;
    }

    if (!uploadForm.title.trim()) {
      error = 'Veuillez entrer un titre';
      return;
    }

    uploadingDocument = true;
    error = null;
    successMessage = null;

    try {
      await uploadPatientDocument({
        patient_id: uploadForm.patient_id,
        title: uploadForm.title,
        description: uploadForm.description || undefined,
        document_type: uploadForm.document_type || undefined,
        file: uploadForm.file,
      });

      successMessage = 'Document téléchargé avec succès !';
      // Reset form
      uploadForm = {
        patient_id: 0,
        title: '',
        description: '',
        document_type: 'medical_report',
        file: null,
      };
      // Reset file input
      const fileInput = document.getElementById('document-file') as HTMLInputElement;
      if (fileInput) fileInput.value = '';
    } catch (err: any) {
      console.error('Error uploading document:', err);
      error = err.response?.data?.detail || 'Erreur lors du téléchargement du document';
    } finally {
      uploadingDocument = false;
    }
  };

  const addMedication = () => {
    prescriptionForm.medications = [
      ...prescriptionForm.medications,
      {
        name: '',
        dosage: '',
        frequency: '',
        duration: '',
        notes: '',
      },
    ];
  };

  const removeMedication = (index: number) => {
    prescriptionForm.medications = prescriptionForm.medications.filter(
      (_, i) => i !== index
    );
  };

  const handleIssuePrescription = async () => {
    if (!prescriptionForm.patient_id) {
      error = 'Veuillez sélectionner un patient';
      return;
    }

    if (prescriptionForm.medications.length === 0) {
      error = 'Veuillez ajouter au moins un médicament';
      return;
    }

    // Validate medications
    for (const med of prescriptionForm.medications) {
      if (!med.name.trim()) {
        error = 'Tous les médicaments doivent avoir un nom';
        return;
      }
    }

    issuingPrescription = true;
    error = null;
    successMessage = null;

    try {
      await issueElectronicPrescription({
        patient_id: prescriptionForm.patient_id,
        medications: prescriptionForm.medications.map((m) => ({
          name: m.name,
          dosage: m.dosage || undefined,
          frequency: m.frequency || undefined,
          duration: m.duration || undefined,
          notes: m.notes || undefined,
        })),
        instructions: prescriptionForm.instructions || undefined,
        expires_at: prescriptionForm.expires_at || undefined,
      });

      successMessage = 'Prescription électronique créée avec succès !';
      // Reset form
      prescriptionForm = {
        patient_id: 0,
        medications: [
          {
            name: '',
            dosage: '',
            frequency: '',
            duration: '',
            notes: '',
          },
        ],
        instructions: '',
        expires_at: '',
      };
    } catch (err: any) {
      console.error('Error issuing prescription:', err);
      error = err.response?.data?.detail || 'Erreur lors de la création de la prescription';
    } finally {
      issuingPrescription = false;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getPrescriptionStatusClass = (status: string) => {
    switch (status) {
      case 'issued':
        return 'bg-green-100 text-green-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      case 'expired':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const getPrescriptionStatusLabel = (status: string) => {
    switch (status) {
      case 'issued':
        return 'Délivrée';
      case 'cancelled':
        return 'Annulée';
      case 'expired':
        return 'Expirée';
      default:
        return status;
    }
  };
</script>

<div class="space-y-6">
  <!-- Header -->
  <div>
    <h2 class="text-2xl font-bold text-gray-900">Documents & Prescriptions</h2>
    <p class="text-gray-600 mt-1">Gérez les documents médicaux et les prescriptions électroniques</p>
  </div>

  <!-- Alerts -->
  {#if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
      <p class="text-red-800">{error}</p>
      <button on:click={() => (error = null)} class="ml-auto text-red-600 hover:text-red-800" aria-label="Fermer l'alerte">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {/if}

  {#if successMessage}
    <div class="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-5 w-5 text-green-600 mt-0.5 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
      <p class="text-green-800">{successMessage}</p>
      <button on:click={() => (successMessage = null)} class="ml-auto text-green-600 hover:text-green-800" aria-label="Fermer le message">
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  {/if}

  <!-- Tabs -->
  <div class="border-b border-gray-200">
    <nav class="flex space-x-8" aria-label="Tabs">
      <button
        on:click={() => (activeTab = 'upload')}
        class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'upload'
          ? 'border-emerald-500 text-emerald-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
      >
        <div class="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          Upload Document
        </div>
      </button>
      <button
        on:click={() => (activeTab = 'prescription')}
        class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors {activeTab === 'prescription'
          ? 'border-emerald-500 text-emerald-600'
          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}"
      >
        <div class="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Prescription Électronique
        </div>
      </button>
      <button
        on:click={() => {
          loadPrescriptions();
        }}
        class="pb-4 px-1 border-b-2 font-medium text-sm transition-colors border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
      >
        <div class="flex items-center gap-2">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          Voir les Prescriptions
        </div>
      </button>
    </nav>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <svg
        class="animate-spin h-8 w-8 text-emerald-600"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
    </div>
  {:else if patients.length === 0}
    <!-- No Patients Message -->
    <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border-2 border-dashed border-blue-200 p-8">
      <div class="text-center">
        <div class="w-20 h-20 bg-gradient-to-br from-blue-100 to-indigo-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <h3 class="text-xl font-bold text-gray-900 mb-2">Aucun patient trouvé</h3>
        <p class="text-gray-600 mb-4 max-w-md mx-auto">
          Vous n'avez pas encore de patients. Les patients apparaîtront ici après qu'ils aient pris un rendez-vous avec vous.
        </p>
        <div class="flex items-center justify-center gap-2 text-sm text-gray-500">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Les patients sont automatiquement ajoutés lorsqu'ils prennent rendez-vous</span>
        </div>
      </div>
    </div>
  {:else}
    <!-- Upload Document Tab -->
    {#if activeTab === 'upload'}
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">Télécharger un document médical</h3>

        <div class="space-y-4">
          <!-- Patient Selection -->
          <div>
            <label for="upload-patient" class="block text-sm font-medium text-gray-700 mb-2">
              Patient <span class="text-red-500">*</span>
            </label>
            <select
              id="upload-patient"
              bind:value={uploadForm.patient_id}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              required
            >
              <option value={0}>
                {patients.length > 0 ? 'Sélectionner un patient...' : 'Aucun patient disponible'}
              </option>
              {#each patients as patient}
                <option value={patient.id}>
                  {patient.first_name}
                  {patient.last_name} ({patient.email})
                </option>
              {/each}
            </select>
            {#if patients.length === 0}
              <p class="mt-1 text-sm text-amber-600 flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Aucun patient n'a encore pris rendez-vous avec vous
              </p>
            {/if}
          </div>

          <!-- Document Type -->
          <div>
            <label for="document-type" class="block text-sm font-medium text-gray-700 mb-2">
              Type de document
            </label>
            <select
              id="document-type"
              bind:value={uploadForm.document_type}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            >
              <option value="medical_report">Rapport médical</option>
              <option value="lab_result">Résultat de laboratoire</option>
              <option value="imaging">Imagerie</option>
              <option value="prescription">Prescription</option>
              <option value="other">Autre</option>
            </select>
          </div>

          <!-- Title -->
          <div>
            <label for="document-title" class="block text-sm font-medium text-gray-700 mb-2">
              Titre <span class="text-red-500">*</span>
            </label>
            <input
              id="document-title"
              type="text"
              bind:value={uploadForm.title}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="Ex: Résultat de l'analyse sanguine"
              required
            />
          </div>

          <!-- Description -->
          <div>
            <label for="document-description" class="block text-sm font-medium text-gray-700 mb-2">
              Description
            </label>
            <textarea
              id="document-description"
              bind:value={uploadForm.description}
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="Description du document..."
            ></textarea>
          </div>

          <!-- File Upload -->
          <div>
            <label for="document-file" class="block text-sm font-medium text-gray-700 mb-2">
              Fichier <span class="text-red-500">*</span>
            </label>
            <input
              id="document-file"
              type="file"
              on:change={handleFileChange}
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100"
              required
            />
            <p class="mt-1 text-sm text-gray-500">
              Formats acceptés: PDF, Word, Images (max. 10 MB)
            </p>
            {#if uploadForm.file}
              <p class="mt-2 text-sm text-emerald-600">
                Fichier sélectionné: {uploadForm.file.name}
              </p>
            {/if}
          </div>

          <!-- Submit Button -->
          <div class="pt-4">
            <button
              on:click={handleUploadDocument}
              disabled={uploadingDocument || !uploadForm.file || !uploadForm.patient_id || !uploadForm.title}
              class="w-full px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {uploadingDocument ? 'Téléchargement en cours...' : 'Télécharger le document'}
            </button>
          </div>
        </div>
      </div>
    {/if}

    <!-- Electronic Prescription Tab -->
    {#if activeTab === 'prescription'}
      <div class="bg-white rounded-xl border border-gray-200 p-6">
        <h3 class="text-lg font-semibold text-gray-900 mb-6">Créer une prescription électronique</h3>

        <div class="space-y-6">
          <!-- Patient Selection -->
          <div>
            <label for="prescription-patient" class="block text-sm font-medium text-gray-700 mb-2">
              Patient <span class="text-red-500">*</span>
            </label>
            <select
              id="prescription-patient"
              bind:value={prescriptionForm.patient_id}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              required
            >
              <option value={0}>
                {patients.length > 0 ? 'Sélectionner un patient...' : 'Aucun patient disponible'}
              </option>
              {#each patients as patient}
                <option value={patient.id}>
                  {patient.first_name}
                  {patient.last_name} ({patient.email})
                </option>
              {/each}
            </select>
            {#if patients.length === 0}
              <p class="mt-1 text-sm text-amber-600 flex items-center gap-1">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                Aucun patient n'a encore pris rendez-vous avec vous
              </p>
            {/if}
          </div>

          <!-- Medications -->
          <div>
            <div class="flex items-center justify-between mb-4">
              <div class="block text-sm font-medium text-gray-700">
                Médicaments <span class="text-red-500">*</span>
              </div>
              <button
                on:click={addMedication}
                class="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 transition-colors text-sm font-medium"
              >
                + Ajouter un médicament
              </button>
            </div>

            <div class="space-y-4">
              {#each prescriptionForm.medications as medication, index}
                <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div class="flex items-center justify-between mb-3">
                    <h4 class="font-medium text-gray-900">Médicament {index + 1}</h4>
                    {#if prescriptionForm.medications.length > 1}
                      <button
                        on:click={() => removeMedication(index)}
                        class="text-red-600 hover:text-red-800 text-sm font-medium"
                      >
                        Supprimer
                      </button>
                    {/if}
                  </div>

                  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div class="md:col-span-2">
                      <label for="med-name-{index}" class="block text-sm font-medium text-gray-700 mb-1">
                        Nom du médicament <span class="text-red-500">*</span>
                      </label>
                      <input
                        id="med-name-{index}"
                        type="text"
                        bind:value={medication.name}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ex: Amoxicilline"
                        required
                      />
                    </div>

                    <div>
                      <label for="med-dosage-{index}" class="block text-sm font-medium text-gray-700 mb-1">
                        Dosage
                      </label>
                      <input
                        id="med-dosage-{index}"
                        type="text"
                        bind:value={medication.dosage}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ex: 500mg"
                      />
                    </div>

                    <div>
                      <label for="med-frequency-{index}" class="block text-sm font-medium text-gray-700 mb-1">
                        Fréquence
                      </label>
                      <input
                        id="med-frequency-{index}"
                        type="text"
                        bind:value={medication.frequency}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ex: 3 fois par jour"
                      />
                    </div>

                    <div>
                      <label for="med-duration-{index}" class="block text-sm font-medium text-gray-700 mb-1">
                        Durée
                      </label>
                      <input
                        id="med-duration-{index}"
                        type="text"
                        bind:value={medication.duration}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ex: 7 jours"
                      />
                    </div>

                    <div class="md:col-span-1">
                      <label for="med-notes-{index}" class="block text-sm font-medium text-gray-700 mb-1">
                        Notes
                      </label>
                      <input
                        id="med-notes-{index}"
                        type="text"
                        bind:value={medication.notes}
                        class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                        placeholder="Ex: À prendre avec un repas"
                      />
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <!-- Instructions -->
          <div>
            <label for="prescription-instructions" class="block text-sm font-medium text-gray-700 mb-2">
              Instructions générales
            </label>
            <textarea
              id="prescription-instructions"
              bind:value={prescriptionForm.instructions}
              rows="3"
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              placeholder="Instructions supplémentaires pour le patient..."
            ></textarea>
          </div>

          <!-- Expiration Date -->
          <div>
            <label for="prescription-expires" class="block text-sm font-medium text-gray-700 mb-2">
              Date d'expiration (optionnelle)
            </label>
            <input
              id="prescription-expires"
              type="datetime-local"
              bind:value={prescriptionForm.expires_at}
              class="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
            />
          </div>

          <!-- Submit Button -->
          <div class="pt-4">
            <button
              on:click={handleIssuePrescription}
              disabled={issuingPrescription || !prescriptionForm.patient_id}
              class="w-full px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
            >
              {issuingPrescription ? 'Création en cours...' : 'Créer la prescription'}
            </button>
          </div>
        </div>
      </div>
    {/if}
  {/if}

  <!-- View Prescriptions (shown when clicking the third tab) -->
  {#if viewingPrescriptions || prescriptions.length > 0}
    <div class="bg-white rounded-xl border border-gray-200 p-6 mt-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-lg font-semibold text-gray-900">Mes Prescriptions</h3>
        <select
          bind:value={selectedPatientId}
          on:change={() => loadPrescriptions(selectedPatientId)}
          class="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500"
        >
          <option value={undefined}>Tous les patients</option>
          {#each patients as patient}
            <option value={patient.id}>
              {patient.first_name}
              {patient.last_name}
            </option>
          {/each}
        </select>
      </div>

      {#if prescriptions.length === 0}
        <div class="text-center py-12">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-16 w-16 text-gray-400 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <p class="text-gray-600">Aucune prescription trouvée</p>
        </div>
      {:else}
        <div class="space-y-4">
          {#each prescriptions as prescription}
            <div class="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
              <div class="flex items-start justify-between mb-3">
                <div>
                  <h4 class="font-semibold text-gray-900">
                    {prescription.patient_first_name || 'N/A'}
                    {prescription.patient_last_name || ''}
                  </h4>
                  <p class="text-sm text-gray-500">N° {prescription.prescription_number}</p>
                </div>
                <span
                  class="px-3 py-1 rounded-full text-sm font-medium {getPrescriptionStatusClass(
                    prescription.status
                  )}"
                >
                  {getPrescriptionStatusLabel(prescription.status)}
                </span>
              </div>

              <div class="mb-3">
                <p class="text-sm text-gray-600 mb-2">
                  <strong>Délivrée le:</strong>
                  {formatDate(prescription.issued_at)}
                </p>
                {#if prescription.expires_at}
                  <p class="text-sm text-gray-600">
                    <strong>Expire le:</strong>
                    {formatDate(prescription.expires_at)}
                  </p>
                {/if}
              </div>

              <div class="bg-gray-50 rounded-lg p-3">
                <p class="text-sm font-semibold text-gray-900 mb-2">Médicaments:</p>
                <ul class="space-y-1">
                  {#each prescription.medications as med}
                    <li class="text-sm text-gray-700">
                      • <strong>{med.name}</strong>
                      {#if med.dosage}- {med.dosage}{/if}
                      {#if med.frequency}- {med.frequency}{/if}
                      {#if med.duration}- {med.duration}{/if}
                    </li>
                  {/each}
                </ul>
              </div>

              {#if prescription.instructions}
                <div class="mt-3 text-sm text-gray-600">
                  <strong>Instructions:</strong>
                  {prescription.instructions}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
</div>
