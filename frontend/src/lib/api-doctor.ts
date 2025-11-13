// API Types and Functions for Doctor
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getToken = (): string | null => {
  return localStorage.getItem('access_token');
};

const getAuthHeaders = () => ({
  Authorization: `Bearer ${getToken()}`,
  'Content-Type': 'application/json',
});

// Enums
export type ConsultationType = 'in_person' | 'teleconsultation' | 'both';
export type AppointmentStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show';
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

export type Specialty = 
  | 'general_practitioner'
  | 'cardiologist'
  | 'dermatologist'
  | 'pediatrician'
  | 'gynecologist'
  | 'psychiatrist'
  | 'ophthalmologist'
  | 'dentist'
  | 'orthopedist'
  | 'neurologist'
  | 'radiologist'
  | 'surgeon'
  | 'other';

// Types
export interface DoctorScheduleEntry {
  id: number;
  doctor_id: number;
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration: number;
  break_duration: number;
  consultation_type: ConsultationType;
  location?: string;
  created_at: string;
}

export interface DoctorMessage {
  id: number;
  sender_id: number;
  recipient_id: number;
  subject?: string;
  content: string;
  is_read: boolean;
  read_at?: string;
  created_at: string;
  sender_first_name: string;
  sender_last_name: string;
  recipient_first_name: string;
  recipient_last_name: string;
}

export interface Payment {
  id: number;
  doctor_id: number;
  patient_id: number;
  appointment_id?: number;
  amount: number;
  currency: string;
  payment_method?: string;
  status: PaymentStatus;
  transaction_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface DoctorAppointment {
  id: number;
  doctor_id: number;
  patient_id: number;
  patient_first_name?: string;
  patient_last_name?: string;
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

export interface DoctorProfile {
  id: number;
  user_id: number;
  specialty: Specialty;
  sub_specialty?: string;
  rpps_number?: string;
  office_address?: string;
  office_city?: string;
  office_postal_code?: string;
  office_phone?: string;
  biography?: string;
  languages: string[];
  education: any[];
  experience_years: number;
  consultation_types: ConsultationType;
  consultation_duration: number;
  consultation_price?: number;
  accepts_new_patients: boolean;
  is_public: boolean;
  is_verified: boolean;
  total_consultations: number;
  average_rating: number;
  total_reviews: number;
  created_at: string;
  updated_at?: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

// API Functions
export const getDoctorSchedule = async (doctorId: number) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/${doctorId}/schedule`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getDoctorProfile = async (doctorId: number): Promise<DoctorProfile> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/${doctorId}`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getMyDoctorProfile = async (): Promise<DoctorProfile> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/me`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getDoctorAppointments = async (
  page = 1,
  page_size = 10,
  status?: AppointmentStatus
) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/appointments`, {
    params: { page, page_size, status },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getDoctorMessages = async (page = 1, page_size = 10) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/messages`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getDoctorPayments = async (page = 1, page_size = 10) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/payments`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};
