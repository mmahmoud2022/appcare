"""
Schémas Pydantic pour le module Patient
"""
from __future__ import annotations

import json
from datetime import datetime, date
from typing import List, Optional, Dict

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.doctor import (
    AppointmentStatusEnum,
    ConsultationTypeEnum,
    PaymentStatusEnum,
)

from app.schemas.doctor import (
    AppointmentUpdate,
    AppointmentCreate,
    DocumentResponse,
    ElectronicPrescriptionResponse,
    MessageResponse,
    PaymentResponse,
)


class PatientProfileBase(BaseModel):
    """Champs communs pour le profil patient"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    gender: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    state: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    emergency_contact_name: Optional[str] = Field(None, max_length=200)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=100)
    notification_preferences: Optional[Dict[str, bool]] = None
    marketing_consent: Optional[bool] = None
    data_processing_consent: Optional[bool] = None


class PatientProfileUpdate(PatientProfileBase):
    """Mise à jour du profil patient"""
    pass


class PatientProfileResponse(PatientProfileBase):
    """Représentation du profil patient"""
    id: int
    email: EmailStr
    created_at: datetime
    updated_at: Optional[datetime]
    terms_accepted_at: Optional[datetime]

    class Config:
        from_attributes = True

    @validator("notification_preferences", pre=True)
    def _deserialize_preferences(cls, value):
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return {}
        return value or {}


class PatientNotification(BaseModel):
    """Notification à afficher dans le tableau de bord"""
    message: str
    level: str = Field(default="info", description="info | warning | success | alert")
    created_at: datetime


class PatientAppointmentSummary(BaseModel):
    """Résumé d'un rendez-vous pour le tableau de bord"""
    id: int
    doctor_id: int
    doctor_first_name: Optional[str]
    doctor_last_name: Optional[str]
    doctor_specialty: Optional[str]
    appointment_date: datetime
    consultation_type: ConsultationTypeEnum
    status: AppointmentStatusEnum
    reason: Optional[str]
    is_teleconsultation: bool = False
    meet_link: Optional[str] = None
    schedule_entry_id: Optional[int] = None


class PatientAppointmentResponse(PatientAppointmentSummary):
    """Réponse détaillée pour les rendez-vous"""
    patient_notes: Optional[str]
    doctor_notes: Optional[str]
    duration: int
    price: Optional[float]


class PatientAppointmentListResponse(BaseModel):
    """Liste paginée de rendez-vous"""
    total: int
    page: int
    page_size: int
    items: List[PatientAppointmentResponse]


class PatientAppointmentCreate(AppointmentCreate):
    """Création d'un rendez-vous patient"""
    pass


class PatientAppointmentUpdate(AppointmentUpdate):
    """Mise à jour d'un rendez-vous patient"""
    pass


class PatientMedicalRecordResponse(BaseModel):
    """Dossier médical patient"""
    appointments: List[PatientAppointmentResponse]
    documents: List[DocumentResponse]
    prescriptions: List[ElectronicPrescriptionResponse]


class PatientPaymentHistory(BaseModel):
    """Historique paginé des paiements"""
    total: int
    page: int
    page_size: int
    items: List[PaymentResponse]


class PatientMessageList(BaseModel):
    """Liste paginée des messages patient"""
    total: int
    page: int
    page_size: int
    items: List[MessageResponse]


class PatientDashboardSummary(BaseModel):
    """Résumé global pour le tableau de bord patient"""
    profile: PatientProfileResponse
    upcoming_appointments: List[PatientAppointmentSummary]
    pending_payments: int
    unread_messages: int
    recent_documents: List[DocumentResponse]
    recent_prescriptions: List[ElectronicPrescriptionResponse]
    notifications: List[PatientNotification]


class DoctorSearchRequest(BaseModel):
    """Filtres de recherche de praticiens"""
    specialty: Optional[str] = None
    city: Optional[str] = None
    language: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    search: Optional[str] = Field(None, max_length=100)


class DoctorSearchResult(BaseModel):
    """Résultat d'un praticien pour la recherche patient"""
    doctor_id: int
    first_name: str
    last_name: str
    specialty: str
    city: Optional[str]
    consultation_types: ConsultationTypeEnum
    consultation_duration: int
    consultation_price: Optional[float]
    average_rating: float
    total_reviews: int
    languages: List[str]
    accepts_new_patients: bool

    class Config:
        from_attributes = True


class DoctorSearchResponse(BaseModel):
    """Réponse paginée pour la recherche de praticiens"""
    total: int
    page: int
    page_size: int
    items: List[DoctorSearchResult]


class DoctorReviewCreate(BaseModel):
    """Création d'un avis patient sur un médecin"""
    doctor_id: int = Field(..., description="ID du médecin à noter")
    appointment_id: Optional[int] = Field(None, description="ID du rendez-vous lié")
    rating: int = Field(..., ge=1, le=5, description="Note de 1 à 5 étoiles")
    comment: Optional[str] = Field(None, max_length=1000, description="Commentaire facultatif")
    is_public: bool = Field(True, description="Rendre l'avis public")


class DoctorReviewResponse(BaseModel):
    """Réponse avec les détails d'un avis"""
    id: int
    doctor_id: int
    patient_id: int
    appointment_id: Optional[int]
    rating: int
    comment: Optional[str]
    doctor_response: Optional[str]
    responded_at: Optional[datetime]
    is_public: bool
    is_verified: bool
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True
