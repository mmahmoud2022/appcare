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

// Types
export type ConsultationType = 'in_person' | 'teleconsultation' | 'both';

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

// API Functions
export const getDoctorSchedule = async (doctorId: number) => {
  const response = await axios.get(`${API_URL}/api/v1/doctors/${doctorId}/schedule`, {
    headers: getAuthHeaders(),
  });
  return response.data;
};
