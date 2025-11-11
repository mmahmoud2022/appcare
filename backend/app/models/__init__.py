"""
Models package
"""
from app.models.user import User, UserRole
from app.models.auth import VerificationToken, RefreshToken, LoginAttempt
from app.models.doctor import (
    DoctorProfile,
    DoctorScheduleEntry,
    DoctorBlockedSlot,
    Appointment,
    DoctorReview,
    DoctorMessage,
    Payment,
    PatientDocument,
    DoctorSettings,
    ElectronicPrescription,
    SpecialtyEnum,
    ConsultationTypeEnum,
    AppointmentStatusEnum,
    PaymentStatusEnum,
    PrescriptionStatusEnum,
)

__all__ = [
    "User",
    "UserRole",
    "VerificationToken",
    "RefreshToken",
    "LoginAttempt",
    "DoctorProfile",
    "DoctorScheduleEntry",
    "DoctorBlockedSlot",
    "Appointment",
    "DoctorReview",
    "DoctorMessage",
    "Payment",
    "PatientDocument",
    "DoctorSettings",
    "ElectronicPrescription",
    "SpecialtyEnum",
    "ConsultationTypeEnum",
    "AppointmentStatusEnum",
    "PaymentStatusEnum",
    "PrescriptionStatusEnum",
]
