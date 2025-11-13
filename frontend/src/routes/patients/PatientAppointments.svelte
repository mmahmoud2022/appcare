<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { fade, fly, scale, blur } from 'svelte/transition';
  import { flip } from 'svelte/animate';
  import { cubicOut, elasticOut } from 'svelte/easing';
  
  // API imports
  import {
    getPatientAppointments,
    createPatientAppointment,
    updatePatientAppointment,
    cancelPatientAppointment,
    createDoctorReview,
    type PatientAppointment,
    type DoctorSearchResult,
    type DoctorReviewCreate
  } from '../../lib/api-patient';
  import {
    getDoctorSchedule,
    type ConsultationType,
    type DoctorScheduleEntry
  } from '../../lib/api-doctor';

  // Utils imports
  import { toInputDateTime, formatTime, formatFullDate, formatShortDate, WEEKDAY_LABELS } from '../../lib/utils/dates';
  import { 
    generateSlotSuggestions, 
    groupSlotsByDay,
    isSlotSelected,
    formatSlotLabel,
    formatSlotChipLabel,
    type SlotSuggestion,
    type SlotSuggestionGroup
  } from '../../lib/utils/slots';
  import { formatSpecialty, CONSULTATION_LABELS } from '../../lib/utils/formatting';
  
  // Stores
  import { 
    appointments,
    upcomingAppointments,
    pastAppointments,
    loading,
    error
  } from '../../stores/appointments';
  
  // Toast notifications
  import { toast } from '../../components/ui/Toast.svelte';
  
  // Components
  import BookingModal from '../../components/booking/BookingModal.svelte';
  import TeleconsultationButton from '../../components/TeleconsultationButton.svelte';

  const dispatch = createEventDispatcher();
  
  // Animation states
  let hoveredAppointment: number | null = null;
  let celebrateBooking = false;

  let showBookingModal = false;
  let bookingStep = 1; // 1: Slots, 2: Details
  let bookingSubmitting = false;
  let selectedDoctor: DoctorSearchResult | null = null;
  let doctorDetail: DoctorSearchResult | null = null;
  let doctorSchedule: DoctorScheduleEntry[] = [];
  let availabilityLoading = false;
  let availabilityError: string | null = null;

  const defaultBookingPayload = () => ({
    doctor_id: 0,
    appointment_date: '',
    consultation_type: 'in_person' as ConsultationType,
    reason: '',
    patient_notes: '',
    schedule_entry_id: undefined as number | undefined
  });

  let bookingPayload = defaultBookingPayload();

  let showRescheduleModal = false;
  let rescheduleSubmitting = false;
  let rescheduleAppointment: PatientAppointment | null = null;
  let rescheduleDate = '';
  let rescheduleNotes = '';
  let showConfirmCancel = false;
  let pendingCancellation: PatientAppointment | null = null;
  let showConfirmReschedule = false;

  // Review modal
  let showReviewModal = false;
  let reviewAppointment: PatientAppointment | null = null;
  let reviewRating = 0;
  let reviewComment = '';
  let reviewSubmitting = false;

  onMount(async () => {
    await loadAppointments();
  });

  const loadAppointments = async () => {
    loading.set(true);
    error.set(null);
    try {
      const response = await getPatientAppointments(1, 100);
      appointments.set(response.items);
    } catch (err: any) {
      console.error('Erreur lors du chargement des rendez-vous:', err);
      error.set("Impossible de charger vos rendez-vous");
    } finally {
      loading.set(false);
    }
  };

  const openBookingModal = () => {
    dispatch('openDoctorSearch');
  };

  const resetBookingForm = () => {
    bookingPayload = defaultBookingPayload();
    selectedDoctor = null;
    doctorDetail = null;
    doctorSchedule = [];
    availabilityError = null;
    availabilityLoading = false;
    showAllSlots = false;
    bookingStep = 1;
  };

  const loadDoctorSchedule = async (doctorId: number) => {
    availabilityLoading = true;
    availabilityError = null;
    showAllSlots = false;
    try {
      doctorSchedule = await getDoctorSchedule(doctorId);
    } catch (err) {
      console.error('Erreur lors du chargement des disponibilités du praticien:', err);
      availabilityError = "Impossible de récupérer les créneaux du praticien";
      doctorSchedule = [];
    } finally {
      availabilityLoading = false;
    }
  };

  // Variables pour les créneaux
  let slotSuggestions: SlotSuggestion[] = [];
  let slotSuggestionGroups: SlotSuggestionGroup[] = [];
  let visibleSlotGroups: SlotSuggestionGroup[] = [];
  let canShowMoreSlots = false;
  let showAllSlots = false;

  // Reactive statements utilisant les utilitaires importés
  $: slotSuggestions = generateSlotSuggestions(doctorSchedule, bookingPayload.consultation_type, 20, 4);
  $: slotSuggestionGroups = groupSlotsByDay(slotSuggestions);
  $: visibleSlotGroups = showAllSlots ? slotSuggestionGroups : slotSuggestionGroups.slice(0, 3);
  $: canShowMoreSlots = slotSuggestionGroups.length > 3;

  $: if (!showBookingModal) {
    showAllSlots = false;
  }

  const selectSlot = (slot: SlotSuggestion) => {
    const resolvedType = slot.entry.consultation_type === 'both'
      ? bookingPayload.consultation_type
      : slot.entry.consultation_type;
    bookingPayload = {
      ...bookingPayload,
      appointment_date: toInputDateTime(slot.start),
      schedule_entry_id: slot.entry.id,
      consultation_type: resolvedType ?? bookingPayload.consultation_type
    };
  };

  const closeBookingModal = () => {
    showBookingModal = false;
    resetBookingForm();
  };

  const consultationTypeOptions = (doctor: DoctorSearchResult | null): { value: ConsultationType; label: string }[] => {
    if (!doctor) {
      return [
        { value: 'in_person' as ConsultationType, label: 'En cabinet' },
        { value: 'teleconsultation' as ConsultationType, label: 'Téléconsultation' },
        { value: 'both' as ConsultationType, label: 'Au choix' }
      ];
    }
    if (doctor.consultation_types === 'both') {
      return [
        { value: 'in_person' as ConsultationType, label: 'En cabinet' },
        { value: 'teleconsultation' as ConsultationType, label: 'Téléconsultation' }
      ];
    }
    const labels: Record<ConsultationType, string> = {
      in_person: 'En cabinet',
      teleconsultation: 'Téléconsultation',
      both: 'Au choix'
    };
    return [{ value: doctor.consultation_types, label: labels[doctor.consultation_types] }];
  };

  export const openBookingForDoctor = async (doctor: DoctorSearchResult) => {
    resetBookingForm();
    selectedDoctor = doctor;
    doctorDetail = doctor;
    showAllSlots = false;
    bookingPayload = {
      ...bookingPayload,
      doctor_id: doctor.doctor_id,
      consultation_type: doctor.consultation_types === 'both' ? 'in_person' : doctor.consultation_types,
      appointment_date: '',
      reason: '',
      patient_notes: '',
      schedule_entry_id: undefined
    };
    showBookingModal = true;
  await loadDoctorSchedule(doctor.doctor_id);
  };

  const formatAppointmentLabel = (appointment: PatientAppointment) => {
    const date = new Date(appointment.appointment_date).toLocaleString('fr-FR', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
    const doctorName = [appointment.doctor_first_name, appointment.doctor_last_name].filter(Boolean).join(' ') || 'Médecin';
    return `${date} · ${doctorName}`;
  };

  const submitBooking = async () => {
    if (!bookingPayload.doctor_id || !bookingPayload.appointment_date) {
      toast.warning('Merci de sélectionner un praticien et une date.');
      return;
    }
    bookingSubmitting = true;
    try {
      await createPatientAppointment({
        doctor_id: bookingPayload.doctor_id,
        appointment_date: new Date(bookingPayload.appointment_date).toISOString(),
        consultation_type: bookingPayload.consultation_type,
        reason: bookingPayload.reason || undefined,
        patient_notes: bookingPayload.patient_notes || undefined,
        schedule_entry_id: bookingPayload.schedule_entry_id
      });
      
      // Celebration animation!
      celebrateBooking = true;
      setTimeout(() => celebrateBooking = false, 3000);
      
      toast.success('Rendez-vous confirmé ! 🎉');
      closeBookingModal();
      await loadAppointments();
      dispatch('refresh');
    } catch (err: any) {
      console.error('Erreur lors de la création du rendez-vous:', err);
      toast.error(err?.response?.data?.detail ?? "Impossible de créer ce rendez-vous");
    } finally {
      bookingSubmitting = false;
    }
  };

  const openRescheduleModal = (appointment: PatientAppointment) => {
    rescheduleAppointment = appointment;
    rescheduleDate = appointment.appointment_date.slice(0, 16);
    rescheduleNotes = appointment.patient_notes ?? '';
    showRescheduleModal = true;
    showConfirmReschedule = false;
  };

  const submitReschedule = async () => {
    if (!rescheduleAppointment || !rescheduleDate) return;
    rescheduleSubmitting = true;
    try {
      await updatePatientAppointment(rescheduleAppointment.id, {
        appointment_date: new Date(rescheduleDate).toISOString(),
        patient_notes: rescheduleNotes || undefined
      });
      toast.success('Rendez-vous replanifié avec succès');
      showRescheduleModal = false;
      rescheduleAppointment = null;
      await loadAppointments();
      dispatch('refresh');
    } catch (err: any) {
      console.error('Erreur lors du report du rendez-vous:', err);
      toast.error(err?.response?.data?.detail ?? "Impossible de replanifier ce rendez-vous");
    } finally {
      rescheduleSubmitting = false;
    }
  };

  const promptCancelAppointment = (appointment: PatientAppointment) => {
    pendingCancellation = appointment;
    showConfirmCancel = true;
  };

  const confirmCancelAppointment = async () => {
    if (!pendingCancellation) return;
    try {
      await cancelPatientAppointment(pendingCancellation.id);
      toast.success('Rendez-vous annulé');
      showConfirmCancel = false;
      pendingCancellation = null;
      await loadAppointments();
      dispatch('refresh');
    } catch (err: any) {
      console.error("Erreur lors de l'annulation:", err);
      toast.error(err?.response?.data?.detail ?? "Impossible d'annuler ce rendez-vous");
    }
  };

  export const refreshAppointments = async () => {
    await loadAppointments();
  };

  const openReviewModal = (appointment: PatientAppointment) => {
    reviewAppointment = appointment;
    reviewRating = 0;
    reviewComment = '';
    showReviewModal = true;
  };

  const closeReviewModal = () => {
    showReviewModal = false;
    reviewAppointment = null;
    reviewRating = 0;
    reviewComment = '';
  };

  const handleReviewModalKeydown = (e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      closeReviewModal();
    }
  };

  const submitReview = async () => {
    if (!reviewAppointment || reviewRating === 0) return;
    
    reviewSubmitting = true;
    try {
      await createDoctorReview({
        doctor_id: reviewAppointment.doctor_id,
        appointment_id: reviewAppointment.id,
        rating: reviewRating,
        comment: reviewComment || undefined,
        is_public: true
      });
      
      toast.success('Votre avis a été enregistré avec succès');
      closeReviewModal();
      await loadAppointments();
    } catch (err: any) {
      console.error('Erreur lors de la soumission de l\'avis:', err);
      toast.error(err?.response?.data?.detail ?? "Impossible d'enregistrer votre avis");
    } finally {
      reviewSubmitting = false;
    }
  };
</script>

<div class="space-y-8 relative">
  <!-- Success Celebration Overlay with Confetti -->
  {#if celebrateBooking}
    <div 
      class="fixed inset-0 z-[100] pointer-events-none"
      transition:fade={{ duration: 300 }}
    >
      <!-- Confetti particles -->
      {#each Array.from({ length: 50 }) as _, i}
        <div
          class="absolute w-3 h-3 rounded-full"
          style="
            left: {Math.random() * 100}%;
            top: -20px;
            background: {['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E2'][i % 8]};
            animation: confettiFloat {2000 + Math.random() * 2000}ms linear forwards;
            animation-delay: {Math.random() * 500}ms;
          "
        ></div>
      {/each}
      
      <!-- Success message -->
      <div class="flex items-center justify-center h-full">
        <div 
          class="relative"
          in:scale={{ duration: 600, easing: elasticOut }}
          out:scale={{ duration: 300 }}
        >
          <div class="w-40 h-40 bg-gradient-to-br from-green-400 via-emerald-500 to-teal-600 rounded-full flex items-center justify-center shadow-2xl">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-20 w-20 text-white animate-bounce" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <!-- Ping effect -->
          <div class="absolute inset-0 animate-ping">
            <div class="w-full h-full bg-gradient-to-br from-green-400 to-teal-600 rounded-full opacity-75"></div>
          </div>
          <!-- Glow effect -->
          <div class="absolute -inset-4 bg-gradient-to-r from-green-400 via-emerald-500 to-teal-600 rounded-full blur-xl opacity-60 animate-pulse"></div>
        </div>
      </div>
      
      <!-- Success text -->
      <div class="absolute bottom-1/3 left-1/2 transform -translate-x-1/2 text-center">
        <p class="text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-green-600 via-emerald-600 to-teal-600 animate-pulse drop-shadow-2xl">
          Rendez-vous confirmé! 🎉
        </p>
        <p class="text-xl font-bold text-gray-700 mt-2 animate-pulse">
          Vous allez recevoir une confirmation par email
        </p>
      </div>
    </div>
  {/if}

  <!-- Ultra Modern Header -->
  <div class="relative overflow-hidden bg-gradient-to-br from-violet-600 via-purple-600 to-fuchsia-600 rounded-[2rem] shadow-2xl p-1">
    <div class="absolute inset-0 bg-grid-white/10 [mask-image:linear-gradient(0deg,white,rgba(255,255,255,0.6))]"></div>
    <div class="absolute top-0 left-0 w-72 h-72 bg-white/20 rounded-full blur-3xl -ml-36 -mt-36 animate-blob"></div>
    <div class="absolute bottom-0 right-0 w-72 h-72 bg-pink-300/20 rounded-full blur-3xl -mr-36 -mb-36 animate-blob animation-delay-2000"></div>
    <div class="absolute top-1/2 left-1/2 w-72 h-72 bg-purple-300/20 rounded-full blur-3xl -ml-36 -mt-36 animate-blob animation-delay-4000"></div>
    
    <div class="relative bg-white/10 backdrop-blur-2xl rounded-[1.75rem] p-8 border border-white/20">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-6">
          <div class="relative">
            <div class="w-20 h-20 bg-gradient-to-br from-white/40 to-white/20 rounded-3xl flex items-center justify-center backdrop-blur-sm border-2 border-white/30 shadow-2xl transform hover:rotate-12 transition-transform duration-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white drop-shadow-lg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="absolute -bottom-2 -right-2 w-8 h-8 bg-gradient-to-br from-green-400 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg animate-pulse">
              <span class="text-white text-xs font-black">{$upcomingAppointments.length}</span>
            </div>
          </div>
          <div>
            <h2 class="text-4xl font-black text-white drop-shadow-lg mb-2 tracking-tight">Mes Rendez-vous</h2>
            <p class="text-lg text-white/90 font-medium">Gérez vos consultations en toute simplicité</p>
          </div>
        </div>
        <button
          on:click={openBookingModal}
          class="group relative px-8 py-4 bg-white text-purple-600 rounded-2xl hover:bg-white/90 transition-all shadow-2xl hover:shadow-3xl font-bold text-lg overflow-hidden transform hover:scale-105 active:scale-95"
        >
          <div class="absolute inset-0 bg-gradient-to-r from-violet-600/20 to-fuchsia-600/20 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div class="relative flex items-center gap-3">
            <div class="w-10 h-10 bg-gradient-to-br from-violet-600 to-fuchsia-600 rounded-xl flex items-center justify-center shadow-lg group-hover:rotate-90 transition-transform duration-500">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </div>
            <span>Nouveau RDV</span>
          </div>
        </button>
      </div>
    </div>
  </div>

  {#if $loading}
    <div class="flex items-center justify-center py-24" transition:fade={{ duration: 300 }}>
      <div class="relative">
        <div class="w-32 h-32 border-8 border-violet-200 border-t-violet-600 rounded-full animate-spin"></div>
        <div class="absolute inset-0 w-32 h-32 border-8 border-fuchsia-200 border-t-fuchsia-600 rounded-full animate-spin animation-delay-150" style="animation-direction: reverse;"></div>
        <div class="absolute inset-0 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 text-violet-600 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
      </div>
    </div>
  {:else if $error}
    <div 
      class="bg-gradient-to-br from-red-50 to-pink-50 border-l-4 border-red-500 rounded-2xl p-6 shadow-xl"
      transition:fly={{ x: -20, duration: 400 }}
    >
      <div class="flex items-start gap-4">
        <div class="w-12 h-12 bg-red-500 rounded-full flex items-center justify-center flex-shrink-0 animate-pulse">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div>
          <h3 class="font-bold text-red-900 text-lg">Oups! Une erreur est survenue</h3>
          <p class="text-red-700 mt-1">{$error}</p>
        </div>
      </div>
    </div>
  {:else}
    <div class="space-y-10">
      <!-- Upcoming Appointments with 3D cards -->
      <section>
        <div class="flex items-center gap-4 mb-6">
          <div class="relative">
            <div class="w-16 h-16 bg-gradient-to-br from-green-400 to-emerald-600 rounded-2xl flex items-center justify-center shadow-xl transform -rotate-6">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <div class="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center shadow-lg animate-bounce">
              <span class="text-white text-xs font-black">{$upcomingAppointments.length}</span>
            </div>
          </div>
          <div>
            <h3 class="text-3xl font-black text-gray-900">À venir</h3>
            <p class="text-gray-600">Vos prochaines consultations</p>
          </div>
        </div>
        
        {#if $upcomingAppointments.length}
          <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {#each $upcomingAppointments as appointment, i (appointment.id)}
              <div
                class="group relative perspective-1000"
                role="article"
                animate:flip={{ duration: 400 }}
                transition:fly={{ y: 20, duration: 400, delay: i * 100 }}
                on:mouseenter={() => hoveredAppointment = appointment.id}
                on:mouseleave={() => hoveredAppointment = null}
              >
                <!-- 3D Card Effect -->
                <div class={`relative transform transition-all duration-500 preserve-3d ${hoveredAppointment === appointment.id ? 'rotate-y-5 scale-105' : ''}`}>
                  <!-- Glow effect -->
                  <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl blur opacity-25 group-hover:opacity-75 transition-opacity duration-500"></div>
                  
                  <!-- Main Card -->
                  <div class="relative bg-white rounded-3xl p-8 shadow-2xl border-2 border-gray-100 overflow-hidden">
                    <!-- Animated background pattern -->
                    <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 group-hover:scale-150 transition-transform duration-1000 pointer-events-none"></div>
                    
                    <!-- Status badge with animation -->
                    <div class="absolute top-6 right-6 z-20">
                      <div class={`relative px-4 py-2 rounded-full font-bold text-sm shadow-lg transform transition-transform duration-300 ${
                        appointment.status === 'confirmed' 
                          ? 'bg-gradient-to-r from-green-400 to-emerald-600 text-white group-hover:scale-110' 
                          : 'bg-gradient-to-r from-blue-400 to-indigo-600 text-white group-hover:scale-110'
                      }`}>
                        <div class="absolute inset-0 rounded-full bg-white/20 animate-ping"></div>
                        <span class="relative">
                          {appointment.status === 'confirmed' ? '✓ Confirmé' : '⏱ En attente'}
                        </span>
                      </div>
                    </div>
                    
                    <div class="relative z-20">
                      <!-- Doctor info with avatar -->
                      <div class="flex items-start gap-4 mb-6">
                        <div class="w-16 h-16 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center text-white text-xl font-black shadow-xl transform group-hover:rotate-12 transition-transform duration-500">
                          {appointment.doctor_first_name?.[0]}{appointment.doctor_last_name?.[0]}
                        </div>
                        <div class="flex-1">
                          <h4 class="text-xl font-black text-gray-900 group-hover:text-violet-600 transition-colors">
                            Dr. {appointment.doctor_first_name} {appointment.doctor_last_name}
                          </h4>
                          <div class="flex items-center gap-2 mt-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span class="text-lg font-bold text-gray-900">
                              {new Date(appointment.appointment_date).toLocaleDateString('fr-FR', { 
                                weekday: 'long', 
                                day: 'numeric', 
                                month: 'long',
                                year: 'numeric'
                              })}
                            </span>
                          </div>
                          <div class="flex items-center gap-2 mt-1">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-fuchsia-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            <span class="text-2xl font-black bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">
                              {new Date(appointment.appointment_date).toLocaleTimeString('fr-FR', { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </span>
                          </div>
                        </div>
                      </div>

                      <!-- Consultation type badge -->
                      <div class="mb-6">
                        <div class="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl border-2 border-indigo-200">
                          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                          </svg>
                          <span class="font-bold text-indigo-700">
                            {CONSULTATION_LABELS[appointment.consultation_type]}
                          </span>
                        </div>
                      </div>

                      {#if appointment.reason}
                        <div class="mb-6 p-4 bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl border-2 border-amber-200">
                          <div class="flex items-start gap-3">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                            </svg>
                            <div>
                              <p class="text-xs font-bold text-amber-700 uppercase tracking-wide">Motif</p>
                              <p class="text-sm text-amber-900 font-semibold mt-1">{appointment.reason}</p>
                            </div>
                          </div>
                        </div>
                      {/if}

                      <!-- Teleconsultation button (if applicable) -->
                      {#if appointment.meet_link}
                        <div class="mb-6">
                          <TeleconsultationButton 
                            meetLink={appointment.meet_link}
                            appointmentDate={appointment.appointment_date}
                            appointmentStatus={appointment.status}
                            size="large"
                          />
                        </div>
                      {/if}

                      <!-- Action buttons with hover effects -->
                      <div class="flex gap-3">
                        <button
                          on:click={() => openRescheduleModal(appointment)}
                          class="group/btn flex-1 relative overflow-hidden px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all transform hover:scale-105 active:scale-95 z-10"
                        >
                          <div class="absolute inset-0 bg-gradient-to-r from-blue-600 to-indigo-700 opacity-0 group-hover/btn:opacity-100 transition-opacity pointer-events-none"></div>
                          <span class="relative flex items-center justify-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Replanifier
                          </span>
                        </button>
                        <button
                          on:click={() => promptCancelAppointment(appointment)}
                          class="group/btn flex-1 relative overflow-hidden px-6 py-4 bg-gradient-to-r from-red-500 to-pink-600 text-white rounded-2xl font-bold shadow-lg hover:shadow-2xl transition-all transform hover:scale-105 active:scale-95 z-10"
                        >
                          <div class="absolute inset-0 bg-gradient-to-r from-red-600 to-pink-700 opacity-0 group-hover/btn:opacity-100 transition-opacity pointer-events-none"></div>
                          <span class="relative flex items-center justify-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                            </svg>
                            Annuler
                          </span>
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <div 
            class="relative overflow-hidden bg-gradient-to-br from-gray-50 via-blue-50 to-purple-50 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
            transition:scale={{ duration: 400, easing: elasticOut }}
          >
            <div class="absolute top-0 left-0 w-full h-full opacity-30">
              <div class="absolute top-10 left-10 w-20 h-20 bg-blue-400 rounded-full blur-xl animate-blob"></div>
              <div class="absolute top-20 right-10 w-32 h-32 bg-purple-400 rounded-full blur-xl animate-blob animation-delay-2000"></div>
              <div class="absolute bottom-10 left-1/2 w-24 h-24 bg-pink-400 rounded-full blur-xl animate-blob animation-delay-4000"></div>
            </div>
            <div class="relative z-10">
              <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-400 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl animate-pulse">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <h3 class="text-3xl font-black text-gray-900 mb-3">Aucun rendez-vous prévu</h3>
              <p class="text-lg text-gray-600 mb-6">Prenez soin de votre santé, réservez une consultation</p>
              <button
                on:click={openBookingModal}
                class="inline-flex items-center gap-3 px-8 py-4 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-2xl hover:from-violet-700 hover:to-fuchsia-700 transition-all font-bold text-lg shadow-xl hover:shadow-2xl transform hover:scale-105"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
                </svg>
                Prendre rendez-vous
              </button>
            </div>
          </div>
        {/if}
      </section>

      <!-- Past Appointments with Timeline -->
      <section>
        <div class="flex items-center gap-4 mb-6">
          <div class="relative">
            <div class="w-16 h-16 bg-gradient-to-br from-gray-400 to-slate-600 rounded-2xl flex items-center justify-center shadow-xl transform rotate-6">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
          <div>
            <h3 class="text-3xl font-black text-gray-900">Historique</h3>
            <p class="text-gray-600">Vos consultations passées</p>
          </div>
        </div>
        
        {#if $pastAppointments.length}
          <div class="relative">
            <!-- Timeline line -->
            <div class="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-gray-300 via-gray-200 to-transparent"></div>
            
            <div class="space-y-6">
              {#each $pastAppointments as appointment, i (appointment.id)}
                <div
                  class="relative pl-20"
                  transition:fly={{ x: -20, duration: 400, delay: i * 80 }}
                >
                  <!-- Timeline dot -->
                  <div class="absolute left-0 top-6 w-16 h-16 flex items-center justify-center">
                    <div class={`w-12 h-12 rounded-full flex items-center justify-center shadow-lg ${
                      appointment.status === 'completed' ? 'bg-gradient-to-br from-green-400 to-emerald-600' :
                      appointment.status === 'cancelled' ? 'bg-gradient-to-br from-red-400 to-rose-600' :
                      'bg-gradient-to-br from-yellow-400 to-orange-600'
                    }`}>
                      <span class="text-2xl">
                        {appointment.status === 'completed' ? '✓' : appointment.status === 'cancelled' ? '✗' : '⊘'}
                      </span>
                    </div>
                  </div>
                  
                  <!-- Glassmorphism card -->
                  <div class="group relative">
                    <!-- Glass effect background -->
                    <div class="absolute inset-0 bg-white/40 backdrop-blur-xl rounded-3xl border border-white/20 shadow-2xl"></div>
                    <div class="absolute inset-0 bg-gradient-to-br from-white/60 to-white/30 rounded-3xl"></div>
                    
                    <!-- Card content -->
                    <div class="relative bg-white/80 backdrop-blur-sm rounded-3xl p-6 border-2 border-gray-100 hover:border-gray-200 transition-all">
                      <div class="flex items-start justify-between mb-4">
                        <div class="flex-1">
                          <!-- Doctor info -->
                          <div class="flex items-center gap-3 mb-3">
                            <div class="w-12 h-12 bg-gradient-to-br from-slate-400 to-gray-600 rounded-xl flex items-center justify-center text-white text-sm font-black shadow-md">
                              {appointment.doctor_first_name?.[0]}{appointment.doctor_last_name?.[0]}
                            </div>
                            <div>
                              <h4 class="text-lg font-black text-gray-900">
                                Dr. {appointment.doctor_first_name} {appointment.doctor_last_name}
                              </h4>
                              <p class="text-sm text-gray-600 font-semibold capitalize flex items-center gap-1.5">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                {CONSULTATION_LABELS[appointment.consultation_type]}
                              </p>
                            </div>
                          </div>
                          
                          <!-- Date and time -->
                          <div class="flex items-center gap-4 text-sm text-gray-700 mb-3">
                            <span class="flex items-center gap-1.5 font-bold">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(appointment.appointment_date).toLocaleDateString('fr-FR', { 
                                day: 'numeric', 
                                month: 'short',
                                year: 'numeric'
                              })}
                            </span>
                            <span class="flex items-center gap-1.5 font-bold">
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              {new Date(appointment.appointment_date).toLocaleTimeString('fr-FR', { 
                                hour: '2-digit', 
                                minute: '2-digit' 
                              })}
                            </span>
                          </div>
                          
                          {#if appointment.reason}
                            <div class="bg-gradient-to-r from-gray-50 to-slate-50 px-4 py-2 rounded-xl border border-gray-200">
                              <p class="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">Motif</p>
                              <p class="text-sm text-gray-800 font-semibold">{appointment.reason}</p>
                            </div>
                          {/if}

                          <!-- Teleconsultation info (if it was a teleconsultation) -->
                          {#if appointment.meet_link && appointment.consultation_type === 'teleconsultation'}
                            <div class="mt-3 bg-gradient-to-r from-green-50 to-emerald-50 px-4 py-2 rounded-xl border border-green-200">
                              <p class="text-xs font-bold text-green-600 uppercase tracking-wide flex items-center gap-1">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                </svg>
                                Téléconsultation effectuée
                              </p>
                            </div>
                          {/if}
                        </div>
                        
                        <!-- Status badge with morphism effect -->
                        <div class="flex flex-col gap-3">
                          <div class={`px-4 py-2 rounded-full font-bold text-sm shadow-lg border-2 ${
                            appointment.status === 'completed' 
                              ? 'bg-gradient-to-r from-green-100 to-emerald-100 text-green-700 border-green-300' 
                              : appointment.status === 'cancelled'
                              ? 'bg-gradient-to-r from-red-100 to-rose-100 text-red-700 border-red-300'
                              : 'bg-gradient-to-r from-yellow-100 to-orange-100 text-yellow-700 border-yellow-300'
                          }`}>
                            {
                              appointment.status === 'completed' ? '✓ Complété' :
                              appointment.status === 'cancelled' ? '✗ Annulé' :
                              '⊘ Non présenté'
                            }
                          </div>
                          
                          {#if appointment.status === 'completed'}
                            <button
                              on:click={() => openReviewModal(appointment)}
                              class="flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-amber-500 to-yellow-500 text-white rounded-full font-bold text-sm shadow-lg hover:shadow-xl hover:from-amber-600 hover:to-yellow-600 transition-all duration-300"
                              title="Noter ce rendez-vous"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                              </svg>
                              Noter
                            </button>
                          {/if}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else}
          <div 
            class="relative overflow-hidden bg-gradient-to-br from-gray-50 via-slate-50 to-gray-100 rounded-3xl p-16 text-center border-2 border-dashed border-gray-300"
            transition:scale={{ duration: 400 }}
          >
            <div class="w-32 h-32 bg-gradient-to-br from-gray-300 to-gray-500 rounded-full flex items-center justify-center mx-auto mb-6 shadow-2xl">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-16 w-16 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 class="text-3xl font-black text-gray-700 mb-3">Aucun historique disponible</h3>
            <p class="text-lg text-gray-600">Vos rendez-vous passés apparaîtront ici</p>
          </div>
        {/if}
      </section>
    </div>
  {/if}
</div>

{#if showBookingModal && selectedDoctor}
  <BookingModal
    show={showBookingModal}
    {selectedDoctor}
    {visibleSlotGroups}
    {canShowMoreSlots}
    {showAllSlots}
    {availabilityLoading}
    {availabilityError}
    {bookingPayload}
    {bookingSubmitting}
    onClose={closeBookingModal}
    onSlotSelect={selectSlot}
    onRefreshSlots={() => selectedDoctor && loadDoctorSchedule(selectedDoctor.doctor_id)}
    onSubmit={submitBooking}
    onToggleShowAllSlots={() => showAllSlots = !showAllSlots}
    {consultationTypeOptions}
  />
{:else if showBookingModal}
  <!-- Simple fallback: no doctor selected -->
  <div class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-2xl max-w-md w-full shadow-xl p-8" transition:fly={{ y: 20, duration: 300 }}>
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-xl font-bold text-gray-900">Nouveau Rendez-vous</h3>
        <button 
          on:click={closeBookingModal} 
          class="w-10 h-10 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors"
          title="Fermer"
        >
          <svg class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
      
      <div class="text-center py-12">
        <div class="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <h4 class="text-lg font-bold text-gray-900 mb-2">Aucun praticien sélectionné</h4>
        <p class="text-gray-600 mb-6">Recherchez et sélectionnez un praticien pour prendre rendez-vous</p>
        <button
          on:click={openBookingModal}
          class="inline-flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-semibold"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          Rechercher un praticien
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showRescheduleModal && rescheduleAppointment}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-3xl max-w-2xl w-full shadow-2xl overflow-hidden border-2 border-gray-100" transition:fly={{ y: 30, duration: 300, easing: elasticOut }}>
      <!-- Enhanced Header -->
      <div class="relative overflow-hidden bg-gradient-to-br from-blue-600 via-indigo-600 to-purple-700 p-8">
        <div class="absolute inset-0 bg-grid-white/10"></div>
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
        <div class="relative flex items-center justify-between">
          <div class="flex items-center gap-4">
            <div class="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-2xl flex items-center justify-center shadow-xl border-2 border-white/30">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div>
              <h3 class="text-2xl font-black text-white drop-shadow-lg">Replanifier le rendez-vous</h3>
              <p class="text-white/90 font-medium">Choisissez une nouvelle date</p>
            </div>
          </div>
          <button 
            on:click={() => showRescheduleModal = false} 
            class="w-12 h-12 bg-white/20 hover:bg-white/30 backdrop-blur-sm rounded-xl flex items-center justify-center transition-all border-2 border-white/30 hover:border-white/50 group"
            title="Fermer"
          >
            <svg class="h-6 w-6 text-white group-hover:rotate-90 transition-transform duration-300" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-8 space-y-6">
        <!-- Current Appointment Info -->
        <div class="relative overflow-hidden bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border-2 border-amber-200">
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-amber-200/30 to-orange-200/30 rounded-full blur-2xl -mr-16 -mt-16"></div>
          <div class="relative">
            <div class="flex items-center gap-3 mb-3">
              <div class="w-12 h-12 bg-gradient-to-br from-amber-500 to-orange-600 rounded-2xl flex items-center justify-center shadow-lg">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h4 class="text-lg font-black text-gray-900">Rendez-vous actuel</h4>
            </div>
            <p class="text-gray-700 font-semibold">{formatAppointmentLabel(rescheduleAppointment)}</p>
          </div>
        </div>
        
        <!-- New Date Input -->
        <div class="space-y-2">
          <label for="reschedule-datetime" class="flex items-center gap-2 text-sm font-bold text-gray-900">
            <div class="w-6 h-6 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            Nouvelle date et heure
          </label>
          <input
            id="reschedule-datetime"
            type="datetime-local"
            bind:value={rescheduleDate}
            class="w-full px-4 py-3.5 border-2 border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium bg-white hover:border-blue-400 shadow-sm"
          />
        </div>
        
        <!-- Notes Input -->
        <div class="space-y-2">
          <label for="reschedule-notes" class="flex items-center gap-2 text-sm font-bold text-gray-900">
            <div class="w-6 h-6 bg-gradient-to-br from-purple-500 to-fuchsia-600 rounded-lg flex items-center justify-center">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
              </svg>
            </div>
            Notes pour le praticien
            <span class="text-gray-500 font-normal text-xs ml-auto">(optionnel)</span>
          </label>
          <textarea
            id="reschedule-notes"
            rows="4"
            bind:value={rescheduleNotes}
            class="w-full px-4 py-3.5 border-2 border-gray-300 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-medium resize-none bg-white hover:border-blue-400 shadow-sm placeholder-gray-400"
            placeholder="Raison du changement, nouvelles informations..."
          ></textarea>
        </div>
      </div>
      
      <!-- Footer -->
      <div class="px-8 py-6 border-t-2 border-gray-200 flex gap-4 bg-gradient-to-r from-blue-50/30 via-indigo-50/30 to-purple-50/30">
        <button
          on:click={() => showRescheduleModal = false}
          class="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 font-bold rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md"
          disabled={rescheduleSubmitting}
        >
          <span class="flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
            Annuler
          </span>
        </button>
        <button
          on:click={() => showConfirmReschedule = true}
          class="group relative flex-[2] px-6 py-4 rounded-2xl font-black shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all overflow-hidden transform hover:scale-105 active:scale-95"
          disabled={rescheduleSubmitting}
        >
          <div class="absolute inset-0 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-700 opacity-90"></div>
          <div class="absolute inset-0 bg-white/10"></div>
          <div class="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
            {#if rescheduleSubmitting}
              <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Validation...
            {:else}
              <div class="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <span class="text-lg">Replanifier</span>
            {/if}
          </span>
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showConfirmCancel && pendingCancellation}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-50 p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-3xl max-w-lg w-full shadow-2xl overflow-hidden border-2 border-gray-100" transition:scale={{ duration: 300, easing: elasticOut }}>
      <!-- Enhanced Header -->
      <div class="relative overflow-hidden bg-gradient-to-br from-red-600 via-rose-600 to-pink-700 p-8">
        <div class="absolute inset-0 bg-grid-white/10"></div>
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
        <div class="relative flex items-center gap-4">
          <div class="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center shadow-2xl border-4 border-white/30 animate-pulse">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 class="text-2xl font-black text-white drop-shadow-lg">Confirmer l'annulation</h3>
            <p class="text-white/90 font-medium">Cette action est irréversible</p>
          </div>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-8 space-y-6">
        <div class="bg-gradient-to-br from-red-50 to-rose-50 rounded-2xl p-6 border-2 border-red-200">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-red-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1">
              <h4 class="text-lg font-black text-gray-900 mb-2">Rendez-vous concerné</h4>
              <p class="text-gray-700 font-semibold">{formatAppointmentLabel(pendingCancellation)}</p>
            </div>
          </div>
        </div>
        
        <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-6 border-2 border-amber-300">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-amber-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h5 class="font-black text-amber-900 mb-2">Important à savoir</h5>
              <ul class="space-y-1 text-sm text-amber-800 font-medium">
                <li class="flex items-start gap-2">
                  <span class="text-amber-600 font-black">•</span>
                  <span>Le praticien sera immédiatement notifié</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-amber-600 font-black">•</span>
                  <span>Vous ne pourrez pas annuler cette action</span>
                </li>
                <li class="flex items-start gap-2">
                  <span class="text-amber-600 font-black">•</span>
                  <span>Pensez à reprendre rendez-vous si nécessaire</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        
        <p class="text-center text-gray-600 font-semibold">Êtes-vous sûr de vouloir continuer ?</p>
      </div>
      
      <!-- Footer -->
      <div class="px-8 py-6 border-t-2 border-gray-200 flex gap-4 bg-gradient-to-r from-red-50/30 via-rose-50/30 to-pink-50/30">
        <button
          class="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 font-bold rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md"
          on:click={() => {
            showConfirmCancel = false;
            pendingCancellation = null;
          }}
        >
          <span class="flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Non, revenir
          </span>
        </button>
        <button
          class="group relative flex-[2] px-6 py-4 rounded-2xl font-black shadow-xl hover:shadow-2xl transition-all overflow-hidden transform hover:scale-105 active:scale-95"
          on:click={confirmCancelAppointment}
        >
          <div class="absolute inset-0 bg-gradient-to-r from-red-600 via-rose-600 to-pink-700 opacity-90"></div>
          <div class="absolute inset-0 bg-white/10"></div>
          <div class="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
            <div class="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <span class="text-lg">Oui, annuler le rendez-vous</span>
          </span>
        </button>
      </div>
    </div>
  </div>
{/if}

{#if showConfirmReschedule && rescheduleAppointment}
  <div class="fixed inset-0 bg-black/60 backdrop-blur-md flex items-center justify-center z-[60] p-4" transition:fade={{ duration: 200 }}>
    <div class="bg-white rounded-3xl max-w-lg w-full shadow-2xl overflow-hidden border-2 border-gray-100" transition:scale={{ duration: 300, easing: elasticOut }}>
      <!-- Enhanced Header -->
      <div class="relative overflow-hidden bg-gradient-to-br from-green-600 via-emerald-600 to-teal-700 p-8">
        <div class="absolute inset-0 bg-grid-white/10"></div>
        <div class="absolute top-0 right-0 w-64 h-64 bg-white/10 rounded-full blur-3xl -mr-32 -mt-32"></div>
        <div class="relative flex items-center gap-4">
          <div class="w-20 h-20 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center shadow-2xl border-4 border-white/30">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 class="text-2xl font-black text-white drop-shadow-lg">Confirmer la modification</h3>
            <p class="text-white/90 font-medium">Vérifiez les informations</p>
          </div>
        </div>
      </div>
      
      <!-- Content -->
      <div class="p-8 space-y-6">
        <div class="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-6 border-2 border-blue-200">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-blue-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <div class="flex-1">
              <h4 class="text-sm font-bold text-blue-700 uppercase tracking-wide mb-2">Rendez-vous actuel</h4>
              <p class="text-gray-700 font-semibold">{formatAppointmentLabel(rescheduleAppointment)}</p>
            </div>
          </div>
        </div>
        
        <div class="flex items-center justify-center">
          <div class="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center shadow-lg animate-bounce">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>
          </div>
        </div>
        
        <div class="bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-6 border-2 border-green-300">
          <div class="flex items-start gap-4">
            <div class="w-12 h-12 bg-green-500 rounded-2xl flex items-center justify-center flex-shrink-0 shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="flex-1">
              <h4 class="text-sm font-bold text-green-700 uppercase tracking-wide mb-2">Nouvelle date</h4>
              <p class="text-2xl font-black text-gray-900">{new Date(rescheduleDate).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</p>
              <p class="text-xl font-bold text-green-600 mt-1">{new Date(rescheduleDate).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</p>
            </div>
          </div>
        </div>
        
        <div class="bg-gradient-to-br from-amber-50 to-orange-50 rounded-2xl p-5 border-2 border-amber-200">
          <div class="flex items-start gap-3">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p class="text-sm text-amber-900 font-semibold">Le praticien sera notifié de ce changement par email</p>
          </div>
        </div>
        
        <p class="text-center text-gray-600 font-semibold">Confirmez-vous cette modification ?</p>
      </div>
      
      <!-- Footer -->
      <div class="px-8 py-6 border-t-2 border-gray-200 flex gap-4 bg-gradient-to-r from-green-50/30 via-emerald-50/30 to-teal-50/30">
        <button
          class="flex-1 px-6 py-4 border-2 border-gray-300 text-gray-700 font-bold rounded-2xl hover:bg-gray-50 hover:border-gray-400 transition-all shadow-sm hover:shadow-md"
          on:click={() => showConfirmReschedule = false}
        >
          <span class="flex items-center justify-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18" />
            </svg>
            Retour
          </span>
        </button>
        <button
          class="group relative flex-[2] px-6 py-4 rounded-2xl font-black shadow-xl hover:shadow-2xl disabled:opacity-50 disabled:cursor-not-allowed transition-all overflow-hidden transform hover:scale-105 active:scale-95"
          on:click={() => {
            showConfirmReschedule = false;
            void submitReschedule();
          }}
          disabled={rescheduleSubmitting}
        >
          <div class="absolute inset-0 bg-gradient-to-r from-green-600 via-emerald-600 to-teal-700 opacity-90"></div>
          <div class="absolute inset-0 bg-white/10"></div>
          <div class="absolute inset-0 bg-gradient-to-br from-white/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
          <span class="relative flex items-center justify-center gap-3 text-white drop-shadow-lg">
            {#if rescheduleSubmitting}
              <svg class="animate-spin h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Modification...
            {:else}
              <div class="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-xl flex items-center justify-center group-hover:rotate-12 transition-transform duration-300">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span class="text-lg">Confirmer la modification</span>
            {/if}
          </span>
        </button>
      </div>
    </div>
  </div>
{/if}

<!-- Review Modal -->
{#if showReviewModal && reviewAppointment}
  <!-- svelte-ignore a11y-no-noninteractive-tabindex -->
  <!-- svelte-ignore a11y-interactive-supports-focus -->
  <div 
    role="dialog"
    aria-modal="true"
    aria-labelledby="review-modal-title"
    tabindex="-1"
    class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    transition:fade={{ duration: 200 }}
    on:click={closeReviewModal}
    on:keydown={handleReviewModalKeydown}
  >
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <div 
      class="bg-white rounded-3xl max-w-lg w-full shadow-2xl transform"
      transition:fly={{ y: 20, duration: 300 }}
      on:click|stopPropagation
    >
      <!-- Header -->
      <div class="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-amber-50 to-yellow-50">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-12 h-12 bg-gradient-to-br from-amber-500 to-yellow-500 rounded-xl flex items-center justify-center shadow-lg">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-white" fill="currentColor" viewBox="0 0 20 20">
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </div>
            <div>
              <h3 id="review-modal-title" class="text-2xl font-bold text-gray-900">Noter le rendez-vous</h3>
              <p class="text-sm text-gray-600 font-medium">Dr. {reviewAppointment.doctor_first_name} {reviewAppointment.doctor_last_name}</p>
            </div>
          </div>
          <button 
            on:click={closeReviewModal}
            class="w-10 h-10 hover:bg-gray-100 rounded-lg flex items-center justify-center transition-colors"
            title="Fermer"
          >
            <svg class="h-5 w-5 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="px-8 py-6 space-y-6">
        <!-- Star Rating -->
        <div>
          <div id="rating-label" class="block text-sm font-bold text-gray-700 mb-3">Votre note <span class="text-red-500">*</span></div>
          <div class="flex items-center gap-2" role="group" aria-labelledby="rating-label">
            {#each [1, 2, 3, 4, 5] as star}
              <button
                type="button"
                aria-label="{star} étoile{star > 1 ? 's' : ''}"
                on:click={() => reviewRating = star}
                class="group transition-transform duration-200 hover:scale-110 active:scale-95"
              >
                <svg 
                  xmlns="http://www.w3.org/2000/svg" 
                  class="h-10 w-10 transition-colors duration-200 {reviewRating >= star ? 'text-yellow-400' : 'text-gray-300'} group-hover:text-yellow-300" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </button>
            {/each}
            {#if reviewRating > 0}
              <span class="ml-3 text-sm font-bold text-gray-700">{reviewRating}/5</span>
            {/if}
          </div>
        </div>

        <!-- Comment -->
        <div>
          <label for="review-comment" class="block text-sm font-bold text-gray-700 mb-2">
            Votre avis (facultatif)
          </label>
          <textarea
            id="review-comment"
            bind:value={reviewComment}
            class="w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-amber-500 focus:border-transparent transition-all resize-none"
            rows="4"
            placeholder="Partagez votre expérience avec ce médecin..."
            maxlength="1000"
          ></textarea>
          <p class="text-xs text-gray-500 mt-1">{reviewComment.length}/1000 caractères</p>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-8 py-6 bg-gray-50 border-t border-gray-200 rounded-b-3xl flex gap-3">
        <button
          on:click={closeReviewModal}
          class="flex-1 px-6 py-3 border-2 border-gray-300 text-gray-700 font-bold rounded-xl hover:bg-gray-100 transition-colors"
        >
          Annuler
        </button>
        <button
          on:click={submitReview}
          disabled={reviewRating === 0 || reviewSubmitting}
          class="flex-1 px-6 py-3 bg-gradient-to-r from-amber-500 to-yellow-500 text-white font-bold rounded-xl hover:from-amber-600 hover:to-yellow-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
        >
          {#if reviewSubmitting}
            <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Envoi...
          {:else}
            Envoyer l'avis
          {/if}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  .perspective-1000 {
    perspective: 1000px;
  }
  
  .preserve-3d {
    transform-style: preserve-3d;
  }
  
  .rotate-y-5 {
    transform: rotateY(5deg);
  }
  
  @keyframes confettiFloat {
    0% {
      transform: translateY(0) rotate(0deg);
      opacity: 1;
    }
    100% {
      transform: translateY(100vh) rotate(720deg);
      opacity: 0;
    }
  }
  
  @keyframes blob {
    0%, 100% {
      transform: translate(0, 0) scale(1);
    }
    33% {
      transform: translate(30px, -50px) scale(1.1);
    }
    66% {
      transform: translate(-20px, 20px) scale(0.9);
    }
  }
  
  .animate-blob {
    animation: blob 7s infinite;
  }
  
  .animation-delay-2000 {
    animation-delay: 2s;
  }
  
  .animation-delay-4000 {
    animation-delay: 4s;
  }
  
  .animation-delay-150 {
    animation-delay: 150ms;
  }
</style>

