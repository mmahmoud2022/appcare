/**
 * Store Svelte pour la gestion des rendez-vous patients
 */

import { writable, derived } from 'svelte/store';
import type { PatientAppointment } from '../lib/api-patient';

// Store principal des rendez-vous
export const appointments = writable<PatientAppointment[]>([]);

// Store de l'état de chargement
export const loading = writable<boolean>(false);

// Store des erreurs
export const error = writable<string | null>(null);

// Rendez-vous à venir (dérivé)
export const upcomingAppointments = derived(
  appointments,
  ($appointments) => {
    const now = new Date();
    // Garder les rendez-vous jusqu'à 60 minutes après leur heure de début
    // pour permettre l'accès à la téléconsultation pendant la session
    const cutoffTime = new Date(now.getTime() - 60 * 60 * 1000); // 60 minutes avant maintenant
    
    return $appointments
      .filter((appt) => {
        const apptDate = new Date(appt.appointment_date);
        return apptDate >= cutoffTime && appt.status !== 'cancelled';
      })
      .sort((a, b) => 
        new Date(a.appointment_date).getTime() - 
        new Date(b.appointment_date).getTime()
      );
  }
);

// Rendez-vous passés (dérivé)
export const pastAppointments = derived(
  appointments,
  ($appointments) => {
    const now = new Date();
    // Un rendez-vous est considéré "passé" seulement 60 minutes après son heure
    // Cela permet de maintenir l'accès à la téléconsultation pendant la session
    const cutoffTime = new Date(now.getTime() - 60 * 60 * 1000); // 60 minutes avant maintenant
    
    return $appointments
      .filter((appt) => {
        const apptDate = new Date(appt.appointment_date);
        return (
          apptDate < cutoffTime || 
          appt.status === 'completed' || 
          appt.status === 'cancelled'
        );
      })
      .sort((a, b) => 
        new Date(b.appointment_date).getTime() - 
        new Date(a.appointment_date).getTime()
      );
  }
);

// Statistiques des rendez-vous (dérivé)
export const appointmentStats = derived(
  appointments,
  ($appointments) => ({
    total: $appointments.length,
    upcoming: $appointments.filter(a => 
      new Date(a.appointment_date) >= new Date() && a.status !== 'cancelled'
    ).length,
    completed: $appointments.filter(a => a.status === 'completed').length,
    cancelled: $appointments.filter(a => a.status === 'cancelled').length,
  })
);
