"""
Endpoints pour le module Doctor
Routes pour la gestion des profils, disponibilités, rendez-vous, messages, avis, etc.
"""
from fastapi import APIRouter, Depends, status, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.doctor import AppointmentStatusEnum, PaymentStatusEnum, Appointment, ConsultationTypeEnum
from app.services.doctor_service import DoctorService
from app.schemas.doctor import (
    DoctorProfileCreate,
    DoctorProfileUpdate,
    DoctorProfileResponse,
    DoctorPublicProfile,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
    ScheduleEntryResponse,
    AppointmentResponse,
    AppointmentStatusUpdate,
    MessageCreate,
    MessageResponse,
    ReviewResponse,
    ReviewResponseCreate,
    PaymentResponse,
    DocumentResponse,
    ElectronicPrescriptionCreate,
    ElectronicPrescriptionResponse,
    ElectronicPrescriptionListResponse,
    DoctorSettingsUpdate,
    DoctorSettingsResponse,
    DoctorStatistics,
    PatientBasicInfo,
    PatientInfo,
    AppointmentListResponse,
    MessageListResponse,
    ReviewListResponse,
    PaymentListResponse,
    PatientListResponse,
    BlockedSlotCreate,
    BlockedSlotResponse,
    AvailableSlotResponse,
)

router = APIRouter(prefix="/doctors", tags=["doctors"])


# ========== 1️⃣ Créer un profil praticien ==========
@router.post("/", response_model=DoctorProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_profile(
    profile_data: DoctorProfileCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Créer un profil professionnel pour un médecin.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.create_doctor_profile(db, current_user.id, profile_data)
    
    # Enrichir avec les données utilisateur
    response = DoctorProfileResponse.model_validate(profile)
    response.first_name = current_user.first_name
    response.last_name = current_user.last_name
    response.email = current_user.email
    
    return response


# ========== 2️⃣ Obtenir le profil du médecin connecté ==========
@router.get("/me", response_model=DoctorProfileResponse)
async def get_my_doctor_profile(
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir le profil professionnel du médecin connecté.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    
    # Enrichir avec les données utilisateur
    response = DoctorProfileResponse.model_validate(profile)
    response.first_name = current_user.first_name
    response.last_name = current_user.last_name
    response.email = current_user.email
    
    return response


# ========== 3️⃣ Mettre à jour le profil du médecin ==========
@router.patch("/me", response_model=DoctorProfileResponse)
async def update_my_doctor_profile(
    profile_data: DoctorProfileUpdate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour le profil professionnel du médecin connecté.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.update_doctor_profile(db, current_user.id, profile_data)
    
    # Enrichir avec les données utilisateur
    response = DoctorProfileResponse.model_validate(profile)
    response.first_name = current_user.first_name
    response.last_name = current_user.last_name
    response.email = current_user.email
    
    return response


# ========== 6️⃣ Créer un créneau de disponibilité ==========
@router.post("/schedule", response_model=ScheduleEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule_entry(
    schedule_entry_data: ScheduleEntryCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Créer un créneau de disponibilité dans l'agenda.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    entry = DoctorService.create_schedule_entry(db, profile.id, schedule_entry_data)
    return ScheduleEntryResponse.model_validate(entry)


# ========== Mettre à jour un créneau de disponibilité ==========
@router.patch("/schedule/{schedule_entry_id}", response_model=ScheduleEntryResponse)
async def update_schedule_entry(
    schedule_entry_id: int,
    schedule_entry_data: ScheduleEntryUpdate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """Mettre à jour un créneau de disponibilité existant."""
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    entry = DoctorService.update_schedule_entry(
        db, profile.id, schedule_entry_id, schedule_entry_data
    )
    return ScheduleEntryResponse.model_validate(entry)


# ========== 7️⃣ Supprimer un créneau de disponibilité ==========
@router.delete("/schedule/{schedule_entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_entry(
    schedule_entry_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Supprimer un créneau de disponibilité non réservé.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    DoctorService.delete_schedule_entry(db, profile.id, schedule_entry_id)
    return None


# ========== 8️⃣ Liste des rendez-vous du médecin ==========
@router.get("/appointments", response_model=AppointmentListResponse)
async def get_my_appointments(
    status_filter: Optional[AppointmentStatusEnum] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste des rendez-vous du médecin connecté.
    
    Filtres disponibles : statut, date de début, date de fin.
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    appointments, total = DoctorService.get_doctor_appointments(
        db, profile.id, status_filter, start_date, end_date, page, page_size
    )
    
    # Enrichir avec les données patient
    items = []
    for appt in appointments:
        response = AppointmentResponse.model_validate(appt)
        # Créer l'objet patient pour le frontend
        if appt.patient:
            response.patient = PatientInfo(
                id=appt.patient.id,
                email=appt.patient.email,
                full_name=appt.patient.full_name,
                phone=appt.patient.phone
            )
        # Garder aussi les champs individuels pour compatibilité
        response.patient_first_name = appt.patient.first_name
        response.patient_last_name = appt.patient.last_name
        response.patient_phone = appt.patient.phone
        items.append(response)
    
    return AppointmentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ========== 9️⃣ Détails d'un rendez-vous ==========
@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment_details(
    appointment_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir les détails d'un rendez-vous spécifique.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    appointment = DoctorService.get_appointment_details(db, profile.id, appointment_id)
    
    # Enrichir avec les données patient
    response = AppointmentResponse.model_validate(appointment)
    if appointment.patient:
        response.patient = PatientInfo(
            id=appointment.patient.id,
            email=appointment.patient.email,
            full_name=appointment.patient.full_name,
            phone=appointment.patient.phone
        )
    response.patient_first_name = appointment.patient.first_name
    response.patient_last_name = appointment.patient.last_name
    response.patient_phone = appointment.patient.phone
    
    return response


# ========== 🔟 Modifier le statut d'un rendez-vous ==========
@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    status_update: AppointmentStatusUpdate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Modifier le statut d'un rendez-vous (confirmé, terminé, annulé, absent).
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    appointment = DoctorService.update_appointment_status(
        db, profile.id, appointment_id, status_update
    )
    
    # Enrichir avec les données patient
    response = AppointmentResponse.model_validate(appointment)
    if appointment.patient:
        response.patient = PatientInfo(
            id=appointment.patient.id,
            email=appointment.patient.email,
            full_name=appointment.patient.full_name,
            phone=appointment.patient.phone
        )
    response.patient_first_name = appointment.patient.first_name
    response.patient_last_name = appointment.patient.last_name
    response.patient_phone = appointment.patient.phone
    
    return response


# ========== 🗑️ Supprimer un rendez-vous ==========
@router.delete("/appointments/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Marquer un rendez-vous comme supprimé (soft delete).
    
    Le rendez-vous reste en base de données pour les statistiques
    mais n'apparaît plus dans les listes.
    
    Nécessite le rôle DOCTOR.
    """
    from datetime import datetime
    
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    
    # Vérifier que le rendez-vous appartient au médecin
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.doctor_id == profile.id,
        Appointment.is_deleted == False  # Ne pas supprimer deux fois
    ).first()
    
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rendez-vous non trouvé"
        )
    
    # Soft delete: marquer comme supprimé
    appointment.is_deleted = True
    appointment.deleted_at = datetime.utcnow()
    appointment.deleted_by = current_user.id
    
    db.commit()
    
    return None


# ========== 11️⃣ Liste des patients suivis ==========
@router.get("/patients", response_model=PatientListResponse)
async def get_my_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste des patients ayant consulté le médecin.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    patients, total = DoctorService.get_doctor_patients(db, profile.id, page, page_size)
    
    items = [PatientBasicInfo(**patient) for patient in patients]
    
    return PatientListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ========== 12️⃣ Dossier médical d'un patient ==========
@router.get("/patients/{patient_id}", response_model=dict)
async def get_patient_medical_record(
    patient_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir le dossier médical complet d'un patient.
    
    Nécessite le rôle DOCTOR et que le patient ait consulté ce médecin.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    record = DoctorService.get_patient_medical_record(db, profile.id, patient_id)

    prescriptions = []
    for prescription in record["prescriptions"]:
        response = ElectronicPrescriptionResponse.model_validate(prescription)
        if prescription.patient:
            response.patient_first_name = prescription.patient.first_name
            response.patient_last_name = prescription.patient.last_name
        prescriptions.append(response)
    
    return {
        "patient": {
            "id": record["patient"].id,
            "first_name": record["patient"].first_name,
            "last_name": record["patient"].last_name,
            "email": record["patient"].email,
            "phone": record["patient"].phone,
            "date_of_birth": record["patient"].date_of_birth,
            "gender": record["patient"].gender,
            "address_line1": record["patient"].address_line1,
            "city": record["patient"].city,
            "postal_code": record["patient"].postal_code,
        },
        "appointments": [AppointmentResponse.model_validate(a) for a in record["appointments"]],
        "documents": [DocumentResponse.model_validate(d) for d in record["documents"]],
        "prescriptions": prescriptions,
        "total_consultations": record["total_consultations"]
    }


# ========== 🗑️ Supprimer un patient ==========
@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(
    patient_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Supprimer un patient et TOUTES ses données associées.
    
    ⚠️ ATTENTION : Cette action supprimera DÉFINITIVEMENT :
    - Tous les rendez-vous avec ce patient
    - Toutes les ordonnances émises
    - Tous les documents partagés
    - Tous les messages échangés
    - Tout l'historique médical
    
    Cette action est IRRÉVERSIBLE !
    
    Nécessite le rôle DOCTOR et que le patient ait consulté ce médecin.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    
    # Vérifier que le patient a consulté ce médecin
    patient = db.query(User).filter(User.id == patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient non trouvé"
        )
    
    # Vérifier qu'il y a au moins un rendez-vous entre le médecin et le patient
    has_appointments = db.query(Appointment).filter(
        Appointment.doctor_id == profile.id,
        Appointment.patient_id == patient_id
    ).first()
    
    if not has_appointments:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Vous ne pouvez supprimer que les patients que vous avez consultés"
        )
    
    # Supprimer tous les rendez-vous avec ce patient
    db.query(Appointment).filter(
        Appointment.doctor_id == profile.id,
        Appointment.patient_id == patient_id
    ).delete(synchronize_session=False)
    
    # Supprimer les documents partagés (importé plus loin)
    from app.models.doctor import PatientDocument
    db.query(PatientDocument).filter(
        PatientDocument.doctor_id == profile.id,
        PatientDocument.patient_id == patient_id
    ).delete(synchronize_session=False)
    
    # Supprimer les ordonnances
    from app.models.doctor import ElectronicPrescription
    db.query(ElectronicPrescription).filter(
        ElectronicPrescription.doctor_id == profile.id,
        ElectronicPrescription.patient_id == patient_id
    ).delete(synchronize_session=False)
    
    # Supprimer les messages
    from app.models.doctor import DoctorMessage
    db.query(DoctorMessage).filter(
        (DoctorMessage.sender_id == current_user.id) & (DoctorMessage.recipient_id == patient_id) |
        (DoctorMessage.sender_id == patient_id) & (DoctorMessage.recipient_id == current_user.id)
    ).delete(synchronize_session=False)
    
    db.commit()
    
    return None


# ========== 13️⃣ Statistiques d'activité ==========
@router.get("/statistics", response_model=DoctorStatistics)
async def get_my_statistics(
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir les statistiques d'activité du médecin.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    statistics = DoctorService.get_doctor_statistics(db, profile.id)
    return statistics


# ========== 14️⃣ Configurations du compte ==========
@router.put("/settings", response_model=DoctorSettingsResponse)
async def update_my_settings(
    settings_data: DoctorSettingsUpdate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Mettre à jour les paramètres et préférences du compte.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    settings = DoctorService.update_doctor_settings(db, profile.id, settings_data)
    return DoctorSettingsResponse.model_validate(settings)


@router.get("/settings", response_model=DoctorSettingsResponse)
async def get_my_settings(
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir les paramètres actuels du compte.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    settings = DoctorService.get_doctor_settings(db, profile.id)
    return DoctorSettingsResponse.model_validate(settings)


# ========== 15️⃣ Envoyer un document patient ==========
@router.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_patient_document(
    patient_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    document_type: Optional[str] = Form(None),
    appointment_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Uploader un document médical pour un patient.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    document = await DoctorService.upload_patient_document(
        db, profile.id, patient_id, file, title, description, document_type, appointment_id
    )
    
    # Créer la réponse et enrichir avec les données patient
    response = DocumentResponse.model_validate(document)
    patient = db.query(User).filter(User.id == patient_id).first()
    if patient:
        response.patient_first_name = patient.first_name
        response.patient_last_name = patient.last_name
    
    return response


# ========== 16️⃣ Ordonnances électroniques ==========
@router.get("/prescriptions", response_model=ElectronicPrescriptionListResponse)
async def list_my_prescriptions(
    patient_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste des ordonnances électroniques émises.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    prescriptions, total = DoctorService.list_prescriptions(
        db, profile.id, page, page_size, patient_id
    )

    items: List[ElectronicPrescriptionResponse] = []
    for prescription in prescriptions:
        response = ElectronicPrescriptionResponse.model_validate(prescription)
        if prescription.patient:
            response.patient_first_name = prescription.patient.first_name
            response.patient_last_name = prescription.patient.last_name
        items.append(response)

    return ElectronicPrescriptionListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


@router.post("/prescriptions", response_model=ElectronicPrescriptionResponse, status_code=status.HTTP_201_CREATED)
async def issue_prescription(
    prescription_data: ElectronicPrescriptionCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Émettre une nouvelle ordonnance électronique pour un patient.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    prescription = DoctorService.issue_prescription(db, profile.id, prescription_data)

    response = ElectronicPrescriptionResponse.model_validate(prescription)
    if prescription.patient:
        response.patient_first_name = prescription.patient.first_name
        response.patient_last_name = prescription.patient.last_name

    return response


@router.get("/prescriptions/{prescription_id}", response_model=ElectronicPrescriptionResponse)
async def get_prescription_detail(
    prescription_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir les détails d'une ordonnance électronique précise.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    prescription = DoctorService.get_prescription(db, profile.id, prescription_id)

    response = ElectronicPrescriptionResponse.model_validate(prescription)
    if prescription.patient:
        response.patient_first_name = prescription.patient.first_name
        response.patient_last_name = prescription.patient.last_name

    return response


# ========== 17️⃣ Boîte de messagerie ==========
@router.get("/messages", response_model=MessageListResponse)
async def get_my_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir la liste des messages reçus et envoyés.
    
    Nécessite le rôle DOCTOR.
    """
    messages, total = DoctorService.get_doctor_messages(db, current_user.id, page, page_size)
    
    # Créer les MessageResponse avec toutes les données requises
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
    
    return MessageListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ========== 18️⃣ Envoyer un message ==========
@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Envoyer un message sécurisé à un patient.
    
    Nécessite le rôle DOCTOR.
    """
    message = DoctorService.send_message(db, current_user.id, message_data)
    
    # Créer la réponse avec toutes les données requises
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


# ========== 19️⃣ Historique des paiements ==========
@router.get("/payments", response_model=PaymentListResponse)
async def get_my_payments(
    status_filter: Optional[PaymentStatusEnum] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir l'historique des paiements reçus.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    payments, total = DoctorService.get_doctor_payments(
        db, profile.id, status_filter, page, page_size
    )
    
    # Enrichir avec les données patient
    items = []
    for payment in payments:
        response = PaymentResponse.model_validate(payment)
        response.patient_first_name = payment.patient.first_name
        response.patient_last_name = payment.patient.last_name
        items.append(response)
    
    return PaymentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ========== 20️⃣ Avis patients ==========
@router.get("/reviews", response_model=ReviewListResponse)
async def get_my_reviews(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Obtenir les avis et notes reçus des patients.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    reviews, total = DoctorService.get_doctor_reviews(db, profile.id, page, page_size)
    
    # Enrichir avec les données patient
    items = []
    for review in reviews:
        response = ReviewResponse.model_validate(review)
        response.patient_first_name = review.patient.first_name
        response.patient_last_name = review.patient.last_name
        items.append(response)
    
    return ReviewListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=items
    )


# ========== 21️⃣ Répondre à un avis ==========
@router.post("/reviews/{review_id}/respond", response_model=ReviewResponse)
async def respond_to_review(
    review_id: int,
    response_data: ReviewResponseCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Répondre à un avis patient.
    
    Nécessite le rôle DOCTOR.
    """
    profile = DoctorService.get_doctor_profile(db, current_user.id)
    review = DoctorService.respond_to_review(db, profile.id, review_id, response_data)
    
    # Enrichir avec les données patient
    db.refresh(review)
    response = ReviewResponse.model_validate(review)
    response.patient_first_name = review.patient.first_name
    response.patient_last_name = review.patient.last_name
    
    return response


# ========== 4️⃣ Consulter un profil public de médecin (DOIT ÊTRE EN DERNIER) ==========
@router.get("/{doctor_id}", response_model=DoctorPublicProfile)
async def get_doctor_public_profile(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Consulter le profil public d'un médecin.
    
    Accessible par tous les utilisateurs authentifiés.
    ⚠️ Cette route DOIT être définie en dernier car elle capture tous les IDs.
    """
    profile = DoctorService.get_public_doctor_profile(db, doctor_id)
    
    # Créer la réponse avec les données publiques
    return DoctorPublicProfile(
        id=profile.id,
        specialty=profile.specialty,
        sub_specialty=profile.sub_specialty,
        office_city=profile.office_city,
        biography=profile.biography,
        languages=profile.languages,
        experience_years=profile.experience_years,
        consultation_types=profile.consultation_types,
        consultation_duration=profile.consultation_duration,
        consultation_price=profile.consultation_price,
        accepts_new_patients=profile.accepts_new_patients,
        average_rating=profile.average_rating,
        total_reviews=profile.total_reviews,
        total_consultations=profile.total_consultations,
        first_name=profile.user.first_name,
        last_name=profile.user.last_name
    )


# ========== 5️⃣ Voir les créneaux disponibles d'un médecin ==========
@router.get("/{doctor_id}/schedule", response_model=List[ScheduleEntryResponse])
async def get_doctor_schedule(
    doctor_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir les créneaux disponibles d'un médecin.
    
    Accessible par tous les utilisateurs authentifiés.
    """
    entries = DoctorService.list_schedule_entries(db, doctor_id)

    if start_date or end_date:
        days_filter = set()
        if start_date and end_date:
            range_start, range_end = start_date, end_date
            if range_end < range_start:
                range_start, range_end = range_end, range_start
            current = range_start
            while current <= range_end:
                days_filter.add((current.weekday() + 1) % 7)
                current += timedelta(days=1)
        elif start_date:
            days_filter.add((start_date.weekday() + 1) % 7)
        elif end_date:
            days_filter.add((end_date.weekday() + 1) % 7)

        if days_filter:
            entries = [entry for entry in entries if entry.day_of_week in days_filter]

    return [ScheduleEntryResponse.model_validate(entry) for entry in entries]


# ========== AVAILABLE SLOTS (Créneaux disponibles) ==========

@router.get("/{doctor_id}/available-slots", response_model=List[AvailableSlotResponse])
async def get_doctor_available_slots(
    doctor_id: int,
    start_date: date = Query(..., description="Date de début de recherche (YYYY-MM-DD)"),
    end_date: date = Query(..., description="Date de fin de recherche (YYYY-MM-DD)"),
    consultation_type: Optional[ConsultationTypeEnum] = Query(None, description="Filtrer par type de consultation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtenir les créneaux RÉELLEMENT disponibles d'un médecin.
    
    Cette API croise automatiquement:
    - ✅ Les horaires récurrents configurés par le médecin
    - ✅ Les slots bloqués (congés, absences)
    - ✅ Les rendez-vous déjà réservés
    - ✅ Le type de consultation (cabinet/téléconsultation)
    
    **Accessible par tous les utilisateurs authentifiés.**
    
    Exemple:
    ```
    GET /api/v1/doctors/1/available-slots?start_date=2025-11-15&end_date=2025-11-22
    ```
    
    Retourne uniquement les créneaux `is_available=True` sauf indication contraire.
    """
    # Validation des dates
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La date de fin doit être après la date de début"
        )
    
    # Limiter la période de recherche à 30 jours max (performance)
    if (end_date - start_date).days > 30:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La période de recherche ne peut pas dépasser 30 jours"
        )
    
    # Récupérer les créneaux
    slots = DoctorService.get_available_slots(
        db=db,
        doctor_id=doctor_id,
        start_date=start_date,
        end_date=end_date,
        consultation_type=consultation_type.value if consultation_type else None
    )
    
    # Convertir en schéma Pydantic
    return [AvailableSlotResponse(**slot) for slot in slots]


# ========== BLOCKED SLOTS (Créneaux bloqués) ==========

@router.get("/me/blocked-slots", response_model=List[BlockedSlotResponse])
async def get_blocked_slots(
    start: Optional[datetime] = Query(None, description="Début de la période de filtrage"),
    end: Optional[datetime] = Query(None, description="Fin de la période de filtrage"),
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Récupérer la liste des créneaux bloqués du médecin connecté.
    
    Paramètres optionnels:
    - start: filtrer les créneaux qui se terminent après cette date
    - end: filtrer les créneaux qui commencent avant cette date
    """
    doctor = DoctorService.get_doctor_profile(db, current_user.id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Profil médecin non trouvé")
    
    slots = DoctorService.list_blocked_slots(db, doctor.id, start, end)
    return [BlockedSlotResponse.model_validate(slot) for slot in slots]


@router.post("/me/blocked-slots", response_model=BlockedSlotResponse, status_code=status.HTTP_201_CREATED)
async def create_blocked_slot(
    payload: BlockedSlotCreate,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Créer un nouveau créneau bloqué (indisponibilité ponctuelle).
    
    Le système vérifie qu'il n'y a pas de chevauchement avec d'autres créneaux bloqués.
    """
    doctor = DoctorService.get_doctor_profile(db, current_user.id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Profil médecin non trouvé")
    
    slot = DoctorService.create_blocked_slot(db, doctor.id, payload)
    return BlockedSlotResponse.model_validate(slot)


@router.delete("/me/blocked-slots/{slot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_blocked_slot(
    slot_id: int,
    current_user: User = Depends(require_role([UserRole.DOCTOR])),
    db: Session = Depends(get_db)
):
    """
    Supprimer un créneau bloqué.
    """
    doctor = DoctorService.get_doctor_profile(db, current_user.id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Profil médecin non trouvé")
    
    DoctorService.delete_blocked_slot(db, doctor.id, slot_id)
    return None
