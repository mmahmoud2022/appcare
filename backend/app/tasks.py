"""
Celery tasks for background processing
"""
from typing import Dict, Any, Optional
import asyncio
from celery import shared_task

from app.core.logging import get_logger
from app.services.email_service import get_email_service

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_task(
    self,
    to_email: str,
    subject: str,
    html_content: str,
    plain_content: Optional[str] = None,
    from_email: Optional[str] = None,
    from_name: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Send an email via Celery task
    
    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML email body
        plain_content: Plain text email body (optional)
        from_email: Sender email (optional)
        from_name: Sender name (optional)
        metadata: Custom metadata for tracking (optional)
        
    Returns:
        Dictionary with send result
    """
    try:
        email_service = get_email_service()
        
        # Run async function in sync context
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            email_service.send_email(
                to_email=to_email,
                subject=subject,
                html_content=html_content,
                plain_content=plain_content,
                from_email=from_email,
                from_name=from_name,
                metadata=metadata
            )
        )
        
        if result["success"]:
            logger.info(f"Email sent successfully to {to_email}")
            return result
        else:
            logger.error(f"Failed to send email to {to_email}: {result.get('error')}")
            raise Exception(result.get("error", "Unknown error"))
            
    except Exception as exc:
        logger.error(f"Email task failed: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_confirmation_task(
    self,
    to_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str,
    appointment_type: str,
    cancellation_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send appointment confirmation email via Celery
    
    Args:
        to_email: Patient email
        patient_name: Patient name
        doctor_name: Doctor name
        appointment_date: Appointment date
        appointment_time: Appointment time
        appointment_type: Type of appointment
        cancellation_url: URL for cancelling appointment
        
    Returns:
        Send result dictionary
    """
    try:
        email_service = get_email_service()
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            email_service.send_appointment_confirmation(
                to_email=to_email,
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                appointment_type=appointment_type,
                cancellation_url=cancellation_url
            )
        )
        
        if result["success"]:
            logger.info(f"Appointment confirmation sent to {to_email}")
            return result
        else:
            raise Exception(result.get("error", "Unknown error"))
            
    except Exception as exc:
        logger.error(f"Appointment confirmation task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_appointment_reminder_task(
    self,
    to_email: str,
    patient_name: str,
    doctor_name: str,
    appointment_date: str,
    appointment_time: str
) -> Dict[str, Any]:
    """
    Send appointment reminder email via Celery
    """
    try:
        email_service = get_email_service()
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            email_service.send_appointment_reminder(
                to_email=to_email,
                patient_name=patient_name,
                doctor_name=doctor_name,
                appointment_date=appointment_date,
                appointment_time=appointment_time
            )
        )
        
        if result["success"]:
            logger.info(f"Appointment reminder sent to {to_email}")
            return result
        else:
            raise Exception(result.get("error", "Unknown error"))
            
    except Exception as exc:
        logger.error(f"Appointment reminder task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_password_reset_task(
    self,
    to_email: str,
    first_name: str,
    reset_url: str,
    expiry_minutes: int = 15
) -> Dict[str, Any]:
    """
    Send password reset email via Celery
    """
    try:
        email_service = get_email_service()
        
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(
            email_service.send_password_reset(
                to_email=to_email,
                first_name=first_name,
                reset_url=reset_url,
                expiry_minutes=expiry_minutes
            )
        )
        
        if result["success"]:
            logger.info(f"Password reset email sent to {to_email}")
            return result
        else:
            raise Exception(result.get("error", "Unknown error"))
            
    except Exception as exc:
        logger.error(f"Password reset task failed: {str(exc)}")
        raise self.retry(exc=exc)


@shared_task
def send_daily_appointment_reminders():
    """
    Scheduled task to send daily appointment reminders (24h before appointment)
    Runs daily at 9:00 AM via Celery Beat
    Finds all appointments in the next 24 hours and sends reminder emails
    """
    from datetime import datetime, timedelta
    from sqlalchemy.orm import Session, joinedload
    from app.core.database import SessionLocal
    from app.models.doctor import Appointment, AppointmentStatusEnum
    from app.models.user import User
    from app.models.doctor import DoctorProfile
    
    try:
        # Calculate time window: next 24 hours from now
        now = datetime.now()
        reminder_start = now
        reminder_end = now + timedelta(hours=24)
        
        logger.info(f"[REMINDER] Checking appointments between {reminder_start} and {reminder_end}")
        
        db: Session = SessionLocal()
        try:
            # Query confirmed appointments in the next 24 hours
            appointments = db.query(Appointment).options(
                joinedload(Appointment.patient),
                joinedload(Appointment.doctor)
            ).filter(
                Appointment.status == AppointmentStatusEnum.CONFIRMED,
                Appointment.appointment_date >= reminder_start,
                Appointment.appointment_date <= reminder_end,
                Appointment.is_deleted == False  # Exclude soft-deleted appointments
            ).all()
            
            logger.info(f"[REMINDER] Found {len(appointments)} appointments to remind")
            
            reminders_sent = 0
            errors = 0
            
            for appointment in appointments:
                try:
                    # Get patient and doctor information
                    patient = appointment.patient
                    doctor = appointment.doctor
                    
                    if not patient or not patient.email:
                        logger.warning(f"[REMINDER] Skipping appointment {appointment.id}: no patient email")
                        continue
                    
                    doctor_name = f"{doctor.user.first_name} {doctor.user.last_name}" if doctor and doctor.user else "Médecin"
                    patient_name = f"{patient.first_name} {patient.last_name}"
                    
                    # Format date and time for email
                    appointment_date = appointment.appointment_date.strftime("%d/%m/%Y")
                    appointment_time = appointment.appointment_date.strftime("%H:%M")
                    
                    logger.info(
                        f"[REMINDER] Sending reminder for appointment {appointment.id} | "
                        f"patient={patient.email} | doctor={doctor_name} | "
                        f"datetime={appointment_date} {appointment_time}"
                    )
                    
                    # Send reminder email asynchronously
                    send_appointment_reminder_task.delay(
                        to_email=patient.email,
                        patient_name=patient_name,
                        doctor_name=doctor_name,
                        appointment_date=appointment_date,
                        appointment_time=appointment_time
                    )
                    
                    reminders_sent += 1
                    
                except Exception as e:
                    errors += 1
                    logger.error(f"[REMINDER] Failed to send reminder for appointment {appointment.id}: {str(e)}")
                    continue
            
            logger.info(
                f"[REMINDER] Completed | sent={reminders_sent} | errors={errors} | total={len(appointments)}"
            )
            
            return {
                "success": True,
                "message": "Daily reminders processed",
                "reminders_sent": reminders_sent,
                "errors": errors,
                "total_appointments": len(appointments)
            }
            
        finally:
            db.close()
        
    except Exception as exc:
        logger.error(f"[REMINDER] Daily reminder task failed: {str(exc)}", exc_info=True)
        raise


@shared_task
def cleanup_expired_tokens():
    """
    Scheduled task to clean up expired password reset tokens
    Runs daily at 2:00 AM via Celery Beat
    """
    from datetime import datetime
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    from app.models.auth import PasswordResetToken, VerificationToken
    
    try:
        logger.info("[CLEANUP] Starting token cleanup task")
        
        db: Session = SessionLocal()
        try:
            now = datetime.now()
            
            # Delete expired password reset tokens
            expired_reset_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < now
            ).delete()
            
            # Delete expired verification tokens
            expired_verification_tokens = db.query(VerificationToken).filter(
                VerificationToken.expires_at < now
            ).delete()
            
            db.commit()
            
            logger.info(
                f"[CLEANUP] Token cleanup completed | "
                f"reset_tokens={expired_reset_tokens} | "
                f"verification_tokens={expired_verification_tokens}"
            )
            
            return {
                "success": True,
                "message": "Token cleanup completed",
                "reset_tokens_deleted": expired_reset_tokens,
                "verification_tokens_deleted": expired_verification_tokens
            }
            
        finally:
            db.close()
        
    except Exception as exc:
        logger.error(f"[CLEANUP] Token cleanup task failed: {str(exc)}", exc_info=True)
        raise


@shared_task
def cleanup_old_appointments():
    """
    Scheduled task to permanently delete old soft-deleted appointments
    Runs weekly on Sunday at 3:00 AM via Celery Beat
    Removes soft-deleted appointments older than 90 days
    """
    from datetime import datetime, timedelta
    from sqlalchemy.orm import Session
    from app.core.database import SessionLocal
    from app.models.doctor import Appointment
    
    try:
        logger.info("[CLEANUP] Starting old appointments cleanup task")
        
        db: Session = SessionLocal()
        try:
            # Delete appointments soft-deleted more than 90 days ago
            cutoff_date = datetime.now() - timedelta(days=90)
            
            deleted_count = db.query(Appointment).filter(
                Appointment.is_deleted == True,
                Appointment.deleted_at < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(
                f"[CLEANUP] Old appointments cleanup completed | "
                f"permanently_deleted={deleted_count}"
            )
            
            return {
                "success": True,
                "message": "Old appointments cleanup completed",
                "appointments_deleted": deleted_count
            }
            
        finally:
            db.close()
        
    except Exception as exc:
        logger.error(f"[CLEANUP] Appointments cleanup task failed: {str(exc)}", exc_info=True)
        raise
