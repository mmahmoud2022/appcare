"""
Routes FastAPI pour les fonctionnalités patient
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User, UserRole
from app.models.doctor import AppointmentStatusEnum, PatientDocument
from app.schemas.doctor import MessageCreate, MessageResponse
from app.schemas.patient import (
    DoctorSearchRequest,
    DoctorSearchResponse,
    PatientAppointmentCreate,
    PatientAppointmentListResponse,
    PatientAppointmentResponse,
    PatientAppointmentUpdate,
    PatientDashboardSummary,
    PatientMedicalRecordResponse,
    PatientMessageList,
    PatientPaymentHistory,
    PatientProfileResponse,
    PatientProfileUpdate,
    DoctorReviewCreate,
    DoctorReviewResponse,
)
from app.services.patient_service import PatientService
import os

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/dashboard", response_model=PatientDashboardSummary)
async def get_patient_dashboard(
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Obtenir les informations principales du tableau de bord patient"""
    return PatientService.get_dashboard_summary(db, current_user.id)


@router.get("/me", response_model=PatientProfileResponse)
async def get_my_patient_profile(
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Récupérer le profil patient"""
    profile = PatientService.get_patient_profile(db, current_user.id)
    return PatientProfileResponse.model_validate(profile)


@router.patch("/me", response_model=PatientProfileResponse)
async def update_my_patient_profile(
    profile_data: PatientProfileUpdate,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Mettre à jour le profil patient"""
    updated = PatientService.update_patient_profile(db, current_user.id, profile_data)
    return PatientProfileResponse.model_validate(updated)


@router.get("/appointments", response_model=PatientAppointmentListResponse)
async def list_patient_appointments(
    status_filter: Optional[AppointmentStatusEnum] = Query(None),
    upcoming_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Lister les rendez-vous du patient"""
    return PatientService.get_patient_appointments(
        db=db,
        patient_id=current_user.id,
        status_filter=status_filter,
        upcoming_only=upcoming_only,
        page=page,
        page_size=page_size
    )


@router.post("/appointments", response_model=PatientAppointmentResponse, status_code=status.HTTP_201_CREATED)
async def create_patient_appointment(
    appointment_data: PatientAppointmentCreate,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Créer un nouveau rendez-vous"""
    appointment = PatientService.create_appointment(
        db=db,
        patient_id=current_user.id,
        appointment_data=appointment_data
    )
    db.refresh(appointment)
    return PatientService._appointment_to_response(appointment)


@router.patch("/appointments/{appointment_id}", response_model=PatientAppointmentResponse)
async def update_patient_appointment(
    appointment_id: int,
    update_data: PatientAppointmentUpdate,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Modifier un rendez-vous"""
    appointment = PatientService.update_appointment(
        db=db,
        patient_id=current_user.id,
        appointment_id=appointment_id,
        update_data=update_data
    )
    db.refresh(appointment)
    return PatientService._appointment_to_response(appointment)


@router.delete("/appointments/{appointment_id}", response_model=PatientAppointmentResponse)
async def cancel_patient_appointment(
    appointment_id: int,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Annuler un rendez-vous"""
    appointment = PatientService.cancel_appointment(db, current_user.id, appointment_id)
    db.refresh(appointment)
    return PatientService._appointment_to_response(appointment)


@router.get("/medical-records", response_model=PatientMedicalRecordResponse)
async def get_patient_medical_records(
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Obtenir le dossier médical complet"""
    return PatientService.get_medical_record(db, current_user.id)


@router.get("/documents/{document_id}/download")
async def download_patient_document(
    document_id: int,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Télécharger un document médical partagé par un médecin"""
    document = db.query(PatientDocument).filter(
        PatientDocument.id == document_id,
        PatientDocument.patient_id == current_user.id,
        PatientDocument.is_patient_visible == True
    ).first()
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document non trouvé ou accès refusé"
        )
    
    if not os.path.exists(document.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichier introuvable sur le serveur"
        )
    
    return FileResponse(
        path=document.file_path,
        filename=document.file_name,
        media_type=document.mime_type or "application/octet-stream"
    )


@router.get("/payments", response_model=PatientPaymentHistory)
async def get_patient_payments(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Historique des paiements"""
    return PatientService.get_payments(db, current_user.id, page, page_size)


@router.get("/messages", response_model=PatientMessageList)
async def get_patient_messages(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Récupérer les messages du patient"""
    return PatientService.get_messages(db, current_user.id, page, page_size)


@router.patch("/messages/{message_id}/read", response_model=MessageResponse)
async def mark_message_as_read(
    message_id: int,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Marquer un message comme lu"""
    return PatientService.mark_message_as_read(db, current_user.id, message_id)


@router.post("/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_patient_message(
    payload: MessageCreate,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Envoyer un message à un praticien"""
    message = PatientService.send_message(
        db=db,
        sender_id=current_user.id,
        recipient_id=payload.recipient_id,
        content=payload.content,
        subject=payload.subject,
        appointment_id=payload.appointment_id
    )
    return message


@router.get("/doctors/search", response_model=DoctorSearchResponse)
async def search_doctors_for_patient(
    specialty: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    search: Optional[str] = Query(None, max_length=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Rechercher des praticiens disponibles (GET)"""
    filters = DoctorSearchRequest(
        specialty=specialty,
        city=city,
        language=language,
        min_price=min_price,
        max_price=max_price,
        search=search
    )
    return PatientService.search_doctors(db, filters, page, page_size)


@router.post("/search-doctors", response_model=DoctorSearchResponse)
async def search_doctors_post(
    request_data: DoctorSearchRequest,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Rechercher des praticiens disponibles (POST - pour le frontend)"""
    page = request_data.page or 1
    page_size = request_data.page_size or 20
    return PatientService.search_doctors(db, request_data, page, page_size)


@router.post("/reviews", response_model=DoctorReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_doctor_review(
    review_data: DoctorReviewCreate,
    current_user: User = Depends(require_role([UserRole.PATIENT])),
    db: Session = Depends(get_db)
):
    """Créer un avis sur un médecin après un rendez-vous terminé"""
    return PatientService.create_doctor_review(db, current_user.id, review_data)