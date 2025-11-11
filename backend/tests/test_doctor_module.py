"""
Tests unitaires pour le module Doctor
"""
import pytest
from datetime import date, time, datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.doctor import (
    DoctorProfile,
    DoctorScheduleEntry,
    DoctorBlockedSlot,
    Appointment,
    SpecialtyEnum,
    ConsultationTypeEnum,
    AppointmentStatusEnum,
)
from app.services.doctor_service import DoctorService
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
    AppointmentStatusUpdate,
)


class TestDoctorProfile:
    """Tests pour la gestion des profils médecins"""
    
    def test_create_doctor_profile_success(self, db: Session, doctor_user: User):
        """Test de création d'un profil médecin"""
        profile_data = DoctorProfileCreate(
            specialty=SpecialtyEnum.CARDIOLOGIST,
            rpps_number="12345678901",
            office_city="Paris",
            biography="Test biography",
            languages=["français", "anglais"],
            education=[],
            experience_years=10,
            consultation_price=50.0
        )
        
        profile = DoctorService.create_doctor_profile(db, doctor_user.id, profile_data)
        
        assert profile.id is not None
        assert profile.user_id == doctor_user.id
        assert profile.specialty == SpecialtyEnum.CARDIOLOGIST
        assert profile.rpps_number == "12345678901"
    
    def test_create_duplicate_rpps_fails(self, db: Session, doctor_user: User, another_doctor_user: User):
        """Test qu'on ne peut pas créer deux profils avec le même RPPS"""
        profile_data = DoctorProfileCreate(
            specialty=SpecialtyEnum.CARDIOLOGIST,
            rpps_number="12345678901",
            office_city="Paris",
            biography="Test",
            languages=["français"],
            education=[],
            experience_years=5,
            consultation_price=50.0
        )
        
        # Créer le premier profil
        DoctorService.create_doctor_profile(db, doctor_user.id, profile_data)
        
        # Tenter de créer un second profil avec le même RPPS
        with pytest.raises(HTTPException) as exc_info:
            DoctorService.create_doctor_profile(db, another_doctor_user.id, profile_data)
        
        assert exc_info.value.status_code == 400
        assert "RPPS" in str(exc_info.value.detail)
    
    def test_create_profile_requires_doctor_role(self, db: Session, patient_user: User):
        """Test qu'un patient ne peut pas créer un profil médecin"""
        profile_data = DoctorProfileCreate(
            specialty=SpecialtyEnum.CARDIOLOGIST,
            rpps_number="12345678901",
            office_city="Paris",
            biography="Test",
            languages=["français"],
            education=[],
            experience_years=5,
            consultation_price=50.0
        )
        
        with pytest.raises(HTTPException) as exc_info:
            DoctorService.create_doctor_profile(db, patient_user.id, profile_data)
        
        assert exc_info.value.status_code == 403
    
    def test_update_doctor_profile(self, db: Session, doctor_profile: DoctorProfile):
        """Test de mise à jour d'un profil"""
        update_data = DoctorProfileUpdate(
            biography="Updated biography",
            consultation_price=60.0,
            accepts_new_patients=False
        )
        
        updated_profile = DoctorService.update_doctor_profile(
            db, doctor_profile.user_id, update_data
        )
        
        assert updated_profile.biography == "Updated biography"
        assert updated_profile.consultation_price == 60.0
        assert updated_profile.accepts_new_patients is False
    
    def test_get_public_profile(self, db: Session, doctor_profile: DoctorProfile):
        """Test de récupération d'un profil public"""
        profile = DoctorService.get_public_doctor_profile(db, doctor_profile.id)
        
        assert profile.id == doctor_profile.id
        assert profile.is_public is True


def _next_date_for_schedule_day(schedule_day: int) -> date:
    """Retourne la prochaine date future correspondant au jour de planning fourni (0=dimanche)."""
    today = date.today()
    today_schedule_day = (today.weekday() + 1) % 7
    delta = (schedule_day - today_schedule_day + 7) % 7
    if delta == 0:
        delta = 7
    return today + timedelta(days=delta)


class TestDoctorSchedule:
    """Tests pour la gestion du planning récurrent et des créneaux générés"""

    def test_create_schedule_entry(self, db: Session, doctor_profile: DoctorProfile):
        entry_data = ScheduleEntryCreate(
            day_of_week=1,
            start_time=time(9, 0),
            end_time=time(12, 0),
            slot_duration=30,
            break_duration=0,
            consultation_type=ConsultationTypeEnum.IN_PERSON,
            location="Cabinet Paris",
        )

        entry = DoctorService.create_schedule_entry(db, doctor_profile.id, entry_data)

        assert entry.id is not None
        assert entry.doctor_id == doctor_profile.id
        assert entry.slot_duration == 30
        assert entry.consultation_type == ConsultationTypeEnum.IN_PERSON

    def test_update_schedule_entry(self, db: Session, doctor_profile: DoctorProfile):
        entry = DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(12, 0),
                slot_duration=30,
                break_duration=0,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )

        updated = DoctorService.update_schedule_entry(
            db,
            doctor_profile.id,
            entry.id,
            ScheduleEntryUpdate(slot_duration=45, break_duration=10, location="Visio"),
        )

        assert updated.slot_duration == 45
        assert updated.break_duration == 10
        assert updated.location == "Visio"

    def test_create_overlapping_schedule_entry_fails(self, db: Session, doctor_profile: DoctorProfile):
        DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(12, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )

        with pytest.raises(HTTPException) as exc_info:
            DoctorService.create_schedule_entry(
                db,
                doctor_profile.id,
                ScheduleEntryCreate(
                    day_of_week=1,
                    start_time=time(10, 0),
                    end_time=time(11, 0),
                    slot_duration=30,
                    consultation_type=ConsultationTypeEnum.IN_PERSON,
                ),
            )

        assert exc_info.value.status_code == 400

    def test_list_schedule_entries(self, db: Session, doctor_profile: DoctorProfile):
        DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(11, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )
        DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=3,
                start_time=time(14, 0),
                end_time=time(17, 0),
                slot_duration=45,
                consultation_type=ConsultationTypeEnum.TELECONSULTATION,
            ),
        )

        entries = DoctorService.list_schedule_entries(db, doctor_profile.id)

        assert len(entries) == 2
        assert entries[0].day_of_week <= entries[1].day_of_week

    def test_delete_schedule_entry(self, db: Session, doctor_profile: DoctorProfile):
        entry = DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(10, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )

        DoctorService.delete_schedule_entry(db, doctor_profile.id, entry.id)

        entries = DoctorService.list_schedule_entries(db, doctor_profile.id)
        assert len(entries) == 0

    def test_generate_availability_slots(self, db: Session, doctor_profile: DoctorProfile):
        entry = DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(11, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )
        target_date = _next_date_for_schedule_day(entry.day_of_week)

        slots = DoctorService.get_doctor_availability_slots(db, doctor_profile.id, target_date)

        assert len(slots) == 4  # 9:00, 9:30, 10:00, 10:30
        assert slots[0].schedule_entry_id == entry.id
        assert slots[0].start.time() == time(9, 0)

    def test_slots_skip_blocked_periods(self, db: Session, doctor_profile: DoctorProfile):
        entry = DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(11, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )
        target_date = _next_date_for_schedule_day(entry.day_of_week)

        blocked = DoctorBlockedSlot(
            doctor_id=doctor_profile.id,
            start_datetime=datetime.combine(target_date, time(9, 30)),
            end_datetime=datetime.combine(target_date, time(10, 0)),
            reason="Réunion",
        )
        db.add(blocked)
        db.commit()

        slots = DoctorService.get_doctor_availability_slots(db, doctor_profile.id, target_date)

        start_times = {slot.start.time() for slot in slots}
        assert time(9, 30) not in start_times

    def test_slots_skip_existing_appointments(self, db: Session, doctor_profile: DoctorProfile, patient_user: User):
        entry = DoctorService.create_schedule_entry(
            db,
            doctor_profile.id,
            ScheduleEntryCreate(
                day_of_week=1,
                start_time=time(9, 0),
                end_time=time(11, 0),
                slot_duration=30,
                consultation_type=ConsultationTypeEnum.IN_PERSON,
            ),
        )
        target_date = _next_date_for_schedule_day(entry.day_of_week)
        slot_start = datetime.combine(target_date, entry.start_time)

        appointment = Appointment(
            doctor_id=doctor_profile.id,
            patient_id=patient_user.id,
            appointment_date=slot_start,
            schedule_entry_id=entry.id,
            duration=entry.slot_duration,
            status=AppointmentStatusEnum.PENDING,
            consultation_type=ConsultationTypeEnum.IN_PERSON,
        )
        db.add(appointment)
        db.commit()

        slots = DoctorService.get_doctor_availability_slots(db, doctor_profile.id, target_date)

        start_times = {slot.start.time() for slot in slots}
        assert time(9, 0) not in start_times


class TestAppointments:
    """Tests pour la gestion des rendez-vous"""
    
    def test_get_doctor_appointments(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test de récupération des rendez-vous"""
        appointments, total = DoctorService.get_doctor_appointments(
            db, doctor_profile.id
        )
        
        assert total >= 1
        assert len(appointments) >= 1
        assert appointments[0].doctor_id == doctor_profile.id
    
    def test_get_appointment_details(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test de récupération des détails d'un rendez-vous"""
        details = DoctorService.get_appointment_details(
            db, doctor_profile.id, appointment.id
        )
        
        assert details.id == appointment.id
        assert details.doctor_id == doctor_profile.id
    
    def test_update_appointment_status(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test de mise à jour du statut d'un rendez-vous"""
        status_update = AppointmentStatusUpdate(
            status=AppointmentStatusEnum.COMPLETED,
            notes="Consultation terminée avec succès"
        )
        
        updated = DoctorService.update_appointment_status(
            db, doctor_profile.id, appointment.id, status_update
        )
        
        assert updated.status == AppointmentStatusEnum.COMPLETED
        assert updated.notes == "Consultation terminée avec succès"
        assert updated.completed_at is not None
    
    def test_completed_appointment_increments_counter(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test que marquer un RDV comme terminé incrémente le compteur"""
        initial_count = doctor_profile.total_consultations
        
        status_update = AppointmentStatusUpdate(
            status=AppointmentStatusEnum.COMPLETED
        )
        
        DoctorService.update_appointment_status(
            db, doctor_profile.id, appointment.id, status_update
        )
        
        db.refresh(doctor_profile)
        assert doctor_profile.total_consultations == initial_count + 1


class TestDoctorStatistics:
    """Tests pour les statistiques"""
    
    def test_get_statistics(self, db: Session, doctor_profile: DoctorProfile):
        """Test de récupération des statistiques"""
        stats = DoctorService.get_doctor_statistics(db, doctor_profile.id)
        
        assert stats.total_consultations >= 0
        assert stats.average_rating >= 0
        assert stats.cancellation_rate >= 0
        assert stats.total_revenue >= 0


class TestDoctorPatients:
    """Tests pour la gestion des patients"""
    
    def test_get_doctor_patients(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test de récupération de la liste des patients"""
        appointment.status = AppointmentStatusEnum.COMPLETED
        db.commit()

        patients, total = DoctorService.get_doctor_patients(db, doctor_profile.id)
        
        assert total >= 1
        assert len(patients) >= 1
    
    def test_get_patient_medical_record(self, db: Session, doctor_profile: DoctorProfile, appointment: Appointment):
        """Test de récupération du dossier médical"""
        record = DoctorService.get_patient_medical_record(
            db, doctor_profile.id, appointment.patient_id
        )
        
        assert record["patient"].id == appointment.patient_id
        assert len(record["appointments"]) >= 1
        assert record["total_consultations"] >= 0
    
    def test_cannot_access_non_patient_record(self, db: Session, doctor_profile: DoctorProfile, patient_user: User):
        """Test qu'on ne peut pas accéder au dossier d'un non-patient"""
        with pytest.raises(HTTPException) as exc_info:
            DoctorService.get_patient_medical_record(
                db, doctor_profile.id, patient_user.id
            )
        
        assert exc_info.value.status_code == 403


# Fixtures pytest
@pytest.fixture
def doctor_user(db: Session):
    """Créer un utilisateur médecin de test"""
    user = User(
        email="doctor@test.com",
        hashed_password="hashed_password",
        first_name="John",
        last_name="Doe",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
        admin_approved=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def another_doctor_user(db: Session):
    """Créer un autre utilisateur médecin"""
    user = User(
        email="doctor2@test.com",
        hashed_password="hashed_password",
        first_name="Jane",
        last_name="Smith",
        role=UserRole.DOCTOR,
        is_active=True,
        is_verified=True,
        admin_approved=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def patient_user(db: Session):
    """Créer un utilisateur patient de test"""
    user = User(
        email="patient@test.com",
        hashed_password="hashed_password",
        first_name="Marie",
        last_name="Martin",
        role=UserRole.PATIENT,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def doctor_profile(db: Session, doctor_user: User):
    """Créer un profil médecin de test"""
    profile = DoctorProfile(
        user_id=doctor_user.id,
        specialty=SpecialtyEnum.CARDIOLOGIST,
        rpps_number="12345678901",
        office_city="Paris",
        biography="Test doctor",
        languages=["français"],
        education=[],
        experience_years=10,
        consultation_price=50.0,
        is_public=True
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@pytest.fixture
def schedule_entry(db: Session, doctor_profile: DoctorProfile):
    """Créer une configuration récurrente de planning"""
    entry = DoctorScheduleEntry(
        doctor_id=doctor_profile.id,
        day_of_week=1,
        start_time=time(9, 0),
        end_time=time(12, 0),
        slot_duration=30,
        break_duration=0,
        consultation_type=ConsultationTypeEnum.IN_PERSON,
        location="Cabinet Paris",
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@pytest.fixture
def appointment(
    db: Session,
    doctor_profile: DoctorProfile,
    patient_user: User,
    schedule_entry: DoctorScheduleEntry,
):
    """Créer un rendez-vous de test"""
    target_date = _next_date_for_schedule_day(schedule_entry.day_of_week)
    start_datetime = datetime.combine(target_date, schedule_entry.start_time)

    appointment = Appointment(
        doctor_id=doctor_profile.id,
        patient_id=patient_user.id,
        appointment_date=start_datetime,
        schedule_entry_id=schedule_entry.id,
        consultation_type=ConsultationTypeEnum.IN_PERSON,
        status=AppointmentStatusEnum.PENDING,
        duration=schedule_entry.slot_duration,
        reason="Consultation de routine",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment
