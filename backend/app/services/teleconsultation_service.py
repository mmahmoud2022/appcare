"""
Service pour la génération de liens de téléconsultation
"""
import hashlib
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from app.models.doctor import Appointment, ConsultationTypeEnum


class TeleconsultationService:
    """Service pour la gestion des téléconsultations via Jitsi Meet"""
    
    # Configuration Jitsi Meet (open-source)
    JITSI_DOMAIN = "meet.jit.si"  # Utiliser l'instance publique ou self-hosted
    
    @staticmethod
    def generate_meet_link(appointment: Appointment, is_doctor: bool = False) -> Optional[str]:
        """
        Génère un lien Jitsi Meet unique pour une téléconsultation
        
        Args:
            appointment: L'objet rendez-vous
            is_doctor: True si le lien est pour le médecin (modérateur), False pour le patient
            
        Returns:
            URL Jitsi Meet ou None si ce n'est pas une téléconsultation
        """
        # Générer un lien uniquement pour les téléconsultations
        if appointment.consultation_type != ConsultationTypeEnum.TELECONSULTATION:
            return None
        
        # Créer un identifiant unique et sécurisé pour la salle
        room_identifier = TeleconsultationService._generate_room_id(
            appointment_id=appointment.id,
            doctor_id=appointment.doctor_id,
            patient_id=appointment.patient_id,
            appointment_date=appointment.appointment_date
        )
        
        # Construire l'URL de base Jitsi Meet
        base_url = f"https://{TeleconsultationService.JITSI_DOMAIN}/{room_identifier}"
        
        # Ajouter des paramètres pour définir le rôle
        if is_doctor:
            # Paramètres pour le médecin (modérateur/hôte)
            params = {
                'userInfo.displayName': f"Dr. {appointment.doctor.user.first_name} {appointment.doctor.user.last_name}" if appointment.doctor else "Docteur",
                'userInfo.email': appointment.doctor.user.email if appointment.doctor else "",
                'config.startWithAudioMuted': 'false',
                'config.startWithVideoMuted': 'false',
                'config.prejoinPageEnabled': 'false',  # Pas d'écran d'attente pour le médecin
                'moderator': 'true'  # Marquer comme modérateur
            }
        else:
            # Paramètres pour le patient
            params = {
                'userInfo.displayName': f"{appointment.patient.first_name} {appointment.patient.last_name}" if appointment.patient else "Patient",
                'userInfo.email': appointment.patient.email if appointment.patient else "",
                'config.startWithAudioMuted': 'true',
                'config.startWithVideoMuted': 'true',
                'config.prejoinPageEnabled': 'true'  # Écran d'attente pour le patient
            }
        
        # Encoder les paramètres et construire l'URL complète
        query_string = urlencode(params, safe='@')
        meet_link = f"{base_url}#{query_string}"
        
        return meet_link
    
    @staticmethod
    def _generate_room_id(
        appointment_id: int,
        doctor_id: int,
        patient_id: int,
        appointment_date: datetime
    ) -> str:
        """
        Génère un identifiant de salle unique et sécurisé
        
        Args:
            appointment_id: ID du rendez-vous
            doctor_id: ID du médecin
            patient_id: ID du patient
            appointment_date: Date du rendez-vous
            
        Returns:
            Identifiant de salle unique
        """
        # Créer une chaîne à hasher avec des informations uniques
        date_str = appointment_date.strftime("%Y%m%d%H%M")
        raw_string = f"sante-{appointment_id}-{doctor_id}-{patient_id}-{date_str}"
        
        # Hasher pour créer un identifiant court et sécurisé
        hash_object = hashlib.sha256(raw_string.encode())
        hash_hex = hash_object.hexdigest()[:16]  # Prendre les 16 premiers caractères
        
        # Format: sante-consult-{hash}
        room_id = f"sante-consult-{hash_hex}"
        
        return room_id
    
    @staticmethod
    def should_generate_meet_link(consultation_type: ConsultationTypeEnum) -> bool:
        """
        Vérifie si un lien de téléconsultation doit être généré
        
        Args:
            consultation_type: Type de consultation
            
        Returns:
            True si un lien doit être généré
        """
        return consultation_type == ConsultationTypeEnum.TELECONSULTATION