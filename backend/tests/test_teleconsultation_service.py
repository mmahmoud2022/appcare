"""
Tests for the teleconsultation service
"""
import pytest
from datetime import datetime, timezone
from app.services.teleconsultation_service import TeleconsultationService
from app.models.doctor import Appointment, ConsultationTypeEnum


class TestTeleconsultationService:
    """Test cases for TeleconsultationService"""
    
    def test_should_generate_meet_link_for_teleconsultation(self):
        """Test that meet link generation is needed for teleconsultation type"""
        assert TeleconsultationService.should_generate_meet_link(
            ConsultationTypeEnum.TELECONSULTATION
        ) is True
    
    def test_should_not_generate_meet_link_for_in_person(self):
        """Test that meet link generation is not needed for in-person type"""
        assert TeleconsultationService.should_generate_meet_link(
            ConsultationTypeEnum.IN_PERSON
        ) is False
    
    def test_should_not_generate_meet_link_for_both(self):
        """Test that meet link generation is not needed for both type"""
        assert TeleconsultationService.should_generate_meet_link(
            ConsultationTypeEnum.BOTH
        ) is False
    
    def test_generate_meet_link_creates_valid_url(self):
        """Test that a valid Jitsi Meet URL is generated"""
        # Create a mock appointment
        appointment = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        meet_link = TeleconsultationService.generate_meet_link(appointment)
        
        # Check that a link was generated
        assert meet_link is not None
        
        # Check that it's a valid Jitsi Meet URL
        assert meet_link.startswith("https://meet.jit.si/")
        
        # Check that it contains the expected room identifier prefix
        assert "sante-consult-" in meet_link
    
    def test_generate_meet_link_returns_none_for_in_person(self):
        """Test that no link is generated for in-person appointments"""
        appointment = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.IN_PERSON
        )
        
        meet_link = TeleconsultationService.generate_meet_link(appointment)
        
        assert meet_link is None
    
    def test_generate_meet_link_is_deterministic(self):
        """Test that the same appointment generates the same link"""
        appointment1 = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        appointment2 = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        link1 = TeleconsultationService.generate_meet_link(appointment1)
        link2 = TeleconsultationService.generate_meet_link(appointment2)
        
        # Same appointment should generate same link
        assert link1 == link2
    
    def test_generate_meet_link_is_unique_per_appointment(self):
        """Test that different appointments generate different links"""
        appointment1 = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        appointment2 = Appointment(
            id=124,  # Different ID
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        link1 = TeleconsultationService.generate_meet_link(appointment1)
        link2 = TeleconsultationService.generate_meet_link(appointment2)
        
        # Different appointments should generate different links
        assert link1 != link2
    
    def test_room_id_generation_is_secure(self):
        """Test that room IDs are hashed and don't expose sensitive info"""
        appointment = Appointment(
            id=123,
            doctor_id=456,
            patient_id=789,
            appointment_date=datetime(2025, 11, 15, 10, 30, tzinfo=timezone.utc),
            consultation_type=ConsultationTypeEnum.TELECONSULTATION
        )
        
        room_id = TeleconsultationService._generate_room_id(
            appointment_id=appointment.id,
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_date=appointment.appointment_date
        )
        
        # Room ID should not contain raw IDs
        assert "123" not in room_id
        assert "456" not in room_id
        assert "789" not in room_id
        
        # Room ID should start with prefix
        assert room_id.startswith("sante-consult-")
        
        # Room ID should have reasonable length (prefix + 16 char hash)
        assert len(room_id) == len("sante-consult-") + 16
