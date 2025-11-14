<script lang="ts">
  import { onMount, createEventDispatcher, tick } from 'svelte';
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
    getDoctorAvailableSlots,
    type ConsultationType,
    type DoctorScheduleEntry,
    type AvailableSlot
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
  import RescheduleModal from '../../components/booking/RescheduleModal.svelte';
  import TeleconsultationButton from '../../components/TeleconsultationButton.svelte';
  
  // WebSocket
  import { DoctorScheduleSocket, type WebSocketMessage } from '../../lib/websocket';
  import { get } from 'svelte/store';

  const dispatch = createEventDispatcher();
  
  // WebSocket state
  let wsClient: DoctorScheduleSocket | null = null;
  let wsConnected = false;
  
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
  let rescheduleNotes = '';
  let rescheduleSchedule: DoctorScheduleEntry[] = []; // 🗑️ Obsolète, remplacé par rescheduleSlotsCache
  let rescheduleSlotsCache: SlotSuggestion[] = []; // 🆕 Cache des créneaux absolus depuis l'API
  let rescheduleAvailabilityLoading = false;
  let rescheduleAvailabilityError: string | null = null;
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

  // 🆕 Utilise la nouvelle API /available-slots qui croise automatiquement:
  // - Horaires récurrents du médecin
  // - Slots bloqués (congés, absences)
  // - Rendez-vous déjà réservés
  const loadDoctorSchedule = async (doctorId: number) => {
    availabilityLoading = true;
    availabilityError = null;
    showAllSlots = false;
    
    try {
      // Charger les créneaux pour les 30 prochains jours
      const today = new Date();
      const endDate = new Date(today);
      endDate.setDate(today.getDate() + 30);
      
      const startDateStr = today.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];
      
      console.log('🔍 Chargement des créneaux disponibles:', {
        doctorId,
        startDate: startDateStr,
        endDate: endDateStr,
        consultationType: bookingPayload.consultation_type
      });
      
      const availableSlots = await getDoctorAvailableSlots(
        doctorId,
        startDateStr,
        endDateStr,
        bookingPayload.consultation_type
      );
      
      console.log('✅ Créneaux reçus:', availableSlots);
      console.log('📊 Nombre de créneaux:', availableSlots?.length);
      
      if (!availableSlots || !Array.isArray(availableSlots)) {
        console.error('❌ Format de réponse invalide:', availableSlots);
        throw new Error('Format de réponse invalide du serveur');
      }
      
      // Filtrer uniquement les créneaux disponibles et convertir au format SlotSuggestion
      availableSlotsList = availableSlots.filter(slot => slot.is_available);
      console.log('✅ Créneaux disponibles filtrés:', availableSlotsList.length);
      
      // Grouper les créneaux par jour
      const groupedSlots = new Map<string, SlotSuggestion[]>();
      
      availableSlotsList.forEach(slot => {
        const startDate = new Date(slot.start_time);
        const endDate = new Date(slot.end_time);
        const dateKey = startDate.toISOString().split('T')[0];
        
        const slotSuggestion: SlotSuggestion = {
          entry: {
            id: slot.schedule_entry_id,
            doctor_id: slot.doctor_id,
            day_of_week: startDate.getDay(),
            start_time: startDate.toTimeString().slice(0, 5),
            end_time: endDate.toTimeString().slice(0, 5),
            consultation_type: slot.consultation_types[0] || 'IN_PERSON',
            slot_duration: Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60)),
            break_duration: 0,
            location: slot.location,
            is_active: true,
            created_at: new Date().toISOString()
          } as DoctorScheduleEntry,
          start: startDate,
          end: endDate,
          consultation_type: slot.consultation_types[0] || 'IN_PERSON',
          location: slot.location
        };
        
        if (!groupedSlots.has(dateKey)) {
          groupedSlots.set(dateKey, []);
        }
        groupedSlots.get(dateKey)!.push(slotSuggestion);
      });
      
      // Convertir en format SlotSuggestionGroup
      slotSuggestionGroups = Array.from(groupedSlots.entries()).map(([dateKey, slots]) => {
        const firstSlot = slots[0];
        const dateObj = firstSlot.start;
        const dateLabel = dateObj.toLocaleDateString('fr-FR', {
          weekday: 'long',
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        });
        
        return {
          key: dateKey,
          date: dateObj,
          dateLabel: dateLabel,
          label: dateLabel,
          slots: slots.sort((a, b) => a.start.getTime() - b.start.getTime())
        };
      });
      
      console.log('📅 Groupes de créneaux créés:', slotSuggestionGroups.length);
      
    } catch (err: any) {
      console.error('❌ Erreur lors du chargement des disponibilités du praticien:', err);
      console.error('📊 Détails erreur:', {
        message: err?.message,
        response: err?.response?.data,
        status: err?.response?.status,
        url: err?.config?.url
      });
      
      // Message d'erreur plus détaillé
      if (err?.response?.status === 404) {
        availabilityError = "Médecin non trouvé";
      } else if (err?.response?.status === 400) {
        availabilityError = err?.response?.data?.detail || "Paramètres invalides";
      } else if (err?.response?.status === 500) {
        availabilityError = "Erreur serveur. Veuillez réessayer plus tard.";
      } else {
        availabilityError = "Impossible de récupérer les créneaux du praticien";
      }
      
      availableSlotsList = [];
      slotSuggestionGroups = [];
    } finally {
      availabilityLoading = false;
    }
  };

  // Variables pour les créneaux
  let availableSlotsList: AvailableSlot[] = [];
  let slotSuggestionGroups: SlotSuggestionGroup[] = [];
  let visibleSlotGroups: SlotSuggestionGroup[] = [];
  let canShowMoreSlots = false;
  let showAllSlots = false;

  // Reactive statements
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
    
    // 🆕 Déconnecter le WebSocket à la fermeture
    disconnectWebSocket();
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
    
    // 🆕 Connecter au WebSocket pour écouter les mises à jour en temps réel
    await connectWebSocket(doctor.doctor_id);
  };
  
  /**
   * 🆕 Établir connexion WebSocket pour synchronisation temps réel
   */
  const connectWebSocket = async (doctorId: number) => {
    try {
      // Récupérer le token JWT
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.warn('⚠️ Pas de token JWT - WebSocket désactivé');
        return;
      }
      
      // Fermer connexion existante si présente
      if (wsClient) {
        wsClient.disconnect();
        wsClient = null;
      }
      
      // Créer nouveau client WebSocket
      wsClient = new DoctorScheduleSocket(doctorId, token);
      
      // Écouter l'événement de connexion
      wsClient.on('connected', (message: WebSocketMessage) => {
        console.log('✅ WebSocket connecté:', message);
        wsConnected = true;
      });
      
      // Écouter les mises à jour de planning
      wsClient.on('schedule_updated', async (message: WebSocketMessage) => {
        console.log('📅 Planning mis à jour par le médecin:', message);
        toast.info('Planning mis à jour - Actualisation...');
        await loadDoctorSchedule(doctorId);
      });
      
      // Écouter les réservations de créneaux
      wsClient.on('slot_booked', async (message: WebSocketMessage) => {
        console.log('🎯 Créneau réservé:', message);
        toast.warning('Un créneau a été réservé - Actualisation...');
        await loadDoctorSchedule(doctorId);
      });
      
      // Écouter les annulations
      wsClient.on('appointment_cancelled', async (message: WebSocketMessage) => {
        console.log('❌ Rendez-vous annulé:', message);
        toast.info('Un rendez-vous a été annulé - Actualisation...');
        await loadDoctorSchedule(doctorId);
      });
      
      // Connecter
      await wsClient.connect();
      
    } catch (error) {
      console.error('❌ Erreur connexion WebSocket:', error);
      wsConnected = false;
      // Ne pas bloquer l'interface si WebSocket échoue
    }
  };
  
  /**
   * 🆕 Déconnecter le WebSocket
   */
  const disconnectWebSocket = () => {
    if (wsClient) {
      console.log('🔌 Déconnexion WebSocket...');
      wsClient.disconnect();
      wsClient = null;
      wsConnected = false;
    }
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

  let rescheduleDoctorDetails: DoctorSearchResult | null = null;

  const openRescheduleModal = async (appointment: PatientAppointment) => {
    if (!appointment?.doctor_id) {
      console.error('❌ Impossible de replanifier: doctor_id manquant sur le rendez-vous', appointment);
      toast.error("Ce rendez-vous n'est pas associé à un praticien valide");
      return;
    }

    rescheduleAppointment = appointment;
    rescheduleNotes = appointment.patient_notes ?? '';
    rescheduleSchedule = [];
    rescheduleAvailabilityError = null;
    showRescheduleModal = true;
    showConfirmReschedule = false;

    // Récupérer les détails du médecin pour connaître les types de consultation disponibles
    try {
      // Essayer de trouver le médecin dans selectedDoctor ou faire une recherche
      if (selectedDoctor && selectedDoctor.doctor_id === appointment.doctor_id) {
        rescheduleDoctorDetails = selectedDoctor;
      } else {
        // Simuler un objet doctor avec consultation_types 'both' par défaut
        // Dans une vraie application, on devrait faire un appel API pour récupérer les détails
        rescheduleDoctorDetails = {
          doctor_id: appointment.doctor_id,
          first_name: appointment.doctor_first_name || '',
          last_name: appointment.doctor_last_name || '',
          specialty: 'general',
          consultation_types: 'both',
          location: '',
          average_rating: 0,
          total_reviews: 0,
          consultation_duration: 30,
          languages: [],
          accepts_new_patients: true
        } as DoctorSearchResult;
      }
    } catch (error) {
      console.warn('⚠️ Impossible de récupérer les détails du médecin, utilisation des valeurs par défaut');
      rescheduleDoctorDetails = null;
    }

    // Charger les créneaux dans une micro-tâche pour laisser la modal s'afficher instantanément
    Promise.resolve().then(async () => {
      try {
        await tick();
        await loadRescheduleSchedule(appointment.doctor_id, appointment.consultation_type);
      } catch (error) {
        console.error('❌ Erreur lors du chargement des créneaux pour la replanification:', error);
        toast.error("Impossible de récupérer les créneaux du praticien");
      }
    });
  };

  // 🆕 Utilise également la nouvelle API /available-slots pour la replanification
  const loadRescheduleSchedule = async (doctorId: number, consultationType: ConsultationType) => {
    rescheduleAvailabilityLoading = true;
    rescheduleAvailabilityError = null;
    
    // 🧹 Réinitialiser le cache des créneaux avant rechargement
    rescheduleSlotsCache = [];
    rescheduleSchedule = [];
    
    try {
      // Charger les créneaux pour les 30 prochains jours
      const today = new Date();
      const endDate = new Date(today);
      endDate.setDate(today.getDate() + 30);
      
      const startDateStr = today.toISOString().split('T')[0];
      const endDateStr = endDate.toISOString().split('T')[0];
      
      console.log('🔍 Chargement des créneaux pour replanification:', {
        doctorId,
        startDate: startDateStr,
        endDate: endDateStr,
        consultationType: consultationType
      });
      
      const availableSlots = await getDoctorAvailableSlots(
        doctorId,
        startDateStr,
        endDateStr,
        consultationType
      );
      
      console.log('✅ Créneaux de replanification reçus:', availableSlots?.length);
      
      if (!availableSlots || !Array.isArray(availableSlots)) {
        console.error('❌ Format de réponse invalide:', availableSlots);
        throw new Error('Format de réponse invalide du serveur');
      }
      
      // ⚠️ Ne plus filtrer - garder TOUS les créneaux (disponibles et non disponibles)
      // pour afficher les créneaux bloqués en rouge/rayé
      
      // 🆕 Convertir directement en SlotSuggestion[] au lieu de DoctorScheduleEntry[]
      // car l'API retourne des créneaux absolus (avec dates), pas des créneaux récurrents
      rescheduleSlotsCache = availableSlots.map(slot => {
        const startDate = new Date(slot.start_time);
        const endDate = new Date(slot.end_time);
        
        return {
          entry: {
            id: slot.schedule_entry_id,
            doctor_id: slot.doctor_id,
            day_of_week: startDate.getDay(),
            start_time: startDate.toTimeString().slice(0, 5),
            end_time: endDate.toTimeString().slice(0, 5),
            consultation_type: slot.consultation_types[0] || 'in_person',
            slot_duration: Math.floor((endDate.getTime() - startDate.getTime()) / (1000 * 60)),
            break_duration: 0,
            location: slot.location,
            created_at: new Date().toISOString()
          },
          start: startDate,
          end: endDate,
          consultation_type: slot.consultation_types[0] || 'in_person',
          location: slot.location,
          is_available: slot.is_available
        };
      });
      
      // Garder un tableau vide pour rescheduleSchedule (plus utilisé)
      rescheduleSchedule = [];
      
      console.log('✅ Créneaux de replanification convertis:', rescheduleSlotsCache.length);
      console.log('📋 Premiers créneaux:', rescheduleSlotsCache.slice(0, 3).map(s => ({
        start: s.start.toISOString(),
        end: s.end.toISOString(),
        type: s.consultation_type,
        available: s.is_available
      })));
      
    } catch (err: any) {
      console.error('❌ Erreur lors du chargement des disponibilités:', err);
      console.error('📊 Détails erreur:', {
        message: err?.message,
        response: err?.response?.data,
        status: err?.response?.status
      });
      
      if (err?.response?.status === 404) {
        rescheduleAvailabilityError = "Médecin non trouvé";
      } else if (err?.response?.status === 400) {
        rescheduleAvailabilityError = err?.response?.data?.detail || "Paramètres invalides";
      } else {
        rescheduleAvailabilityError = "Impossible de récupérer les créneaux du praticien";
      }
      
      // 🧹 Vider les caches en cas d'erreur
      rescheduleSchedule = [];
      rescheduleSlotsCache = [];
    } finally {
      rescheduleAvailabilityLoading = false;
    }
  };

  // submitReschedule est appelé par le RescheduleModal quand on clique sur "Replanifier"
  // Il affiche l'écran de confirmation DANS le RescheduleModal
  const submitReschedule = async () => {
    if (!rescheduleAppointment) return;
    showConfirmReschedule = true;
  };

  // confirmReschedule est appelé par le RescheduleModal quand on clique sur "Confirmer la modification"
  // dans l'écran de confirmation intégré
  const confirmReschedule = async () => {
    if (!rescheduleAppointment) return;
    rescheduleSubmitting = true;
    
    console.log('🔧 DEBUG - confirmReschedule called');
    console.log('📅 Appointment ID:', rescheduleAppointment.id);
    console.log('📅 New appointment_date:', rescheduleAppointment.appointment_date);
    console.log('� New consultation_type:', rescheduleAppointment.consultation_type);
    console.log('�📝 Notes:', rescheduleNotes);
    
    try {
      const updateData = {
        appointment_date: rescheduleAppointment.appointment_date,
        consultation_type: rescheduleAppointment.consultation_type,
        patient_notes: rescheduleNotes || undefined
      };
      console.log('📤 Sending update request with data:', updateData);
      
      const result = await updatePatientAppointment(rescheduleAppointment.id, updateData);
      console.log('✅ Update successful:', result);
      
      toast.success('Rendez-vous replanifié avec succès');
      showRescheduleModal = false;
      showConfirmReschedule = false;
      rescheduleAppointment = null;
      rescheduleNotes = '';
      await loadAppointments();
      dispatch('refresh');
    } catch (err: any) {
      console.error('❌ Erreur lors du report du rendez-vous:', err);
      console.error('📊 Error response:', err?.response?.data);
      console.error('📊 Error status:', err?.response?.status);
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
                  <div class="absolute -inset-1 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 rounded-3xl blur opacity-25 group-hover:opacity-75 transition-opacity duration-500 -z-10"></div>
                  
                  <!-- Main Card -->
                  <div class="relative bg-white rounded-3xl p-8 shadow-2xl border-2 border-gray-100 overflow-hidden z-10">
                    <!-- Animated background pattern -->
                    <div class="absolute top-0 right-0 w-64 h-64 bg-gradient-to-br from-blue-50 to-purple-50 rounded-full blur-3xl -mr-32 -mt-32 opacity-50 group-hover:scale-150 transition-transform duration-1000 -z-10"></div>
                    
                    <!-- Status badge with animation -->
                    <div class="absolute top-6 right-6 z-20 pointer-events-none">
                      <div class={`relative px-4 py-2 rounded-full font-bold text-sm shadow-lg transform transition-transform duration-300 ${
                        appointment.status === 'confirmed' 
                          ? 'bg-gradient-to-r from-green-400 to-emerald-600 text-white group-hover:scale-110' 
                          : 'bg-gradient-to-r from-blue-400 to-indigo-600 text-white group-hover:scale-110'
                      }`}>
                        <div class="absolute inset-0 rounded-full bg-white/20 animate-ping pointer-events-none"></div>
                        <span class="relative">
                          {appointment.status === 'confirmed' ? '✓ Confirmé' : '⏱ En attente'}
                        </span>
                      </div>
                    </div>
                    
                    <div class="relative z-30">
                      <!-- Doctor info with avatar -->
                      <div class="flex items-start gap-4 mb-6 relative">
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
                        <div class={`inline-flex items-center gap-2 px-4 py-2 rounded-xl border-2 ${
                          appointment.consultation_type === 'teleconsultation' 
                            ? 'bg-gradient-to-r from-emerald-50 to-green-50 border-emerald-200'
                            : appointment.consultation_type === 'both'
                            ? 'bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200'
                            : 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200'
                        }`}>
                          {#if appointment.consultation_type === 'teleconsultation'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                            </svg>
                            <span class="font-bold text-emerald-700">
                              {CONSULTATION_LABELS[appointment.consultation_type]}
                            </span>
                          {:else if appointment.consultation_type === 'both'}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                            </svg>
                            <span class="font-bold text-purple-700">
                              {CONSULTATION_LABELS[appointment.consultation_type]}
                            </span>
                          {:else}
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                            </svg>
                            <span class="font-bold text-blue-700">
                              {CONSULTATION_LABELS[appointment.consultation_type]}
                            </span>
                          {/if}
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

                      <!-- Action buttons -->
                      <div class="flex gap-3 relative z-40">
                        <button
                          on:click|stopPropagation={() => openRescheduleModal(appointment)}
                          class="flex-1 px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors shadow-sm hover:shadow-md"
                        >
                          <span class="flex items-center justify-center gap-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                            </svg>
                            Replanifier
                          </span>
                        </button>
                        <button
                          on:click|stopPropagation={() => promptCancelAppointment(appointment)}
                          class="flex-1 px-6 py-3 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-colors shadow-sm hover:shadow-md"
                        >
                          <span class="flex items-center justify-center gap-2">
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
                                {#if appointment.consultation_type === 'teleconsultation'}
                                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                  </svg>
                                {:else if appointment.consultation_type === 'both'}
                                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                                  </svg>
                                {:else}
                                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                                  </svg>
                                {/if}
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
    {wsConnected}
    {bookingPayload}
    {bookingSubmitting}
    onClose={closeBookingModal}
    onSlotSelect={selectSlot}
    onRefreshSlots={() => selectedDoctor && loadDoctorSchedule(selectedDoctor.doctor_id)}
    onSubmit={submitBooking}
    onToggleShowAllSlots={() => showAllSlots = !showAllSlots}
    onConsultationTypeChange={() => selectedDoctor && loadDoctorSchedule(selectedDoctor.doctor_id)}
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

<!-- Reschedule Modal -->
<RescheduleModal
  show={showRescheduleModal}
  appointment={rescheduleAppointment}
  doctorSchedule={rescheduleSchedule}
  slotsCache={rescheduleSlotsCache}
  availabilityLoading={rescheduleAvailabilityLoading}
  availabilityError={rescheduleAvailabilityError}
  doctorDetails={rescheduleDoctorDetails}
  bind:rescheduleNotes
  submitting={rescheduleSubmitting}
  showConfirm={showConfirmReschedule}
  onClose={() => showRescheduleModal = false}
  onLoadSchedule={loadRescheduleSchedule}
  onSubmit={submitReschedule}
  onConfirm={confirmReschedule}
  onBack={() => showConfirmReschedule = false}
/>

<!-- Cancel Confirmation Modal -->

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

