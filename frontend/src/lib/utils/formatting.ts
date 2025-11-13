// Formatting Utilities
import type { ConsultationType } from '../api-patient';

export const CONSULTATION_LABELS: Record<ConsultationType, string> = {
  in_person: 'En présentiel',
  teleconsultation: 'Téléconsultation',
  both: 'Les deux',
};

export const formatSpecialty = (specialty: string): string => {
  const specialtyMap: Record<string, string> = {
    general_practitioner: 'Médecin généraliste',
    cardiologist: 'Cardiologue',
    dermatologist: 'Dermatologue',
    pediatrician: 'Pédiatre',
    gynecologist: 'Gynécologue',
    psychiatrist: 'Psychiatre',
    ophthalmologist: 'Ophtalmologue',
    dentist: 'Dentiste',
    orthopedist: 'Orthopédiste',
    neurologist: 'Neurologue',
    radiologist: 'Radiologue',
    surgeon: 'Chirurgien',
    other: 'Autre',
  };
  return specialtyMap[specialty] || specialty;
};
