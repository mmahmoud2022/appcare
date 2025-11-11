<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    getMyPatients,
    getPatientMedicalRecord,
    uploadPatientDocument,
    issueElectronicPrescription,
    deletePatient,
    type PatientInfo,
    type MedicalRecord,
    type PrescriptionMedication
  } from '../../lib/api-doctor';
  
  let patients: PatientInfo[] = [];
  let loading = true;
  let error: string | null = null;
  let selectedPatient: PatientInfo | null = null;
  let showDetailsModal = false;
  let medicalRecord: MedicalRecord | null = null;
  let loadingRecord = false;
  let uploadingDocument = false;
  let documentTitle = '';
  let documentDescription = '';
  let documentType = '';
  let documentFile: File | null = null;
  let documentError: string | null = null;
  let documentSuccess: string | null = null;
  let issuingPrescription = false;
  let prescriptionError: string | null = null;
  let prescriptionSuccess: string | null = null;
  let prescriptionInstructions = '';
  let prescriptionExpiresAt = '';
  let prescriptionMedications: PrescriptionMedication[] = [
    { name: '', dosage: '', frequency: '', duration: '', notes: '' }
  ];
  let deletingPatient = false;

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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric'
    });
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const openPatientDetails = async (patient: PatientInfo) => {
    selectedPatient = patient;
    showDetailsModal = true;
    loadingRecord = true;
    resetDocumentForm();
  resetPrescriptionForm();
    
    try {
      medicalRecord = await getPatientMedicalRecord(patient.id);
    } catch (err) {
      console.error('Error loading patient medical record:', err);
    } finally {
      loadingRecord = false;
    }
  };

  const closeDetailsModal = () => {
    showDetailsModal = false;
    selectedPatient = null;
    medicalRecord = null;
    resetDocumentForm();
    resetPrescriptionForm();
  };

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'confirmed': return 'bg-blue-100 text-blue-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'cancelled': return 'bg-red-100 text-red-800';
      case 'no_show': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'pending': return 'En attente';
      case 'confirmed': return 'Confirmé';
      case 'completed': return 'Terminé';
      case 'cancelled': return 'Annulé';
      case 'no_show': return 'Absent';
      default: return status;
    }
  };

  const getPrescriptionStatusBadge = (status: string) => {
    switch (status) {
      case 'issued':
        return 'bg-emerald-100 text-emerald-800';
      case 'expired':
        return 'bg-yellow-100 text-yellow-800';
      case 'cancelled':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getPrescriptionStatusLabel = (status: string) => {
    switch (status) {
      case 'issued':
        return 'Active';
      case 'expired':
        return 'Expirée';
      case 'cancelled':
        return 'Annulée';
      default:
        return status;
    }
  };

  const resetDocumentForm = () => {
    documentTitle = '';
    documentDescription = '';
    documentType = '';
    documentFile = null;
    documentError = null;
    documentSuccess = null;
  };

  const resetPrescriptionForm = () => {
    prescriptionMedications = [{ name: '', dosage: '', frequency: '', duration: '', notes: '' }];
    prescriptionInstructions = '';
    prescriptionExpiresAt = '';
    prescriptionError = null;
    prescriptionSuccess = null;
  };

  const updateMedicationField = (index: number, field: keyof PrescriptionMedication, value: string) => {
    prescriptionError = null;
    prescriptionMedications = prescriptionMedications.map((medication, idx) =>
      idx === index ? { ...medication, [field]: value } : medication
    );
  };

  const addMedicationRow = () => {
    prescriptionError = null;
    prescriptionMedications = [
      ...prescriptionMedications,
      { name: '', dosage: '', frequency: '', duration: '', notes: '' }
    ];
  };

  const removeMedicationRow = (index: number) => {
    if (prescriptionMedications.length === 1) {
      prescriptionError = 'Au moins un médicament doit être renseigné';
      return;
    }
    prescriptionMedications = prescriptionMedications.filter((_, idx) => idx !== index);
    prescriptionError = null;
  };

  const handleDocumentFileChange = (event: Event) => {
    const input = event.target as HTMLInputElement;
    documentFile = input.files?.[0] ?? null;
  };

  const handleUploadDocument = async () => {
    if (!selectedPatient) return;
    if (!documentTitle.trim()) {
      documentError = 'Veuillez saisir un titre pour le document';
      return;
    }
    if (!documentFile) {
      documentError = 'Veuillez sélectionner un fichier à envoyer';
      return;
    }

    uploadingDocument = true;
    documentError = null;
    documentSuccess = null;
    try {
      await uploadPatientDocument({
        patient_id: selectedPatient.id,
        title: documentTitle.trim(),
        description: documentDescription.trim() || undefined,
        document_type: documentType.trim() || undefined,
        file: documentFile
      });
      documentSuccess = 'Document envoyé avec succès';
      setTimeout(() => documentSuccess = null, 3000);
      documentTitle = '';
      documentDescription = '';
      documentType = '';
      documentFile = null;
      medicalRecord = await getPatientMedicalRecord(selectedPatient.id);
    } catch (err) {
      console.error('Error uploading document:', err);
      documentError = 'Erreur lors du téléversement du document';
    } finally {
      uploadingDocument = false;
    }
  };

  const handleIssuePrescription = async () => {
    if (!selectedPatient) return;

    const sanitizedMedications = prescriptionMedications
      .map((medication) => ({
        name: medication.name.trim(),
        dosage: medication.dosage?.trim() || undefined,
        frequency: medication.frequency?.trim() || undefined,
        duration: medication.duration?.trim() || undefined,
        notes: medication.notes?.trim() || undefined
      }))
      .filter((medication) => medication.name.length > 0);

    if (sanitizedMedications.length === 0) {
      prescriptionError = 'Renseignez au moins un médicament';
      return;
    }

    issuingPrescription = true;
    prescriptionError = null;
    prescriptionSuccess = null;

    try {
      const payload = {
        patient_id: selectedPatient.id,
        medications: sanitizedMedications,
        instructions: prescriptionInstructions.trim() || undefined,
        expires_at: prescriptionExpiresAt ? new Date(prescriptionExpiresAt).toISOString() : undefined
      };

      await issueElectronicPrescription(payload);

      resetPrescriptionForm();
      prescriptionSuccess = 'Ordonnance envoyée avec succès';
      setTimeout(() => prescriptionSuccess = null, 4000);

      medicalRecord = await getPatientMedicalRecord(selectedPatient.id);
    } catch (err) {
      console.error('Error issuing prescription:', err);
      prescriptionError = "Erreur lors de l'émission de l'ordonnance";
    } finally {
      issuingPrescription = false;
    }
  };

  const handleDeletePatient = async (patient: PatientInfo) => {
    if (!confirm(`⚠️ ATTENTION : Êtes-vous sûr de vouloir supprimer le patient ${patient.first_name} ${patient.last_name} ?\n\nCette action supprimera également :\n- Tous les rendez-vous\n- Toutes les ordonnances\n- Tous les documents\n- Tout l'historique médical\n\nCette action est IRRÉVERSIBLE !`)) {
      return;
    }
    
    // Double confirmation
    if (!confirm('Confirmer la suppression définitive ?')) {
      return;
    }
    
    deletingPatient = true;
    try {
      await deletePatient(patient.id);
      closeDetailsModal();
      await loadPatients();
    } catch (err: any) {
      console.error('Error deleting patient:', err);
      alert('Erreur lors de la suppression du patient');
    } finally {
      deletingPatient = false;
    }
  };

</script>

<div class="space-y-6">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div>
      <h2 class="text-2xl font-bold text-gray-900">Mes Patients</h2>
      <p class="text-gray-600 mt-1">{patients.length} patient{patients.length > 1 ? 's' : ''} au total</p>
    </div>
  </div>

  {#if loading}
    <div class="flex items-center justify-center py-12">
      <svg class="animate-spin h-8 w-8 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
    </div>
  {:else if error}
    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
      <p class="text-red-800">{error}</p>
    </div>
  {:else if patients.length === 0}
    <div class="text-center py-12 bg-white rounded-lg border border-gray-200">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
      <p class="text-gray-600">Aucun patient pour le moment</p>
    </div>
  {:else}
    <!-- Patients Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each patients as patient}
        <button 
          type="button"
          class="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-lg transition-shadow text-left w-full"
          on:click={() => openPatientDetails(patient)}
        >
          <div class="flex items-start gap-4">
            <div class="w-14 h-14 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-7 w-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div class="flex-1 min-w-0">
              <h3 class="font-semibold text-gray-900 truncate">{patient.first_name} {patient.last_name}</h3>
              <p class="text-sm text-gray-500 truncate">{patient.email}</p>
              {#if patient.phone}
                <p class="text-sm text-gray-500 mt-1">{patient.phone}</p>
              {/if}
            </div>
          </div>
          
          <div class="mt-4 pt-4 border-t border-gray-200 space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-600">Rendez-vous:</span>
              <span class="font-semibold text-gray-900">{patient.total_appointments}</span>
            </div>
            {#if patient.last_appointment_date}
              <div class="flex items-center justify-between text-sm">
                <span class="text-gray-600">Dernier RDV:</span>
                <span class="font-medium text-gray-700">{formatDate(patient.last_appointment_date)}</span>
              </div>
            {/if}
          </div>
          
          <span class="mt-4 w-full block px-4 py-2 bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 transition-colors text-sm font-medium text-center">
            Voir l'historique
          </span>
        </button>
      {/each}
    </div>
  {/if}
</div>

<!-- Patient Details Modal -->
{#if showDetailsModal && selectedPatient}
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
    <div class="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
      <div class="p-6 border-b border-gray-200">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-full flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <div>
              <h3 class="text-2xl font-bold text-gray-900">{selectedPatient.first_name} {selectedPatient.last_name}</h3>
              <p class="text-gray-600">{selectedPatient.email}</p>
              {#if selectedPatient.phone}
                <p class="text-gray-600">{selectedPatient.phone}</p>
              {/if}
            </div>
          </div>
          <button on:click={closeDetailsModal} class="text-gray-400 hover:text-gray-600" title="Fermer">
            <svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            <span class="sr-only">Fermer</span>
          </button>
        </div>
      </div>
      
      <!-- Stats -->
      <div class="p-6 bg-gray-50 border-b border-gray-200">
        <div class="grid grid-cols-2 gap-4">
          <div class="text-center">
            <p class="text-3xl font-bold text-gray-900">{selectedPatient.total_appointments}</p>
            <p class="text-sm text-gray-600 mt-1">Total rendez-vous</p>
          </div>
          <div class="text-center">
            <p class="text-3xl font-bold text-emerald-600">
              {medicalRecord?.total_consultations || 0}
            </p>
            <p class="text-sm text-gray-600 mt-1">Consultations terminées</p>
          </div>
        </div>
      </div>
      
      <!-- Appointments History -->
      <div class="p-6">
        <h4 class="text-lg font-semibold text-gray-900 mb-4">Historique des consultations</h4>
        
        {#if loadingRecord}
          <div class="flex items-center justify-center py-8">
            <svg class="animate-spin h-6 w-6 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        {:else if !medicalRecord || medicalRecord.appointments.length === 0}
          <p class="text-gray-500 text-center py-8">Aucun rendez-vous trouvé</p>
        {:else}
          <div class="space-y-3 max-h-96 overflow-y-auto">
            {#each medicalRecord.appointments as appointment}
              <div class="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <div class="flex items-start justify-between mb-2">
                  <div class="flex-1">
                    <div class="flex items-center gap-2 mb-1">
                      <p class="font-medium text-gray-900">
                        {formatDate(appointment.appointment_date)}
                      </p>
                      <span class="px-2 py-1 rounded-full text-xs font-medium {getStatusBadgeClass(appointment.status)}">
                        {getStatusLabel(appointment.status)}
                      </span>
                    </div>
                    {#if appointment.reason}
                      <p class="text-sm text-gray-600">Motif: {appointment.reason}</p>
                    {/if}
                  </div>
                </div>
                {#if appointment.doctor_notes}
                  <div class="bg-gray-100 rounded p-3 mt-2">
                    <p class="text-sm font-medium text-gray-900 mb-1">Notes:</p>
                    <p class="text-sm text-gray-700">{appointment.doctor_notes}</p>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Prescriptions Section -->
      <div class="px-6 pb-6 space-y-6">
        <div>
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Ordonnances électroniques</h4>
          {#if medicalRecord && medicalRecord.prescriptions.length > 0}
            <div class="space-y-3">
              {#each medicalRecord.prescriptions as prescription}
                <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div class="flex items-start justify-between gap-4">
                    <div>
                      <h5 class="font-semibold text-gray-900">Ordonnance {prescription.prescription_number}</h5>
                      <p class="text-sm text-gray-600 mt-1">Émise le {formatDateTime(prescription.issued_at)}</p>
                      {#if prescription.expires_at}
                        <p class="text-xs text-gray-500 mt-1">Expiration le {formatDate(prescription.expires_at)}</p>
                      {/if}
                    </div>
                    <span class={`px-3 py-1 rounded-full text-xs font-medium ${getPrescriptionStatusBadge(prescription.status)}`}>
                      {getPrescriptionStatusLabel(prescription.status)}
                    </span>
                  </div>
                  <ul class="mt-3 space-y-2">
                    {#each prescription.medications as medication}
                      <li class="text-sm text-gray-600">
                        <span class="font-medium text-gray-900">{medication.name}</span>
                        {#if medication.dosage}
                          <span> — {medication.dosage}</span>
                        {/if}
                        {#if medication.frequency}
                          <span class="text-gray-500"> · {medication.frequency}</span>
                        {/if}
                        {#if medication.duration}
                          <span class="text-gray-500"> · Durée : {medication.duration}</span>
                        {/if}
                        {#if medication.notes}
                          <div class="text-xs text-gray-500 mt-1">{medication.notes}</div>
                        {/if}
                      </li>
                    {/each}
                  </ul>
                  {#if prescription.instructions}
                    <div class="bg-white border border-emerald-100 rounded-lg p-3 mt-3">
                      <p class="text-sm text-gray-700 whitespace-pre-line">{prescription.instructions}</p>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-sm text-gray-500">Aucune ordonnance n'a encore été émise pour ce patient.</p>
          {/if}
        </div>

        <div class="border border-emerald-200 bg-emerald-50 rounded-lg p-6">
          <h5 class="font-semibold text-emerald-900 mb-4">Émettre une nouvelle ordonnance</h5>

          <div class="space-y-4">
            {#each prescriptionMedications as medication, index}
              <div class="border border-emerald-200 bg-white rounded-lg p-4 space-y-3">
                <div class="flex items-center justify-between">
                  <h6 class="text-sm font-semibold text-emerald-900">Médicament {index + 1}</h6>
                  {#if prescriptionMedications.length > 1}
                    <button
                      type="button"
                      class="text-xs text-red-600 hover:text-red-700"
                      on:click={() => removeMedicationRow(index)}
                    >
                      Retirer
                    </button>
                  {/if}
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label for={`medication-name-${index}`} class="block text-sm font-medium text-emerald-900 mb-1">Nom du médicament *</label>
                    <input
                      id={`medication-name-${index}`}
                      type="text"
                      class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      placeholder="Paracétamol, Ibuprofène..."
                      value={medication.name}
                      on:input={(event) => updateMedicationField(index, 'name', (event.target as HTMLInputElement).value)}
                      disabled={issuingPrescription}
                    />
                  </div>
                  <div>
                    <label for={`medication-dosage-${index}`} class="block text-sm font-medium text-emerald-900 mb-1">Dosage</label>
                    <input
                      id={`medication-dosage-${index}`}
                      type="text"
                      class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      placeholder="500 mg"
                      value={medication.dosage}
                      on:input={(event) => updateMedicationField(index, 'dosage', (event.target as HTMLInputElement).value)}
                      disabled={issuingPrescription}
                    />
                  </div>
                  <div>
                    <label for={`medication-frequency-${index}`} class="block text-sm font-medium text-emerald-900 mb-1">Fréquence</label>
                    <input
                      id={`medication-frequency-${index}`}
                      type="text"
                      class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      placeholder="3 fois par jour"
                      value={medication.frequency}
                      on:input={(event) => updateMedicationField(index, 'frequency', (event.target as HTMLInputElement).value)}
                      disabled={issuingPrescription}
                    />
                  </div>
                  <div>
                    <label for={`medication-duration-${index}`} class="block text-sm font-medium text-emerald-900 mb-1">Durée</label>
                    <input
                      id={`medication-duration-${index}`}
                      type="text"
                      class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                      placeholder="5 jours"
                      value={medication.duration}
                      on:input={(event) => updateMedicationField(index, 'duration', (event.target as HTMLInputElement).value)}
                      disabled={issuingPrescription}
                    />
                  </div>
                </div>
                <div>
                  <label for={`medication-notes-${index}`} class="block text-sm font-medium text-emerald-900 mb-1">Notes</label>
                  <textarea
                    id={`medication-notes-${index}`}
                    rows="2"
                    class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                    placeholder="Conseils supplémentaires"
                    value={medication.notes}
                    on:input={(event) => updateMedicationField(index, 'notes', (event.target as HTMLTextAreaElement).value)}
                    disabled={issuingPrescription}
                  ></textarea>
                </div>
              </div>
            {/each}
          </div>

          <div class="mt-4">
            <button
              type="button"
              class="text-sm font-medium text-emerald-700 hover:text-emerald-900"
              on:click={addMedicationRow}
              disabled={issuingPrescription}
            >
              + Ajouter un médicament
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-6">
            <div>
              <label for="prescription-expires-at" class="block text-sm font-medium text-emerald-900 mb-1">Date d'expiration</label>
              <input
                id="prescription-expires-at"
                type="date"
                class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                bind:value={prescriptionExpiresAt}
                disabled={issuingPrescription}
              />
            </div>
            <div>
              <label for="prescription-instructions" class="block text-sm font-medium text-emerald-900 mb-1">Instructions générales</label>
              <textarea
                id="prescription-instructions"
                rows="3"
                class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                bind:value={prescriptionInstructions}
                placeholder="Conseils de prise, recommandations supplémentaires"
                disabled={issuingPrescription}
              ></textarea>
            </div>
          </div>

          {#if prescriptionError}
            <div class="mt-4 bg-red-100 border border-red-200 text-red-700 px-4 py-2 rounded-lg">
              {prescriptionError}
            </div>
          {/if}

          {#if prescriptionSuccess}
            <div class="mt-4 bg-emerald-100 border border-emerald-200 text-emerald-800 px-4 py-2 rounded-lg">
              {prescriptionSuccess}
            </div>
          {/if}

          <div class="mt-6 flex justify-end">
            <button
              class="px-5 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
              on:click={handleIssuePrescription}
              disabled={issuingPrescription}
            >
              {issuingPrescription ? 'Envoi de l\'ordonnance...' : 'Émettre l\'ordonnance'}
            </button>
          </div>
        </div>
      </div>

      <!-- Documents Section -->
      <div class="px-6 pb-6 space-y-6">
        <div>
          <h4 class="text-lg font-semibold text-gray-900 mb-4">Documents partagés</h4>
          {#if medicalRecord && medicalRecord.documents.length > 0}
            <div class="space-y-3">
              {#each medicalRecord.documents as document}
                <div class="border border-gray-200 rounded-lg p-4 bg-gray-50">
                  <div class="flex items-start justify-between">
                    <div>
                      <h5 class="font-semibold text-gray-900">{document.title}</h5>
                      <p class="text-sm text-gray-600 mt-1">{document.document_type || 'Document médical'}</p>
                    </div>
                    <span class="text-xs text-gray-500">{new Date(document.created_at).toLocaleString('fr-FR')}</span>
                  </div>
                  <p class="text-sm text-gray-500 mt-2">Fichier : {document.file_name}</p>
                  {#if document.description}
                    <p class="text-sm text-gray-600 mt-2">{document.description}</p>
                  {/if}
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-sm text-gray-500">Aucun document partagé pour l'instant.</p>
          {/if}
        </div>

        <div class="border border-emerald-200 bg-emerald-50 rounded-lg p-6">
          <h5 class="font-semibold text-emerald-900 mb-4">Partager un document avec le patient</h5>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label for="document-title" class="block text-sm font-medium text-emerald-900 mb-1">Titre *</label>
              <input
                id="document-title"
                type="text"
                bind:value={documentTitle}
                class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="Ordonnance, Compte-rendu..."
                disabled={uploadingDocument}
              />
            </div>
            <div>
              <label for="document-type" class="block text-sm font-medium text-emerald-900 mb-1">Type</label>
              <input
                id="document-type"
                type="text"
                bind:value={documentType}
                class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
                placeholder="ordonnance, analyse, certificat..."
                disabled={uploadingDocument}
              />
            </div>
          </div>
          <div class="mt-4">
            <label for="document-description" class="block text-sm font-medium text-emerald-900 mb-1">Description</label>
            <textarea
              id="document-description"
              bind:value={documentDescription}
              class="w-full px-4 py-2 border border-emerald-200 rounded-lg focus:ring-2 focus:ring-emerald-500"
              rows="3"
              placeholder="Informations complémentaires pour le patient"
              disabled={uploadingDocument}
            ></textarea>
          </div>
          <div class="mt-4">
            <label for="document-file" class="block text-sm font-medium text-emerald-900 mb-1">Fichier *</label>
            <input
              id="document-file"
              type="file"
              on:change={handleDocumentFileChange}
              class="block w-full text-sm text-emerald-900 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-emerald-100 file:text-emerald-700 hover:file:bg-emerald-200"
              disabled={uploadingDocument}
            />
            <p class="mt-1 text-xs text-emerald-700">Formats acceptés : PDF, images, documents (taille maximale selon votre politique interne)</p>
          </div>

          {#if documentError}
            <div class="mt-4 bg-red-100 border border-red-200 text-red-700 px-4 py-2 rounded-lg">
              {documentError}
            </div>
          {/if}

          {#if documentSuccess}
            <div class="mt-4 bg-emerald-100 border border-emerald-200 text-emerald-800 px-4 py-2 rounded-lg">
              {documentSuccess}
            </div>
          {/if}

          <div class="mt-4 flex justify-end">
            <button
              on:click={handleUploadDocument}
              class="px-5 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors disabled:opacity-50"
              disabled={uploadingDocument}
            >
              {uploadingDocument ? 'Envoi en cours...' : 'Envoyer le document'}
            </button>
          </div>
        </div>
      </div>
      
      <div class="p-6 border-t border-gray-200">
        <div class="flex gap-3">
          <button
            on:click={closeDetailsModal}
            class="flex-1 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
          >
            Fermer
          </button>
          <button
            on:click={() => selectedPatient && handleDeletePatient(selectedPatient)}
            class="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 flex items-center gap-2"
            disabled={deletingPatient}
            title="Supprimer définitivement ce patient"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
            </svg>
            {deletingPatient ? 'Suppression...' : 'Supprimer'}
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}
