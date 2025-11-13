"""
Schémas Pydantic pour le module Doctor
"""
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict
from datetime import datetime, date, time
from app.models.doctor import (
    SpecialtyEnum,
    ConsultationTypeEnum,
    AppointmentStatusEnum,
    PaymentStatusEnum,
    PrescriptionStatusEnum,
)


# ========== Doctor Profile Schemas ==========

class DoctorProfileBase(BaseModel):
    """Base schema pour le profil médecin"""
    specialty: SpecialtyEnum
    sub_specialty: Optional[str] = None
    rpps_number: Optional[str] = Field(None, min_length=11, max_length=11, description="Numéro RPPS (11 chiffres) - optionnel")
    
    office_address: Optional[str] = None
    office_city: Optional[str] = None
    office_postal_code: Optional[str] = None
    office_phone: Optional[str] = None
    
    biography: Optional[str] = Field(None, max_length=2000)
    languages: List[str] = Field(default_factory=list)
    education: List[Dict] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    
    consultation_types: ConsultationTypeEnum = ConsultationTypeEnum.BOTH
    consultation_duration: int = Field(default=30, ge=15, le=180)
    consultation_price: Optional[float] = Field(None, ge=0)
    accepts_new_patients: bool = True
    is_public: bool = True


class DoctorProfileCreate(DoctorProfileBase):
    """Schema pour la création d'un profil médecin"""
    pass


class DoctorProfileUpdate(BaseModel):
    """Schema pour la mise à jour d'un profil médecin"""
    specialty: Optional[SpecialtyEnum] = None
    sub_specialty: Optional[str] = None
    office_address: Optional[str] = None
    office_city: Optional[str] = None
    office_postal_code: Optional[str] = None
    office_phone: Optional[str] = None
    biography: Optional[str] = None
    languages: Optional[List[str]] = None
    education: Optional[List[Dict]] = None
    experience_years: Optional[int] = None
    consultation_types: Optional[ConsultationTypeEnum] = None
    consultation_duration: Optional[int] = Field(None, ge=15, le=180)
    consultation_price: Optional[float] = Field(None, ge=0)
    accepts_new_patients: Optional[bool] = None
    is_public: Optional[bool] = None


class DoctorProfileResponse(DoctorProfileBase):
    """Schema de réponse pour un profil médecin complet"""
    id: int
    user_id: int
    is_verified: bool
    total_consultations: int
    average_rating: float
    total_reviews: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    # Informations utilisateur
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True


class DoctorPublicProfile(BaseModel):
    """Schema pour le profil public d'un médecin (accessible par les patients)"""
    id: int
    specialty: SpecialtyEnum
    sub_specialty: Optional[str]
    office_city: Optional[str]
    biography: Optional[str]
    languages: List[str]
    experience_years: int
    consultation_types: ConsultationTypeEnum
    consultation_duration: int
    consultation_price: Optional[float]
    accepts_new_patients: bool
    average_rating: float
    total_reviews: int
    total_consultations: int
    
    # Informations utilisateur publiques
    first_name: str
    last_name: str
    
    class Config:
        from_attributes = True


# ========== Planning/Schedule Schemas ========== 

class ScheduleEntryBase(BaseModel):
    """Configuration hebdomadaire d'un planning médecin"""
    day_of_week: int = Field(
        ..., ge=0, le=6,
        description="Jour de la semaine (0=Dimanche, 1=Lundi, ..., 6=Samedi)"
    )
    start_time: time
    end_time: time
    slot_duration: int = Field(..., gt=0, description="Durée d'un rendez-vous en minutes")
    break_duration: int = Field(0, ge=0, description="Durée de la pause entre deux créneaux en minutes")
    consultation_type: ConsultationTypeEnum
    location: Optional[str] = Field(None, max_length=255)

    @validator("end_time")
    def validate_time_range(cls, value, values):
        if "start_time" in values and value <= values["start_time"]:
            raise ValueError("L'heure de fin doit être après l'heure de début")
        return value


class ScheduleEntryCreate(ScheduleEntryBase):
    """Création d'une configuration de planning"""
    pass


class ScheduleEntryResponse(ScheduleEntryBase):
    """Réponse pour une configuration de planning"""
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduleEntryUpdate(BaseModel):
    """Mise à jour d'une configuration de planning"""
    day_of_week: Optional[int] = Field(None, ge=0, le=6)
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    consultation_type: Optional[ConsultationTypeEnum] = None
    slot_duration: Optional[int] = Field(None, gt=0)
    break_duration: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=255)

    @validator("end_time")
    def validate_time_range(cls, value, values):
        start_time = values.get("start_time")
        if value is not None and start_time is not None and value <= start_time:
            raise ValueError("L'heure de fin doit être après l'heure de début")
        return value

    class Config:
        from_attributes = True


class DoctorAvailabilitySlot(BaseModel):
    """Slot disponible calculé dynamiquement"""
    schedule_entry_id: int
    start: datetime
    end: datetime
    consultation_type: ConsultationTypeEnum
    location: Optional[str] = None

    class Config:
        from_attributes = True


class BlockedSlotBase(BaseModel):
    """Base schema pour une indisponibilité ponctuelle"""
    start_datetime: datetime
    end_datetime: datetime
    reason: Optional[str] = Field(None, max_length=255)

    @validator('end_datetime')
    def validate_block_range(cls, v, values):
        start = values.get('start_datetime')
        if start and v <= start:
            raise ValueError("La fin doit être postérieure au début")
        return v


class BlockedSlotCreate(BlockedSlotBase):
    """Création d'une indisponibilité ponctuelle"""
    pass


class BlockedSlotResponse(BlockedSlotBase):
    """Réponse pour une indisponibilité ponctuelle"""
    id: int
    doctor_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ========== Appointment Schemas ==========

class PatientInfo(BaseModel):
    """Schema pour les informations du patient"""
    id: int
    email: str
    full_name: str
    phone: Optional[str] = None

    class Config:
        from_attributes = True


class AppointmentBase(BaseModel):
    """Base schema pour les rendez-vous"""
    appointment_date: datetime
    consultation_type: ConsultationTypeEnum
    reason: Optional[str] = None
    patient_notes: Optional[str] = None


class AppointmentCreate(AppointmentBase):
    """Schema pour la création d'un rendez-vous (par le patient)"""
    doctor_id: int
    schedule_entry_id: Optional[int] = None


class AppointmentUpdate(BaseModel):
    """Schema pour la mise à jour d'un rendez-vous"""
    appointment_date: Optional[datetime] = None
    consultation_type: Optional[ConsultationTypeEnum] = None
    reason: Optional[str] = None
    patient_notes: Optional[str] = None
    doctor_notes: Optional[str] = None


class AppointmentStatusUpdate(BaseModel):
    """Schema pour la mise à jour du statut d'un rendez-vous"""
    status: AppointmentStatusEnum
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None


class AppointmentResponse(AppointmentBase):
    """Schema de réponse pour un rendez-vous"""
    id: int
    doctor_id: int
    patient_id: int
    status: AppointmentStatusEnum
    duration: int
    price: Optional[float]
    is_paid: bool
    doctor_notes: Optional[str]
    notes: Optional[str]
    diagnosis: Optional[str]
    prescription: Optional[str]
    meet_link: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    completed_at: Optional[datetime]
    schedule_entry_id: Optional[int] = None
    
    # Informations patient (pour le médecin)
    patient: Optional[PatientInfo] = None
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None
    patient_phone: Optional[str] = None
    
    # Informations médecin (pour le patient)
    doctor_first_name: Optional[str] = None
    doctor_last_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== Review Schemas ==========

class ReviewBase(BaseModel):
    """Base schema pour les avis"""
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewCreate(ReviewBase):
    """Schema pour la création d'un avis (par le patient)"""
    doctor_id: int
    appointment_id: Optional[int] = None


class ReviewResponse(ReviewBase):
    """Schema de réponse pour un avis"""
    id: int
    doctor_id: int
    patient_id: int
    doctor_response: Optional[str]
    responded_at: Optional[datetime]
    is_public: bool
    created_at: datetime
    
    # Informations patient
    patient_first_name: str
    patient_last_name: str

    class Config:
        from_attributes = True


class ReviewResponseCreate(BaseModel):
    """Schema pour la réponse d'un médecin à un avis"""
    response: str = Field(..., max_length=1000)


# ========== Message Schemas ==========

class MessageBase(BaseModel):
    """Base schema pour les messages"""
    subject: Optional[str] = Field(None, max_length=255)
    content: str = Field(..., min_length=1, max_length=5000)


class MessageCreate(MessageBase):
    """Schema pour la création d'un message"""
    recipient_id: int
    appointment_id: Optional[int] = None


class MessageResponse(MessageBase):
    """Schema de réponse pour un message"""
    id: int
    sender_id: int
    recipient_id: int
    is_read: bool
    read_at: Optional[datetime]
    created_at: datetime
    
    # Informations expéditeur
    sender_first_name: str
    sender_last_name: str
    
    # Informations destinataire
    recipient_first_name: str
    recipient_last_name: str

    class Config:
        from_attributes = True


# ========== Payment Schemas ==========

class PaymentBase(BaseModel):
    """Base schema pour les paiements"""
    amount: float = Field(..., gt=0)
    currency: str = Field(default="EUR", max_length=3)
    payment_method: Optional[str] = None


class PaymentCreate(PaymentBase):
    """Schema pour la création d'un paiement"""
    appointment_id: int


class PaymentResponse(PaymentBase):
    """Schema de réponse pour un paiement"""
    id: int
    doctor_id: int
    patient_id: int
    appointment_id: Optional[int]
    status: PaymentStatusEnum
    transaction_id: Optional[str]
    created_at: datetime
    paid_at: Optional[datetime]
    
    # Informations patient
    patient_first_name: str
    patient_last_name: str

    class Config:
        from_attributes = True


# ========== Document Schemas ==========

class DocumentBase(BaseModel):
    """Base schema pour les documents"""
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    document_type: Optional[str] = None


class DocumentCreate(DocumentBase):
    """Schema pour la création d'un document"""
    patient_id: int
    appointment_id: Optional[int] = None


class DocumentResponse(DocumentBase):
    """Schema de réponse pour un document"""
    id: int
    doctor_id: int
    patient_id: int
    file_name: str
    file_size: Optional[int]
    mime_type: Optional[str]
    is_patient_visible: bool
    created_at: datetime
    
    # Informations patient (optionnelles, enrichies selon le contexte)
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== Prescription Schemas ==========

class PrescriptionMedication(BaseModel):
    """Détail d'un médicament prescrit"""
    name: str = Field(..., max_length=255)
    dosage: Optional[str] = Field(None, max_length=255)
    frequency: Optional[str] = Field(None, max_length=255)
    duration: Optional[str] = Field(None, max_length=255)
    notes: Optional[str] = Field(None, max_length=500)

    @validator('name')
    def validate_name(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("Le nom du médicament est requis")
        return value.strip()


class ElectronicPrescriptionBase(BaseModel):
    """Base schema pour une ordonnance électronique"""
    patient_id: int
    appointment_id: Optional[int] = None
    medications: List[PrescriptionMedication]
    instructions: Optional[str] = Field(None, max_length=2000)
    expires_at: Optional[datetime] = None

    @validator('medications')
    def validate_medications(cls, value: List[PrescriptionMedication]) -> List[PrescriptionMedication]:
        if not value:
            raise ValueError("Au moins un médicament est requis")
        return value


class ElectronicPrescriptionCreate(ElectronicPrescriptionBase):
    """Schema pour l'émission d'une ordonnance"""
    pass


class ElectronicPrescriptionResponse(BaseModel):
    """Schema de réponse pour une ordonnance"""
    id: int
    doctor_id: int
    patient_id: int
    appointment_id: Optional[int]
    prescription_number: str
    medications: List[PrescriptionMedication]
    instructions: Optional[str]
    status: PrescriptionStatusEnum
    issued_at: datetime
    expires_at: Optional[datetime]
    delivered_at: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    # Informations patient
    patient_first_name: Optional[str] = None
    patient_last_name: Optional[str] = None

    class Config:
        from_attributes = True


# ========== Settings Schemas ==========

class DoctorSettingsUpdate(BaseModel):
    """Schema pour la mise à jour des paramètres"""
    email_notifications: Optional[bool] = None
    sms_notifications: Optional[bool] = None
    appointment_reminders: Optional[bool] = None
    profile_visibility: Optional[str] = Field(None, pattern="^(public|private|restricted)$")
    show_phone: Optional[bool] = None
    show_email: Optional[bool] = None
    language: Optional[str] = Field(None, max_length=5)
    timezone: Optional[str] = Field(None, max_length=50)
    payment_enabled: Optional[bool] = None
    payment_methods: Optional[List[str]] = None


class DoctorSettingsResponse(BaseModel):
    """Schema de réponse pour les paramètres"""
    id: int
    doctor_id: int
    email_notifications: bool
    sms_notifications: bool
    appointment_reminders: bool
    profile_visibility: str
    show_phone: bool
    show_email: bool
    language: str
    timezone: str
    payment_enabled: bool
    payment_methods: List[str]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ========== Statistics Schemas ==========

class DoctorStatistics(BaseModel):
    """Schema pour les statistiques du médecin"""
    total_consultations: int
    completed_consultations: int
    cancelled_consultations: int
    no_show_consultations: int
    cancellation_rate: float
    average_rating: float
    total_reviews: int
    new_patients_count: int
    returning_patients_count: int
    total_revenue: float
    pending_revenue: float
    upcoming_appointments: int
    today_appointments: int


# ========== Patient List Schemas ==========

class PatientBasicInfo(BaseModel):
    """Schema pour les informations de base d'un patient"""
    id: int
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    date_of_birth: Optional[datetime]
    total_appointments: int
    last_appointment_date: Optional[datetime]

    class Config:
        from_attributes = True


# ========== List Response Schemas ==========

class PaginatedResponse(BaseModel):
    """Schema générique pour les réponses paginées"""
    total: int
    page: int
    page_size: int
    items: List


class ScheduleEntryListResponse(PaginatedResponse):
    """Réponse paginée pour les configurations de planning"""
    items: List[ScheduleEntryResponse]


class AppointmentListResponse(PaginatedResponse):
    """Réponse paginée pour les rendez-vous"""
    items: List[AppointmentResponse]


class MessageListResponse(PaginatedResponse):
    """Réponse paginée pour les messages"""
    items: List[MessageResponse]


class PaymentListResponse(PaginatedResponse):
    """Réponse paginée pour les paiements"""
    items: List[PaymentResponse]


class ReviewListResponse(PaginatedResponse):
    """Réponse paginée pour les avis"""
    items: List[ReviewResponse]


class PatientListResponse(PaginatedResponse):
    """Réponse paginée pour les patients"""
    items: List[PatientBasicInfo]


class ElectronicPrescriptionListResponse(PaginatedResponse):
    """Réponse paginée pour les ordonnances"""
    items: List[ElectronicPrescriptionResponse]
