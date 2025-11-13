import { writable } from 'svelte/store';

// Holds the appointment id that should be opened in the appointments view/modal.
export const selectedAppointmentId = writable<string | null>(null);

export const openAppointment = (id: string | number) => {
  selectedAppointmentId.set(String(id));
};

export const clearSelectedAppointment = () => {
  selectedAppointmentId.set(null);
};
