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
export type PaymentStatus = 'pending' | 'completed' | 'failed' | 'refunded';

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
  doctor_id: number;
  first_name: string;
  last_name: string;
  specialty: string;
  city?: string;
  consultation_types: ConsultationType;
  consultation_duration: number;
  consultation_price?: number;
  average_rating: number;
  total_reviews: number;
  languages: string[];
  accepts_new_patients: boolean;
}

export interface DoctorSearchResponse {
  total: number;
  page: number;
  page_size: number;
  items: DoctorSearchResult[];
}

export interface DoctorReviewCreate {
  doctor_id: number;
  appointment_id?: number;
  rating: number;
  comment?: string;
  is_public?: boolean;
}

export interface DocumentResponse {
  id: number;
  appointment_id?: number;
  document_type: string;
  file_name: string;
  file_path: string;
  file_size: number;
  uploaded_at: string;
  title?: string;
  description?: string;
  created_at?: string;
}

export interface ElectronicPrescriptionResponse {
  id: number;
  appointment_id: number;
  prescription_date: string;
  medications: any[];
  instructions?: string;
  status: string;
  prescription_number?: string;
  issued_at?: string;
}

export interface PatientMedicalRecord {
  appointments: PatientAppointment[];
  documents: DocumentResponse[];
  prescriptions: ElectronicPrescriptionResponse[];
}

export interface PaymentResponse {
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

export interface PatientPaymentHistory {
  total: number;
  page: number;
  page_size: number;
  items: PaymentResponse[];
}

export interface MessageResponse {
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

export interface PatientMessageList {
  total: number;
  page: number;
  page_size: number;
  items: MessageResponse[];
}

export interface PatientProfile {
  id: number;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  gender?: string;
  date_of_birth?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  notification_preferences?: Record<string, boolean>;
  marketing_consent?: boolean;
  data_processing_consent?: boolean;
  created_at: string;
  updated_at?: string;
  terms_accepted_at?: string;
}

export interface PatientProfileUpdatePayload {
  first_name?: string;
  last_name?: string;
  phone?: string;
  gender?: string;
  date_of_birth?: string;
  address_line1?: string;
  address_line2?: string;
  city?: string;
  state?: string;
  postal_code?: string;
  country?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relationship?: string;
  notification_preferences?: Record<string, boolean>;
  marketing_consent?: boolean;
  data_processing_consent?: boolean;
}

export interface PatientDashboardNotification {
  message: string;
  level: string;
  created_at: string;
}

export interface PatientDashboardSummary {
  profile: PatientProfile;
  upcoming_appointments: PatientAppointment[];
  pending_payments: number;
  unread_messages: number;
  recent_documents: DocumentResponse[];
  recent_prescriptions: ElectronicPrescriptionResponse[];
  notifications: PatientDashboardNotification[];
}

// API Functions
export const getPatientAppointments = async (page = 1, page_size = 10) => {
  const response = await axios.get(`${API_URL}/api/v1/patients/appointments`, {
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
  const response = await axios.post(`${API_URL}/api/v1/patients/appointments`, data, {
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
  const response = await axios.patch(`${API_URL}/api/v1/patients/appointments/${appointmentId}`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const cancelPatientAppointment = async (appointmentId: number) => {
  const response = await axios.delete(`${API_URL}/api/v1/patients/appointments/${appointmentId}`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const createDoctorReview = async (data: DoctorReviewCreate) => {
  const response = await axios.post(`${API_URL}/api/v1/patients/reviews`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getPatientMedicalRecords = async () => {
  const response = await axios.get(`${API_URL}/api/v1/patients/medical-records`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getPatientPayments = async (page = 1, page_size = 10) => {
  const response = await axios.get(`${API_URL}/api/v1/patients/payments`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const searchDoctorsForPatient = async (params: {
  specialty?: string;
  city?: string;
  language?: string;
  min_price?: number;
  max_price?: number;
  search?: string;
  page?: number;
  page_size?: number;
}): Promise<DoctorSearchResponse> => {
  const response = await axios.post(`${API_URL}/api/v1/patients/search-doctors`, params, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getPatientMessages = async (page = 1, page_size = 10): Promise<PatientMessageList> => {
  const response = await axios.get(`${API_URL}/api/v1/patients/messages`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const markMessageAsRead = async (messageId: number): Promise<void> => {
  await axios.patch(
    `${API_URL}/api/v1/patients/messages/${messageId}/read`,
    {},
    {
      headers: getAuthHeaders(),
    }
  );
};

export const getPatientProfile = async (): Promise<PatientProfile> => {
  const response = await axios.get(`${API_URL}/api/v1/patients/me`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const updatePatientProfile = async (
  data: PatientProfileUpdatePayload
): Promise<PatientProfile> => {
  const response = await axios.patch(`${API_URL}/api/v1/patients/me`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getPatientDashboard = async (): Promise<PatientDashboardSummary> => {
  const response = await axios.get(`${API_URL}/api/v1/patients/dashboard`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};