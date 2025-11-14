"""
Service pour la gestion des fonctionnalités patient
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, date, time, timezone
import unicodedata
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, desc, cast, String
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from app.models.user import User, UserRole
from app.models.doctor import (
    DoctorProfile,
    DoctorScheduleEntry,
    DoctorBlockedSlot,
    Appointment,
    AppointmentStatusEnum,
    ConsultationTypeEnum,
    DoctorMessage,
    Payment,
    PaymentStatusEnum,
    ElectronicPrescription,
    PatientDocument,
    SpecialtyEnum,
    DoctorReview,
)
from app.schemas.patient import (
    DoctorSearchRequest,
    DoctorSearchResponse,
    DoctorSearchResult,
    PatientAppointmentCreate,
    PatientAppointmentListResponse,
    PatientAppointmentResponse,
    PatientAppointmentSummary,
    PatientAppointmentUpdate,
    PatientDashboardSummary,
    PatientMedicalRecordResponse,
    PatientMessageList,
    PatientNotification,
    PatientPaymentHistory,
    PatientProfileResponse,
    PatientProfileUpdate,
    DoctorReviewCreate,
)
from app.schemas.doctor import (
    DocumentResponse,
    ElectronicPrescriptionResponse,
    MessageCreate,
    MessageResponse,
    PaymentResponse,
    DoctorAvailabilitySlot,
)
from app.services.doctor_service import DoctorService
from app.services.teleconsultation_service import TeleconsultationService


SPECIALTY_ALIASES: Dict[str, SpecialtyEnum] = {}


def _normalize_text(value: Optional[str]) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return " ".join(stripped.lower().strip().split())


class PatientService:
    """Service pour la gestion des fonctionnalités patient."""

    @staticmethod
    def _normalize_datetime_to_minute(value: datetime) -> datetime:
        return value.replace(second=0, microsecond=0)

    @staticmethod
    def _find_slot_for_datetime(
        db: Session,
        doctor_id: int,
        appointment_datetime: datetime
    ) -> DoctorAvailabilitySlot:
        """Retrouve le slot correspondant à une date donnée ou lève une erreur."""
        normalized = PatientService._normalize_datetime_to_minute(appointment_datetime)
        slots = DoctorService.get_doctor_availability_slots(db, doctor_id, normalized.date())
        for slot in slots:
            if PatientService._normalize_datetime_to_minute(slot.start) == normalized:
                return slot
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ce créneau n'est plus disponible"
        )

    @staticmethod
    def _resolve_consultation_type(
        doctor: DoctorProfile,
        slot: DoctorAvailabilitySlot,
        requested_type: ConsultationTypeEnum
    ) -> ConsultationTypeEnum:
        """Valide et détermine le type de consultation final."""
        entry_type = slot.consultation_type
        final_type = requested_type
        if entry_type != ConsultationTypeEnum.BOTH and entry_type != requested_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce type de consultation n'est pas disponible pour ce créneau"
            )
        if entry_type == ConsultationTypeEnum.BOTH:
            final_type = requested_type

        doctor_type = doctor.consultation_types or ConsultationTypeEnum.BOTH
        if doctor_type != ConsultationTypeEnum.BOTH and doctor_type != final_type:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Le praticien n'accepte pas ce type de consultation"
            )
        return final_type

    @staticmethod
    def _slot_belongs_to_entry(entry: DoctorScheduleEntry, slot_start: datetime) -> bool:
        """Vérifie que le créneau appartient toujours à la configuration fournie."""
        entry_start = datetime.combine(slot_start.date(), entry.start_time, tzinfo=timezone.utc)
        entry_end = datetime.combine(slot_start.date(), entry.end_time, tzinfo=timezone.utc)
        slot_delta = timedelta(minutes=entry.slot_duration)
        break_delta = timedelta(minutes=entry.break_duration or 0)
        current = entry_start
        safety = 0
        while current + slot_delta <= entry_end:
            safety += 1
            if safety > 500:
                return False
            if current == slot_start:
                return True
            current = current + slot_delta + break_delta
        return False

    @staticmethod
    def _get_patient(db: Session, user_id: int) -> User:
        user = db.query(User).filter(
            User.id == user_id,
            User.role == UserRole.PATIENT
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil patient introuvable"
            )
        return user

    @staticmethod
    def _parse_notification_preferences(raw_value: Optional[str]) -> Dict[str, bool]:
        if not raw_value:
            return {}
        try:
            data = json.loads(raw_value)
            if isinstance(data, dict):
                return {str(k): bool(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
        return {}

    @staticmethod
    def get_patient_profile(db: Session, user_id: int) -> User:
        """Retourner le profil patient"""
        return PatientService._get_patient(db, user_id)

    @staticmethod
    def update_patient_profile(
        db: Session,
        user_id: int,
        profile_data: PatientProfileUpdate
    ) -> User:
        """Mettre à jour les informations du patient"""
        patient = PatientService._get_patient(db, user_id)
        update_data = profile_data.model_dump(exclude_unset=True)

        notification_preferences = update_data.pop("notification_preferences", None)
        if notification_preferences is not None:
            patient.notification_preferences = json.dumps(notification_preferences)

        if "date_of_birth" in update_data:
            dob = update_data.pop("date_of_birth")
            if dob is not None:
                patient.date_of_birth = datetime.combine(dob, datetime.min.time())
            else:
                patient.date_of_birth = None

        allowed_fields = {
            "first_name",
            "last_name",
            "phone",
            "gender",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "postal_code",
            "country",
            "emergency_contact_name",
            "emergency_contact_phone",
            "emergency_contact_relationship",
            "marketing_consent",
            "data_processing_consent",
        }

        for field, value in update_data.items():
            if field in allowed_fields:
                setattr(patient, field, value)

        db.commit()
        db.refresh(patient)
        return patient

    @staticmethod
    def _appointment_to_summary(appointment: Appointment) -> PatientAppointmentSummary:
        doctor_user = appointment.doctor.user if appointment.doctor else None
        doctor_specialty = None
        if appointment.doctor and appointment.doctor.specialty:
            doctor_specialty = appointment.doctor.specialty.value
        return PatientAppointmentSummary(
            id=appointment.id,
            doctor_id=appointment.doctor_id,
            doctor_first_name=doctor_user.first_name if doctor_user else None,
            doctor_last_name=doctor_user.last_name if doctor_user else None,
            doctor_specialty=doctor_specialty,
            appointment_date=appointment.appointment_date,
            consultation_type=appointment.consultation_type,
            status=appointment.status,
            reason=appointment.reason,
            is_teleconsultation=appointment.consultation_type == ConsultationTypeEnum.TELECONSULTATION,
            meet_link=appointment.meet_link
        )

    @staticmethod
    def _appointment_to_response(appointment: Appointment) -> PatientAppointmentResponse:
        summary = PatientService._appointment_to_summary(appointment)
        return PatientAppointmentResponse(
            **summary.model_dump(),
            patient_notes=appointment.patient_notes,
            doctor_notes=appointment.doctor_notes,
            duration=appointment.duration,
            price=appointment.price
        )

    @staticmethod
    def get_dashboard_summary(db: Session, user_id: int) -> PatientDashboardSummary:
        """Retourner les données principales du tableau de bord patient"""
        patient = PatientService._get_patient(db, user_id)
        now = datetime.now(timezone.utc)

        upcoming_appointments = db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user)
        ).filter(
            Appointment.patient_id == patient.id,
            Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]),
            Appointment.appointment_date >= now
        ).order_by(Appointment.appointment_date.asc()).limit(5).all()

        documents = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient.id,
            PatientDocument.is_patient_visible == True
        ).order_by(PatientDocument.created_at.desc()).limit(5).all()

        prescriptions = db.query(ElectronicPrescription).options(
            joinedload(ElectronicPrescription.doctor).joinedload(DoctorProfile.user)
        ).filter(
            ElectronicPrescription.patient_id == patient.id
        ).order_by(ElectronicPrescription.issued_at.desc()).limit(5).all()

        unread_messages = db.query(func.count(DoctorMessage.id)).filter(
            DoctorMessage.recipient_id == patient.id,
            DoctorMessage.is_read == False
        ).scalar() or 0

        pending_payments = db.query(func.count(Payment.id)).filter(
            Payment.patient_id == patient.id,
            Payment.status == PaymentStatusEnum.PENDING
        ).scalar() or 0

        notifications: List[PatientNotification] = []
        if not patient.data_processing_consent:
            notifications.append(PatientNotification(
                message="Merci d'accepter le consentement de traitement des données pour profiter pleinement du service.",
                level="warning",
                created_at=now
            ))
        if upcoming_appointments:
            next_appointment = upcoming_appointments[0]
            doctor_user = next_appointment.doctor.user if next_appointment.doctor else None
            notifications.append(PatientNotification(
                message="Prochain rendez-vous le {} avec le Dr {} {}".format(
                    next_appointment.appointment_date.strftime("%d/%m/%Y à %Hh%M"),
                    doctor_user.first_name if doctor_user else "",
                    doctor_user.last_name if doctor_user else ""
                ),
                level="info",
                created_at=now
            ))

        return PatientDashboardSummary(
            profile=PatientProfileResponse.model_validate(patient),
            upcoming_appointments=[
                PatientService._appointment_to_summary(appt) for appt in upcoming_appointments
            ],
            pending_payments=pending_payments,
            unread_messages=unread_messages,
            recent_documents=[DocumentResponse.model_validate(doc) for doc in documents],
            recent_prescriptions=[ElectronicPrescriptionResponse.model_validate(p) for p in prescriptions],
            notifications=notifications,
        )

    @staticmethod
    def get_patient_appointments(
        db: Session,
        patient_id: int,
        status_filter: Optional[AppointmentStatusEnum] = None,
        upcoming_only: bool = False,
        page: int = 1,
        page_size: int = 50
    ) -> PatientAppointmentListResponse:
        """Obtenir la liste des rendez-vous patient"""
        query = db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user)
        ).filter(Appointment.patient_id == patient_id)

        if status_filter:
            query = query.filter(Appointment.status == status_filter)

        if upcoming_only:
            query = query.filter(
                Appointment.appointment_date >= datetime.now(timezone.utc),
                Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED])
            )

        total = query.count()

        appointments = query.order_by(desc(Appointment.appointment_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = [PatientService._appointment_to_response(appt) for appt in appointments]
        return PatientAppointmentListResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    @staticmethod
    def create_appointment(
        db: Session,
        patient_id: int,
        appointment_data: PatientAppointmentCreate
    ) -> Appointment:
        """Créer un rendez-vous pour un patient"""
        doctor = db.query(DoctorProfile).options(joinedload(DoctorProfile.user)).filter(
            DoctorProfile.id == appointment_data.doctor_id
        ).first()
        if not doctor or not doctor.is_public:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médecin introuvable"
            )

        # Ensure appointment_date is timezone-aware (UTC)
        appointment_date = appointment_data.appointment_date
        if appointment_date.tzinfo is None:
            # If naive datetime from frontend, treat as UTC
            appointment_date = appointment_date.replace(tzinfo=timezone.utc)
        appointment_date = PatientService._normalize_datetime_to_minute(appointment_date)
        
        # Use timezone-aware datetime for comparison
        now_utc = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        if appointment_date <= now_utc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La date du rendez-vous doit être dans le futur"
            )
        slot = PatientService._find_slot_for_datetime(db, doctor.id, appointment_date)
        consultation_type = PatientService._resolve_consultation_type(
            doctor,
            slot,
            appointment_data.consultation_type
        )

        slot_start = PatientService._normalize_datetime_to_minute(slot.start)
        slot_end = PatientService._normalize_datetime_to_minute(slot.end)
        slot_duration = int((slot_end - slot_start).total_seconds() // 60) or doctor.consultation_duration or 30

        day_start = datetime.combine(slot_start.date(), time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(slot_start.date(), time.max, tzinfo=timezone.utc)

        try:
            schedule_entry = db.query(DoctorScheduleEntry).filter(
                DoctorScheduleEntry.id == slot.schedule_entry_id,
                DoctorScheduleEntry.doctor_id == doctor.id
            ).with_for_update().first()

            if not schedule_entry:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="La configuration du planning n'existe plus"
                )

            if not PatientService._slot_belongs_to_entry(schedule_entry, slot_start):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce créneau ne correspond plus au planning du médecin"
                )

            if slot_end <= datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce créneau est déjà passé"
                )

            # ✅ VALIDATION: Vérifier que le créneau n'est pas bloqué (avec verrouillage)
            blocked_conflict = db.query(DoctorBlockedSlot).with_for_update().filter(
                DoctorBlockedSlot.doctor_id == doctor.id,
                DoctorBlockedSlot.start_datetime < slot_end,
                DoctorBlockedSlot.end_datetime > slot_start
            ).first()
            if blocked_conflict:
                reason = blocked_conflict.reason or "Indisponible"
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Ce créneau est bloqué par le praticien: {reason}"
                )

            doctor_conflicts = db.query(Appointment).with_for_update().filter(
                Appointment.doctor_id == doctor.id,
                Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]),
                Appointment.appointment_date >= day_start,
                Appointment.appointment_date <= day_end
            ).all()
            for conflict in doctor_conflicts:
                conflict_end = conflict.appointment_date + timedelta(minutes=conflict.duration or slot_duration)
                if conflict.appointment_date < slot_end and slot_start < conflict_end:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Ce créneau vient d'être réservé par un autre patient. Veuillez en choisir un autre."
                    )

            patient_conflicts = db.query(Appointment).with_for_update().filter(
                Appointment.patient_id == patient_id,
                Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]),
                Appointment.appointment_date >= day_start,
                Appointment.appointment_date <= day_end
            ).all()
            for conflict in patient_conflicts:
                conflict_end = conflict.appointment_date + timedelta(minutes=conflict.duration or slot_duration)
                if conflict.appointment_date < slot_end and slot_start < conflict_end:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Vous avez déjà un rendez-vous à cet horaire"
                    )

            appointment = Appointment(
                doctor_id=doctor.id,
                patient_id=patient_id,
                appointment_date=slot_start,
                schedule_entry_id=schedule_entry.id,
                consultation_type=consultation_type,
                status=AppointmentStatusEnum.PENDING,
                reason=appointment_data.reason,
                patient_notes=appointment_data.patient_notes,
                duration=schedule_entry.slot_duration,
                price=doctor.consultation_price,
            )
            db.add(appointment)
            db.flush()  # Flush to get the ID before generating meet link
            
            # Générer le lien de téléconsultation si nécessaire
            if TeleconsultationService.should_generate_meet_link(consultation_type):
                appointment.meet_link = TeleconsultationService.generate_meet_link(appointment)
            
            db.commit()
            
            # 🔔 Notification WebSocket: créneau réservé
            from app.core.websocket import manager as websocket_manager
            import asyncio
            try:
                slot_id = appointment.appointment_date.isoformat()
                asyncio.create_task(
                    websocket_manager.broadcast_slot_booked(
                        doctor.id,
                        slot_id,
                        patient_id
                    )
                )
            except Exception as e:
                logger.warning(f"⚠️ Erreur notification WebSocket: {e}")
        except Exception:
            db.rollback()
            raise

        db.refresh(appointment)
        return appointment

    @staticmethod
    def update_appointment(
        db: Session,
        patient_id: int,
        appointment_id: int,
        update_data: PatientAppointmentUpdate
    ) -> Appointment:
        """Modifier un rendez-vous existant"""
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id
        ).with_for_update().first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rendez-vous introuvable"
            )

        if appointment.status not in [AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Seuls les rendez-vous en attente ou confirmés peuvent être modifiés"
            )

        data = update_data.model_dump(exclude_unset=True)
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == appointment.doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin introuvable"
            )

        new_consultation_type = data.get("consultation_type", appointment.consultation_type)

        try:
            if "appointment_date" in data:
                new_date = PatientService._normalize_datetime_to_minute(data["appointment_date"])
                if new_date <= datetime.now(timezone.utc).replace(second=0, microsecond=0):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="La nouvelle date doit être dans le futur"
                    )

                slot = PatientService._find_slot_for_datetime(db, doctor.id, new_date)
                new_consultation_type = PatientService._resolve_consultation_type(doctor, slot, new_consultation_type)

                slot_start = PatientService._normalize_datetime_to_minute(slot.start)
                slot_end = PatientService._normalize_datetime_to_minute(slot.end)
                slot_duration = int((slot_end - slot_start).total_seconds() // 60) or appointment.duration or doctor.consultation_duration or 30

                day_start = datetime.combine(slot_start.date(), time.min, tzinfo=timezone.utc)
                day_end = datetime.combine(slot_start.date(), time.max, tzinfo=timezone.utc)

                schedule_entry = db.query(DoctorScheduleEntry).filter(
                    DoctorScheduleEntry.id == slot.schedule_entry_id,
                    DoctorScheduleEntry.doctor_id == doctor.id
                ).with_for_update().first()

                if not schedule_entry:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="La configuration du planning n'existe plus"
                    )

                if not PatientService._slot_belongs_to_entry(schedule_entry, slot_start):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ce créneau ne correspond plus au planning du médecin"
                    )

                blocked_conflict = db.query(DoctorBlockedSlot).with_for_update().filter(
                    DoctorBlockedSlot.doctor_id == doctor.id,
                    DoctorBlockedSlot.start_datetime < slot_end,
                    DoctorBlockedSlot.end_datetime > slot_start
                ).first()
                if blocked_conflict:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ce créneau est bloqué par le praticien"
                    )

                doctor_conflicts = db.query(Appointment).with_for_update().filter(
                    Appointment.doctor_id == doctor.id,
                    Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]),
                    Appointment.appointment_date >= day_start,
                    Appointment.appointment_date <= day_end,
                ).all()
                for conflict in doctor_conflicts:
                    if conflict.id == appointment.id:
                        continue
                    conflict_end = conflict.appointment_date + timedelta(minutes=conflict.duration or slot_duration)
                    if conflict.appointment_date < slot_end and slot_start < conflict_end:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Ce créneau est déjà réservé"
                        )

                patient_conflicts = db.query(Appointment).with_for_update().filter(
                    Appointment.patient_id == patient_id,
                    Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED]),
                    Appointment.appointment_date >= day_start,
                    Appointment.appointment_date <= day_end,
                ).all()
                for conflict in patient_conflicts:
                    if conflict.id == appointment.id:
                        continue
                    conflict_end = conflict.appointment_date + timedelta(minutes=conflict.duration or slot_duration)
                    if conflict.appointment_date < slot_end and slot_start < conflict_end:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Vous avez déjà un rendez-vous à cet horaire"
                        )

                appointment.appointment_date = slot_start
                appointment.schedule_entry_id = schedule_entry.id
                appointment.duration = schedule_entry.slot_duration
            else:
                schedule_entry = None
                if appointment.schedule_entry_id:
                    schedule_entry = db.query(DoctorScheduleEntry).filter(
                        DoctorScheduleEntry.id == appointment.schedule_entry_id,
                        DoctorScheduleEntry.doctor_id == doctor.id
                    ).with_for_update().first()

                entry_type = schedule_entry.consultation_type if schedule_entry else ConsultationTypeEnum.BOTH
                if entry_type != ConsultationTypeEnum.BOTH and entry_type != new_consultation_type:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Ce type de consultation n'est pas disponible pour ce créneau"
                    )

                slot_stub = DoctorAvailabilitySlot(
                    schedule_entry_id=appointment.schedule_entry_id or (schedule_entry.id if schedule_entry else 0),
                    start=appointment.appointment_date,
                    end=appointment.appointment_date + timedelta(minutes=appointment.duration or (schedule_entry.slot_duration if schedule_entry else doctor.consultation_duration or 30)),
                    consultation_type=entry_type if entry_type != ConsultationTypeEnum.BOTH else appointment.consultation_type,
                    location=schedule_entry.location if schedule_entry else None,
                )
                new_consultation_type = PatientService._resolve_consultation_type(doctor, slot_stub, new_consultation_type)

            appointment.consultation_type = new_consultation_type

            if "reason" in data:
                appointment.reason = data["reason"]
            if "patient_notes" in data:
                appointment.patient_notes = data["patient_notes"]
            
            # Générer ou mettre à jour le lien de téléconsultation si nécessaire
            if TeleconsultationService.should_generate_meet_link(new_consultation_type):
                if not appointment.meet_link:  # Générer uniquement si pas déjà présent
                    appointment.meet_link = TeleconsultationService.generate_meet_link(appointment)
            else:
                # Supprimer le lien si le type change et n'est plus une téléconsultation
                appointment.meet_link = None

            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(appointment)
        return appointment

    @staticmethod
    def cancel_appointment(db: Session, patient_id: int, appointment_id: int) -> Appointment:
        """Annuler un rendez-vous"""
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.patient_id == patient_id
        ).first()
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rendez-vous introuvable"
            )

        if appointment.status == AppointmentStatusEnum.CANCELLED:
            return appointment

        if appointment.appointment_date <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Impossible d'annuler un rendez-vous passé"
            )

        appointment.status = AppointmentStatusEnum.CANCELLED
        appointment.cancelled_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(appointment)
        return appointment

    @staticmethod
    def get_medical_record(db: Session, patient_id: int) -> PatientMedicalRecordResponse:
        """Obtenir le dossier médical du patient"""
        appointments = db.query(Appointment).options(
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user)
        ).filter(
            Appointment.patient_id == patient_id
        ).order_by(desc(Appointment.appointment_date)).all()

        documents = db.query(PatientDocument).filter(
            PatientDocument.patient_id == patient_id,
            PatientDocument.is_patient_visible == True
        ).order_by(desc(PatientDocument.created_at)).all()

        prescriptions = db.query(ElectronicPrescription).options(
            joinedload(ElectronicPrescription.doctor).joinedload(DoctorProfile.user)
        ).filter(
            ElectronicPrescription.patient_id == patient_id
        ).order_by(desc(ElectronicPrescription.issued_at)).all()

        return PatientMedicalRecordResponse(
            appointments=[PatientService._appointment_to_response(appt) for appt in appointments],
            documents=[DocumentResponse.model_validate(doc) for doc in documents],
            prescriptions=[ElectronicPrescriptionResponse.model_validate(p) for p in prescriptions]
        )

    @staticmethod
    def get_payments(
        db: Session,
        patient_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> PatientPaymentHistory:
        """Obtenir l'historique des paiements"""
        query = db.query(Payment).filter(Payment.patient_id == patient_id).options(
            joinedload(Payment.doctor)
        )

        total = query.count()
        payments = query.order_by(desc(Payment.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = [PaymentResponse.model_validate(payment) for payment in payments]
        return PatientPaymentHistory(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    @staticmethod
    def get_messages(
        db: Session,
        patient_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> PatientMessageList:
        """Obtenir les messages du patient"""
        query = db.query(DoctorMessage).filter(
            or_(
                DoctorMessage.sender_id == patient_id,
                DoctorMessage.recipient_id == patient_id
            )
        ).options(
            joinedload(DoctorMessage.sender),
            joinedload(DoctorMessage.recipient)
        )

        total = query.count()
        messages = query.order_by(desc(DoctorMessage.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        # Créer manuellement les MessageResponse avec les champs requis
        items = []
        for msg in messages:
            items.append(MessageResponse(
                id=msg.id,
                sender_id=msg.sender_id,
                recipient_id=msg.recipient_id,
                subject=msg.subject,
                content=msg.content,
                is_read=msg.is_read,
                read_at=msg.read_at,
                created_at=msg.created_at,
                sender_first_name=msg.sender.first_name,
                sender_last_name=msg.sender.last_name,
                recipient_first_name=msg.recipient.first_name,
                recipient_last_name=msg.recipient.last_name
            ))

        return PatientMessageList(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    @staticmethod
    def mark_message_as_read(
        db: Session,
        patient_id: int,
        message_id: int
    ) -> MessageResponse:
        """Marquer un message comme lu"""
        # Récupérer le message
        message = db.query(DoctorMessage).options(
            joinedload(DoctorMessage.sender),
            joinedload(DoctorMessage.recipient)
        ).filter(DoctorMessage.id == message_id).first()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message non trouvé"
            )
        
        # Vérifier que le patient est le destinataire
        if message.recipient_id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'êtes pas autorisé à marquer ce message comme lu"
            )
        
        # Marquer comme lu si ce n'est pas déjà fait
        if not message.is_read:
            message.is_read = True
            message.read_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(message)
        
        # Retourner le message avec les informations complètes
        return MessageResponse(
            id=message.id,
            sender_id=message.sender_id,
            recipient_id=message.recipient_id,
            subject=message.subject,
            content=message.content,
            is_read=message.is_read,
            read_at=message.read_at,
            created_at=message.created_at,
            sender_first_name=message.sender.first_name,
            sender_last_name=message.sender.last_name,
            recipient_first_name=message.recipient.first_name,
            recipient_last_name=message.recipient.last_name
        )

    @staticmethod
    def send_message(
        db: Session,
        sender_id: int,
        recipient_id: int,
        content: str,
        subject: Optional[str] = None,
        appointment_id: Optional[int] = None
    ) -> MessageResponse:
        """Envoyer un message vers un praticien"""
        message_schema = MessageCreate(
            recipient_id=recipient_id,
            content=content,
            subject=subject,
            appointment_id=appointment_id
        )

        message = DoctorService.send_message(
            db,
            sender_id,
            message_schema
        )
        return MessageResponse.model_validate(message)

    @staticmethod
    def search_doctors(
        db: Session,
        filters: DoctorSearchRequest,
        page: int = 1,
        page_size: int = 20
    ) -> DoctorSearchResponse:
        """Rechercher des praticiens selon des filtres"""
        query = db.query(DoctorProfile).join(User).filter(
            User.is_active == True,
            DoctorProfile.is_public == True,
            User.role == UserRole.DOCTOR
        )

        if filters.specialty:
            normalized = _normalize_text(filters.specialty)
            if normalized:
                resolved_enum = SPECIALTY_ALIASES.get(normalized)
                if not resolved_enum:
                    for specialty in SpecialtyEnum:
                        variants = {
                            _normalize_text(specialty.value),
                            _normalize_text(specialty.name),
                            _normalize_text(specialty.value.replace('_', ' ')),
                            _normalize_text(specialty.name.replace('_', ' ')),
                        }
                        if normalized in variants:
                            resolved_enum = specialty
                            break
                        if any(normalized in variant or variant in normalized for variant in variants if variant):
                            resolved_enum = specialty
                            break
                if resolved_enum:
                    query = query.filter(DoctorProfile.specialty == resolved_enum)
                else:
                    like_pattern = f"%{normalized}%"
                    query = query.filter(
                        or_(
                            func.lower(cast(DoctorProfile.specialty, String)).like(like_pattern),
                            func.lower(func.coalesce(DoctorProfile.sub_specialty, '')).like(like_pattern),
                            func.lower(func.coalesce(DoctorProfile.biography, '')).like(like_pattern),
                        )
                    )
        if filters.city:
            query = query.filter(DoctorProfile.office_city.ilike(f"%{filters.city}%"))
        if filters.language:
            query = query.filter(DoctorProfile.languages.contains([filters.language]))
        if filters.min_price is not None:
            query = query.filter(DoctorProfile.consultation_price >= filters.min_price)
        if filters.max_price is not None:
            query = query.filter(DoctorProfile.consultation_price <= filters.max_price)
        if filters.search:
            normalized_search = _normalize_text(filters.search)
            if normalized_search:
                search_term = f"%{normalized_search}%"
                query = query.filter(
                    or_(
                        func.lower(func.coalesce(User.first_name, '')).like(search_term),
                        func.lower(func.coalesce(User.last_name, '')).like(search_term),
                        func.lower(func.coalesce(DoctorProfile.biography, '')).like(search_term),
                        func.lower(func.coalesce(DoctorProfile.sub_specialty, '')).like(search_term),
                        func.lower(cast(DoctorProfile.specialty, String)).like(search_term),
                    )
                )

        total = query.count()
        doctors = query.order_by(User.last_name.asc()).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        items = [
            DoctorSearchResult(
                doctor_id=doc.id,
                first_name=doc.user.first_name,
                last_name=doc.user.last_name,
                specialty=doc.specialty.value if doc.specialty else "",
                city=doc.office_city,
                consultation_types=doc.consultation_types,
                consultation_duration=doc.consultation_duration,
                consultation_price=doc.consultation_price,
                average_rating=doc.average_rating,
                total_reviews=doc.total_reviews,
                languages=doc.languages or [],
                accepts_new_patients=doc.accepts_new_patients,
            )
            for doc in doctors
        ]

        return DoctorSearchResponse(
            total=total,
            page=page,
            page_size=page_size,
            items=items
        )

    @staticmethod
    def create_doctor_review(
        db: Session,
        patient_id: int,
        review_data: DoctorReviewCreate
    ) -> DoctorReview:
        """Créer un avis sur un médecin après un rendez-vous terminé"""
        
        # Vérifier que le médecin existe
        doctor = db.query(DoctorProfile).filter(
            DoctorProfile.id == review_data.doctor_id
        ).first()
        
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médecin non trouvé"
            )
        
        # Si un appointment_id est fourni, vérifier qu il est terminé
        if review_data.appointment_id:
            appointment = db.query(Appointment).filter(
                Appointment.id == review_data.appointment_id,
                Appointment.patient_id == patient_id,
                Appointment.doctor_id == review_data.doctor_id
            ).first()
            
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Rendez-vous non trouvé"
                )
            
            if appointment.status != AppointmentStatusEnum.COMPLETED:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vous ne pouvez noter que les rendez-vous terminés"
                )
            
            # Vérifier qu il n y a pas déjà un avis pour ce rendez-vous
            existing_review = db.query(DoctorReview).filter(
                DoctorReview.appointment_id == review_data.appointment_id,
                DoctorReview.patient_id == patient_id
            ).first()
            
            if existing_review:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Vous avez déjà noté ce rendez-vous"
                )
        
        # Créer l avis
        review = DoctorReview(
            doctor_id=review_data.doctor_id,
            patient_id=patient_id,
            appointment_id=review_data.appointment_id,
            rating=review_data.rating,
            comment=review_data.comment,
            is_public=review_data.is_public
        )
        
        db.add(review)
        db.commit()
        db.refresh(review)
        
        # 🆕 Mettre à jour les statistiques du docteur
        all_reviews = db.query(DoctorReview).filter(
            DoctorReview.doctor_id == review_data.doctor_id
        ).all()
        
        if all_reviews:
            total_reviews_count = len(all_reviews)
            average_rating_value = sum(r.rating for r in all_reviews) / total_reviews_count
            
            doctor.total_reviews = total_reviews_count
            doctor.average_rating = round(average_rating_value, 2)
            db.commit()
        
        return review
