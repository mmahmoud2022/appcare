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
export type PrescriptionStatus = 'issued' | 'cancelled' | 'delivered';

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
  appointment_id?: number;
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
  paid_at?: string;
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
  user?: {
    id: number;
    email: string;
    first_name?: string;
    last_name?: string;
  };
}

export interface PatientInfo {
  id: number;
  email: string;
  full_name: string;
  phone?: string;
  first_name?: string;
  last_name?: string;
  date_of_birth?: string;
  total_appointments?: number;
  last_appointment_date?: string;
}

export interface PatientBasicInfo {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  date_of_birth?: string;
  total_appointments: number;
  last_appointment_date?: string;
  full_name?: string;
}

export interface Appointment {
  id: number;
  doctor_id: number;
  patient_id: number;
  appointment_date: string;
  consultation_type: ConsultationType;
  reason?: string;
  status: AppointmentStatus;
  duration: number;
  price?: number;
  is_paid: boolean;
  patient_notes?: string;
  doctor_notes?: string;
  notes?: string;
  diagnosis?: string;
  prescription?: string;
  meet_link?: string;
  created_at: string;
  updated_at?: string;
  cancelled_at?: string;
  completed_at?: string;
  schedule_entry_id?: number;
  patient?: PatientInfo;
  patient_first_name?: string;
  patient_last_name?: string;
  patient_phone?: string;
  doctor_first_name?: string;
  doctor_last_name?: string;
}

export interface DoctorStatistics {
  total_consultations: number;
  completed_consultations: number;
  cancelled_consultations: number;
  no_show_consultations: number;
  cancellation_rate: number;
  average_rating: number;
  total_reviews: number;
  new_patients_count: number;
  returning_patients_count: number;
  total_revenue: number;
  pending_revenue: number;
  upcoming_appointments: number;
  today_appointments: number;
}

export interface PrescriptionMedication {
  name: string;
  dosage?: string;
  frequency?: string;
  duration?: string;
  notes?: string;
}

export interface ElectronicPrescription {
  id: number;
  doctor_id: number;
  patient_id: number;
  appointment_id?: number;
  prescription_number: string;
  medications: PrescriptionMedication[];
  instructions?: string;
  status: PrescriptionStatus;
  issued_at: string;
  expires_at?: string;
  delivered_at?: string;
  created_at: string;
  updated_at?: string;
  patient_first_name?: string;
  patient_last_name?: string;
}

export interface ElectronicPrescriptionCreate {
  patient_id: number;
  appointment_id?: number;
  medications: PrescriptionMedication[];
  instructions?: string;
  expires_at?: string;
}

export interface DocumentUpload {
  patient_id: number;
  title: string;
  description?: string;
  document_type?: string;
  appointment_id?: number;
  file: File;
}

export interface PatientListResponse {
  total: number;
  page: number;
  page_size: number;
  items: PatientBasicInfo[];
}

export interface ElectronicPrescriptionListResponse {
  total: number;
  page: number;
  page_size: number;
  items: ElectronicPrescription[];
}

export interface ScheduleEntryCreate {
  day_of_week: number;
  start_time: string;
  end_time: string;
  slot_duration: number;
  break_duration: number;
  consultation_type: ConsultationType;
  location?: string;
}

export interface ScheduleEntryUpdate {
  day_of_week?: number;
  start_time?: string;
  end_time?: string;
  slot_duration?: number;
  break_duration?: number;
  consultation_type?: ConsultationType;
  location?: string;
}

export interface BlockedSlot {
  id: number;
  doctor_id: number;
  start_datetime: string;
  end_datetime: string;
  reason?: string;
  created_at: string;
}

export interface BlockedSlotCreate {
  start_datetime: string;
  end_datetime: string;
  reason?: string;
}

export interface AppointmentStatusUpdate {
  status: AppointmentStatus;
  notes?: string;
  diagnosis?: string;
  prescription?: string;
}

export interface DoctorReview {
  id: number;
  doctor_id: number;
  patient_id: number;
  appointment_id?: number;
  rating: number;
  comment?: string;
  doctor_response?: string;
  responded_at?: string;
  is_public: boolean;
  created_at: string;
  patient_first_name: string;
  patient_last_name: string;
}

export interface ReviewResponseCreate {
  response: string;
}

export interface DoctorSettings {
  id: number;
  doctor_id: number;
  email_notifications: boolean;
  sms_notifications: boolean;
  appointment_reminders: boolean;
  profile_visibility: string;
  show_phone: boolean;
  show_email: boolean;
  language: string;
  timezone: string;
  payment_enabled: boolean;
  payment_methods: string[];
  created_at: string;
  updated_at?: string;
}

export interface DoctorSettingsUpdate {
  email_notifications?: boolean;
  sms_notifications?: boolean;
  appointment_reminders?: boolean;
  profile_visibility?: string;
  show_phone?: boolean;
  show_email?: boolean;
  language?: string;
  timezone?: string;
  payment_enabled?: boolean;
  payment_methods?: string[];
}

export interface DoctorProfileUpdate {
  specialty?: Specialty;
  sub_specialty?: string;
  rpps_number?: string;
  office_address?: string;
  office_city?: string;
  office_postal_code?: string;
  office_phone?: string;
  biography?: string;
  languages?: string[];
  education?: any[];
  experience_years?: number;
  consultation_types?: ConsultationType;
  consultation_duration?: number;
  consultation_price?: number;
  accepts_new_patients?: boolean;
  is_public?: boolean;
}

export interface MedicalRecord {
  appointments: Appointment[];
  documents: any[];
  prescriptions: ElectronicPrescription[];
  total_consultations?: number;
}

export interface MessageCreate {
  recipient_id: number;
  subject?: string;
  content: string;
  appointment_id?: number;
}

// API Functions
export const getDoctorSchedule = async (doctorId: number) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/${doctorId}/schedule`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

/**
 * Récupère les créneaux RÉELLEMENT disponibles d'un médecin
 * Cette API croise automatiquement:
 * - Les horaires récurrents
 * - Les slots bloqués
 * - Les rendez-vous déjà réservés
 * 
 * @param doctorId - ID du médecin
 * @param startDate - Date de début (format YYYY-MM-DD)
 * @param endDate - Date de fin (format YYYY-MM-DD) 
 * @param consultationType - Optionnel: filtrer par type (IN_PERSON, TELECONSULTATION)
 */
export interface AvailableSlot {
  id: string;
  doctor_id: number;
  start_time: string;
  end_time: string;
  consultation_types: ConsultationType[];
  is_available: boolean;
  schedule_entry_id: number;
  location?: string;
}

export const getDoctorAvailableSlots = async (
  doctorId: number,
  startDate: string,
  endDate: string,
  consultationType?: ConsultationType
): Promise<AvailableSlot[]> => {
  const params: any = {
    start_date: startDate,
    end_date: endDate,
  };
  
  if (consultationType) {
    params.consultation_type = consultationType;
  }
  
  const response = await axios.get(`${API_URL}/api/v1/doctors/${doctorId}/available-slots`, {
    headers: getAuthHeaders(),
    params,
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

// Alias for compatibility
export const getCurrentDoctorProfile = getMyDoctorProfile;

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

export const getDoctorPayments = async (page = 1, page_size = 10, status?: PaymentStatus) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/payments`, {
    params: { page, page_size, status },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getDoctorStatistics = async (): Promise<DoctorStatistics> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/statistics`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getMyPatients = async (
  page = 1,
  page_size = 50
): Promise<PatientListResponse> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/patients`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const uploadPatientDocument = async (
  data: DocumentUpload
): Promise<any> => {
  const formData = new FormData();
  formData.append('patient_id', data.patient_id.toString());
  formData.append('title', data.title);
  if (data.description) formData.append('description', data.description);
  if (data.document_type) formData.append('document_type', data.document_type);
  if (data.appointment_id) formData.append('appointment_id', data.appointment_id.toString());
  formData.append('file', data.file);

  const response = await axios.post(
    `${API_URL}/api/v1/doctors/documents`,
    formData,
    {
      headers: {
        Authorization: `Bearer ${getToken()}`,
        // Don't set Content-Type, let browser set it with boundary
      },
    }
  );
  return response.data;
};

export const getDoctorPrescriptions = async (
  patient_id?: number,
  page = 1,
  page_size = 50
): Promise<ElectronicPrescriptionListResponse> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/prescriptions`, {
    params: { patient_id, page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const issueElectronicPrescription = async (
  data: ElectronicPrescriptionCreate
): Promise<ElectronicPrescription> => {
  const response = await axios.post(
    `${API_URL}/api/v1/doctors/prescriptions`,
    data,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const createScheduleEntry = async (
  data: ScheduleEntryCreate
): Promise<DoctorScheduleEntry> => {
  const response = await axios.post(
    `${API_URL}/api/v1/doctors/schedule`,
    data,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const updateScheduleEntry = async (
  scheduleEntryId: number,
  data: ScheduleEntryUpdate
): Promise<DoctorScheduleEntry> => {
  const response = await axios.patch(
    `${API_URL}/api/v1/doctors/schedule/${scheduleEntryId}`,
    data,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const deleteScheduleEntry = async (
  scheduleEntryId: number
): Promise<void> => {
  await axios.delete(
    `${API_URL}/api/v1/doctors/schedule/${scheduleEntryId}`,
    {
      headers: getAuthHeaders(),
    }
  );
};

export const getBlockedSlots = async (
  start?: string,
  end?: string
): Promise<BlockedSlot[]> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/me/blocked-slots`, {
    params: { start, end },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const createBlockedSlot = async (
  data: BlockedSlotCreate
): Promise<BlockedSlot> => {
  const response = await axios.post(
    `${API_URL}/api/v1/doctors/me/blocked-slots`,
    data,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const deleteBlockedSlot = async (
  slotId: number
): Promise<void> => {
  await axios.delete(
    `${API_URL}/api/v1/doctors/me/blocked-slots/${slotId}`,
    {
      headers: getAuthHeaders(),
    }
  );
};

export const updateAppointmentStatus = async (
  appointmentId: number,
  data: AppointmentStatusUpdate
): Promise<Appointment> => {
  const response = await axios.patch(
    `${API_URL}/api/v1/doctors/appointments/${appointmentId}/status`,
    data,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const deleteAppointment = async (
  appointmentId: number
): Promise<void> => {
  await axios.delete(
    `${API_URL}/api/v1/doctors/appointments/${appointmentId}`,
    {
      headers: getAuthHeaders(),
    }
  );
};

export const getPatientMedicalRecord = async (
  patientId: number
): Promise<MedicalRecord> => {
  const response = await axios.get(
    `${API_URL}/api/v1/doctors/patients/${patientId}`,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const deletePatient = async (patientId: number): Promise<void> => {
  await axios.delete(`${API_URL}/api/v1/doctors/patients/${patientId}`, {
    headers: getAuthHeaders(),
  });
};

export const getMyReviews = async (
  page = 1,
  page_size = 50
): Promise<{ total: number; page: number; page_size: number; items: DoctorReview[] }> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/reviews`, {
    params: { page, page_size },
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const respondToReview = async (
  reviewId: number,
  data: ReviewResponseCreate | string
): Promise<DoctorReview> => {
  const payload = typeof data === 'string' ? { response: data } : data;
  const response = await axios.post(
    `${API_URL}/api/v1/doctors/reviews/${reviewId}/response`,
    payload,
    {
      headers: getAuthHeaders(),
    }
  );
  return response.data;
};

export const sendMessage = async (data: MessageCreate): Promise<DoctorMessage> => {
  const response = await axios.post(`${API_URL}/api/v1/doctors/messages`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const updateDoctorProfile = async (
  data: DoctorProfileUpdate
): Promise<DoctorProfile> => {
  const response = await axios.patch(`${API_URL}/api/v1/doctors/me`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const getMySettings = async (): Promise<DoctorSettings> => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/settings`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};

export const updateMySettings = async (
  data: DoctorSettingsUpdate
): Promise<DoctorSettings> => {
  const response = await axios.put(`${API_URL}/api/v1/doctors/settings`, data, {
    headers: getAuthHeaders(),
  });
  return response.data;
};