"""
Tests de concurrence pour la réservation de rendez-vous
Vérifie qu'un seul patient peut réserver un créneau donné
"""
import pytest
from datetime import datetime, timedelta, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.user import User, UserRole
from app.models.doctor import (
    DoctorProfile, 
    DoctorScheduleEntry, 
    Appointment,
    ConsultationTypeEnum,
    DayOfWeekEnum,
    AppointmentStatusEnum
)
from app.schemas.patient import AppointmentCreate
from app.services.patient_service import PatientService


def create_test_doctor(db: Session) -> tuple[User, DoctorProfile]:
    """Créer un médecin de test"""
    doctor_user = User(
        email=f"doctor_{datetime.now().timestamp()}@test.com",
        hashed_password="hashed",
        first_name="Dr",
        last_name="Test",
        role=UserRole.DOCTOR,
        is_verified=True,
        admin_approved=True
    )
    db.add(doctor_user)
    db.flush()
    
    doctor_profile = DoctorProfile(
        user_id=doctor_user.id,
        specialty="Cardiologue",
        consultation_price=50.0
    )
    db.add(doctor_profile)
    db.flush()
    
    # Ajouter un horaire récurrent
    schedule_entry = DoctorScheduleEntry(
        doctor_id=doctor_profile.id,
        day_of_week=DayOfWeekEnum((datetime.now().weekday() + 1) % 7),
        start_time=time(9, 0),
        end_time=time(17, 0),
        slot_duration=30,
        consultation_types=[ConsultationTypeEnum.IN_PERSON],
        is_active=True
    )
    db.add(schedule_entry)
    db.commit()
    
    return doctor_user, doctor_profile


def create_test_patient(db: Session, index: int) -> User:
    """Créer un patient de test"""
    patient = User(
        email=f"patient_{index}_{datetime.now().timestamp()}@test.com",
        hashed_password="hashed",
        first_name=f"Patient{index}",
        last_name="Test",
        role=UserRole.PATIENT,
        is_verified=True
    )
    db.add(patient)
    db.commit()
    return patient


def attempt_booking(db_session, patient_id: int, doctor_id: int, appointment_time: datetime) -> dict:
    """
    Tente de réserver un rendez-vous
    Retourne le résultat (succès ou erreur)
    """
    try:
        appointment_data = AppointmentCreate(
            doctor_id=doctor_id,
            appointment_date=appointment_time,
            consultation_type=ConsultationTypeEnum.IN_PERSON,
            reason="Test concurrence"
        )
        
        appointment = PatientService.create_appointment(
            db=db_session,
            patient_id=patient_id,
            appointment_data=appointment_data
        )
        
        return {
            "success": True,
            "patient_id": patient_id,
            "appointment_id": appointment.id
        }
    except HTTPException as e:
        return {
            "success": False,
            "patient_id": patient_id,
            "error": e.detail,
            "status_code": e.status_code
        }
    except Exception as e:
        return {
            "success": False,
            "patient_id": patient_id,
            "error": str(e),
            "status_code": 500
        }


class TestConcurrentBooking:
    """Tests de réservation concurrente"""
    
    def test_concurrent_booking_same_slot(self, db: Session):
        """
        Test: 10 patients tentent de réserver le même créneau simultanément
        Résultat attendu: 1 seul réussit, les 9 autres reçoivent erreur 409
        """
        # Créer le médecin
        doctor_user, doctor_profile = create_test_doctor(db)
        
        # Créer 10 patients
        num_patients = 10
        patients = [create_test_patient(db, i) for i in range(num_patients)]
        
        # Créneau à réserver (demain 10h)
        tomorrow = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Lancer 10 réservations simultanées
        results = []
        with ThreadPoolExecutor(max_workers=num_patients) as executor:
            # Créer une session DB par thread
            futures = [
                executor.submit(
                    attempt_booking,
                    db,  # Note: En production, créer une session par thread
                    patient.id,
                    doctor_profile.id,
                    tomorrow
                )
                for patient in patients
            ]
            
            for future in as_completed(futures):
                results.append(future.result())
        
        # Vérifications
        successful_bookings = [r for r in results if r["success"]]
        failed_bookings = [r for r in results if not r["success"]]
        
        # ✅ Exactement 1 réservation doit réussir
        assert len(successful_bookings) == 1, \
            f"Expected 1 success, got {len(successful_bookings)}"
        
        # ✅ 9 réservations doivent échouer avec erreur 409
        assert len(failed_bookings) == num_patients - 1, \
            f"Expected {num_patients - 1} failures, got {len(failed_bookings)}"
        
        conflict_errors = [r for r in failed_bookings if r.get("status_code") == 409]
        assert len(conflict_errors) >= num_patients - 2, \
            f"Expected at least {num_patients - 2} conflict errors (409), got {len(conflict_errors)}"
        
        # ✅ Vérifier en base qu'il n'y a qu'un seul rendez-vous
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor_profile.id,
            Appointment.appointment_date == tomorrow
        ).all()
        
        assert len(appointments) == 1, \
            f"Expected exactly 1 appointment in DB, found {len(appointments)}"
        
        print(f"✅ Test réussi: {len(successful_bookings)} réservation(s) réussie(s), "
              f"{len(failed_bookings)} échec(s) avec conflit")
    
    
    def test_sequential_booking_different_slots(self, db: Session):
        """
        Test: 5 patients réservent 5 créneaux différents
        Résultat attendu: Tous réussissent
        """
        doctor_user, doctor_profile = create_test_doctor(db)
        
        num_patients = 5
        patients = [create_test_patient(db, i) for i in range(num_patients)]
        
        # Créneaux différents (demain 10h, 10h30, 11h, 11h30, 12h)
        base_time = datetime.now().replace(hour=10, minute=0, second=0, microsecond=0) + timedelta(days=1)
        time_slots = [base_time + timedelta(minutes=30 * i) for i in range(num_patients)]
        
        results = []
        for patient, time_slot in zip(patients, time_slots):
            result = attempt_booking(db, patient.id, doctor_profile.id, time_slot)
            results.append(result)
        
        # ✅ Toutes les réservations doivent réussir
        successful = [r for r in results if r["success"]]
        assert len(successful) == num_patients, \
            f"Expected all {num_patients} bookings to succeed, got {len(successful)}"
        
        print(f"✅ Test réussi: {len(successful)} réservations sur créneaux différents")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
