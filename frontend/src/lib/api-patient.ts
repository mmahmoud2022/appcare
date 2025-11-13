// API Types and Functions for Patient
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Auth Token Management
export const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

export const setToken = (token: string): void => {
  localStorage.setItem('access_token', token);
};

const getAuthHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
  'Content-Type': 'application/json',
});

// Enums
export type ConsultationType = 'in_person' | 'teleconsultation' | 'both';
export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';

// Types
export interface PatientAppointment {
  id: number;
  doctor_id: number;
  doctor_first_name?: string;
  doctor_last_name?: string;
  doctor_specialty?: string;
  appointment_date: string;
  consultation_type: ConsultationType;
  status: AppointmentStatus;
  reason?: string;
  is_teleconsultation: boolean;
  meet_link?: string | null;
  schedule_entry_id?: number;
  patient_notes?: string;
  doctor_notes?: string;
  duration: number;
  price?: number;
}

export interface DoctorSearchResult {
  id: number;
  user_id: number;
  first_name: string;
  last_name: string;
  specialty: string;
  sub_specialty?: string;
  office_city?: string;
  biography?: string;
  languages: string[];
  experience_years: number;
  consultation_types: ConsultationType;
  consultation_duration: number;
  consultation_price?: number;
  accepts_new_patients: boolean;
  average_rating: number;
  total_reviews: number;
  total_consultations: number;
}

export interface DoctorReviewCreate {
  doctor_id: number;
  appointment_id?: number;
  rating: number;
  comment?: string;
}

// API Functions
export const getPatientAppointments = async (page = 1, page_size = 10) => {
  const response = await axios.get(`${API_URL}/api/v1/patient/appointments`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const createPatientAppointment = async (data: {
  doctor_id: number;
  appointment_date: string;
  consultation_type: ConsultationType;
  reason?: string;
  patient_notes?: string;
  schedule_entry_id?: number;
}) => {
  const response = await axios.post(`${API_URL}/api/v1/patient/appointments`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const updatePatientAppointment = async (appointmentId: number, data: {
  appointment_date?: string;
  consultation_type?: ConsultationType;
  reason?: string;
  patient_notes?: string;
}) => {
  const response = await axios.patch(`${API_URL}/api/v1/patient/appointments/${appointmentId}`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const cancelPatientAppointment = async (appointmentId: number) => {
  const response = await axios.delete(`${API_URL}/api/v1/patient/appointments/${appointmentId}`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const createDoctorReview = async (data: DoctorReviewCreate) => {
  const response = await axios.post(`${API_URL}/api/v1/patient/reviews`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};
