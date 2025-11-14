"""
Service pour la gestion des profils et actions des médecins
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc
from typing import Optional, List, Tuple
from datetime import datetime, date, time, timedelta, timezone
from fastapi import HTTPException, status, UploadFile
import os
import uuid

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
    AppointmentStatusEnum,
    PaymentStatusEnum,
    ElectronicPrescription,
    PrescriptionStatusEnum,
)
from app.models.user import User, UserRole
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
    BlockedSlotCreate,
    AppointmentStatusUpdate,
    MessageCreate,
    ReviewResponseCreate,
    DoctorSettingsUpdate,
    DoctorStatistics,
    ElectronicPrescriptionCreate,
    DoctorAvailabilitySlot,
    BlockedSlotResponse,
)


class DoctorService:
    """Service pour gérer les opérations liées aux médecins"""

    @staticmethod
    def _generate_prescription_number(db: Session) -> str:
        """Génère un identifiant unique pour une ordonnance électronique"""
        for _ in range(5):  # Essayer quelques fois en cas de collision improbable
            candidate = f"RX-{uuid.uuid4().hex[:10].upper()}"
            exists = db.query(ElectronicPrescription).filter(
                ElectronicPrescription.prescription_number == candidate
            ).first()
            if not exists:
                return candidate
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Impossible de générer un numéro d'ordonnance unique"
        )

    @staticmethod
    def create_doctor_profile(
        db: Session,
        user_id: int,
        profile_data: DoctorProfileCreate
    ) -> DoctorProfile:
        """Créer un profil de médecin"""
        # Vérifier que l'utilisateur existe et a le rôle doctor
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Utilisateur non trouvé"
            )
        
        if user.role != UserRole.DOCTOR:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Seuls les utilisateurs avec le rôle 'doctor' peuvent créer un profil médecin"
            )
        
        # Vérifier que le profil n'existe pas déjà
        existing_profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == user_id
        ).first()
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Un profil médecin existe déjà pour cet utilisateur"
            )
        
        # Vérifier l'unicité du numéro RPPS (uniquement si fourni)
        if profile_data.rpps_number:
            existing_rpps = db.query(DoctorProfile).filter(
                DoctorProfile.rpps_number == profile_data.rpps_number
            ).first()
            if existing_rpps:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Ce numéro RPPS est déjà utilisé"
                )
        
        # Créer le profil
        doctor_profile = DoctorProfile(
            user_id=user_id,
            **profile_data.model_dump()
        )
        db.add(doctor_profile)
        db.flush()  # Force l'insertion pour obtenir l'ID sans committer
        
        # Créer les paramètres par défaut (maintenant que doctor_profile.id existe)
        settings = DoctorSettings(doctor_id=doctor_profile.id)
        db.add(settings)
        
        db.commit()
        db.refresh(doctor_profile)
        return doctor_profile

    @staticmethod
    def get_doctor_profile(db: Session, user_id: int) -> DoctorProfile:
        """Obtenir le profil du médecin connecté"""
        profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == user_id
        ).options(joinedload(DoctorProfile.user)).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin non trouvé"
            )
        
        return profile

    @staticmethod
    def update_doctor_profile(
        db: Session,
        user_id: int,
        profile_data: DoctorProfileUpdate
    ) -> DoctorProfile:
        """Mettre à jour le profil du médecin (ou le créer s'il n'existe pas)"""
        # Vérifier si le profil existe déjà
        profile = db.query(DoctorProfile).filter(
            DoctorProfile.user_id == user_id
        ).first()
        
        if not profile:
            # Créer le profil s'il n'existe pas
            # Convertir DoctorProfileUpdate en DoctorProfileCreate
            from app.schemas.doctor import DoctorProfileCreate
            create_data = DoctorProfileCreate(**profile_data.model_dump(exclude_unset=True))
            return DoctorService.create_doctor_profile(db, user_id, create_data)
        
        # Mettre à jour uniquement les champs fournis
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)
        
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_public_doctor_profile(db: Session, doctor_id: int) -> DoctorProfile:
        """Obtenir le profil public d'un médecin"""
        profile = db.query(DoctorProfile).filter(
            DoctorProfile.id == doctor_id,
            DoctorProfile.is_public == True
        ).options(joinedload(DoctorProfile.user)).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin non trouvé ou non public"
            )
        
        return profile

    # ========== Gestion des disponibilités ==========

    @staticmethod
    def _validate_schedule_entry_window(
        start_time: time,
        end_time: time,
        slot_duration: int,
        break_duration: int
    ) -> None:
        """Valider qu'une configuration de planning est cohérente."""
        if slot_duration <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La durée d'un créneau doit être supérieure à zéro"
            )
        window_minutes = int(
            (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() // 60
        )
        if window_minutes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"L'heure de fin ({end_time}) doit être après l'heure de début ({start_time})"
            )
        if slot_duration > window_minutes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La durée du créneau ne peut pas dépasser la plage horaire"
            )
        if break_duration < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La pause entre les créneaux ne peut pas être négative"
            )

    @staticmethod
    def create_schedule_entry(
        db: Session,
        doctor_id: int,
        entry_data: ScheduleEntryCreate
    ) -> DoctorScheduleEntry:
        """Créer une configuration de disponibilité récurrente"""
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin non trouvé"
            )

        DoctorService._validate_schedule_entry_window(
            entry_data.start_time,
            entry_data.end_time,
            entry_data.slot_duration,
            entry_data.break_duration,
        )

        overlapping = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.doctor_id == doctor_id,
            DoctorScheduleEntry.day_of_week == entry_data.day_of_week,
            or_(
                and_(
                    DoctorScheduleEntry.start_time <= entry_data.start_time,
                    DoctorScheduleEntry.end_time > entry_data.start_time
                ),
                and_(
                    DoctorScheduleEntry.start_time < entry_data.end_time,
                    DoctorScheduleEntry.end_time >= entry_data.end_time
                ),
                and_(
                    DoctorScheduleEntry.start_time >= entry_data.start_time,
                    DoctorScheduleEntry.end_time <= entry_data.end_time
                )
            )
        ).first()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce créneau chevauche une configuration existante pour ce jour"
            )

        entry = DoctorScheduleEntry(
            doctor_id=doctor_id,
            **entry_data.model_dump()
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def update_schedule_entry(
        db: Session,
        doctor_id: int,
        schedule_entry_id: int,
        entry_data: ScheduleEntryUpdate
    ) -> DoctorScheduleEntry:
        """Mettre à jour une configuration de disponibilité"""
        entry = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.id == schedule_entry_id,
            DoctorScheduleEntry.doctor_id == doctor_id
        ).first()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration non trouvée"
            )

        update_fields = entry_data.model_dump(exclude_unset=True)
        if not update_fields:
            return entry

        new_day = update_fields.get("day_of_week", entry.day_of_week)
        new_start = update_fields.get("start_time", entry.start_time)
        new_end = update_fields.get("end_time", entry.end_time)
        new_slot_duration = update_fields.get("slot_duration", entry.slot_duration)
        new_break = update_fields.get("break_duration", entry.break_duration)

        DoctorService._validate_schedule_entry_window(
            new_start,
            new_end,
            new_slot_duration,
            new_break,
        )

        overlapping = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.doctor_id == doctor_id,
            DoctorScheduleEntry.day_of_week == new_day,
            DoctorScheduleEntry.id != schedule_entry_id,
            or_(
                and_(
                    DoctorScheduleEntry.start_time <= new_start,
                    DoctorScheduleEntry.end_time > new_start
                ),
                and_(
                    DoctorScheduleEntry.start_time < new_end,
                    DoctorScheduleEntry.end_time >= new_end
                ),
                and_(
                    DoctorScheduleEntry.start_time >= new_start,
                    DoctorScheduleEntry.end_time <= new_end
                )
            )
        ).first()

        if overlapping:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ce créneau chevauche une configuration existante pour ce jour"
            )

        for field, value in update_fields.items():
            setattr(entry, field, value)

        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def list_schedule_entries(db: Session, doctor_id: int) -> List[DoctorScheduleEntry]:
        """Lister les configurations de disponibilités du médecin"""
        return db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.doctor_id == doctor_id
        ).order_by(DoctorScheduleEntry.day_of_week, DoctorScheduleEntry.start_time).all()

    @staticmethod
    def get_available_slots(
        db: Session,
        doctor_id: int,
        start_date: date,
        end_date: date,
        consultation_type: Optional[str] = None
    ) -> List[dict]:
        """
        Génère les créneaux disponibles en croisant:
        1. Horaires récurrents (DoctorScheduleEntry)
        2. Slots bloqués (DoctorBlockedSlot)
        3. Rendez-vous existants (Appointment)
        
        Args:
            doctor_id: ID du médecin
            start_date: Date de début de recherche
            end_date: Date de fin de recherche
            consultation_type: Filtre optionnel par type (IN_PERSON, TELECONSULTATION)
        
        Returns:
            Liste de dictionnaires représentant les créneaux disponibles
        """
        # 1. Vérifier que le médecin existe
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médecin non trouvé"
            )
        
        # 2. Récupérer les entrées de planning
        schedule_entries = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.doctor_id == doctor_id
        ).all()
        
        # Filtrer par type de consultation si spécifié
        if consultation_type:
            filtered_entries = []
            for entry in schedule_entries:
                # entry.consultation_type peut être "IN_PERSON", "TELECONSULTATION" ou "BOTH"
                if entry.consultation_type == "BOTH":
                    filtered_entries.append(entry)
                elif entry.consultation_type == consultation_type:
                    filtered_entries.append(entry)
            schedule_entries = filtered_entries
        
        # 3. Récupérer les slots bloqués dans la période
        # Créer des datetimes timezone-aware pour la comparaison avec la DB
        start_datetime = datetime.combine(start_date, time.min).replace(tzinfo=timezone.utc)
        end_datetime = datetime.combine(end_date, time.max).replace(tzinfo=timezone.utc)
        
        blocked_slots = db.query(DoctorBlockedSlot).filter(
            DoctorBlockedSlot.doctor_id == doctor_id,
            DoctorBlockedSlot.start_datetime < end_datetime,
            DoctorBlockedSlot.end_datetime > start_datetime
        ).all()
        
        # 4. Récupérer les rendez-vous existants (statuts PENDING ou CONFIRMED)
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= start_datetime,
            Appointment.appointment_date <= end_datetime,
            Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED])
        ).all()
        
        # 5. Générer tous les créneaux possibles
        slots = []
        current_date = start_date
        
        while current_date <= end_date:
            # Convertir jour Python (Monday=0) vers format DB (Sunday=0)
            day_of_week = (current_date.weekday() + 1) % 7
            
            # Trouver les entrées de planning pour ce jour
            day_entries = [e for e in schedule_entries if e.day_of_week == day_of_week]
            
            for entry in day_entries:
                # Déterminer les types de consultation disponibles pour ce créneau
                if entry.consultation_type == "BOTH":
                    slot_consultation_types = ["IN_PERSON", "TELECONSULTATION"]
                else:
                    slot_consultation_types = [entry.consultation_type]
                
                # Générer les slots pour cette entrée
                slot_start_time = entry.start_time
                duration_minutes = entry.slot_duration or 30
                
                while slot_start_time < entry.end_time:
                    # Créer le datetime du slot (timezone-aware pour compatibilité DB)
                    slot_start_naive = datetime.combine(current_date, slot_start_time)
                    slot_start = slot_start_naive.replace(tzinfo=timezone.utc)
                    slot_end = slot_start + timedelta(minutes=duration_minutes)
                    
                    # Vérifier si le slot est bloqué
                    is_blocked = any(
                        blocked.start_datetime <= slot_start < blocked.end_datetime
                        for blocked in blocked_slots
                    )
                    
                    # Vérifier si le slot est déjà réservé
                    # Tolérance de 1 minute pour éviter les problèmes d'arrondi
                    is_booked = any(
                        abs((appt.appointment_date - slot_start).total_seconds()) < 60
                        for appt in appointments
                    )
                    
                    # Ajouter le slot à la liste
                    slots.append({
                        'id': slot_start.isoformat(),
                        'doctor_id': doctor_id,
                        'start_time': slot_start,
                        'end_time': slot_end,
                        'consultation_types': slot_consultation_types,
                        'is_available': not (is_blocked or is_booked),
                        'schedule_entry_id': entry.id,
                        'location': entry.location
                    })
                    
                    # Passer au créneau suivant
                    next_time = datetime.combine(current_date, slot_start_time) + timedelta(minutes=duration_minutes)
                    slot_start_time = next_time.time()
                    
                    # Ajouter la pause si configurée
                    if entry.break_duration and entry.break_duration > 0:
                        next_time += timedelta(minutes=entry.break_duration)
                        slot_start_time = next_time.time()
            
            current_date += timedelta(days=1)
        
        return slots

    @staticmethod
    def delete_schedule_entry(db: Session, doctor_id: int, schedule_entry_id: int) -> None:
        """Supprimer une configuration de disponibilité"""
        entry = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.id == schedule_entry_id,
            DoctorScheduleEntry.doctor_id == doctor_id
        ).first()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuration non trouvée"
            )

        db.delete(entry)
        db.commit()

    @staticmethod
    def list_blocked_slots(
        db: Session,
        doctor_id: int,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> List[DoctorBlockedSlot]:
        """Obtenir les indisponibilités ponctuelles d'un médecin"""
        query = db.query(DoctorBlockedSlot).filter(DoctorBlockedSlot.doctor_id == doctor_id)
        if start:
            query = query.filter(DoctorBlockedSlot.end_datetime >= start)
        if end:
            query = query.filter(DoctorBlockedSlot.start_datetime <= end)
        return query.order_by(DoctorBlockedSlot.start_datetime.asc()).all()

    @staticmethod
    def create_blocked_slot(
        db: Session,
        doctor_id: int,
        payload: BlockedSlotCreate
    ) -> DoctorBlockedSlot:
        """Créer une indisponibilité ponctuelle"""
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin non trouvé"
            )

        overlap = db.query(DoctorBlockedSlot).filter(
            DoctorBlockedSlot.doctor_id == doctor_id,
            DoctorBlockedSlot.start_datetime < payload.end_datetime,
            DoctorBlockedSlot.end_datetime > payload.start_datetime
        ).first()
        if overlap:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Une indisponibilité existe déjà sur cette période"
            )

        blocked = DoctorBlockedSlot(
            doctor_id=doctor_id,
            **payload.model_dump()
        )
        db.add(blocked)
        db.commit()
        db.refresh(blocked)
        return blocked

    @staticmethod
    def delete_blocked_slot(db: Session, doctor_id: int, slot_id: int) -> None:
        """Supprimer une indisponibilité ponctuelle"""
        blocked = db.query(DoctorBlockedSlot).filter(
            DoctorBlockedSlot.id == slot_id,
            DoctorBlockedSlot.doctor_id == doctor_id
        ).first()
        if not blocked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Indisponibilité non trouvée"
            )
        db.delete(blocked)
        db.commit()

    @staticmethod
    def get_doctor_availability_slots(
        db: Session,
        doctor_id: int,
        target_date: date
    ) -> List[DoctorAvailabilitySlot]:
        """Calculer dynamiquement les créneaux disponibles pour un jour donné"""
        weekday = (target_date.weekday() + 1) % 7
        schedule_entries = db.query(DoctorScheduleEntry).filter(
            DoctorScheduleEntry.doctor_id == doctor_id,
            DoctorScheduleEntry.day_of_week == weekday
        ).all()

        if not schedule_entries:
            return []

        day_start = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        day_end = datetime.combine(target_date, time.max, tzinfo=timezone.utc)

        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date >= day_start,
            Appointment.appointment_date <= day_end,
            Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED])
        ).all()

        blocked_slots = db.query(DoctorBlockedSlot).filter(
            DoctorBlockedSlot.doctor_id == doctor_id,
            DoctorBlockedSlot.start_datetime < day_end,
            DoctorBlockedSlot.end_datetime > day_start
        ).all()

        now_utc = datetime.now(timezone.utc)
        slots: List[DoctorAvailabilitySlot] = []

        def overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
            return start_a < end_b and start_b < end_a

        for entry in schedule_entries:
            current_start = datetime.combine(target_date, entry.start_time, tzinfo=timezone.utc)
            schedule_end = datetime.combine(target_date, entry.end_time, tzinfo=timezone.utc)
            slot_delta = timedelta(minutes=entry.slot_duration)
            break_delta = timedelta(minutes=entry.break_duration or 0)

            safety_counter = 0
            while current_start + slot_delta <= schedule_end:
                safety_counter += 1
                if safety_counter > 500:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Configuration de planning invalide: trop de créneaux générés"
                    )

                slot_start = current_start
                slot_end = slot_start + slot_delta

                current_start = slot_end + break_delta

                if slot_end <= now_utc:
                    continue

                blocked_conflict = any(
                    overlaps(slot_start, slot_end, b.start_datetime, b.end_datetime)
                    for b in blocked_slots
                )
                if blocked_conflict:
                    continue

                appointment_conflict = False
                for appt in appointments:
                    appt_duration = appt.duration or entry.slot_duration
                    appt_end = appt.appointment_date + timedelta(minutes=appt_duration)
                    if overlaps(slot_start, slot_end, appt.appointment_date, appt_end):
                        appointment_conflict = True
                        break
                if appointment_conflict:
                    continue

                slots.append(DoctorAvailabilitySlot(
                    schedule_entry_id=entry.id,
                    start=slot_start,
                    end=slot_end,
                    consultation_type=entry.consultation_type,
                    location=entry.location,
                ))

        return sorted(slots, key=lambda s: s.start)

    # ========== Gestion des rendez-vous ==========

    @staticmethod
    def get_doctor_appointments(
        db: Session,
        doctor_id: int,
        status_filter: Optional[AppointmentStatusEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Appointment], int]:
        """Obtenir les rendez-vous d'un médecin (sauf les supprimés)"""
        query = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.is_deleted == False  # Exclure les supprimés
        ).options(joinedload(Appointment.patient))
        
        if status_filter:
            query = query.filter(Appointment.status == status_filter)
        
        if start_date:
            query = query.filter(Appointment.appointment_date >= start_date)
        
        if end_date:
            query = query.filter(Appointment.appointment_date <= end_date)
        
        total = query.count()
        
        appointments = query.order_by(desc(Appointment.appointment_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return appointments, total

    @staticmethod
    def get_appointment_details(
        db: Session,
        doctor_id: int,
        appointment_id: int
    ) -> Appointment:
        """Obtenir les détails d'un rendez-vous"""
        appointment = db.query(Appointment).filter(
            Appointment.id == appointment_id,
            Appointment.doctor_id == doctor_id,
            Appointment.is_deleted == False  # Exclure les supprimés
        ).options(joinedload(Appointment.patient)).first()
        
        if not appointment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Rendez-vous non trouvé"
            )
        
        return appointment

    @staticmethod
    def update_appointment_status(
        db: Session,
        doctor_id: int,
        appointment_id: int,
        status_update: AppointmentStatusUpdate
    ) -> Appointment:
        """Mettre à jour le statut d'un rendez-vous"""
        appointment = DoctorService.get_appointment_details(db, doctor_id, appointment_id)
        
        old_status = appointment.status
        appointment.status = status_update.status
        
        # Mettre à jour les notes, diagnostic et prescription
        if status_update.notes:
            appointment.notes = status_update.notes
        if status_update.diagnosis:
            appointment.diagnosis = status_update.diagnosis
        if status_update.prescription:
            appointment.prescription = status_update.prescription
        
        # Mettre à jour les timestamps
        if status_update.status == AppointmentStatusEnum.COMPLETED:
            appointment.completed_at = datetime.now(timezone.utc)
            # Incrémenter le compteur de consultations
            doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
            if doctor:
                doctor.total_consultations += 1
        elif status_update.status == AppointmentStatusEnum.CANCELLED:
            appointment.cancelled_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(appointment)
        return appointment

    # ========== Gestion des patients ==========

    @staticmethod
    def get_doctor_patients(
        db: Session,
        doctor_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[dict], int]:
        """Obtenir la liste des patients suivis par un médecin"""
        # Sous-requête pour compter les rendez-vous par patient
        subquery = db.query(
            Appointment.patient_id,
            func.count(Appointment.id).label('total_appointments'),
            func.max(Appointment.appointment_date).label('last_appointment_date')
        ).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatusEnum.COMPLETED, AppointmentStatusEnum.CONFIRMED])
        ).group_by(Appointment.patient_id).subquery()
        
        # Requête principale
        query = db.query(
            User,
            subquery.c.total_appointments,
            subquery.c.last_appointment_date
        ).join(
            subquery, User.id == subquery.c.patient_id
        )
        
        total = query.count()
        
        results = query.order_by(desc(subquery.c.last_appointment_date)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        patients = []
        for user, total_appts, last_appt_date in results:
            patients.append({
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
                "phone": user.phone,
                "date_of_birth": user.date_of_birth,
                "total_appointments": total_appts or 0,
                "last_appointment_date": last_appt_date
            })
        
        return patients, total

    @staticmethod
    def get_patient_medical_record(
        db: Session,
        doctor_id: int,
        patient_id: int
    ) -> dict:
        """Obtenir le dossier médical d'un patient"""
        # Vérifier que le patient a bien consulté ce médecin
        has_consulted = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id
        ).first()
        
        if not has_consulted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous n'avez pas accès au dossier de ce patient"
            )
        
        # Récupérer le patient
        patient = db.query(User).filter(User.id == patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient non trouvé"
            )
        
        # Récupérer l'historique des rendez-vous
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id
        ).order_by(desc(Appointment.appointment_date)).all()
        
        # Récupérer les documents
        documents = db.query(PatientDocument).filter(
            PatientDocument.doctor_id == doctor_id,
            PatientDocument.patient_id == patient_id
        ).order_by(desc(PatientDocument.created_at)).all()

        prescriptions = db.query(ElectronicPrescription).filter(
            ElectronicPrescription.doctor_id == doctor_id,
            ElectronicPrescription.patient_id == patient_id
        ).options(
            joinedload(ElectronicPrescription.patient)
        ).order_by(desc(ElectronicPrescription.issued_at)).all()
        
        return {
            "patient": patient,
            "appointments": appointments,
            "documents": documents,
            "prescriptions": prescriptions,
            "total_consultations": len([a for a in appointments if a.status == AppointmentStatusEnum.COMPLETED])
        }

    # ========== Statistiques ==========

    @staticmethod
    def get_doctor_statistics(db: Session, doctor_id: int) -> DoctorStatistics:
        """Générer les statistiques d'activité du médecin"""
        doctor = db.query(DoctorProfile).filter(DoctorProfile.id == doctor_id).first()
        if not doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Profil médecin non trouvé"
            )
        
        # Compter les consultations par statut
        completed = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatusEnum.COMPLETED
        ).scalar() or 0
        
        cancelled = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatusEnum.CANCELLED
        ).scalar() or 0
        
        no_show = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.status == AppointmentStatusEnum.NO_SHOW
        ).scalar() or 0
        
        total = completed + cancelled + no_show
        cancellation_rate = (cancelled + no_show) / total * 100 if total > 0 else 0
        
        # Patients nouveaux vs récurrents
        total_patients = db.query(func.count(func.distinct(Appointment.patient_id))).filter(
            Appointment.doctor_id == doctor_id
        ).scalar() or 0
        
        # Patients avec plus d'un rendez-vous
        returning_patients = db.query(func.count(func.distinct(Appointment.patient_id))).filter(
            Appointment.doctor_id == doctor_id
        ).group_by(Appointment.patient_id).having(
            func.count(Appointment.id) > 1
        ).count()
        
        new_patients = total_patients - returning_patients
        
        # Revenus
        total_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.doctor_id == doctor_id,
            Payment.status == PaymentStatusEnum.COMPLETED
        ).scalar() or 0
        
        pending_revenue = db.query(func.sum(Payment.amount)).filter(
            Payment.doctor_id == doctor_id,
            Payment.status == PaymentStatusEnum.PENDING
        ).scalar() or 0
        
        # Rendez-vous à venir
        now = datetime.now(timezone.utc)
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today(), time.max)
        
        upcoming_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date > now,
            Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED])
        ).scalar() or 0
        
        today_appointments = db.query(func.count(Appointment.id)).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.appointment_date.between(today_start, today_end),
            Appointment.status.in_([AppointmentStatusEnum.PENDING, AppointmentStatusEnum.CONFIRMED])
        ).scalar() or 0
        
        return DoctorStatistics(
            total_consultations=total,
            completed_consultations=completed,
            cancelled_consultations=cancelled,
            no_show_consultations=no_show,
            cancellation_rate=round(cancellation_rate, 2),
            average_rating=doctor.average_rating,
            total_reviews=doctor.total_reviews,
            new_patients_count=new_patients,
            returning_patients_count=returning_patients,
            total_revenue=total_revenue,
            pending_revenue=pending_revenue,
            upcoming_appointments=upcoming_appointments,
            today_appointments=today_appointments
        )

    # ========== Messages ==========

    @staticmethod
    def get_doctor_messages(
        db: Session,
        user_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DoctorMessage], int]:
        """Obtenir les messages du médecin"""
        query = db.query(DoctorMessage).filter(
            or_(
                DoctorMessage.sender_id == user_id,
                DoctorMessage.recipient_id == user_id
            )
        ).options(
            joinedload(DoctorMessage.sender),
            joinedload(DoctorMessage.recipient)
        )
        
        total = query.count()
        
        messages = query.order_by(desc(DoctorMessage.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return messages, total

    @staticmethod
    def send_message(
        db: Session,
        sender_id: int,
        message_data: MessageCreate
    ) -> DoctorMessage:
        """Envoyer un message"""
        # Vérifier que le destinataire existe
        recipient = db.query(User).filter(User.id == message_data.recipient_id).first()
        if not recipient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destinataire non trouvé"
            )
        
        message = DoctorMessage(
            sender_id=sender_id,
            **message_data.model_dump()
        )
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Charger les relations
        db.refresh(message)
        message.sender
        message.recipient
        
        return message

    # ========== Avis ==========

    @staticmethod
    def get_doctor_reviews(
        db: Session,
        doctor_id: int,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[DoctorReview], int]:
        """Obtenir les avis d'un médecin"""
        query = db.query(DoctorReview).filter(
            DoctorReview.doctor_id == doctor_id,
            DoctorReview.is_public == True
        ).options(joinedload(DoctorReview.patient))
        
        total = query.count()
        
        reviews = query.order_by(desc(DoctorReview.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return reviews, total

    @staticmethod
    def respond_to_review(
        db: Session,
        doctor_id: int,
        review_id: int,
        response_data: ReviewResponseCreate
    ) -> DoctorReview:
        """Répondre à un avis"""
        review = db.query(DoctorReview).filter(
            DoctorReview.id == review_id,
            DoctorReview.doctor_id == doctor_id
        ).first()
        
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Avis non trouvé"
            )
        
        review.doctor_response = response_data.response
        review.responded_at = datetime.now(timezone.utc)
        
        db.commit()
        db.refresh(review)
        return review

    # ========== Paiements ==========

    @staticmethod
    def get_doctor_payments(
        db: Session,
        doctor_id: int,
        status_filter: Optional[PaymentStatusEnum] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Payment], int]:
        """Obtenir l'historique des paiements"""
        query = db.query(Payment).filter(
            Payment.doctor_id == doctor_id
        ).options(joinedload(Payment.patient))
        
        if status_filter:
            query = query.filter(Payment.status == status_filter)
        
        total = query.count()
        
        payments = query.order_by(desc(Payment.created_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()
        
        return payments, total

    # ========== Documents ==========

    @staticmethod
    async def upload_patient_document(
        db: Session,
        doctor_id: int,
        patient_id: int,
        file: UploadFile,
        title: str,
        description: Optional[str] = None,
        document_type: Optional[str] = None,
        appointment_id: Optional[int] = None
    ) -> PatientDocument:
        """Uploader un document pour un patient"""
        # Vérifier que le patient existe et a consulté ce médecin
        has_consulted = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == patient_id
        ).first()
        
        if not has_consulted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez envoyer des documents qu'à vos patients"
            )
        
        # Créer le dossier uploads si nécessaire
        upload_dir = "uploads/documents"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Générer un nom de fichier unique
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Créer l'entrée en base de données
        document = PatientDocument(
            doctor_id=doctor_id,
            patient_id=patient_id,
            appointment_id=appointment_id,
            title=title,
            description=description,
            file_path=file_path,
            file_name=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            document_type=document_type
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return document

    # ========== Ordonnances électroniques ==========

    @staticmethod
    def list_prescriptions(
        db: Session,
        doctor_id: int,
        page: int = 1,
        page_size: int = 50,
        patient_id: Optional[int] = None
    ) -> Tuple[List[ElectronicPrescription], int]:
        """Obtenir les ordonnances émises par le médecin"""
        query = db.query(ElectronicPrescription).filter(
            ElectronicPrescription.doctor_id == doctor_id
        ).options(joinedload(ElectronicPrescription.patient))

        if patient_id:
            query = query.filter(ElectronicPrescription.patient_id == patient_id)

        total = query.count()

        prescriptions = query.order_by(desc(ElectronicPrescription.issued_at)).offset(
            (page - 1) * page_size
        ).limit(page_size).all()

        return prescriptions, total

    @staticmethod
    def get_prescription(
        db: Session,
        doctor_id: int,
        prescription_id: int
    ) -> ElectronicPrescription:
        """Récupérer une ordonnance spécifique"""
        prescription = db.query(ElectronicPrescription).filter(
            ElectronicPrescription.id == prescription_id,
            ElectronicPrescription.doctor_id == doctor_id
        ).options(joinedload(ElectronicPrescription.patient)).first()

        if not prescription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ordonnance non trouvée"
            )

        return prescription

    @staticmethod
    def issue_prescription(
        db: Session,
        doctor_id: int,
        prescription_data: ElectronicPrescriptionCreate
    ) -> ElectronicPrescription:
        """Émettre une nouvelle ordonnance électronique"""
        # Vérifier que le patient existe
        patient = db.query(User).filter(User.id == prescription_data.patient_id).first()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Patient non trouvé"
            )

        # Vérifier que le patient a consulté ce médecin
        has_consulted = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_id,
            Appointment.patient_id == prescription_data.patient_id
        ).first()

        if not has_consulted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Vous ne pouvez prescrire qu'à vos patients"
            )

        appointment_id = prescription_data.appointment_id
        if appointment_id:
            appointment = db.query(Appointment).filter(
                Appointment.id == appointment_id,
                Appointment.doctor_id == doctor_id,
                Appointment.patient_id == prescription_data.patient_id
            ).first()
            if not appointment:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Le rendez-vous lié à l'ordonnance est invalide"
                )

        prescription_number = DoctorService._generate_prescription_number(db)

        prescription = ElectronicPrescription(
            doctor_id=doctor_id,
            patient_id=prescription_data.patient_id,
            appointment_id=appointment_id,
            prescription_number=prescription_number,
            medications=[item.model_dump() for item in prescription_data.medications],
            instructions=prescription_data.instructions,
            expires_at=prescription_data.expires_at,
            status=PrescriptionStatusEnum.ISSUED,
            issued_at=datetime.now(timezone.utc)
        )

        db.add(prescription)
        db.commit()
        db.refresh(prescription)

        # Charger les relations utiles pour la réponse
        prescription.patient

        return prescription

    # ========== Paramètres ==========

    @staticmethod
    def get_doctor_settings(db: Session, doctor_id: int) -> DoctorSettings:
        """Obtenir les paramètres du médecin"""
        settings = db.query(DoctorSettings).filter(
            DoctorSettings.doctor_id == doctor_id
        ).first()
        
        if not settings:
            # Créer des paramètres par défaut si inexistants
            settings = DoctorSettings(doctor_id=doctor_id)
            db.add(settings)
            db.commit()
            db.refresh(settings)
        
        return settings

    @staticmethod
    def update_doctor_settings(
        db: Session,
        doctor_id: int,
        settings_data: DoctorSettingsUpdate
    ) -> DoctorSettings:
        """Mettre à jour les paramètres du médecin"""
        settings = DoctorService.get_doctor_settings(db, doctor_id)
        
        update_data = settings_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(settings, field, value)
        
        db.commit()
        db.refresh(settings)
        return settings
